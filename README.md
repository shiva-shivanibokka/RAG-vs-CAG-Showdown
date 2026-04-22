# CAG vs RAG Showdown

A modular benchmarking framework that compares **Context Augmented Generation (CAG)** and **Retrieval Augmented Generation (RAG)** head-to-head on accuracy, latency, and cost — using the Anthropic Claude API and an AI/ML concepts knowledge base.

---

## What is CAG?

**Context Augmented Generation** eliminates the retrieval step entirely by loading the full knowledge base into the LLM's context window. Modern LLMs (Claude: 200K tokens, Gemini: 1M tokens) make this feasible for small-to-medium corpora.

| | RAG | CAG |
|---|---|---|
| Retrieval step | Yes (vector DB + ANN search) | None |
| Multi-hop reasoning | Weak (single retrieval pass) | Strong (full context always available) |
| Architecture complexity | High (embeddings + vector DB) | Low (just the LLM) |
| Scalability | Millions of documents | Limited by context window |
| Latency per query | Higher (retrieval overhead) | Lower (especially with KV cache) |
| Chunking required | Yes (major design decision) | No |

---

## Project Structure

```
CAG-vs-RAG-Showdown/
├── main.py                        # CLI entrypoint
├── requirements.txt
├── knowledge_base/
│   └── aiml_corpus.txt            # AI/ML knowledge base (~15 topics)
├── src/
│   ├── cag/
│   │   └── engine.py              # CAGEngine: full context load + Claude API
│   ├── rag/
│   │   └── engine.py              # RAGEngine: FAISS + sentence-transformers + Claude API
│   └── benchmark/
│       └── evaluator.py           # Benchmarker + LLM-as-judge scorer
└── results/                       # Auto-generated JSON + CSV benchmark results
```

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set your Anthropic API key
```bash
# Windows
set ANTHROPIC_API_KEY=your_key_here

# Unix / macOS
export ANTHROPIC_API_KEY=your_key_here
```

---

## Usage

### Run the full benchmark (10 questions, LLM judge scoring)
```bash
python main.py benchmark
```

### Run benchmark without judge scoring (faster, cheaper)
```bash
python main.py benchmark --no-judge
```

### Ask a single question to both engines side by side
```bash
python main.py ask both "What is the KV cache and how does CAG exploit it?"
```

### Ask a single question to CAG only
```bash
python main.py ask cag "Explain multi-head attention."
```

### Interactive chat session
```bash
python main.py chat cag
python main.py chat rag
```

### Use a different model or RAG top-k
```bash
python main.py benchmark --model claude-3-5-sonnet-20241022 --top-k 5
```

---

## How It Works

### CAG Engine (`src/cag/engine.py`)
1. Loads the full knowledge base at startup
2. Embeds it in the Claude system prompt
3. Each query: only the question is sent — no retrieval

### RAG Engine (`src/rag/engine.py`)
1. **Indexing** (one-time): Splits corpus into topic-based chunks → embeds with `all-MiniLM-L6-v2` → stores in FAISS
2. **Query**: Embeds question → cosine similarity search → top-k chunks → Claude generates from retrieved context

### Benchmarker (`src/benchmark/evaluator.py`)
- Runs 10 predefined questions across 4 categories: factual, comparison, multi-hop, technical
- Measures: latency, input/output tokens, estimated USD cost per question
- **LLM-as-judge**: Uses Claude to score each answer on correctness, completeness, coherence, and groundedness (1–5 scale)
- Saves results to `results/benchmark_<timestamp>.json` and `.csv`

---

## Benchmark Questions

| ID | Category | Question (truncated) |
|----|----------|----------------------|
| Q01 | factual | What is the KV cache and how does it benefit CAG? |
| Q02 | comparison | What are the main weaknesses of RAG compared to CAG? |
| Q03 | technical | Explain MHA vs MQA vs GQA |
| Q04 | factual | What is RLHF and its alternatives? |
| Q05 | multi_hop | How does tokenization affect CAG context window limits? |
| Q06 | multi_hop | CAG or RAG for a medical QA system with 50K words? |
| Q07 | reasoning | Compare encoder/decoder architectures for RAG generators |
| Q08 | reasoning | Best chunking strategy vs why CAG eliminates it |
| Q09 | technical | Scaled dot-product attention formula and scaling factor |
| Q10 | technical | How MoE achieves better perf per compute unit |

---

## Adding Your Own Knowledge Base

Replace `knowledge_base/aiml_corpus.txt` with your own plain-text file. Use the topic separator format for best RAG chunking:

```
================================================================================
TOPIC: Your Topic Name
================================================================================
Your content here...

```

Or pass any plain-text file — the RAG engine falls back to fixed-size chunking if no topic markers are found.

---

## Key Design Decisions

- **Same LLM for both**: Claude is used for both CAG and RAG generation, making the comparison fair
- **Open-source embeddings**: `all-MiniLM-L6-v2` (no OpenAI API needed for RAG embedding)
- **FAISS in-memory**: No vector database server required
- **Topic-based chunking**: Semantic chunks aligned to document structure rather than arbitrary token windows
- **LLM-as-judge**: Avoids expensive human annotation while providing meaningful quality scores

---

## Results Interpretation

After running, check `results/benchmark_<timestamp>.csv` for a full row-by-row comparison. Key things to look for:

- **Multi-hop questions (Q05, Q06)**: CAG typically wins here — all context is available simultaneously
- **Input token count**: CAG sends the full knowledge base every time; RAG sends only retrieved chunks
- **Cost**: For large knowledge bases, RAG is cheaper per query; for small bases with many queries, KV cache makes CAG competitive
- **Retrieval score**: Check which chunks RAG retrieved — misses reveal why RAG fails on certain questions

---

## Requirements

- Python 3.11+
- `anthropic` >= 0.40.0
- `faiss-cpu` >= 1.7.4
- `sentence-transformers` >= 3.0.0
- `numpy` >= 1.26.0
