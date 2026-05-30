"""Structured logging helpers."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

LOG = logging.getLogger("zref")


def configure_logging(level: int = logging.INFO) -> None:
    if LOG.handlers:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    LOG.setLevel(level)
    LOG.addHandler(handler)
    LOG.propagate = False


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        ef = getattr(record, "extra_fields", None)
        if isinstance(ef, dict):
            payload.update(ef)
        return json.dumps(payload, default=str)


def log_extra(**kwargs: Any) -> dict[str, Any]:
    return {"extra": {"extra_fields": kwargs}}
