from zref.cache import make_cache_key, read_cache, write_cache
from zref.schema import VisionSchema


def test_cache_roundtrip(tmp_path) -> None:
    b = b"abc"
    k = make_cache_key(b, {"a": 1})
    assert len(k) == 64
    payload = {"schema": VisionSchema().model_dump(), "provider": "gemini"}
    write_cache(tmp_path, k, payload)
    got = read_cache(tmp_path, k)
    assert got is not None
    assert got["provider"] == "gemini"
