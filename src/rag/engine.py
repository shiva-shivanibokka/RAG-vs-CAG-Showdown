"""
RAG Engine — Retrieval Augmented Generation (Cloudflare Workers AI backend)
===========================================================================
1. Index: chunk -> embed (fastembed / ONNX, no PyTorch) -> FAISS
2. Query: embed question -> top-k retrieval -> Cloudflare AI generation
"""

import logging
import re
import time
from pathlib import Path

import faiss
import numpy as np
from fastembed import TextEmbedding
from openai import AsyncOpenAI, OpenAI

from src.config import (
    CF_ACCOUNT_ID,
    CF_API_TOKEN,
    CF_MODEL,
    EMBEDDING_MODEL,
    MAX_RETRIES,
    MAX_TOKENS,
    RAG_TOP_K,
)

logger = logging.getLogger(__name__)

_CF_BASE_URL = (
    f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/v1"
)


# ---------------------------------------------------------------------------
# Chunking helpers
# ---------------------------------------------------------------------------


def chunk_by_topic(text: str) -> list[dict]:
    """Split on === TOPIC: ... === markers. Returns list of {title, text} dicts."""
    pattern = r"={3,}\nTOPIC: (.+?)\n={3,}\n(.*?)(?=={3,}\nTOPIC:|\Z)"
    matches = re.findall(pattern, text, re.DOTALL)
    return [
        {"title": title.strip(), "text": content.strip()}
        for title, content in matches
        if content.strip()
    ]


def chunk_fixed_size(text: str, chunk_size: int = 400, overlap: int = 50) -> list[dict]:
    """Sliding-window word chunking with overlap."""
    words = text.split()
    step = max(1, chunk_size - overlap)
    chunks = []
    for i in range(0, len(words), step):
        chunk_words = words[i : i + chunk_size]
        chunks.append({"title": f"chunk_{i // step}", "text": " ".join(chunk_words)})
    return chunks


# ---------------------------------------------------------------------------
# RAG Engine
# ---------------------------------------------------------------------------


