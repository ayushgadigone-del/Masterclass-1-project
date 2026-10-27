"""
config.py — environment-driven settings for Legal Rights Navigator backend.

Reads from environment variables (or .env file via python-dotenv).
The LLM_PROVIDER variable switches between Ollama (free, local) and
OpenAI (paid, cloud) without any code changes.
"""
from __future__ import annotations

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    app_env: str = "development"
    cors_origins: str = "http://localhost:3000"

    # ── LLM provider switch ───────────────────────────────────────────────────
    llm_provider: str = "ollama"          # "ollama" | "openai"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"

    # OpenAI (only used when llm_provider == "openai")
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # ── MCP statute server ────────────────────────────────────────────────────
    mcp_server_path: str = "../mcp-statute-server/server.py"

    # ── Settlement ────────────────────────────────────────────────────────────
    settlement_secret_key: str = "change-me-in-production"
    settlement_base_url: str = "http://localhost:3000/settlement"

    # ── Storage ───────────────────────────────────────────────────────────────
    data_dir: str = "./data"
    pdf_dir: str = "./data/pdfs"

    # ── Database ──────────────────────────────────────────────────────────────
    # dev:  sqlite:///./data/legal_navigator.db  (default, zero-config)
    # prod: postgresql+psycopg2://user:pass@host/dbname
    database_url: str = "sqlite:///./data/legal_navigator.db"

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        if v not in ("ollama", "openai"):
            raise ValueError("LLM_PROVIDER must be 'ollama' or 'openai'")
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    def ensure_dirs(self) -> None:
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.pdf_dir).mkdir(parents=True, exist_ok=True)


# Module-level singleton — import and use directly
settings = Settings()
