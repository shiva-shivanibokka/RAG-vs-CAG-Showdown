"""
CAG Engine — Context Augmented Generation (Ollama backend)
==========================================================
Loads the entire knowledge base into the LLM context window.
No retrieval step. No vector database. No chunking.
"""

import logging
import time
from pathlib import Path

from ollama import AsyncClient, Client

from src.config import MAX_RETRIES, MAX_TOKENS, OLLAMA_HOST, OLLAMA_MODEL

logger = logging.getLogger(__name__)


class CAGEngine:
    """
    Context Augmented Generation engine backed by a local Ollama model.

    The full knowledge base is placed in the system prompt once at startup.
    Every query sends only the question — the context is already loaded.

    Parameters
    ----------
    knowledge_base_path : str | Path
    model : str
        Ollama model tag, e.g. "llama3.1:8b".
    max_tokens : int
        Maximum tokens to generate (maps to Ollama's num_predict).
    ollama_host : str
        Ollama server URL.
    max_retries : int
        Number of retry attempts on transient failures.
    _client : optional
        Injected Ollama Client — used in tests to avoid a live server.
    """

    def __init__(
        self,
        knowledge_base_path: str | Path,
        model: str = OLLAMA_MODEL,
        max_tokens: int = MAX_TOKENS,
        ollama_host: str = OLLAMA_HOST,
        max_retries: int = MAX_RETRIES,
        _client=None,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self._ollama_host = ollama_host
        self._max_retries = max_retries
        self._client: Client = _client or Client(host=ollama_host)

        kb_path = Path(knowledge_base_path)
        if not kb_path.exists():
            raise FileNotFoundError(f"Knowledge base not found: {kb_path}")
        self._kb_text = kb_path.read_text(encoding="utf-8")
        self._system_prompt = self._build_system_prompt()

        logger.info(
            "CAGEngine ready | kb=%d chars (~%d tokens) | model=%s",
            len(self._kb_text),
            len(self._kb_text) // 4,
            self.model,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_system_prompt(self) -> str:
        return (
            "You are an expert AI/ML assistant. Answer questions ONLY using the "
            "information in the KNOWLEDGE BASE below. If the answer is not there, "
            'say "I don\'t have information about that in my knowledge base."\n\n'
            "Be precise and cite specific concepts from the knowledge base.\n\n"
            f"========== KNOWLEDGE BASE ==========\n{self._kb_text}\n====================================="
        )

    def _chat(self, messages: list[dict]) -> object:
        """Call Ollama with exponential-backoff retry on transient errors."""
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                return self._client.chat(
                    model=self.model,
                    messages=messages,
                    options={"num_predict": self.max_tokens},
                )
            except Exception as exc:
                last_exc = exc
                wait = 2**attempt
                logger.warning(
                    "Ollama call failed (attempt %d/%d): %s. Retrying in %ds.",
                    attempt + 1,
                    self._max_retries,
                    exc,
                    wait,
                )
                time.sleep(wait)
        raise RuntimeError(
            f"Ollama call failed after {self._max_retries} attempts"
        ) from last_exc

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def query(self, question: str) -> dict:
        """Answer a question using the full preloaded knowledge base context."""
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": question},
        ]
        start = time.perf_counter()
        response = self._chat(messages)
        latency = time.perf_counter() - start

        return {
            "answer": response.message.content,
            "latency_seconds": round(latency, 3),
            "input_tokens": response.prompt_eval_count or 0,
            "output_tokens": response.eval_count or 0,
            "model": self.model,
            "method": "CAG",
            "context_used": "Full knowledge base (no retrieval)",
            "retrieved_chunks": None,
        }

    async def query_async(self, question: str) -> dict:
        """Async version of query — used by the parallel benchmark runner."""
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": question},
        ]
        start = time.perf_counter()
        client = AsyncClient(host=self._ollama_host)
        response = await client.chat(
            model=self.model,
            messages=messages,
            options={"num_predict": self.max_tokens},
        )
        latency = time.perf_counter() - start

        return {
            "answer": response.message.content,
            "latency_seconds": round(latency, 3),
            "input_tokens": response.prompt_eval_count or 0,
            "output_tokens": response.eval_count or 0,
            "model": self.model,
            "method": "CAG",
            "context_used": "Full knowledge base (no retrieval)",
            "retrieved_chunks": None,
        }

    def interactive(self) -> None:
        """Launch an interactive Q&A session in the terminal."""
        print("\n" + "=" * 60)
        print(f"  CAG Interactive Session  (model: {self.model})")
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
            print(f"\nCAG: {result['answer']}")
            print(
                f"\n[Latency: {result['latency_seconds']}s | "
                f"Tokens in: {result['input_tokens']:,} | "
                f"Tokens out: {result['output_tokens']:,}]\n"
            )
