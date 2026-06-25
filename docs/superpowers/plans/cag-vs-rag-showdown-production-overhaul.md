# CAG vs RAG Showdown — Production Overhaul Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Overhaul the CAG vs RAG Showdown CLI tool into a production-grade system: migrate all LLM calls from Anthropic to Ollama (free, local), add proper error handling and structured logging, a pytest test suite, GitHub Actions CI, async parallel benchmarking, a FastAPI REST layer, Docker Compose deployment, and a Streamlit results dashboard.

**Architecture:** Three independently runnable surfaces — CLI (`main.py`), REST API (`api/app.py` via FastAPI + uvicorn), and results dashboard (`dashboard/app.py` via Streamlit) — all backed by the same `CAGEngine`/`RAGEngine` core. Docker Compose orchestrates three services: `ollama` (LLM server), `api` (FastAPI), and `dashboard` (Streamlit). All tests are fully mocked — no live Ollama required for CI.

**Tech Stack:** Python 3.11, Ollama (`llama3.1:8b` default), FAISS, `sentence-transformers/all-MiniLM-L6-v2`, FastAPI, Streamlit, pytest + pytest-asyncio, ruff, GitHub Actions, Docker + Docker Compose

## Global Constraints

- Python >= 3.11 (uses `X | Y` union syntax, `match` statements, etc.)
- Zero Anthropic API usage — all LLM generation goes through `ollama` Python package
- `sentence-transformers` embedding model stays unchanged (already open-source, no API needed)
- All source code passes `ruff check src tests main.py api dashboard` with zero errors
- All tests pass with `pytest tests/ -v` with no live Ollama service (everything mocked)
- Commit after every task; commit message format: `feat: <task description>`
- `.env` is never committed; `.env.example` is always kept up to date

---

## File Map

```
CAG-vs-RAG-Showdown/
├── .gitignore                         MODIFY
├── .env.example                       CREATE
├── .github/
│   └── workflows/
│       └── ci.yml                     CREATE
├── pyproject.toml                     CREATE  (replaces requirements.txt as source of truth)
├── requirements.txt                   KEEP    (keep for users who don't use pip install -e)
├── Dockerfile                         CREATE
├── .dockerignore                      CREATE
├── docker-compose.yml                 CREATE
├── main.py                            MODIFY  (remove API key check, add Ollama health check, add async benchmark)
├── knowledge_base/
│   └── aiml_corpus.txt                KEEP
├── src/
│   ├── __init__.py                    KEEP
│   ├── config.py                      CREATE  (central env-var config + logging setup)
│   ├── cag/
│   │   ├── __init__.py                KEEP
│   │   └── engine.py                  REWRITE (Anthropic → Ollama, retry logic, logging)
│   ├── rag/
│   │   ├── __init__.py                KEEP
│   │   └── engine.py                  REWRITE (Anthropic → Ollama, retry logic, logging)
│   └── benchmark/
│       ├── __init__.py                KEEP
│       └── evaluator.py              REWRITE  (Ollama judge, fix JSON parsing, async run)
├── api/
│   ├── __init__.py                    CREATE
│   └── app.py                         CREATE  (FastAPI: /health, /query/cag, /query/rag, /benchmark)
├── dashboard/
│   └── app.py                         CREATE  (Streamlit: load results, charts, per-Q detail)
├── tests/
│   ├── __init__.py                    CREATE
│   ├── conftest.py                    CREATE  (shared fixtures: tmp_knowledge_base, mock_ollama_client)
│   ├── test_chunking.py               CREATE
│   ├── test_cag_engine.py             CREATE
│   ├── test_rag_engine.py             CREATE
│   ├── test_evaluator.py             CREATE
│   └── test_api.py                    CREATE
└── results/
    └── .gitkeep                       CREATE
```

---

### Task 1: Infra Foundations

**Files:**
- Modify: `.gitignore`
- Create: `.env.example`
- Create: `pyproject.toml`
- Create: `src/config.py`
- Create: `results/.gitkeep`

**Interfaces:**
- Produces: `src.config.OLLAMA_HOST`, `src.config.OLLAMA_MODEL`, `src.config.EMBEDDING_MODEL`, `src.config.RAG_TOP_K`, `src.config.MAX_TOKENS`, `src.config.MAX_RETRIES`, `src.config.setup_logging(level: str) -> None` — all consumed by Tasks 2, 3, 4, 8

- [ ] **Step 1: Write `.gitignore`**

```gitignore
# Python
__pycache__/
*.py[cod]
*.pyd
.Python
*.egg-info/
dist/
build/
.eggs/
.venv/
venv/
env/
*.egg

# Environment
.env
.env.*
!.env.example

# Benchmark results (generated files; commit selectively if desired)
results/*.json
results/*.csv

# ML model caches
sentence_transformers_cache/
.cache/
*.bin
*.pt

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Test / coverage
.pytest_cache/
.coverage
htmlcov/
```

- [ ] **Step 2: Write `.env.example`**

```bash
# Copy to .env and fill in values
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
EMBEDDING_MODEL=all-MiniLM-L6-v2
RAG_TOP_K=3
MAX_TOKENS=1024
MAX_RETRIES=3
LOG_LEVEL=INFO
```

- [ ] **Step 3: Write `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "cag-vs-rag-showdown"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "faiss-cpu>=1.8.0",
    "sentence-transformers>=3.3.0",
    "numpy>=1.26.0",
    "ollama>=0.4.0",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.9.0",
    "streamlit>=1.40.0",
    "pandas>=2.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "ruff>=0.8.0",
    "httpx>=0.27.0",
]

[tool.hatch.build.targets.wheel]
packages = ["src", "api", "dashboard"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]
ignore = ["E501"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.coverage.run]
source = ["src", "api"]
omit = ["tests/*", "dashboard/*"]
```

- [ ] **Step 4: Write `src/config.py`**

```python
import logging
import os

OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "3"))
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1024"))
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
```

- [ ] **Step 5: Create `results/.gitkeep`**

Create an empty file at `results/.gitkeep` so the directory is tracked by git.

- [ ] **Step 6: Install deps and verify ruff**

```bash
pip install -e ".[dev]"
ruff check src main.py
```

Expected: `All checks passed!` (or only pre-existing issues — fix any that appear)

- [ ] **Step 7: Commit**

```bash
git add .gitignore .env.example pyproject.toml src/config.py results/.gitkeep
git commit -m "feat: add infra foundations — pyproject.toml, config, gitignore"
```

---

### Task 2: CAG Engine — Ollama Migration

**Files:**
- Rewrite: `src/cag/engine.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py` (partial — `tmp_knowledge_base` fixture only)
- Create: `tests/test_cag_engine.py`

**Interfaces:**
- Consumes: `src.config.OLLAMA_HOST`, `src.config.OLLAMA_MODEL`, `src.config.MAX_TOKENS`, `src.config.MAX_RETRIES`
- Produces:
  - `CAGEngine(knowledge_base_path, model, max_tokens, ollama_host, max_retries, _client=None)`
  - `CAGEngine.query(question: str) -> dict` — keys: `answer`, `latency_seconds`, `input_tokens`, `output_tokens`, `model`, `method`, `context_used`, `retrieved_chunks`
  - `CAGEngine.query_async(question: str) -> dict` — same keys (used in Task 7)
  - `CAGEngine.interactive() -> None`

- [ ] **Step 1: Write `tests/__init__.py`**

Empty file — just `touch tests/__init__.py`.

- [ ] **Step 2: Write `tests/conftest.py`**

