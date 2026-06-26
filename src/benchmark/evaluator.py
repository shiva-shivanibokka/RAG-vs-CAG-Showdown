"""
Benchmark Evaluator
===================
Runs questions through CAG and RAG, measures latency and token counts,
scores answers with an LLM-as-judge (Cloudflare Workers AI), saves JSON + CSV.
"""

import asyncio
import csv
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path

from openai import AsyncOpenAI, OpenAI

from src.config import TOGETHER_API_KEY, TOGETHER_BASE_URL, TOGETHER_MODEL, MAX_RETRIES

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default benchmark questions
# ---------------------------------------------------------------------------

DEFAULT_QUESTIONS = [
    {
        "id": "Q01",
        "question": "What is the KV cache and how does it benefit CAG specifically?",
        "category": "factual",
        "expected_concepts": ["key-value cache", "precomputation", "CAG", "latency"],
    },
    {
        "id": "Q02",
        "question": "What are the main weaknesses of RAG compared to CAG?",
        "category": "comparison",
        "expected_concepts": ["retrieval errors", "chunking", "multi-hop", "latency"],
    },
    {
        "id": "Q03",
        "question": "Explain the difference between Multi-Head Attention, Multi-Query Attention, and Grouped Query Attention.",
        "category": "technical",
        "expected_concepts": ["MHA", "MQA", "GQA", "heads", "keys", "values"],
    },
    {
        "id": "Q04",
        "question": "What is RLHF and what are its main alternatives?",
        "category": "factual",
        "expected_concepts": ["RLHF", "reward model", "PPO", "DPO", "RLAIF"],
    },
    {
        "id": "Q05",
        "question": "How does tokenization affect the practical context window available for CAG, and which tokenization algorithm does LLaMA use?",
        "category": "multi_hop",
        "expected_concepts": ["BPE", "tokens", "context window", "LLaMA", "characters"],
    },
    {
        "id": "Q06",
        "question": "If I want to minimize hallucinations in a medical QA system and my knowledge base is 50,000 words, should I use CAG or RAG? Justify using specifics from both approaches.",
        "category": "multi_hop",
        "expected_concepts": [
            "hallucination",
            "context window",
            "faithfulness",
            "retrieval errors",
            "CAG",
            "RAG",
        ],
    },
    {
        "id": "Q07",
        "question": "Compare the encoder-only, decoder-only, and encoder-decoder Transformer architectures for a RAG system's generator component.",
        "category": "reasoning",
        "expected_concepts": ["encoder", "decoder", "autoregressive", "BART", "generation"],
    },
    {
        "id": "Q08",
        "question": "What chunking strategy would you recommend for a RAG system over a technical manual, and why does CAG eliminate this concern?",
        "category": "reasoning",
        "expected_concepts": ["chunking", "semantic", "overlap", "CAG", "full context"],
    },
    {
        "id": "Q09",
        "question": "What is the mathematical formula for scaled dot-product attention, and what is the purpose of the scaling factor?",
        "category": "technical",
        "expected_concepts": ["Q", "K", "V", "softmax", "sqrt(d_k)", "numerical stability"],
    },
    {
        "id": "Q10",
        "question": "How does Mixture of Experts achieve better performance per compute unit compared to dense models?",
        "category": "technical",
        "expected_concepts": ["experts", "router", "sparse", "active parameters", "compute"],
    },
]

# ---------------------------------------------------------------------------
# LLM-as-Judge
# ---------------------------------------------------------------------------

_JUDGE_SYSTEM = (
    "You are an expert AI/ML evaluator. Score the answer on these 4 dimensions (each 1-5):\n\n"
    "1. CORRECTNESS (1-5): Factual accuracy.\n"
    "2. COMPLETENESS (1-5): Covers expected concepts.\n"
    "3. COHERENCE (1-5): Clear and well-structured.\n"
    "4. GROUNDEDNESS (1-5): Grounded in specifics, not vague generalities.\n\n"
    "Expected concepts: {expected_concepts}\n\n"
    "Respond ONLY with valid JSON — no markdown, no extra text:\n"
    '{{"correctness": <1-5>, "completeness": <1-5>, "coherence": <1-5>, '
    '"groundedness": <1-5>, "reasoning": "<one sentence>"}}'
)

