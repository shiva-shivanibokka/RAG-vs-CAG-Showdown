import logging
import os

from dotenv import load_dotenv

load_dotenv()

# Cerebras — text generation (free tier: 60K TPM for 8B, 30K TPM for 70B)
CEREBRAS_API_KEY: str = os.getenv("CEREBRAS_API_KEY", "")
CEREBRAS_MODEL: str = os.getenv("CEREBRAS_MODEL", "llama-3.3-70b")
CEREBRAS_BASE_URL: str = "https://api.cerebras.ai/v1"

# Cloudflare Workers AI — embeddings only
CF_ACCOUNT_ID: str = os.getenv("CF_ACCOUNT_ID", "")
CF_API_TOKEN: str = os.getenv("CF_API_TOKEN", "")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "@cf/baai/bge-small-en-v1.5")

RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "3"))
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1024"))
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
API_ROOT_PATH: str = os.getenv("API_ROOT_PATH", "")
CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
