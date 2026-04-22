"""
RAG Engine — Retrieval Augmented Generation
============================================
Classic RAG pipeline:
  1. Index phase: Chunk documents → embed chunks → store in FAISS vector DB
  2. Query phase: Embed query → retrieve top-k chunks → generate with Claude

Uses:
  - sentence-transformers for embeddings (all-MiniLM-L6-v2, open-source, free)
  - FAISS for vector similarity search (in-memory, no server needed)
  - Anthropic Claude for generation (same model as CAG for fair comparison)
"""

import time
import re
import numpy as np
import anthropic
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import Optional


# ---------------------------------------------------------------------------
# Chunking helpers
# ---------------------------------------------------------------------------


def chunk_by_topic(text: str) -> list[dict]:
    """
    Split the knowledge base by topic sections (denoted by === TOPIC: ... ===).
    Returns a list of dicts with 'title' and 'text' keys.
    This is a semantic chunking strategy — each chunk is a coherent topic.
    """
    pattern = r"={3,}\nTOPIC: (.+?)\n={3,}\n(.*?)(?=={3,}\nTOPIC:|\Z)"
    matches = re.findall(pattern, text, re.DOTALL)
    chunks = []
    for title, content in matches:
        content = content.strip()
        if content:
            chunks.append({"title": title.strip(), "text": content})
    return chunks


def chunk_fixed_size(text: str, chunk_size: int = 400, overlap: int = 50) -> list[dict]:
    """
    Fixed-size chunking: split text into overlapping windows of ~chunk_size words.
    Falls back option if topic-based chunking yields too few chunks.
    """
    words = text.split()
    chunks = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(words), step):
        chunk_words = words[i : i + chunk_size]
        chunks.append(
            {
                "title": f"chunk_{i // step}",
                "text": " ".join(chunk_words),
            }
        )
    return chunks


# ---------------------------------------------------------------------------
# RAG Engine
# ---------------------------------------------------------------------------


