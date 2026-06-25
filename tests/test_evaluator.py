import json

import pytest

from src.benchmark.evaluator import DEFAULT_QUESTIONS, Benchmarker, LLMJudge

# ---------------------------------------------------------------------------
# LLMJudge._parse_judge_response
# ---------------------------------------------------------------------------


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
    raw = '```json\n{"correctness": 4, "completeness": 3, "coherence": 5, "groundedness": 4, "reasoning": "ok"}\n```'
    result = j._parse_judge_response(raw)
    assert result["correctness"] == 4


def test_parse_strips_bare_code_fences():
    j = make_judge()
    raw = '```\n{"correctness": 5, "completeness": 5, "coherence": 5, "groundedness": 5, "reasoning": "perfect"}\n```'
    result = j._parse_judge_response(raw)
    assert result["total"] == 5.0


def test_parse_raises_on_missing_field():
    j = make_judge()
    raw = '{"correctness": 4, "completeness": 3}'
    with pytest.raises(ValueError, match="Missing fields"):
        j._parse_judge_response(raw)


def test_parse_raises_on_invalid_json():
    j = make_judge()
    with pytest.raises(json.JSONDecodeError):
        j._parse_judge_response("not json at all")


# ---------------------------------------------------------------------------
# LLMJudge.score
# ---------------------------------------------------------------------------


def test_score_returns_zeros_on_error():
    from unittest.mock import MagicMock

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("connection refused")
    judge = LLMJudge(_client=mock_client, max_retries=1)
    result = judge.score("q", "a", ["concept"])
    assert result["total"] == 0
    assert "Judge error" in result["reasoning"]


def test_score_parses_valid_response():
    from unittest.mock import MagicMock

    raw = '{"correctness": 5, "completeness": 4, "coherence": 5, "groundedness": 4, "reasoning": "great"}'
    mock_choice = MagicMock()
    mock_choice.message.content = raw
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_resp
    judge = LLMJudge(_client=mock_client)
    result = judge.score("q", "a", ["c"])
    assert result["total"] == 4.5


# ---------------------------------------------------------------------------
# Benchmarker._compute_summary
# ---------------------------------------------------------------------------


def test_compute_summary_cag_wins():
    bench = Benchmarker.__new__(Benchmarker)
    results = [
        {
            "cag": {
                "latency_seconds": 1.0,
                "input_tokens": 100,
                "output_tokens": 50,
                "judge_scores": {"total": 5.0},
            },
            "rag": {
                "latency_seconds": 0.5,
                "input_tokens": 40,
                "output_tokens": 20,
                "judge_scores": {"total": 3.0},
            },
        },
        {
            "cag": {
                "latency_seconds": 2.0,
                "input_tokens": 200,
                "output_tokens": 80,
                "judge_scores": {"total": 4.0},
            },
            "rag": {
                "latency_seconds": 1.0,
                "input_tokens": 50,
                "output_tokens": 25,
                "judge_scores": {"total": 4.0},
            },
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
