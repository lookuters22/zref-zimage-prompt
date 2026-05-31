"""VisionSchema → Z-Image natural-language prompt with token budget.

Uses **multi-paragraph literary prose** (reference-style hooks, layered scenery,
woven optics) tuned for Qwen-style encoders — see `narrative_prose.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

from zref.compiler import narrative_prose as narr
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


def _fit_paragraphs(paras: list[str], max_tokens: int, tokenizer_model_id: str) -> str:
    """Drop whole paragraphs from the end first (keeps opening + subject longest)."""
    work = paras[:]
    while work:
        text = narr.join_paragraphs(work)
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
    paras = narr.build_reference_style_paragraphs(schema)
    body = _fit_paragraphs(paras, max_tokens=max_tokens, tokenizer_model_id=tokenizer_model_id)
    if not body.strip():
        body = schema.image_summary.strip() or "Photoreal reproduction of the reference scene and subjects."
        body = _truncate_words(body, max_tokens, tokenizer_model_id)
    else:
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