```python
import pytest
from pathlib import Path
from unittest.mock import MagicMock

SAMPLE_CORPUS = """\
================================================================================
TOPIC: Machine Learning
================================================================================
Machine learning is a subset of artificial intelligence where systems learn
from data without being explicitly programmed. Key algorithms include linear
regression, decision trees, and support vector machines.

================================================================================
TOPIC: Neural Networks
================================================================================
Neural networks are computational models inspired by the human brain. They
consist of layers of interconnected nodes (neurons) that process information
using connectionist approaches to computation.

================================================================================
TOPIC: KV Cache
================================================================================
The key-value (KV) cache stores the attention keys and values computed for
the context in memory, so they do not need to be recomputed for each new
token. This is the core mechanism that makes CAG efficient.
"""


@pytest.fixture
def tmp_knowledge_base(tmp_path: Path) -> Path:
    kb = tmp_path / "corpus.txt"
    kb.write_text(SAMPLE_CORPUS, encoding="utf-8")
    return kb


@pytest.fixture
def mock_ollama_client():
    client = MagicMock()
    response = MagicMock()
    response.message.content = "This is a test answer."
    response.prompt_eval_count = 150
    response.eval_count = 40
    client.chat.return_value = response
    return client
```

- [ ] **Step 3: Write `tests/test_cag_engine.py`**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.cag.engine import CAGEngine


def test_query_returns_correct_keys(tmp_knowledge_base, mock_ollama_client):
    engine = CAGEngine(tmp_knowledge_base, _client=mock_ollama_client)
    result = engine.query("What is KV cache?")

    assert set(result.keys()) == {
        "answer", "latency_seconds", "input_tokens", "output_tokens",
        "model", "method", "context_used", "retrieved_chunks",
    }


def test_query_answer_text(tmp_knowledge_base, mock_ollama_client):
    engine = CAGEngine(tmp_knowledge_base, _client=mock_ollama_client)
    result = engine.query("What is KV cache?")
    assert result["answer"] == "This is a test answer."


def test_query_method_is_cag(tmp_knowledge_base, mock_ollama_client):
    engine = CAGEngine(tmp_knowledge_base, _client=mock_ollama_client)
    result = engine.query("test")
    assert result["method"] == "CAG"
    assert result["retrieved_chunks"] is None


def test_query_token_counts(tmp_knowledge_base, mock_ollama_client):
    engine = CAGEngine(tmp_knowledge_base, _client=mock_ollama_client)
    result = engine.query("test")
    assert result["input_tokens"] == 150
    assert result["output_tokens"] == 40


def test_query_latency_is_positive_float(tmp_knowledge_base, mock_ollama_client):
    engine = CAGEngine(tmp_knowledge_base, _client=mock_ollama_client)
    result = engine.query("test")
    assert isinstance(result["latency_seconds"], float)
    assert result["latency_seconds"] >= 0.0


def test_missing_knowledge_base_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        CAGEngine(tmp_path / "nonexistent.txt")


def test_retry_on_failure(tmp_knowledge_base):
    fail_then_succeed = MagicMock(side_effect=[
        RuntimeError("connection refused"),
        MagicMock(message=MagicMock(content="ok"), prompt_eval_count=10, eval_count=5),
    ])
    client = MagicMock(chat=fail_then_succeed)
    engine = CAGEngine(tmp_knowledge_base, max_retries=3, _client=client)
    result = engine.query("test")
    assert result["answer"] == "ok"
    assert client.chat.call_count == 2


def test_exhausted_retries_raises(tmp_knowledge_base):
    client = MagicMock()
    client.chat.side_effect = RuntimeError("always fails")
    engine = CAGEngine(tmp_knowledge_base, max_retries=2, _client=client)
    with pytest.raises(RuntimeError):
        engine.query("test")


@pytest.mark.asyncio
async def test_query_async_returns_correct_keys(tmp_knowledge_base):
    async_response = MagicMock()
    async_response.message.content = "async answer"
    async_response.prompt_eval_count = 100
    async_response.eval_count = 30

    async_client = MagicMock()
    async_client.chat = AsyncMock(return_value=async_response)

    with patch("src.cag.engine.AsyncClient", return_value=async_client):
        engine = CAGEngine(tmp_knowledge_base)
        result = await engine.query_async("test")

    assert result["answer"] == "async answer"
    assert result["method"] == "CAG"
```

- [ ] **Step 4: Run tests — expect FAIL**

```bash
pytest tests/test_cag_engine.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `CAGEngine` not yet updated.

- [ ] **Step 5: Rewrite `src/cag/engine.py`**

```python
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
            "say \"I don't have information about that in my knowledge base.\"\n\n"
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
        print("  CAG Interactive Session  (model: " + self.model + ")")
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
```

- [ ] **Step 6: Run tests — expect PASS**

```bash
pytest tests/test_cag_engine.py -v
```

Expected: All 9 tests pass.

- [ ] **Step 7: Lint**

```bash
ruff check src/cag/engine.py src/config.py tests/conftest.py tests/test_cag_engine.py
```

Expected: No errors. Fix any that appear before committing.

- [ ] **Step 8: Commit**

```bash
git add src/cag/engine.py src/config.py tests/__init__.py tests/conftest.py tests/test_cag_engine.py
git commit -m "feat: migrate CAG engine to Ollama with retry logic and async support"
```

---

### Task 3: RAG Engine — Ollama Migration + Chunking Tests

**Files:**
- Rewrite: `src/rag/engine.py`
- Create: `tests/test_chunking.py`
- Create: `tests/test_rag_engine.py`

**Interfaces:**
- Consumes: `src.config.OLLAMA_HOST`, `src.config.OLLAMA_MODEL`, `src.config.EMBEDDING_MODEL`, `src.config.MAX_TOKENS`, `src.config.MAX_RETRIES`
- Produces:
  - `chunk_by_topic(text: str) -> list[dict]` — each dict: `{"title": str, "text": str}`
  - `chunk_fixed_size(text: str, chunk_size: int, overlap: int) -> list[dict]`
  - `RAGEngine(knowledge_base_path, model, embedding_model_name, top_k, max_tokens, ollama_host, max_retries, chunking_strategy, _client=None)`
  - `RAGEngine.query(question: str) -> dict` — keys: `answer`, `latency_seconds`, `retrieval_latency_seconds`, `generation_latency_seconds`, `input_tokens`, `output_tokens`, `model`, `method`, `context_used`, `retrieved_chunks`
  - `RAGEngine.query_async(question: str) -> dict` — same keys
  - `RAGEngine.interactive() -> None`

- [ ] **Step 1: Write `tests/test_chunking.py`**

```python
from src.rag.engine import chunk_by_topic, chunk_fixed_size

TOPIC_TEXT = """\
================================================================================
TOPIC: Machine Learning
================================================================================
Machine learning is a subset of artificial intelligence.

================================================================================
TOPIC: Deep Learning
================================================================================
Deep learning uses neural networks with many layers.
"""


def test_chunk_by_topic_finds_all_topics():
    chunks = chunk_by_topic(TOPIC_TEXT)
    assert len(chunks) == 2


def test_chunk_by_topic_titles():
    chunks = chunk_by_topic(TOPIC_TEXT)
    assert chunks[0]["title"] == "Machine Learning"
    assert chunks[1]["title"] == "Deep Learning"


def test_chunk_by_topic_returns_content():
    chunks = chunk_by_topic(TOPIC_TEXT)
    assert "artificial intelligence" in chunks[0]["text"]
    assert "neural networks" in chunks[1]["text"]


def test_chunk_by_topic_strips_whitespace():
    chunks = chunk_by_topic(TOPIC_TEXT)
    for chunk in chunks:
        assert chunk["text"] == chunk["text"].strip()


def test_chunk_by_topic_empty_returns_empty():
    assert chunk_by_topic("no topic markers here") == []


def test_chunk_fixed_size_produces_chunks():
    text = " ".join(["word"] * 500)
    chunks = chunk_fixed_size(text, chunk_size=100, overlap=10)
    assert len(chunks) > 1


def test_chunk_fixed_size_chunk_dict_keys():
    chunks = chunk_fixed_size("a b c d e", chunk_size=3, overlap=1)
    assert all("title" in c and "text" in c for c in chunks)


def test_chunk_fixed_size_respects_chunk_size():
    text = " ".join(str(i) for i in range(200))
    chunks = chunk_fixed_size(text, chunk_size=50, overlap=10)
    for chunk in chunks:
        assert len(chunk["text"].split()) <= 50


def test_chunk_fixed_size_overlap_creates_continuity():
    words = [str(i) for i in range(20)]
    text = " ".join(words)
    chunks = chunk_fixed_size(text, chunk_size=10, overlap=5)
    # Second chunk should start before where first chunk ended
    first_end = set(chunks[0]["text"].split()[-5:])
    second_start = set(chunks[1]["text"].split()[:5])
    assert first_end & second_start  # overlap exists
```

