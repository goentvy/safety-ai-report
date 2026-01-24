"""
한국산업안전보건공단 API를 통해 법령 데이터 수집

사용법:
    python scripts/collect_law_data.py
"""

import os
import json
import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# API 설정
KOSHA_API_KEY = os.getenv("KOSHA_API_KEY")
# 공공데이터포털 API 엔드포인트
BASE_URL = "https://apis.data.go.kr/B552468/srch"

# 출력 디렉토리 설정
OUTPUT_DIR = Path("data/raw_laws")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 수집 키워드 리스트 (중요도 순)
SEARCH_KEYWORDS = [
    "안전",  # 4,603개
    "작업",  # 4,130개
    "보건",  # 2,312개
    "산업안전보건법",  # 2,024개
    "규칙",  # 1,268개
]


class KoshaAPIClient:
    """한국산업안전보건공단 API 클라이언트"""

    def __init__(self, api_key: str):
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            raise ValueError(
                "KOSHA_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요."
            )
        self.api_key = api_key
        self.session = requests.Session()

    def search_law(
        self,
        category: int = 0,
        search_value: str = "",
        page_no: int = 1,
        num_of_rows: int = 100,
    ) -> Dict[str, Any]:
        """
        법령 검색 API 호출

        Args:
            category: 카테고리 (0:전체, 1:산안법령보고, 2:판정/해석사례, 3:산업표준지침,
                     4:산업안전보건 기술규칙, 5:산업안전 가이드라인, 6:물질, 7:예규)
            search_value: 검색어 (선택)
            page_no: 페이지 번호
            num_of_rows: 페이지당 결과 수

        Returns:
            API 응답 데이터
        """
        # 엔드포인트
        endpoint = f"{BASE_URL}/smartSearch"

        params = {
            "serviceKey": self.api_key,
            "pageNo": page_no,
            "numOfRows": num_of_rows,
            "category": category,
        }

        if search_value:
            params["searchValue"] = search_value

        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API 호출 실패: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"   응답 내용: {e.response.text[:500]}")
            raise


