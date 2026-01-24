"""
공단 API 연결 테스트 스크립트

사용법:
    python scripts/test_kosha_api.py
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

KOSHA_API_KEY = os.getenv("KOSHA_API_KEY")
BASE_URL = "https://apis.data.go.kr/B552468/srch"


def test_api_connection():
    """API 연결 테스트"""
    print("=" * 60)
    print("한국산업안전보건공단 API 연결 테스트")
    print("=" * 60)

    if not KOSHA_API_KEY or KOSHA_API_KEY == "YOUR_API_KEY_HERE":
        print("❌ KOSHA_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 발급받은 API 키를 입력하세요.")
        return

    print(f"✅ API 키 확인: {KOSHA_API_KEY[:10]}...{KOSHA_API_KEY[-5:]}")
    print(f"✅ 엔드포인트: {BASE_URL}")

    # 단일 요청 테스트
    print("\n📡 API 요청 테스트 시작...")
    print("   파라미터: pageNo=1, numOfRows=10, category=0 (전체)")

    try:
        params = {
            "serviceKey": KOSHA_API_KEY,
            "pageNo": 1,
            "numOfRows": 10,
            "category": 0,
        }

        response = requests.get(f"{BASE_URL}/smartSearch", params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        # 응답 구조 출력
        print("\n✅ API 호출 성공!")
        print("\n📋 응답 구조:")
        print(json.dumps(data, ensure_ascii=False, indent=2))

        # 응답 파싱: response.header, response.body 경로로 접근
        response_obj = data.get("response", {})
        header = response_obj.get("header", {})
        result_code = header.get("resultCode", "N/A")
        result_msg = header.get("resultMsg", "N/A")

        print(f"\n📊 응답 헤더:")
        print(f"   resultCode: {result_code}")
        print(f"   resultMsg: {result_msg}")

        if result_code != "00":
            print(f"\n⚠️  API 오류 코드: {result_code}")
            print(f"   메시지: {result_msg}")
            return

        # body 정보 확인
        body = response_obj.get("body", {})
        total_count = body.get("totalCount", "0")
        page_no = body.get("pageNo", "1")
        num_of_rows = body.get("numOfRows", "0")

        print(f"\n📊 응답 body:")
        print(f"   totalCount: {total_count}")
        print(f"   pageNo: {page_no}")
        print(f"   numOfRows: {num_of_rows}")

        # items 확인
        items = body.get("items", {})
        item = items.get("item")

        if item is None:
            print("\n⚠️  응답에 item이 없습니다.")
        elif isinstance(item, dict):
            print(f"\n✅ 단일 객체 응답 확인")
            print(f"   doc_id: {item.get('doc_id', 'N/A')}")
            print(f"   title: {item.get('title', 'N/A')[:50]}...")
            print(f"   category: {item.get('category', 'N/A')}")
        elif isinstance(item, list):
            print(f"\n✅ 배열 응답 확인 ({len(item)}개 항목)")
            if len(item) > 0:
                print(f"   첫 번째 항목:")
                print(f"     doc_id: {item[0].get('doc_id', 'N/A')}")
                print(f"     title: {item[0].get('title', 'N/A')[:50]}...")
                print(f"     category: {item[0].get('category', 'N/A')}")

        print("\n✅ 테스트 완료!")

    except requests.exceptions.Timeout:
        print("❌ API 요청 타임아웃 (30초 초과)")
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP 오류: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"   응답 상태 코드: {e.response.status_code}")
            print(f"   응답 내용: {e.response.text[:500]}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 오류: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        print(f"   응답 내용: {response.text[:500]}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        import traceback

        traceback.print_exc()


def test_multiple_params():
    """다양한 파라미터 조합 테스트"""
    if not KOSHA_API_KEY or KOSHA_API_KEY == "YOUR_API_KEY_HERE":
        print("❌ KOSHA_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 발급받은 API 키를 입력하세요.")
        return None

    test_cases = [
        # case 1: 기본 (숫자)
        {"pageNo": 1, "numOfRows": 10, "category": 0},
        # case 2: category를 문자열로
        {"pageNo": 1, "numOfRows": 10, "category": "0"},
        # case 3: searchValue 추가
        {"pageNo": 1, "numOfRows": 10, "category": 0, "searchValue": "안전"},
        # case 4: category 없이
        {"pageNo": 1, "numOfRows": 10},
        # case 5: category를 1로
        {"pageNo": 1, "numOfRows": 10, "category": 1},
    ]

    for i, params in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"테스트 케이스 {i}: {params}")
        print("=" * 60)

        params["serviceKey"] = KOSHA_API_KEY

        try:
            response = requests.get(
                f"{BASE_URL}/smartSearch", params=params, timeout=30
            )
            response.raise_for_status()
            data = response.json()

            response_obj = data.get("response", {})
            header = response_obj.get("header", {})
            result_code = header.get("resultCode", "N/A")
            result_msg = header.get("resultMsg", "N/A")

            print(f"✅ resultCode: {result_code}")
            print(f"   resultMsg: {result_msg}")

            if result_code == "00":
                print("   🎉 성공!")
                body = response_obj.get("body", {})
                total_count = body.get("totalCount", "0")
                print(f"   totalCount: {total_count}")

                # 성공한 경우 응답 구조 일부 출력
                items = body.get("items", {})
                item = items.get("item")
                if item:
                    if isinstance(item, list) and len(item) > 0:
                        print(
                            f"   첫 번째 항목 제목: {item[0].get('title', 'N/A')[:50]}..."
                        )
                    elif isinstance(item, dict):
                        print(f"   항목 제목: {item.get('title', 'N/A')[:50]}...")

                return params  # 성공한 파라미터 반환
            else:
                print(f"   ❌ 실패")

        except Exception as e:
            print(f"   ❌ 에러: {e}")
            import traceback

            traceback.print_exc()

    return None


def test_full_collection_strategies():
    """전체 법령 수집 전략 테스트"""
    if not KOSHA_API_KEY or KOSHA_API_KEY == "YOUR_API_KEY_HERE":
        print("❌ KOSHA_API_KEY가 설정되지 않았습니다.")
        return {}

    print("=" * 60)
    print("전체 법령 수집 전략 테스트")
    print("=" * 60)

    strategies = [
        ("빈 문자열", ""),
        ("공백", " "),
        ("와일드카드 *", "*"),
        ("산업안전보건법", "산업안전보건법"),
        ("안전", "안전"),
        ("보건", "보건"),
        ("작업", "작업"),
        ("법령", "법령"),
        ("규칙", "규칙"),
    ]

    results = {}

    for strategy_name, search_value in strategies:
        print(f"\n[{strategy_name}] 테스트 중...")

        params = {
            "serviceKey": KOSHA_API_KEY,
            "pageNo": 1,
            "numOfRows": 10,
            "category": 0,
            "searchValue": search_value,
        }

        try:
            response = requests.get(
                f"{BASE_URL}/smartSearch", params=params, timeout=30
            )
            response.raise_for_status()
            data = response.json()

            response_obj = data.get("response", {})
            header = response_obj.get("header", {})
            result_code = header.get("resultCode", "N/A")

            if result_code == "00":
                body = response_obj.get("body", {})
                total_count = int(body.get("totalCount", "0"))
                results[strategy_name] = {
                    "search_value": search_value,
                    "total_count": total_count,
                }
                print(f"  ✅ 성공: {total_count:,}개")
            else:
                result_msg = header.get("resultMsg", "N/A")
                print(f"  ❌ 실패: {result_msg}")

        except Exception as e:
            print(f"  ❌ 에러: {e}")

    print("\n" + "=" * 60)
    print("결과 요약:")
    print("=" * 60)
    if results:
        sorted_results = sorted(
            results.items(), key=lambda x: x[1]["total_count"], reverse=True
        )
        for strategy, data in sorted_results:
            print(
                f"  {strategy:15s} (searchValue='{data['search_value']}'): {data['total_count']:,}개"
            )
    else:
        print("  성공한 전략이 없습니다.")

    return results


def run_step1():
    """1단계: 기본 API 연결 테스트"""
    print("=" * 60)
    print("1단계: 기본 API 연결 테스트")
    print("=" * 60 + "\n")

    successful_params = test_multiple_params()

    if successful_params:
        print(f"\n{'='*60}")
        print(f"✅ 성공한 파라미터: {successful_params}")
        print("=" * 60)
        return successful_params
    else:
        print("\n❌ 기본 테스트 실패")
        print("\n기본 연결 테스트 실행...")
        test_api_connection()
        return None


def run_step2():
    """2단계: 전체 법령 수집 전략 테스트"""
    print("=" * 60)
    print("2단계: 전체 법령 수집 전략 테스트")
    print("=" * 60 + "\n")

    strategies_result = test_full_collection_strategies()

    # 최적 전략 추천
    if strategies_result:
        best_strategy = max(
            strategies_result.items(), key=lambda x: x[1]["total_count"]
        )
        print("\n" + "=" * 60)
        print("🎯 추천 전략")
        print("=" * 60)
        print(f"  전략명: '{best_strategy[0]}'")
        print(f"  searchValue: '{best_strategy[1]['search_value']}'")
        print(f"  총 데이터 수: {best_strategy[1]['total_count']:,}개")
        print("\n💡 collect_law_data.py에서 다음 파라미터를 사용하세요:")
        print(f"   search_value='{best_strategy[1]['search_value']}'")
        print("=" * 60)
        return best_strategy
    else:
        print("\n❌ 성공한 전략이 없습니다.")
        return None


if __name__ == "__main__":
    import sys

    # 명령줄 인자 확인
    if len(sys.argv) > 1:
        step = sys.argv[1]

        if step == "1" or step == "step1":
            run_step1()
        elif step == "2" or step == "step2":
            run_step2()
        elif step == "all":
            # 전체 실행
            result1 = run_step1()
            if result1:
                print("\n\n")
                run_step2()
        else:
            print(f"❌ 알 수 없는 단계: {step}")
            print("\n사용법:")
            print("  python scripts/test_kosha_api.py 1      # 1단계만 실행")
            print("  python scripts/test_kosha_api.py 2      # 2단계만 실행")
            print("  python scripts/test_kosha_api.py all    # 전체 실행")
            print("  python scripts/test_kosha_api.py         # 전체 실행 (기본)")
    else:
        # 인자 없으면 전체 실행
        result1 = run_step1()
        if result1:
            print("\n\n")
            run_step2()
