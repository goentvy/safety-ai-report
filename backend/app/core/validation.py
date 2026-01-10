"""
환경 검증 및 예외 처리 유틸리티
"""
import os
import logging
from typing import Optional
from anthropic import APIError, RateLimitError, APIConnectionError

logger = logging.getLogger(__name__)


# ============================================================================
# 환경변수 검증
# ============================================================================

def validate_environment() -> None:
    """
    필수 환경변수를 검증합니다.

    Raises:
        RuntimeError: 필수 환경변수가 누락된 경우
    """
    required_vars = {
        "ANTHROPIC_API_KEY": "Claude API 키",
    }

    missing_vars = []

    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if not value or value.strip() == "":
            missing_vars.append(f"{var_name} ({description})")

    if missing_vars:
        error_msg = f"필수 환경변수가 설정되지 않았습니다:\n" + "\n".join(f"  - {var}" for var in missing_vars)
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.info("✅ 모든 필수 환경변수 검증 완료")


def validate_optional_environment() -> dict[str, Optional[str]]:
    """
    선택적 환경변수를 검증하고 상태를 반환합니다.

    Returns:
        dict: 환경변수 이름과 값 또는 None
    """
    optional_vars = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "LLAMA_CLOUD_API_KEY": os.getenv("LLAMA_CLOUD_API_KEY"),
    }

    for var_name, value in optional_vars.items():
        if value:
            logger.info(f"✅ {var_name} 설정됨")
        else:
            logger.warning(f"⚠️  {var_name} 미설정 (선택적)")

    return optional_vars


# ============================================================================
# 커스텀 예외
# ============================================================================

class FileTooLargeError(Exception):
    """파일 크기 초과 예외"""
    def __init__(self, size: int, max_size: int):
        self.size = size
        self.max_size = max_size
        super().__init__(
            f"파일 크기({size / 1024 / 1024:.2f}MB)가 "
            f"최대 허용 크기({max_size / 1024 / 1024:.2f}MB)를 초과합니다"
        )


class UnsupportedFileTypeError(Exception):
    """지원하지 않는 파일 타입 예외"""
    def __init__(self, file_type: str, supported_types: list[str]):
        self.file_type = file_type
        self.supported_types = supported_types
        super().__init__(
            f"지원하지 않는 파일 형식입니다: {file_type}. "
            f"지원 형식: {', '.join(supported_types)}"
        )


class InvalidMessageError(Exception):
    """잘못된 메시지 예외"""
    pass


# ============================================================================
# 예외 핸들러
# ============================================================================

def handle_anthropic_error(error: Exception) -> tuple[int, str, Optional[str]]:
    """
    Anthropic API 에러를 처리하고 HTTP 상태 코드와 메시지를 반환합니다.

    Args:
        error: 발생한 예외

    Returns:
        tuple: (HTTP 상태 코드, 에러 메시지, 에러 코드)
    """
    if isinstance(error, RateLimitError):
        logger.warning(f"Rate limit 초과: {error}")
        return 429, "API 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.", "RATE_LIMIT_EXCEEDED"

    elif isinstance(error, APIConnectionError):
        logger.error(f"API 연결 실패: {error}")
        return 503, "AI 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.", "API_CONNECTION_ERROR"

    elif isinstance(error, APIError):
        logger.error(f"API 에러: {error}")
        return 500, f"AI 서비스 오류가 발생했습니다: {str(error)}", "API_ERROR"

    elif isinstance(error, FileTooLargeError):
        logger.warning(f"파일 크기 초과: {error}")
        return 413, str(error), "FILE_TOO_LARGE"

    elif isinstance(error, UnsupportedFileTypeError):
        logger.warning(f"지원하지 않는 파일 타입: {error}")
        return 415, str(error), "UNSUPPORTED_FILE_TYPE"

    elif isinstance(error, InvalidMessageError):
        logger.warning(f"잘못된 메시지: {error}")
        return 400, str(error), "INVALID_MESSAGE"

    elif isinstance(error, ValueError):
        logger.warning(f"입력 값 오류: {error}")
        return 400, str(error), "INVALID_INPUT"

    else:
        logger.error(f"예상치 못한 에러: {error}", exc_info=True)
        return 500, "서버 내부 오류가 발생했습니다.", "INTERNAL_ERROR"


# ============================================================================
# 파일 검증
# ============================================================================

def validate_file_size(file_size: Optional[int], max_size: int) -> None:
    """
    파일 크기를 검증합니다.

    Args:
        file_size: 파일 크기 (bytes)
        max_size: 최대 허용 크기 (bytes)

    Raises:
        FileTooLargeError: 파일 크기가 최대 크기를 초과한 경우
    """
    if file_size and file_size > max_size:
        raise FileTooLargeError(file_size, max_size)


def validate_image_type(content_type: Optional[str], supported_types: dict[str, str]) -> str:
    """
    이미지 타입을 검증하고 표준화된 media_type을 반환합니다.

    Args:
        content_type: 파일의 content_type
        supported_types: 지원하는 타입 딕셔너리

    Returns:
        str: 표준화된 media_type

    Raises:
        UnsupportedFileTypeError: 지원하지 않는 파일 타입인 경우
    """
    if not content_type:
        raise UnsupportedFileTypeError("Unknown", list(supported_types.keys()))

    content_type = content_type.lower()

    if content_type not in supported_types:
        raise UnsupportedFileTypeError(content_type, list(supported_types.keys()))

    return supported_types[content_type]