_REQUIRED_FIELDS = {"correctness", "completeness", "coherence", "groundedness"}


class LLMJudge:
    """Scores answers using Cloudflare Workers AI as an LLM judge."""

    def __init__(
        self,
        judge_model: str = TOGETHER_MODEL,
        max_retries: int = MAX_RETRIES,
        _client=None,
    ):
        self.judge_model = judge_model
        self._max_retries = max_retries
        self._client: OpenAI = _client or OpenAI(
            api_key=TOGETHER_API_KEY,
            base_url=TOGETHER_BASE_URL,
        )

    def _parse_judge_response(self, raw: str) -> dict:
        """Strip markdown fences, parse JSON, validate required fields, add total."""
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
        data = json.loads(cleaned)
        missing = _REQUIRED_FIELDS - data.keys()
        if missing:
            raise ValueError(f"Missing fields in judge response: {missing}")
        data["total"] = round(
            sum(data[k] for k in _REQUIRED_FIELDS) / len(_REQUIRED_FIELDS), 2
        )
        return data

    def score(self, question: str, answer: str, expected_concepts: list[str]) -> dict:
        system = _JUDGE_SYSTEM.format(expected_concepts=", ".join(expected_concepts))
        user = f"QUESTION: {question}\n\nANSWER TO EVALUATE:\n{answer}"
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self.judge_model,
                    messages=messages,
                    max_tokens=256,
                )
                return self._parse_judge_response(response.choices[0].message.content)
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "Judge attempt %d/%d failed: %s", attempt + 1, self._max_retries, exc
                )
                time.sleep(2**attempt)

        return {
            "correctness": 0,
            "completeness": 0,
            "coherence": 0,
            "groundedness": 0,
            "total": 0,
            "reasoning": f"Judge error: {last_exc}",
        }

    async def score_async(
        self, question: str, answer: str, expected_concepts: list[str]
    ) -> dict:
        system = _JUDGE_SYSTEM.format(expected_concepts=", ".join(expected_concepts))
        user = f"QUESTION: {question}\n\nANSWER TO EVALUATE:\n{answer}"
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                async_client = AsyncOpenAI(api_key=TOGETHER_API_KEY, base_url=TOGETHER_BASE_URL)
                response = await async_client.chat.completions.create(
                    model=self.judge_model,
                    messages=messages,
                    max_tokens=256,
                )
                return self._parse_judge_response(response.choices[0].message.content)
            except Exception as exc:
                last_exc = exc
                wait = 2**attempt
                logger.warning(
                    "Async judge attempt %d/%d failed: %s. Retrying in %ds.",
                    attempt + 1,
                    self._max_retries,
                    exc,
                    wait,
                )
                await asyncio.sleep(wait)

        return {
            "correctness": 0,
            "completeness": 0,
            "coherence": 0,
            "groundedness": 0,
            "total": 0,
            "reasoning": f"Judge error after {self._max_retries} attempts: {last_exc}",
        }


# ---------------------------------------------------------------------------
# Benchmarker
# ---------------------------------------------------------------------------


