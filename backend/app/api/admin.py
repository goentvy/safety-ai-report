"""
관리자 API

엔드포인트:
- GET  /admin/health - DB 상태 확인
- GET  /admin/stats - 통계 정보
- POST /admin/rebuild - DB 재구축 (백그라운드)
- POST /admin/reset - DB 초기화
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pathlib import Path
import chromadb
from chromadb.config import Settings
import subprocess
import shutil
from typing import Dict, Any

router = APIRouter(prefix="/admin", tags=["Admin"])

CHROMA_DB_PATH = Path("safety_db")
COLLECTION_NAME = "safety_laws"


def get_db_stats() -> Dict[str, Any]:
    """DB 통계 조회"""
    try:
        client = chromadb.PersistentClient(
            path=str(CHROMA_DB_PATH),
            settings=Settings(anonymized_telemetry=False),
        )
        collection = client.get_collection(name=COLLECTION_NAME)

        # 전체 개수
        total_count = collection.count()

        # 카테고리별 개수 (카테고리 1)
        try:
            cat1_results = collection.get(where={"category": "1"}, limit=10000)
            cat1_count = len(cat1_results["ids"]) if cat1_results["ids"] else 0
        except Exception:
            cat1_count = 0

        return {
            "db_exists": True,
            "total_documents": total_count,
            "category_1_count": cat1_count,
            "db_path": str(CHROMA_DB_PATH),
        }
    except Exception as e:
        return {"db_exists": False, "error": str(e)}


@router.get("/health")
async def health_check():
    """DB 상태 확인"""
    stats = get_db_stats()

    if not stats.get("db_exists"):
        return {
            "status": "unhealthy",
            "message": "DB가 존재하지 않거나 손상되었습니다",
            "details": stats,
        }

    return {
        "status": "healthy",
        "message": "DB 정상 작동",
        "details": stats,
    }


@router.get("/stats")
async def get_stats():
    """통계 정보"""
    stats = get_db_stats()

    if not stats.get("db_exists"):
        raise HTTPException(status_code=404, detail="DB가 존재하지 않습니다")

    return stats


def rebuild_db_task():
    """DB 재구축 백그라운드 태스크"""
    try:
        subprocess.run(
            ["python", "scripts/rebuild_all.py", "--skip-collect"], check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"재구축 실패: {e}")


@router.post("/rebuild")
async def rebuild_database(background_tasks: BackgroundTasks):
    """
    DB 재구축 (백그라운드)

    - 기존 데이터 유지
    - 전처리 → 벡터 DB 재구축
    - 백그라운드 실행 (응답 즉시 반환)
    """
    background_tasks.add_task(rebuild_db_task)

    return {
        "status": "started",
        "message": "DB 재구축이 백그라운드에서 시작되었습니다",
        "note": "완료까지 10-15분 소요될 수 있습니다",
    }


@router.post("/reset")
async def reset_database(confirm: bool = False):
    """
    DB 완전 초기화

    ⚠️ 주의: 모든 데이터가 삭제됩니다

    Query Params:
        - confirm: true 설정 시 확인 없이 삭제
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="confirm=true 파라미터를 추가하여 삭제를 확인해주세요",
        )

    if not CHROMA_DB_PATH.exists():
        raise HTTPException(status_code=404, detail="DB가 존재하지 않습니다")

    try:
        shutil.rmtree(CHROMA_DB_PATH)
        return {
            "status": "success",
            "message": "DB가 성공적으로 삭제되었습니다",
            "path": str(CHROMA_DB_PATH),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB 삭제 실패: {str(e)}")
