"""Disk cache keyed by image hash + options."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from zref.schema import VisionSchema


def make_cache_key(image_bytes: bytes, parts: dict[str, Any]) -> str:
    h = hashlib.sha256()
    h.update(image_bytes)
    h.update(json.dumps(parts, sort_keys=True, default=str).encode("utf-8"))
    return h.hexdigest()


def cache_path(cache_dir: Path, key: str) -> Path:
    return cache_dir / f"{key}.json"


def read_cache(cache_dir: Path | None, key: str) -> dict[str, Any] | None:
    if cache_dir is None:
        return None
    p = cache_path(cache_dir, key)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def write_cache(cache_dir: Path | None, key: str, payload: dict[str, Any]) -> None:
    if cache_dir is None:
        return
    cache_dir.mkdir(parents=True, exist_ok=True)
    p = cache_path(cache_dir, key)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def schema_from_cache(obj: dict[str, Any]) -> VisionSchema:
    return VisionSchema.model_validate(obj["schema"])
