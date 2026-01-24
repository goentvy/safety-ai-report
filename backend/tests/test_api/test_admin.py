"""
Admin API 테스트
"""
import pytest
from fastapi import status


def test_admin_health(client):
    """관리자 헬스체크 테스트"""
    response = client.get("/admin/health")
    assert response.status_code == status.HTTP_200_OK
    assert "status" in response.json()


def test_admin_stats(client):
    """관리자 통계 테스트"""
    response = client.get("/admin/stats")
    # DB가 없을 수 있으므로 200 또는 404
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


def test_admin_reset_without_confirm(client):
    """확인 없이 DB 초기화 시도"""
    response = client.post("/admin/reset")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
