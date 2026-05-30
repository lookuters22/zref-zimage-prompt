"""VisionSchema → Z-Image natural-language prompt with token budget."""

from __future__ import annotations

from dataclasses import dataclass

from zref.compiler import tokenizer_util as _tokutil
from zref.compiler.presets import Preset, get_preset
from zref.compiler.realism import naturalize, strip_banned_terms
from zref.schema import VisionSchema


@dataclass
class CompiledPrompt:
    positive: str
    negative: str
    system_prompt: str | None
    token_count: int


def _add(sec: list[tuple[int, str]], pr: int, text: str) -> None:
    t = (text or "").strip()
    if t:
        sec.append((pr, t))


def _subject_sections(schema: VisionSchema) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for i, s in enumerate(schema.subjects):
        label = f"Person {i + 1}" if s.role in ("", "subject", "primary") else f"{s.role} (figure {i + 1})"
        p = s.pose
        pr_pose = p.priority
        bits = []
        if p.overall:
            bits.append(p.overall)
        if p.torso_angle:
            bits.append(f"torso {p.torso_angle}")
        if p.head_tilt:
            bits.append(f"head {p.head_tilt}")
        if p.shoulders:
            bits.append(f"shoulders {p.shoulders}")
        if p.hips:
            bits.append(f"hips {p.hips}")
        if p.legs:
            bits.append(f"legs {p.legs}")
        if p.feet:
            bits.append(f"feet {p.feet}")
        if p.weight_distribution:
            bits.append(f"weight {p.weight_distribution}")
        if p.interaction_with_environment:
            bits.append(p.interaction_with_environment)
        if bits:
            _add(out, pr_pose, f"{label} pose: {', '.join(bits)}.")

        a = s.anatomy
        abits = [x for x in (a.body_type, a.proportions, a.visible_musculature, a.notes) if x]
        if abits:
            _add(out, a.priority, f"{label} body: {'; '.join(abits)}.")

        if s.hands:
            hb = "; ".join(
                h.description + (" (not visible)" if not h.visible else "") + (f" — {h.issues}" if h.issues else "")
                for h in s.hands
                if h.description or h.issues
            )
            if hb:
                _add(out, 1, f"{label} hands: {hb}.")

        f = s.face
        fbits = [
            x
            for x in (
                f.age_apparent,
                f.expression,
                f.gaze_direction,
                f.makeup,
                f.facial_hair,
                f.distinctive_features,
            )
            if x
        ]
        if fbits:
            _add(out, f.priority, f"{label} face: {'; '.join(fbits)}.")

        h = s.hair
        hbits = [x for x in (h.length, h.style, h.color, h.texture) if x]
        if hbits:
            _add(out, h.priority, f"{label} hair: {'; '.join(hbits)}.")

        sk = s.skin
        skbits = [x for x in (sk.tone, sk.texture, sk.lighting_interaction) if x]
        if skbits:
            _add(out, sk.priority, f"{label} skin: {'; '.join(skbits)}.")

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
                _add(out, w.priority, f"{label} wardrobe: {wb.strip()}.")

        for acc in s.accessories:
            if acc.text.strip():
                _add(out, acc.priority, f"{label} accessory: {acc.text.strip()}.")

        if s.notes.text.strip():
            _add(out, s.notes.priority, f"{label} notes: {s.notes.text.strip()}.")

    return out


def _global_sections(schema: VisionSchema) -> list[tuple[int, str]]:
    sec: list[tuple[int, str]] = []
    for line in schema.reproduction_critical:
        if line.strip():
            _add(sec, 1, f"Must preserve: {line.strip()}.")
    if schema.image_summary.strip():
        _add(sec, 2, schema.image_summary.strip())

    nh = schema.non_human_primary.text.strip()
    if nh:
        _add(sec, schema.non_human_primary.priority, f"Non-human primary focus: {nh}")

    c = schema.composition
    cb = [
        x
        for x in (
            c.framing,
            c.camera_height,
            c.angle,
            c.subject_placement,
            c.negative_space,
            c.leading_lines,
            c.aspect_ratio_hint,
        )
        if x
    ]
    if cb:
        _add(sec, c.priority, "Composition: " + "; ".join(cb) + ".")

    cam = schema.camera
    camb = [
        x
        for x in (
            cam.estimated_focal_length_mm and f"~{cam.estimated_focal_length_mm}mm lens feel",
            cam.aperture_f_stop and f"f/{cam.aperture_f_stop}",
            cam.depth_of_field,
            cam.bokeh,
            cam.lens_character,
            cam.sensor_format_hint,
        )
        if x
    ]
    if camb:
        _add(sec, cam.priority, "Camera/optics: " + "; ".join(camb) + ".")

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
    if lb:
        _add(sec, L.priority, "Lighting: " + "; ".join(lb) + ".")

    cg = schema.color_grade
    cgb = [x for x in (cg.palette, cg.saturation, cg.contrast_curve, cg.split_toning, cg.film_stock_or_lut_hint) if x]
    if cgb:
        _add(sec, cg.priority, "Color grade: " + "; ".join(cgb) + ".")

    r = schema.realism
    rb = [
        x
        for x in (r.grain, r.motion_blur, r.micro_asymmetry, r.skin_imperfections, r.fabric_wrinkles_dust_wear, r.optical_imperfections)
        if x
    ]
    if rb:
        _add(sec, r.priority, "Real-world imperfections: " + "; ".join(rb) + ".")

    e = schema.environment
    eb = [e.location_type, e.set_description, e.background_busyness, e.depth_layers]
    if e.props:
        eb.append("props: " + ", ".join(e.props))
    eb = [x for x in eb if x]
    if eb:
        _add(sec, e.priority, "Environment: " + "; ".join(eb) + ".")

    if schema.mood.text.strip():
        _add(sec, schema.mood.priority, f"Mood: {schema.mood.text.strip()}.")

    if schema.era_or_style.strip():
        _add(sec, 7, f"Era/style cue: {schema.era_or_style.strip()}.")

    if schema.medium != "unknown":
        _add(sec, 8, f"Medium read: {schema.medium}.")

    return sec


def _fit_token_budget(parts: list[tuple[int, str]], max_tokens: int, tokenizer_model_id: str) -> str:
    # Sort: low priority number first (more important), drop from end (least important)
    parts = sorted(parts, key=lambda x: (x[0], x[1]))
    work = parts[:]
    while work:
        text = " ".join(p[1] for p in work).strip()
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
    sections: list[tuple[int, str]] = []
    sections.extend(_global_sections(schema))
    sections.extend(_subject_sections(schema))

    body = _fit_token_budget(sections, max_tokens=max_tokens, tokenizer_model_id=tokenizer_model_id)
    if not body.strip():
        body = schema.image_summary.strip() or "Photoreal reproduction of the reference scene and subjects."
        body = _truncate_words(body, max_tokens, tokenizer_model_id)

    body = strip_banned_terms(body, schema.avoid_ai_cliches)
    body = naturalize(body)

    positive = (pr.positive_prefix + body + pr.positive_suffix).strip()
    positive = naturalize(positive)
    # Final safety truncate including prefix/suffix
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
