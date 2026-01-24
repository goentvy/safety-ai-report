"""
Chat API - 통합 챗 엔드포인트
"""
import os
import base64
from typing import Optional, List, Union
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.core.constants import (
    MAX_FILE_SIZE,
    SUPPORTED_IMAGE_TYPES,
    DOCUMENT_KEYWORDS,
)
from app.core.validation import (
    validate_file_size,
    validate_image_type,
    handle_anthropic_error,
    InvalidMessageError,
)
from app.core.logging_config import get_logger
from app.models.schemas import (
    VisionResponse,
    DocumentResponse,
    QAResponse,
)
from app.services.ai_service import get_ai_service
from app.services.rag_service import TOP_K, get_rag_service, format_context_for_llm

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def get_media_type(file: UploadFile) -> str:
    """파일의 media_type을 검증하고 반환"""
    content_type = file.content_type

    # content_type이 None이면 파일 확장자로 추측
    if not content_type:
        filename = file.filename or ""
        if filename.lower().endswith((".jpg", ".jpeg")):
            content_type = "image/jpeg"
        elif filename.lower().endswith(".png"):
            content_type = "image/png"
        elif filename.lower().endswith(".gif"):
            content_type = "image/gif"
        elif filename.lower().endswith(".webp"):
            content_type = "image/webp"

    return validate_image_type(content_type, SUPPORTED_IMAGE_TYPES)


