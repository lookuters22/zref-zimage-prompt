"""VisionSchema → Z-Image natural-language prompt with token budget.

Assembles **one narrative** in a fixed order tuned for Qwen-style encoders:
must-preserve → subjects (pose/limbs first) → camera+shot → place/weather
→ light+color → realism → optional summary last (so it is trimmed first
when tokens are tight).
"""

from __future__ import annotations

from dataclasses import dataclass

from zref.compiler import tokenizer_util as _tokutil
from zref.compiler.presets import Preset, get_preset
from zref.compiler.realism import naturalize, strip_banned_terms
from zref.schema import Subject, VisionSchema


@dataclass
class CompiledPrompt:
    positive: str
    negative: str
    system_prompt: str | None
    token_count: int


def _reproduction_chunk(schema: VisionSchema) -> str:
    lines = [f"Must preserve: {x.strip()}." for x in schema.reproduction_critical if x.strip()]
    return " ".join(lines).strip()


def _subject_paragraph(s: Subject, idx: int) -> str:
    label = f"Subject {idx + 1}" if s.role in ("", "subject", "primary") else f"{s.role} (figure {idx + 1})"
    clauses: list[str] = []

    p = s.pose
    if (p.arms_hands_lr or "").strip():
        clauses.append((p.arms_hands_lr or "").strip())
    pose_bits = [
        p.overall,
        p.torso_angle and f"torso {p.torso_angle}",
        p.head_tilt and f"head {p.head_tilt}",
        p.shoulders and f"shoulders {p.shoulders}",
        p.hips and f"hips {p.hips}",
        p.legs and f"legs {p.legs}",
        p.feet and f"feet {p.feet}",
        p.weight_distribution and f"weight {p.weight_distribution}",
        p.interaction_with_environment,
    ]
    pose_bits = [x for x in pose_bits if x]
    if pose_bits:
        clauses.append("Pose: " + "; ".join(pose_bits))

    a = s.anatomy
    abits = [x for x in (a.body_type, a.proportions, a.visible_musculature, a.notes) if x]
    if abits:
        clauses.append("Body: " + "; ".join(abits))

    if s.hands:
        hb = "; ".join(
            (h.description + (" (hidden)" if not h.visible else "") + (f" — {h.issues}" if h.issues else "")).strip()
            for h in s.hands
            if (h.description or h.issues)
        )
        if hb:
            clauses.append("Hands: " + hb)

    f = s.face
    fbits = [x for x in (f.age_apparent, f.expression, f.gaze_direction, f.makeup, f.facial_hair, f.distinctive_features) if x]
    if fbits:
        clauses.append("Face: " + "; ".join(fbits))

    h = s.hair
    hbits = [x for x in (h.length, h.style, h.color, h.texture) if x]
    if hbits:
        clauses.append("Hair: " + "; ".join(hbits))

    sk = s.skin
    skbits = [x for x in (sk.tone, sk.texture, sk.lighting_interaction) if x]
    if skbits:
        clauses.append("Skin: " + "; ".join(skbits))

    for w in s.wardrobe:
        wb = " ".join(
            p
            for p in (
                w.name,
                f"material {w.material}" if w.material else "",
                f"color {w.color}" if w.color else "",
                f"pattern {w.pattern}" if w.pattern else "",
                f"fit {w.fit}" if w.fit else "",
                w.details,
            )
            if p
        )
        if wb.strip():
            clauses.append("Wardrobe: " + wb.strip())

    for acc in s.accessories:
        if acc.text.strip():
            clauses.append("Accessory: " + acc.text.strip())

    if s.notes.text.strip():
        clauses.append("Notes: " + s.notes.text.strip())

    if not clauses:
        return ""
    return f"{label}: " + " ".join(clauses) + "."


def _scene_camera_chunk(schema: VisionSchema) -> str:
    c = schema.composition
    cam = schema.camera
    parts: list[str] = []
    cb = [
        x
        for x in (
            c.shot_scale and f"shot scale {c.shot_scale}",
            c.framing and f"crop {c.framing}",
            c.camera_height,
            c.angle and f"camera angle {c.angle}",
            c.subject_placement,
            c.negative_space,
            c.leading_lines,
            c.aspect_ratio_hint and f"aspect {c.aspect_ratio_hint}",
        )
        if x
    ]
    if cb:
        parts.append("Composition: " + "; ".join(cb))
    camb = [
        x
        for x in (
            cam.estimated_focal_length_mm and f"~{cam.estimated_focal_length_mm}mm lens",
            cam.aperture_f_stop and f"f/{cam.aperture_f_stop}",
            cam.depth_of_field,
            cam.bokeh,
            cam.lens_character,
            cam.sensor_format_hint,
        )
        if x
    ]
    if camb:
        parts.append("Optics: " + "; ".join(camb))
    if not parts:
        return ""
    return " ".join(parts) + "."


