"""Application settings (env / .env)."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, SecretStr
from pydantic import AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


ProviderName = Literal["openai", "anthropic", "gemini"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ZREF_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API keys (also read unprefixed common names)
    openai_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY", "ZREF_OPENAI_API_KEY"),
    )
    anthropic_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("ANTHROPIC_API_KEY", "ZREF_ANTHROPIC_API_KEY"),
    )
    google_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("GOOGLE_API_KEY", "GEMINI_API_KEY", "ZREF_GOOGLE_API_KEY"),
    )

    default_provider: ProviderName = "openai"
    openai_model: str = "gpt-4o"
    anthropic_model: str = "claude-sonnet-4-20250514"
    gemini_model: str = "gemini-2.0-flash"

    max_prompt_tokens: int = 480
    tokenizer_model_id: str = "Qwen/Qwen3-4B"

    http_timeout_s: float = 120.0
    max_retries: int = 4
    cache_dir: str | None = Field(default=None, description="Disk cache for describe results")

    # API server
    api_key: SecretStr | None = Field(default=None, description="Optional Bearer for /describe")


def get_settings() -> Settings:
    return Settings()
