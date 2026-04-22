"""
Benchmark Evaluator
===================
Runs a predefined set of questions through both CAG and RAG engines,
measures latency, token usage, estimated cost, and uses an LLM-as-judge
approach to score answer quality.

Produces a side-by-side comparison report and saves results to JSON/CSV.
"""

import json
import time
import csv
import anthropic
from pathlib import Path
from datetime import datetime
from typing import Optional

# Anthropic pricing (per million tokens) — update as needed
PRICING = {
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},  # $ per 1M tokens
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
}

# ---------------------------------------------------------------------------
# Default benchmark questions
# ---------------------------------------------------------------------------

DEFAULT_QUESTIONS = [
    # Factual / Direct retrieval
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
    # Multi-hop: requires combining information from multiple topics
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
    # Reasoning / synthesis
    {
        "id": "Q07",
        "question": "Compare the encoder-only, decoder-only, and encoder-decoder Transformer architectures for a RAG system's generator component.",
        "category": "reasoning",
        "expected_concepts": [
            "encoder",
            "decoder",
            "autoregressive",
            "BART",
            "generation",
        ],
    },
    {
        "id": "Q08",
        "question": "What chunking strategy would you recommend for a RAG system over a technical manual, and why does CAG eliminate this concern?",
        "category": "reasoning",
        "expected_concepts": ["chunking", "semantic", "overlap", "CAG", "full context"],
    },
    # Harder / obscure details
    {
        "id": "Q09",
        "question": "What is the mathematical formula for scaled dot-product attention, and what is the purpose of the scaling factor?",
        "category": "technical",
        "expected_concepts": [
            "Q",
            "K",
            "V",
            "softmax",
            "sqrt(d_k)",
            "numerical stability",
        ],
    },
    {
        "id": "Q10",
        "question": "How does Mixture of Experts achieve better performance per compute unit compared to dense models?",
        "category": "technical",
        "expected_concepts": [
            "experts",
            "router",
            "sparse",
            "active parameters",
            "compute",
        ],
    },
]


# ---------------------------------------------------------------------------
# LLM-as-Judge scorer
# ---------------------------------------------------------------------------

JUDGE_SYSTEM_PROMPT = """You are an expert AI/ML evaluator. Your job is to score an LLM's answer on a question about AI/ML topics.

Score the answer on these 4 dimensions (each 1-5):

1. CORRECTNESS (1-5): Is the answer factually accurate based on the expected concepts?
2. COMPLETENESS (1-5): Does the answer cover the key concepts expected?
3. COHERENCE (1-5): Is the answer well-structured, clear, and easy to understand?
4. GROUNDEDNESS (1-5): Is the answer grounded in specific facts rather than vague generalities?

Expected concepts that a good answer should mention: {expected_concepts}

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{"correctness": <1-5>, "completeness": <1-5>, "coherence": <1-5>, "groundedness": <1-5>, "reasoning": "<one sentence>"}}"""


