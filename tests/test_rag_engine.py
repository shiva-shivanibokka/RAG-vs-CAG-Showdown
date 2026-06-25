from unittest.mock import patch

import numpy as np
import pytest

from src.rag.engine import RAGEngine


def test_query_returns_correct_keys(tmp_knowledge_base, mock_ollama_client):
    with patch("src.rag.engine.SentenceTransformer") as mock_st:
        mock_st.return_value.encode.return_value = np.random.rand(3, 384).astype("float32")
        engine = RAGEngine(tmp_knowledge_base, _client=mock_ollama_client)
        mock_ollama_client.chat.return_value.message.content = "RAG answer"
        mock_ollama_client.chat.return_value.prompt_eval_count = 80
        mock_ollama_client.chat.return_value.eval_count = 30
        result = engine.query("What is KV cache?")

    assert set(result.keys()) == {
        "answer",
        "latency_seconds",
        "retrieval_latency_seconds",
        "generation_latency_seconds",
        "input_tokens",
        "output_tokens",
        "model",
        "method",
        "context_used",
        "retrieved_chunks",
    }


def test_query_method_is_rag(tmp_knowledge_base, mock_ollama_client):
    with patch("src.rag.engine.SentenceTransformer") as mock_st:
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
        mock_st.return_value.encode.return_value = np.random.rand(1, 384).astype("float32")
        engine = RAGEngine(kb, _client=mock_ollama_client)
    assert len(engine.chunks) > 0
