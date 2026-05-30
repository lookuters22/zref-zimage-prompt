"""Load packaged prompts and run VLM extraction."""

from __future__ import annotations

import importlib.resources
from zref.config import ProviderName, Settings
from zref.providers import VisionRequest, get_provider
from zref.providers.base import VisionResponse


def _read_package_file(name: str) -> str:
    pkg = importlib.resources.files("zref.extraction.prompts")
    return pkg.joinpath(name).read_text(encoding="utf-8")


def load_default_prompts() -> tuple[str, str]:
    system = _read_package_file("v1_system.md")
    user = _read_package_file("v1_user.md")
    return system, user


async def extract_schema(
    image_bytes: bytes,
    mime_type: str,
    *,
    settings: Settings,
    provider: ProviderName | None = None,
    system_prompt: str | None = None,
    user_prompt: str | None = None,
) -> VisionResponse:
    sys_p, usr_p = load_default_prompts()
    p = get_provider(settings, provider)
    req = VisionRequest(
        image_bytes=image_bytes,
        mime_type=mime_type,
        system_prompt=system_prompt or sys_p,
        user_prompt=user_prompt or usr_p,
    )
    return await p.describe(req)


def extract_schema_sync(
    image_bytes: bytes,
    mime_type: str,
    *,
    settings: Settings,
    provider: ProviderName | None = None,
    system_prompt: str | None = None,
    user_prompt: str | None = None,
) -> VisionResponse:
    import asyncio

    return asyncio.run(
        extract_schema(
            image_bytes,
            mime_type,
            settings=settings,
            provider=provider,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
    )
