"""Application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

def _resolve_env_files() -> tuple[str, ...]:
    """Prefer monorepo root `.env`, then `apps/api/.env`, then cwd `.env`."""
    here = Path(__file__).resolve()
    candidates = [
        here.parents[4] / ".env",  # d:/AI WORKSPACE/.env
        here.parents[2] / ".env",  # apps/api/.env
        Path.cwd() / ".env",
    ]
    found: list[str] = []
    for path in candidates:
        if path.is_file() and str(path) not in found:
            found.append(str(path))
    return tuple(found) if found else (str(Path.cwd() / ".env"),)


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=_resolve_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"

    jwt_secret: str = "change-me-to-a-long-random-string-at-least-32-chars"
    access_token_ttl_seconds: int = 900
    refresh_token_ttl_seconds: int = 604800

    database_url: str = "postgresql+psycopg://aiworkspace:aiworkspace@localhost:5432/aiworkspace"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "document_chunks"

    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "tinyllama"
    ollama_embed_model: str = "nomic-embed-text"

    default_model_family: str = "llama"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_chat_model: str = "gpt-4o-mini"
    mistral_api_key: str = ""
    mistral_base_url: str = "https://api.mistral.ai/v1"
    mistral_chat_model: str = "mistral-small-latest"
    huggingface_api_key: str = ""
    huggingface_model: str = "meta-llama/Meta-Llama-3-8B-Instruct"

    upload_dir: str = "./uploads"
    max_upload_mb: int = 20

    rate_limit_enabled: bool = True
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    rate_limit_auth_requests: int = 30

    ollama_whisper_model: str = ""
    enable_api_docs: bool = True

    require_email_verification: bool = False
    app_base_url: str = "http://localhost:3000"
    api_public_url: str = "http://localhost:8000"
    mail_from: str = "noreply@aiworkspace.local"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    hybrid_search_enabled: bool = True
    ocr_enabled: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        # Local/dev convenience: browsers often hit 127.0.0.1 or LAN IP instead of localhost
        if self.environment in {"development", "test"}:
            extras = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3001",
            ]
            for origin in extras:
                if origin not in origins:
                    origins.append(origin)
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
