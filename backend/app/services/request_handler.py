"""
Request Handler - 사용자 요청 타입 판별 및 처리
"""
from typing import Optional
from enum import Enum
from app.core.constants import DOCUMENT_KEYWORDS
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RequestType(str, Enum):
    """요청 타입"""
    VISION = "vision"
    DOCUMENT = "document"
    QA = "qa"


class RequestHandler:
    """사용자 요청을 분석하여 적절한 처리 방식 결정"""

    @staticmethod
    def determine_request_type(
        has_file: bool,
        message: Optional[str],
    ) -> RequestType:
        """
        파일과 메시지를 기반으로 요청 타입 결정

        Args:
            has_file: 파일 여부
            message: 사용자 메시지

        Returns:
            RequestType: 결정된 요청 타입
        """
        # 이미지가 있으면 비전 분석
        if has_file:
            return RequestType.VISION

        # 문서 생성 키워드 확인
        if message and any(keyword in message for keyword in DOCUMENT_KEYWORDS):
            return RequestType.DOCUMENT

        # 기본값: 질의응답
        return RequestType.QA

    @staticmethod
    def should_use_default_prompt(message: Optional[str]) -> bool:
        """
        메시지가 없으면 기본 프롬프트 사용 여부 판단

        Args:
            message: 사용자 메시지

        Returns:
            bool: 기본 프롬프트 사용 여부
        """
        return not (message and message.strip())

