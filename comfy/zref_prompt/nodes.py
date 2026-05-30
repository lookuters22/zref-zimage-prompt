"""ComfyUI nodes (requires `zref` installed in the ComfyUI Python env)."""

from __future__ import annotations

import asyncio
import io
import json
from typing import Any

import numpy as np
from PIL import Image
from pydantic import SecretStr

try:
    from zref.config import ProviderName, Settings, get_settings
    from zref.pipeline import describe_image
except ImportError as e:  # pragma: no cover - ComfyUI runtime
    get_settings = None  # type: ignore[assignment]
    describe_image = None  # type: ignore[assignment]
    Settings = object  # type: ignore[misc, assignment]
    ProviderName = str  # type: ignore[misc, assignment]
    _IMPORT_ERROR = e
else:
    _IMPORT_ERROR = None


def _tensor_to_jpeg_bytes(image: Any) -> tuple[bytes, str]:
    arr = image.cpu().numpy()
    if arr.ndim == 4:
        arr = arr[0]
    arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
    pil = Image.fromarray(arr)
    buf = io.BytesIO()
    pil.save(buf, format="JPEG", quality=92)
    return buf.getvalue(), "image/jpeg"


def _merge_settings(
    *,
    openai_key: str,
    anthropic_key: str,
    google_key: str,
    cache_dir: str,
) -> Settings:
    if get_settings is None:
        raise RuntimeError(f"zref is not importable: {_IMPORT_ERROR}")
    s = get_settings()
    updates: dict[str, Any] = {}
    if openai_key.strip():
        updates["openai_api_key"] = SecretStr(openai_key.strip())
    if anthropic_key.strip():
        updates["anthropic_api_key"] = SecretStr(anthropic_key.strip())
    if google_key.strip():
        updates["google_api_key"] = SecretStr(google_key.strip())
    if cache_dir.strip():
        updates["cache_dir"] = cache_dir.strip()
    if updates:
        return s.model_copy(update=updates)
    return s


class ZRefDescribeImage:
    """IMAGE → positive / negative / schema JSON strings."""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        providers = ["openai", "anthropic", "gemini"]
        presets = ["default", "editorial", "candid", "studio", "ecomm"]
        return {
            "required": {
                "image": ("IMAGE",),
                "provider": (providers, {"default": providers[0]}),
                "preset": (presets, {"default": "default"}),
                "max_prompt_tokens": ("INT", {"default": 480, "min": 64, "max": 512, "step": 1}),
                "use_cache": ("BOOLEAN", {"default": True}),
                "openai_api_key": ("STRING", {"default": ""}),
                "anthropic_api_key": ("STRING", {"default": ""}),
                "google_api_key": ("STRING", {"default": ""}),
                "cache_dir": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive", "negative", "schema_json")
    FUNCTION = "encode"
    CATEGORY = "zref"
    OUTPUT_NODE = False

    def encode(
        self,
        image: Any,
        provider: str,
        preset: str,
        max_prompt_tokens: int,
        use_cache: bool,
        openai_api_key: str,
        anthropic_api_key: str,
        google_api_key: str,
        cache_dir: str,
    ) -> tuple[str, str, str]:
        if describe_image is None:
            raise RuntimeError(
                "zref package not found. pip install zref (or editable install) into ComfyUI's Python."
            ) from _IMPORT_ERROR
        data, mime = _tensor_to_jpeg_bytes(image)
        s = _merge_settings(
            openai_key=openai_api_key,
            anthropic_key=anthropic_api_key,
            google_key=google_api_key,
            cache_dir=cache_dir,
        )
        prov: ProviderName | None = provider  # type: ignore[assignment]
        res = asyncio.run(
            describe_image(
                data,
                mime,
                settings=s,
                provider=prov,
                preset=preset,
                max_prompt_tokens=max_prompt_tokens,
                use_cache=use_cache,
            )
        )
        schema_json = json.dumps(res.schema.model_dump(), ensure_ascii=False, indent=2)
        return (res.positive, res.negative, schema_json)


NODE_CLASS_MAPPINGS = {"ZRefDescribeImage": ZRefDescribeImage}
NODE_DISPLAY_NAME_MAPPINGS = {"ZRefDescribeImage": "ZRef Describe Image (→ prompt)"}
