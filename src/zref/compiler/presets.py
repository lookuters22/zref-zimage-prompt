"""Style / encoder system presets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PresetName = Literal["default", "editorial", "candid", "studio", "ecomm"]


@dataclass(frozen=True)
class Preset:
    name: str
    system_prompt: str
    positive_prefix: str
    positive_suffix: str
    negative: str


PRESETS: dict[str, Preset] = {
    "default": Preset(
        name="default",
        system_prompt="",
        positive_prefix="",
        positive_suffix=" Natural photographic imperfections; believable optics, atmosphere, and material response.",
        negative="illustration, vector, 3D render, oversharpened, plastic skin, waxy skin, CGI",
    ),
    "editorial": Preset(
        name="editorial",
        system_prompt="",
        positive_prefix="Editorial photograph with restrained color and print-ready contrast. ",
        positive_suffix=" Subtle grain; natural skin texture; realistic lens bokeh.",
        negative="HDR glow, oversaturation, stock photo cliché, beauty filter",
    ),
    "candid": Preset(
        name="candid",
        system_prompt="",
        positive_prefix="Candid documentary photograph; momentary pose; handheld camera feel. ",
        positive_suffix=" Slight motion realism; imperfect framing acceptable; available light.",
        negative="studio perfection, frozen mannequin pose, symmetrical staging",
    ),
    "studio": Preset(
        name="studio",
        system_prompt="",
        positive_prefix="Studio photograph; controlled lighting; clean subject separation. ",
        positive_suffix=" Accurate material response; soft shadows with natural penumbra.",
        negative="on-location chaos, heavy HDR, painterly",
    ),
    "ecomm": Preset(
        name="ecomm",
        system_prompt="",
        positive_prefix="Commercial product-style photograph; accurate colors; crisp edges where intended. ",
        positive_suffix=" Neutral background unless reference shows otherwise; faithful materials.",
        negative="fantasy lighting, painterly, illustration",
    ),
}


def get_preset(name: str) -> Preset:
    return PRESETS.get(name, PRESETS["default"])
