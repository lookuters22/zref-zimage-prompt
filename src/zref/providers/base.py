"""Vision provider protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from zref.schema import VisionSchema


@dataclass
class VisionRequest:
    image_bytes: bytes
    mime_type: str = "image/jpeg"
    system_prompt: str = ""
    user_prompt: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class VisionUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cost_usd: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class VisionResponse:
    schema: VisionSchema
    usage: VisionUsage = field(default_factory=VisionUsage)
    provider: str = ""


class VisionProvider(ABC):
    name: str = ""

    @abstractmethod
    async def describe(self, req: VisionRequest) -> VisionResponse:
        raise NotImplementedError
