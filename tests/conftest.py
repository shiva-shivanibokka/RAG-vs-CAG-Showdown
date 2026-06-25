from pathlib import Path
from unittest.mock import MagicMock

import pytest

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
