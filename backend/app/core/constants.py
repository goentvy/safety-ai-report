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

# AI 모델 설정
MODEL_CONFIG = {
    "vision": {
        "max_tokens": 1500,
        "temperature": 0.7,
    },
    "document": {
        "max_tokens": 3000,
        "temperature": 0.5,
    },
    "qa": {
        "max_tokens": 2048,
        "temperature": 0.3,
    },
}

# 시스템 프롬프트
SYSTEM_PROMPTS = {
    "vision": (
        "당신은 현장 안전 점검관입니다. 산업안전보건법, 시행령/시행규칙, "
        "안전보건기준에 관한 규칙을 근거로 판단하세요. "
        "가능하면 관련 조항/별표 번호를 함께 제시하고 법적 책임 면책 문구를 마지막에 포함하세요."
    ),
    "document": "당신은 안전 행정 전문가입니다. 마크다운 형식으로 문서를 작성하세요.",
    "qa": "산업안전보건법 전문가입니다. 법령 근거로 답변하세요.",
}

# 기본 비전 프롬프트
DEFAULT_VISION_PROMPT = (
    "사진만 제공되어도 대한민국 산업안전보건 기준과 안전보건기준에 관한 규칙을 우선 적용하여 점검하세요. "
    "사람이 있으면 1) 보호구 착용 여부 2) 위반 가능성 3) 즉시/근본 조치 4) 관련 규정(조/별표) 출처를 항목별로 제시하세요. "
    "사람이 없으면 작업환경과 설비 위험요인을 기준(난간 높이, 개구부 가림, 비계 발판, 조도 등)으로 점검하고 출처를 명시하세요. "
    "사진만으로 확정할 수 없는 경우는 추정과 추가 확인 항목을 분리해 작성하세요."
)

# 문서 생성 키워드
DOCUMENT_KEYWORDS = ["작성", "체크리스트", "표", "위험성평가", "만들어"]

