"""
CAG vs RAG Showdown — Main CLI
================================
Usage:
    python main.py benchmark          Run full benchmark (CAG vs RAG, 10 questions)
    python main.py chat cag           Interactive chat using CAG
    python main.py chat rag           Interactive chat using RAG
    python main.py ask cag "..."      Single question via CAG
    python main.py ask rag "..."      Single question via RAG
    python main.py ask both "..."     Ask both and compare side by side
    python main.py benchmark --no-judge   Skip LLM judge scoring (faster/cheaper)
    python main.py benchmark --top-k 5    Set RAG top-k chunks (default: 3)

Environment variables:
    ANTHROPIC_API_KEY   Required — your Anthropic API key
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.cag.engine import CAGEngine
from src.rag.engine import RAGEngine
from src.benchmark.evaluator import Benchmarker

KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge_base" / "aiml_corpus.txt"
RESULTS_DIR = PROJECT_ROOT / "results"
DEFAULT_MODEL = "claude-3-5-haiku-20241022"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def check_api_key():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[ERROR] ANTHROPIC_API_KEY environment variable is not set.")
        print("  Set it with: set ANTHROPIC_API_KEY=your_key_here  (Windows)")
        print("           or: export ANTHROPIC_API_KEY=your_key_here  (Unix)")
        sys.exit(1)


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║           CAG vs RAG Showdown Framework                      ║
║           Context Augmented Generation vs                    ║
║           Retrieval Augmented Generation                     ║
╚══════════════════════════════════════════════════════════════╝
""")


def format_answer_block(method: str, result: dict) -> str:
    """Pretty-print a single engine result."""
    lines = [
        f"\n{'─' * 60}",
        f"  {method} ANSWER",
        f"{'─' * 60}",
        result["answer"],
        f"\n  Stats:",
        f"  • Latency       : {result['latency_seconds']}s",
        f"  • Input tokens  : {result['input_tokens']:,}",
        f"  • Output tokens : {result['output_tokens']:,}",
        f"  • Context used  : {result['context_used']}",
    ]
    if result.get("retrieved_chunks"):
        chunks = [c["title"] for c in result["retrieved_chunks"]]
        lines.append(f"  • Retrieved     : {chunks}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_benchmark(args):
    print_banner()
    check_api_key()

    model = args.model or DEFAULT_MODEL
    top_k = args.top_k or 3
    use_judge = not args.no_judge

    print(f"  Model       : {model}")
    print(f"  RAG top-k   : {top_k}")
    print(f"  LLM Judge   : {'enabled' if use_judge else 'disabled'}")
    print()

    cag = CAGEngine(KNOWLEDGE_BASE, model=model)
    rag = RAGEngine(KNOWLEDGE_BASE, model=model, top_k=top_k)

    bench = Benchmarker(
        cag_engine=cag,
        rag_engine=rag,
        use_judge=use_judge,
        results_dir=RESULTS_DIR,
    )
    bench.run(verbose=True)


def cmd_chat(args):
    print_banner()
    check_api_key()

    method = args.method.lower()
    model = args.model or DEFAULT_MODEL

    if method == "cag":
        engine = CAGEngine(KNOWLEDGE_BASE, model=model)
        engine.interactive()
    elif method == "rag":
        engine = RAGEngine(KNOWLEDGE_BASE, model=model, top_k=args.top_k or 3)
        engine.interactive()
    else:
        print(f"Unknown method '{method}'. Use 'cag' or 'rag'.")
        sys.exit(1)


def cmd_ask(args):
    print_banner()
    check_api_key()

    question = args.question
    method = args.method.lower()
    model = args.model or DEFAULT_MODEL
    top_k = args.top_k or 3

    print(f"  Question: {question}\n")

    if method in ("cag", "both"):
        engine = CAGEngine(KNOWLEDGE_BASE, model=model)
        result = engine.query(question)
        print(format_answer_block("CAG", result))

    if method in ("rag", "both"):
        engine = RAGEngine(KNOWLEDGE_BASE, model=model, top_k=top_k)
        result = engine.query(question)
        print(format_answer_block("RAG", result))

    print()


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="CAG vs RAG Showdown — benchmark and compare both approaches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- benchmark ---
    bench_parser = subparsers.add_parser("benchmark", help="Run full benchmark suite")
    bench_parser.add_argument(
        "--model", type=str, default=None, help="Anthropic model ID"
    )
    bench_parser.add_argument(
        "--top-k", type=int, default=3, help="RAG top-k chunks (default: 3)"
    )
    bench_parser.add_argument(
        "--no-judge", action="store_true", help="Skip LLM judge scoring"
    )
    bench_parser.set_defaults(func=cmd_benchmark)

    # --- chat ---
    chat_parser = subparsers.add_parser("chat", help="Interactive chat session")
    chat_parser.add_argument("method", choices=["cag", "rag"], help="Engine to use")
    chat_parser.add_argument(
        "--model", type=str, default=None, help="Anthropic model ID"
    )
    chat_parser.add_argument(
        "--top-k", type=int, default=3, help="RAG top-k (default: 3)"
    )
    chat_parser.set_defaults(func=cmd_chat)

    # --- ask ---
    ask_parser = subparsers.add_parser(
        "ask", help="Single question, one or both engines"
    )
    ask_parser.add_argument(
        "method", choices=["cag", "rag", "both"], help="Engine to use"
    )
    ask_parser.add_argument("question", type=str, help="The question to ask")
    ask_parser.add_argument(
        "--model", type=str, default=None, help="Anthropic model ID"
    )
    ask_parser.add_argument(
        "--top-k", type=int, default=3, help="RAG top-k (default: 3)"
    )
    ask_parser.set_defaults(func=cmd_ask)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
