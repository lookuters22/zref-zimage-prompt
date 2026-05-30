"""zref: reference image → Z-Image (Qwen3-4B) prompts."""

__version__ = "0.1.0"

from zref.pipeline import PromptResult, describe_image, describe_image_sync, serialize_result

__all__ = ["__version__", "PromptResult", "describe_image", "describe_image_sync", "serialize_result"]
