"""End-to-end describe: image bytes → structured schema + compiled prompts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from zref.cache import make_cache_key, read_cache, schema_from_cache, write_cache
from zref.compiler.zimage import CompiledPrompt, compile_zimage_prompt
from zref.config import ProviderName, Settings, get_settings
from zref.extraction.extractor import extract_schema
from zref.providers.base import VisionUsage
from zref.schema import VisionSchema


@dataclass
class PromptResult:
    positive: str
    negative: str
    system_prompt: str | None
    schema: VisionSchema
    token_count: int
    provider: str
    usage: VisionUsage | None = None
    meta: dict[str, Any] = field(default_factory=dict)


def serialize_result(result: PromptResult, out_dir: Path, stem: str) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    txt = out_dir / f"{stem}.txt"
    js = out_dir / f"{stem}.schema.json"
    txt.write_text(result.positive, encoding="utf-8")
    js.write_text(
        json.dumps(result.schema.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return txt, js


async def describe_image(
    image_bytes: bytes,
    mime_type: str,
    *,
    settings: Settings | None = None,
    provider: ProviderName | None = None,
    preset: str = "default",
    max_prompt_tokens: int | None = None,
    use_cache: bool = True,
    system_prompt: str | None = None,
    user_prompt: str | None = None,
) -> PromptResult:
    s = settings or get_settings()
    max_tok = max_prompt_tokens if max_prompt_tokens is not None else s.max_prompt_tokens
    prov = provider or s.default_provider

    cache_dir = Path(s.cache_dir) if s.cache_dir else None
    key_parts = {
        "provider": prov,
        "preset": preset,
        "max_prompt_tokens": max_tok,
        "system_prompt": system_prompt or "",
        "user_prompt": user_prompt or "",
        "schema_version": "1.0",
    }
    ck = make_cache_key(image_bytes, key_parts)

    if use_cache and cache_dir:
        cached = read_cache(cache_dir, ck)
        if cached:
            schema = schema_from_cache(cached)
            compiled = compile_zimage_prompt(
                schema,
                preset=preset,
                max_tokens=max_tok,
                tokenizer_model_id=s.tokenizer_model_id,
            )
            return PromptResult(
                positive=compiled.positive,
                negative=compiled.negative,
                system_prompt=compiled.system_prompt,
                schema=schema,
                token_count=compiled.token_count,
                provider=cached.get("provider", prov),
                usage=None,
                meta={"cache_hit": True, "cache_key": ck},
            )

    vr = await extract_schema(
        image_bytes,
        mime_type,
        settings=s,
        provider=prov,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    compiled = compile_zimage_prompt(
        vr.schema,
        preset=preset,
        max_tokens=max_tok,
        tokenizer_model_id=s.tokenizer_model_id,
    )
    result = PromptResult(
        positive=compiled.positive,
        negative=compiled.negative,
        system_prompt=compiled.system_prompt,
        schema=vr.schema,
        token_count=compiled.token_count,
        provider=vr.provider,
        usage=vr.usage,
        meta={"cache_hit": False, "cache_key": ck},
    )

    if use_cache and cache_dir:
        write_cache(
            cache_dir,
            ck,
            {
                "schema": vr.schema.model_dump(),
                "provider": vr.provider,
                "usage": {
                    "input_tokens": vr.usage.input_tokens,
                    "output_tokens": vr.usage.output_tokens,
                    "total_tokens": vr.usage.total_tokens,
                    "cost_usd": vr.usage.cost_usd,
                },
            },
        )

    return result


def describe_image_sync(
    image_bytes: bytes,
    mime_type: str,
    *,
    settings: Settings | None = None,
    provider: ProviderName | None = None,
    preset: str = "default",
    max_prompt_tokens: int | None = None,
    use_cache: bool = True,
    system_prompt: str | None = None,
    user_prompt: str | None = None,
) -> PromptResult:
    import asyncio

    return asyncio.run(
        describe_image(
            image_bytes,
            mime_type,
            settings=settings,
            provider=provider,
            preset=preset,
            max_prompt_tokens=max_prompt_tokens,
            use_cache=use_cache,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
    )
