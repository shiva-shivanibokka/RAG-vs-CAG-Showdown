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
    python main.py benchmark --no-judge   Skip LLM judge scoring (faster)
    python main.py benchmark --top-k 5    Set RAG top-k chunks (default: 3)

Environment variables (see .env):
    CF_ACCOUNT_ID   Cloudflare account ID
    CF_API_TOKEN    Cloudflare Workers AI API token
    CF_MODEL        Model tag (default: @cf/meta/llama-3.1-8b-instruct)
    RAG_TOP_K       Top-k chunks for RAG (default: 3)
    LOG_LEVEL       Logging verbosity (default: INFO)
"""

import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.benchmark.evaluator import Benchmarker  # noqa: E402
from src.cag.engine import CAGEngine  # noqa: E402
from src.config import CF_ACCOUNT_ID, CF_API_TOKEN, CF_MODEL, RAG_TOP_K, setup_logging  # noqa: E402
from src.rag.engine import RAGEngine  # noqa: E402

KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge_base" / "aiml_corpus.txt"
RESULTS_DIR = PROJECT_ROOT / "results"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def check_cloudflare() -> None:
    if not CF_ACCOUNT_ID or not CF_API_TOKEN:
        print("[ERROR] CF_ACCOUNT_ID and CF_API_TOKEN must be set in your .env file.")
        print("  1. Sign up for free at https://cloudflare.com")
        print("  2. Copy your Account ID from the dashboard right sidebar")
        print("  3. Create an API token: My Profile → API Tokens → Create Token")
        print("     Use the 'Workers AI' template or grant 'Workers AI:Read' permission")
        print("  4. Add both to your .env file")
        sys.exit(1)


def print_banner() -> None:
    print("""
╔═══════════════════════════════════════════════════════════════╗
║           CAG vs RAG Showdown Framework                      ║
║           Context Augmented Generation vs                    ║
║           Retrieval Augmented Generation                     ║
╚═══════════════════════════════════════════════════════════════╝
""")


def format_answer_block(method: str, result: dict) -> str:
    lines = [
        f"\n{'─' * 60}",
        f"  {method} ANSWER",
        f"{'─' * 60}",
        result["answer"],
        "\n  Stats:",
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


def cmd_benchmark(args) -> None:
    print_banner()
    check_cloudflare()

    model = args.model or CF_MODEL
    top_k = args.top_k or RAG_TOP_K
    use_judge = not args.no_judge

    print(f"  Model       : {model}")
    print(f"  RAG top-k   : {top_k}")
    print(f"  LLM Judge   : {'enabled' if use_judge else 'disabled'}")
    print("  Mode        : async parallel\n")

    cag = CAGEngine(KNOWLEDGE_BASE, model=model)
    rag = RAGEngine(KNOWLEDGE_BASE, model=model, top_k=top_k)
    bench = Benchmarker(
        cag_engine=cag, rag_engine=rag, use_judge=use_judge, results_dir=RESULTS_DIR
    )
    asyncio.run(bench.run_async(verbose=True))


def cmd_chat(args) -> None:
    print_banner()
    check_cloudflare()

    model = args.model or CF_MODEL
    if args.method == "cag":
        CAGEngine(KNOWLEDGE_BASE, model=model).interactive()
    else:
        RAGEngine(KNOWLEDGE_BASE, model=model, top_k=args.top_k or RAG_TOP_K).interactive()


def cmd_ask(args) -> None:
    print_banner()
    check_cloudflare()

    question = args.question
    model = args.model or CF_MODEL
    top_k = args.top_k or RAG_TOP_K
    print(f"  Question: {question}\n")

    if args.method in ("cag", "both"):
        result = CAGEngine(KNOWLEDGE_BASE, model=model).query(question)
        print(format_answer_block("CAG", result))

    if args.method in ("rag", "both"):
        result = RAGEngine(KNOWLEDGE_BASE, model=model, top_k=top_k).query(question)
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

    bench_parser = subparsers.add_parser("benchmark", help="Run full benchmark suite")
    bench_parser.add_argument("--model", type=str, default=None)
    bench_parser.add_argument("--top-k", type=int, default=None)
    bench_parser.add_argument("--no-judge", action="store_true")
    bench_parser.set_defaults(func=cmd_benchmark)

    chat_parser = subparsers.add_parser("chat", help="Interactive chat session")
    chat_parser.add_argument("method", choices=["cag", "rag"])
    chat_parser.add_argument("--model", type=str, default=None)
    chat_parser.add_argument("--top-k", type=int, default=None)
    chat_parser.set_defaults(func=cmd_chat)

    ask_parser = subparsers.add_parser("ask", help="Single question")
    ask_parser.add_argument("method", choices=["cag", "rag", "both"])
    ask_parser.add_argument("question", type=str)
    ask_parser.add_argument("--model", type=str, default=None)
    ask_parser.add_argument("--top-k", type=int, default=None)
    ask_parser.set_defaults(func=cmd_ask)

    return parser


def main() -> None:
    setup_logging()
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
