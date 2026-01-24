"""
RAG (Retrieval-Augmented Generation) 서비스

법령 데이터를 벡터화하여 저장하고 유사도 검색을 수행합니다.
"""
import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 설정
CHROMA_DB_PATH = Path("safety_db")
COLLECTION_NAME = "safety_laws"
EMBEDDING_MODEL = "text-embedding-3-small"
TOP_K = 5


class RAGService:
    """RAG 서비스 클래스"""

    def __init__(self):
        """RAG 서비스 초기화"""
        # OpenAI 클라이언트 초기화
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

        self.openai_client = OpenAI(api_key=openai_api_key)
        self.embedding_model = EMBEDDING_MODEL

        # ChromaDB 클라이언트 초기화
        CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)

        self.chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_DB_PATH),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # 컬렉션 가져오기 또는 생성
        try:
            self.collection = self.chroma_client.get_collection(name=COLLECTION_NAME)
        except Exception:
            self.collection = self.chroma_client.create_collection(
                name=COLLECTION_NAME,
                metadata={
                    "description": "산업안전보건 법령 데이터",
                    "hnsw:space": "cosine"  # cosine similarity 사용
                }
            )

    def get_embedding(self, text: str) -> List[float]:
        """
        텍스트를 임베딩 벡터로 변환

        Args:
            text: 임베딩할 텍스트

        Returns:
            임베딩 벡터
        """
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"임베딩 생성 실패: {e}")

    def load_and_store_laws(self, processed_data_path: Optional[str] = None) -> int:
        """
        전처리된 법령 데이터를 로드하여 벡터 저장소에 저장

        Args:
            processed_data_path: 전처리된 데이터 파일 경로 (None이면 자동 탐색)

        Returns:
            저장된 청크 수
        """
        # 파일 경로 결정
        if processed_data_path:
            data_path = Path(processed_data_path)
        else:
            # data/processed_laws 디렉토리에서 가장 최근 파일 찾기
            processed_dir = Path("data/processed_laws")
            if not processed_dir.exists():
                raise FileNotFoundError("전처리된 데이터 디렉토리를 찾을 수 없습니다.")

            json_files = list(processed_dir.glob("processed_laws_*.json"))
            if not json_files:
                raise FileNotFoundError("전처리된 데이터 파일을 찾을 수 없습니다.")

            # 가장 최근 파일 선택
            data_path = max(json_files, key=lambda p: p.stat().st_mtime)

        print(f"📂 데이터 파일 로드: {data_path}")

        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        chunks = data.get("chunks", [])
        print(f"   총 {len(chunks)}개 청크 로드됨")

        # 기존 데이터 삭제 (전체 재로드)
        try:
            self.chroma_client.delete_collection(name=COLLECTION_NAME)
            self.collection = self.chroma_client.create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "산업안전보건 법령 데이터"}
            )
        except Exception:
            pass

        # 배치 처리로 임베딩 및 저장
        batch_size = 100
        total_stored = 0

        print("\n📥 벡터 저장 시작...")

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            # 배치별로 처리
            ids = []
            texts = []
            embeddings = []
            metadatas = []

            for chunk in batch:
                chunk_id = chunk.get("chunk_id", f"chunk_{i + len(ids)}")
                chunk_text = chunk.get("chunk_text", "")

                if not chunk_text:
                    continue

                # 임베딩 생성
                try:
                    embedding = self.get_embedding(chunk_text)
                except Exception as e:
                    print(f"   ⚠️  청크 {chunk_id} 임베딩 실패: {e}")
                    continue

                ids.append(chunk_id)
                texts.append(chunk_text)
                embeddings.append(embedding)

                # 메타데이터 구성
                metadata = {
                    "doc_id": chunk.get("doc_id", ""),
                    "title": chunk.get("title", ""),
                    "category": chunk.get("category", ""),
                    "category_name": chunk.get("category_name", ""),
                    "filepath": chunk.get("filepath", ""),
                    "keyword": chunk.get("keyword", ""),
                    "chunk_index": str(chunk.get("chunk_index", 0)),
                    "total_chunks": str(chunk.get("total_chunks", 0))
                }
                metadatas.append(metadata)

            # ChromaDB에 저장
            if ids:
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas
                )
                total_stored += len(ids)
                print(f"   진행 중: {total_stored}/{len(chunks)}개 저장됨")

        print(f"\n✅ 벡터 저장 완료: {total_stored}개 청크")
        return total_stored

    def search(
        self,
        query: str,
        top_k: int = TOP_K,
        law_only: bool = False,
        min_law_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        쿼리와 유사한 법령 청크 검색

        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            law_only: True면 법령(카테고리 1)만 검색
            min_law_results: 법령 검색 최소 결과 수 (부족하면 전체 검색)

        Returns:
            검색 결과 리스트 (메타데이터 포함)
        """
        try:
            # 쿼리 임베딩
            query_embedding = self.get_embedding(query)

            # 1차 검색: 카테고리 1 (산업안전보건법령)만 검색
            if law_only:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k * 2,  # 여유있게 검색
                    where={"category": "1"}  # 카테고리 1만
                )

                # 결과가 충분한지 확인
                num_results = len(results["ids"][0]) if results["ids"] and results["ids"][0] else 0

                # 결과가 부족하면 전체 검색
                if num_results < min_law_results:
                    results = self.collection.query(
                        query_embeddings=[query_embedding],
                        n_results=top_k
                    )
            else:
                # 전체 검색
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k
                )

            # 결과 포맷팅
            formatted_results = []

            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    distance = results["distances"][0][i] if results["distances"] else 0

                    # Cosine distance를 similarity로 변환
                    # Cosine distance: 0 (identical) ~ 2 (opposite)
                    # Cosine similarity: 1 (identical) ~ -1 (opposite)
                    # similarity = 1 - distance
                    similarity = 1 - distance

                    # 음수 similarity 방지 (클리핑)
                    similarity = max(0.0, min(1.0, similarity))

                    result = {
                        "chunk_id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": distance,
                        "similarity": similarity  # similarity 추가
                    }
                    formatted_results.append(result)

            return formatted_results[:top_k]

        except Exception as e:
            raise Exception(f"검색 실패: {e}")

    def search_with_category_priority(
        self,
        query: str,
        top_k: int = TOP_K
    ) -> Dict[str, Any]:
        """
        카테고리별 우선순위 검색 (법령 우선)

        1순위: 카테고리 1 (산업안전보건법령)
        2순위: 전체 검색 (결과 부족 시)

        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 수

        Returns:
            검색 결과 및 메타 정보
        """
        # 1단계: 법령만 검색
        law_results = self.search(query, top_k=top_k, law_only=True, min_law_results=3)

        # 2단계: 결과가 부족하면 전체 검색
        if len(law_results) < 3:
            all_results = self.search(query, top_k=top_k, law_only=False)

            return {
                "search_type": "fallback",  # 전체 검색으로 폴백
                "law_results_count": len(law_results),
                "results": all_results,
                "message": "법령 검색 결과가 부족하여 전체 문서를 검색했습니다."
            }

        return {
            "search_type": "law_only",  # 법령만 검색
            "results": law_results,
            "message": "산업안전보건법령에서 검색했습니다."
        }

    def get_context_from_query(
        self,
        query: str,
        top_k: int = TOP_K,
        law_only: bool = True
    ) -> str:
        """
        쿼리에 대한 컨텍스트 문자열 생성 (법령 우선)

        Args:
            query: 검색 쿼리
            top_k: 사용할 최대 결과 수
            law_only: True면 법령 우선 검색

        Returns:
            컨텍스트 문자열
        """
        if law_only:
            # 법령 우선 검색 사용
            search_result = self.search_with_category_priority(query, top_k)
            results = search_result.get("results", [])
        else:
            results = self.search(query, top_k)

        if not results:
            return ""

        context_parts = []
        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            title = metadata.get("title", "제목 없음")
            category = metadata.get("category", "")
            category_name = metadata.get("category_name", category)
            text = result.get("text", "")

            context_parts.append(
                f"[참조 {i}] {title} (카테고리: {category_name})\n{text}\n"
            )

        return "\n".join(context_parts)


def format_context_for_llm(search_results: List[Dict[str, Any]]) -> str:
    """
    검색 결과를 LLM 컨텍스트로 포맷팅

    Args:
        search_results: 검색 결과 리스트 (search_with_category_priority의 results 형식)

    Returns:
        포맷팅된 컨텍스트 문자열
    """
    if not search_results:
        return "관련 법령을 찾을 수 없습니다."

    context_parts = []
    for idx, result in enumerate(search_results, 1):
        metadata = result.get("metadata", {})
        title = metadata.get("title", "제목 없음")
        text = result.get("text", "")

        # similarity가 이미 계산되어 있으면 사용, 없으면 distance에서 계산
        similarity = result.get("similarity")
        if similarity is None:
            distance = result.get("distance", 0)
            similarity = max(0.0, min(1.0, 1 - distance))

        context_parts.append(
            f"[법령 {idx}] {title}\n"
            f"내용: {text}\n"
            f"(유사도: {similarity:.2%})\n"
        )

    return "\n".join(context_parts)


# 전역 인스턴스 (선택적)
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """
    RAG 서비스 싱글톤 인스턴스 반환

    Returns:
        RAGService 인스턴스
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
