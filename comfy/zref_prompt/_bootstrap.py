"""Make the `zref` package importable on ephemeral RunPod containers.

RunPod only persists the network volume (usually ``/workspace``). Anything
``pip install``ed into the container's own Python site-packages is wiped every
time you launch a fresh pod, which is why the node keeps "losing" zref.

This module fixes that by keeping zref + its dependencies on the persistent
volume and re-attaching them to ``sys.path`` on every ComfyUI start:

  1. Add a persistent deps dir (default ``/workspace/zref_deps``, override with
     ``ZREF_DEPS``) to ``sys.path``.
  2. Add the repo ``src/`` dir (so ``zref`` itself is importable) if present.
  3. If ``import zref`` still fails, do a ONE-TIME ``pip install --target`` into
     the persistent deps dir. Subsequent fresh pods then import instantly with
     no reinstall, because the deps dir lives on the persistent volume.

You normally only run an install once (manually via scripts/runpod_setup.sh or
automatically the first time). After that it survives fresh pods for free.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys

LOGGER = logging.getLogger("zref_prompt.bootstrap")

_NODE_DIR = os.path.dirname(os.path.abspath(__file__))


def _persistent_deps_dir() -> str:
    env = os.environ.get("ZREF_DEPS")
    if env:
        return env
    # RunPod's persistent volume is /workspace; fall back to home otherwise.
    if os.path.isdir("/workspace"):
        return "/workspace/zref_deps"
    return os.path.join(os.path.expanduser("~"), ".zref_deps")


def _candidate_src_dirs() -> list[str]:
    cands: list[str] = []
    env = os.environ.get("ZREF_SRC")
    if env:
        cands.append(env)
    # Node copied/symlinked while still inside the repo: comfy/zref_prompt -> repo/src
    cands.append(os.path.normpath(os.path.join(_NODE_DIR, "..", "..", "src")))
    # Common clone locations on RunPod / Linux.
    for base in ("/workspace", os.path.expanduser("~")):
        cands.append(os.path.join(base, "zref-zimage-prompt", "src"))
    return cands


def _repo_root() -> str | None:
    """Find a checkout we can pip-install zref from (must contain pyproject.toml)."""
    cands: list[str] = []
    env = os.environ.get("ZREF_REPO")
    if env:
        cands.append(env)
    cands.append(os.path.normpath(os.path.join(_NODE_DIR, "..", "..")))
    for base in ("/workspace", os.path.expanduser("~")):
        cands.append(os.path.join(base, "zref-zimage-prompt"))
    for c in cands:
        if c and os.path.isfile(os.path.join(c, "pyproject.toml")):
            return c
    return None


def _add_path(p: str) -> None:
    if p and os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)


def _can_import_zref() -> bool:
    try:
        import importlib

        importlib.invalidate_caches()
        import zref  # noqa: F401

        return True
    except Exception:  # pragma: no cover - runtime probe
        return False


def _auto_install(deps_dir: str) -> bool:
    repo = _repo_root()
    if repo is None:
        LOGGER.error(
            "zref not found and no repo checkout to install from. "
            "Clone https://github.com/lookuters22/zref-zimage-prompt.git to /workspace, "
            "or set ZREF_REPO / ZREF_DEPS."
        )
        return False
    os.makedirs(deps_dir, exist_ok=True)
    cmd = [sys.executable, "-m", "pip", "install", "--target", deps_dir, repo]
    LOGGER.warning("zref deps missing -> one-time install into %s: %s", deps_dir, " ".join(cmd))
    try:
        subprocess.check_call(cmd)
    except Exception as e:  # pragma: no cover - runtime install
        LOGGER.error("zref auto-install failed: %s", e)
        return False
    _add_path(deps_dir)
    return _can_import_zref()


def ensure_zref(auto_install: bool = True) -> bool:
    """Best-effort make `import zref` work. Returns True if importable afterwards."""
    deps_dir = _persistent_deps_dir()
    _add_path(deps_dir)
    for src in _candidate_src_dirs():
        if os.path.isdir(os.path.join(src, "zref")):
            _add_path(src)
            break

    if _can_import_zref():
        return True

    if not auto_install:
        return False

    # Allow opting out of the in-process install (e.g. ZREF_NO_AUTOINSTALL=1).
    if os.environ.get("ZREF_NO_AUTOINSTALL"):
        LOGGER.error("zref not importable and ZREF_NO_AUTOINSTALL is set; skipping auto-install.")
        return False

    return _auto_install(deps_dir)
