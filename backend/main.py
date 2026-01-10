"""
Safety AI Agent - 산업안전 통합 AI 서비스
"""
import anthropic
import os
import base64
from typing import Optional, List, Union
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from anthropic.types import MessageParam, TextBlock, ContentBlock

# 내부 모듈
from app.core.constants import (
    MODEL_ID,
    MAX_FILE_SIZE,
    SUPPORTED_IMAGE_TYPES,
    MODEL_CONFIG,
    SYSTEM_PROMPTS,
    DEFAULT_VISION_PROMPT,
    DOCUMENT_KEYWORDS
)
from app.core.validation import (
    validate_environment,
    validate_optional_environment,
    validate_file_size,
    validate_image_type,
    handle_anthropic_error,
    InvalidMessageError
)
from app.core.logging_config import setup_logging, get_logger
from app.models.schemas import (
    VisionResponse,
    DocumentResponse,
    QAResponse,
    ErrorResponse
)

# 환경변수 로드
load_dotenv()

# 로깅 설정
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=os.getenv("LOG_FILE", None)
)
logger = get_logger(__name__)

# 환경변수 검증 (앱 시작 시 즉시 실행)
try:
    validate_environment()
    validate_optional_environment()
except RuntimeError as e:
    logger.critical(f"❌ 환경변수 검증 실패: {e}")
    raise

# FastAPI 앱 초기화
app = FastAPI(
    title="Safety AI Agent",
    description="산업안전보건 통합 AI 분석 서비스 - 이미지 분석, 문서 생성, 질의응답",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Anthropic 클라이언트 초기화
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

logger.info(f"✅ Safety AI Agent 시작 완료 (모델: {MODEL_ID})")


# ============================================================================
# 헬퍼 함수
# ============================================================================

def extract_full_text(content_blocks: List[ContentBlock]) -> str:
    """Anthropic 응답 블록에서 텍스트만 추출"""
    return "".join([block.text for block in content_blocks if isinstance(block, TextBlock)])


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



# ============================================================================
# API 엔드포인트
# ============================================================================

@app.get("/")
async def root():
    """헬스체크 엔드포인트"""
    return {
        "status": "healthy",
        "service": "Safety AI Agent",
        "version": "2.0.0"
    }


@app.post(
    "/chat",
    response_model=Union[VisionResponse, DocumentResponse, QAResponse],
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        413: {"model": ErrorResponse, "description": "파일 크기 초과"},
        415: {"model": ErrorResponse, "description": "지원하지 않는 파일 타입"},
        429: {"model": ErrorResponse, "description": "API 요청 한도 초과"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    },
    summary="안전 점검 통합 API",
    description=(
        "이미지 분석, 문서 생성, 질의응답을 수행하는 통합 엔드포인트입니다.\n\n"
        "**사용 예시:**\n"
        "1. 이미지만 전송 → 산안법 기준으로 자동 분석\n"
        "2. 이미지 + 질문 → 맞춤형 분석\n"
        "3. 텍스트(문서 생성 키워드 포함) → 문서 생성\n"
        "4. 일반 텍스트 질문 → 질의응답"
    ),
    tags=["chat"]
)
async def integrated_chat(
    file: Optional[UploadFile] = File(None, description="분석할 이미지 파일 (최대 10MB)"),
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
    logger.info(f"[{request_id}] 요청 시작 - file: {bool(file)}, message: {bool(message)}")

    try:
        # 1. 입력 검증
        if not file and not (message and message.strip()):
            logger.warning(f"[{request_id}] 입력 누락")
            raise InvalidMessageError("파일 또는 메시지 중 하나는 반드시 제공되어야 합니다.")

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
            user_text = (message or "").strip() or DEFAULT_VISION_PROMPT

            # API 호출
            vision_messages: List[MessageParam] = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_image,
                            },
                        },
                        {"type": "text", "text": user_text},
                    ],
                }
            ]

            response = client.messages.create(
                model=MODEL_ID,
                max_tokens=MODEL_CONFIG["vision"]["max_tokens"],
                temperature=MODEL_CONFIG["vision"]["temperature"],
                system=SYSTEM_PROMPTS["vision"],
                messages=vision_messages,
            )

            result_content = extract_full_text(response.content)
            logger.info(f"[{request_id}] 이미지 분석 완료 - {len(result_content)} chars")

            return VisionResponse(
                type="vision",
                content=result_content,
                status="success"
            )

        # 3. 문서 생성 처리
        if message and any(keyword in message for keyword in DOCUMENT_KEYWORDS):
            logger.info(f"[{request_id}] 문서 생성 시작")

            doc_messages: List[MessageParam] = [{"role": "user", "content": message}]

            response = client.messages.create(
                model=MODEL_ID,
                max_tokens=MODEL_CONFIG["document"]["max_tokens"],
                temperature=MODEL_CONFIG["document"]["temperature"],
                system=SYSTEM_PROMPTS["document"],
                messages=doc_messages,
            )

            result_content = extract_full_text(response.content)
            logger.info(f"[{request_id}] 문서 생성 완료 - {len(result_content)} chars")

            return DocumentResponse(
                type="document",
                content=result_content,
                status="success"
            )

        # 4. 일반 질의응답 처리
        logger.info(f"[{request_id}] 질의응답 시작")

        qa_message_content = message or "산업안전보건 관련 질의"
        qa_messages: List[MessageParam] = [{"role": "user", "content": qa_message_content}]

        response = client.messages.create(
            model=MODEL_ID,
            max_tokens=MODEL_CONFIG["qa"]["max_tokens"],
            temperature=MODEL_CONFIG["qa"]["temperature"],
            system=SYSTEM_PROMPTS["qa"],
            messages=qa_messages,
        )

        result_content = extract_full_text(response.content)
        logger.info(f"[{request_id}] 질의응답 완료 - {len(result_content)} chars")

        return QAResponse(
            type="qa",
            content=result_content,
            model_used=MODEL_ID,
            status="success"
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
                "error_code": error_code
            }
        )