class RAGEngine:
    """
    Retrieval Augmented Generation engine.

    Indexes a knowledge base using FAISS + sentence-transformers, then
    retrieves relevant chunks at query time to ground Claude's answers.

    Parameters
    ----------
    knowledge_base_path : str | Path
        Path to the plain-text knowledge base file.
    model : str
        Anthropic model ID for generation.
    embedding_model_name : str
        Sentence-Transformers model for embeddings.
    top_k : int
        Number of chunks to retrieve per query.
    max_tokens : int
        Maximum tokens to generate per response.
    chunking_strategy : str
        "topic" (semantic) or "fixed" (fixed-size window).
    """

    def __init__(
        self,
        knowledge_base_path: str | Path,
        model: str = "claude-3-5-haiku-20241022",
        embedding_model_name: str = "all-MiniLM-L6-v2",
        top_k: int = 3,
        max_tokens: int = 1024,
        chunking_strategy: str = "topic",
    ):
        self.model = model
        self.top_k = top_k
        self.max_tokens = max_tokens
        self.chunking_strategy = chunking_strategy
        self.client = anthropic.Anthropic()

        print(f"[RAG] Loading embedding model: {embedding_model_name}")
        self.embedder = SentenceTransformer(embedding_model_name)

        # Load and index
        kb_path = Path(knowledge_base_path)
        if not kb_path.exists():
            raise FileNotFoundError(f"Knowledge base not found: {kb_path}")
        raw_text = kb_path.read_text(encoding="utf-8")

        print(f"[RAG] Chunking knowledge base (strategy: {chunking_strategy})")
        self.chunks = self._chunk(raw_text)
        print(f"[RAG] Created {len(self.chunks)} chunks")

        print("[RAG] Building FAISS index...")
        self._index_time = self._build_index()
        print(f"[RAG] Index built in {self._index_time:.3f}s")
        print(f"[RAG] Model: {self.model} | Top-k: {self.top_k}")

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def _chunk(self, text: str) -> list[dict]:
        if self.chunking_strategy == "topic":
            chunks = chunk_by_topic(text)
            if len(chunks) < 3:
                print(
                    "[RAG] Warning: few topic chunks found, falling back to fixed-size"
                )
                chunks = chunk_fixed_size(text)
        else:
            chunks = chunk_fixed_size(text)
        return chunks

    def _build_index(self) -> float:
        """Embed all chunks and build a FAISS inner-product index."""
        start = time.perf_counter()
        texts = [c["text"] for c in self.chunks]
        embeddings = self.embedder.encode(
            texts, show_progress_bar=False, convert_to_numpy=True
        )

        # Normalize for cosine similarity via inner product
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        self.embeddings = embeddings / np.maximum(norms, 1e-10)

        dim = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(
            dim
        )  # Inner product (= cosine after normalization)
        self.index.add(self.embeddings.astype(np.float32))

        return time.perf_counter() - start

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def _retrieve(self, question: str) -> tuple[list[dict], float]:
        """
        Embed the question and retrieve top-k most similar chunks.

        Returns (retrieved_chunks, retrieval_latency_seconds).
        """
        start = time.perf_counter()
        q_emb = self.embedder.encode([question], convert_to_numpy=True)
        q_norm = q_emb / np.maximum(np.linalg.norm(q_emb, axis=1, keepdims=True), 1e-10)

        scores, indices = self.index.search(q_norm.astype(np.float32), self.top_k)
        retrieval_time = time.perf_counter() - start

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0:
                results.append(
                    {
                        "title": self.chunks[idx]["title"],
                        "text": self.chunks[idx]["text"],
                        "similarity_score": round(float(score), 4),
                    }
                )
        return results, retrieval_time

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def _build_prompt(
        self, question: str, retrieved_chunks: list[dict]
    ) -> tuple[str, str]:
        """Build system and user prompts using retrieved chunks as context."""
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            context_parts.append(
                f"--- RETRIEVED CHUNK {i}: {chunk['title']} "
                f"(similarity: {chunk['similarity_score']}) ---\n{chunk['text']}"
            )
        context = "\n\n".join(context_parts)

        system = (
            "You are an expert AI/ML assistant. Answer the question using ONLY the "
            "context chunks provided below. If the answer is not in the context, say "
            "'The retrieved context does not contain enough information to answer this question.'\n\n"
            "Be precise and reference specific information from the retrieved chunks."
        )

        user = f"CONTEXT:\n{context}\n\nQUESTION: {question}"
        return system, user

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def query(self, question: str) -> dict:
        """
        Answer a question using retrieval + generation.

        Returns
        -------
        dict with keys:
            answer, latency_seconds, retrieval_latency_seconds,
            generation_latency_seconds, input_tokens, output_tokens,
            model, method, retrieved_chunks.
        """
        total_start = time.perf_counter()

        # Step 1: Retrieve
        retrieved_chunks, retrieval_latency = self._retrieve(question)

        # Step 2: Generate
        system_prompt, user_prompt = self._build_prompt(question, retrieved_chunks)
        gen_start = time.perf_counter()
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        generation_latency = time.perf_counter() - gen_start

        total_latency = time.perf_counter() - total_start
        answer = next(
            block.text  # type: ignore[union-attr]
            for block in response.content
            if block.type == "text"
        )

        return {
            "answer": answer,
            "latency_seconds": round(total_latency, 3),
            "retrieval_latency_seconds": round(retrieval_latency, 3),
            "generation_latency_seconds": round(generation_latency, 3),
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "model": self.model,
            "method": "RAG",
            "context_used": f"Top-{self.top_k} retrieved chunks",
            "retrieved_chunks": [
                {"title": c["title"], "similarity_score": c["similarity_score"]}
                for c in retrieved_chunks
            ],
        }

    def interactive(self):
        """Launch an interactive Q&A session in the terminal."""
        print("\n" + "=" * 60)
        print("  RAG Interactive Session")
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
                f"\n[Latency: {result['latency_seconds']}s "
                f"(retrieval: {result['retrieval_latency_seconds']}s + "
                f"generation: {result['generation_latency_seconds']}s) | "
                f"Tokens in: {result['input_tokens']:,} | "
                f"Tokens out: {result['output_tokens']:,}]"
            )
            print(f"[Retrieved: {[c['title'] for c in result['retrieved_chunks']]}]\n")
