"""
Safety AI Agent - 산업안전 통합 AI 서비스
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 내부 모듈
from app.core.constants import MODEL_ID
from app.core.validation import validate_environment, validate_optional_environment
from app.core.logging_config import setup_logging, get_logger
from app.services.rag_service import get_rag_service
from app.api import admin, chat

# 환경변수 로드
load_dotenv()

# 로깅 설정
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"), log_file=os.getenv("LOG_FILE", None)
)
logger = get_logger(__name__)

# 환경변수 검증 (앱 시작 시 즉시 실행)
try:
    validate_environment()
    validate_optional_environment()
except RuntimeError as e:
    logger.critical(f"❌ 환경변수 검증 실패: {e}")
    raise

# FastAPI 앱 초기화
app = FastAPI(
    title="Safety AI Agent",
    description="산업안전보건 통합 AI 분석 서비스 - 이미지 분석, 문서 생성, 질의응답",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RAG 서비스 초기화 (선택적, 오류 발생 시 경고만)
try:
    get_rag_service()
    logger.info("✅ RAG 서비스 초기화 완료")
except Exception as e:
    logger.warning(f"⚠️  RAG 서비스 초기화 실패: {e}")
    logger.warning("   질의응답 시 법령 검색 기능이 비활성화됩니다.")

logger.info(f"✅ Safety AI Agent 시작 완료 (모델: {MODEL_ID})")

# ============================================================================
# API 라우터 등록
# ============================================================================

# 관리자 API
app.include_router(admin.router)

# Chat API
app.include_router(chat.router)

# ============================================================================
# 기본 엔드포인트
# ============================================================================


@app.get("/")
async def root():
    """헬스체크 엔드포인트"""
    return {"status": "healthy", "service": "Safety AI Agent", "version": "2.0.0"}
