import anthropic
import os
import base64
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Safety AI Agent")
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL_ID = "claude-sonnet-4-5"  # 스크린샷에서 확인한 활성 모델 ID


@app.post("/chat")
async def integrated_chat(
        file: Optional[UploadFile] = File(None),
        message: str = Form(...)
):
    try:
        # 1. 사진 분석 로직 (파일이 존재할 때)
        if file:
            contents = await file.read()
            base64_image = base64.b64encode(contents).decode('utf-8')

            response = client.messages.create(
                model=MODEL_ID,  # claude-4-sonnet
                max_tokens=1500,
                system="""당신은 현장 안전 점검관입니다. 
                사진에 사람이 있다면 1)보호구 2)위반소지 3)조치를 리스트로 답하고, 
                사람이 없다면 "분석 대상인 작업자가 사진에 탐지되지 않았습니다."라고 답하세요.""",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image",
                         "source": {"type": "base64", "media_type": file.content_type, "data": base64_image}},
                        {"type": "text", "text": message}
                    ]
                }]
            )
            return {
                "type": "vision",
                "content": response.content[0].text,
                "status": "success"
            }

        # 2. 문서 생성 로직 (특정 키워드 포함 시)
        document_keywords = ["작성", "체크리스트", "표", "위험성평가", "만들어"]
        if any(keyword in message for keyword in document_keywords):
            response = client.messages.create(
                model=MODEL_ID,
                max_tokens=3000,
                system="당신은 안전 행정 전문가입니다. 마크다운 형식으로 문서를 작성하세요.",
                messages=[{"role": "user", "content": message}]
            )
            return {
                "type": "document",
                "content": response.content[0].text,
                "status": "success"
            }

        # 3. 일반 질의응답 (그 외)
        response = client.messages.create(
            model=MODEL_ID,
            max_tokens=2048,
            system="산업안전보건법 전문가입니다. 법령 근거로 답변하세요.",
            messages=[{"role": "user", "content": message}]
        )
        return {
            "type": "qa",
            "content": response.content[0].text,
            "status": "success"
        }

    except Exception as e:
        # 에러 발생 시 응답 구조
        return {
            "type": "error",
            "content": str(e),
            "status": "fail"
        }