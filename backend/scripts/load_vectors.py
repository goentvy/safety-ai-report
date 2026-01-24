"""
전처리된 법령 데이터를 벡터 저장소에 로드하는 스크립트

사용법:
    python scripts/load_vectors.py [processed_data_file.json]
"""
import sys
from pathlib import Path
from app.services.rag_service import get_rag_service

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("법령 데이터 벡터 저장소 로드")
    print("=" * 60)

    try:
        rag_service = get_rag_service()

        # 파일 경로 지정 (선택적)
        processed_file = sys.argv[1] if len(sys.argv) > 1 else None

        print("\n📥 벡터 저장소에 데이터 로드 중...")
        stored_count = rag_service.load_and_store_laws(processed_file)

        print(f"\n✅ 완료! 총 {stored_count}개 청크가 저장되었습니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
