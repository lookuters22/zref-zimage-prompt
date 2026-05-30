Analyze the attached reference image and emit the vision schema.

Focus order:
1) Human subjects: pose, anatomy, hands, face, hair, skin, wardrobe materials/colors.
2) Composition and camera optics.
3) Lighting and color grade.
4) Environment and props.
5) Mood (only if visually grounded).

Remember: the consumer model is a **text-to-image** system with a **~512 token** text budget downstream—be dense, avoid redundancy, and rank importance via each section's `priority` fields (1 = most critical).
