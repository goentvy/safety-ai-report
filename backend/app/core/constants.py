"""
애플리케이션 상수 정의
"""

# 모델 설정
MODEL_ID = "claude-sonnet-4-5"

# 파일 크기 제한 (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# 지원 이미지 타입
SUPPORTED_IMAGE_TYPES = {
    "image/jpeg": "image/jpeg",
    "image/jpg": "image/jpeg",
    "image/png": "image/png",
    "image/gif": "image/gif",
    "image/webp": "image/webp",
}

# AI 모델 설정 (토큰 최소화)
MODEL_CONFIG = {
    "vision": {
        "max_tokens": 800,
        "temperature": 0.7,
    },
    "document": {
        "max_tokens": 1500,
        "temperature": 0.5,
    },
    "qa": {
        "max_tokens": 800,
        "temperature": 0.3,
    },
}

# 시스템 프롬프트 (최소화)
SYSTEM_PROMPTS = {
    "vision": "산업안전보건법 기준으로 점검. 위반사항, 조치, 규정(조항) 명시.",
    "document": "마크다운 형식으로 작성.",
    "qa": "산업안전보건법 근거로 답변.",
}

# 기본 비전 프롬프트 (최소화)
DEFAULT_VISION_PROMPT = (
    "산업안전보건 기준으로 점검: 보호구 착용, 위반 가능성, 조치, 규정 출처 제시. "
    "사람 없으면 설비 위험요인과 기준(난간/조도 등) 점검."
)

# 문서 생성 키워드
DOCUMENT_KEYWORDS = ["작성", "체크리스트", "표", "위험성평가", "만들어"]

