"""
CAG vs RAG Showdown — FastAPI REST layer
=========================================
Serves the CAG and RAG engines as HTTP endpoints.
Run with: uvicorn api.app:app --reload
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from src.benchmark.evaluator import Benchmarker
from src.cag.engine import CAGEngine
from src.config import API_ROOT_PATH, CF_MODEL, CORS_ORIGINS, RAG_TOP_K
from src.rag.engine import RAGEngine

logger = logging.getLogger(__name__)

KNOWLEDGE_BASE = Path(__file__).parent.parent / "knowledge_base" / "aiml_corpus.txt"

_cag: CAGEngine | None = None
_rag: RAGEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _cag, _rag
    logger.info("Loading engines on startup (model=%s)...", CF_MODEL)
    _cag = CAGEngine(KNOWLEDGE_BASE, model=CF_MODEL)
    _rag = RAGEngine(KNOWLEDGE_BASE, model=CF_MODEL, top_k=RAG_TOP_K)
    logger.info("Engines ready.")
    yield
    _cag = None
    _rag = None


app = FastAPI(
    title="CAG vs RAG Showdown API",
    description="Benchmark and compare Context Augmented Generation vs Retrieval Augmented Generation",
    version="1.0.0",
    lifespan=lifespan,
    root_path=API_ROOT_PATH,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in CORS_ORIGINS.split(",") if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ---------------------------------------------------------------------------
# Dependency injection (enables test overrides)
# ---------------------------------------------------------------------------


def get_cag() -> CAGEngine:
    if _cag is None:
        raise HTTPException(status_code=503, detail="CAG engine not initialized")
    return _cag


def get_rag() -> RAGEngine:
    if _rag is None:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    return _rag


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class QueryRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("question must not be empty")
        return v.strip()


class BenchmarkRequest(BaseModel):
    use_judge: bool = True


class RetrievedChunk(BaseModel):
    title: str
    similarity_score: float


class QueryResponse(BaseModel):
    answer: str
    latency_seconds: float
    input_tokens: int
    output_tokens: int
    model: str
    method: str
    context_used: str
    retrieved_chunks: list[RetrievedChunk] | None = None
    retrieval_latency_seconds: float | None = None
    generation_latency_seconds: float | None = None


class BothQueryResponse(BaseModel):
    cag: QueryResponse
    rag: QueryResponse


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
def health():
    return {"status": "ok", "model": CF_MODEL, "provider": "Cloudflare Workers AI"}


@app.post("/query/cag", response_model=QueryResponse)
def query_cag(req: QueryRequest, cag: Annotated[CAGEngine, Depends(get_cag)]):
    try:
        return cag.query(req.question)
    except Exception as exc:
        logger.error("CAG query failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/query/rag", response_model=QueryResponse)
def query_rag(req: QueryRequest, rag: Annotated[RAGEngine, Depends(get_rag)]):
    try:
        return rag.query(req.question)
    except Exception as exc:
        logger.error("RAG query failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/query/both", response_model=BothQueryResponse)
def query_both(
    req: QueryRequest,
    cag: Annotated[CAGEngine, Depends(get_cag)],
    rag: Annotated[RAGEngine, Depends(get_rag)],
):
    try:
        return {"cag": cag.query(req.question), "rag": rag.query(req.question)}
    except Exception as exc:
        logger.error("Dual query failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/benchmark")
async def run_benchmark(
    req: BenchmarkRequest,
    cag: Annotated[CAGEngine, Depends(get_cag)],
    rag: Annotated[RAGEngine, Depends(get_rag)],
):
    try:
        bench = Benchmarker(
            cag_engine=cag,
            rag_engine=rag,
            use_judge=req.use_judge,
            results_dir=Path(__file__).parent.parent / "results",
        )
        return await bench.run_async(verbose=False)
    except Exception as exc:
        logger.error("Benchmark failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
