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
        buffer_size: int = 200,
    ) -> AsyncGenerator[str, None]:
        """
        텍스트 조각을 모아서 JSON으로 변환하여 전송

        기능:
        - ✅ 권장 4: 하트비트 추가 (연결 유지)
        - ✅ 권장 5: 동적 버퍼 크기 조정 (적응형)

        Args:
            generator: 텍스트 조각 제너레이터
            buffer_size: 한 번에 모을 문자 수 (기본값: 200자)

        Yields:
            JSON 형식의 버퍼링된 텍스트 + 종료 신호
        """
        buffer = ""
        chunk_count = 0
        total_received = 0
        heartbeat_counter = 0
        adaptive_buffer_size = buffer_size

        try:
            async for text in generator:
                buffer += text
                total_received += len(text)
                heartbeat_counter += 1

                # ✅ 권장 5: 동적 버퍼 크기 조정
                # 청크가 증가하면 버퍼 크기도 증가 (최대 500자)
                if chunk_count > 2:
                    adaptive_buffer_size = min(buffer_size * 2, 500)

                # 버퍼가 충분히 차면 전송
                if len(buffer) >= adaptive_buffer_size:
                    json_data = json.dumps(
                        {"type": "text", "content": buffer},
                        ensure_ascii=False
                    )
                    yield json_data
                    chunk_count += 1
                    buffer = ""
                    heartbeat_counter = 0

                # ✅ 권장 4: 하트비트 추가 (연결 유지, 약 1초마다)
                # 30번 이터레이션 = 약 1초 (Claude 토큰 속도 기준)
                if heartbeat_counter >= 30 and len(buffer) > 0 and len(buffer) < adaptive_buffer_size:
                    heartbeat = json.dumps(
                        {"type": "heartbeat", "content": ""},
                        ensure_ascii=False
                    )
                    yield heartbeat
                    heartbeat_counter = 0
                    logger.debug("💓 하트비트 전송 (연결 유지)")

            # 남은 버퍼 전송 (중요: 마지막 조각)
            if buffer:
                json_data = json.dumps(
                    {"type": "text", "content": buffer},
                    ensure_ascii=False
                )
                yield json_data
                chunk_count += 1

            # 명시적 종료 신호
            done_signal = json.dumps(
                {
                    "type": "done",
                    "content": "",
                    "total_chunks": chunk_count,
                    "total_chars": total_received,
                    "adaptive_buffer_used": adaptive_buffer_size
                },
                ensure_ascii=False
            )
            yield done_signal

            logger.info(
                f"✅ 스트림 완료: {chunk_count}개 청크, "
                f"총 {total_received}자, "
                f"버퍼 크기: {adaptive_buffer_size}자"
            )

        except Exception as e:
            logger.error(f"❌ 버퍼링 중 에러: {e}")
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

        # 버퍼링하여 JSON으로 변환 (200자 단위)
        async for json_chunk in self._buffer_and_json(raw_generator(), buffer_size=200):
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

        # 버퍼링하여 JSON으로 변환 (문서는 250자 단위)
        async for json_chunk in self._buffer_and_json(raw_generator(), buffer_size=250):
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

        # 버퍼링하여 JSON으로 변환 (200자 단위)
        async for json_chunk in self._buffer_and_json(raw_generator(), buffer_size=200):
            yield json_chunk