class RAGEngine:
    """
    Retrieval Augmented Generation backed by FAISS + Cloudflare Workers AI.

    Parameters
    ----------
    knowledge_base_path : str | Path
    model : str
        Cloudflare Workers AI model tag.
    embedding_model_name : str
        sentence-transformers model for embedding (runs locally).
    top_k : int
        Number of chunks to retrieve per query.
    max_tokens : int
        Maximum tokens to generate.
    max_retries : int
    chunking_strategy : str
        "topic" (semantic, preferred) or "fixed" (fallback).
    _client : optional
        Injected OpenAI-compatible client for tests.
    """

    def __init__(
        self,
        knowledge_base_path: str | Path,
        model: str = CF_MODEL,
        embedding_model_name: str = EMBEDDING_MODEL,
        top_k: int = RAG_TOP_K,
        max_tokens: int = MAX_TOKENS,
        max_retries: int = MAX_RETRIES,
        chunking_strategy: str = "topic",
        _client=None,
    ):
        self.model = model
        self.top_k = top_k
        self.max_tokens = max_tokens
        self._max_retries = max_retries
        self._client: OpenAI = _client or OpenAI(
            api_key=CF_API_TOKEN,
            base_url=_CF_BASE_URL,
        )

        kb_path = Path(knowledge_base_path)
        if not kb_path.exists():
            raise FileNotFoundError(f"Knowledge base not found: {kb_path}")

        logger.info("RAG | loading embedding model: %s", embedding_model_name)
        self.embedder = TextEmbedding(embedding_model_name)

        raw_text = kb_path.read_text(encoding="utf-8")
        self.chunks = self._chunk(raw_text, chunking_strategy)
        logger.info(
            "RAG | %d chunks created (strategy: %s)", len(self.chunks), chunking_strategy
        )

        index_time = self._build_index()
        logger.info(
            "RAG | FAISS index built in %.3fs | model=%s | top_k=%d",
            index_time,
            model,
            top_k,
        )

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def _chunk(self, text: str, strategy: str) -> list[dict]:
        if strategy == "topic":
            chunks = chunk_by_topic(text)
            if len(chunks) < 3:
                logger.warning(
                    "Too few topic chunks (%d); falling back to fixed-size.", len(chunks)
                )
                chunks = chunk_fixed_size(text)
        else:
            chunks = chunk_fixed_size(text)
        return chunks

    def _build_index(self) -> float:
        start = time.perf_counter()
        texts = [c["text"] for c in self.chunks]
        embeddings = np.array(list(self.embedder.embed(texts)))
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        self._embeddings = embeddings / np.maximum(norms, 1e-10)
        dim = self._embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dim)
        self._index.add(self._embeddings.astype(np.float32))
        return time.perf_counter() - start

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def _retrieve(self, question: str) -> tuple[list[dict], float]:
        start = time.perf_counter()
        q_emb = np.array(list(self.embedder.embed([question])))
        q_norm = q_emb / np.maximum(
            np.linalg.norm(q_emb, axis=1, keepdims=True), 1e-10
        )
        scores, indices = self._index.search(q_norm.astype(np.float32), self.top_k)
        retrieval_time = time.perf_counter() - start

        results = [
            {
                "title": self.chunks[idx]["title"],
                "text": self.chunks[idx]["text"],
                "similarity_score": round(float(score), 4),
            }
            for score, idx in zip(scores[0], indices[0])
            if idx >= 0
        ]
        return results, retrieval_time

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def _build_messages(self, question: str, retrieved_chunks: list[dict]) -> list[dict]:
        context = "\n\n".join(
            f"--- CHUNK {i}: {c['title']} (score: {c['similarity_score']}) ---\n{c['text']}"
            for i, c in enumerate(retrieved_chunks, 1)
        )
        system = (
            "You are an expert AI/ML assistant. Answer using ONLY the context chunks below. "
            "If the answer is not in the context, say 'The retrieved context does not contain "
            "enough information to answer this question.'\n\nBe precise and reference the chunks."
        )
        user = f"CONTEXT:\n{context}\n\nQUESTION: {question}"
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]

    def _chat(self, messages: list[dict]) -> object:
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                return self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                )
            except Exception as exc:
                last_exc = exc
                wait = 2**attempt
                logger.warning(
                    "CF AI call failed (attempt %d/%d): %s. Retrying in %ds.",
                    attempt + 1,
                    self._max_retries,
                    exc,
                    wait,
                )
                time.sleep(wait)
        raise RuntimeError(
            f"CF AI call failed after {self._max_retries} attempts"
        ) from last_exc

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def query(self, question: str) -> dict:
        """Retrieve top-k chunks and generate an answer."""
        total_start = time.perf_counter()
        retrieved_chunks, retrieval_latency = self._retrieve(question)

        messages = self._build_messages(question, retrieved_chunks)
        gen_start = time.perf_counter()
        response = self._chat(messages)
        generation_latency = time.perf_counter() - gen_start
        total_latency = time.perf_counter() - total_start

        return {
            "answer": response.choices[0].message.content,
            "latency_seconds": round(total_latency, 3),
            "retrieval_latency_seconds": round(retrieval_latency, 3),
            "generation_latency_seconds": round(generation_latency, 3),
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
            "model": self.model,
            "method": "RAG",
            "context_used": f"Top-{self.top_k} retrieved chunks",
            "retrieved_chunks": [
                {"title": c["title"], "similarity_score": c["similarity_score"]}
                for c in retrieved_chunks
            ],
        }

    async def query_async(self, question: str) -> dict:
        """Async version — retrieval is sync (local FAISS), only generation is async."""
        total_start = time.perf_counter()
        retrieved_chunks, retrieval_latency = self._retrieve(question)

        messages = self._build_messages(question, retrieved_chunks)
        gen_start = time.perf_counter()
        async_client = AsyncOpenAI(api_key=CF_API_TOKEN, base_url=_CF_BASE_URL)
        response = await async_client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
        )
        generation_latency = time.perf_counter() - gen_start
        total_latency = time.perf_counter() - total_start

        return {
            "answer": response.choices[0].message.content,
            "latency_seconds": round(total_latency, 3),
            "retrieval_latency_seconds": round(retrieval_latency, 3),
            "generation_latency_seconds": round(generation_latency, 3),
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
            "model": self.model,
            "method": "RAG",
            "context_used": f"Top-{self.top_k} retrieved chunks",
            "retrieved_chunks": [
                {"title": c["title"], "similarity_score": c["similarity_score"]}
                for c in retrieved_chunks
            ],
        }

    def interactive(self) -> None:
        print("\n" + "=" * 60)
        print(f"  RAG Interactive Session  (model: {self.model})")
        print("  Type 'quit' or 'exit' to stop")
        print("=" * 60 + "\n")

        while True:
            try:
                question = input("You: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting.")
                break
            if not question:
                continue
            if question.lower() in {"quit", "exit", "q"}:
                print("Goodbye.")
                break

            result = self.query(question)
            print(f"\nRAG: {result['answer']}")
            print(
                f"\n[Total: {result['latency_seconds']}s "
                f"(retrieval: {result['retrieval_latency_seconds']}s + "
                f"generation: {result['generation_latency_seconds']}s) | "
                f"Tokens in: {result['input_tokens']:,} | out: {result['output_tokens']:,}]"
            )
            print(f"[Retrieved: {[c['title'] for c in result['retrieved_chunks']]}]\n")
