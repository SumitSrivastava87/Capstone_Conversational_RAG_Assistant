"""
FAISS-backed vector store with per-intent namespaces.
Each intent maps to its own FAISS index so retrieval stays scoped.
Embeddings use a local HuggingFace sentence-transformer model — no OpenAI key needed.
"""

import os
from pathlib import Path
from typing import Optional

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

INTENTS = ["complaint", "refund", "product_info", "escalate", "general"]
INDEX_DIR = Path(os.getenv("FAISS_INDEX_DIR", "data/indexes"))
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Singleton — model is loaded once and reused across calls
_embed_model: Optional[HuggingFaceEmbeddings] = None


def _embeddings() -> HuggingFaceEmbeddings:
    global _embed_model
    if _embed_model is None:
        _embed_model = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    return _embed_model


def get_index_path(intent: str) -> Path:
    return INDEX_DIR / intent


def load_store(intent: str) -> Optional[FAISS]:
    path = get_index_path(intent)
    if not path.exists():
        return None
    return FAISS.load_local(str(path), _embeddings(), allow_dangerous_deserialization=True)


def save_store(store: FAISS, intent: str) -> None:
    path = get_index_path(intent)
    path.mkdir(parents=True, exist_ok=True)
    store.save_local(str(path))


def add_documents(docs: list, intent: str) -> FAISS:
    """Add LangChain Document objects to the intent namespace, creating index if needed."""
    existing = load_store(intent)
    if existing:
        existing.add_documents(docs)
        save_store(existing, intent)
        return existing
    store = FAISS.from_documents(docs, _embeddings())
    save_store(store, intent)
    return store


def similarity_search(query: str, intent: str, k: int = 4) -> list:
    """Return top-k (Document, score) pairs from the intent namespace."""
    store = load_store(intent)
    if store is None:
        return []
    return store.similarity_search_with_relevance_scores(query, k=k)
