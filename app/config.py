from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class AISettings:
    provider: str
    chat_completions_url: str
    api_key: str
    model: str | None
    timeout_seconds: int

    @property
    def enabled(self) -> bool:
        return bool(self.chat_completions_url and self.api_key)


@dataclass(frozen=True)
class DataSettings:
    source: str
    database_url: str

    @property
    def use_postgres(self) -> bool:
        return self.source == "postgres" and bool(self.database_url)


@dataclass(frozen=True)
class ObjectStoreSettings:
    endpoint: str
    access_key: str
    secret_key: str
    bucket_name: str
    secure: bool

    @property
    def configured(self) -> bool:
        return bool(self.endpoint and self.access_key and self.secret_key and self.bucket_name)


@lru_cache(maxsize=1)
def get_ai_settings() -> AISettings:
    timeout_value = os.getenv("AI_TIMEOUT_SECONDS", "30").strip() or "30"

    return AISettings(
        provider=os.getenv("AI_PROVIDER", "disabled").strip() or "disabled",
        chat_completions_url=os.getenv("AI_CHAT_COMPLETIONS_URL", "").strip(),
        api_key=os.getenv("AI_API_KEY", "").strip(),
        model=os.getenv("AI_MODEL", "").strip() or None,
        timeout_seconds=int(timeout_value),
    )


@lru_cache(maxsize=1)
def get_data_settings() -> DataSettings:
    return DataSettings(
        source=os.getenv("DATA_SOURCE", "json").strip().lower() or "json",
        database_url=os.getenv("DATABASE_URL", "").strip(),
    )


@lru_cache(maxsize=1)
def get_object_store_settings() -> ObjectStoreSettings:
    return ObjectStoreSettings(
        endpoint=os.getenv("OBJECT_STORE_ENDPOINT", "").strip(),
        access_key=os.getenv("OBJECT_STORE_ACCESS_KEY", "").strip(),
        secret_key=os.getenv("OBJECT_STORE_SECRET_KEY", "").strip(),
        bucket_name=os.getenv("OBJECT_STORE_BUCKET", "contract-documents").strip() or "contract-documents",
        secure=(os.getenv("OBJECT_STORE_SECURE", "false").strip().lower() == "true"),
    )


def clear_ai_settings_cache() -> None:
    get_ai_settings.cache_clear()


def clear_data_settings_cache() -> None:
    get_data_settings.cache_clear()


def clear_object_store_settings_cache() -> None:
    get_object_store_settings.cache_clear()
