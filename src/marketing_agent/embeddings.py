"""
Marketing Intelligence Agent — Pinecone Embeddings & RAG
Embeds insights, stores in Pinecone, supports semantic retrieval
"""
import logging
import uuid
import hashlib
from typing import List, Dict, Any, Optional
from shared import config
from shared.db import get_conn

logger = logging.getLogger("marketing_agent.embeddings")

# ── Embedding model (sentence-transformers, no API key needed) ───────────────
_embed_model = None


def _get_embed_model():
    global _embed_model
    if _embed_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embed_model = SentenceTransformer(config.EMBEDDING_MODEL)
            logger.info(f"Loaded embedding model: {config.EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    return _embed_model


def _embed_text(text: str) -> List[float]:
    model = _get_embed_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


# ── Pinecone client ──────────────────────────────────────────────────────────
_pinecone_index = None


def _get_pinecone_index():
    global _pinecone_index
    if _pinecone_index is not None:
        return _pinecone_index

    if not config.PINECONE_API_KEY:
        logger.warning("PINECONE_API_KEY not set — using in-memory FAISS fallback")
        return None

    try:
        from pinecone import Pinecone, ServerlessSpec
        pc = Pinecone(api_key=config.PINECONE_API_KEY)

        existing = [i.name for i in pc.list_indexes()]
        if config.PINECONE_INDEX_NAME not in existing:
            pc.create_index(
                name=config.PINECONE_INDEX_NAME,
                dimension=config.EMBEDDING_DIM,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=config.PINECONE_ENVIRONMENT),
            )
            logger.info(f"Created Pinecone index: {config.PINECONE_INDEX_NAME}")

        _pinecone_index = pc.Index(config.PINECONE_INDEX_NAME)
        logger.info("Connected to Pinecone index")
        return _pinecone_index
    except Exception as e:
        logger.error(f"Pinecone init failed: {e}")
        return None


# ── In-memory FAISS fallback ─────────────────────────────────────────────────
_faiss_store: List[Dict] = []


def _faiss_upsert(vector_id: str, embedding: List[float], metadata: Dict):
    _faiss_store.append({"id": vector_id, "embedding": embedding, "metadata": metadata})


def _faiss_query(query_embedding: List[float], top_k: int, filter_pid: Optional[str] = None) -> List[Dict]:
    import math
    results = []
    for item in _faiss_store:
        if filter_pid and item["metadata"].get("property_id") != filter_pid:
            continue
        # Cosine similarity
        a, b = query_embedding, item["embedding"]
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        score = dot / (norm_a * norm_b + 1e-9)
        results.append({**item["metadata"], "_score": score})
    results.sort(key=lambda x: x["_score"], reverse=True)
    return results[:top_k]


# ── Public API ────────────────────────────────────────────────────────────────

def is_already_processed(property_id: str) -> bool:
    """Check SQLite to see if this property has been embedded before"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM market_insights WHERE property_id = ? AND embedded = 1",
            (property_id,),
        ).fetchone()
        return row["cnt"] > 0


def embed_and_store(property_id: str, insights: List[Dict[str, str]]):
    """Embed each insight and upsert into Pinecone (or FAISS fallback)"""
    index = _get_pinecone_index()
    vectors = []

    for item in insights:
        text = item["content"]
        vector_id = f"{property_id}-{hashlib.md5(text.encode()).hexdigest()[:8]}"
        embedding = _embed_text(text)
        metadata = {
            "property_id": property_id,
            "insight_type": item["type"],
            "content": text,
        }

        if index is not None:
            vectors.append({"id": vector_id, "values": embedding, "metadata": metadata})
        else:
            _faiss_upsert(vector_id, embedding, metadata)

    if index is not None and vectors:
        index.upsert(vectors=vectors)
        logger.info(f"Upserted {len(vectors)} vectors to Pinecone for {property_id}")

    # Mark as embedded in SQLite
    with get_conn() as conn:
        conn.execute(
            "UPDATE market_insights SET embedded = 1 WHERE property_id = ?",
            (property_id,),
        )
    logger.info(f"Embeddings stored for property {property_id}")


def query_insights(
    query: str, property_id: Optional[str] = None, top_k: int = 5
) -> List[Dict[str, Any]]:
    """Semantic search over stored market insights"""
    query_embedding = _embed_text(query)
    index = _get_pinecone_index()

    if index is not None:
        filter_dict = {"property_id": {"$eq": property_id}} if property_id else {}
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict if filter_dict else None,
        )
        matches = [
            {
                "content": m.metadata.get("content", ""),
                "insight_type": m.metadata.get("insight_type", ""),
                "property_id": m.metadata.get("property_id", ""),
                "score": round(m.score, 4),
            }
            for m in results.matches
        ]
    else:
        raw = _faiss_query(query_embedding, top_k=top_k, filter_pid=property_id)
        matches = [
            {
                "content": r.get("content", ""),
                "insight_type": r.get("insight_type", ""),
                "property_id": r.get("property_id", ""),
                "score": round(r.get("_score", 0.0), 4),
            }
            for r in raw
        ]

    logger.info(f"RAG query returned {len(matches)} results")
    return matches