- [ ] **Step 2: Write `tests/test_rag_engine.py`**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.rag.engine import RAGEngine


def test_query_returns_correct_keys(tmp_knowledge_base, mock_ollama_client):
    with patch("src.rag.engine.SentenceTransformer") as mock_st:
        import numpy as np
        mock_st.return_value.encode.return_value = np.random.rand(3, 384).astype("float32")
        engine = RAGEngine(tmp_knowledge_base, _client=mock_ollama_client)
        mock_ollama_client.chat.return_value.message.content = "RAG answer"
        mock_ollama_client.chat.return_value.prompt_eval_count = 80
        mock_ollama_client.chat.return_value.eval_count = 30
        result = engine.query("What is KV cache?")

    assert set(result.keys()) == {
        "answer", "latency_seconds", "retrieval_latency_seconds",
        "generation_latency_seconds", "input_tokens", "output_tokens",
        "model", "method", "context_used", "retrieved_chunks",
    }


def test_query_method_is_rag(tmp_knowledge_base, mock_ollama_client):
    with patch("src.rag.engine.SentenceTransformer") as mock_st:
        import numpy as np
        mock_st.return_value.encode.return_value = np.random.rand(3, 384).astype("float32")
        engine = RAGEngine(tmp_knowledge_base, _client=mock_ollama_client)
        result = engine.query("test")

    assert result["method"] == "RAG"
    assert isinstance(result["retrieved_chunks"], list)


def test_missing_knowledge_base_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        RAGEngine(tmp_path / "nonexistent.txt")


def test_falls_back_to_fixed_chunking_when_no_topics(tmp_path, mock_ollama_client):
    kb = tmp_path / "plain.txt"
    kb.write_text("No topic markers here. Just plain text with many words. " * 50)
    with patch("src.rag.engine.SentenceTransformer") as mock_st:
        import numpy as np
        mock_st.return_value.encode.return_value = np.random.rand(1, 384).astype("float32")
        engine = RAGEngine(kb, _client=mock_ollama_client)
    assert len(engine.chunks) > 0
```

- [ ] **Step 3: Run chunking tests — expect FAIL**

```bash
pytest tests/test_chunking.py -v
```

Expected: FAIL (chunking functions not yet updated).

- [ ] **Step 4: Rewrite `src/rag/engine.py`**

```python
"""
RAG Engine — Retrieval Augmented Generation (Ollama backend)
============================================================
1. Index: chunk → embed (sentence-transformers) → FAISS
2. Query: embed question → top-k retrieval → Ollama generation
"""

import logging
import re
import time
from pathlib import Path

import faiss
import numpy as np
from ollama import AsyncClient, Client
from sentence_transformers import SentenceTransformer

