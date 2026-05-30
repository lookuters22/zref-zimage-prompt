"""Structured vision schema for reference → Z-Image prompt."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Priority = int  # 1 = most important for reproduction, 10 = least


class PT(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Free text with compiler priority (1=highest)."""

    text: str = ""
    priority: Priority = Field(default=5, ge=1, le=10)


class BoundingRegion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Optional coarse location in frame (0–1 normalized)."""

    x0: float = Field(ge=0, le=1, default=0)
    y0: float = Field(ge=0, le=1, default=0)
    x1: float = Field(ge=0, le=1, default=1)
    y1: float = Field(ge=0, le=1, default=1)


class WardrobeItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = ""
    material: str = ""
    color: str = ""
    pattern: str = ""
    fit: str = ""
    details: str = ""
    priority: Priority = 6


class HandDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str = ""
    visible: bool = True
    issues: str = ""  # occlusion, motion blur, etc.


class FaceDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    age_apparent: str = ""
    expression: str = ""
    gaze_direction: str = ""
    makeup: str = ""
    facial_hair: str = ""
    distinctive_features: str = ""
    priority: Priority = 2


class HairDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    length: str = ""
    style: str = ""
    color: str = ""
    texture: str = ""
    priority: Priority = 3


class SkinDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tone: str = ""
    texture: str = ""  # pores, freckles, sheen
    lighting_interaction: str = ""
    priority: Priority = 4


class PoseDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    overall: str = ""  # standing, seated, crouched, walking
    torso_angle: str = ""
    head_tilt: str = ""
    shoulders: str = ""
    hips: str = ""
    legs: str = ""
    feet: str = ""
    weight_distribution: str = ""
    interaction_with_environment: str = ""
    priority: Priority = 1


class AnatomyDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    body_type: str = ""
    proportions: str = ""
    visible_musculature: str = ""
    notes: str = ""
    priority: Priority = 3


class Subject(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """One person or primary figure."""

    role: str = Field(default="subject", description="primary, secondary, background, etc.")
    region: BoundingRegion | None = None
    pose: PoseDetail = Field(default_factory=PoseDetail)
    anatomy: AnatomyDetail = Field(default_factory=AnatomyDetail)
    hands: list[HandDetail] = Field(default_factory=list)
    face: FaceDetail = Field(default_factory=FaceDetail)
    hair: HairDetail = Field(default_factory=HairDetail)
    skin: SkinDetail = Field(default_factory=SkinDetail)
    wardrobe: list[WardrobeItem] = Field(default_factory=list)
    accessories: list[PT] = Field(default_factory=list)
    notes: PT = Field(default_factory=lambda: PT(priority=7))


class CameraOptics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    estimated_focal_length_mm: str = ""  # e.g. "35", "85"
    aperture_f_stop: str = ""
    depth_of_field: str = ""  # shallow, deep
    bokeh: str = ""
    lens_character: str = ""  # flare, CA, vignette
    sensor_format_hint: str = ""  # full-frame, APS-C, phone
    priority: Priority = 4


class LightingModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quality: str = ""  # hard, soft, mixed
    direction: str = ""  # key direction
    color_temperature: str = ""  # warm, cool, mixed K if known
    contrast: str = ""
    shadows: str = ""
    highlights: str = ""
    rim_separation: str = ""
    practicals: str = ""  # visible sources
    priority: Priority = 2


class ColorGrade(BaseModel):
    model_config = ConfigDict(extra="forbid")
    palette: str = ""
    saturation: str = ""
    contrast_curve: str = ""
    split_toning: str = ""
    film_stock_or_lut_hint: str = ""
    priority: Priority = 5


class EnvironmentDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    location_type: str = ""  # indoor studio, street, home, etc.
    set_description: str = ""
    props: list[str] = Field(default_factory=list)
    background_busyness: str = ""
    depth_layers: str = ""  # foreground/mid/background
    priority: Priority = 6


class RealismCues(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Authentic-imperfection cues (baked into positive for Z-Image Turbo)."""

    grain: str = ""
    motion_blur: str = ""
    micro_asymmetry: str = ""
    skin_imperfections: str = ""
    fabric_wrinkles_dust_wear: str = ""
    optical_imperfections: str = ""
    priority: Priority = 3


class CompositionDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    framing: str = ""  # full body, waist-up, close-up
    camera_height: str = ""
    angle: str = ""  # eye level, low, high
    subject_placement: str = ""  # rule of thirds, center, etc.
    negative_space: str = ""
    leading_lines: str = ""
    aspect_ratio_hint: str = ""  # "3:4", "16:9", "1:1"
    priority: Priority = 2


class VisionSchema(BaseModel):
    """Full structured description from a reference image."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default="1.0")
    image_summary: str = Field(default="", description="One dense paragraph of global gist")

    subjects: list[Subject] = Field(default_factory=list)
    non_human_primary: PT = Field(
        default_factory=lambda: PT(priority=6),
        description="Product/scene focus when no people",
    )

    composition: CompositionDetail = Field(default_factory=CompositionDetail)
    camera: CameraOptics = Field(default_factory=CameraOptics)
    lighting: LightingModel = Field(default_factory=LightingModel)
    color_grade: ColorGrade = Field(default_factory=ColorGrade)
    environment: EnvironmentDetail = Field(default_factory=EnvironmentDetail)
    realism: RealismCues = Field(default_factory=RealismCues)
    mood: PT = Field(default_factory=lambda: PT(priority=8))

    medium: Literal["photo", "cgi", "illustration", "unknown"] = "photo"
    era_or_style: str = ""

    reproduction_critical: list[str] = Field(
        default_factory=list,
        description="Bullet list of must-not-miss details for identity/pose",
    )
    avoid_ai_cliches: list[str] = Field(
        default_factory=list,
        description="Things to avoid saying (compiler strips similar terms too)",
    )

def vision_schema_json_schema() -> dict:
    """JSON Schema for VLM structured output."""
    return VisionSchema.model_json_schema()
