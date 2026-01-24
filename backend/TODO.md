# 📝 TODO - Safety AI Agent 개선 작업

**버전:** 3.0.0  
**마지막 업데이트:** 2026년 1월 24일

---

## 🎯 우선순위 개요

| 우선순위 | 작업 | 예상 시간 | 담당 |
|---------|------|---------|------|
| 🔴 P0 | [데이터 완성](#p0-데이터-완성) | 2-3일 | 백엔드 |
| 🔴 P0 | [검색 품질 개선](#p0-검색-품질-개선) | 1주 | 백엔드 |
| 🟡 P1 | [성능 최적화](#p1-성능-최적화) | 1주 | 백엔드 |
| 🟡 P1 | [보안 강화](#p1-보안-강화) | 2주 | 백엔드/DevOps |
| 🟢 P2 | [기능 추가](#p2-기능-추가) | 2-3주 | 전체 |
| 🟢 P2 | [문서화](#p2-문서화) | 1주 | 백엔드 |

---

## 🔴 P0: 데이터 완성

### 목표
법령 데이터 커버리지 **5% → 90%+**

### 세부 작업

#### 1. API 파라미터 분석 및 최적화
- [ ] 카테고리별 데이터 분포 분석
  ```bash
  python scripts/analyze_categories.py
  ```
- [ ] 최적의 검색 키워드 조합 발견
  ```python
  CATEGORIES = {
      "1": "법령",  # 목표: 900개
      "2": "고시",
      "3": "예규",
      # ...
  }
  ```
- [ ] 각 카테고리별 전수 수집 전략 수립

**예상 결과:**
- 카테고리 1 문서: 48개 → 900개+
- 총 수집 문서: 9,052개 → 15,000개+

**소요 시간:** 1일

---

#### 2. 법령 데이터 재수집
- [ ] `collect_law_data.py` 수정
  ```python
  # 법령 우선 수집 전략
  def collect_law_priority():
      # 1. 산업안전보건법 (법률)
      # 2. 시행령
      # 3. 시행규칙 3개
      # 4. 기타 관련 법령
      pass
  ```
- [ ] Pagination 완벽 구현
- [ ] 중복 제거 강화 (제목 + 내용 해시)
- [ ] 메타데이터 보완
  - 법령명 추가
  - 법령 유형 (법률/시행령/시행규칙)
  - 조항 번호 파싱

**체크리스트:**
- [ ] 산업안전보건법: 170개 조문 수집
- [ ] 시행령: 150개 조문 수집
- [ ] 시행규칙: 200개 조문 수집
- [ ] 유해위험작업 규칙: 50개 조문 수집
- [ ] 안전보건기준 규칙: 650개 조문 수집 ⭐

**소요 시간:** 1-2일 (API 호출 시간 포함)

---

#### 3. 데이터 품질 검증
- [ ] 수집된 데이터 검증 스크립트 작성
  ```bash
  python scripts/validate_data.py
  ```
- [ ] 체크 항목:
  - [ ] 중복 확인
  - [ ] 내용 누락 확인
  - [ ] 메타데이터 완전성
  - [ ] 조문 번호 정합성

**소요 시간:** 0.5일

---

## 🔴 P0: 검색 품질 개선

### 목표
Similarity Score **0.4 → 0.8+**

### 세부 작업

#### 1. 하이브리드 검색 구현
- [ ] `rag_service.py`에 하이브리드 검색 추가
  ```python
  def hybrid_search(query: str) -> List[Result]:
      # 벡터 검색 (70%)
      vector_results = vector_search(query, top_k=20)
      
      # 키워드 매칭 (30%)
      keyword_scores = keyword_match(query, vector_results)
      
      # 하이브리드 점수
      final_scores = combine_scores(vector_results, keyword_scores)
      
      return top_k(final_scores, k=5)
  ```
- [ ] 가중치 튜닝 (0.7/0.3 → 최적값)
- [ ] 성능 테스트

**소요 시간:** 2일

---

#### 2. 청킹 전략 최적화
- [ ] `preprocess_laws.py` 개선
  ```python
  def smart_chunking(text: str, law_type: str):
      if law_type == "법률":
          # 조항 단위 분할
          return split_by_articles(text)
      else:
          # 의미 단위 분할 + 문맥 유지
          return semantic_chunking(text)
  ```
- [ ] 조항별 청킹 로직 구현
- [ ] 오버랩 전략 개선 (200자 → 동적)

**소요 시간:** 2일

---

#### 3. Re-ranking 도입
- [ ] Cross-encoder 모델 통합
  ```python
  from sentence_transformers import CrossEncoder
  
  reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
  
  def rerank(query: str, results: List[Result]):
      scores = reranker.predict([(query, r.content) for r in results])
      return sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
  ```
- [ ] 성능 측정 (응답 시간 +0.5초 이내)

**소요 시간:** 2일

---

#### 4. 검색 테스트 세트 구축
- [ ] 테스트 쿼리 100개 작성
  ```python
  test_queries = [
      {"query": "안전모 착용 의무", "expected_article": "제38조"},
      {"query": "고소작업 안전조치", "expected_article": "제42조"},
      # ...
  ]
  ```
- [ ] 자동화 평가 스크립트
- [ ] Precision@5, Recall@5 측정

**소요 시간:** 1일

---

## 🟡 P1: 성능 최적화

### 목표
응답 시간 **2.5초 → 1.5초**

### 세부 작업

#### 1. 캐싱 도입
- [ ] Redis 설치 및 설정
- [ ] 쿼리 결과 캐싱
  ```python
  @lru_cache(maxsize=1000)
  def cached_search(query: str):
      return search_laws(query)
  ```
- [ ] 캐시 만료 정책 (1시간)
- [ ] 캐시 히트율 모니터링

**소요 시간:** 2일

---

#### 2. 비동기 처리 강화
- [ ] RAG 검색 비동기화
  ```python
  async def async_rag_search(query: str):
      embedding_task = asyncio.create_task(generate_embedding(query))
      # ...
  ```
- [ ] LLM 호출과 병렬 처리
- [ ] 성능 테스트

**소요 시간:** 2일

---

#### 3. DB 최적화
- [ ] ChromaDB 인덱스 최적화
- [ ] 쿼리 성능 프로파일링
- [ ] 불필요한 메타데이터 제거

**소요 시간:** 1일

---

## 🟡 P1: 보안 강화

### 목표
프로덕션 레벨 보안

### 세부 작업

#### 1. 인증/인가 구현
- [ ] OAuth2 인증 추가
  ```python
  from fastapi.security import OAuth2PasswordBearer
  
  oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
  
  @app.post("/chat")
  async def chat(token: str = Depends(oauth2_scheme)):
      # ...
  ```
- [ ] JWT 토큰 발급
- [ ] 사용자 role 기반 접근 제어

**소요 시간:** 3일

---

#### 2. Rate Limiting
- [ ] Redis 기반 Rate Limiter
  ```python
  from slowapi import Limiter
  
  limiter = Limiter(key_func=get_remote_address)
  
  @app.post("/chat")
  @limiter.limit("10/minute")
  async def chat():
      # ...
  ```
- [ ] IP별 제한: 10회/분
- [ ] 사용자별 제한: 100회/시간

**소요 시간:** 2일

---

#### 3. HTTPS 및 CORS
- [ ] SSL 인증서 적용
- [ ] CORS 설정 강화
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["https://frontend.example.com"],
      allow_methods=["POST"],
      allow_headers=["*"],
  )
  ```

**소요 시간:** 1일

---

#### 4. 관리자 API 보호
- [ ] Admin 전용 인증
- [ ] IP 화이트리스트
- [ ] 감사 로그 (Audit Log)

**소요 시간:** 2일

---

## 🟢 P2: 기능 추가

### 세부 작업

#### 1. 고급 검색 기능
- [ ] 법령 유형별 필터
  ```python
  @app.post("/search")
  async def advanced_search(
      query: str,
      law_types: List[str] = ["법률", "시행령"],
      date_from: Optional[date] = None
  ):
      # ...
  ```
- [ ] 날짜 범위 검색
- [ ] 개정 이력 조회

**소요 시간:** 1주

---

#### 2. 멀티모달 분석
- [ ] 동영상 분석 (프레임 추출)
- [ ] 다중 이미지 처리
- [ ] 음성 입력 (STT)

**소요 시간:** 2주

---

#### 3. 자동 업데이트
- [ ] 배치 스케줄러 (APScheduler)
  ```python
  from apscheduler.schedulers.background import BackgroundScheduler
  
  scheduler = BackgroundScheduler()
  scheduler.add_job(collect_and_rebuild, 'cron', hour=2)  # 매일 새벽 2시
  scheduler.start()
  ```
- [ ] 증분 업데이트 로직
- [ ] 실패 시 알림

**소요 시간:** 1주

---

## 🟢 P2: 문서화

### 세부 작업

#### 1. 사용 가이드
- [ ] 튜토리얼 작성
  - [ ] 빠른 시작 (5분 안에)
  - [ ] 단계별 가이드
  - [ ] 문제 해결
- [ ] 동영상 튜토리얼

**소요 시간:** 3일

---

#### 2. API 문서 개선
- [ ] Swagger 설명 보완
- [ ] 요청/응답 예시 추가
- [ ] 에러 코드 상세화

**소요 시간:** 2일

---

#### 3. 아키텍처 문서
- [ ] 시스템 구조도
- [ ] 데이터 플로우
- [ ] 배포 가이드

**소요 시간:** 2일

---

## 📊 진행 상황 추적

### Week 1 (2026-01-27 ~ 2026-01-31)
- [ ] P0: 데이터 완성
  - [ ] API 파라미터 분석
  - [ ] 법령 데이터 재수집
  - [ ] 데이터 검증

**목표:** 법령 900개 수집 완료

---

### Week 2 (2026-02-03 ~ 2026-02-07)
- [ ] P0: 검색 품질 개선
  - [ ] 하이브리드 검색
  - [ ] 청킹 최적화
  - [ ] Re-ranking

**목표:** Similarity 0.8+ 달성

---

### Week 3-4 (2026-02-10 ~ 2026-02-21)
- [ ] P1: 성능 최적화
  - [ ] 캐싱
  - [ ] 비동기 처리
- [ ] P1: 보안 강화
  - [ ] 인증/인가
  - [ ] Rate Limiting

**목표:** 응답 시간 1.5초, 보안 강화

---

### Week 5-6 (2026-02-24 ~ 2026-03-07)
- [ ] P2: 기능 추가
- [ ] P2: 문서화

**목표:** 프로덕션 준비 완료

---

## 🔄 정기 작업

### 일일
- [ ] 로그 모니터링
- [ ] 에러 확인

### 주간
- [ ] 성능 측정
- [ ] 데이터 품질 체크
- [ ] 보안 스캔

### 월간
- [ ] 법령 데이터 업데이트
- [ ] 의존성 업데이트
- [ ] 백업 검증

---

## 📝 완료 기록

### 2026-01-24 (완료)
- ✅ RAG 시스템 구축
- ✅ 법령 데이터 수집 파이프라인
- ✅ 관리자 API
- ✅ 문서화 (README, LIMITATIONS)

---

## 🤝 기여 방법

1. Issue 생성
2. Feature Branch 생성 (`feature/your-feature`)
3. 작업 완료 후 PR
4. 리뷰 및 병합

---

**마지막 업데이트:** 2026년 1월 24일  
**담당자:** 백엔드 개발팀  
**다음 리뷰:** 2026년 2월 1일
