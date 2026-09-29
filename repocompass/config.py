"""Settings loaded from environment variables (and a local `.env` file)."""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


@dataclass(frozen=True)
class Settings:
    github_token: str
    default_provider: str

    openai_api_key: str
    openai_model: str
    openai_base_url: str

    anthropic_api_key: str
    anthropic_model: str

    gemini_api_key: str
    gemini_model: str

    ollama_base_url: str
    ollama_model: str
    ollama_num_ctx: int

    frontend_origins: tuple[str, ...]
    cache_dir: Path


@lru_cache
def get_settings() -> Settings:
    return Settings(
        github_token=_env("GITHUB_TOKEN"),
        default_provider=_env("DEFAULT_LLM_PROVIDER", "ollama").lower(),
        openai_api_key=_env("OPENAI_API_KEY"),
        openai_model=_env("OPENAI_MODEL") or "gpt-5-mini",
        openai_base_url=_env("OPENAI_BASE_URL"),
        anthropic_api_key=_env("ANTHROPIC_API_KEY"),
        anthropic_model=_env("ANTHROPIC_MODEL") or "claude-opus-5-5",
        gemini_api_key=_env("GEMINI_API_KEY") or _env("GOOGLE_API_KEY"),
        gemini_model=_env("GEMINI_MODEL") or "gemini-2.5-flash",
        ollama_base_url=(_env("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/"),
        ollama_model=_env("OLLAMA_MODEL") or "qwen3:4b-instruct",
        ollama_num_ctx=int(_env("OLLAMA_NUM_CTX") or 8192),
        frontend_origins=tuple(
            origin.strip().rstrip("/")
            for origin in (_env("FRONTEND_ORIGINS") or "http://localhost:3000,http://127.0.0.1:3000").split(",")
            if origin.strip()
        ),
        cache_dir=PROJECT_ROOT / ".cache",
    )
