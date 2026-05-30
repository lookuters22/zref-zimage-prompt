"""Google Gemini vision → VisionSchema."""

from __future__ import annotations

import io
from typing import Any

from google import genai
from google.genai import types
from PIL import Image

from zref.config import Settings
from zref.providers.base import VisionProvider, VisionRequest, VisionResponse, VisionUsage
from zref.providers.retry import async_retry
from zref.schema import VisionSchema, vision_schema_json_schema


_GEMINI_PRICE: dict[str, dict[str, float]] = {
    "gemini-2.0-flash": {"input": 0.1, "output": 0.4},
    "default": {"input": 0.1, "output": 0.4},
}


def _estimate_gemini_cost(model: str, inp: int | None, out: int | None) -> float | None:
    if inp is None and out is None:
        return None
    tier = _GEMINI_PRICE.get(model, _GEMINI_PRICE["default"])
    inp = inp or 0
    out = out or 0
    return (inp * tier["input"] + out * tier["output"]) / 1_000_000


class GeminiVisionProvider(VisionProvider):
    name = "gemini"

    def __init__(self, settings: Settings) -> None:
        key = settings.google_api_key
        if key is None:
            raise ValueError("Gemini: set GOOGLE_API_KEY or ZREF_GOOGLE_API_KEY")
        self._client = genai.Client(api_key=key.get_secret_value())
        self._model = settings.gemini_model
        self._settings = settings
        self._schema_dict: dict[str, Any] = vision_schema_json_schema()

    async def describe(self, req: VisionRequest) -> VisionResponse:
        pil = Image.open(io.BytesIO(req.image_bytes))
        # Gemini accepts PIL images in contents

        async def call() -> VisionResponse:
            # google-genai sync client — run in thread for async API surface
            import asyncio

            def sync_call() -> VisionResponse:
                cfg = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=self._schema_dict,
                    system_instruction=req.system_prompt or None,
                )
                resp = self._client.models.generate_content(
                    model=self._model,
                    contents=[pil, req.user_prompt],
                    config=cfg,
                )
                text = resp.text or "{}"
                parsed = VisionSchema.model_validate_json(text)
                um = getattr(resp, "usage_metadata", None)
                inp = getattr(um, "prompt_token_count", None) if um else None
                out = getattr(um, "candidates_token_count", None) if um else None
                tot = getattr(um, "total_token_count", None) if um else None
                usage = VisionUsage(
                    input_tokens=inp,
                    output_tokens=out,
                    total_tokens=tot,
                    cost_usd=_estimate_gemini_cost(self._model, inp, out),
                    raw={"model": self._model, "provider": self.name},
                )
                return VisionResponse(schema=parsed, usage=usage, provider=self.name)

            return await asyncio.to_thread(sync_call)

        return await async_retry(call, max_retries=self._settings.max_retries)
