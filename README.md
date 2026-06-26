# CAG vs RAG Showdown ⚔️

> **Recruiter TL;DR**
> - Full-stack LLM benchmarking app that pits Context Augmented Generation against Retrieval Augmented Generation head-to-head on 10 AI/ML questions, scored by an LLM-as-judge in real time
> - Hardest engineering problem: eliminated all cloud embedding dependencies by running a local ONNX model inside Docker after every major free-tier LLM provider failed due to token/rate limits (Groq 12K TPM cap, Cloudflare 10K neurons/day, Gemini regional quota, Cerebras model-access errors, OpenRouter free-model discontinuation, Together AI billing wall)
> - In a live tournament run: CAG scored **4.95/5 avg** vs RAG's **3.73/5**, with multi-hop questions showing the widest gap (5/5 vs 1.25/5) — at the cost of 30% higher latency (5.03s vs 3.86s), consistent with CAG's larger prompt

[![CI](https://github.com/shiva-shivanibokka/RAG-vs-CAG-Showdown/actions/workflows/ci.yml/badge.svg)](https://github.com/shiva-shivanibokka/RAG-vs-CAG-Showdown/actions)
![Python](https://img.shields.io/badge/python-3.11-blue)

**Live demo** → [rag-vs-cag-showdown.vercel.app](https://rag-vs-cag-showdown.vercel.app/)

---

## What is CAG vs RAG?

| | CAG | RAG |
|---|---|---|
| Core idea | Load the **entire** knowledge base into the LLM's context window | **Retrieve** only the most relevant chunks at query time |
| Retrieval step | None | Vector similarity search (FAISS) |
| Multi-hop reasoning | Strong — all context always available | Weak — only retrieved chunks available |
| Hallucination risk | Lower — LLM can't invent what isn't there | Higher — retrieval gaps can mislead generation |
| Architecture complexity | Low — just the LLM | High — embeddings + vector DB + chunking |
| Scalability | Limited by context window | Millions of documents |
| Latency | Lower (especially with KV cache warm) | Higher (retrieval adds overhead) |
| Cost per query | Higher input tokens (full KB every time) | Lower input tokens (only retrieved chunks) |

**When CAG wins:** multi-hop questions, small-to-medium knowledge bases, when consistency matters more than scale.

**When RAG wins:** large corpora, latency-sensitive applications, cost-sensitive high-volume workloads.

---

## Features

- **⚔️ Single Challenge** — ask any question and see CAG and RAG answers side by side with latency and token counts
- **🏆 Full Tournament** — run all 10 benchmark questions in parallel; an LLM judge scores each answer on correctness, completeness, coherence, and groundedness (1–5 each)
- **🛡️ Battle HQ** — live backend health check showing model, embedding strategy, and knowledge base status
- **API key gate** — visitors supply their own LLM key; it goes browser → provider directly, the server never stores it
- **🔑 Change Key** button in the header to swap keys without a page refresh
- Per-question latency chart and score chart rendered after each tournament
- Retrieved chunk titles shown alongside every RAG answer

---

## Getting Started — Entering Your API Key

When you open the app you'll see an **API Key Gate** before the main interface. This is intentional — your key is sent directly from your browser to the LLM provider on every request. The server never stores it.

### Supported providers

| Provider | Works? | Notes |
|---|---|---|
| **OpenAI** (any tier) | ✅ | Recommended. No per-request token cap. Get key at platform.openai.com |
| **Anthropic** | ✅ | 200K context window. Get key at console.anthropic.com |
| **Google Gemini free** | ✅ | 1 million TPM — easily handles the 13,500-token CAG prompt. Get key at aistudio.google.com |
| **Groq free tier** | ⚠️ | Hard 12,000 TPM cap per minute. CAG needs 13,500 tokens → will fail. RAG-only still works. |
| Any provider with < 14K token per-request limit | ❌ | CAG will be rejected at the provider level |

> **Why 13,500 tokens?** CAG loads all 30 knowledge base topics into a single LLM call. That's the cost of the "no retrieval" approach — the provider must accept one large request.

### Cost estimate (OpenAI gpt-4o-mini rates)

| Action | Tokens | Approx. cost |
|---|---|---|
| Single Challenge (CAG + RAG) | ~17,000 | ~$0.003 |
| Full Tournament (10 questions + LLM judge) | ~185,000 | ~$0.036 |

$1 of OpenAI credit covers ~300 single challenges or ~27 full tournaments.

### Changing your key

A **🔑 Change Key** button appears in the top-right corner of the header on every page. Click it to clear your stored key and return to the entry screen. Keys are stored in `localStorage` and never leave your browser except as request headers to your chosen provider.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Vercel (Frontend)                  │
│   React + Vite + Tailwind CSS                        │
│   • API key gate (localStorage)                      │
│   • ⚔️ Challenge tab (single question)               │
│   • 🏆 Tournament tab (10 questions + LLM judge)     │
│   • 🛡️ Battle HQ tab (system health)                 │
└──────────────────┬──────────────────────────────────┘
                   │ HTTPS  (X-OpenAI-Key header)
┌──────────────────▼──────────────────────────────────┐
│                  Render (Backend)                    │
│   FastAPI + Python 3.11 + Docker                     │
│                                                      │
│   ┌─────────────────┐   ┌──────────────────────┐   │
│   │   CAG Engine    │   │     RAG Engine        │   │
│   │                 │   │                       │   │
│   │ Full KB in      │   │ fastembed (local ONNX)│   │
│   │ system prompt   │   │ → FAISS IndexFlatIP   │   │
│   │ (~13,500 tok)   │   │ → top-3 chunks        │   │
│   └────────┬────────┘   └──────────┬────────────┘  │
│            │                        │               │
│            └────────────┬───────────┘               │
│                         │                           │
│                  LLM API call                       │
│              (user's key, per-request)              │
└─────────────────────────────────────────────────────┘
```

### Key components

**CAG Engine** (`src/cag/engine.py`)
- Reads the full `knowledge_base/aiml_corpus.txt` at startup (~13,500 tokens)
- Builds a system prompt: preamble + entire knowledge base
- Each query: one LLM call with the full KB in context, no retrieval

**RAG Engine** (`src/rag/engine.py`)
- Loads pre-computed embeddings from `knowledge_base/embeddings_cache.npy` (30 × 384 float32, committed to git — no API call at startup)
- At query time: embeds the question locally using **fastembed** (BAAI/bge-small-en-v1.5 ONNX model) — zero API calls, zero rate limits
- FAISS `IndexFlatIP` cosine similarity → top-3 chunks retrieved
- One LLM call with retrieved context only (~2,000 tokens)

**LLM Judge** (`src/benchmark/evaluator.py`)
- Same LLM, third role: scores each answer on 4 dimensions (1–5 each)
- Correctness, Completeness, Coherence, Groundedness
- Runs in parallel with `asyncio.gather` for speed

---

## Benchmark Results

Results from a full 10-question tournament run (OpenAI gpt-4o-mini):

| Metric | CAG | RAG |
|---|---|---|
| Avg judge score | **4.95 / 5** | 3.73 / 5 |
| Avg latency | 5.03s | 3.86s |
| Wins | **5** | 0 |
| Ties | 5 | 5 |

**Where the gap was largest — multi-hop questions:**

| Question | CAG | RAG |
|---|---|---|
| Q05: How does tokenization affect CAG's context window? | 5/5 | 1.25/5 |
| Q06: CAG or RAG for a 50,000-word medical QA system? | 5/5 | 1.25/5 |
| Q07: Compare encoder/decoder architectures for RAG | 5/5 | 1.25/5 |

Multi-hop questions require synthesizing information across multiple topics simultaneously. CAG has all 30 topics in context; RAG retrieves top-3 chunks and misses the connections between them. This is the clearest demonstration of when each approach wins.

**The latency tradeoff is real:** CAG is ~30% slower on average because it sends ~13,500 tokens on every request. RAG sends ~2,000. If latency matters more than multi-hop accuracy, RAG wins that dimension.

---

## Knowledge Base

30 AI/ML topics (~13,500 tokens total), each a structured explanation designed to test both retrieval and full-context reasoning:

| # | Topic |
|---|-------|
| 1 | Transformer Architecture |
| 2 | RAG (Retrieval Augmented Generation) |
| 3 | CAG (Context Augmented Generation) |
| 4 | Large Language Models |
| 5 | Vector Databases & Embeddings |
| 6 | Hallucination in LLMs |
| 7 | Prompt Engineering |
| 8 | Fine-Tuning vs In-Context Learning |
| 9 | Evaluation Metrics for LLMs |
| 10 | Agentic AI & Tool Use |
| 11 | Attention Mechanisms & KV Cache |
| 12 | Neural Network Fundamentals |
| 13 | Tokenization |
| 14 | RLHF |
| 15 | Encoder / Decoder Architectures |
| 16 | Chunking Strategies for RAG |
| 17 | Mixture of Experts (MoE) |
| 18 | Constitutional AI & Safety |
| 19 | Scaling Laws & Emergent Abilities |
| 20 | Advanced RAG Techniques |
| 21 | Lost-in-the-Middle Problem |
| 22 | Position Encoding (RoPE, ALiBi) |
| 23 | Inference Optimization (vLLM) |
| 24 | Quantization & Compression |
| 25 | Production Deployment Trade-offs |
| 26 | When RAG Beats CAG |
| 27 | Embedding Model Selection & MTEB |
| 28 | Multi-Hop Reasoning |
| 29 | Faithfulness & Hallucination |
| 30 | Benchmark Evaluation Design |

---

## Benchmark Questions (Tournament)

| ID | Category | Question |
|----|----------|----------|
| Q01 | factual | What is the KV cache and how does it benefit CAG specifically? |
| Q02 | comparison | What are the main weaknesses of RAG compared to CAG? |
| Q03 | technical | Explain MHA vs MQA vs GQA |
| Q04 | factual | What is RLHF and what are its main alternatives? |
| Q05 | multi-hop | How does tokenization affect the context window available for CAG, and which tokenizer does LLaMA use? |
| Q06 | multi-hop | CAG or RAG for a medical QA system with 50,000 words? |
| Q07 | reasoning | Compare encoder-only, decoder-only, and encoder-decoder architectures for a RAG generator |
| Q08 | reasoning | Best chunking strategy for a technical manual, and why does CAG eliminate this concern? |
| Q09 | technical | Scaled dot-product attention formula and purpose of the scaling factor |
| Q10 | technical | How does MoE achieve better performance per compute unit vs dense models? |

---

## Challenges Faced During Development

Building this project involved navigating the constraints of every major free-tier LLM API. Here's what broke and why.

### 1. Cloudflare Workers AI — 10,000 neuron/day limit

The original plan used Cloudflare Workers AI for both embeddings and text generation. The problem: CAG's 13,331-token prompt consumed the entire 10,000 neuron daily budget in **3–4 requests**. The app was effectively unusable.

**Fix (partial):** Pre-computed all 30 topic embeddings locally using fastembed, saved as `knowledge_base/embeddings_cache.npy`, committed to git. Startup no longer calls CF at all. But CF was still being called at query time to embed the user's question — this continued to burn neurons.

**Final fix:** Replaced CF entirely with [fastembed](https://github.com/qdrant/fastembed) (BAAI/bge-small-en-v1.5 ONNX model). All embeddings — both knowledge base and user queries — now run locally inside the Docker container. No API, no rate limit, no daily quota. The model is pre-downloaded during the Docker build step so there's no cold-start delay.

### 2. Groq — TPM hard cap too low for CAG

Groq's free tier looked promising (fast inference, generous daily request limits), but the per-minute token limits are a hard ceiling per request:

- `llama-3.3-70b-versatile`: 12,000 TPM → CAG needs 13,331 → **rejected**
- `llama-3.1-8b-instant`: 6,000 TPM → even worse

The error was explicit: `TPM: Limit 12000, Requested 13333`. No workaround exists without paying for a higher tier. Groq works fine for RAG (small prompts ~2,000 tokens), but CAG is architecturally incompatible with Groq's free tier.

### 3. Google Gemini — quota = 0 (regional issue)

Gemini's free tier advertises 1 million TPM — theoretically perfect for CAG. In practice, both `gemini-2.0-flash` and `gemini-1.5-flash` returned `limit: 0` errors. Creating a new Google Cloud project and generating a fresh API key from Google AI Studio did not resolve it. This appeared to be a regional quota provisioning issue (India) affecting specific account types. Gemini *should* work for users in other regions.

### 4. Cerebras — model access errors

Cerebras offers fast inference on custom silicon with a free tier. The API is OpenAI-compatible. However, both `llama3.3-70b` and `llama3.1-8b` returned 404: "Model does not exist or you do not have access to it." The error wording suggests model-level access controls (possibly requiring Meta license acceptance in the Cerebras dashboard), but the dashboard showed no such prompts.

### 5. OpenRouter — free models discontinued mid-integration

OpenRouter aggregates many providers and marks some models as `:free`. This seemed like the ideal solution. In practice:

- `meta-llama/llama-3.1-8b-instruct:free` — removed from free tier
- `mistralai/mistral-7b-instruct:free` — removed from free tier
- `google/gemma-3-12b-it:free` — removed from free tier

The `:free` catalog changes without notice. By the time we switched to each model, it had been made paid-only. OpenRouter's paid models are very cheap, but require a credit card.

### 6. Together AI — free tier removed

Together AI historically gave $5 free credit on signup without a credit card. At time of integration, they now require billing information to create API keys, even for the initial free credit.

### 7. The actual solution — user-supplied API key

After exhausting free-tier options, the architecture was redesigned: **visitors bring their own API key**. This approach:

- Costs the project owner nothing regardless of traffic
- Lets any visitor use the provider they already have an account with
- Teaches visitors about provider token limits (a real CAG constraint)
- Makes the limitation itself part of the educational demo

The key is passed in an `X-OpenAI-Key` request header on every API call, used per-request to create an OpenAI-compatible client, and never logged or stored server-side.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS |
| Backend | FastAPI, Python 3.11, Uvicorn |
| Deployment | Render (backend, Docker free tier), Vercel (frontend) |
| Embeddings | fastembed — BAAI/bge-small-en-v1.5 (local ONNX, no API) |
| Vector search | FAISS `IndexFlatIP` (in-memory cosine similarity) |
| LLM | User-supplied key — OpenAI, Anthropic, Gemini, or compatible |
| Embedding cache | NumPy `.npy` file committed to git (30 × 384 float32) |

---

## Skills Demonstrated

| Competency | How it appears in this project |
|---|---|
| LLM application development & RAG | CAG and RAG engines built from scratch; LLM-as-judge evaluation loop |
| RESTful API design | Five typed FastAPI endpoints (`/health`, `/query/cag`, `/query/rag`, `/query/both`, `/benchmark`) with Pydantic request/response models |
| System design & architecture | Documented CAG vs RAG tradeoff reasoning; fastembed-over-API decision; embeddings-cache-in-git strategy |
| Asynchronous & concurrent systems | `asyncio.gather` runs CAG, RAG, and judge calls in parallel during tournament; async engine methods throughout |
| Containerization & Docker | Multi-stage Dockerfile with fastembed ONNX model pre-downloaded at build time to eliminate cold-start latency |
| CI/CD pipeline | GitHub Actions: ruff lint + pytest on every push and PR (`pip install -e ".[dev]"`, `--cov` report) |
| Cloud deployment | Render (Docker-based backend) + Vercel (frontend with SPA rewrite rule) |
| Observability & monitoring | Structured logging (`logging` module throughout), `/health` endpoint reporting model/KB/embedding status |

---

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend

```bash
# Install all dependencies including dev tools (linting, testing)
pip install -e ".[dev]"

# Set your API key (used as fallback if no key sent in header)
# Windows
set OPENAI_API_KEY=sk-...
# macOS / Linux
export OPENAI_API_KEY=sk-...

# Start the API server
uvicorn api.app:app --reload
# → http://localhost:8000
# → API docs at http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install

# Create .env.local
echo "VITE_API_URL=http://localhost:8000" > .env.local

npm run dev
# → http://localhost:5173
```

### Regenerating the embeddings cache (optional)

The cache (`knowledge_base/embeddings_cache.npy`) is already committed. Only needed if you change the knowledge base:

```bash
python scripts/precompute_embeddings.py
# Saves 30 × 384 float32 embeddings to knowledge_base/embeddings_cache.npy
```

### Running tests

```bash
pytest tests/ -v --cov=src --cov=api --cov-report=term-missing
# 38 tests covering CAG engine, RAG engine, chunking, evaluator, and API routes
```

---

## Deployment

### Backend — Render

1. Connect your GitHub repo on [render.com](https://render.com)
2. Service type: **Web Service**, environment: **Docker**
3. Environment variables (set in Render dashboard):
   - `OPENAI_API_KEY` — optional server-side fallback; leave empty to require user-supplied keys
   - `CORS_ORIGINS` — set to your Vercel frontend URL (e.g. `https://rag-vs-cag-showdown.vercel.app`)
4. The Docker build pre-downloads the fastembed ONNX model so cold starts are fast

### Frontend — Vercel

1. Import the repo on [vercel.com](https://vercel.com)
2. Framework: **Vite**
3. Root directory: `frontend`
4. Environment variable: `VITE_API_URL` = your Render backend URL (e.g. `https://your-app.onrender.com`)

> **Note:** Render free tier spins down after 15 minutes of inactivity. First request after a cold start may take ~30 seconds. The Battle HQ tab shows backend status.

---

## Project Structure

```
CAG-vs-RAG-Showdown/
├── api/
│   └── app.py                         # FastAPI routes
├── src/
│   ├── cag/engine.py                  # CAGEngine — full KB in context
│   ├── rag/engine.py                  # RAGEngine — fastembed + FAISS + retrieval
│   ├── benchmark/evaluator.py         # Benchmarker + LLMJudge
│   └── config.py                      # Environment variable loading
├── frontend/
│   └── src/
│       ├── App.jsx                    # Tab router + API key gate
│       ├── api.js                     # Fetch wrapper (passes X-OpenAI-Key header)
│       └── components/
│           ├── ApiKeyGate.jsx         # Key entry screen with cost + provider warnings
│           ├── Header.jsx             # Battle arena header + Change Key button
│           ├── QueryPanel.jsx         # Single question challenge UI
│           ├── BenchmarkPanel.jsx     # Full tournament UI
│           ├── ResultsView.jsx        # Tournament scorecard
│           └── HealthStatus.jsx       # Backend status (Battle HQ)
├── knowledge_base/
│   ├── aiml_corpus.txt                # 30 AI/ML topics (~13,500 tokens)
│   └── embeddings_cache.npy           # Pre-computed 30×384 float32 embeddings (git-tracked)
├── scripts/
│   └── precompute_embeddings.py       # Local script to regenerate embeddings_cache.npy
├── tests/                             # 38 pytest tests
├── Dockerfile                         # Python 3.11-slim + fastembed model pre-download
├── render.yaml                        # Render deployment config
└── requirements.txt
```

---

## Key Design Decisions

**Same LLM for both engines and the judge** — the comparison is fair because the only variable is retrieval strategy, not model quality.

**fastembed over API-based embeddings** — eliminates all embedding rate limits, costs, and daily quotas. The ONNX model runs inside the container. Pre-downloading in the Dockerfile means zero cold-start penalty.

**Embeddings committed to git** — the 30-topic embedding cache (46KB numpy file) is committed so Render never calls any embedding API at startup. Regenerate locally if the knowledge base changes.

**User-supplied API key** — after exhausting every free-tier LLM option (see Challenges section), the architecture was redesigned so visitors use their own keys. This makes the CAG token constraint tangible and educational: visitors learn exactly why provider selection matters for CAG.

**FAISS IndexFlatIP in-memory** — no vector database server, no persistence complexity. For 30 chunks the exhaustive search is instantaneous. Scales cleanly to a few thousand chunks before latency becomes a concern.

**Topic-based chunking** — chunks aligned to document structure (one chunk per topic) rather than arbitrary token windows. This improves retrieval precision because each chunk is semantically coherent.

**LLM-as-judge** — avoids expensive human annotation while providing structured, reproducible quality scores. The judge uses the same model as the engines but in a distinct role, scoring each answer independently without comparing them directly.

---

## Roadmap

- **Upload your own knowledge base** — let visitors paste or upload their own documents and run CAG vs RAG on their own content. This turns the app from a fixed demo into a general-purpose evaluation tool, and makes the context-window constraint tangible for any domain.
- **Streaming responses** — stream tokens to the UI as they arrive instead of waiting for the full response. CAG's latency disadvantage (~30% slower in the sample tournament) is largely a perception problem at full-document scale; streaming would make it feel much faster.
- **Advanced RAG techniques** — add re-ranking (Cohere Rerank or a cross-encoder), HyDE (hypothetical document embeddings), or multi-query retrieval to close the accuracy gap. The current RAG pipeline is intentionally simple to make the comparison fair to CAG; a "RAG Pro" mode would show how far retrieval quality can be pushed.
