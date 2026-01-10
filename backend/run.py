"""
Safety AI Agent - 서버 실행 스크립트
타임아웃 및 스트림 최적화 설정 포함
"""
import uvicorn
import sys

if __name__ == "__main__":
    print("🚀 Safety AI Agent 시작...")
    print("📡 스트림 최적화 설정 활성화")
    print("   - 타임아웃: 120초")
    print("   - 하트비트: 활성화")
    print("   - 동적 버퍼: 활성화")
    print()

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        timeout_keep_alive=120,  # ✅ 권장 2: 타임아웃 증가 (기본 5초)
        timeout_graceful_shutdown=30,
        log_level="info"
    )

