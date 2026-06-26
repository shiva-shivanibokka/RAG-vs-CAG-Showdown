"""
One-time script: pre-compute chunk embeddings and save to disk.

Run this locally (not on Render) whenever you update the knowledge base:
    python scripts/precompute_embeddings.py

Requires CF_ACCOUNT_ID and CF_API_TOKEN in your .env file.
Output: knowledge_base/embeddings_cache.npy
Commit that file — the RAGEngine will load it at startup instead of calling the API.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from openai import OpenAI

from src.config import CF_ACCOUNT_ID, CF_API_TOKEN, EMBEDDING_MODEL
from src.rag.engine import chunk_by_topic

KB_PATH = Path(__file__).parent.parent / "knowledge_base" / "aiml_corpus.txt"
CACHE_PATH = Path(__file__).parent.parent / "knowledge_base" / "embeddings_cache.npy"


def main() -> None:
    if not CF_ACCOUNT_ID or not CF_API_TOKEN:
        print("ERROR: CF_ACCOUNT_ID and CF_API_TOKEN must be set in .env")
        sys.exit(1)

    cf_base_url = (
        f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/v1"
    )
    client = OpenAI(api_key=CF_API_TOKEN, base_url=cf_base_url)

    text = KB_PATH.read_text(encoding="utf-8")
    chunks = chunk_by_topic(text)
    print(f"Found {len(chunks)} chunks to embed using {EMBEDDING_MODEL}")

    texts = [c["text"] for c in chunks]
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), 10):
        batch = texts[i : i + 10]
        resp = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        all_embeddings.extend(item.embedding for item in resp.data)
        print(f"  Embedded {min(i + 10, len(texts))}/{len(texts)} chunks")

    embeddings = np.array(all_embeddings, dtype=np.float32)
    np.save(str(CACHE_PATH), embeddings)
    print(f"\nSaved {embeddings.shape} embeddings → {CACHE_PATH}")
    print("Now run: git add knowledge_base/embeddings_cache.npy && git commit -m 'chore: add pre-computed embeddings cache' && git push")


if __name__ == "__main__":
    main()
