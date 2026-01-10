"""
Safety AI Agent - 산업안전 통합 AI 서비스
스트리밍(SSE) 기반 실시간 응답
"""
import anthropic
import os
import base64
from typing import Optional, List, Union, AsyncGenerator
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 내부 모듈
from app.core.constants import (
    MODEL_ID,
    MAX_FILE_SIZE,
    SUPPORTED_IMAGE_TYPES,
    DEFAULT_VISION_PROMPT,
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
from app.services.chat_service import ChatService
from app.services.request_handler import RequestHandler, RequestType

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
    description="산업안전보건 통합 AI 분석 서비스 - 스트리밍 기반 실시간 응답",
    version="2.1.0",
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

# 서비스 초기화
api_key = os.getenv("ANTHROPIC_API_KEY")
chat_service = ChatService(api_key)

logger.info(f"✅ Safety AI Agent 시작 완료 (모델: {MODEL_ID}, 스트리밍 활성화)")


# ============================================================================
# 헬퍼 함수
# ============================================================================

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


async def stream_response(
    generator: AsyncGenerator[str, None],
) -> AsyncGenerator[str, None]:
    """
    버퍼링된 JSON을 SSE 포맷으로 변환

    Args:
        generator: JSON 문자열 제너레이터

    Yields:
        SSE 포맷의 데이터 (data: {JSON}\n\n)
    """
    async for json_chunk in generator:
        # SSE 포맷: data: {JSON}\n\n
        yield f"data: {json_chunk}\n\n"


# ============================================================================
# API 엔드포인트
# ============================================================================

@app.get("/")
async def root():
    """헬스체크 엔드포인트"""
    return {
        "status": "healthy",
        "service": "Safety AI Agent",
        "version": "2.1.0",
        "streaming": True
    }


@app.post(
    "/chat/stream",
    summary="안전 점검 통합 API (스트리밍)",
    description=(
        "실시간 스트리밍(SSE) 기반 응답 제공\n\n"
        "**사용 예시:**\n"
        "1. 이미지만 전송 → 산안법 기준으로 자동 분석\n"
        "2. 이미지 + 질문 → 맞춤형 분석\n"
        "3. 텍스트(문서 생성 키워드 포함) → 문서 생성\n"
        "4. 일반 텍스트 질문 → 질의응답"
    ),
    tags=["chat"],
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        413: {"model": ErrorResponse, "description": "파일 크기 초과"},
        415: {"model": ErrorResponse, "description": "지원하지 않는 파일 타입"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    }
)
async def chat_stream(
    file: Optional[UploadFile] = File(None, description="분석할 이미지 파일 (최대 10MB)"),
    message: Optional[str] = Form(None, description="질문 또는 요청 메시지"),
):
    """
    스트리밍 기반 안전 점검 통합 처리

    Returns:
        StreamingResponse: SSE 형식의 실시간 응답 스트림
    """
    request_id = f"req_{os.urandom(4).hex()}"
    logger.info(f"[{request_id}] 스트리밍 요청 시작 - file: {bool(file)}, message: {bool(message)}")

    try:
        # 1. 입력 검증
        if not file and not (message and message.strip()):
            logger.warning(f"[{request_id}] 입력 누락")
            raise InvalidMessageError("파일 또는 메시지 중 하나는 반드시 제공되어야 합니다.")

        # 2. 요청 타입 결정
        request_type = RequestHandler.determine_request_type(bool(file), message)
        logger.info(f"[{request_id}] 요청 타입: {request_type}")

        # 3. 이미지 분석
        if request_type == RequestType.VISION:
            file_content = await file.read()
            validate_file_size(len(file_content), MAX_FILE_SIZE)

            media_type = get_media_type(file)
            base64_image = base64.b64encode(file_content).decode("utf-8")

            # 프롬프트 결정 (메시지 없으면 기본값 사용)
            user_prompt = (message or "").strip() or DEFAULT_VISION_PROMPT

            logger.info(f"[{request_id}] 이미지 분석 스트리밍 시작")

            generator = chat_service.stream_vision_analysis(
                base64_image=base64_image,
                media_type=media_type,
                user_prompt=user_prompt,
            )

            return StreamingResponse(
                stream_response(generator),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                }
            )

        # 4. 문서 생성
        if request_type == RequestType.DOCUMENT:
            logger.info(f"[{request_id}] 문서 생성 스트리밍 시작")

            generator = chat_service.stream_document_generation(
                user_message=message
            )

            return StreamingResponse(
                stream_response(generator),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                }
            )

        # 5. 질의응답
        if request_type == RequestType.QA:
            logger.info(f"[{request_id}] 질의응답 스트리밍 시작")

            generator = chat_service.stream_qa(user_message=message)

            return StreamingResponse(
                stream_response(generator),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                }
            )

    except HTTPException as he:
        logger.error(f"[{request_id}] HTTP 예외: {he.detail}")
        raise

    except Exception as e:
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