from src.config import (
    EMBEDDING_MODEL,
    MAX_RETRIES,
    MAX_TOKENS,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    RAG_TOP_K,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Chunking helpers
# ---------------------------------------------------------------------------


def chunk_by_topic(text: str) -> list[dict]:
    """Split on === TOPIC: ... === markers. Returns list of {title, text} dicts."""
    pattern = r"={3,}\nTOPIC: (.+?)\n={3,}\n(.*?)(?=={3,}\nTOPIC:|\Z)"
    matches = re.findall(pattern, text, re.DOTALL)
    return [
        {"title": title.strip(), "text": content.strip()}
        for title, content in matches
        if content.strip()
    ]


def chunk_fixed_size(text: str, chunk_size: int = 400, overlap: int = 50) -> list[dict]:
    """Sliding-window word chunking with overlap."""
    words = text.split()
    step = max(1, chunk_size - overlap)
    chunks = []
    for i in range(0, len(words), step):
        chunk_words = words[i : i + chunk_size]
        chunks.append({"title": f"chunk_{i // step}", "text": " ".join(chunk_words)})
    return chunks


# ---------------------------------------------------------------------------
# RAG Engine
# ---------------------------------------------------------------------------


class RAGEngine:
    """
    Retrieval Augmented Generation backed by FAISS + local Ollama model.

    Parameters
    ----------
    knowledge_base_path : str | Path
    model : str
        Ollama model tag.
    embedding_model_name : str
        sentence-transformers model for embedding.
    top_k : int
        Number of chunks to retrieve per query.
    max_tokens : int
        Maximum tokens to generate.
    ollama_host : str
    max_retries : int
    chunking_strategy : str
        "topic" (semantic, preferred) or "fixed" (fallback).
    _client : optional
        Injected Ollama Client for tests.
    """

    def __init__(
        self,
        knowledge_base_path: str | Path,
        model: str = OLLAMA_MODEL,
        embedding_model_name: str = EMBEDDING_MODEL,
        top_k: int = RAG_TOP_K,
        max_tokens: int = MAX_TOKENS,
        ollama_host: str = OLLAMA_HOST,
        max_retries: int = MAX_RETRIES,
        chunking_strategy: str = "topic",
        _client=None,
    ):
        self.model = model
        self.top_k = top_k
        self.max_tokens = max_tokens
        self._ollama_host = ollama_host
        self._max_retries = max_retries
        self._client: Client = _client or Client(host=ollama_host)

        kb_path = Path(knowledge_base_path)
        if not kb_path.exists():
            raise FileNotFoundError(f"Knowledge base not found: {kb_path}")

        logger.info("RAG | loading embedding model: %s", embedding_model_name)
        self.embedder = SentenceTransformer(embedding_model_name)

        raw_text = kb_path.read_text(encoding="utf-8")
        self.chunks = self._chunk(raw_text, chunking_strategy)
        logger.info("RAG | %d chunks created (strategy: %s)", len(self.chunks), chunking_strategy)

        index_time = self._build_index()
        logger.info("RAG | FAISS index built in %.3fs | model=%s | top_k=%d", index_time, model, top_k)

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def _chunk(self, text: str, strategy: str) -> list[dict]:
        if strategy == "topic":
            chunks = chunk_by_topic(text)
            if len(chunks) < 3:
                logger.warning("Too few topic chunks (%d); falling back to fixed-size.", len(chunks))
                chunks = chunk_fixed_size(text)
        else:
            chunks = chunk_fixed_size(text)
        return chunks

    def _build_index(self) -> float:
        start = time.perf_counter()
        texts = [c["text"] for c in self.chunks]
        embeddings = self.embedder.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        self._embeddings = embeddings / np.maximum(norms, 1e-10)
        dim = self._embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dim)
        self._index.add(self._embeddings.astype(np.float32))
        return time.perf_counter() - start

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def _retrieve(self, question: str) -> tuple[list[dict], float]:
        start = time.perf_counter()
        q_emb = self.embedder.encode([question], convert_to_numpy=True)
        q_norm = q_emb / np.maximum(np.linalg.norm(q_emb, axis=1, keepdims=True), 1e-10)
        scores, indices = self._index.search(q_norm.astype(np.float32), self.top_k)
        retrieval_time = time.perf_counter() - start

        results = [
            {
                "title": self.chunks[idx]["title"],
                "text": self.chunks[idx]["text"],
                "similarity_score": round(float(score), 4),
            }
            for score, idx in zip(scores[0], indices[0])
            if idx >= 0
        ]
        return results, retrieval_time

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def _build_messages(self, question: str, retrieved_chunks: list[dict]) -> list[dict]:
        context = "\n\n".join(
            f"--- CHUNK {i}: {c['title']} (score: {c['similarity_score']}) ---\n{c['text']}"
            for i, c in enumerate(retrieved_chunks, 1)
        )
        system = (
            "You are an expert AI/ML assistant. Answer using ONLY the context chunks below. "
            "If the answer is not in the context, say 'The retrieved context does not contain "
            "enough information to answer this question.'\n\nBe precise and reference the chunks."
        )
        user = f"CONTEXT:\n{context}\n\nQUESTION: {question}"
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]

    def _chat(self, messages: list[dict]) -> object:
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
                    attempt + 1, self._max_retries, exc, wait,
                )
                time.sleep(wait)
        raise RuntimeError(f"Ollama call failed after {self._max_retries} attempts") from last_exc

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def query(self, question: str) -> dict:
        """Retrieve top-k chunks and generate an answer."""
        total_start = time.perf_counter()
        retrieved_chunks, retrieval_latency = self._retrieve(question)

        messages = self._build_messages(question, retrieved_chunks)
        gen_start = time.perf_counter()
        response = self._chat(messages)
        generation_latency = time.perf_counter() - gen_start
        total_latency = time.perf_counter() - total_start

        return {
            "answer": response.message.content,
            "latency_seconds": round(total_latency, 3),
            "retrieval_latency_seconds": round(retrieval_latency, 3),
            "generation_latency_seconds": round(generation_latency, 3),
            "input_tokens": response.prompt_eval_count or 0,
            "output_tokens": response.eval_count or 0,
            "model": self.model,
            "method": "RAG",
            "context_used": f"Top-{self.top_k} retrieved chunks",
            "retrieved_chunks": [
                {"title": c["title"], "similarity_score": c["similarity_score"]}
                for c in retrieved_chunks
            ],
        }

    async def query_async(self, question: str) -> dict:
        """Async version — retrieval is sync (local FAISS), only generation is async."""
        total_start = time.perf_counter()
        retrieved_chunks, retrieval_latency = self._retrieve(question)

        messages = self._build_messages(question, retrieved_chunks)
        gen_start = time.perf_counter()
        client = AsyncClient(host=self._ollama_host)
        response = await client.chat(
            model=self.model,
            messages=messages,
            options={"num_predict": self.max_tokens},
        )
        generation_latency = time.perf_counter() - gen_start
        total_latency = time.perf_counter() - total_start

        return {
            "answer": response.message.content,
            "latency_seconds": round(total_latency, 3),
            "retrieval_latency_seconds": round(retrieval_latency, 3),
            "generation_latency_seconds": round(generation_latency, 3),
            "input_tokens": response.prompt_eval_count or 0,
            "output_tokens": response.eval_count or 0,
            "model": self.model,
            "method": "RAG",
            "context_used": f"Top-{self.top_k} retrieved chunks",
            "retrieved_chunks": [
                {"title": c["title"], "similarity_score": c["similarity_score"]}
                for c in retrieved_chunks
            ],
        }

    def interactive(self) -> None:
        print("\n" + "=" * 60)
        print(f"  RAG Interactive Session  (model: {self.model})")
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
                f"\n[Total: {result['latency_seconds']}s "
                f"(retrieval: {result['retrieval_latency_seconds']}s + "
                f"generation: {result['generation_latency_seconds']}s) | "
                f"Tokens in: {result['input_tokens']:,} | out: {result['output_tokens']:,}]"
            )
            print(f"[Retrieved: {[c['title'] for c in result['retrieved_chunks']]}]\n")
```

- [ ] **Step 5: Run all tests — expect PASS**

```bash
pytest tests/test_chunking.py tests/test_rag_engine.py -v
```

Expected: All tests pass.

- [ ] **Step 6: Lint**

```bash
ruff check src/rag/engine.py tests/test_chunking.py tests/test_rag_engine.py
```

- [ ] **Step 7: Commit**

```bash
git add src/rag/engine.py tests/test_chunking.py tests/test_rag_engine.py
git commit -m "feat: migrate RAG engine to Ollama with retry logic and async support"
```

---

### Task 4: Benchmark Evaluator — Fix + Ollama Migration

**Files:**
- Rewrite: `src/benchmark/evaluator.py`
- Create: `tests/test_evaluator.py`

**Interfaces:**
- Consumes: `src.config.OLLAMA_MODEL`, `src.config.MAX_RETRIES`
- Produces:
  - `LLMJudge(judge_model, ollama_host, max_retries, _client=None)`
  - `LLMJudge.score(question, answer, expected_concepts) -> dict` — keys: `correctness`, `completeness`, `coherence`, `groundedness`, `total`, `reasoning`
  - `LLMJudge.score_async(question, answer, expected_concepts) -> dict` — same keys
  - `LLMJudge._parse_judge_response(raw: str) -> dict` — strips markdown fences, validates required fields
  - `Benchmarker(cag_engine, rag_engine, questions, use_judge, results_dir)`
  - `Benchmarker.run(verbose) -> dict`
  - `Benchmarker.run_async(verbose) -> dict` (used in Task 7)
  - `Benchmarker._compute_summary(results) -> dict`

Key changes vs original:
- Anthropic client → Ollama client
- Remove `PRICING` dict and `compute_cost` — local models have no API cost; keep field as `0.0`
- Fix `LLMJudge.score`: add `_parse_judge_response` that strips markdown fences before `json.loads`
- Validate all four required score fields exist before computing total

- [ ] **Step 1: Write `tests/test_evaluator.py`**

```python
import json
import pytest
from unittest.mock import MagicMock
from src.benchmark.evaluator import LLMJudge, Benchmarker, DEFAULT_QUESTIONS


# --- LLMJudge._parse_judge_response ---

def make_judge():
    j = LLMJudge.__new__(LLMJudge)
    return j


def test_parse_valid_json():
    j = make_judge()
    raw = '{"correctness": 4, "completeness": 3, "coherence": 5, "groundedness": 4, "reasoning": "Good."}'
    result = j._parse_judge_response(raw)
    assert result["correctness"] == 4
    assert result["total"] == 4.0


def test_parse_strips_markdown_fences():
    j = make_judge()
    raw = "```json\n{\"correctness\": 4, \"completeness\": 3, \"coherence\": 5, \"groundedness\": 4, \"reasoning\": \"ok\"}\n```"
    result = j._parse_judge_response(raw)
    assert result["correctness"] == 4


def test_parse_strips_bare_code_fences():
    j = make_judge()
    raw = "```\n{\"correctness\": 5, \"completeness\": 5, \"coherence\": 5, \"groundedness\": 5, \"reasoning\": \"perfect\"}\n```"
    result = j._parse_judge_response(raw)
    assert result["total"] == 5.0


def test_parse_raises_on_missing_field():
    j = make_judge()
    raw = '{"correctness": 4, "completeness": 3}'  # missing coherence + groundedness
    with pytest.raises(ValueError, match="Missing fields"):
        j._parse_judge_response(raw)


