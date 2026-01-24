"""
ChromaDB 초기화 스크립트

사용법:
    python scripts/reset_db.py
    python scripts/reset_db.py --confirm
"""
import sys
import shutil
from pathlib import Path
import argparse

CHROMA_DB_PATH = Path("safety_db")


def reset_database(confirm: bool = False):
    """ChromaDB 완전 삭제"""

    if not CHROMA_DB_PATH.exists():
        print("❌ DB가 존재하지 않습니다.")
        return

    print("=" * 60)
    print("⚠️  ChromaDB 초기화")
    print("=" * 60)
    print(f"경로: {CHROMA_DB_PATH}")

    if not confirm:
        response = input("\n정말로 DB를 삭제하시겠습니까? (yes/no): ")
        if response.lower() != "yes":
            print("❌ 취소되었습니다.")
            return

    try:
        shutil.rmtree(CHROMA_DB_PATH)
        print(f"✅ DB 삭제 완료: {CHROMA_DB_PATH}")
    except Exception as e:
        print(f"❌ DB 삭제 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChromaDB 초기화")
    parser.add_argument(
        "--confirm", action="store_true", help="확인 없이 바로 삭제"
    )
    args = parser.parse_args()

    reset_database(args.confirm)
