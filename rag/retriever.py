"""Property-scoped retrieval with Hugging Face Sentence Transformer embeddings."""

from __future__ import annotations

import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv

from rag.embeddings import (
    document_embedding_function,
    query_embedding_function,
)


load_dotenv()

CHROMA_PATH = os.getenv("CHROMA_PATH").strip()
print(CHROMA_PATH)
client_instance = None


def chroma_client():
    global client_instance
    if client_instance is None:
        Path(CHROMA_PATH).mkdir(parents=True, exist_ok=True)
        client_instance = chromadb.PersistentClient(path=CHROMA_PATH)
    return client_instance


def collection_name(property_id: str) -> str:
    return f"collection_{str(property_id).strip()}"


def get_or_create_property_collection(property_id: str):
    name = collection_name(property_id)
    return chroma_client().get_or_create_collection(
        name=name,
        embedding_function=document_embedding_function(),
        metadata={
            "property_id": str(property_id).strip(),
            "hnsw:space": "cosine",
        },
    )


def property_exists(property_id: str) -> bool:
    try:
        chroma_client().get_collection(
            collection_name(property_id),
            embedding_function=document_embedding_function(),
        )
        return True
    except Exception:
        return False


def retrieve_context(
    query: str,
    property_id: str,
    top_k: int = 8,
    max_distance: float = 0.55,
    extra_queries: list[str] | None = None,
) -> str:
    """Retrieve chunks using Hugging Face embeddings; keep strong cosine hits."""
    collection = chroma_client().get_collection(
        collection_name(property_id),
        embedding_function=document_embedding_function(),
    )
    queries = [query]
    if extra_queries:
        queries.extend(q for q in extra_queries if q and q not in queries)

    query_ef = query_embedding_function()
    ranked: dict[str, tuple[float, str, str]] = {}
    for q in queries:
        embeddings = query_ef([q])
        result = collection.query(
            query_embeddings=embeddings,
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        ids = (result.get("ids") or [[]])[0]
        for doc_id, doc, meta, dist in zip(ids, docs, metas, distances):
            if dist is None or dist > max_distance or not doc:
                continue
            prev = ranked.get(doc_id)
            if prev is None or dist < prev[0]:
                section = (meta or {}).get("section", "general")
                ranked[doc_id] = (float(dist), section, doc)

    if not ranked:
        return ""

    ordered = sorted(ranked.values(), key=lambda item: item[0])[:top_k]
    blocks = [f"[{section}] {text}" for _dist, section, text in ordered]
    return "\n\n".join(blocks)



