# 🏗️ Safety AI Agent - 산업안전 통합 AI 서비스

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Anthropic Claude](https://img.shields.io/badge/Claude-Sonnet%204.5-purple.svg)](https://www.anthropic.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#)

> 대한민국 산업안전보건법 기준으로 현장 안전을 AI가 자동 분석하는 **RAG 기반** 서비스

---

## 🎯 서비스 개요

**Safety AI Agent**는 산업현장의 안전을 자동으로 점검하고, **법령 데이터베이스를 검색하여** 정확한 법적 근거를 제공하는 AI 기반 서비스입니다.

### 핵심 기능

| 기능 | 설명 | 입력 | 출력 |
|------|------|------|------|
| **📷 이미지 분석** | 현장 사진을 산안법 기준으로 점검 | 이미지 + 질문 (선택) | 점검 결과 + 법적 근거 + 출처 |
| **📄 문서 생성** | 안전 점검 문서 자동 생성 | 생성 요청 텍스트 | 마크다운 문서 |
| **❓ 질의응답 (RAG)** | 법령 DB 검색 후 답변 | 텍스트 질문 | 법령 기반 답변 + 출처 |

### 🆕 RAG (Retrieval-Augmented Generation) 시스템

- **법령 데이터베이스**: 산업안전보건법령 12,805개 청크 (9,052개 원본 문서)
- **벡터 검색**: OpenAI text-embedding-3-small (1536차원)
- **저장소**: ChromaDB (로컬 영구 저장)
- **검색 우선순위**: 법령(카테고리 1) → 전체 문서
- **데이터 출처**: 한국산업안전보건공단 공공 API

### 기술 스택

```
Frontend:   React/Vue (TBD)
Backend:    FastAPI (Python 3.12)
AI Model:   Claude Sonnet 4.5 (Anthropic)
Vector DB:  ChromaDB 0.4+
Embedding:  OpenAI text-embedding-3-small
Data:       한국산업안전보건공단 API
```

---

## 🚀 빠른 시작

### 사전 요구사항

- Python 3.12+
- Anthropic API 키
- OpenAI API 키 (임베딩용)
- 한국산업안전보건공단 API 키
- macOS 또는 Linux (Windows WSL2 가능)

### 1단계: 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd safety-ai-report/backend

# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2단계: 환경변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 수정
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-proj-your-key-here
KOSHA_API_KEY=your-kosha-api-key

LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 3단계: 법령 데이터 수집 및 벡터 DB 구축

```bash
# 전체 파이프라인 자동 실행 (최초 1회)
python scripts/rebuild_all.py

# 또는 단계별 실행
python scripts/collect_law_data.py      # 1. 법령 데이터 수집 (15분)
python scripts/preprocess_laws.py       # 2. 데이터 전처리 (1분)
python scripts/build_vectordb.py        # 3. 벡터 DB 구축 (10분)
```

### 4단계: 서버 실행

```bash
# 개발 서버 (자동 리로드)
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 서버
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5단계: API 테스트

```bash
# 헬스체크
curl http://localhost:8000/

# Swagger UI 접속
open http://localhost:8000/docs

# 질의응답 테스트
curl -X POST http://localhost:8000/chat \
  -F "message=안전모 착용 의무는?"
```

---

## 📚 API 사용 예시

### 예제 1: 이미지 분석 (사진만)

```bash
curl -X POST http://localhost:8000/chat \
  -F "file=@construction_site.jpg"
```

**응답:**
```json
{
  "type": "vision",
  "content": "# 현장 안전 점검 결과\n\n## 주요 안전 위반사항\n...",
  "status": "success",
  "source_docs": [
    {
      "title": "제38조 보호구의 지급 등",
      "category": "1",
      "similarity": 0.78
    }
  ]
}
```

### 예제 2: 질의응답 (RAG)

```bash
curl -X POST http://localhost:8000/chat \
  -F "message=고소작업 시 안전조치는?"
```

**응답:**
```json
{
  "type": "qa",
  "content": "고소작업 시 안전조치는 산업안전보건법...",
  "model_used": "claude-sonnet-4-5",
  "status": "success",
  "source_docs": [
    {
      "title": "제51조 사업주의 작업중지",
      "category": "1",
      "similarity": 0.73,
      "content_preview": "사업주는 산업재해가 발생할..."
    }
  ]
}
```

### 예제 3: 관리자 API

```bash
# DB 상태 확인
curl http://localhost:8000/admin/health

# 통계 조회
curl http://localhost:8000/admin/stats

# DB 재구축 (백그라운드)
curl -X POST http://localhost:8000/admin/rebuild

# DB 초기화
curl -X POST "http://localhost:8000/admin/reset?confirm=true"
```

---

## 🔧 프로젝트 구조

```
backend/
├── main.py                         # 메인 애플리케이션 (앱 초기화)
├── requirements.txt                # Python 의존성
├── .env                           # 환경변수 (미포함)
├── .env.example                   # 환경변수 예시
│
├── app/                            # 애플리케이션 코드
│   ├── __init__.py
│   │
│   ├── core/                       # 핵심 기능
│   │   ├── __init__.py
│   │   ├── constants.py           # 상수 정의
│   │   ├── validation.py          # 검증 및 예외 처리
│   │   └── logging_config.py      # 로깅 설정
│   │
│   ├── models/                     # 데이터 모델
│   │   ├── __init__.py
│   │   └── schemas.py             # Pydantic 스키마
│   │
│   ├── services/                   # 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── ai_service.py          # AI 서비스 (Claude API) ⭐
│   │   └── rag_service.py         # RAG 검색 서비스 ⭐
│   │
│   └── api/                        # API 라우터
│       ├── __init__.py
│       ├── chat.py                # Chat API (통합 엔드포인트) ⭐
│       └── admin.py               # 관리자 API ⭐
│
├── tests/                          # 테스트 코드
│   ├── __init__.py
│   ├── conftest.py                # pytest 설정 및 픽스처
│   ├── test_api/                  # API 테스트
│   │   ├── __init__.py
│   │   ├── test_chat.py
│   │   └── test_admin.py
│   └── test_services/             # 서비스 테스트
│       ├── __init__.py
│       └── test_rag_service.py
│
├── scripts/                        # 유틸리티 스크립트
│   ├── collect_law_data.py        # 법령 데이터 수집 ⭐
│   ├── preprocess_laws.py         # 데이터 전처리 ⭐
│   ├── build_vectordb.py          # 벡터 DB 구축 ⭐
│   ├── rebuild_all.py             # 전체 파이프라인 ⭐
│   ├── reset_db.py               # DB 초기화 ⭐
│   ├── test_kosha_api.py          # API 연결 테스트
│   └── test_rag.py                # RAG 검색 테스트
│
├── data/                           # 데이터 파일 (Git 무시)
│   ├── raw_laws/
│   │   └── laws_data.json         # 원본 법령 (9,052개)
│   └── processed_laws/
│       └── processed_laws.json    # 전처리 청크 (12,805개)
│
├── safety_db/                      # ChromaDB 저장소 (Git 무시) ⭐
│   └── chroma.sqlite3
│
└── logs/                           # 로그 파일 (Git 무시)
    └── app.log
```

---

## 🛠️ 관리 도구

### DB 초기화

```bash
# 스크립트로 초기화
python scripts/reset_db.py --confirm

# API로 초기화
curl -X POST "http://localhost:8000/admin/reset?confirm=true"
```

### DB 재구축

```bash
# 전체 재구축 (수집 → 전처리 → 벡터화)
python scripts/rebuild_all.py

# 수집 건너뛰고 재구축 (기존 데이터 사용)
python scripts/rebuild_all.py --skip-collect

# API로 재구축 (백그라운드)
curl -X POST http://localhost:8000/admin/rebuild
```

### DB 상태 확인

```bash
# 헬스체크
curl http://localhost:8000/admin/health

# 상세 통계
curl http://localhost:8000/admin/stats
```

**응답 예시:**
```json
{
  "status": "healthy",
  "details": {
    "db_exists": true,
    "total_documents": 12805,
    "category_1_count": 48,
    "db_path": "safety_db"
  }
}
```

---

## 📊 성능 및 제한사항

### API 응답 시간

| 작업 | 평균 시간 | 최대 시간 |
|------|---------|---------|
| 이미지 분석 (RAG) | 3-4초 | 7초 |
| 질의응답 (RAG) | 2-3초 | 5초 |
| 문서 생성 | 3-4초 | 6초 |

### 요청 제한

- 최대 파일 크기: 10MB
- 최대 메시지 길이: 5,000자
- 동시 요청: 무제한 (API 한도에 따름)

### 데이터 제한사항

⚠️ **현재 제한사항:**
- 카테고리 1 (법령) 문서: **48개** (전체의 약 5%)
- 실제 법령 조문 수: 약 900개
- 검색 품질: 제한적 (데이터 부족)

📝 **상세 내용**: [LIMITATIONS.md](LIMITATIONS.md) 참조

---

## 🧪 테스트

### 단위 테스트 (pytest)

```bash
# 테스트 의존성 설치
pip install pytest pytest-asyncio httpx

# 전체 테스트 실행
pytest tests/ -v

# 특정 테스트만 실행
pytest tests/test_api/test_chat.py -v

# 커버리지 포함
pytest tests/ --cov=app --cov-report=html
```

### 스크립트 테스트

```bash
# RAG 검색 테스트
python scripts/test_rag.py

# API 연결 테스트
python scripts/test_kosha_api.py 1
```

### API 테스트

```bash
# Swagger UI
open http://localhost:8000/docs

# curl 테스트
curl -X POST http://localhost:8000/chat \
  -F "message=건설현장 추락방지 조치"

# 헬스체크
curl http://localhost:8000/
```

---

## 🔒 보안

### 현재 적용

- ✅ 환경변수로 API 키 관리
- ✅ 파일 크기/타입 검증
- ✅ 입력값 검증
- ✅ 구조화된 에러 처리

### 향후 계획

- [ ] CORS 설정 강화
- [ ] Rate Limiting
- [ ] API 인증 (OAuth2/JWT)
- [ ] HTTPS 적용

---

## 🐛 디버깅

### 로그 확인

```bash
# 실시간 모니터링
tail -f logs/app.log

# 특정 요청 추적
grep "req_xxxxx" logs/app.log

# 에러만 필터링
grep "ERROR\|CRITICAL" logs/app.log

# RAG 검색 로그
grep "RAG 검색" logs/app.log
```

### 일반적인 문제

#### 1. RAG 검색 실패
```
Error executing plan: Internal error: Error finding id
```
**해결:** DB 재구축
```bash
python scripts/rebuild_all.py --skip-collect
```

#### 2. 카테고리 1 검색 결과 없음
```
law_results_count: 0
```
**원인:** 카테고리 1 데이터 부족 (48개만 존재)
**해결:** 전체 법령 재수집 필요 (TODO.md 참조)

---

## 📄 추가 문서

- **[API 명세서](API_SPECIFICATION.md)** - 프론트팀용 상세 API 문서
- **[제한사항](LIMITATIONS.md)** - 현재 시스템의 제약사항 및 개선 방향
- **[TODO](TODO.md)** - 향후 개선 작업 목록

---

## 🚀 로드맵

### ✅ 완료 (2026년 1월)
- [x] 기본 API 구현 (이미지 분석, 질의응답, 문서 생성)
- [x] 타입 안전성 강화 (Pydantic v2)
- [x] 에러 처리 표준화
- [x] RAG 시스템 구축 (벡터 DB + 검색)
- [x] 법령 데이터 수집 파이프라인 (12,805개 청크)
- [x] 관리자 API (DB 관리, 상태 확인)
- [x] 배치 스크립트 (수집, 전처리, 구축)
- [x] 코드 리팩토링 (서비스 레이어 분리, API 라우터 분리)
- [x] 테스트 구조 구축 (pytest 설정 및 기본 테스트)

### 🔄 진행 중 (2026년 2월)
- [ ] 법령 데이터 완성 (카테고리 1: 48개 → 900개)
- [ ] 검색 품질 개선 (하이브리드 검색)
- [x] 단위 테스트 구조 구축 (테스트 프레임워크 준비 완료)
- [ ] 테스트 커버리지 확대 (80%+ 목표)
- [ ] 문서화 완성 (사용 가이드, API 예시)

### 📋 계획 중 (2026년 Q1-Q2)
- [ ] CORS 보안 강화
- [ ] Rate Limiting 추가
- [ ] 배치 스케줄러 (일일 자동 업데이트)
- [ ] 증분 데이터 업데이트
- [ ] Docker 컨테이너화
- [ ] CI/CD 파이프라인

### 🔮 미래 계획 (2026년 Q3-Q4)
- [ ] 프론트엔드 개발 (React)
- [ ] 멀티모달 분석 (동영상 지원)
- [ ] 다국어 지원 (영어, 중국어)
- [ ] 모바일 앱
- [ ] 고급 분석 (트렌드, 통계)
- [ ] 커스텀 법령 업로드

---

## 🤝 기여

### 버그 리포트
GitHub Issues에서 버그를 리포트해주세요.

### 기능 제안
새로운 기능 제안은 Discussions에서 논의해주세요.

---

## 📞 문의

| 항목 | 담당자 | 연락처 |
|------|--------|--------|
| 백엔드 | 개발팀 | backend@example.com |
| 데이터 | 데이터팀 | data@example.com |
| 기타 문의 | 관리자 | admin@example.com |

---

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일 참고

---

**마지막 업데이트:** 2026년 1월 24일
**버전:** 3.0.0 (RAG 통합)
**상태:** 🟡 프로토타입 (데이터 개선 필요)
