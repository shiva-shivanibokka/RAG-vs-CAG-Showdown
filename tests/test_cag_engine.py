from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.cag.engine import CAGEngine


def test_query_returns_correct_keys(tmp_knowledge_base, mock_ollama_client):
    engine = CAGEngine(tmp_knowledge_base, _client=mock_ollama_client)
    result = engine.query("What is KV cache?")

    assert set(result.keys()) == {
        "answer",
        "latency_seconds",
        "input_tokens",
        "output_tokens",
        "model",
        "method",
        "context_used",
        "retrieved_chunks",
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
    success_response = MagicMock()
    success_response.message.content = "ok"
    success_response.prompt_eval_count = 10
    success_response.eval_count = 5

    fail_then_succeed = MagicMock(
        side_effect=[RuntimeError("connection refused"), success_response]
    )
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
