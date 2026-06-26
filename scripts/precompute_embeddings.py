"""
One-time script: pre-compute chunk embeddings and save to disk.

Run this locally (not on Render). Requires fastembed:
    pip install fastembed
    python scripts/precompute_embeddings.py

Uses BAAI/bge-small-en-v1.5 (same model as CF Workers AI) — vectors are
fully compatible with query-time CF embeddings.

Output: knowledge_base/embeddings_cache.npy
Commit that file — the RAGEngine loads it at startup instead of calling any API.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np

from src.rag.engine import chunk_by_topic

KB_PATH = Path(__file__).parent.parent / "knowledge_base" / "aiml_corpus.txt"
CACHE_PATH = Path(__file__).parent.parent / "knowledge_base" / "embeddings_cache.npy"

MODEL_NAME = "BAAI/bge-small-en-v1.5"


def main() -> None:
    try:
        from fastembed import TextEmbedding
    except ImportError:
        print("fastembed not found. Install it with:  pip install fastembed")
        sys.exit(1)

    text = KB_PATH.read_text(encoding="utf-8")
    chunks = chunk_by_topic(text)
    texts = [c["text"] for c in chunks]
    print(f"Found {len(chunks)} chunks. Loading {MODEL_NAME} locally...")

    model = TextEmbedding(MODEL_NAME)
    embeddings = np.array(list(model.embed(texts)), dtype=np.float32)

    np.save(str(CACHE_PATH), embeddings)
    print(f"Saved {embeddings.shape} embeddings → {CACHE_PATH}")
    print("\nNext steps:")
    print("  git add knowledge_base/embeddings_cache.npy")
    print('  git commit -m "chore: add pre-computed embeddings cache"')
    print("  git push")


if __name__ == "__main__":
    main()
