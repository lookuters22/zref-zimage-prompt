#!/usr/bin/env bash
# One-time persistent setup for zref on RunPod (or any ephemeral-container host).
#
# RunPod only persists the network volume (/workspace). Anything pip-installed
# into the container's site-packages disappears on a fresh pod. This script
# installs zref + deps into a folder ON THE VOLUME and links the ComfyUI node,
# so every future fresh pod works with zero extra steps (the node's bootstrap
# re-attaches the persistent deps dir to sys.path automatically).
#
# Run it ONCE from the repo root on the pod:
#   bash scripts/runpod_setup.sh
#
# Re-run it only after you change zref's dependencies or want to update.

set -euo pipefail

# --- config (override via env) ---------------------------------------------
ZREF_DEPS="${ZREF_DEPS:-/workspace/zref_deps}"
COMFY_DIR="${COMFY_DIR:-/workspace/runpod-slim/ComfyUI}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[zref] repo:        $REPO_DIR"
echo "[zref] deps target: $ZREF_DEPS"
echo "[zref] comfy dir:   $COMFY_DIR"

if [[ ! -f "$REPO_DIR/pyproject.toml" ]]; then
  echo "[zref] ERROR: $REPO_DIR does not look like the zref repo (no pyproject.toml)." >&2
  exit 1
fi

# --- 1. install zref + all deps into the persistent volume ------------------
mkdir -p "$ZREF_DEPS"
echo "[zref] installing into persistent volume (this can take a few minutes the first time)..."
python -m pip install --upgrade pip >/dev/null 2>&1 || true
python -m pip install --target "$ZREF_DEPS" "$REPO_DIR"

# --- 2. link the ComfyUI node into custom_nodes -----------------------------
if [[ -d "$COMFY_DIR/custom_nodes" ]]; then
  NODE_LINK="$COMFY_DIR/custom_nodes/zref_prompt"
  if [[ -e "$NODE_LINK" && ! -L "$NODE_LINK" ]]; then
    echo "[zref] $NODE_LINK exists (not a symlink); leaving it as-is."
  else
    ln -sfn "$REPO_DIR/comfy/zref_prompt" "$NODE_LINK"
    echo "[zref] linked node -> $NODE_LINK"
  fi
else
  echo "[zref] WARNING: $COMFY_DIR/custom_nodes not found. Set COMFY_DIR and re-run, or copy"
  echo "[zref]          comfy/zref_prompt into your ComfyUI custom_nodes manually."
fi

# --- 3. verify --------------------------------------------------------------
echo "[zref] verifying import..."
PYTHONPATH="$ZREF_DEPS:${PYTHONPATH:-}" python -c "import zref; print('[zref] OK ->', zref.__file__)"

cat <<EOF

[zref] Done.
       Persistent deps live in: $ZREF_DEPS
       On every fresh pod the node auto-adds that dir to sys.path, so you do NOT
       need to reinstall. If you ever move the volume, set ZREF_DEPS to match.
EOF
