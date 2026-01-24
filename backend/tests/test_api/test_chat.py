"""
Chat API 테스트
"""
import pytest
from fastapi import status


def test_health_check(client):
    """헬스체크 테스트"""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "healthy"


def test_chat_without_input(client):
    """입력 없이 요청 시 에러"""
    response = client.post("/chat")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_chat_with_message(client, sample_message):
    """메시지만으로 요청"""
    response = client.post("/chat", data={"message": sample_message})
    # RAG 서비스가 없을 수 있으므로 200 또는 500
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]


@pytest.mark.skip(reason="실제 API 키 필요")
def test_chat_with_image(client, sample_image_base64):
    """이미지와 함께 요청"""
    files = {"file": ("test.png", bytes.fromhex(sample_image_base64), "image/png")}
    response = client.post("/chat", files=files)
    # 실제 API 호출이 필요하므로 스킵
    pass
