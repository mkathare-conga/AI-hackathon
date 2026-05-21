from __future__ import annotations

from urllib.parse import urlparse

from app.config import get_object_store_settings


def _resolve_endpoint() -> tuple[str, bool]:
    settings = get_object_store_settings()
    parsed = urlparse(settings.endpoint)
    if parsed.scheme:
        return parsed.netloc, settings.secure or parsed.scheme == "https"
    return settings.endpoint, settings.secure


def get_minio_client():
    from minio import Minio

    settings = get_object_store_settings()
    if not settings.configured:
        raise RuntimeError("Object store settings are not configured")

    endpoint, secure = _resolve_endpoint()
    return Minio(
        endpoint,
        access_key=settings.access_key,
        secret_key=settings.secret_key,
        secure=secure,
    )