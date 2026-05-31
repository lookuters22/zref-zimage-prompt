Analyze the attached reference image and emit the vision schema.

**First**, draft **`image_summary`** as the **opening paragraph** (see system prompt: 3–6 long sentences, scenic envelope + vibe + light/optical finish). That paragraph is the main **hook** for the downstream model.

**Then** fill structured fields so they **agree** with that hook (no contradictions). Use this order:

1. `reproduction_critical`  
2. `subjects[]` (pose + `arms_hands_lr`, hands, face, hair, skin, wardrobe)  
3. `composition` + `camera`  
4. `environment` (`weather_sky`, `set_description`, `depth_layers`)  
5. `lighting` + `color_grade` + `realism`  
6. `mood` / `era_or_style` only if grounded  

Remember: downstream **~512 token** budget — be dense; set `priority` **1** for pose/limbs and identity, **2** for camera + environment + light.
