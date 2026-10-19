"""Konfigurasi aplikasi. Semua rahasia dibaca dari environment (NFR-08, FR-35)."""
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _list(name: str, default: str) -> list[str]:
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = "VAME - Virtual Asisten Mentor Edukasi"
    api_prefix: str = "/api/v1"  # FR-43

    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./vame.db")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-ganti-di-produksi")
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

    ai_provider: str = os.getenv("AI_PROVIDER", "mock").lower()
    ai_model: str = os.getenv("AI_MODEL", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    local_llm_url: str = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/v1")
    local_llm_api_key: str = os.getenv("LOCAL_LLM_API_KEY", "")
    ai_timeout: float = float(os.getenv("AI_TIMEOUT_SECONDS", "30"))
    ai_max_retries: int = int(os.getenv("AI_MAX_RETRIES", "2"))
    ai_backoff_base: float = float(os.getenv("AI_BACKOFF_BASE", "0.5"))

    pass_threshold: int = int(os.getenv("PASS_THRESHOLD", "70"))  # BR-04 (default)
    min_mentor_interactions: int = int(os.getenv("MIN_MENTOR_INTERACTIONS", "1"))
    rate_limit_ai_per_minute: int = int(os.getenv("RATE_LIMIT_AI_PER_MINUTE", "20"))  # NFR-11
    cors_origins: list[str] = field(
        default_factory=lambda: _list("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    )

    # Penyimpanan berkas (Issue #10). Default lokal filesystem; siap diganti S3.
    storage_backend: str = os.getenv("STORAGE_BACKEND", "local")
    storage_root: str = os.getenv("STORAGE_ROOT", "storage")


settings = Settings()
