from unittest.mock import MagicMock

import pytest
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
def client():
    mock_cag = MagicMock()
    mock_cag.query.return_value = MOCK_CAG_RESULT

    mock_rag = MagicMock()
    mock_rag.query.return_value = MOCK_RAG_RESULT

    from api.app import app, get_cag, get_rag

    app.dependency_overrides[get_cag] = lambda: mock_cag
    app.dependency_overrides[get_rag] = lambda: mock_rag

    yield TestClient(app)

    app.dependency_overrides.clear()


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
