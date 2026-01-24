"""
RAG 서비스 테스트
"""

import pytest
from app.services.rag_service import RAGService, get_rag_service


@pytest.mark.skip(reason="ChromaDB 및 OpenAI API 키 필요")
def test_rag_service_initialization():
    """RAG 서비스 초기화 테스트"""
    service = RAGService()
    assert service is not None
    assert service.collection is not None


@pytest.mark.skip(reason="ChromaDB 및 OpenAI API 키 필요")
def test_rag_search():
    """RAG 검색 테스트"""
    service = get_rag_service()
    results = service.search_with_category_priority("안전모 착용", top_k=3)
    assert "results" in results
    assert "search_type" in results
