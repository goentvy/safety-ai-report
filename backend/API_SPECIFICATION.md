# 🔌 Safety AI Agent - API 명세서 (Frontend Team)

**버전:** 2.0.0  
**마지막 업데이트:** 2026년 1월 10일  
**상태:** ✅ 프로덕션 준비 완료

---

## 📋 목차

1. [개요](#개요)
2. [인증](#인증)
3. [기본 정보](#기본-정보)
4. [API 엔드포인트](#api-엔드포인트)
5. [요청/응답 스키마](#요청응답-스키마)
6. [에러 처리](#에러-처리)
7. [코드 예시](#코드-예시)
8. [FAQ](#faq)

---

## 개요

### 서비스 설명

Safety AI Agent는 산업현장 사진을 자동으로 분석하여 산업안전보건법 위반사항을 지적하고, 안전 관련 질문에 법령 기반으로 답변하는 AI 서비스입니다.

### 기본 URL

```
개발 환경: http://localhost:8000
스테이징:  https://staging-api.example.com
프로덕션: https://api.example.com
```

### 지원 버전

- Python 3.12+
- FastAPI 0.104+
- Pydantic v2

---

## 인증

### 현재 상태
🔓 **인증 없음** (개발 단계)

### 향후 계획
🔐 **OAuth2 / JWT 인증** (Q2 2026 예정)

---

## 기본 정보

### 요청 형식

모든 API는 **multipart/form-data**를 사용합니다.

```
Content-Type: multipart/form-data
```

### 응답 형식

모든 응답은 **JSON**입니다.

```
Content-Type: application/json; charset=utf-8
```

### 요청 인코딩

- UTF-8 권장
- 이미지는 Base64 자동 인코딩

### 응답 인코딩

- UTF-8 (모든 응답)
- 한국어 완벽 지원

---

## API 엔드포인트

### 1. 헬스체크 (Health Check)

#### 요청

```http
GET /
```

#### 응답

**200 OK**

```json
{
  "status": "healthy",
  "service": "Safety AI Agent",
  "version": "2.0.0"
}
```

**사용 목적:**
- 서버 상태 확인
- 서비스 가용성 확인
- 응답 시간 측정

---

### 2. 통합 챗 API (Unified Chat API)

#### 요청

```http
POST /chat
```

**파라미터:**

| 이름 | 타입 | 필수 | 제한 | 설명 |
|------|------|:----:|------|------|
| `file` | File | ✗ | <10MB | 이미지 파일 (JPEG/PNG/GIF/WEBP) |
| `message` | String | ✗ | ≤5000자 | 텍스트 메시지 |

**제약조건:**
- `file`과 `message` 중 하나는 반드시 필요 (둘 다 필수 아님)
- 파일은 이미지 형식만 지원
- 파일 크기는 10MB 이하

#### 응답

**200 OK - 성공 (3가지 타입)**

**Type 1: 이미지 분석 결과 (VisionResponse)**

```json
{
  "type": "vision",
  "content": "안전모 미착용이 확인되었습니다. 산업안전보건기준에 관한 규칙 제38조에 따르면...",
  "status": "success"
}
```

**Type 2: 문서 생성 결과 (DocumentResponse)**

```json
{
  "type": "document",
  "content": "# 건설업 안전점검 체크리스트\n\n## 1. 보호구\n...",
  "status": "success"
}
```

**Type 3: 질의응답 결과 (QAResponse)**

```json
{
  "type": "qa",
  "content": "산업안전보건법 제38조에 따르면...",
  "model_used": "claude-sonnet-4-5",
  "source_docs": [],
  "status": "success"
}
```

#### 에러 응답

**400 Bad Request**

```json
{
  "type": "error",
  "status": "fail",
  "content": "파일 또는 메시지 중 하나는 반드시 제공되어야 합니다.",
  "error_code": "INVALID_MESSAGE"
}
```

**413 Payload Too Large**

```json
{
  "type": "error",
  "status": "fail",
  "content": "파일 크기(12.34MB)가 최대 허용 크기(10.00MB)를 초과합니다",
  "error_code": "FILE_TOO_LARGE"
}
```

**415 Unsupported Media Type**

```json
{
  "type": "error",
  "status": "fail",
  "content": "지원하지 않는 파일 형식입니다: application/pdf",
  "error_code": "UNSUPPORTED_FILE_TYPE"
}
```

**429 Too Many Requests**

```json
{
  "type": "error",
  "status": "fail",
  "content": "API 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.",
  "error_code": "RATE_LIMIT_EXCEEDED"
}
```

**500 Internal Server Error**

```json
{
  "type": "error",
  "status": "fail",
  "content": "서버 내부 오류가 발생했습니다.",
  "error_code": "INTERNAL_ERROR"
}
```

---

## 요청/응답 스키마

### 요청 파라미터

```typescript
interface ChatRequest {
  file?: File;           // 이미지 파일 (선택)
  message?: string;      // 텍스트 메시지 (선택)
}
```

### 응답 스키마

```typescript
// 공통 응답
interface BaseResponse {
  status: "success" | "fail";
}

// 이미지 분석 응답
interface VisionResponse extends BaseResponse {
  type: "vision";
  content: string;        // AI 분석 결과
  status: "success";
}

// 문서 생성 응답
interface DocumentResponse extends BaseResponse {
  type: "document";
  content: string;        // 마크다운 형식 문서
  status: "success";
}

// 질의응답 응답
interface QAResponse extends BaseResponse {
  type: "qa";
  content: string;        // 답변 텍스트
  model_used?: string;    // 사용된 AI 모델
  source_docs?: Array<{   // 참조 문서 메타데이터 (RAG)
    source: string;
    chunk_index: number;
  }>;
  status: "success";
}

// 에러 응답
interface ErrorResponse extends BaseResponse {
  type: "error";
  status: "fail";
  content: string;        // 에러 메시지
  error_code?: string;    // 에러 코드
}
```

---

## 에러 처리

### HTTP 상태 코드

| 코드 | 의미 | 설명 |
|------|------|------|
| 200 | OK | 요청 성공 |
| 400 | Bad Request | 잘못된 요청 (필수 파라미터 누락, 형식 오류) |
| 413 | Payload Too Large | 파일 크기 초과 (10MB 초과) |
| 415 | Unsupported Media Type | 지원하지 않는 파일 타입 |
| 429 | Too Many Requests | API 요청 한도 초과 |
| 500 | Internal Server Error | 서버 오류 |
| 503 | Service Unavailable | AI 서비스 연결 불가 |

### 에러 코드

| 코드 | 설명 | HTTP | 재시도 |
|------|------|------|--------|
| `INVALID_MESSAGE` | 메시지/파일 누락 | 400 | ✗ |
| `FILE_TOO_LARGE` | 파일 크기 초과 | 413 | ✗ |
| `UNSUPPORTED_FILE_TYPE` | 지원하지 않는 파일 타입 | 415 | ✗ |
| `RATE_LIMIT_EXCEEDED` | API 요청 한도 초과 | 429 | ✅ (대기 후) |
| `API_ERROR` | AI API 오류 | 500 | ✅ (지수 백오프) |
| `API_CONNECTION_ERROR` | AI 서비스 연결 실패 | 503 | ✅ (대기 후) |
| `INTERNAL_ERROR` | 서버 내부 오류 | 500 | ✅ (3회 제한) |

### 재시도 전략

```javascript
// 지수 백오프 재시도 예시
async function apiCallWithRetry(request, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fetch('/chat', request);
    } catch (error) {
      if (error.status === 429 || error.status >= 500) {
        const delay = Math.pow(2, i) * 1000; // 1초, 2초, 4초
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        throw error; // 재시도 불가능한 에러
      }
    }
  }
  throw new Error('Max retries exceeded');
}
```

---

## 코드 예시

### JavaScript / TypeScript

#### 예제 1: 이미지 분석 (사진만)

```javascript
async function analyzeImage(imageFile) {
  const formData = new FormData();
  formData.append('file', imageFile);
  
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    body: formData
  });
  
  if (!response.ok) {
    const error = await response.json();
    console.error(`Error: ${error.error_code} - ${error.content}`);
    return null;
  }
  
  const result = await response.json();
  console.log(result.content);
  return result;
}
```

#### 예제 2: 이미지 분석 (사진 + 질문)

```javascript
async function analyzeImageWithQuestion(imageFile, question) {
  const formData = new FormData();
  formData.append('file', imageFile);
  formData.append('message', question);
  
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  if (result.status === 'success') {
    return result.content;
  } else {
    throw new Error(result.content);
  }
}
```

#### 예제 3: 질의응답

```javascript
async function askQuestion(question) {
  const formData = new FormData();
  formData.append('message', question);
  
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  return result.content;
}
```

#### 예제 4: 문서 생성

```javascript
async function generateDocument(request) {
  const formData = new FormData();
  formData.append('message', request);
  
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  // Markdown을 HTML로 변환 (marked.js 등 사용)
  return markdownToHtml(result.content);
}
```

#### 예제 5: 재시도 로직이 있는 호출

```javascript
async function callWithRetry(formData, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        return await response.json();
      }
      
      const error = await response.json();
      
      // 재시도 가능한 에러인지 확인
      if ([429, 503].includes(response.status)) {
        const delay = Math.pow(2, attempt - 1) * 1000;
        console.log(`재시도 ${attempt}/${maxRetries} (${delay}ms 대기)`);
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      
      // 재시도 불가능한 에러
      throw new Error(`${error.error_code}: ${error.content}`);
    } catch (error) {
      if (attempt === maxRetries) throw error;
    }
  }
}
```

### React 컴포넌트 예제

```typescript
import React, { useState } from 'react';

interface ChatResult {
  type: 'vision' | 'document' | 'qa';
  content: string;
  status: 'success' | 'fail';
}

export const SafetyChat: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ChatResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (
    imageFile?: File,
    message?: string
  ) => {
    setLoading(true);
    setError(null);

    const formData = new FormData();
    if (imageFile) formData.append('file', imageFile);
    if (message) formData.append('message', message);

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.content);
      }

      const data: ChatResult = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {loading && <p>처리 중...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {result && <p>{result.content}</p>}
      <button onClick={() => handleSubmit(undefined, '안전모 규정은?')}>
        질문하기
      </button>
    </div>
  );
};
```

### Python 예제

```python
import requests
from typing import Optional

API_URL = "http://localhost:8000"

def analyze_image(image_path: str, question: Optional[str] = None) -> dict:
    """이미지 분석"""
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {'message': question} if question else {}
        
        response = requests.post(
            f"{API_URL}/chat",
            files=files,
            data=data
        )
    
    response.raise_for_status()
    return response.json()

def ask_question(question: str) -> dict:
    """질문하기"""
    data = {'message': question}
    response = requests.post(f"{API_URL}/chat", data=data)
    response.raise_for_status()
    return response.json()

# 사용 예시
result = analyze_image('site.jpg', '이 현장의 위험요소는?')
print(result['content'])
```

---

## FAQ

### Q1. 파일 크기 제한은?
**A.** 최대 10MB입니다. 더 큰 파일은 먼저 압축하거나 해상도를 낮춰서 업로드하세요.

### Q2. 어떤 이미지 형식을 지원하나요?
**A.** JPEG, PNG, GIF, WebP를 지원합니다. BMP, TIFF 등은 지원하지 않습니다.

### Q3. 요청에 응답이 없으면 어떻게 하나요?
**A.** 최대 30초 대기 후 에러를 반환합니다. 타임아웃 에러는 재시도 가능합니다.

### Q4. 요청 개수 제한이 있나요?
**A.** 현재는 제한이 없지만, 향후 Rate Limiting이 추가될 예정입니다.

### Q5. 한국어 이외 언어도 지원하나요?
**A.** 현재는 한국어만 최적화되어 있습니다. 다국어 지원은 Q3 2026 예정입니다.

### Q6. 이미지 분석이 느린데 어떻게 하나요?
**A.** 다음을 시도해보세요:
- 이미지 크기 줄이기 (최대한 작게)
- 불필요한 세부사항 제거
- 잠시 후 재시도

### Q7. API 응답이 정확하지 않으면?
**A.** 질문을 더 구체적으로 작성하거나, 이미지를 더 선명하게 촬영하세요.

### Q8. CORS 에러가 발생하면?
**A.** 현재 개발 환경에서는 모든 도메인을 허용합니다. 프로덕션에서는 올바른 도메인으로 요청하세요.

### Q9. 사용자 데이터는 보관되나요?
**A.** 아니요. 요청 처리 직후 모든 데이터는 삭제됩니다.

### Q10. API 키 없이 호출할 수 있나요?
**A.** 네. 현재 개발 단계에서는 인증이 필요 없습니다. 향후 OAuth2 인증이 추가됩니다.

---

## 문제 해결

### 연결 실패

```
Error: Failed to fetch

✅ 해결:
1. 서버가 실행 중인지 확인: curl http://localhost:8000/
2. 올바른 URL을 사용하는지 확인
3. 방화벽 설정 확인
```

### 파일 업로드 실패

```
413 Payload Too Large

✅ 해결:
1. 파일 크기 확인: 최대 10MB
2. 파일 크기 줄이기 (이미지 압축 등)
```

### 응답이 없음

```
504 Gateway Timeout

✅ 해결:
1. 잠시 후 재시도
2. 더 작은 이미지로 시도
3. 쿼리를 더 간단하게 작성
```

---

## 지원

### 버그 리포트
- GitHub Issues: https://github.com/example/issues
- 이메일: backend@example.com

### 기능 요청
- Discussions: https://github.com/example/discussions

### 기술 지원
- Slack: #ai-support
- Email: support@example.com

---

**마지막 업데이트:** 2026년 1월 10일  
**버전:** 2.0.0  
**상태:** ✅ 프로덕션 준비 완료

