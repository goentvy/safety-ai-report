"""
API 요청/응답 스키마 정의
"""
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# 응답 스키마
# ============================================================================

class BaseResponse(BaseModel):
    """기본 응답 스키마"""
    status: Literal["success", "fail"] = Field(..., description="처리 상태")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success"
            }
        }


class VisionResponse(BaseResponse):
    """이미지 분석 응답"""
    type: Literal["vision"] = Field(default="vision", description="응답 타입")
    content: str = Field(..., description="분석 결과 텍스트")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "vision",
                "content": "안전모 미착용이 확인되었습니다. 산업안전보건기준에 관한 규칙 제38조...",
                "status": "success"
            }
        }


class DocumentResponse(BaseResponse):
    """문서 생성 응답"""
    type: Literal["document"] = Field(default="document", description="응답 타입")
    content: str = Field(..., description="생성된 문서 (마크다운 형식)")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "document",
                "content": "# 안전 점검 체크리스트\n\n1. 보호구 착용 여부\n...",
                "status": "success"
            }
        }


class QAResponse(BaseResponse):
    """질의응답 응답"""
    type: Literal["qa"] = Field(default="qa", description="응답 타입")
    content: str = Field(..., description="질문에 대한 답변")
    source_docs: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="참조된 문서 메타데이터 (RAG 사용 시)"
    )
    model_used: Optional[str] = Field(default=None, description="사용된 AI 모델")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "qa",
                "content": "산업안전보건법 제38조에 따르면...",
                "source_docs": [],
                "model_used": "claude-sonnet-4-5",
                "status": "success"
            }
        }


class ErrorResponse(BaseResponse):
    """에러 응답"""
    type: Literal["error"] = Field(default="error", description="응답 타입")
    status: Literal["fail"] = Field(default="fail", description="실패 상태")
    content: str = Field(..., description="에러 메시지")
    error_code: Optional[str] = Field(default=None, description="에러 코드")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "error",
                "status": "fail",
                "content": "파일 크기가 10MB를 초과합니다",
                "error_code": "FILE_TOO_LARGE"
            }
        }


# ============================================================================
# 기타 스키마
# ============================================================================

class UploadResponse(BaseModel):
    """파일 업로드 응답"""
    status: str
    message: str
    db_path: Optional[str] = None


class RetrievalResult(BaseModel):
    """RAG 검색 결과"""
    query: str
    results: Any


class RiskAnalysisRequest(BaseModel):
    """위험성 평가 요청"""
    image_base64: Optional[str] = None
    context: Optional[str] = None

