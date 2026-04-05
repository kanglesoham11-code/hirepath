"""
vector_store.py — ChromaDB integration for semantic candidate search.
Stores candidate profiles as embeddings for similarity search.
"""
from typing import Optional
from config import settings

try:
    import chromadb
    from chromadb.utils import embedding_functions
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False


def get_chroma_client():
    if not HAS_CHROMA:
        return None
    try:
        client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        return client
    except Exception as e:
        print(f"[ChromaDB] Init error: {e}")
        return None


def get_candidates_collection():
    client = get_chroma_client()
    if not client:
        return None
    try:
        ef = embedding_functions.DefaultEmbeddingFunction()
        return client.get_or_create_collection("candidates", embedding_function=ef)
    except Exception as e:
        print(f"[ChromaDB] Collection error: {e}")
        return None


def upsert_candidate(candidate_id: int, name: str, profile_text: str, metadata: dict = None):
    """Add or update a candidate in the vector store."""
    col = get_candidates_collection()
    if not col:
        return
    try:
        col.upsert(
            ids=[str(candidate_id)],
            documents=[profile_text],
            metadatas=[{"name": name, **(metadata or {})}],
        )
    except Exception as e:
        print(f"[ChromaDB] Upsert error: {e}")


def search_similar_candidates(query: str, n_results: int = 5, role_id: Optional[int] = None) -> list[dict]:
    """Find candidates semantically similar to a query string."""
    col = get_candidates_collection()
    if not col:
        return []
    try:
        where = {"role_id": str(role_id)} if role_id else None
        results = col.query(query_texts=[query], n_results=n_results, where=where)
        out = []
        for i, doc_id in enumerate(results["ids"][0]):
            out.append({
                "candidate_id": int(doc_id),
                "distance": results["distances"][0][i],
                "metadata": results["metadatas"][0][i],
            })
        return out
    except Exception as e:
        print(f"[ChromaDB] Search error: {e}")
        return []
