"""
RAG 검색 테스트 (법령 우선)

사용법:
    python scripts/test_rag.py
"""
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rag_service import get_rag_service


def main():
    print("=" * 60)
    print("RAG 검색 테스트 (법령 우선)")
    print("=" * 60)

    try:
        rag_service = get_rag_service()
    except Exception as e:
        print(f"❌ RAG 서비스 초기화 실패: {e}")
        print("   ChromaDB가 구축되었는지 확인하세요.")
        print("   실행: python scripts/build_vectordb.py")
        return

    test_queries = [
        "안전모 착용 의무는?",
        "고소작업 시 안전조치는?",
        "화학물질 취급 기준은?",
        "사업주의 안전보건 조치 의무",
        "건설현장 추락방지 조치",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"🔍 쿼리: '{query}'")
        print('='*60)

        try:
            result = rag_service.search_with_category_priority(query, top_k=3)

            print(f"✅ 검색 방식: {result['search_type']}")
            print(f"💬 {result['message']}")

            if result['search_type'] == 'fallback':
                print(f"   (법령 검색 결과: {result.get('law_results_count', 0)}개)")

            print(f"\n📋 상위 3개 결과:")

            for idx, item in enumerate(result['results'], 1):
                metadata = item.get("metadata", {})
                title = metadata.get("title", "제목 없음")
                category = metadata.get("category", "unknown")
                text = item.get("text", "")
                distance = item.get("distance", 0)
                similarity = 1 - distance if distance else 0

                print(f"\n  [{idx}] {title}")
                print(f"      📁 카테고리: {category}")
                print(f"      📊 유사도: {similarity:.2%}")
                print(f"      📝 내용: {text[:150]}...")

        except Exception as e:
            print(f"❌ 검색 실패: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("✅ 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