def _environment_chunk(schema: VisionSchema) -> str:
    e = schema.environment
    bits: list[str] = []
    if e.location_type:
        bits.append(f"place type {e.location_type}")
    if (e.weather_sky or "").strip():
        bits.append(e.weather_sky.strip())
    if e.set_description:
        bits.append(e.set_description.strip())
    if e.depth_layers:
        bits.append(f"depth {e.depth_layers}")
    if e.background_busyness:
        bits.append(e.background_busyness)
    if e.props:
        bits.append("props " + ", ".join(e.props))
    if not bits:
        return ""
    return "Scene: " + "; ".join(bits) + "."


def _lighting_color_chunk(schema: VisionSchema) -> str:
    L = schema.lighting
    lb = [
        x
        for x in (
            L.quality,
            L.direction,
            L.color_temperature,
            L.contrast,
            L.shadows,
            L.highlights,
            L.rim_separation,
            L.practicals,
        )
        if x
    ]
    cg = schema.color_grade
    cgb = [x for x in (cg.palette, cg.saturation, cg.contrast_curve, cg.split_toning, cg.film_stock_or_lut_hint) if x]
    parts: list[str] = []
    if lb:
        parts.append("Light: " + "; ".join(lb))
    if cgb:
        parts.append("Color: " + "; ".join(cgb))
    if not parts:
        return ""
    return " ".join(parts) + "."


def _realism_chunk(schema: VisionSchema) -> str:
    r = schema.realism
    rb = [
        x
        for x in (
            r.grain,
            r.motion_blur,
            r.micro_asymmetry,
            r.skin_imperfections,
            r.fabric_wrinkles_dust_wear,
            r.optical_imperfections,
        )
        if x
    ]
    if not rb:
        return ""
    return "Imperfections: " + "; ".join(rb) + "."


def _narrative_chunks(schema: VisionSchema) -> list[str]:
    """Ordered chunks; later chunks are dropped first when over token budget."""
    out: list[str] = []

    r = _reproduction_chunk(schema)
    if r:
        out.append(r)

    for i, subj in enumerate(schema.subjects):
        sp = _subject_paragraph(subj, i)
        if sp:
            out.append(sp)

    sc = _scene_camera_chunk(schema)
    if sc:
        out.append(sc)

    env = _environment_chunk(schema)
    if env:
        out.append(env)

    lc = _lighting_color_chunk(schema)
    if lc:
        out.append(lc)

    rm = _realism_chunk(schema)
    if rm:
        out.append(rm)

    nh = (schema.non_human_primary.text or "").strip()
    if nh:
        out.append(f"Primary non-person detail: {nh}")

    if schema.era_or_style.strip():
        out.append(f"Era/style: {schema.era_or_style.strip()}.")

    if schema.medium != "unknown":
        out.append(f"Medium: {schema.medium}.")

    if schema.image_summary.strip():
        out.append(schema.image_summary.strip())

    if schema.mood.text.strip():
        out.append(f"Mood: {schema.mood.text.strip()}.")

    return [x.strip() for x in out if x.strip()]


def _fit_chunks(chunks: list[str], max_tokens: int, tokenizer_model_id: str) -> str:
    work = chunks[:]
    while work:
        text = " ".join(work).strip()
        if _tokutil.count_tokens(text, tokenizer_model_id) <= max_tokens:
            return text
        work.pop()
    return ""


def _truncate_words(text: str, max_tokens: int, tokenizer_model_id: str) -> str:
    words = text.split()
    if not words:
        return ""
    lo, hi = 0, len(words)
    best = ""
    while lo <= hi:
        mid = (lo + hi) // 2
        cand = " ".join(words[:mid])
        if _tokutil.count_tokens(cand, tokenizer_model_id) <= max_tokens:
            best = cand
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def compile_zimage_prompt(
    schema: VisionSchema,
    *,
    preset: str = "default",
    max_tokens: int = 480,
    tokenizer_model_id: str = "Qwen/Qwen3-4B",
) -> CompiledPrompt:
    pr = get_preset(preset)
    chunks = _narrative_chunks(schema)
    body = _fit_chunks(chunks, max_tokens=max_tokens, tokenizer_model_id=tokenizer_model_id)
    if not body.strip():
        body = schema.image_summary.strip() or "Photoreal reproduction of the reference scene and subjects."
        body = _truncate_words(body, max_tokens, tokenizer_model_id)

    body = strip_banned_terms(body, schema.avoid_ai_cliches)
    body = naturalize(body)

    positive = (pr.positive_prefix + body + pr.positive_suffix).strip()
    positive = naturalize(positive)
    while _tokutil.count_tokens(positive, tokenizer_model_id) > max_tokens and positive:
        positive = _truncate_words(positive, max_tokens, tokenizer_model_id)

    tok = _tokutil.count_tokens(positive, tokenizer_model_id)
    sys_p = pr.system_prompt.strip() or None
    return CompiledPrompt(
        positive=positive,
        negative=pr.negative,
        system_prompt=sys_p,
        token_count=tok,
    )
