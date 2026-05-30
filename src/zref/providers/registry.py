"""Provider registry + factory."""

from __future__ import annotations

import asyncio

from zref.config import ProviderName, Settings
from zref.providers.anthropic import AnthropicVisionProvider
from zref.providers.base import VisionProvider, VisionRequest, VisionResponse
from zref.providers.gemini import GeminiVisionProvider
from zref.providers.openai import OpenAIVisionProvider


def get_provider(settings: Settings, name: ProviderName | None = None) -> VisionProvider:
    n = name or settings.default_provider
    if n == "openai":
        return OpenAIVisionProvider(settings)
    if n == "anthropic":
        return AnthropicVisionProvider(settings)
    if n == "gemini":
        return GeminiVisionProvider(settings)
    raise ValueError(f"Unknown provider: {n}")


class RateLimitedProvider(VisionProvider):
    """Wrap a provider with an asyncio semaphore."""

    def __init__(self, inner: VisionProvider, semaphore: asyncio.Semaphore) -> None:
        self._inner = inner
        self._sem = semaphore
        self.name = inner.name

    async def describe(self, req: VisionRequest) -> VisionResponse:
        async with self._sem:
            return await self._inner.describe(req)


def wrap_rate_limit(inner: VisionProvider, max_concurrent: int = 4) -> VisionProvider:
    return RateLimitedProvider(inner, asyncio.Semaphore(max_concurrent))
