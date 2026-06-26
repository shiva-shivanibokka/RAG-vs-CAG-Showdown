import logging
import os

from dotenv import load_dotenv

load_dotenv()

# OpenAI — text generation (gpt-4o-mini: ~$0.000002/request, $5 ≈ 2500 CAG requests)
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1024"))
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
API_ROOT_PATH: str = os.getenv("API_ROOT_PATH", "")
CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
