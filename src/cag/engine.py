"""
CAG Engine — Context Augmented Generation (Gemini backend)
==========================================================
Loads the entire knowledge base into the LLM context window.
No retrieval step. No vector database. No chunking.
"""

import logging
import time
from pathlib import Path

from openai import AsyncOpenAI, OpenAI

from src.config import CEREBRAS_API_KEY, CEREBRAS_BASE_URL, CEREBRAS_MODEL, MAX_RETRIES, MAX_TOKENS

logger = logging.getLogger(__name__)


class CAGEngine:
    def __init__(
        self,
        knowledge_base_path: str | Path,
        model: str = CEREBRAS_MODEL,
        max_tokens: int = MAX_TOKENS,
        max_retries: int = MAX_RETRIES,
        _client=None,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self._max_retries = max_retries
        self._client: OpenAI = _client or OpenAI(
            api_key=CEREBRAS_API_KEY,
            base_url=CEREBRAS_BASE_URL,
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

    def _build_system_prompt(self) -> str:
        return (
            "You are an expert AI/ML assistant. Answer questions ONLY using the "
            "information in the KNOWLEDGE BASE below. If the answer is not there, "
            'say "I don\'t have information about that in my knowledge base."\n\n'
            "Be precise and cite specific concepts from the knowledge base.\n\n"
            f"========== KNOWLEDGE BASE ==========\n{self._kb_text}\n====================================="
        )

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
                    "AI call failed (attempt %d/%d): %s. Retrying in %ds.",
                    attempt + 1, self._max_retries, exc, wait,
                )
                time.sleep(wait)
        raise RuntimeError(
            f"AI call failed after {self._max_retries} attempts: {last_exc}"
        ) from last_exc

    def query(self, question: str) -> dict:
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
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": question},
        ]
        start = time.perf_counter()
        async_client = AsyncOpenAI(api_key=CEREBRAS_API_KEY, base_url=CEREBRAS_BASE_URL)
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
