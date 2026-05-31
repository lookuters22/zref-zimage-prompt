"""Build long-form reference-style prose (multi-paragraph) for Z-Image / Qwen.

Mimics strong human prompts: opening hook, dense subject/texture, layered place,
woven camera/optics, closing light/colour/finish — not field labels like
\"Composition:\".
"""

from __future__ import annotations

from zref.schema import Subject, VisionSchema


def _period(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    return s if s.endswith((".", "!", "?")) else s + "."


def paragraph_opening(schema: VisionSchema) -> str:
    """First paragraph: hook + stakes (reproduction_critical woven in)."""
    summary = (schema.image_summary or "").strip()
    anchors = [x.strip() for x in schema.reproduction_critical if x.strip()][:10]
    if len(summary) >= 80:
        base = summary.rstrip(".") + "."
        if anchors:
            base += (
                " Fidelity to the reference depends equally on "
                + ", ".join(anchors)
                + "."
            )
        return base

    e = schema.environment
    mood = (schema.mood.text or "").strip()
    bits: list[str] = []
    if e.location_type:
        bits.append(e.location_type.strip())
    if (e.weather_sky or "").strip():
        bits.append((e.weather_sky or "").strip())
    if e.set_description.strip():
        bits.append(e.set_description.strip())
    elif (e.depth_layers or "").strip():
        bits.append((e.depth_layers or "").strip())
    scene = " ".join(bits).strip()
    if not scene:
        scene = "a scene read straight from life with continuous foreground-to-background detail"
    lead = "This colour photograph captures "
    if mood and len(mood) < 90:
        lead += f"a {mood.rstrip('.')} feeling in "
    base = _period(lead + scene)
    if anchors:
        base += " " + _period(
            "Non-negotiable anchors drawn from the source include " + ", ".join(anchors)
        )
    return base


def _subject_prose(s: Subject) -> str:
    sentences: list[str] = []
    p = s.pose
    lr = (p.arms_hands_lr or "").strip()
    if lr:
        sentences.append(_period(lr))
    if (p.overall or "").strip():
        sentences.append(_period(p.overall))
    extra_pose = [
        x
        for x in (
            p.torso_angle and f"The torso reads as {p.torso_angle}",
            p.head_tilt and f"Head attitude: {p.head_tilt}",
            p.shoulders and f"Shoulders {p.shoulders}",
            p.hips and f"Hips {p.hips}",
            p.legs and f"Legs {p.legs}",
            p.feet and f"Feet {p.feet}",
            p.weight_distribution and f"Weight sits {p.weight_distribution}",
            p.interaction_with_environment,
        )
        if x
    ]
    for x in extra_pose:
        sentences.append(_period(x))

    a = s.anatomy
    abits = [x for x in (a.body_type, a.proportions, a.visible_musculature, a.notes) if x]
    if abits:
        sentences.append(_period("Physique and massing: " + "; ".join(abits)))

    if s.hands:
        for h in s.hands:
            if not (h.description or h.issues):
                continue
            frag = h.description.strip()
            if not h.visible:
                frag += " (partially hidden)"
            if h.issues:
                frag += f" — {h.issues}"
            sentences.append(_period(frag))

    f = s.face
    fbits = [x for x in (f.age_apparent, f.expression, f.gaze_direction, f.makeup, f.facial_hair, f.distinctive_features) if x]
    if fbits:
        sentences.append(_period("Face and gaze: " + "; ".join(fbits)))

    h = s.hair
    hbits = [x for x in (h.length, h.style, h.color, h.texture) if x]
    if hbits:
        sentences.append(_period("Hair reads as " + "; ".join(hbits)))

    sk = s.skin
    skbits = [x for x in (sk.tone, sk.texture, sk.lighting_interaction) if x]
    if skbits:
        sentences.append(_period("Skin shows " + "; ".join(skbits)))

    for w in s.wardrobe:
        wb = " ".join(
            p
            for p in (
                w.name,
                w.material and f"{w.material} cloth",
                w.color and f"colour {w.color}",
                w.pattern,
                w.fit and f"fit {w.fit}",
                w.details,
            )
            if p
        )
        if wb.strip():
            sentences.append(_period("Dressing includes " + wb.strip()))

    for acc in s.accessories:
        if acc.text.strip():
            sentences.append(_period(acc.text.strip()))

    if s.notes.text.strip():
        sentences.append(_period(s.notes.text.strip()))

    if not sentences:
        return ""
    return " ".join(sentences)


def paragraph_subjects(schema: VisionSchema) -> str:
    if not schema.subjects:
        nh = (schema.non_human_primary.text or "").strip()
        if nh:
            return _period("The frame revolves around " + nh)
        return ""
    parts: list[str] = []
    for i, subj in enumerate(schema.subjects):
        block = _subject_prose(subj)
        if block:
            parts.append(block)
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    # Second figure: natural hand-off like the reference prompts
    out = parts[0]
    for p in parts[1:]:
        out += " " + p
    return out


def paragraph_place(schema: VisionSchema) -> str:
    e = schema.environment
    sents: list[str] = []
    if (e.depth_layers or "").strip() and (e.set_description or "").strip():
        dl = (e.depth_layers or "").strip().rstrip(".")
        sd = (e.set_description or "").strip().rstrip(".")
        sents.append(_period(f"Spatial depth stacks as {dl}: {sd}"))
    elif (e.set_description or "").strip():
        sents.append(_period((e.set_description or "").strip()))
    elif (e.depth_layers or "").strip():
        sents.append(_period("Layering across distance reads as " + (e.depth_layers or "").strip()))
    if (e.background_busyness or "").strip():
        sents.append(_period((e.background_busyness or "").strip()))
    if e.props:
        sents.append(
            _period("Notable props and set dressing include " + ", ".join(e.props[:16]))
        )
    if not sents:
        return ""
    return " ".join(sents)


def paragraph_camera(schema: VisionSchema) -> str:
    c = schema.composition
    cam = schema.camera
    view_bits = [x for x in (c.shot_scale, c.framing, c.camera_height, c.angle) if x]
    place_bits = [x for x in (c.subject_placement, c.negative_space, c.leading_lines) if x]
    asp = (c.aspect_ratio_hint or "").strip()
    sents: list[str] = []
    if view_bits or place_bits:
        a = ", ".join(view_bits) if view_bits else ""
        b = "; ".join(place_bits) if place_bits else ""
        core = "The perspective reads as " + (a if a else "a deliberate still-camera read")
        if b:
            core += ", with " + b
        if asp:
            core += f", inside roughly a {asp} frame feel"
        sents.append(_period(core))
    opt_bits = [
        x
        for x in (
            cam.estimated_focal_length_mm and f"a ~{cam.estimated_focal_length_mm}mm field of view",
            cam.aperture_f_stop and f"around f/{cam.aperture_f_stop}",
            cam.depth_of_field,
            cam.bokeh,
            cam.lens_character,
            cam.sensor_format_hint,
        )
        if x
    ]
    if opt_bits:
        sents.append(
            _period(
                "Optical behaviour suggests "
                + ", ".join(opt_bits)
                + ", so materials and distance collapse the way glass and air actually would"
            )
        )
    if not sents:
        return ""
    return " ".join(sents)


def paragraph_finish(schema: VisionSchema) -> str:
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
    sents: list[str] = []
    if lb:
        sents.append(_period("Light in the scene behaves as " + "; ".join(lb)))
    if cgb:
        sents.append(_period("Colour and contrast read as " + "; ".join(cgb)))
    if rb:
        sents.append(
            _period(
                "Surface and camera honesty show up as "
                + "; ".join(rb)
                + ", so nothing reads as plastic perfection"
            )
        )
    era = (schema.era_or_style or "").strip()
    if era:
        sents.append(_period("Overall period or treatment cue: " + era))
    if schema.medium != "unknown" and schema.medium != "photo":
        sents.append(_period(f"Medium classification: {schema.medium}"))
    if not sents:
        return ""
    return " ".join(sents)


def build_reference_style_paragraphs(schema: VisionSchema) -> list[str]:
    """Ordered paragraphs; trim from the end of this list when over token budget."""
    paras: list[str] = []
    o = paragraph_opening(schema)
    if o:
        paras.append(o)
    su = paragraph_subjects(schema)
    if su:
        paras.append(su)
    pl = paragraph_place(schema)
    if pl:
        paras.append(pl)
    ca = paragraph_camera(schema)
    if ca:
        paras.append(ca)
    fi = paragraph_finish(schema)
    if fi:
        paras.append(fi)
    nh = (schema.non_human_primary.text or "").strip()
    if nh and schema.subjects:
        paras.append(_period("Parallel emphasis on non-person elements: " + nh))
    return [p.strip() for p in paras if p.strip()]


def join_paragraphs(paras: list[str]) -> str:
    return "\n\n".join(paras).strip()
