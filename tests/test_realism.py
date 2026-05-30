from zref.compiler.realism import naturalize, strip_banned_terms


def test_naturalize_strips_hype() -> None:
    t = naturalize("A masterpiece 8k HDR render with perfect skin and cinematic lighting.")
    assert "masterpiece" not in t.lower()
    assert "8k" not in t.lower()
    assert "perfect skin" not in t.lower()


def test_strip_banned_terms_extra() -> None:
    t = strip_banned_terms("hello plastic skin world", ["plastic skin"])
    assert "plastic" not in t.lower()
