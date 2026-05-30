Analyze the attached reference image and emit the vision schema.

**Fill order (matches how the downstream prompt is assembled):**

1. **`reproduction_critical`** — 3–8 bullets: limbs (L/R), pose silhouette, camera angle/shot scale, 1–2 non‑negotiable background anchors.  
2. **Each `subjects[]` entry** — `pose` including **`arms_hands_lr`**; then anatomy; **`hands[]`** with Left/Right in text; face (gaze vs camera); hair; skin; wardrobe (material + color).  
3. **`composition`** — `shot_scale`, `framing`, `camera_height`, `angle`, placement, aspect hint.  
4. **`camera`** — focal length guess from {24,28,35,50,85,135}, DoF, bokeh, lens character.  
5. **`environment`** — **`weather_sky`**, `set_description` (foreground→background), `depth_layers`, `location_type`, props.  
6. **`lighting`** then **`color_grade`**.  
7. **`realism`**.  
8. **`image_summary`** — one paragraph, **no duplication** of fields above.  
9. **`mood`** / `era_or_style` only if grounded in pixels.

Remember: downstream **~512 token** budget — be dense, set `priority` **1** for anything identity- or pose-critical, **2** for camera+environment+light, **3–5** for color/realism/mood.
