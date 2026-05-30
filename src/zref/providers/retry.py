"""Retry / backoff helpers."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx

T = TypeVar("T")


async def async_retry(
    fn: Callable[[], Awaitable[T]],
    *,
    max_retries: int = 4,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
) -> T:
    last: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except (httpx.HTTPStatusError, httpx.TransportError, asyncio.TimeoutError) as e:
            last = e
            if attempt >= max_retries:
                break
            # Respect Retry-After if present
            delay = base_delay * (2**attempt) + random.random() * 0.1
            if isinstance(e, httpx.HTTPStatusError) and e.response is not None:
                ra = e.response.headers.get("Retry-After")
                if ra:
                    try:
                        delay = max(delay, float(ra))
                    except ValueError:
                        pass
            delay = min(delay, max_delay)
            await asyncio.sleep(delay)
        except Exception as e:
            # OpenAI/Anthropic SDK errors
            code = getattr(e, "status_code", None) or getattr(e, "code", None)
            if code in (429, 500, 502, 503, 504) and attempt < max_retries:
                last = e
                delay = min(base_delay * (2**attempt), max_delay)
                await asyncio.sleep(delay)
                continue
            raise
    assert last is not None
    raise last
