import anthropic
import os
import base64
from typing import Optional, List, cast
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from anthropic.types import MessageParam, TextBlock

# 환경변수 로드
load_dotenv()

app = FastAPI(title="Safety AI Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST 등 모든 메소드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL_ID = "claude-3-5-sonnet-20241022"  # 공식 모델 ID 사용 권장

# --- 헬퍼 함수: 응답 블록에서 텍스트만 안전하게 추출 ---
def extract_full_text(content_blocks: list) -> str:
    """
    Anthropic 응답 블록 리스트에서 TextBlock인 요소들의 text만 합쳐서 반환합니다.
    Pylance의 'attribute access' 경고를 방지합니다.
    """
    return "".join([block.text for block in content_blocks if isinstance(block, TextBlock)])

@app.post("/chat")
async def integrated_chat(
    file: Optional[UploadFile] = File(None),
    message: str = Form(...)
):
    try:
        # 1. 사진 분석 로직 (파일이 존재할 때)
        if file:
            contents = await file.read()
            base64_image = base64.b64encode(contents).decode("utf-8")

            vision_messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": file.content_type or "image/jpeg",
                                "data": base64_image,
                            },
                        },
                        {"type": "text", "text": message}
                    ],
                }
            ]

            response = client.messages.create(
                model=MODEL_ID,
                max_tokens=1500,
                system="당신은 현장 안전 점검관입니다. 사진에 사람이 있다면 1)보호구 2)위반소지 3)조치를 리스트로 답하고, 사람이 없다면 '분석 대상인 작업자가 사진에 탐지되지 않았습니다.'라고 답하세요.",
                messages=cast(List[MessageParam], vision_messages)
            )
            
            return {
                "type": "vision",
                "content": extract_full_text(response.content),
                "status": "success"
            }

        # 2. 문서 생성 로직 (특정 키워드 포함 시)
        document_keywords = ["작성", "체크리스트", "표", "위험성평가", "만들어"]
        if any(keyword in message for keyword in document_keywords):
            doc_messages = [{"role": "user", "content": message}]
            
            response = client.messages.create(
                model=MODEL_ID,
                max_tokens=3000,
                system="당신은 안전 행정 전문가입니다. 마크다운 형식으로 문서를 작성하세요.",
                messages=cast(List[MessageParam], doc_messages)
            )
            return {
                "type": "document",
                "content": extract_full_text(response.content),
                "status": "success"
            }

        # 3. 일반 질의응답 (그 외)
        qa_messages = [{"role": "user", "content": message}]
        
        response = client.messages.create(
            model=MODEL_ID,
            max_tokens=2048,
            system="산업안전보건법 전문가입니다. 법령 근거로 답변하세요.",
            messages=cast(List[MessageParam], qa_messages)
        )
        return {
            "type": "qa",
            "content": extract_full_text(response.content),
            "status": "success"
        }

    except Exception as e:
        return {
            "type": "error",
            "content": str(e),
            "status": "fail"
        }