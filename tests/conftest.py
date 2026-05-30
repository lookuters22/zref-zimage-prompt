import pytest


@pytest.fixture(autouse=True)
def fake_token_count(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid downloading Qwen tokenizer during unit tests."""

    import zref.compiler.tokenizer_util as tu

    def fake_count(text: str, model_id: str) -> int:
        if not text.strip():
            return 0
        # Deterministic proxy: ~1 token per 4 characters
        return max(1, (len(text) + 3) // 4)

    monkeypatch.setattr(tu, "count_tokens", fake_count)
