FROM python:3.11-slim

WORKDIR /app

# curl for healthcheck probes; no gcc/g++ needed — fastembed and faiss-cpu ship pre-built wheels
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Pre-download ONNX embedding model (~25 MB) so cold starts don't re-download it
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5')"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