@router.post(
    "/",
    response_model=Union[VisionResponse, DocumentResponse, QAResponse],
    summary="안전 점검 통합 API",
    description=(
        "이미지 분석, 문서 생성, 질의응답을 수행하는 통합 엔드포인트입니다.\n\n"
        "**사용 예시:**\n"
        "1. 이미지만 전송 → 산안법 기준으로 자동 분석\n"
        "2. 이미지 + 질문 → 맞춤형 분석\n"
        "3. 텍스트(문서 생성 키워드 포함) → 문서 생성\n"
        "4. 일반 텍스트 질문 → 질의응답"
    ),
)
async def integrated_chat(
    file: Optional[UploadFile] = File(
        None, description="분석할 이미지 파일 (최대 10MB)"
    ),
    message: Optional[str] = Form(None, description="질문 또는 요청 메시지"),
) -> Union[VisionResponse, DocumentResponse, QAResponse]:
    """
    안전 점검 통합 처리

    Args:
        file: 업로드된 이미지 파일 (선택)
        message: 사용자 메시지 (선택)

    Returns:
        Union[VisionResponse, DocumentResponse, QAResponse]: 처리 결과

    Raises:
        HTTPException: 입력 검증 실패 또는 처리 오류
    """
    request_id = f"req_{os.urandom(4).hex()}"
    logger.info(
        f"[{request_id}] 요청 시작 - file: {bool(file)}, message: {bool(message)}"
    )

    try:
        # 1. 입력 검증
        if not file and not (message and message.strip()):
            logger.warning(f"[{request_id}] 입력 누락")
            raise InvalidMessageError(
                "파일 또는 메시지 중 하나는 반드시 제공되어야 합니다."
            )

        ai_service = get_ai_service()

        # RAG 서비스 가져오기 (선택적)
        rag_service = None
        try:
            rag_service = get_rag_service()
        except Exception:
            pass  # RAG 서비스 없이도 동작 가능

        # 2. 이미지 분석 처리
        if file:
            logger.info(f"[{request_id}] 이미지 분석 시작 - {file.filename}")

            # 파일 크기 검증
            file_content = await file.read()
            validate_file_size(len(file_content), MAX_FILE_SIZE)

            # 이미지 타입 검증
            media_type = get_media_type(file)

            # Base64 인코딩
            base64_image = base64.b64encode(file_content).decode("utf-8")

            # 프롬프트 결정
            user_text = (message or "").strip()

            # RAG 검색 추가 (사용자가 질문을 포함한 경우)
            rag_result = None
            rag_context = ""
            source_docs = []

            if message and message.strip() and rag_service:
                try:
                    logger.info(f"[{request_id}] 이미지 분석 - RAG 검색 수행 중...")
                    rag_result = rag_service.search_with_category_priority(
                        message.strip(), top_k=3
                    )
                    if rag_result.get("results"):
                        rag_context = "\n\n[참고 법령]\n" + format_context_for_llm(
                            rag_result["results"]
                        )

                        # source_docs 구성
                        for result in rag_result["results"]:
                            metadata = result.get("metadata", {})
                            similarity = result.get("similarity")
                            if similarity is None:
                                distance = result.get("distance", 0)
                                similarity = max(0.0, min(1.0, 1 - distance))
                            source_docs.append(
                                {
                                    "title": metadata.get("title", ""),
                                    "category": metadata.get("category", ""),
                                    "similarity": round(similarity, 4),
                                }
                            )

                        logger.info(
                            f"[{request_id}] RAG 검색 완료 - {len(rag_result['results'])}개 법령"
                        )
                except Exception as e:
                    logger.warning(f"[{request_id}] RAG 검색 실패: {e}")

            # 시스템 프롬프트에 법령 정보 추가
            from app.core.constants import SYSTEM_PROMPTS

            system_prompt = SYSTEM_PROMPTS["vision"]
            if rag_context:
                system_prompt = system_prompt + rag_context

            # AI 서비스를 통한 이미지 분석
            result_content = await ai_service.analyze_image(
                base64_image, media_type, user_text, system_prompt
            )

            logger.info(
                f"[{request_id}] 이미지 분석 완료 - {len(result_content)} chars"
            )

            return VisionResponse(
                type="vision",
                content=result_content,
                status="success",
                source_docs=source_docs if source_docs else None,
            )

        # 3. 문서 생성 처리
        if message and any(keyword in message for keyword in DOCUMENT_KEYWORDS):
            logger.info(f"[{request_id}] 문서 생성 시작")

            result_content = await ai_service.generate_document(message)

            logger.info(f"[{request_id}] 문서 생성 완료 - {len(result_content)} chars")

            return DocumentResponse(
                type="document", content=result_content, status="success"
            )

        # 4. 일반 질의응답 처리
        logger.info(f"[{request_id}] 질의응답 시작")

        qa_message_content = message or "산업안전보건 관련 질의"

        # RAG 검색 수행
        source_docs = []
        enhanced_system_prompt = None

        if rag_service:
            try:
                logger.info(f"[{request_id}] RAG 검색 수행 중... (법령 우선)")

                # 법령 우선 검색 사용
                rag_result = rag_service.search_with_category_priority(
                    qa_message_content, top_k=TOP_K
                )
                search_results = rag_result.get("results", [])
                search_type = rag_result.get("search_type", "unknown")

                if search_results:
                    # 컨텍스트 생성
                    rag_context = format_context_for_llm(search_results)

                    # 시스템 프롬프트에 법령 정보 추가
                    from app.core.constants import SYSTEM_PROMPTS

                    enhanced_system_prompt = (
                        f"{SYSTEM_PROMPTS['qa']}\n\n"
                        f"## 검색된 관련 법령\n"
                        f"다음은 질문과 관련된 산업안전보건법령입니다. 이 법령을 기반으로 답변해주세요:\n\n"
                        f"{rag_context}\n"
                    )

                    # 소스 문서 메타데이터 추출
                    for result in search_results:
                        metadata = result.get("metadata", {})
                        similarity = result.get("similarity")
                        if similarity is None:
                            distance = result.get("distance", 0)
                            similarity = max(0.0, min(1.0, 1 - distance))
                        source_docs.append(
                            {
                                "title": metadata.get("title", ""),
                                "category": metadata.get("category", ""),
                                "category_name": metadata.get("category_name", ""),
                                "doc_id": metadata.get("doc_id", ""),
                                "filepath": metadata.get("filepath", ""),
                                "similarity": round(similarity, 4),
                                "content_preview": result.get("text", "")[:200] + "...",
                            }
                        )

                    logger.info(
                        f"[{request_id}] RAG 검색 완료 - {len(search_results)}개 결과 ({search_type})"
                    )
                else:
                    logger.info(f"[{request_id}] RAG 검색 결과 없음")
            except Exception as e:
                logger.warning(f"[{request_id}] RAG 검색 실패: {e}")
                # RAG 실패해도 기본 질의응답은 수행

        # AI 서비스를 통한 질의응답
        result_content = await ai_service.answer_question(
            qa_message_content, enhanced_system_prompt
        )

        logger.info(f"[{request_id}] 질의응답 완료 - {len(result_content)} chars")

        return QAResponse(
            type="qa",
            content=result_content,
            source_docs=source_docs,
            model_used=ai_service.model_id,
            status="success",
        )

    except HTTPException:
        # FastAPI HTTPException은 그대로 전파
        raise

    except Exception as e:
        # 모든 예외를 적절한 HTTP 응답으로 변환
        status_code, error_message, error_code = handle_anthropic_error(e)
        logger.error(f"[{request_id}] 에러 발생: {error_message}", exc_info=True)

        raise HTTPException(
            status_code=status_code,
            detail={
                "type": "error",
                "status": "fail",
                "content": error_message,
                "error_code": error_code,
            },
        )
