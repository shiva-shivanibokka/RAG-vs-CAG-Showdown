"""
CAG Engine — Context Augmented Generation
==========================================
Loads the entire knowledge base into the LLM's context window.
No retrieval step. No vector database. No chunking.

The full corpus is placed in the system prompt. Claude's 200K token
context window makes this feasible for small-to-medium knowledge bases.
"""

import time
import anthropic
from pathlib import Path
from typing import Optional


class CAGEngine:
    """
    Context Augmented Generation engine using the Anthropic API.

    The entire knowledge base is preloaded into the system prompt.
    Each query is answered by the model with full access to all documents
    simultaneously — no retrieval, no chunking, no vector database.

    Parameters
    ----------
    knowledge_base_path : str | Path
        Path to the plain-text knowledge base file.
    model : str
        Anthropic model ID to use.
    max_tokens : int
        Maximum tokens to generate per response.
    """

    def __init__(
        self,
        knowledge_base_path: str | Path,
        model: str = "claude-3-5-haiku-20241022",
        max_tokens: int = 1024,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.client = anthropic.Anthropic()

        # Load the full knowledge base once at startup
        self.knowledge_base_path = Path(knowledge_base_path)
        self.knowledge_base_text = self._load_knowledge_base()

        # Build the system prompt — this is the "context" in CAG
        self.system_prompt = self._build_system_prompt()

        print(
            f"[CAG] Knowledge base loaded: {len(self.knowledge_base_text):,} characters"
        )
        print(f"[CAG] Estimated tokens: ~{len(self.knowledge_base_text) // 4:,}")
        print(f"[CAG] Model: {self.model}")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_knowledge_base(self) -> str:
        """Read the full knowledge base from disk."""
        if not self.knowledge_base_path.exists():
            raise FileNotFoundError(
                f"Knowledge base not found: {self.knowledge_base_path}"
            )
        return self.knowledge_base_path.read_text(encoding="utf-8")

    def _build_system_prompt(self) -> str:
        """Construct the system prompt that embeds the full knowledge base."""
        return f"""You are an expert AI/ML assistant with deep knowledge of the topics below.

Answer questions ONLY using the information provided in the KNOWLEDGE BASE below.
If the answer is not contained in the knowledge base, say "I don't have information about that in my knowledge base."

Be precise, thorough, and cite specific concepts from the knowledge base in your answers.
When relevant, compare or contrast related concepts to give a complete picture.

========== KNOWLEDGE BASE ==========
{self.knowledge_base_text}
=====================================
"""

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def query(self, question: str) -> dict:
        """
        Answer a question using the full preloaded context.

        Parameters
        ----------
        question : str
            The user's question.

        Returns
        -------
        dict with keys:
            answer (str): The model's response.
            latency_seconds (float): End-to-end wall-clock time.
            input_tokens (int): Number of input tokens consumed.
            output_tokens (int): Number of output tokens generated.
            model (str): Model used.
            method (str): Always "CAG".
        """
        start_time = time.perf_counter()

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            messages=[{"role": "user", "content": question}],
        )

        latency = time.perf_counter() - start_time
        answer = next(
            block.text  # type: ignore[union-attr]
            for block in response.content
            if block.type == "text"
        )

        return {
            "answer": answer,
            "latency_seconds": round(latency, 3),
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "model": self.model,
            "method": "CAG",
            "context_used": "Full knowledge base (no retrieval)",
            "retrieved_chunks": None,
        }

    def interactive(self):
        """Launch an interactive Q&A session in the terminal."""
        print("\n" + "=" * 60)
        print("  CAG Interactive Session")
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
