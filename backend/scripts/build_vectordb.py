"""
벡터 데이터베이스 구축

사용법:
    python scripts/build_vectordb.py
"""

import os
import json
from typing import List, Dict, Any
from pathlib import Path
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from dotenv import load_dotenv
import time

# 환경변수 로드
load_dotenv()

# 설정
INPUT_FILE = Path("data/processed_laws/processed_laws.json")
CHROMA_DB_PATH = Path("safety_db")
COLLECTION_NAME = "safety_laws"
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100  # 배치당 처리할 청크 수

# OpenAI 클라이언트 초기화
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

openai_client = OpenAI(api_key=openai_api_key)


def load_processed_data(filepath: Path) -> Dict[str, Any]:
    """전처리된 데이터 로드"""
    if not filepath.exists():
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {filepath}")

    print(f"📂 파일 로드 중: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"✅ 총 {data['total_chunks']}개 청크 로드됨")
    return data


def generate_embeddings(
    texts: List[str], batch_size: int = BATCH_SIZE
) -> List[List[float]]:
    """
    OpenAI API로 임베딩 생성 (배치 처리)

    Args:
        texts: 임베딩할 텍스트 리스트
        batch_size: 배치 크기

    Returns:
        임베딩 벡터 리스트
    """
    all_embeddings = []
    total_batches = (len(texts) + batch_size - 1) // batch_size

    print(f"\n🔄 임베딩 생성 중 (총 {len(texts)}개, {total_batches}개 배치)")

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        batch_num = i // batch_size + 1

        print(f"  배치 {batch_num}/{total_batches} ({len(batch)}개)...", end=" ")

        try:
            response = openai_client.embeddings.create(
                model=EMBEDDING_MODEL, input=batch
            )

            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

            print("✅")

            # Rate limit 방지
            if batch_num < total_batches:
                time.sleep(0.5)

        except Exception as e:
            print(f"❌ 에러: {e}")
            # 에러 발생 시 빈 임베딩 추가 (또는 재시도 로직)
            # text-embedding-3-small의 차원은 1536
            all_embeddings.extend([[0.0] * 1536] * len(batch))

    print(f"✅ 임베딩 생성 완료: {len(all_embeddings)}개")
    return all_embeddings


def build_chromadb(chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
    """
    ChromaDB에 데이터 저장

    Args:
        chunks: 청크 리스트
        embeddings: 임베딩 벡터 리스트
    """
    print(f"\n💾 ChromaDB 구축 중...")
    print(f"   경로: {CHROMA_DB_PATH}")
    print(f"   컬렉션: {COLLECTION_NAME}")

    # ChromaDB 클라이언트 초기화
    CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=str(CHROMA_DB_PATH),
        settings=Settings(anonymized_telemetry=False, allow_reset=True),
    )

    # 기존 컬렉션 삭제 (있다면)
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"   기존 컬렉션 삭제됨")
    except:
        pass

    # 새 컬렉션 생성 (cosine similarity 사용)
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "산업안전보건법령 벡터 DB",
            "hnsw:space": "cosine",  # cosine similarity 사용
        },
    )

    # 데이터 준비
    ids = []
    documents = []
    metadatas = []

    for chunk in chunks:
        ids.append(chunk["chunk_id"])
        documents.append(chunk["content"])
        metadatas.append(
            {
                "doc_id": chunk["doc_id"],
                "title": chunk["title"],
                "category": str(chunk.get("category", "unknown")),
                "search_keyword": chunk.get("search_keyword", "unknown"),
                "chunk_index": str(chunk.get("chunk_index", 0)),
                "total_chunks": str(chunk.get("total_chunks", 0)),
            }
        )

    # 배치로 추가
    db_batch_size = 1000
    total_batches = (len(ids) + db_batch_size - 1) // db_batch_size

    print(f"\n   데이터 추가 중 ({total_batches}개 배치)...")

    for i in range(0, len(ids), db_batch_size):
        batch_num = i // db_batch_size + 1
        end_idx = min(i + db_batch_size, len(ids))

        collection.add(
            ids=ids[i:end_idx],
            embeddings=embeddings[i:end_idx],
            documents=documents[i:end_idx],
            metadatas=metadatas[i:end_idx],
        )

        print(f"     배치 {batch_num}/{total_batches} 완료 ({end_idx - i}개)")

    print(f"✅ ChromaDB 구축 완료: {len(ids)}개 청크 저장됨")

    return collection


def test_search(collection):
    """
    벡터 검색 테스트

    Args:
        collection: ChromaDB 컬렉션
    """
    print(f"\n🔍 벡터 검색 테스트...")

    test_queries = [
        "안전모 착용 의무는?",
        "고소작업 시 안전조치",
        "화학물질 취급 기준",
    ]

    for query in test_queries:
        print(f"\n  쿼리: '{query}'")

        try:
            # 임베딩 생성
            query_embedding = (
                openai_client.embeddings.create(model=EMBEDDING_MODEL, input=[query])
                .data[0]
                .embedding
            )

            # 검색
            results = collection.query(query_embeddings=[query_embedding], n_results=3)

            print(f"  상위 3개 결과:")
            if results["documents"] and len(results["documents"][0]) > 0:
                for idx, (doc, metadata, distance) in enumerate(
                    zip(
                        results["documents"][0],
                        results["metadatas"][0],
                        results["distances"][0],
                    ),
                    1,
                ):
                    # Cosine distance를 similarity로 변환
                    similarity = max(0.0, min(1.0, 1 - distance))
                    print(f"    [{idx}] 제목: {metadata.get('title', 'N/A')}")
                    print(f"        유사도: {similarity:.4f} (거리: {distance:.4f})")
                    print(f"        내용: {doc[:80]}...")
            else:
                print("    결과 없음")
        except Exception as e:
            print(f"    ❌ 검색 실패: {e}")


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("벡터 데이터베이스 구축")
    print("=" * 60)

    # 1. 전처리된 데이터 로드
    data = load_processed_data(INPUT_FILE)
    chunks = data["chunks"]

    if not chunks:
        print("❌ 청크 데이터가 없습니다.")
        return

    # 2. 임베딩 생성
    texts = [chunk["content"] for chunk in chunks]
    embeddings = generate_embeddings(texts)

    # 임베딩 개수 확인
    if len(embeddings) != len(chunks):
        print(
            f"⚠️  경고: 임베딩 개수({len(embeddings)})와 청크 개수({len(chunks)})가 일치하지 않습니다."
        )
        min_len = min(len(embeddings), len(chunks))
        embeddings = embeddings[:min_len]
        chunks = chunks[:min_len]
        print(f"   {min_len}개로 조정하여 진행합니다.")

    # 3. ChromaDB 구축
    collection = build_chromadb(chunks, embeddings)

    # 4. 검색 테스트
    test_search(collection)

    print("\n" + "=" * 60)
    print("✅ 모든 작업 완료!")
    print("=" * 60)
    print(f"\n💡 다음 단계:")
    print(f"   1. RAG 서비스 테스트 (이미 구현됨: app/services/rag_service.py)")
    print(f"   2. API 통합 확인 (main.py)")
    print(f"   3. 서버 실행 및 질의응답 테스트")


if __name__ == "__main__":
    main()
