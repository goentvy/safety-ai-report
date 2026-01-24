"""
법령 데이터 전처리 및 청킹

사용법:
    python scripts/preprocess_laws.py
"""
import os
import json
import re
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

# 입출력 디렉토리
INPUT_FILE = Path("data/raw_laws/laws_data.json")
OUTPUT_DIR = Path("data/processed_laws")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 청킹 설정
CHUNK_SIZE = 1000  # 문자 단위
CHUNK_OVERLAP = 200  # 겹치는 부분


def load_raw_data(filepath: Path) -> Dict[str, Any]:
    """원본 JSON 파일 로드"""
    print(f"📂 파일 로드 중: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"✅ 총 {data['total_count']}개 법령 로드됨")
    return data


def clean_text(text: str) -> str:
    """
    텍스트 정제
    - HTML 태그 제거
    - 다중 공백 제거
    - 다중 줄바꿈 제거
    """
    if not text:
        return ""

    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)

    # 다중 공백을 단일 공백으로
    text = re.sub(r'\s+', ' ', text)

    # 양끝 공백 제거
    text = text.strip()

    return text


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    텍스트를 청크로 분할

    Args:
        text: 분할할 텍스트
        chunk_size: 청크 크기 (문자 단위)
        overlap: 겹치는 부분 크기

    Returns:
        청크 리스트
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # 마지막 청크가 아니고, 문장 중간에서 끊기면 마침표까지 포함
        if end < len(text) and chunk[-1] not in ['.', '。', '\n']:
            # 마지막 마침표 찾기
            last_period = max(chunk.rfind('.'), chunk.rfind('。'))
            if last_period > chunk_size // 2:  # 절반 이상 진행했다면
                end = start + last_period + 1
                chunk = text[start:end]

        chunks.append(chunk.strip())

        # 다음 청크 시작 위치 (overlap 적용)
        start = end - overlap

        # 무한 루프 방지
        if start >= len(text):
            break
        if start <= 0:
            start = end

    return chunks


def process_law(law: Dict[str, Any], law_index: int) -> List[Dict[str, Any]]:
    """
    단일 법령을 처리하여 청크 리스트 생성

    Args:
        law: 법령 데이터
        law_index: 법령 인덱스

    Returns:
        처리된 청크 리스트
    """
    doc_id = law.get("doc_id", f"unknown_{law_index}")
    title = law.get("title", "제목 없음")
    category = law.get("category", "unknown")
    search_keyword = law.get("_search_keyword", "unknown")
    content = law.get("content", "")

    # highlight_content가 있으면 사용 (더 정확한 내용)
    if not content:
        content = law.get("highlight_content", "")

    # 텍스트 정제
    content = clean_text(content)

    if not content:
        return []

    # 청킹
    chunks = chunk_text(content, CHUNK_SIZE, CHUNK_OVERLAP)

    if not chunks:
        return []

    # 각 청크에 메타데이터 추가
    processed_chunks = []
    for chunk_index, chunk in enumerate(chunks):
        processed_chunk = {
            "doc_id": doc_id,
            "chunk_id": f"{doc_id}_chunk_{chunk_index}",
            "chunk_index": chunk_index,
            "total_chunks": len(chunks),
            "title": title,
            "category": category,
            "search_keyword": search_keyword,
            "content": chunk,
            "content_length": len(chunk),
        }
        processed_chunks.append(processed_chunk)

    return processed_chunks


def preprocess_all_laws(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    모든 법령 전처리

    Args:
        raw_data: 원본 데이터

    Returns:
        전처리된 청크 리스트
    """
    laws = raw_data.get("laws", [])
    all_chunks = []

    print(f"\n📝 전처리 시작 (총 {len(laws)}개 법령)")
    print(f"   청크 크기: {CHUNK_SIZE}자")
    print(f"   오버랩: {CHUNK_OVERLAP}자")
    print()

    for idx, law in enumerate(laws, 1):
        if idx % 500 == 0:
            print(f"  진행: {idx}/{len(laws)} ({idx/len(laws)*100:.1f}%)")

        try:
            chunks = process_law(law, idx)
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"  ⚠️  법령 {idx} 처리 실패: {e}")
            continue

    print(f"\n✅ 전처리 완료")
    print(f"   원본 법령: {len(laws)}개")
    print(f"   생성된 청크: {len(all_chunks)}개")
    if len(laws) > 0:
        print(f"   평균 청크/법령: {len(all_chunks)/len(laws):.2f}개")

    return all_chunks


def save_processed_data(chunks: List[Dict[str, Any]], output_file: Path):
    """
    전처리된 데이터 저장

    Args:
        chunks: 청크 리스트
        output_file: 출력 파일 경로
    """
    # 통계 계산
    category_stats = {}
    keyword_stats = {}
    chunk_size_stats = []

    for chunk in chunks:
        category = chunk.get("category", "unknown")
        keyword = chunk.get("search_keyword", "unknown")

        category_stats[category] = category_stats.get(category, 0) + 1
        keyword_stats[keyword] = keyword_stats.get(keyword, 0) + 1
        chunk_size_stats.append(chunk.get("content_length", 0))

    avg_chunk_size = (
        sum(chunk_size_stats) / len(chunk_size_stats) if chunk_size_stats else 0
    )

    output_data = {
        "processed_at": datetime.now().isoformat(),
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "total_chunks": len(chunks),
        "avg_chunk_size": round(avg_chunk_size, 2),
        "category_stats": category_stats,
        "keyword_stats": keyword_stats,
        "chunks": chunks,
    }

    print(f"\n💾 저장 중: {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    file_size_mb = output_file.stat().st_size / 1024 / 1024
    print(f"✅ 저장 완료: {output_file}")
    print(f"   파일 크기: {file_size_mb:.2f} MB")

    print(f"\n📊 통계:")
    print(f"   총 청크: {len(chunks)}개")
    print(f"   평균 청크 크기: {avg_chunk_size:.0f}자")

    print(f"\n   카테고리별 분포 (상위 10개):")
    for cat, count in sorted(
        category_stats.items(), key=lambda x: x[1], reverse=True
    )[:10]:
        print(f"     - 카테고리 {cat}: {count}개")

    print(f"\n   키워드별 분포:")
    for kw, count in sorted(keyword_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"     - {kw}: {count}개")


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("법령 데이터 전처리 및 청킹")
    print("=" * 60)

    # 1. 원본 데이터 로드
    if not INPUT_FILE.exists():
        print(f"❌ 입력 파일을 찾을 수 없습니다: {INPUT_FILE}")
        print("   먼저 collect_law_data.py를 실행하여 데이터를 수집하세요.")
        return

    raw_data = load_raw_data(INPUT_FILE)

    # 2. 전처리 및 청킹
    processed_chunks = preprocess_all_laws(raw_data)

    if not processed_chunks:
        print("❌ 전처리된 청크가 없습니다.")
        return

    # 3. 저장
    output_file = OUTPUT_DIR / "processed_laws.json"
    save_processed_data(processed_chunks, output_file)

    print("\n✅ 모든 작업 완료!")


if __name__ == "__main__":
    main()
