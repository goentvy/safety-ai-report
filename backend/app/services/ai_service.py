"""
AI 서비스 - Anthropic Claude API 호출
"""
import os
import base64
from typing import List, Optional
import anthropic
from anthropic.types import MessageParam, TextBlock, ContentBlock

from app.core.constants import (
    MODEL_ID,
    MODEL_CONFIG,
    SYSTEM_PROMPTS,
    DEFAULT_VISION_PROMPT,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class AIService:
    """AI 서비스 클래스"""

    def __init__(self):
        """AI 서비스 초기화"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model_id = MODEL_ID

    def extract_full_text(self, content_blocks: List[ContentBlock]) -> str:
        """Anthropic 응답 블록에서 텍스트만 추출"""
        return "".join(
            [block.text for block in content_blocks if isinstance(block, TextBlock)]
        )

    async def analyze_image(
        self,
        image_base64: str,
        media_type: str,
        user_text: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        이미지 분석 수행

        Args:
            image_base64: Base64 인코딩된 이미지
            media_type: 이미지 미디어 타입
            user_text: 사용자 질문 (선택)
            system_prompt: 시스템 프롬프트 (선택)

        Returns:
            분석 결과 텍스트
        """
        user_prompt = (user_text or "").strip() or DEFAULT_VISION_PROMPT
        system = system_prompt or SYSTEM_PROMPTS["vision"]

        messages: List[MessageParam] = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64,
                        },
                    },
                    {"type": "text", "text": user_prompt},
                ],
            }
        ]

        response = self.client.messages.create(
            model=self.model_id,
            max_tokens=MODEL_CONFIG["vision"]["max_tokens"],
            temperature=MODEL_CONFIG["vision"]["temperature"],
            system=system,
            messages=messages,
        )

        return self.extract_full_text(response.content)

    async def generate_document(self, request_text: str) -> str:
        """
        문서 생성 수행

        Args:
            request_text: 문서 생성 요청 텍스트

        Returns:
            생성된 문서 (마크다운 형식)
        """
        messages: List[MessageParam] = [{"role": "user", "content": request_text}]

        response = self.client.messages.create(
            model=self.model_id,
            max_tokens=MODEL_CONFIG["document"]["max_tokens"],
            temperature=MODEL_CONFIG["document"]["temperature"],
            system=SYSTEM_PROMPTS["document"],
            messages=messages,
        )

        return self.extract_full_text(response.content)

    async def answer_question(
        self, question: str, system_prompt: Optional[str] = None
    ) -> str:
        """
        질의응답 수행

        Args:
            question: 질문 텍스트
            system_prompt: 시스템 프롬프트 (선택, RAG 컨텍스트 포함 가능)

        Returns:
            답변 텍스트
        """
        system = system_prompt or SYSTEM_PROMPTS["qa"]
        messages: List[MessageParam] = [{"role": "user", "content": question}]

        response = self.client.messages.create(
            model=self.model_id,
            max_tokens=MODEL_CONFIG["qa"]["max_tokens"],
            temperature=MODEL_CONFIG["qa"]["temperature"],
            system=system,
            messages=messages,
        )

        return self.extract_full_text(response.content)


# 싱글톤 인스턴스
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """AI 서비스 싱글톤 인스턴스 반환"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