class LLMJudge:
    """Uses Claude to score answers on a 1-5 scale across 4 dimensions."""

    def __init__(self, judge_model: str = "claude-3-5-haiku-20241022"):
        self.client = anthropic.Anthropic()
        self.judge_model = judge_model

    def score(self, question: str, answer: str, expected_concepts: list[str]) -> dict:
        """Score a single answer. Returns dict with scores and total."""
        system = JUDGE_SYSTEM_PROMPT.format(
            expected_concepts=", ".join(expected_concepts)
        )
        user = f"QUESTION: {question}\n\nANSWER TO EVALUATE:\n{answer}"

        try:
            response = self.client.messages.create(
                model=self.judge_model,
                max_tokens=256,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            raw = next(
                block.text  # type: ignore[union-attr]
                for block in response.content
                if block.type == "text"
            )
            scores = json.loads(raw)
            scores["total"] = round(
                (
                    scores["correctness"]
                    + scores["completeness"]
                    + scores["coherence"]
                    + scores["groundedness"]
                )
                / 4,
                2,
            )
            return scores
        except Exception as e:
            return {
                "correctness": 0,
                "completeness": 0,
                "coherence": 0,
                "groundedness": 0,
                "total": 0,
                "reasoning": f"Judge error: {e}",
            }


# ---------------------------------------------------------------------------
# Main Benchmarker
# ---------------------------------------------------------------------------


def compute_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """Estimate cost in USD for a single API call."""
    pricing = PRICING.get(model, {"input": 1.0, "output": 5.0})
    return round(
        (input_tokens / 1_000_000) * pricing["input"]
        + (output_tokens / 1_000_000) * pricing["output"],
        6,
    )


class Benchmarker:
    """
    Runs CAG and RAG engines on the same question set and produces a
    detailed comparison report.

    Parameters
    ----------
    cag_engine : CAGEngine
        Initialized CAG engine.
    rag_engine : RAGEngine
        Initialized RAG engine.
    questions : list[dict] | None
        Custom questions. Uses DEFAULT_QUESTIONS if None.
    use_judge : bool
        Whether to use LLM-as-judge scoring (costs extra API calls).
    results_dir : str | Path
        Directory to save results.
    """

    def __init__(
        self,
        cag_engine,
        rag_engine,
        questions: Optional[list[dict]] = None,
        use_judge: bool = True,
        results_dir: str | Path = "results",
    ):
        self.cag = cag_engine
        self.rag = rag_engine
        self.questions = questions or DEFAULT_QUESTIONS
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.judge = LLMJudge() if use_judge else None

    def run(self, verbose: bool = True) -> dict:
        """
        Run the full benchmark.

        Returns
        -------
        dict with full results and summary statistics.
        """
        results = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print("\n" + "=" * 70)
        print(f"  BENCHMARK: CAG vs RAG — {len(self.questions)} questions")
        print(f"  Judge scoring: {'enabled' if self.judge else 'disabled'}")
        print("=" * 70 + "\n")

        for i, q in enumerate(self.questions, 1):
            qid = q.get("id", f"Q{i:02d}")
            question = q["question"]
            category = q.get("category", "general")
            expected = q.get("expected_concepts", [])

            if verbose:
                print(f"[{i}/{len(self.questions)}] {qid} ({category})")
                print(f"  Q: {question[:80]}{'...' if len(question) > 80 else ''}")

            # --- CAG ---
            cag_result = self.cag.query(question)
            cag_cost = compute_cost(
                cag_result["input_tokens"],
                cag_result["output_tokens"],
                cag_result["model"],
            )

            # --- RAG ---
            rag_result = self.rag.query(question)
            rag_cost = compute_cost(
                rag_result["input_tokens"],
                rag_result["output_tokens"],
                rag_result["model"],
            )

            # --- Judge scoring ---
            cag_scores = {}
            rag_scores = {}
            if self.judge:
                cag_scores = self.judge.score(question, cag_result["answer"], expected)
                rag_scores = self.judge.score(question, rag_result["answer"], expected)

            # Compile result
            entry = {
                "id": qid,
                "question": question,
                "category": category,
                "expected_concepts": expected,
                "cag": {
                    **cag_result,
                    "cost_usd": cag_cost,
                    "judge_scores": cag_scores,
                },
                "rag": {
                    **rag_result,
                    "cost_usd": rag_cost,
                    "judge_scores": rag_scores,
                },
            }
            results.append(entry)

            if verbose:
                self._print_result_row(entry)

        summary = self._compute_summary(results)
        output = {"timestamp": timestamp, "summary": summary, "results": results}

        # Save files
        json_path = self.results_dir / f"benchmark_{timestamp}.json"
        csv_path = self.results_dir / f"benchmark_{timestamp}.csv"
        self._save_json(output, json_path)
        self._save_csv(results, csv_path)

        print("\n" + "=" * 70)
        self._print_summary(summary)
        print(f"\n  Results saved to:")
        print(f"    {json_path}")
        print(f"    {csv_path}")
        print("=" * 70 + "\n")

        return output

    # ------------------------------------------------------------------
    # Reporting helpers
    # ------------------------------------------------------------------

    def _print_result_row(self, entry: dict):
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
            f"tokens_in={cag['input_tokens']:,} | cost=${cag['cost_usd']:.5f} | "
            f"score={cag_score}/5"
        )
        print(
            f"  RAG: latency={rag['latency_seconds']}s | "
            f"tokens_in={rag['input_tokens']:,} | cost=${rag['cost_usd']:.5f} | "
            f"score={rag_score}/5{winner}"
        )
        print()

    def _compute_summary(self, results: list[dict]) -> dict:
        def avg(lst):
            return round(sum(lst) / len(lst), 3) if lst else 0

        cag_latencies = [r["cag"]["latency_seconds"] for r in results]
        rag_latencies = [r["rag"]["latency_seconds"] for r in results]
        cag_tokens_in = [r["cag"]["input_tokens"] for r in results]
        rag_tokens_in = [r["rag"]["input_tokens"] for r in results]
        cag_costs = [r["cag"]["cost_usd"] for r in results]
        rag_costs = [r["rag"]["cost_usd"] for r in results]
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
                "avg_latency_seconds": avg(cag_latencies),
                "avg_input_tokens": avg(cag_tokens_in),
                "total_cost_usd": round(sum(cag_costs), 5),
                "avg_judge_score": avg(cag_scores),
                "wins": cag_wins,
            },
            "rag": {
                "avg_latency_seconds": avg(rag_latencies),
                "avg_input_tokens": avg(rag_tokens_in),
                "total_cost_usd": round(sum(rag_costs), 5),
                "avg_judge_score": avg(rag_scores),
                "wins": rag_wins,
            },
            "ties": len(results) - cag_wins - rag_wins,
        }

    def _print_summary(self, s: dict):
        c = s["cag"]
        r = s["rag"]
        print("  SUMMARY")
        print(f"  {'Metric':<30} {'CAG':>12} {'RAG':>12}")
        print(f"  {'-' * 54}")
        print(
            f"  {'Avg Latency (s)':<30} {c['avg_latency_seconds']:>12} {r['avg_latency_seconds']:>12}"
        )
        print(
            f"  {'Avg Input Tokens':<30} {c['avg_input_tokens']:>12,.0f} {r['avg_input_tokens']:>12,.0f}"
        )
        print(
            f"  {'Total Cost (USD)':<30} ${c['total_cost_usd']:>11.5f} ${r['total_cost_usd']:>11.5f}"
        )
        print(
            f"  {'Avg Judge Score (/5)':<30} {c['avg_judge_score']:>12} {r['avg_judge_score']:>12}"
        )
        print(f"  {'Wins':<30} {c['wins']:>12} {r['wins']:>12}")
        print(f"  {'Ties':<30} {s['ties']:>12}")

    def _save_json(self, data: dict, path: Path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _save_csv(self, results: list[dict], path: Path):
        rows = []
        for r in results:
            rows.append(
                {
                    "id": r["id"],
                    "category": r["category"],
                    "question": r["question"],
                    "cag_latency": r["cag"]["latency_seconds"],
                    "cag_input_tokens": r["cag"]["input_tokens"],
                    "cag_output_tokens": r["cag"]["output_tokens"],
                    "cag_cost_usd": r["cag"]["cost_usd"],
                    "cag_score": r["cag"]["judge_scores"].get("total", ""),
                    "cag_correctness": r["cag"]["judge_scores"].get("correctness", ""),
                    "cag_completeness": r["cag"]["judge_scores"].get(
                        "completeness", ""
                    ),
                    "cag_coherence": r["cag"]["judge_scores"].get("coherence", ""),
                    "cag_groundedness": r["cag"]["judge_scores"].get(
                        "groundedness", ""
                    ),
                    "rag_latency": r["rag"]["latency_seconds"],
                    "rag_retrieval_latency": r["rag"].get(
                        "retrieval_latency_seconds", ""
                    ),
                    "rag_input_tokens": r["rag"]["input_tokens"],
                    "rag_output_tokens": r["rag"]["output_tokens"],
                    "rag_cost_usd": r["rag"]["cost_usd"],
                    "rag_score": r["rag"]["judge_scores"].get("total", ""),
                    "rag_correctness": r["rag"]["judge_scores"].get("correctness", ""),
                    "rag_completeness": r["rag"]["judge_scores"].get(
                        "completeness", ""
                    ),
                    "rag_coherence": r["rag"]["judge_scores"].get("coherence", ""),
                    "rag_groundedness": r["rag"]["judge_scores"].get(
                        "groundedness", ""
                    ),
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
            )

        if rows:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
