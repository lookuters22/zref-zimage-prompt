"""Replace AI-slop vocabulary with photographic language."""

from __future__ import annotations

import re

# Lowercase keys; matched as word-ish boundaries
_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bcinematic lighting\b", re.I), "controlled studio-style lighting with believable falloff"),
    (re.compile(r"\b8k\b|\bultra hd\b|\bhyper[- ]?detailed\b", re.I), "high microcontrast fine detail"),
    (re.compile(r"\bmasterpiece\b|\bbest quality\b|\baward winning\b", re.I), ""),
    (re.compile(r"\bsharp focus everywhere\b|\beverything in focus\b", re.I), "depth of field consistent with the lens"),
    (re.compile(r"\bperfect skin\b|\bflawless skin\b", re.I), "natural skin texture with visible pores where lit"),
    (re.compile(r"\bhdr\b|\bhyper[- ]?real\b", re.I), "natural highlight rolloff"),
    (re.compile(r"\bsymmetrical face\b|\bperfect symmetry\b", re.I), "natural facial asymmetry"),
    (re.compile(r"\banime\b|\b3d render\b|\bcgi\b", re.I), "photograph"),
]

# Strip if standalone phrases
_STRIP_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(ambient occlusion|ray tracing|unreal engine|octane render)\b", re.I),
]


def naturalize(text: str) -> str:
    t = text
    for pat, rep in _REPLACEMENTS:
        t = pat.sub(rep, t)
    for pat in _STRIP_PATTERNS:
        t = pat.sub("", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    t = re.sub(r"\s+,", ",", t)
    return t


def strip_banned_terms(text: str, extra_banned: list[str] | None = None) -> str:
    t = text
    if extra_banned:
        for term in extra_banned:
            if not term.strip():
                continue
            t = re.sub(re.escape(term), "", t, flags=re.I)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t
