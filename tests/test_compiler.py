from zref.compiler.zimage import compile_zimage_prompt
from zref.schema import (
    CompositionDetail,
    FaceDetail,
    PoseDetail,
    RealismCues,
    Subject,
    VisionSchema,
)


def test_compiler_respects_budget() -> None:
    # Tight budget with fake tokenizer (chars/4 from conftest)
    subj = Subject(
        pose=PoseDetail(overall="x" * 2000, priority=1),
        face=FaceDetail(expression="y" * 2000, priority=2),
    )
    schema = VisionSchema(
        image_summary="z" * 4000,
        subjects=[subj],
        composition=CompositionDetail(framing="wide", priority=3),
        realism=RealismCues(grain="fine", priority=3),
    )
    out = compile_zimage_prompt(schema, preset="default", max_tokens=120, tokenizer_model_id="dummy")
    assert out.token_count <= 120
    assert len(out.positive) > 0


def test_preset_prefix() -> None:
    schema = VisionSchema(image_summary="One person outdoors.")
    out = compile_zimage_prompt(schema, preset="candid", max_tokens=500, tokenizer_model_id="dummy")
    assert "Candid" in out.positive or "candid" in out.positive.lower()
