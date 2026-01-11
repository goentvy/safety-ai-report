# 🏗️ Safety AI Agent - 산업안전 통합 AI 서비스

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangogo.com/)
[![Anthropic Claude](https://img.shields.io/badge/Claude-Sonnet%204.5-purple.svg)](https://www.anthropic.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#)

> 대한민국 산업안전보건법 기준으로 현장 안전을 AI가 자동 분석하는 서비스

---

## 🎯 서비스 개요

**Safety AI Agent**는 산업현장의 안전을 자동으로 점검하는 AI 기반 서비스입니다.

### 핵심 기능

| 기능 | 설명 | 입력 | 특징 |
|------|------|------|------|
| **📷 이미지 분석** | 현장 사진을 산안법 기준으로 점검 | 이미지 + 질문(선택) | 실시간 스트리밍 응답 |
| **📄 문서 생성** | 안전 점검 문서 자동 생성 | 텍스트 요청 | 마크다운 형식 |
| **❓ 질의응답** | 산안법 관련 질문에 AI가 답변 | 텍스트 질문 | 법령 근거 제시 |

### 기술 스택

- **Backend**: FastAPI (Python 3.12)
- **AI Model**: Claude Sonnet 4.5 (Anthropic)
- **Streaming**: Server-Sent Events (SSE)
- **Vector DB**: ChromaDB (로컬 저장)
- **Logging**: 구조화된 로깅 시스템

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
ANTHROPIC_API_KEY=sk-ant-your-key-here
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
LLAMA_CLOUD_API_KEY=your-llama-parse-key  # PDF 파싱용 (선택)
```

### 3단계: 서버 실행

```bash
# 개발 서버 실행 (자동 리로드)
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 서버 실행
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### 4단계: API 테스트

```bash
# 헬스체크
curl http://localhost:8000/

# Swagger UI 접속 (대화형 API 문서)
http://localhost:8000/docs

# ReDoc 접속 (읽기 전용 API 문서)
http://localhost:8000/redoc
```

---

## 📚 API 사용 예시

### 예제 1: 스트리밍 기반 이미지 분석

```bash
# 사진만 전송 (기본 프롬프트 사용)
curl -X POST http://localhost:8000/chat/stream \
  -F "file=@photo.jpg" \
  -H "Accept: text/event-stream"

# 사진 + 질문
curl -X POST http://localhost:8000/chat/stream \
  -F "file=@photo.jpg" \
  -F "message=비계의 안전성을 점검해줘" \
  -H "Accept: text/event-stream"
```

**응답 예시 (JSON 버퍼링 SSE 스트림):**
```json
data: {"type":"text","content":"비계 점검 결과:\n## 1. 보호구 착용 여부\n- 안전모: 미착용 (×위반)\n\n## 2. 난간대 높이\n- 현황: 85cm\n- 기준: 90cm 이상\n- 판정: 부적합\n\n## 3. 개구부 방호\n- 덮개 미설치\n- 위험도: 높음\n\n### 조치사항\n1. 즉시 안전난간 설치\n2. 개구부 덮개 설치\n3. 안전대 부착설비"}
data: {"type":"heartbeat","content":""}
data: {"type":"text","content":" 점검\n\n### 관련 법규\n- 산업안전보건기준에 관한 규칙 제13조 (안전난간)\n- 산업안전보건기준에 관한 규칙 제42조 (개구부 등의 방호)\n- 산업안전보건기준에 관한 규칙 제43조 (안전대 부착설비)\n\n**※ 본 점검 결과는 AI 분석이며, 최종 판단은 안전관리자가 확인해야 합니다."}
data: {"type":"done","content":"","total_chunks":2,"total_chars":389,"adaptive_buffer_used":200}
```

**종료 신호**: 스트림이 완료되면 `{"type":"done"}` 신호와 함께 통계 정보가 전송됩니다.
- `total_chunks`: 전송된 청크 수
- `total_chars`: 총 문자 수
- `adaptive_buffer_used`: 사용된 실제 버퍼 크기

### 예제 2: 문서 생성

```bash
curl -X POST http://localhost:8000/chat/stream \
  -F "message=안전 점검 체크리스트를 마크다운 형식으로 만들어줘" \
  -H "Accept: text/event-stream"
```

### 예제 3: 질의응답

```bash
curl -X POST http://localhost:8000/chat/stream \
  -F "message=안전보건기준에 관한 규칙에서 비계의 난간대 높이는?" \
  -H "Accept: text/event-stream"
```

---

## 🔄 실시간 스트리밍 아키텍처

### 응답 흐름

```
┌─────────┐      ┌──────────┐      ┌─────────────┐      ┌──────────┐
│ Browser │──→  │ FastAPI  │──→  │ Claude API  │──→  │ Browser  │
│         │      │ (SSE)    │      │ (Streaming) │      │  (UI)    │
└─────────┘      └──────────┘      └─────────────┘      └──────────┘
                       ↓
                   버퍼링 처리
                  (50~60자 단위)
                       ↓
                  JSON 형식 변환
                       ↓
                    SSE 스트림
```

### 성능 비교

| 항목 | 이전 (토큰 단위) | 개선 (버퍼링) |
|------|-----------------|-----------------|
| 네트워크 요청 수 | 800+ | 4~6 |
| 평균 응답 크기 | 2~5 bytes | 200~250 bytes |
| 프론트엔드 부담 | 높음 | 매우 낮음 |
| UX | 끊김 현상 | 매우 부드러움 |
| 종료 신호 | ❌ 없음 | ✅ 명시적 (total_chars 포함) |
| 응답 잘림 | ⚠️ 발생 | ✅ 해결 |

### 스트림 안정성 강화

SSE 스트리밍의 안정성을 위해 다음 기능들이 적용되었습니다:

- **✅ 타임아웃 증가** (120초): 장시간 응답도 안정적으로 처리
- **✅ X-Accel-Buffering 헤더**: Nginx 등 프록시의 버퍼링 비활성화
- **✅ 하트비트 신호**: 1초마다 연결 상태 확인 (`{"type":"heartbeat"}`)
- **✅ 동적 버퍼 크기**: 청크 수에 따라 200~500자로 자동 조정

### 응답 예시 (개선된 SSE)

---

```
backend/
├── main.py                           # FastAPI 애플리케이션 진입점 (스트리밍)
├── requirements.txt                  # Python 의존성
├── .env                             # 환경변수 설정
├── .gitignore                       # Git 제외 파일
├── README.md                        # 이 파일
│
├── app/
│   ├── __init__.py
│   │
│   ├── api/                         # API 라우터 (Admin, Chat 등)
│   │   ├── __init__.py
│   │   ├── admin.py                 # 관리자 API (문서 업로드, DB 관리)
│   │   └── chat.py                  # 채팅 API (레거시, 비스트리밍)
│   │
│   ├── services/                    # 비즈니스 로직 계층
│   │   ├── __init__.py
│   │   ├── chat_service.py          # AI 응답 스트리밍 처리 (핵심)
│   │   ├── request_handler.py       # 요청 타입 판별
│   │   ├── doc_service.py           # 문서 파싱 (DOCX, PDF)
│   │   ├── ai_service.py            # AI 호출 (레거시)
│   │   ├── rag_service.py           # ChromaDB 벡터 검색
│   │   └── doc_classifier.py        # 문서 분류
│   │
│   ├── core/                        # 핵심 유틸리티 및 설정
│   │   ├── __init__.py
│   │   ├── constants.py             # 상수 (모델, 프롬프트, 토큰 설정)
│   │   ├── validation.py            # 입력 검증 및 에러 처리
│   │   ├── logging_config.py        # 로깅 설정
│   │   ├── config.py                # 애플리케이션 설정
│   │   ├── utils.py                 # 청킹, 법령 분석 유틸리티
│   │   └── weighted_retriever.py    # 가중치 기반 검색
│   │
│   └── models/                      # Pydantic 스키마 정의
│       ├── __init__.py
│       └── schemas.py               # Response/Request 모델
│
├── logs/                            # 로그 파일
│   └── app.log
│
└── safety_db/                       # ChromaDB 로컬 저장소
    └── chroma.sqlite3
```

---

## 🔄 요청 처리 흐름

### 스트리밍 기반 처리 (v2.1.0+)

```
User Request
    ↓
[main.py] /chat/stream 엔드포인트
    ↓
[request_handler.py] 요청 타입 판별
    ├─ Vision (이미지 있음)
    ├─ Document (문서 생성 키워드)
    └─ QA (일반 질문)
    ↓
[chat_service.py] 스트리밍 생성
    ↓
[anthropic API] stream_vision_analysis / stream_document_generation / stream_qa
    ↓
[SSE] Server-Sent Events 포맷으로 클라이언트에 실시간 전송
    ↓
User receives streamed response
```

### 핵심 개선사항

| 항목 | 이전 (v2.0) | 현재 (v2.1) |
|------|-----------|-----------|
| 응답 방식 | 전체 응답 대기 후 반환 | 실시간 스트리밍 |
| 체감 응답시간 | 3-5초 대기 | 0.2초 부분 응답 |
| 토큰 한계 | Vision: 1500, QA: 2048 | Vision: 800, QA: 800 |
| 프롬프트 | 길고 자세함 | 간결하고 효율적 |
| 비용 | 높음 | 40% 절감 |

---

## 🔐 환경변수

```bash
# 필수
ANTHROPIC_API_KEY=sk-ant-...        # Anthropic API 키

# 선택
LOG_LEVEL=INFO                      # 로깅 레벨 (DEBUG, INFO, WARNING, ERROR)
LOG_FILE=logs/app.log              # 로그 파일 경로
LLAMA_CLOUD_API_KEY=...            # PDF 고급 파싱용 (선택)
```

---

## 📊 성능 최적화

### 1. 스트리밍 응답
- SSE를 통한 실시간 청크 전송
- 첫 응답까지 ~200ms
- 사용자가 첫 단어를 빠르게 볼 수 있음

### 2. 토큰 최소화
- Vision: 1500 → 800 토큰 (47% 감소)
- QA: 2048 → 800 토큰 (61% 감소)
- Document: 3000 → 1500 토큰 (50% 감소)

### 3. 프롬프트 최적화
- 불필요한 설명 제거
- 핵심 지시사항만 유지
- 응답 길이 자동으로 단축

---

## 🛠️ 개발자 가이드

### 새로운 기능 추가

#### 1. 스트리밍 함수 추가 (chat_service.py)

```python
async def stream_custom_feature(self, params) -> AsyncGenerator[str, None]:
    """새로운 기능의 스트리밍 응답"""
    with self.client.messages.stream(...) as stream:
        for text in stream.text_stream:
            yield text
```

#### 2. 엔드포인트 추가 (main.py)

```python
@app.post("/chat/stream")
async def chat_stream_custom(...):
    generator = chat_service.stream_custom_feature(...)
    return StreamingResponse(stream_response(generator), media_type="text/event-stream")
```

### 테스트

```bash
# 단위 테스트
pytest tests/ -v

# API 통합 테스트
pytest tests/integration/ -v

# 로드 테스트 (스트리밍 성능)
locust -f tests/load_test.py
```

---

## 🐛 트러블슈팅

### 문제: "ANTHROPIC_API_KEY 환경변수 누락"
**해결책**:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
# 또는 .env 파일에 설정
```

### 문제: "스트림이 끝나지 않음"
**해결책**:
1. 네트워크 연결 확인
2. API 할당량 확인
3. `Cache-Control` 헤더 확인

### 문제: "이미지 인식이 안 됨"
**해결책**:
1. 이미지 형식 확인 (JPEG, PNG, GIF, WebP)
2. 파일 크기 확인 (최대 10MB)
3. 이미지 품질 확인 (너무 어두우면 인식 어려움)

---

## 📝 커밋 메시지 가이드

```bash
# 기능 추가
git commit -m "feat: 스트리밍 기반 채팅 API 추가"

# 버그 수정
git commit -m "fix: 파일 크기 검증 로직 수정"

# 성능 개선
git commit -m "perf: 프롬프트 최소화로 응답 속도 40% 향상"

# 리팩토링
git commit -m "refactor: main.py를 chat_service.py로 분리"

# 문서
git commit -m "docs: API 사용 예시 추가"
```

---

## 📄 라이센스

MIT License - 자유롭게 사용, 수정, 배포 가능

---

## 📞 지원

문제가 발생하면:
1. GitHub Issues에 버그 리포트
2. 상세한 오류 로그 첨부
3. 재현 가능한 예시 코드 제공

---

**마지막 업데이트**: 2026-01-10  
**버전**: 2.1.0  
**상태**: 프로덕션 준비 완료 ✅

