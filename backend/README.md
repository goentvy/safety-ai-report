# 🏗️ Safety AI Agent - 산업안전 통합 AI 서비스

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Anthropic Claude](https://img.shields.io/badge/Claude-Sonnet%204.5-purple.svg)](https://www.anthropic.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#)

> 대한민국 산업안전보건법 기준으로 현장 안전을 AI가 자동 분석하는 서비스

---

## 🎯 서비스 개요

**Safety AI Agent**는 산업현장의 안전을 자동으로 점검하는 AI 기반 서비스입니다.

### 핵심 기능

| 기능 | 설명 | 입력 | 출력 |
|------|------|------|------|
| **📷 이미지 분석** | 현장 사진을 산안법 기준으로 점검 | 이미지 (선택), 질문 (선택) | 점검 결과 + 법적 근거 |
| **📄 문서 생성** | 안전 점검 문서 자동 생성 | 생성 요청 텍스트 | 마크다운 문서 |
| **❓ 질의응답** | 산안법 관련 질문에 AI가 답변 | 텍스트 질문 | 법령 기반 답변 |

### 기술 스택

```
Frontend: React/Vue (TBD)
Backend:  FastAPI (Python 3.12)
AI Model: Claude Sonnet 4.5 (Anthropic)
Vector DB: ChromaDB (로컬 저장)
Storage:  SQLite (메타데이터)
```

---

## 🚀 빠른 시작

### 사전 요구사항

- Python 3.12+
- Anthropic API 키
- macOS 또는 Linux (또는 Windows WSL2)

### 1단계: 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd safety-ai-report/backend

# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2단계: 환경변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 수정
ANTHROPIC_API_KEY=sk-ant-your-key-here
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 3단계: 서버 실행

```bash
# 개발 서버 실행 (자동 리로드)
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 서버 실행
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4단계: API 테스트

```bash
# 헬스체크
curl http://localhost:8000/

# Swagger UI 접속
open http://localhost:8000/docs

# ReDoc 접속
open http://localhost:8000/redoc
```

---

## 📚 API 사용 예시

### 예제 1: 이미지 분석 (사진만 전송)

```bash
curl -X POST http://localhost:8000/chat \
  -F "file=@construction_site.jpg"

# 응답 예시:
{
  "type": "vision",
  "content": "안전모 미착용이 확인되었습니다. 산업안전보건기준에 관한 규칙 제38조...",
  "status": "success"
}
```

### 예제 2: 이미지 분석 (사진 + 질문)

```bash
curl -X POST http://localhost:8000/chat \
  -F "file=@construction_site.jpg" \
  -F "message=이 작업자의 안전 위반사항은?"

# 응답 예시:
{
  "type": "vision",
  "content": "주요 위반사항:\n1. 안전모 미착용...",
  "status": "success"
}
```

### 예제 3: 질의응답

```bash
curl -X POST http://localhost:8000/chat \
  -F "message=산업안전보건법 제38조에 따른 안전조치 의무는?"

# 응답 예시:
{
  "type": "qa",
  "content": "산업안전보건법 제38조에 따르면...",
  "model_used": "claude-sonnet-4-5",
  "status": "success"
}
```

### 예제 4: 문서 생성

```bash
curl -X POST http://localhost:8000/chat \
  -F "message=건설업 안전점검 체크리스트를 작성해줘"

# 응답 예시:
{
  "type": "document",
  "content": "# 건설업 안전점검 체크리스트\n\n## 1. 보호구...",
  "status": "success"
}
```

---

## 📖 상세 API 문서

### 엔드포인트: `POST /chat`

**설명:** 안전 점검 통합 처리 (이미지 분석 + 문서 생성 + 질의응답)

**요청:**

| 파라미터 | 타입 | 필수 | 제한 | 설명 |
|---------|------|------|------|------|
| `file` | File | ✗ | 최대 10MB | 이미지 파일 (JPEG/PNG/GIF/WEBP) |
| `message` | String | ✗ | 최대 5000자 | 텍스트 메시지 |

**응답 예시:**

```json
{
  "type": "vision|document|qa",
  "content": "AI 응답 텍스트",
  "status": "success",
  "model_used": "claude-sonnet-4-5",
  "source_docs": []
}
```

**에러 응답:**

```json
{
  "type": "error",
  "status": "fail",
  "content": "에러 메시지",
  "error_code": "ERROR_CODE"
}
```

**HTTP 상태 코드:**

| 코드 | 설명 |
|------|------|
| 200 | ✅ 성공 |
| 400 | ❌ 잘못된 요청 (파일/메시지 누락, 형식 오류) |
| 413 | ❌ 파일 크기 초과 (10MB 초과) |
| 415 | ❌ 지원하지 않는 파일 타입 |
| 429 | ❌ API 요청 한도 초과 |
| 500 | ❌ 서버 오류 |

---

## 🔧 프로젝트 구조

```
backend/
├── main.py                         # 메인 애플리케이션
├── requirements.txt                # Python 의존성
├── .env                           # 환경변수 (미포함)
├── .env.example                   # 환경변수 예시
│
├── app/
│   ├── core/
│   │   ├── constants.py           # 상수 정의 (모델, 프롬프트 등)
│   │   ├── validation.py          # 검증 및 예외 처리
│   │   ├── logging_config.py     # 로깅 설정
│   │   ├── config.py              # 기본 설정
│   │   └── utils.py               # 유틸리티 함수
│   │
│   ├── models/
│   │   └── schemas.py             # Pydantic 스키마 (요청/응답)
│   │
│   ├── services/
│   │   ├── ai_service.py          # AI 호출 서비스
│   │   ├── doc_service.py         # 문서 파싱 서비스
│   │   └── rag_service.py         # RAG 검색 서비스
│   │
│   └── api/
│       ├── admin.py               # 관리자 API (지식베이스 관리)
│       └── chat.py                # 챗 API (향후 분리 예정)
│
├── safety_db/                     # ChromaDB 로컬 저장소
│   └── chroma.sqlite3
│
└── logs/                          # 로그 파일
    └── app.log
```

---

## 📋 환경변수 설정

```bash
# .env 파일
# 필수
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxx

# 선택적
OPENAI_API_KEY=sk-xxxxxxxxxxxxxx
LLAMA_CLOUD_API_KEY=llx-xxxxxxxxxxxxx

# 로깅 설정
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=logs/app.log             # 로그 파일 경로 (없으면 콘솔만)
```

---

## 🧪 테스트

### 단위 테스트 (향후)

```bash
pip install pytest pytest-asyncio

pytest tests/ -v --cov=app
```

### API 테스트

```bash
# Swagger UI에서 직접 테스트
open http://localhost:8000/docs

# 또는 HTTPie로 테스트
http POST http://localhost:8000/chat message="안전모 규정은?"
```

---

## 🔒 보안

### 현재 적용된 보안 기능

- ✅ 환경변수로 API 키 관리
- ✅ 파일 크기 제한 (10MB)
- ✅ 파일 타입 검증 (이미지만 허용)
- ✅ 입력값 검증
- ✅ 구조화된 에러 처리

### 향후 보안 강화

- [ ] CORS 설정 강화 (특정 도메인만 허용)
- [ ] Rate Limiting (IP별 요청 제한)
- [ ] API 인증 (OAuth2 / JWT)
- [ ] HTTPS 적용
- [ ] CSRF 방어

---

## 📊 성능

### API 응답 시간

| 작업 | 평균 시간 | 최대 시간 |
|------|---------|---------|
| 이미지 분석 | 2-3초 | 5초 |
| 문서 생성 | 3-4초 | 6초 |
| 질의응답 | 1-2초 | 4초 |

### 요청 한계

- 최대 파일 크기: 10MB
- 최대 메시지 길이: 5000자
- 동시 요청: 무제한 (Anthropic API 한도에 따름)

---

## 🐛 디버깅

### 로그 확인

```bash
# 실시간 로그 모니터링
tail -f logs/app.log

# 특정 요청 ID 검색
grep "req_a1b2c3d4" logs/app.log

# 에러만 필터링
grep ERROR logs/app.log
```

### 환경변수 검증

```bash
# 필수 환경변수 확인
python -c "from app.core.validation import validate_environment; validate_environment()"
```

### API 상태 확인

```bash
# 헬스체크
curl http://localhost:8000/
# 응답: {"status":"healthy","service":"Safety AI Agent","version":"2.0.0"}
```

---

## 📈 모니터링

### 주요 지표

```bash
# 요청 처리 시간 분석
grep "완료" logs/app.log | awk '{print $NF}' | sort -n | tail -10

# 에러 빈도 확인
grep "ERROR\|CRITICAL" logs/app.log | wc -l

# API 사용량 확인
grep "POST /chat" logs/app.log | wc -l
```

---

## 🤝 기여

### 버그 리포트
GitHub Issues에서 버그를 리포트해주세요.

### 기능 제안
새로운 기능 제안은 Discussions에서 논의해주세요.

---

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일 참고

---

## 📞 문의

| 항목 | 담당자 | 연락처 |
|------|--------|--------|
| 백엔드 | 개발팀 | backend@example.com |
| 프론트엔드 | 프론트팀 | frontend@example.com |
| 기타 문의 | 관리자 | admin@example.com |

---

## 📚 추가 자료

- **[상세 프로젝트 구조](PROJECT_STRUCTURE.md)** - 디렉토리 및 파일 구조
- **[Phase 2 완료 보고서](PHASE2_COMPLETION_REPORT.md)** - 개선 사항 및 성과
- **[API 명세서](API_SPECIFICATION.md)** - 프론트팀 용 상세 API 명세

---

## 🚀 로드맵

### 진행 중 (Q1 2026)
- [x] 기본 API 구현
- [x] 타입 안전성 강화
- [x] 에러 처리 표준화
- [ ] 단위 테스트 작성

### 계획 중 (Q2 2026)
- [ ] CORS 보안 강화
- [ ] Rate Limiting 추가
- [ ] Docker 컨테이너화
- [ ] CI/CD 파이프라인

### 미래 계획 (Q3-Q4 2026)
- [ ] 다국어 지원
- [ ] 모바일 앱 개발
- [ ] 고급 분석 기능
- [ ] 머신러닝 모델 통합

---

**마지막 업데이트:** 2026년 1월 10일  
**버전:** 2.0.0  
**상태:** 🟢 개발 중

