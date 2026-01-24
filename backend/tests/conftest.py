"""
pytest 설정 및 공통 픽스처
"""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """테스트 클라이언트 픽스처"""
    return TestClient(app)


@pytest.fixture
def sample_image_base64():
    """샘플 이미지 Base64 (1x1 PNG)"""
    # 1x1 투명 PNG
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


@pytest.fixture
def sample_message():
    """샘플 메시지"""
    return "안전모 착용 의무는?"
