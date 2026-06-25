"""
CAG Engine — Context Augmented Generation (Cloudflare Workers AI backend)
=========================================================================
Loads the entire knowledge base into the LLM context window.
No retrieval step. No vector database. No chunking.
"""

import logging
import time
from pathlib import Path

from openai import AsyncOpenAI, OpenAI

from src.config import CF_ACCOUNT_ID, CF_API_TOKEN, CF_MODEL, MAX_RETRIES, MAX_TOKENS

logger = logging.getLogger(__name__)

_CF_BASE_URL = (
    f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/v1"
)


class CAGEngine:
    """
    Context Augmented Generation engine backed by Cloudflare Workers AI.

    The full knowledge base is placed in the system prompt once at startup.
    Every query sends only the question — the context is already loaded.

    Parameters
    ----------
    knowledge_base_path : str | Path
    model : str
        Cloudflare Workers AI model tag, e.g. "@cf/meta/llama-3.1-8b-instruct".
    max_tokens : int
        Maximum tokens to generate.
    max_retries : int
        Retry attempts on transient failures.
    _client : optional
        Injected OpenAI-compatible client — used in tests to avoid live API calls.
    """

    def __init__(
        self,
        knowledge_base_path: str | Path,
        model: str = CF_MODEL,
        max_tokens: int = MAX_TOKENS,
        max_retries: int = MAX_RETRIES,
        _client=None,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self._max_retries = max_retries
        self._client: OpenAI = _client or OpenAI(
            api_key=CF_API_TOKEN,
            base_url=_CF_BASE_URL,
        )

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
        """Call Cloudflare Workers AI with exponential-backoff retry."""
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
        """Answer a question using the full preloaded knowledge base context."""
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": question},
        ]
        start = time.perf_counter()
        response = self._chat(messages)
        latency = time.perf_counter() - start

        return {
            "answer": response.choices[0].message.content,
            "latency_seconds": round(latency, 3),
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
            "model": self.model,
            "method": "CAG",
            "context_used": "Full knowledge base (no retrieval)",
            "retrieved_chunks": None,
        }

    async def query_async(self, question: str) -> dict:
        """Async version — used by the parallel benchmark runner."""
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": question},
        ]
        start = time.perf_counter()
        async_client = AsyncOpenAI(api_key=CF_API_TOKEN, base_url=_CF_BASE_URL)
        response = await async_client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
        )
        latency = time.perf_counter() - start

        return {
            "answer": response.choices[0].message.content,
            "latency_seconds": round(latency, 3),
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
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
