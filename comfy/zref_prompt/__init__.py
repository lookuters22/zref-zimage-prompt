"""ComfyUI custom node registration."""

# Make `zref` importable from the persistent volume BEFORE nodes.py imports it.
# (RunPod wipes the container's site-packages on every fresh pod.)
from ._bootstrap import ensure_zref

ensure_zref()

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
