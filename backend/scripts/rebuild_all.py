"""
전체 파이프라인 재구축 (데이터 수집 → 전처리 → 벡터 DB 구축)

사용법:
    python scripts/rebuild_all.py
    python scripts/rebuild_all.py --skip-collect  # 수집 건너뛰기
"""
import sys
import subprocess
import argparse
from pathlib import Path

SCRIPTS = {
    "collect": "scripts/collect_law_data.py",
    "preprocess": "scripts/preprocess_laws.py",
    "build_db": "scripts/build_vectordb.py",
}


def run_script(script_name: str, script_path: str) -> bool:
    """스크립트 실행"""
    print("\n" + "=" * 60)
    print(f"▶️  {script_name} 시작: {script_path}")
    print("=" * 60)

    try:
        result = subprocess.run(
            ["python", script_path], check=True, capture_output=False
        )
        print(f"✅ {script_name} 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {script_name} 실패: {e}")
        return False


def rebuild_all(skip_collect: bool = False):
    """전체 재구축 파이프라인"""
    print("=" * 60)
    print("🔄 전체 파이프라인 재구축")
    print("=" * 60)

    steps = [
        ("데이터 수집", SCRIPTS["collect"]),
        ("데이터 전처리", SCRIPTS["preprocess"]),
        ("벡터 DB 구축", SCRIPTS["build_db"]),
    ]

    if skip_collect:
        print("⏭️  데이터 수집 건너뛰기")
        steps = steps[1:]

    for step_name, script_path in steps:
        if not Path(script_path).exists():
            print(f"❌ 스크립트 없음: {script_path}")
            sys.exit(1)

        success = run_script(step_name, script_path)
        if not success:
            print(f"\n❌ {step_name}에서 실패했습니다.")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ 전체 재구축 완료!")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="전체 파이프라인 재구축")
    parser.add_argument(
        "--skip-collect", action="store_true", help="데이터 수집 건너뛰기"
    )
    args = parser.parse_args()

    rebuild_all(skip_collect=args.skip_collect)
