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
    first_end = set(chunks[0]["text"].split()[-5:])
    second_start = set(chunks[1]["text"].split()[:5])
    assert first_end & second_start
