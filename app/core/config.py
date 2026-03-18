from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True, slots=True)
class Settings:
    max_file_size_mb: int
    virtual_max_lines_per_page: int
    virtual_max_chars_per_page: int
    remote_fetch_timeout_sec: int
    openai_api_key: str | None
    swagger_username: str | None
    swagger_password: str | None
    openai_api_base: str
    openai_model: str
    openai_timeout_sec: int
    openai_excerpt_chars: int

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    raw_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("TEXT_EXTRACTION_OPENAI_API_KEY")
    raw_swagger_username = os.getenv("SWAGGER_USERNAME")
    raw_swagger_password = os.getenv("SWAGGER_PASSWORD")
    return Settings(
        max_file_size_mb=_env_int("TEXT_EXTRACTION_MAX_FILE_SIZE_MB", 50),
        virtual_max_lines_per_page=_env_int("TEXT_EXTRACTION_MAX_LINES_PER_PAGE", 50),
        virtual_max_chars_per_page=_env_int("TEXT_EXTRACTION_MAX_CHARS_PER_PAGE", 3500),
        remote_fetch_timeout_sec=_env_int("TEXT_EXTRACTION_REMOTE_FETCH_TIMEOUT_SEC", 20),
        openai_api_key=raw_api_key.strip() if raw_api_key and raw_api_key.strip() else None,
        swagger_username=raw_swagger_username.strip() if raw_swagger_username and raw_swagger_username.strip() else None,
        swagger_password=raw_swagger_password.strip() if raw_swagger_password and raw_swagger_password.strip() else None,
        openai_api_base=os.getenv("TEXT_EXTRACTION_OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/"),
        openai_model=os.getenv("TEXT_EXTRACTION_OPENAI_MODEL", "gpt-4.1-mini"),
        openai_timeout_sec=_env_int("TEXT_EXTRACTION_OPENAI_TIMEOUT_SEC", 20),
        openai_excerpt_chars=_env_int("TEXT_EXTRACTION_OPENAI_EXCERPT_CHARS", 8000),
    )
