"""OpenAI vision → VisionSchema."""

from __future__ import annotations

import base64
import json
from typing import Any

from openai import AsyncOpenAI

from zref.config import Settings
from zref.providers.base import VisionProvider, VisionRequest, VisionResponse, VisionUsage
from zref.providers.retry import async_retry
from zref.schema import VisionSchema


# USD per 1M tokens (approximate; update for your billing)
_OPENAI_PRICE: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    "default": {"input": 2.5, "output": 10.0},
}


def _estimate_openai_cost(model: str, inp: int | None, out: int | None) -> float | None:
    if inp is None and out is None:
        return None
    tier = _OPENAI_PRICE.get(model, _OPENAI_PRICE["default"])
    inp = inp or 0
    out = out or 0
    return (inp * tier["input"] + out * tier["output"]) / 1_000_000


class OpenAIVisionProvider(VisionProvider):
    name = "openai"

    def __init__(self, settings: Settings) -> None:
        key = settings.openai_api_key
        if key is None:
            raise ValueError("OpenAI: set OPENAI_API_KEY or ZREF_OPENAI_API_KEY")
        self._client = AsyncOpenAI(api_key=key.get_secret_value(), timeout=settings.http_timeout_s)
        self._model = settings.openai_model
        self._settings = settings

    async def describe(self, req: VisionRequest) -> VisionResponse:
        b64 = base64.standard_b64encode(req.image_bytes).decode("ascii")
        data_url = f"data:{req.mime_type};base64,{b64}"

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": req.system_prompt or "You analyze images precisely."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": req.user_prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ]

        async def call_parse() -> VisionResponse:
            resp = await self._client.beta.chat.completions.parse(
                model=self._model,
                messages=messages,
                response_format=VisionSchema,
            )
            choice = resp.choices[0]
            parsed = choice.message.parsed
            if parsed is None:
                raw = choice.message.refusal or choice.message.content or ""
                raise ValueError(f"OpenAI parse failed: {raw[:500]}")
            u = resp.usage
            inp = getattr(u, "prompt_tokens", None) if u else None
            out = getattr(u, "completion_tokens", None) if u else None
            tot = getattr(u, "total_tokens", None) if u else None
            usage = VisionUsage(
                input_tokens=inp,
                output_tokens=out,
                total_tokens=tot,
                cost_usd=_estimate_openai_cost(self._model, inp, out),
                raw={"model": self._model, "provider": self.name},
            )
            return VisionResponse(schema=parsed, usage=usage, provider=self.name)

        async def call_json_object() -> VisionResponse:
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content or "{}"
            data = json.loads(content)
            parsed = VisionSchema.model_validate(data)
            u = resp.usage
            inp = getattr(u, "prompt_tokens", None) if u else None
            out = getattr(u, "completion_tokens", None) if u else None
            tot = getattr(u, "total_tokens", None) if u else None
            usage = VisionUsage(
                input_tokens=inp,
                output_tokens=out,
                total_tokens=tot,
                cost_usd=_estimate_openai_cost(self._model, inp, out),
                raw={"model": self._model, "provider": self.name, "fallback": "json_object"},
            )
            return VisionResponse(schema=parsed, usage=usage, provider=self.name)

        async def call() -> VisionResponse:
            try:
                return await call_parse()
            except Exception:
                return await call_json_object()

        return await async_retry(call, max_retries=self._settings.max_retries)
