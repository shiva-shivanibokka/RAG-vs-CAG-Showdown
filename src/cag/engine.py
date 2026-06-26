"""
CAG Engine — Context Augmented Generation
==========================================
Loads the entire knowledge base into the LLM context window.
No retrieval step. No vector database. No chunking.
"""

import logging
import time
from pathlib import Path

from openai import AsyncOpenAI, OpenAI

from src.config import MAX_RETRIES, MAX_TOKENS, OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)


class CAGEngine:
    def __init__(
        self,
        knowledge_base_path: str | Path,
        model: str = OPENAI_MODEL,
        max_tokens: int = MAX_TOKENS,
        max_retries: int = MAX_RETRIES,
        _client=None,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self._max_retries = max_retries
        self._client: OpenAI = _client or OpenAI(api_key=OPENAI_API_KEY or "not-configured")

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

    def _chat(self, messages: list[dict], client=None, model: str | None = None) -> object:
        c = client or self._client
        m = model or self.model
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                return c.chat.completions.create(
                    model=m,
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

    def query(self, question: str, llm_config: dict | None = None) -> dict:
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": question},
        ]
        start = time.perf_counter()
        if llm_config:
            kwargs: dict = {"api_key": llm_config["key"]}
            if llm_config.get("base_url"):
                kwargs["base_url"] = llm_config["base_url"]
            client = OpenAI(**kwargs)
            model = llm_config.get("model") or self.model
        else:
            client = None
            model = self.model
        response = self._chat(messages, client=client, model=model)
        latency = time.perf_counter() - start

        return {
            "answer": response.choices[0].message.content,
            "latency_seconds": round(latency, 3),
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
            "model": model,
            "method": "CAG",
            "context_used": "Full knowledge base (no retrieval)",
            "retrieved_chunks": None,
        }

    async def query_async(self, question: str, llm_config: dict | None = None) -> dict:
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": question},
        ]
        start = time.perf_counter()
        kwargs: dict = {"api_key": (llm_config["key"] if llm_config else None) or OPENAI_API_KEY}
        if llm_config and llm_config.get("base_url"):
            kwargs["base_url"] = llm_config["base_url"]
        async_client = AsyncOpenAI(**kwargs)
        model = (llm_config.get("model") if llm_config else None) or self.model
        response = await async_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=self.max_tokens,
        )
        latency = time.perf_counter() - start

        return {
            "answer": response.choices[0].message.content,
            "latency_seconds": round(latency, 3),
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
            "model": model,
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