class Benchmarker:
    """
    Runs CAG and RAG engines on the same question set and produces a
    detailed side-by-side comparison report saved to JSON + CSV.
    """

    def __init__(
        self,
        cag_engine,
        rag_engine,
        questions: list[dict] | None = None,
        use_judge: bool = True,
        results_dir: str | Path = "results",
    ):
        self.cag = cag_engine
        self.rag = rag_engine
        self.questions = questions or DEFAULT_QUESTIONS
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.judge: LLMJudge | None = LLMJudge() if use_judge else None

    # ------------------------------------------------------------------
    # Sync run
    # ------------------------------------------------------------------

    def run(self, verbose: bool = True) -> dict:
        results = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._print_header(timestamp)

        for i, q in enumerate(self.questions, 1):
            if verbose:
                print(
                    f"[{i}/{len(self.questions)}] {q.get('id', f'Q{i:02d}')} "
                    f"({q.get('category', 'general')})"
                )
                print(
                    f"  Q: {q['question'][:80]}{'...' if len(q['question']) > 80 else ''}"
                )

            cag_result = self.cag.query(q["question"])
            rag_result = self.rag.query(q["question"])

            cag_scores, rag_scores = {}, {}
            if self.judge:
                cag_scores = self.judge.score(
                    q["question"], cag_result["answer"], q.get("expected_concepts", [])
                )
                rag_scores = self.judge.score(
                    q["question"], rag_result["answer"], q.get("expected_concepts", [])
                )

            entry = self._build_entry(q, cag_result, rag_result, cag_scores, rag_scores)
            results.append(entry)
            if verbose:
                self._print_result_row(entry)

        return self._finalize(results, timestamp)

    # ------------------------------------------------------------------
    # Async run (parallel per question)
    # ------------------------------------------------------------------

    async def run_async(self, verbose: bool = True) -> dict:
        results = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._print_header(timestamp, async_mode=True)

        for i, q in enumerate(self.questions, 1):
            if verbose:
                print(
                    f"[{i}/{len(self.questions)}] {q.get('id', f'Q{i:02d}')} "
                    f"({q.get('category', 'general')})"
                )

            cag_result, rag_result = await asyncio.gather(
                self.cag.query_async(q["question"]),
                self.rag.query_async(q["question"]),
            )

            cag_scores, rag_scores = {}, {}
            if self.judge:
                cag_scores, rag_scores = await asyncio.gather(
                    self.judge.score_async(
                        q["question"],
                        cag_result["answer"],
                        q.get("expected_concepts", []),
                    ),
                    self.judge.score_async(
                        q["question"],
                        rag_result["answer"],
                        q.get("expected_concepts", []),
                    ),
                )

            entry = self._build_entry(q, cag_result, rag_result, cag_scores, rag_scores)
            results.append(entry)
            if verbose:
                self._print_result_row(entry)

        return self._finalize(results, timestamp)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_entry(self, q, cag_result, rag_result, cag_scores, rag_scores) -> dict:
        return {
            "id": q.get("id", ""),
            "question": q["question"],
            "category": q.get("category", "general"),
            "expected_concepts": q.get("expected_concepts", []),
            "cag": {**cag_result, "judge_scores": cag_scores},
            "rag": {**rag_result, "judge_scores": rag_scores},
        }

    def _finalize(self, results: list[dict], timestamp: str) -> dict:
        summary = self._compute_summary(results)
        output = {"timestamp": timestamp, "summary": summary, "results": results}
        json_path = self.results_dir / f"benchmark_{timestamp}.json"
        csv_path = self.results_dir / f"benchmark_{timestamp}.csv"
        self._save_json(output, json_path)
        self._save_csv(results, csv_path)
        print(f"\n{'=' * 70}")
        self._print_summary(summary)
        print(f"\n  Results saved to:\n    {json_path}\n    {csv_path}")
        print(f"{'=' * 70}\n")
        return output

    def _print_header(self, timestamp: str, async_mode: bool = False) -> None:
        mode = " (async parallel)" if async_mode else ""
        print(f"\n{'=' * 70}")
        print(f"  BENCHMARK: CAG vs RAG{mode} — {len(self.questions)} questions")
        print(f"  Judge scoring: {'enabled' if self.judge else 'disabled'}")
        print(f"{'=' * 70}\n")

    def _print_result_row(self, entry: dict) -> None:
        cag = entry["cag"]
        rag = entry["rag"]
        cag_score = cag["judge_scores"].get("total", "N/A")
        rag_score = rag["judge_scores"].get("total", "N/A")
        winner = ""
        if isinstance(cag_score, (int, float)) and isinstance(rag_score, (int, float)):
            if cag_score > rag_score:
                winner = " <- CAG wins"
            elif rag_score > cag_score:
                winner = " <- RAG wins"
            else:
                winner = " <- TIE"

        print(
            f"  CAG: latency={cag['latency_seconds']}s | "
            f"tokens_in={cag['input_tokens']:,} | score={cag_score}/5"
        )
        print(
            f"  RAG: latency={rag['latency_seconds']}s | "
            f"tokens_in={rag['input_tokens']:,} | score={rag_score}/5{winner}\n"
        )

    def _compute_summary(self, results: list[dict]) -> dict:
        def avg(lst: list) -> float:
            return round(sum(lst) / len(lst), 3) if lst else 0.0

        cag_scores = [
            r["cag"]["judge_scores"].get("total", 0)
            for r in results
            if r["cag"]["judge_scores"]
        ]
        rag_scores = [
            r["rag"]["judge_scores"].get("total", 0)
            for r in results
            if r["rag"]["judge_scores"]
        ]
        cag_wins = sum(
            1
            for r in results
            if r["cag"]["judge_scores"].get("total", 0)
            > r["rag"]["judge_scores"].get("total", 0)
        )
        rag_wins = sum(
            1
            for r in results
            if r["rag"]["judge_scores"].get("total", 0)
            > r["cag"]["judge_scores"].get("total", 0)
        )

        return {
            "num_questions": len(results),
            "cag": {
                "avg_latency_seconds": avg([r["cag"]["latency_seconds"] for r in results]),
                "avg_input_tokens": avg([r["cag"]["input_tokens"] for r in results]),
                "avg_judge_score": avg(cag_scores),
                "wins": cag_wins,
            },
            "rag": {
                "avg_latency_seconds": avg([r["rag"]["latency_seconds"] for r in results]),
                "avg_input_tokens": avg([r["rag"]["input_tokens"] for r in results]),
                "avg_judge_score": avg(rag_scores),
                "wins": rag_wins,
            },
            "ties": len(results) - cag_wins - rag_wins,
        }

    def _print_summary(self, s: dict) -> None:
        c, r = s["cag"], s["rag"]
        print("  SUMMARY")
        print(f"  {'Metric':<30} {'CAG':>12} {'RAG':>12}")
        print(f"  {'-' * 54}")
        print(
            f"  {'Avg Latency (s)':<30} {c['avg_latency_seconds']:>12} "
            f"{r['avg_latency_seconds']:>12}"
        )
        print(
            f"  {'Avg Input Tokens':<30} {c['avg_input_tokens']:>12,.0f} "
            f"{r['avg_input_tokens']:>12,.0f}"
        )
        print(
            f"  {'Avg Judge Score (/5)':<30} {c['avg_judge_score']:>12} "
            f"{r['avg_judge_score']:>12}"
        )
        print(f"  {'Wins':<30} {c['wins']:>12} {r['wins']:>12}")
        print(f"  {'Ties':<30} {s['ties']:>12}")

    def _save_json(self, data: dict, path: Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _save_csv(self, results: list[dict], path: Path) -> None:
        rows = [
            {
                "id": r["id"],
                "category": r["category"],
                "question": r["question"],
                "cag_latency": r["cag"]["latency_seconds"],
                "cag_input_tokens": r["cag"]["input_tokens"],
                "cag_output_tokens": r["cag"]["output_tokens"],
                "cag_score": r["cag"]["judge_scores"].get("total", ""),
                "cag_correctness": r["cag"]["judge_scores"].get("correctness", ""),
                "cag_completeness": r["cag"]["judge_scores"].get("completeness", ""),
                "cag_coherence": r["cag"]["judge_scores"].get("coherence", ""),
                "cag_groundedness": r["cag"]["judge_scores"].get("groundedness", ""),
                "rag_latency": r["rag"]["latency_seconds"],
                "rag_retrieval_latency": r["rag"].get("retrieval_latency_seconds", ""),
                "rag_input_tokens": r["rag"]["input_tokens"],
                "rag_output_tokens": r["rag"]["output_tokens"],
                "rag_score": r["rag"]["judge_scores"].get("total", ""),
                "rag_correctness": r["rag"]["judge_scores"].get("correctness", ""),
                "rag_completeness": r["rag"]["judge_scores"].get("completeness", ""),
                "rag_coherence": r["rag"]["judge_scores"].get("coherence", ""),
                "rag_groundedness": r["rag"]["judge_scores"].get("groundedness", ""),
                "retrieved_chunks": str(
                    [c["title"] for c in r["rag"].get("retrieved_chunks") or []]
                ),
                "winner": (
                    "CAG"
                    if r["cag"]["judge_scores"].get("total", 0)
                    > r["rag"]["judge_scores"].get("total", 0)
                    else "RAG"
                    if r["rag"]["judge_scores"].get("total", 0)
                    > r["cag"]["judge_scores"].get("total", 0)
                    else "TIE"
                ),
            }
            for r in results
        ]
        if rows:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
