"""
Chat Service - 스트리밍 기반 AI 응답 처리
"""
import anthropic
import json
from typing import AsyncGenerator
from anthropic.types import MessageParam
from app.core.constants import MODEL_ID, MODEL_CONFIG, SYSTEM_PROMPTS
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ChatService:
    """Anthropic API를 이용한 스트리밍 응답 처리"""

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    async def _buffer_and_json(
        self,
        generator: AsyncGenerator[str, None],
        buffer_size: int = 50,
    ) -> AsyncGenerator[str, None]:
        """
        텍스트 조각을 모아서 JSON으로 변환하여 전송

        Args:
            generator: 텍스트 조각 제너레이터
            buffer_size: 한 번에 모을 문자 수 (기본값: 50자)

        Yields:
            JSON 형식의 버퍼링된 텍스트
        """
        buffer = ""
        try:
            async for text in generator:
                buffer += text
                # 버퍼가 충분히 차면 전송
                if len(buffer) >= buffer_size:
                    json_data = json.dumps(
                        {"type": "text", "content": buffer},
                        ensure_ascii=False
                    )
                    yield json_data
                    buffer = ""

            # 남은 버퍼 전송
            if buffer:
                json_data = json.dumps(
                    {"type": "text", "content": buffer},
                    ensure_ascii=False
                )
                yield json_data
        except Exception as e:
            logger.error(f"버퍼링 중 에러: {e}")
            error_json = json.dumps(
                {"type": "error", "content": str(e)},
                ensure_ascii=False
            )
            yield error_json

    async def stream_vision_analysis(
        self,
        base64_image: str,
        media_type: str,
        user_prompt: str,
    ) -> AsyncGenerator[str, None]:
        """
        이미지 분석 스트리밍 응답 (JSON 버퍼링)

        Args:
            base64_image: Base64로 인코딩된 이미지
            media_type: 이미지 타입 (image/jpeg, image/png 등)
            user_prompt: 사용자 프롬프트

        Yields:
            JSON 형식의 버퍼링된 응답
        """
        messages: list[MessageParam] = [
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
                    {"type": "text", "text": user_prompt},
                ],
            }
        ]

        # 원본 텍스트 제너레이터
        async def raw_generator():
            with self.client.messages.stream(
                model=MODEL_ID,
                max_tokens=MODEL_CONFIG["vision"]["max_tokens"],
                temperature=MODEL_CONFIG["vision"]["temperature"],
                system=SYSTEM_PROMPTS["vision"],
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield text

        # 버퍼링하여 JSON으로 변환
        async for json_chunk in self._buffer_and_json(raw_generator(), buffer_size=50):
            yield json_chunk

    async def stream_document_generation(
        self,
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        """
        문서 생성 스트리밍 응답 (JSON 버퍼링)

        Args:
            user_message: 사용자 메시지

        Yields:
            JSON 형식의 버퍼링된 응답
        """
        messages: list[MessageParam] = [{"role": "user", "content": user_message}]

        # 원본 텍스트 제너레이터
        async def raw_generator():
            with self.client.messages.stream(
                model=MODEL_ID,
                max_tokens=MODEL_CONFIG["document"]["max_tokens"],
                temperature=MODEL_CONFIG["document"]["temperature"],
                system=SYSTEM_PROMPTS["document"],
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield text

        # 버퍼링하여 JSON으로 변환
        async for json_chunk in self._buffer_and_json(raw_generator(), buffer_size=60):
            yield json_chunk

    async def stream_qa(
        self,
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        """
        질의응답 스트리밍 응답 (JSON 버퍼링)

        Args:
            user_message: 사용자 질문

        Yields:
            JSON 형식의 버퍼링된 응답
        """
        messages: list[MessageParam] = [{"role": "user", "content": user_message}]

        # 원본 텍스트 제너레이터
        async def raw_generator():
            with self.client.messages.stream(
                model=MODEL_ID,
                max_tokens=MODEL_CONFIG["qa"]["max_tokens"],
                temperature=MODEL_CONFIG["qa"]["temperature"],
                system=SYSTEM_PROMPTS["qa"],
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield text

        # 버퍼링하여 JSON으로 변환
        async for json_chunk in self._buffer_and_json(raw_generator(), buffer_size=50):
            yield json_chunk