def test_parse_raises_on_invalid_json():
    j = make_judge()
    with pytest.raises(json.JSONDecodeError):
        j._parse_judge_response("not json at all")


# --- LLMJudge.score ---

def test_score_returns_zeros_on_error():
    mock_client = MagicMock()
    mock_client.chat.side_effect = RuntimeError("connection refused")
    judge = LLMJudge(_client=mock_client, max_retries=1)
    result = judge.score("q", "a", ["concept"])
    assert result["total"] == 0
    assert "Judge error" in result["reasoning"]


def test_score_parses_valid_response():
    raw = '{"correctness": 5, "completeness": 4, "coherence": 5, "groundedness": 4, "reasoning": "great"}'
    mock_resp = MagicMock()
    mock_resp.message.content = raw
    mock_client = MagicMock()
    mock_client.chat.return_value = mock_resp
    judge = LLMJudge(_client=mock_client)
    result = judge.score("q", "a", ["c"])
    assert result["total"] == 4.5


# --- Benchmarker._compute_summary ---

def test_compute_summary_cag_wins():
    bench = Benchmarker.__new__(Benchmarker)
    results = [
        {
            "cag": {"latency_seconds": 1.0, "input_tokens": 100, "output_tokens": 50,
                    "judge_scores": {"total": 5.0}},
            "rag": {"latency_seconds": 0.5, "input_tokens": 40, "output_tokens": 20,
                    "judge_scores": {"total": 3.0}},
        },
        {
            "cag": {"latency_seconds": 2.0, "input_tokens": 200, "output_tokens": 80,
                    "judge_scores": {"total": 4.0}},
            "rag": {"latency_seconds": 1.0, "input_tokens": 50, "output_tokens": 25,
                    "judge_scores": {"total": 4.0}},
        },
    ]
    summary = bench._compute_summary(results)
    assert summary["cag"]["wins"] == 1
    assert summary["rag"]["wins"] == 0
    assert summary["ties"] == 1
    assert summary["cag"]["avg_latency_seconds"] == 1.5


def test_default_questions_have_required_keys():
    for q in DEFAULT_QUESTIONS:
        assert "id" in q
        assert "question" in q
        assert "category" in q
        assert "expected_concepts" in q
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_evaluator.py -v
```

Expected: FAIL — `LLMJudge` doesn't have `_parse_judge_response` yet; Anthropic import will fail.

- [ ] **Step 3: Rewrite `src/benchmark/evaluator.py`**

```python
"""
Benchmark Evaluator
===================
Runs questions through CAG and RAG, measures latency and token counts,
scores answers with an LLM-as-judge (local Ollama), saves JSON + CSV.
"""

import asyncio
import csv
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path

from ollama import AsyncClient, Client

from src.config import MAX_RETRIES, OLLAMA_HOST, OLLAMA_MODEL

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
        "expected_concepts": ["hallucination", "context window", "faithfulness", "retrieval errors", "CAG", "RAG"],
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
    '{{ "correctness": <1-5>, "completeness": <1-5>, "coherence": <1-5>, '
    '"groundedness": <1-5>, "reasoning": "<one sentence>" }}'
)

_REQUIRED_FIELDS = {"correctness", "completeness", "coherence", "groundedness"}