def parse_response_items(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    API 응답에서 items 추출 (단일 객체 또는 배열 처리)

    Args:
        response: API 응답 데이터

    Returns:
        법령 아이템 리스트
    """
    try:
        # response.body.items.item 경로로 접근
        response_obj = response.get("response", {})
        body = response_obj.get("body", {})
        items = body.get("items", {})

        # item이 단일 객체인지 배열인지 확인
        item = items.get("item")

        if item is None:
            return []

        # 단일 객체인 경우 리스트로 변환
        if isinstance(item, dict):
            return [item]
        elif isinstance(item, list):
            return item
        else:
            return []
    except Exception as e:
        print(f"⚠️  응답 파싱 오류: {e}")
        return []


def collect_laws_by_category(
    client: KoshaAPIClient, category: int, search_value: str = ""
) -> List[Dict[str, Any]]:
    """
    특정 카테고리의 법령 데이터 수집 (페이지네이션 처리)

    Args:
        client: API 클라이언트
        category: 카테고리 번호 (0~7)
        search_value: 검색어 (선택)

    Returns:
        수집된 법령 목록
    """
    category_names = {
        0: "전체",
        1: "산안법령보고",
        2: "판정/해석사례",
        3: "산업표준지침",
        4: "산업안전보건 기술규칙",
        5: "산업안전 가이드라인",
        6: "물질",
        7: "예규",
    }

    category_name = category_names.get(category, f"카테고리{category}")
    all_laws = []
    page_no = 1
    num_of_rows = 100

    print(f"📥 [{category_name}] 법령 데이터 수집 시작...")

    while True:
        print(f"  페이지 {page_no} 수집 중...")

        try:
            response = client.search_law(
                category=category,
                search_value=search_value,
                page_no=page_no,
                num_of_rows=num_of_rows,
            )

            # 응답 구조 파싱
            items = parse_response_items(response)

            if not items:
                print(f"  ✅ [{category_name}] 총 {len(all_laws)}개 법령 수집 완료")
                break

            # 카테고리 정보 추가
            for item in items:
                item["_category"] = category
                item["_category_name"] = category_name

            all_laws.extend(items)
            print(f"    → {len(items)}개 수집 (누적: {len(all_laws)}개)")

            # totalCount 확인하여 페이지네이션 종료 판단
            response_obj = response.get("response", {})
            body = response_obj.get("body", {})
            total_count = int(body.get("totalCount", "0"))

            if len(all_laws) >= total_count or len(items) < num_of_rows:
                print(f"  ✅ [{category_name}] 총 {len(all_laws)}개 법령 수집 완료")
                break

            page_no += 1

            # Rate limit 방지를 위한 대기
            time.sleep(0.5)

        except Exception as e:
            print(f"  ⚠️  페이지 {page_no} 수집 실패: {e}")
            # 부분 저장을 위해 현재까지 수집한 데이터는 유지
            if all_laws:
                print(f"  💾 부분 저장: {len(all_laws)}개 데이터 보존")
            break

    return all_laws


def collect_laws_by_keyword(
    client: KoshaAPIClient, keyword: str, category: int = 0
) -> List[Dict[str, Any]]:
    """
    특정 키워드로 법령 데이터 수집

    Args:
        client: API 클라이언트
        keyword: 검색 키워드
        category: 카테고리 (0: 전체)

    Returns:
        수집된 법령 목록
    """
    all_laws = []
    page_no = 1
    num_of_rows = 100

    print(f"📥 키워드 '{keyword}' 수집 시작...")

    while True:
        print(f"  페이지 {page_no} 수집 중...")

        try:
            response = client.search_law(
                category=category,
                search_value=keyword,
                page_no=page_no,
                num_of_rows=num_of_rows,
            )

            # 응답 파싱
            items = parse_response_items(response)

            if not items:
                print(f"  ✅ '{keyword}' 총 {len(all_laws)}개 수집 완료")
                break

            # 키워드 정보 추가
            for item in items:
                item["_search_keyword"] = keyword

            all_laws.extend(items)
            print(f"    → {len(items)}개 수집 (누적: {len(all_laws)}개)")

            # totalCount 확인
            response_obj = response.get("response", {})
            body = response_obj.get("body", {})
            total_count = int(body.get("totalCount", 0))

            if len(all_laws) >= total_count or len(items) < num_of_rows:
                print(f"  ✅ '{keyword}' 총 {len(all_laws)}개 수집 완료")
                break

            page_no += 1
            time.sleep(0.5)  # Rate limit

        except Exception as e:
            print(f"  ⚠️  '{keyword}' 페이지 {page_no} 수집 실패: {e}")
            if all_laws:
                print(f"  💾 부분 저장: {len(all_laws)}개 데이터 보존")
            break

    return all_laws


def deduplicate_laws(laws: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    doc_id 기준으로 중복 제거

    Args:
        laws: 법령 목록

    Returns:
        중복 제거된 법령 목록
    """
    print(f"\n🔄 중복 제거 시작 (수집: {len(laws)}개)")

    seen_doc_ids = set()
    unique_laws = []
    duplicate_count = 0

    for law in laws:
        doc_id = law.get("doc_id")

        if not doc_id:
            # doc_id가 없는 경우 (혹시 모를 예외 상황)
            unique_laws.append(law)
            continue

        if doc_id not in seen_doc_ids:
            seen_doc_ids.add(doc_id)
            unique_laws.append(law)
        else:
            duplicate_count += 1

    print(f"  ✅ 중복 제거 완료")
    print(f"     원본: {len(laws)}개")
    print(f"     중복: {duplicate_count}개")
    print(f"     최종: {len(unique_laws)}개")

    return unique_laws


def collect_all_laws(client: KoshaAPIClient) -> List[Dict[str, Any]]:
    """
    다중 키워드로 법령 데이터 수집 후 중복 제거

    Args:
        client: API 클라이언트

    Returns:
        중복 제거된 법령 목록
    """
    all_laws = []

    print("=" * 60)
    print(f"다중 키워드 수집 시작 (총 {len(SEARCH_KEYWORDS)}개 키워드)")
    print("=" * 60)

    for idx, keyword in enumerate(SEARCH_KEYWORDS, 1):
        print(f"\n[{idx}/{len(SEARCH_KEYWORDS)}] 키워드: '{keyword}'")
        print("-" * 60)

        try:
            keyword_laws = collect_laws_by_keyword(client, keyword)
            all_laws.extend(keyword_laws)

            # 키워드 간 대기
            if idx < len(SEARCH_KEYWORDS):
                time.sleep(1)

        except Exception as e:
            print(f"⚠️  키워드 '{keyword}' 수집 중 오류: {e}")
            continue

    print("\n" + "=" * 60)
    print(f"키워드별 수집 완료: 총 {len(all_laws)}개 (중복 포함)")
    print("=" * 60)

    # 중복 제거
    unique_laws = deduplicate_laws(all_laws)

    return unique_laws


def save_laws_to_json(laws: List[Dict[str, Any]], filename: str = "laws_data.json"):
    """
    수집된 법령을 JSON 파일로 저장

    Args:
        laws: 법령 목록
        filename: 저장할 파일명
    """
    output_path = OUTPUT_DIR / filename

    # 키워드별 통계 계산
    keyword_stats = {}
    for law in laws:
        keyword = law.get("_search_keyword", "unknown")
        keyword_stats[keyword] = keyword_stats.get(keyword, 0) + 1

    # 카테고리별 통계 계산
    category_stats = {}
    for law in laws:
        category = law.get("category", "unknown")
        category_stats[category] = category_stats.get(category, 0) + 1

    data = {
        "collected_at": datetime.now().isoformat(),
        "total_count": len(laws),
        "search_keywords": SEARCH_KEYWORDS,
        "keyword_stats": keyword_stats,
        "category_stats": category_stats,
        "laws": laws,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"💾 저장 완료: {output_path}")
    print(f"   총 {len(laws)}개 법령 저장됨")

    print(f"\n   키워드별 기여도:")
    for keyword, count in sorted(
        keyword_stats.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"     - {keyword}: {count}개")

    print(f"\n   카테고리별 분포:")
    for category, count in sorted(
        category_stats.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"     - {category}: {count}개")


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("한국산업안전보건공단 법령 데이터 수집")
    print("=" * 60)

    try:
        # API 클라이언트 초기화
        client = KoshaAPIClient(KOSHA_API_KEY)

        print(f"\n🔍 사용 키워드: {', '.join(SEARCH_KEYWORDS)}")
        print(f"   총 {len(SEARCH_KEYWORDS)}개 키워드로 다중 수집 후 중복 제거\n")

        # 법령 데이터 수집
        laws = collect_all_laws(client)

        if not laws:
            print("⚠️  수집된 법령이 없습니다.")
            return

        # JSON 파일로 저장
        save_laws_to_json(laws)

        # 통계 출력
        print("\n📊 수집 통계:")
        print(f"   총 법령 수: {len(laws)}")

        # 카테고리별 통계
        category_stats = {}
        for law in laws:
            cat_name = law.get("_category_name", "unknown")
            category_stats[cat_name] = category_stats.get(cat_name, 0) + 1

        print("\n   카테고리별 분포:")
        for cat_name, count in sorted(category_stats.items()):
            print(f"     - {cat_name}: {count}개")

        # 첫 번째 법령 샘플 출력
        if laws:
            print("\n📄 첫 번째 법령 샘플:")
            sample = {
                k: v for k, v in laws[0].items() if k != "content"
            }  # content는 너무 길 수 있음
            sample["content_preview"] = laws[0].get("content", "")[:200] + "..."
            print(json.dumps(sample, ensure_ascii=False, indent=2))

        print("\n✅ 모든 작업 완료!")

    except ValueError as e:
        print(f"❌ 설정 오류: {e}")
        print("   .env 파일에 KOSHA_API_KEY를 설정하세요.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise


if __name__ == "__main__":
    main()
