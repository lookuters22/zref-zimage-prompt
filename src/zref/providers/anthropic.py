"""Anthropic vision → VisionSchema (tool use for JSON)."""

from __future__ import annotations


import anthropic

from zref.config import Settings
from zref.providers.base import VisionProvider, VisionRequest, VisionResponse, VisionUsage
from zref.providers.retry import async_retry
from zref.schema import VisionSchema, vision_schema_json_schema


_ANTHROPIC_PRICE: dict[str, dict[str, float]] = {
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "default": {"input": 3.0, "output": 15.0},
}


def _estimate_anthropic_cost(model: str, inp: int | None, out: int | None) -> float | None:
    if inp is None and out is None:
        return None
    tier = _ANTHROPIC_PRICE.get(model, _ANTHROPIC_PRICE["default"])
    inp = inp or 0
    out = out or 0
    return (inp * tier["input"] + out * tier["output"]) / 1_000_000


class AnthropicVisionProvider(VisionProvider):
    name = "anthropic"

    def __init__(self, settings: Settings) -> None:
        key = settings.anthropic_api_key
        if key is None:
            raise ValueError("Anthropic: set ANTHROPIC_API_KEY or ZREF_ANTHROPIC_API_KEY")
        self._client = anthropic.AsyncAnthropic(
            api_key=key.get_secret_value(),
            timeout=settings.http_timeout_s,
        )
        self._model = settings.anthropic_model
        self._settings = settings
        self._tool_name = "emit_vision_schema"
        self._tool_schema: dict[str, Any] = vision_schema_json_schema()

    async def describe(self, req: VisionRequest) -> VisionResponse:
        b64 = base64.standard_b64encode(req.image_bytes).decode("ascii")

        async def call() -> VisionResponse:
            msg = await self._client.messages.create(
                model=self._model,
                max_tokens=16384,
                system=req.system_prompt or "You analyze images precisely.",
                tools=[
                    {
                        "name": self._tool_name,
                        "description": "Emit the full vision schema as structured JSON.",
                        "input_schema": self._tool_schema,
                    }
                ],
                tool_choice={"type": "tool", "name": self._tool_name},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": req.mime_type,
                                    "data": b64,
                                },
                            },
                            {"type": "text", "text": req.user_prompt},
                        ],
                    }
                ],
            )
            tool_input: dict[str, Any] | None = None
            for block in msg.content:
                if block.type == "tool_use" and block.name == self._tool_name:
                    tool_input = block.input  # type: ignore[assignment]
                    break
            if not tool_input:
                raise ValueError("Anthropic: no tool_use block in response")
            parsed = VisionSchema.model_validate(tool_input)
            u = msg.usage
            inp = getattr(u, "input_tokens", None)
            out = getattr(u, "output_tokens", None)
            usage = VisionUsage(
                input_tokens=inp,
                output_tokens=out,
                total_tokens=(inp or 0) + (out or 0) if (inp is not None or out is not None) else None,
                cost_usd=_estimate_anthropic_cost(self._model, inp, out),
                raw={"model": self._model, "provider": self.name},
            )
            return VisionResponse(schema=parsed, usage=usage, provider=self.name)

        return await async_retry(call, max_retries=self._settings.max_retries)