class LLMJudge:
    """Scores answers using a local Ollama model as judge."""

    def __init__(
        self,
        judge_model: str = OLLAMA_MODEL,
        ollama_host: str = OLLAMA_HOST,
        max_retries: int = MAX_RETRIES,
        _client=None,
    ):
        self.judge_model = judge_model
        self._ollama_host = ollama_host
        self._max_retries = max_retries
        self._client: Client = _client or Client(host=ollama_host)

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
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]

        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = self._client.chat(
                    model=self.judge_model,
                    messages=messages,
                    options={"num_predict": 256},
                )
                return self._parse_judge_response(response.message.content)
            except Exception as exc:
                last_exc = exc
                logger.warning("Judge attempt %d/%d failed: %s", attempt + 1, self._max_retries, exc)
                time.sleep(2**attempt)

        return {
            "correctness": 0, "completeness": 0, "coherence": 0, "groundedness": 0,
            "total": 0, "reasoning": f"Judge error: {last_exc}",
        }

    async def score_async(
        self, question: str, answer: str, expected_concepts: list[str]
    ) -> dict:
        system = _JUDGE_SYSTEM.format(expected_concepts=", ".join(expected_concepts))
        user = f"QUESTION: {question}\n\nANSWER TO EVALUATE:\n{answer}"
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        try:
            client = AsyncClient(host=self._ollama_host)
            response = await client.chat(
                model=self.judge_model,
                messages=messages,
                options={"num_predict": 256},
            )
            return self._parse_judge_response(response.message.content)
        except Exception as exc:
            logger.warning("Async judge failed: %s", exc)
            return {
                "correctness": 0, "completeness": 0, "coherence": 0, "groundedness": 0,
                "total": 0, "reasoning": f"Judge error: {exc}",
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
                print(f"[{i}/{len(self.questions)}] {q.get('id', f'Q{i:02d}')} ({q.get('category', 'general')})")
                print(f"  Q: {q['question'][:80]}{'...' if len(q['question']) > 80 else ''}")

            cag_result = self.cag.query(q["question"])
            rag_result = self.rag.query(q["question"])

            cag_scores, rag_scores = {}, {}
            if self.judge:
                cag_scores = self.judge.score(q["question"], cag_result["answer"], q.get("expected_concepts", []))
                rag_scores = self.judge.score(q["question"], rag_result["answer"], q.get("expected_concepts", []))

            entry = self._build_entry(q, cag_result, rag_result, cag_scores, rag_scores)
            results.append(entry)
            if verbose:
                self._print_result_row(entry)

        return self._finalize(results, timestamp)

    # ------------------------------------------------------------------
    # Async run (parallel per question — see Task 7)
    # ------------------------------------------------------------------

    async def run_async(self, verbose: bool = True) -> dict:
        results = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._print_header(timestamp, async_mode=True)

        for i, q in enumerate(self.questions, 1):
            if verbose:
                print(f"[{i}/{len(self.questions)}] {q.get('id', f'Q{i:02d}')} ({q.get('category', 'general')})")

            cag_result, rag_result = await asyncio.gather(
                self.cag.query_async(q["question"]),
                self.rag.query_async(q["question"]),
            )

            cag_scores, rag_scores = {}, {}
            if self.judge:
                cag_scores, rag_scores = await asyncio.gather(
                    self.judge.score_async(q["question"], cag_result["answer"], q.get("expected_concepts", [])),
                    self.judge.score_async(q["question"], rag_result["answer"], q.get("expected_concepts", [])),
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

        print(f"  CAG: latency={cag['latency_seconds']}s | tokens_in={cag['input_tokens']:,} | score={cag_score}/5")
        print(f"  RAG: latency={rag['latency_seconds']}s | tokens_in={rag['input_tokens']:,} | score={rag_score}/5{winner}\n")

    def _compute_summary(self, results: list[dict]) -> dict:
        def avg(lst: list) -> float:
            return round(sum(lst) / len(lst), 3) if lst else 0.0

        cag_scores = [r["cag"]["judge_scores"].get("total", 0) for r in results if r["cag"]["judge_scores"]]
        rag_scores = [r["rag"]["judge_scores"].get("total", 0) for r in results if r["rag"]["judge_scores"]]
        cag_wins = sum(
            1 for r in results
            if r["cag"]["judge_scores"].get("total", 0) > r["rag"]["judge_scores"].get("total", 0)
        )
        rag_wins = sum(
            1 for r in results
            if r["rag"]["judge_scores"].get("total", 0) > r["cag"]["judge_scores"].get("total", 0)
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
        print(f"  {'Avg Latency (s)':<30} {c['avg_latency_seconds']:>12} {r['avg_latency_seconds']:>12}")
        print(f"  {'Avg Input Tokens':<30} {c['avg_input_tokens']:>12,.0f} {r['avg_input_tokens']:>12,.0f}")
        print(f"  {'Avg Judge Score (/5)':<30} {c['avg_judge_score']:>12} {r['avg_judge_score']:>12}")
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
                "retrieved_chunks": str([c["title"] for c in r["rag"].get("retrieved_chunks") or []]),
                "winner": (
                    "CAG" if r["cag"]["judge_scores"].get("total", 0) > r["rag"]["judge_scores"].get("total", 0)
                    else "RAG" if r["rag"]["judge_scores"].get("total", 0) > r["cag"]["judge_scores"].get("total", 0)
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
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_evaluator.py -v
```

Expected: All tests pass.

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 6: Lint**

```bash
ruff check src/benchmark/evaluator.py tests/test_evaluator.py
```

- [ ] **Step 7: Commit**

```bash
git add src/benchmark/evaluator.py tests/test_evaluator.py
git commit -m "feat: migrate evaluator to Ollama, fix judge JSON parsing, add async run"
```

---

### Task 5: Update `main.py` + Logging

**Files:**
- Modify: `main.py`

**Changes:**
- Remove `check_api_key()` — replace with `check_ollama()` that pings `OLLAMA_HOST/api/tags`
- Import `setup_logging` from `src.config` and call it at startup
- `cmd_benchmark` calls `asyncio.run(bench.run_async(...))` instead of `bench.run(...)`
- Remove Anthropic pricing references from `DEFAULT_MODEL` (change to read from `OLLAMA_MODEL`)
- Remove `json` import (no longer needed at top level)

- [ ] **Step 1: Rewrite `main.py`**

```python
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

Environment variables (see .env.example):
    OLLAMA_HOST     Ollama server URL (default: http://localhost:11434)
    OLLAMA_MODEL    Model tag (default: llama3.1:8b)
    RAG_TOP_K       Top-k chunks for RAG (default: 3)
    LOG_LEVEL       Logging verbosity (default: INFO)
"""

import argparse
import asyncio
import sys
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import OLLAMA_HOST, OLLAMA_MODEL, RAG_TOP_K, setup_logging
from src.cag.engine import CAGEngine
from src.rag.engine import RAGEngine
from src.benchmark.evaluator import Benchmarker

KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge_base" / "aiml_corpus.txt"
RESULTS_DIR = PROJECT_ROOT / "results"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def check_ollama() -> None:
    try:
        urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=3)
    except urllib.error.URLError:
        print(f"[ERROR] Cannot reach Ollama at {OLLAMA_HOST}")
        print("  1. Start Ollama:  ollama serve")
        print(f"  2. Pull a model:  ollama pull {OLLAMA_MODEL}")
        sys.exit(1)


def print_banner() -> None:
    print("""
╔══════════════════════════════════════════════════════════════╗
║           CAG vs RAG Showdown Framework                      ║
║           Context Augmented Generation vs                    ║
║           Retrieval Augmented Generation                     ║
╚══════════════════════════════════════════════════════════════╝
""")


def format_answer_block(method: str, result: dict) -> str:
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


def cmd_benchmark(args) -> None:
    print_banner()
    check_ollama()

    model = args.model or OLLAMA_MODEL
    top_k = args.top_k or RAG_TOP_K
    use_judge = not args.no_judge

    print(f"  Model       : {model}")
    print(f"  RAG top-k   : {top_k}")
    print(f"  LLM Judge   : {'enabled' if use_judge else 'disabled'}")
    print(f"  Mode        : async parallel\n")

    cag = CAGEngine(KNOWLEDGE_BASE, model=model)
    rag = RAGEngine(KNOWLEDGE_BASE, model=model, top_k=top_k)
    bench = Benchmarker(cag_engine=cag, rag_engine=rag, use_judge=use_judge, results_dir=RESULTS_DIR)
    asyncio.run(bench.run_async(verbose=True))


def cmd_chat(args) -> None:
    print_banner()
    check_ollama()

    model = args.model or OLLAMA_MODEL
    if args.method == "cag":
        CAGEngine(KNOWLEDGE_BASE, model=model).interactive()
    else:
        RAGEngine(KNOWLEDGE_BASE, model=model, top_k=args.top_k or RAG_TOP_K).interactive()


def cmd_ask(args) -> None:
    print_banner()
    check_ollama()

    question = args.question
    model = args.model or OLLAMA_MODEL
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
```

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests pass (nothing in tests imports main.py directly).

- [ ] **Step 3: Lint**

```bash
ruff check main.py
```

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "feat: update main.py — Ollama health check, async benchmark, structured logging"
```

---

### Task 6: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

**What it does:** On every push/PR to `main`, install Python 3.11, install dev deps, lint with `ruff`, run the full pytest suite. No live Ollama needed — all tests are mocked.

- [ ] **Step 1: Create `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    name: Lint & Test
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Lint (ruff)
        run: ruff check src tests main.py api dashboard

      - name: Test (pytest)
        run: pytest tests/ -v --cov=src --cov-report=term-missing
```

- [ ] **Step 2: Create `api/__init__.py`** (empty — needed for ruff to lint the `api` directory in the CI step above)

Empty file.

- [ ] **Step 3: Create `dashboard/__init__.py`** (empty)

Empty file, but also create `dashboard/app.py` as a minimal stub so `ruff check dashboard` doesn't fail:

```python
# dashboard/app.py — full implementation in Task 10
```

(Just a comment stub — ruff won't error on an empty-ish file.)

- [ ] **Step 4: Commit and push — let CI run**

```bash
git add .github/ api/__init__.py dashboard/__init__.py dashboard/app.py
git commit -m "feat: add GitHub Actions CI with ruff + pytest"
git push origin main
```

Then open `https://github.com/<your-username>/CAG-vs-RAG-Showdown/actions` to verify the workflow goes green.

---

### Task 7: FastAPI REST Layer

**Files:**
- Create: `api/app.py`
- Create: `tests/test_api.py`

**Endpoints:**
- `GET /health` → `{"status": "ok", "model": "<model>", "ollama_host": "<host>"}`
- `POST /query/cag` body `{"question": "..."}` → full query result dict
- `POST /query/rag` body `{"question": "..."}` → full query result dict
- `POST /query/both` body `{"question": "..."}` → `{"cag": {...}, "rag": {...}}`
- `POST /benchmark` body `{"use_judge": true, "top_k": 3}` → full benchmark result dict

**Interfaces:**
- Consumes: `CAGEngine`, `RAGEngine`, `Benchmarker` from Tasks 2/3/4
- Consumes: `src.config.OLLAMA_MODEL`, `src.config.OLLAMA_HOST`

- [ ] **Step 1: Write `tests/test_api.py`**

```python
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


MOCK_CAG_RESULT = {
    "answer": "KV cache stores attention keys and values.",
    "latency_seconds": 1.2,
    "input_tokens": 500,
    "output_tokens": 80,
    "model": "llama3.1:8b",
    "method": "CAG",
    "context_used": "Full knowledge base (no retrieval)",
    "retrieved_chunks": None,
}

MOCK_RAG_RESULT = {
    "answer": "KV cache is a memory optimization.",
    "latency_seconds": 0.4,
    "retrieval_latency_seconds": 0.05,
    "generation_latency_seconds": 0.35,
    "input_tokens": 200,
    "output_tokens": 60,
    "model": "llama3.1:8b",
    "method": "RAG",
    "context_used": "Top-3 retrieved chunks",
    "retrieved_chunks": [{"title": "KV Cache", "similarity_score": 0.91}],
}


@pytest.fixture
def client(tmp_knowledge_base):
    mock_cag = MagicMock()
    mock_cag.query.return_value = MOCK_CAG_RESULT
    mock_cag.query_async = MagicMock(return_value=MOCK_CAG_RESULT)

    mock_rag = MagicMock()
    mock_rag.query.return_value = MOCK_RAG_RESULT
    mock_rag.query_async = MagicMock(return_value=MOCK_RAG_RESULT)

    with patch("api.app.CAGEngine", return_value=mock_cag), \
         patch("api.app.RAGEngine", return_value=mock_rag):
        from api.app import app
        return TestClient(app)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model" in data


def test_query_cag(client):
    response = client.post("/query/cag", json={"question": "What is KV cache?"})
    assert response.status_code == 200
    data = response.json()
    assert data["method"] == "CAG"
    assert "answer" in data


def test_query_rag(client):
    response = client.post("/query/rag", json={"question": "What is KV cache?"})
    assert response.status_code == 200
    data = response.json()
    assert data["method"] == "RAG"
    assert "retrieved_chunks" in data


def test_query_both(client):
    response = client.post("/query/both", json={"question": "What is KV cache?"})
    assert response.status_code == 200
    data = response.json()
    assert "cag" in data
    assert "rag" in data


def test_query_empty_question_rejected(client):
    response = client.post("/query/cag", json={"question": ""})
    assert response.status_code == 422
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_api.py -v
```

Expected: FAIL — `api.app` doesn't exist yet.

- [ ] **Step 3: Write `api/app.py`**

```python
"""
CAG vs RAG Showdown — FastAPI REST layer
=========================================
Serves the CAG and RAG engines as HTTP endpoints.
Run with: uvicorn api.app:app --reload
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, field_validator

from src.benchmark.evaluator import Benchmarker
from src.cag.engine import CAGEngine
from src.config import OLLAMA_HOST, OLLAMA_MODEL, RAG_TOP_K
from src.rag.engine import RAGEngine

logger = logging.getLogger(__name__)

KNOWLEDGE_BASE = Path(__file__).parent.parent / "knowledge_base" / "aiml_corpus.txt"

_cag: CAGEngine | None = None
_rag: RAGEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _cag, _rag
    logger.info("Loading engines on startup (model=%s)...", OLLAMA_MODEL)
    _cag = CAGEngine(KNOWLEDGE_BASE, model=OLLAMA_MODEL)
    _rag = RAGEngine(KNOWLEDGE_BASE, model=OLLAMA_MODEL, top_k=RAG_TOP_K)
    logger.info("Engines ready.")
    yield
    _cag = None
    _rag = None


app = FastAPI(
    title="CAG vs RAG Showdown API",
    description="Benchmark and compare Context Augmented Generation vs Retrieval Augmented Generation",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Dependency injection (enables test overrides)
# ---------------------------------------------------------------------------


def get_cag() -> CAGEngine:
    if _cag is None:
        raise HTTPException(status_code=503, detail="CAG engine not initialized")
    return _cag


def get_rag() -> RAGEngine:
    if _rag is None:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    return _rag


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class QueryRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("question must not be empty")
        return v.strip()


class BenchmarkRequest(BaseModel):
    use_judge: bool = True
    top_k: int = RAG_TOP_K


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
def health():
    return {"status": "ok", "model": OLLAMA_MODEL, "ollama_host": OLLAMA_HOST}


@app.post("/query/cag")
def query_cag(req: QueryRequest, cag: Annotated[CAGEngine, Depends(get_cag)]):
    try:
        return cag.query(req.question)
    except Exception as exc:
        logger.error("CAG query failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/query/rag")
def query_rag(req: QueryRequest, rag: Annotated[RAGEngine, Depends(get_rag)]):
    try:
        return rag.query(req.question)
    except Exception as exc:
        logger.error("RAG query failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/query/both")
def query_both(
    req: QueryRequest,
    cag: Annotated[CAGEngine, Depends(get_cag)],
    rag: Annotated[RAGEngine, Depends(get_rag)],
):
    try:
        return {"cag": cag.query(req.question), "rag": rag.query(req.question)}
    except Exception as exc:
        logger.error("Dual query failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/benchmark")
def run_benchmark(
    req: BenchmarkRequest,
    cag: Annotated[CAGEngine, Depends(get_cag)],
    rag: Annotated[RAGEngine, Depends(get_rag)],
):
    try:
        bench = Benchmarker(
            cag_engine=cag,
            rag_engine=rag,
            use_judge=req.use_judge,
            results_dir=Path(__file__).parent.parent / "results",
        )
        return bench.run(verbose=False)
    except Exception as exc:
        logger.error("Benchmark failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
```

- [ ] **Step 4: Run API tests — expect PASS**

```bash
pytest tests/test_api.py -v
```

Expected: All 5 tests pass.

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 6: Lint**

```bash
ruff check api/app.py tests/test_api.py
```

- [ ] **Step 7: Commit**

```bash
git add api/app.py api/__init__.py tests/test_api.py
git commit -m "feat: add FastAPI REST layer with /health, /query/*, /benchmark endpoints"
```

---

### Task 8: Docker + Docker Compose

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`
- Create: `docker-compose.yml`

**What it builds:** Three services — `ollama` (LLM server + model), `api` (FastAPI via uvicorn), `dashboard` (Streamlit — stubbed now, filled in Task 9). The `ollama` service uses a health check so `api` only starts after Ollama is ready.

No tests for this task — verify manually by running `docker compose up`.

- [ ] **Step 1: Write `.dockerignore`**

```dockerignore
.git
.gitignore
.env
.venv
venv
__pycache__
*.pyc
*.pyd
*.egg-info
dist
build
results/*.json
results/*.csv
.pytest_cache
.coverage
htmlcov
docs
*.md
```

- [ ] **Step 2: Write `Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install build deps for faiss-cpu
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy source after deps so layer is cached
COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Write `docker-compose.yml`**

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:11434/api/tags || exit 1"]
      interval: 15s
      timeout: 10s
      retries: 8
      start_period: 30s

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - OLLAMA_MODEL=${OLLAMA_MODEL:-llama3.1:8b}
      - RAG_TOP_K=${RAG_TOP_K:-3}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    depends_on:
      ollama:
        condition: service_healthy
    restart: on-failure

  dashboard:
    build: .
    command: streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0
    ports:
      - "8501:8501"
    environment:
      - RESULTS_DIR=/app/results
    volumes:
      - ./results:/app/results
    depends_on:
      - api

volumes:
  ollama_data:
```

- [ ] **Step 4: Commit**

```bash
git add Dockerfile .dockerignore docker-compose.yml
git commit -m "feat: add Dockerfile and Docker Compose with Ollama + API + Dashboard services"
```

- [ ] **Step 5: Smoke-test Docker build (optional, requires Docker installed)**

```bash
docker compose build api
```

Expected: Build succeeds with no errors.

---

### Task 9: Streamlit Results Dashboard

**Files:**
- Rewrite: `dashboard/app.py`

**What it does:** Loads any JSON file from `results/`, shows KPI metrics (avg score, avg latency, wins), a score comparison bar chart, a latency bar chart, a per-question results table, and an expandable per-question detail pane with both answers and judge scores side by side.

- [ ] **Step 1: Rewrite `dashboard/app.py`**

```python
"""
CAG vs RAG Showdown — Streamlit Dashboard
==========================================
Run: streamlit run dashboard/app.py
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

RESULTS_DIR = Path(__file__).parent.parent / "results"

st.set_page_config(
    page_title="CAG vs RAG Showdown",
    page_icon="⚔️",
    layout="wide",
)

st.title("⚔️ CAG vs RAG Benchmark Dashboard")

# ---------------------------------------------------------------------------
# Sidebar — file selection
# ---------------------------------------------------------------------------

result_files = sorted(RESULTS_DIR.glob("benchmark_*.json"), reverse=True)

if not result_files:
    st.warning("No benchmark results found yet.")
    st.info("Run a benchmark first:  `python main.py benchmark`")
    st.stop()

selected_file = st.sidebar.selectbox(
    "Benchmark Run",
    result_files,
    format_func=lambda p: p.stem,
)

with open(selected_file, encoding="utf-8") as f:
    data = json.load(f)

summary = data["summary"]
results = data["results"]

st.sidebar.caption(f"Run timestamp: {data.get('timestamp', 'unknown')}")
st.sidebar.caption(f"Questions: {summary['num_questions']}")

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------

st.subheader("Summary")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### CAG")
    st.metric("Avg Judge Score", f"{summary['cag']['avg_judge_score']:.2f} / 5")
    st.metric("Avg Latency", f"{summary['cag']['avg_latency_seconds']:.2f}s")
    st.metric("Wins", summary["cag"]["wins"])

with col2:
    st.markdown("### RAG")
    st.metric("Avg Judge Score", f"{summary['rag']['avg_judge_score']:.2f} / 5")
    st.metric("Avg Latency", f"{summary['rag']['avg_latency_seconds']:.2f}s")
    st.metric("Wins", summary["rag"]["wins"])

with col3:
    st.markdown("### Head-to-head")
    st.metric("Ties", summary["ties"])
    total = summary["num_questions"]
    cag_pct = round(summary["cag"]["wins"] / total * 100) if total else 0
    rag_pct = round(summary["rag"]["wins"] / total * 100) if total else 0
    st.write(f"CAG win rate: **{cag_pct}%**")
    st.write(f"RAG win rate: **{rag_pct}%**")

st.divider()

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

chart_col1, chart_col2 = st.columns(2)

ids = [r["id"] for r in results]
cag_scores = [r["cag"]["judge_scores"].get("total", 0) for r in results]
rag_scores = [r["rag"]["judge_scores"].get("total", 0) for r in results]
cag_latencies = [r["cag"]["latency_seconds"] for r in results]
rag_latencies = [r["rag"]["latency_seconds"] for r in results]

with chart_col1:
    st.subheader("Judge Score by Question")
    score_df = pd.DataFrame({"CAG": cag_scores, "RAG": rag_scores}, index=ids)
    st.bar_chart(score_df, y_label="Score (0–5)")

with chart_col2:
    st.subheader("Latency by Question (s)")
    latency_df = pd.DataFrame({"CAG": cag_latencies, "RAG": rag_latencies}, index=ids)
    st.bar_chart(latency_df, y_label="Seconds")

st.divider()

# ---------------------------------------------------------------------------
# Results table
# ---------------------------------------------------------------------------

st.subheader("Per-Question Results")
rows = []
for r in results:
    cag_s = r["cag"]["judge_scores"].get("total", 0)
    rag_s = r["rag"]["judge_scores"].get("total", 0)
    rows.append({
        "ID": r["id"],
        "Category": r["category"],
        "Question": r["question"][:70] + ("..." if len(r["question"]) > 70 else ""),
        "CAG Score": cag_s,
        "RAG Score": rag_s,
        "CAG Latency (s)": r["cag"]["latency_seconds"],
        "RAG Latency (s)": r["rag"]["latency_seconds"],
        "Winner": "CAG" if cag_s > rag_s else ("RAG" if rag_s > cag_s else "TIE"),
    })

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

# ---------------------------------------------------------------------------
# Per-question detail
# ---------------------------------------------------------------------------

st.subheader("Question Detail")
selected_id = st.selectbox("Select question", ids)
q_data = next(r for r in results if r["id"] == selected_id)

st.markdown(f"**Category:** {q_data['category']}")
st.markdown(f"**Question:** {q_data['question']}")
st.markdown(f"**Expected concepts:** {', '.join(q_data.get('expected_concepts', []))}")

detail_col1, detail_col2 = st.columns(2)

with detail_col1:
    st.markdown("#### CAG Answer")
    st.write(q_data["cag"]["answer"])
    st.markdown("**Judge Scores**")
    scores = q_data["cag"]["judge_scores"]
    if scores:
        st.json({k: v for k, v in scores.items() if k != "total"})
        st.metric("Total", f"{scores.get('total', 'N/A')} / 5")

with detail_col2:
    st.markdown("#### RAG Answer")
    st.write(q_data["rag"]["answer"])
    retrieved = q_data["rag"].get("retrieved_chunks") or []
    if retrieved:
        st.markdown(f"**Retrieved chunks:** {[c['title'] for c in retrieved]}")
    st.markdown("**Judge Scores**")
    scores = q_data["rag"]["judge_scores"]
    if scores:
        st.json({k: v for k, v in scores.items() if k != "total"})
        st.metric("Total", f"{scores.get('total', 'N/A')} / 5")
```

- [ ] **Step 2: Lint**

```bash
ruff check dashboard/app.py
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/app.py dashboard/__init__.py
git commit -m "feat: add Streamlit dashboard with KPI metrics, charts, and per-question detail"
```

---

## Self-Review

### Spec coverage check

| Audit Finding | Task that addresses it |
|---|---|
| C1: No error handling on API calls | Task 2 + Task 3 (`_chat` retry loop) |
| C2: LLM judge JSON parsing fragile | Task 4 (`_parse_judge_response`) |
| C3: No `.gitignore` | Task 1 |
| I1: Zero tests | Tasks 2, 3, 4, 7 (test_*.py files) |
| I2: No prompt caching — N/A for Ollama | Removed (Ollama-local has no prompt caching) |
| I3: Stale hardcoded pricing | Task 4 (pricing removed entirely) |
| I4: No CI/CD | Task 6 |
| I5: Unpinned `>=` deps | Task 1 (`pyproject.toml`) |
| I6: No `pyproject.toml` | Task 1 |
| I7: No structured logging | Tasks 1, 2, 3, 4, 5 |
| I8: Benchmark is synchronous | Tasks 4 + 5 (`run_async`, `asyncio.run`) |
| N1: No Docker | Task 8 |
| N2: No rich terminal output | Not included — scope deferred (use `tqdm` later if desired) |
| N4: `Optional` imported but unused | Fixed during rewrites (not used in new code) |
| N5: No API key validation | Replaced with `check_ollama()` in Task 5 |
| FastAPI layer | Task 7 |
| Streamlit dashboard | Task 9 |

### Placeholder scan

No placeholders found — all steps contain complete code.

### Type consistency check

- `CAGEngine.query()` returns `dict` with 8 keys — matches what `Benchmarker._build_entry()` unpacks
- `RAGEngine.query()` returns `dict` with 10 keys — `retrieved_chunks` key present, matches API schema
- `LLMJudge._parse_judge_response()` always returns dict with `correctness`, `completeness`, `coherence`, `groundedness`, `total`, `reasoning` — matches what `test_evaluator.py` and `_compute_summary` access
- `Benchmarker._compute_summary()` accesses `r["cag"]["latency_seconds"]`, `r["cag"]["input_tokens"]`, `r["cag"]["judge_scores"]["total"]` — all present in `_build_entry` output

---

**Plan complete and saved to `docs/superpowers/plans/2026-06-25-production-overhaul.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** — Fresh subagent dispatched per task, you review between tasks, fast iteration with isolation

**2. Inline Execution** — Execute tasks sequentially in this session using `superpowers:executing-plans`

**Which approach?**
