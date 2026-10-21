"""Central configuration (reads environment variables / .env)."""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BASE_DIR.parent
load_dotenv(BASE_DIR / ".env")


def _bool(name: str, default: str) -> bool:
    return os.getenv(name, default).lower() in ("1", "true", "yes")


class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'rephraseai.db'}")
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))

    MODEL_NAME = os.getenv("MODEL_NAME", "google/flan-t5-base")
    FINETUNED_MODEL_DIR = Path(os.getenv("FINETUNED_MODEL_DIR", str(PROJECT_DIR / "models" / "flan-t5-paraphrase")))
    if not FINETUNED_MODEL_DIR.is_absolute():
        FINETUNED_MODEL_DIR = (BASE_DIR / FINETUNED_MODEL_DIR).resolve()
    DEVICE = os.getenv("DEVICE", "auto")

    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "distilgpt2")
    BERTSCORE_MODEL = os.getenv("BERTSCORE_MODEL", "distilbert-base-uncased")
    ENABLE_BERTSCORE = _bool("ENABLE_BERTSCORE", "true")
    WARMUP_ON_STARTUP = _bool("WARMUP_ON_STARTUP", "false")

    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]
    COMPARISON_FILE = PROJECT_DIR / "docs" / "results" / "comparison.json"


settings = Settings()
