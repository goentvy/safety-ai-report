# safety-ai-report

AI 기반 건설현장 안전 보고 시스템  
영상/이미지 분석을 통해 위험 상황을 자동 감지하고 보고서를 생성합니다.

---

## 📘 프로젝트 소개
`safety-ai-report`는 건설현장에서 발생하는 불합리·위험 상황을 **AI 분석**과 **자동 보고서 생성** 기능으로 관리하는 시스템입니다.  
- 작업자가 촬영한 이미지/영상 → AI가 위험 요소 감지  
- 자동 보고서 생성 및 담당자 지정  
- 알림(SMS/Email/메신저) 전송  
- 조치추적 및 감사 로그 관리  

---

## 📂 프로젝트 구조
```text
safety-ai-report/ 
├── frontend/ # React Native 앱 (촬영, 보고서 작성, 알림 수신) 
├── backend/ # Nest.js API 서버 (인증, 보고서, 알림, 조치추적) 
├── ai/ # AI 모델 (TensorFlow Lite, ONNX) 
├── infra/ # Docker, Kubernetes, CI/CD 설정 
└── README.md # 프로젝트 문서
```

---

## ⚙️ 개발 스택
- **Frontend**: React Native, React Navigation, Zustand/Redux  
- **Backend**: Nest.js, Supabase(Postgres), Swagger(OpenAPI)  
- **AI**: TensorFlow Lite, ONNX Runtime  
- **Storage**: AWS S3, Supabase Storage  
- **Notifications**: Twilio(SMS), SendGrid(Email), 카카오워크 API  
- **DevOps**: Docker, Kubernetes(AWS EKS), GitHub Actions, Sentry, Datadog  

---

## 🚀 배포 플로우
1. GitHub → 코드 푸시  
2. GitHub Actions → 빌드 & 테스트 (Jest + Newman)  
3. Docker → 이미지 빌드  
4. AWS ECR → 이미지 저장  
5. Kubernetes → 서비스 배포  
6. Sentry/Datadog → 모니터링 및 알림