"""Lazy Qwen3 tokenizer for token budgeting."""

from __future__ import annotations

from functools import lru_cache

from transformers import AutoTokenizer


@lru_cache(maxsize=4)
def get_qwen_tokenizer(model_id: str):
    return AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)


def count_tokens(text: str, model_id: str) -> int:
    if not text.strip():
        return 0
    tok = get_qwen_tokenizer(model_id)
    return len(tok.encode(text, add_special_tokens=False))
