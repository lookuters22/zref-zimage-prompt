"""FastAPI server."""

from __future__ import annotations

import io
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from PIL import Image

from zref.config import ProviderName, get_settings
from zref.logging import configure_logging
from zref.pipeline import describe_image


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    yield


app = FastAPI(title="zref", version="0.1.0", lifespan=lifespan)
_bearer = HTTPBearer(auto_error=False)


async def _optional_auth(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> None:
    s = get_settings()
    expected = s.api_key.get_secret_value() if s.api_key else None
    if not expected:
        return
    if creds is None or creds.credentials != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/describe")
async def describe(
    _auth: Annotated[None, Depends(_optional_auth)],
    file: UploadFile = File(...),
    provider: Annotated[str | None, Form(None)] = None,
    preset: Annotated[str, Form("default")] = "default",
    max_prompt_tokens: Annotated[int | None, Form(None)] = None,
    no_cache: Annotated[bool, Form(False)] = False,
) -> dict:
    s = get_settings()
    raw = await file.read()
    mime = file.content_type or "image/jpeg"
    try:
        im = Image.open(io.BytesIO(raw))
        im = im.convert("RGB")
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=92)
        raw = buf.getvalue()
        mime = "image/jpeg"
    except OSError as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}") from e

    prov: ProviderName | None = None  # type: ignore[assignment]
    if provider in ("openai", "anthropic", "gemini"):
        prov = provider  # type: ignore[assignment]

    res = await describe_image(
        raw,
        mime,
        settings=s,
        provider=prov,
        preset=preset,
        max_prompt_tokens=max_prompt_tokens,
        use_cache=not no_cache,
    )
    return {
        "positive": res.positive,
        "negative": res.negative,
        "system_prompt": res.system_prompt,
        "token_count": res.token_count,
        "provider": res.provider,
        "schema": res.schema.model_dump(),
        "usage": {
            "input_tokens": res.usage.input_tokens if res.usage else None,
            "output_tokens": res.usage.output_tokens if res.usage else None,
            "total_tokens": res.usage.total_tokens if res.usage else None,
            "cost_usd": res.usage.cost_usd if res.usage else None,
        },
        "meta": res.meta,
    }
