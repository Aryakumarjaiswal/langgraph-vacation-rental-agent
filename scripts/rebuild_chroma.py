"""Rebuild Chroma collections with Hugging Face embeddings."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env", override=True)

import pandas as pd

from rag.chunking import (
    chunks_from_summary,
    rebuild_summary_column,
    resolve_property_id,
)
from rag.retriever import (
    chroma_client,
    collection_name,
    get_or_create_property_collection,
)

CHROMA_PATH = os.getenv(
    "CHROMA_PATH",
    str(ROOT / "chroma_db" / "UNITS_INFO_CHUNCK"),
).strip()
FINAL_DATA_PATH = os.getenv(
    "FINAL_DATA_PATH",
    str(ROOT / "data" / "final_data.xlsx"),
).strip()


def main() -> None:
    path = Path(FINAL_DATA_PATH)
    if not path.exists():
        raise SystemExit(f"Missing {path}. Put final_data.xlsx in data/ first.")

    df = pd.read_excel(path)
    df = rebuild_summary_column(df)
    Path(CHROMA_PATH).mkdir(parents=True, exist_ok=True)
    client = chroma_client()

    stored = 0
    for _, row in df.iterrows():
        try:
            property_id = resolve_property_id(row)
        except ValueError:
            continue
        chunks = chunks_from_summary(str(row["summary"]), property_id)
        if not chunks:
            continue
        name = collection_name(property_id)
        try:
            client.delete_collection(name)
        except Exception:
            pass
        
        collection = get_or_create_property_collection(property_id)
        
        collection.add(
            documents=[c["text"] for c in chunks],
            metadatas=[
                {"section": c["section"], "property_id": c["property_id"]}
                for c in chunks 
            ],
            ids=[f"{property_id}_{i}" for i in range(len(chunks))],
        )
        stored += 1
        print(f"Indexed property {property_id} ({len(chunks)} chunks)")

    print(f"\nDone. Indexed {stored} properties into {CHROMA_PATH}")
    print(
        "Embedding model:",
        os.getenv("EMBEDDING_MODEL","BAAI/bge-small-en-v1.5"),
    )


if __name__ == "__main__":
    main()
