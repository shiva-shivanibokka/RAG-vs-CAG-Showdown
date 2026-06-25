from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.cag.engine import CAGEngine


def test_query_returns_correct_keys(tmp_knowledge_base, mock_cf_client):
    engine = CAGEngine(tmp_knowledge_base, _client=mock_cf_client)
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


def test_query_answer_text(tmp_knowledge_base, mock_cf_client):
    engine = CAGEngine(tmp_knowledge_base, _client=mock_cf_client)
    result = engine.query("What is KV cache?")
    assert result["answer"] == "This is a test answer."


def test_query_method_is_cag(tmp_knowledge_base, mock_cf_client):
    engine = CAGEngine(tmp_knowledge_base, _client=mock_cf_client)
    result = engine.query("test")
    assert result["method"] == "CAG"
    assert result["retrieved_chunks"] is None


def test_query_token_counts(tmp_knowledge_base, mock_cf_client):
    engine = CAGEngine(tmp_knowledge_base, _client=mock_cf_client)
    result = engine.query("test")
    assert result["input_tokens"] == 150
    assert result["output_tokens"] == 40


def test_query_latency_is_positive_float(tmp_knowledge_base, mock_cf_client):
    engine = CAGEngine(tmp_knowledge_base, _client=mock_cf_client)
    result = engine.query("test")
    assert isinstance(result["latency_seconds"], float)
    assert result["latency_seconds"] >= 0.0


def test_missing_knowledge_base_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        CAGEngine(tmp_path / "nonexistent.txt")


def test_retry_on_failure(tmp_knowledge_base):
    choice = MagicMock()
    choice.message.content = "ok"
    success_response = MagicMock()
    success_response.choices = [choice]
    success_response.usage.prompt_tokens = 10
    success_response.usage.completion_tokens = 5

    client = MagicMock()
    client.chat.completions.create.side_effect = [
        RuntimeError("connection refused"),
        success_response,
    ]
    engine = CAGEngine(tmp_knowledge_base, max_retries=3, _client=client)
    result = engine.query("test")
    assert result["answer"] == "ok"
    assert client.chat.completions.create.call_count == 2


def test_exhausted_retries_raises(tmp_knowledge_base):
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("always fails")
    engine = CAGEngine(tmp_knowledge_base, max_retries=2, _client=client)
    with pytest.raises(RuntimeError):
        engine.query("test")


@pytest.mark.asyncio
async def test_query_async_returns_correct_keys(tmp_knowledge_base):
    choice = MagicMock()
    choice.message.content = "async answer"
    async_response = MagicMock()
    async_response.choices = [choice]
    async_response.usage.prompt_tokens = 100
    async_response.usage.completion_tokens = 30

    async_client = MagicMock()
    async_client.chat.completions.create = AsyncMock(return_value=async_response)

    with patch("src.cag.engine.AsyncOpenAI", return_value=async_client):
        engine = CAGEngine(tmp_knowledge_base)
        result = await engine.query_async("test")

    assert result["answer"] == "async answer"
    assert result["method"] == "CAG"
