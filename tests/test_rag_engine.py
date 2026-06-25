from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from src.rag.engine import RAGEngine


def test_query_returns_correct_keys(tmp_knowledge_base, mock_cf_client):
    with patch("src.rag.engine.SentenceTransformer") as mock_st:
        mock_st.return_value.encode.return_value = np.random.rand(3, 384).astype("float32")
        engine = RAGEngine(tmp_knowledge_base, _client=mock_cf_client)
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


def test_query_method_is_rag(tmp_knowledge_base, mock_cf_client):
    with patch("src.rag.engine.SentenceTransformer") as mock_st:
        mock_st.return_value.encode.return_value = np.random.rand(3, 384).astype("float32")
        engine = RAGEngine(tmp_knowledge_base, _client=mock_cf_client)
        result = engine.query("test")

    assert result["method"] == "RAG"
    assert isinstance(result["retrieved_chunks"], list)


def test_missing_knowledge_base_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        RAGEngine(tmp_path / "nonexistent.txt")


def test_falls_back_to_fixed_chunking_when_no_topics(tmp_path, mock_cf_client):
    kb = tmp_path / "plain.txt"
    kb.write_text("No topic markers here. Just plain text with many words. " * 50)
    with patch("src.rag.engine.SentenceTransformer") as mock_st:
        mock_st.return_value.encode.return_value = np.random.rand(1, 384).astype("float32")
        engine = RAGEngine(kb, _client=mock_cf_client)
    assert len(engine.chunks) > 0


@pytest.mark.asyncio
async def test_query_async_returns_correct_keys(tmp_knowledge_base):
    choice = MagicMock()
    choice.message.content = "async RAG answer"
    async_response = MagicMock()
    async_response.choices = [choice]
    async_response.usage.prompt_tokens = 120
    async_response.usage.completion_tokens = 45

    async_client = MagicMock()
    async_client.chat.completions.create = AsyncMock(return_value=async_response)

    with (
        patch("src.rag.engine.SentenceTransformer") as mock_st,
        patch("src.rag.engine.AsyncOpenAI", return_value=async_client),
    ):
        mock_st.return_value.encode.return_value = np.random.rand(3, 384).astype("float32")
        engine = RAGEngine(tmp_knowledge_base)
        result = await engine.query_async("What is KV cache?")

    assert result["answer"] == "async RAG answer"
    assert result["method"] == "RAG"
    assert "retrieved_chunks" in result
    assert "retrieval_latency_seconds" in result
