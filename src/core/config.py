"""
Valura AI — Core Configuration Module.

Centralized configuration using Pydantic Settings.
All env variables are loaded and validated here.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr


class Settings(BaseSettings):
    """Application-wide settings loaded from environment / .env file."""

    # ── Groq LLM ──────────────────────────────────────────────
    groq_api_key: SecretStr = Field(default="", description="Groq API key")
    groq_model: str = Field(default="llama-3.3-70b-versatile", description="Primary Groq model")
    groq_fast_model: str = Field(default="llama-3.1-8b-instant", description="Fast/cheap Groq model")
    groq_temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    groq_max_tokens: int = Field(default=4096, ge=256, le=32768)

    # ── Server ────────────────────────────────────────────────
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    debug: bool = Field(default=False)

    # ── Database ──────────────────────────────────────────────
    database_url: str = Field(default="sqlite+aiosqlite:///./valura.db")
    db_path: str = Field(default="valura.db")

    # ── Optional Data Sources ─────────────────────────────────
    alpha_vantage_api_key: SecretStr = Field(default="")
    finnhub_api_key: SecretStr = Field(default="")
    polygon_api_key: SecretStr = Field(default="")
    tavily_api_key: SecretStr = Field(default="")

    # ── Frontend ──────────────────────────────────────────────
    backend_url: str = Field(default="http://localhost:8000")

    # ── Operational ───────────────────────────────────────────
    log_level: str = Field(default="INFO")
    request_timeout: int = Field(default=60, description="LLM request timeout in seconds")
    max_retries: int = Field(default=3)
    memory_window: int = Field(default=20, description="Number of messages to keep in context")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton settings accessor with caching."""
    return Settings()


# ── Convenience Paths ─────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_ROOT = Path(__file__).resolve().parent.parent
