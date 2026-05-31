# Install zref (RunPod, ComfyUI, local)

## What you need

- **Python 3.10+** (same environment as ComfyUI on RunPod).
- **OpenAI API key** if you use the default provider (you can paste it in the Comfy node instead of env vars).

## Option A — RunPod / ephemeral container with ComfyUI (PERSISTENT, recommended)

> **Why the node keeps disappearing on a fresh pod:** RunPod only persists the
> **network volume** (usually `/workspace`). Anything you `pip install` goes into the
> **container's** Python site-packages, which is **wiped** every time you start a fresh pod.
> The fix is to keep `zref` + its deps **on the volume** and let the node re-attach them on
> every boot. You then install **once**.

### 1. Clone the repo onto the volume

Clone somewhere under `/workspace` so it persists:

```bash
cd /workspace
git clone https://github.com/lookuters22/zref-zimage-prompt.git
cd zref-zimage-prompt
```

### 2. Run the one-time persistent setup

```bash
bash scripts/runpod_setup.sh
```

This:
- installs `zref` + all dependencies into **`/workspace/zref_deps`** (on the persistent volume),
- symlinks `comfy/zref_prompt` into `ComfyUI/custom_nodes/`,
- verifies `import zref` works.

Override locations with env vars if your paths differ:

```bash
ZREF_DEPS=/workspace/zref_deps COMFY_DIR=/workspace/runpod-slim/ComfyUI bash scripts/runpod_setup.sh
```

Restart ComfyUI. You should see **ZRef Describe Image** under category **zref**.

### 3. Fresh pods from now on — nothing to do

On every new pod the node's bootstrap (`comfy/zref_prompt/_bootstrap.py`) automatically adds
`/workspace/zref_deps` (and the repo `src/`) to `sys.path`, so `zref` imports instantly with
**no reinstall**. If `zref_deps` is ever empty/missing, the node will do a one-time
`pip install --target` from the repo automatically the first time ComfyUI loads it.

> Tip: keep both the repo **and** `zref_deps` under `/workspace`. If you change the deps,
> re-run `scripts/runpod_setup.sh`. To disable the in-process auto-install, set
> `ZREF_NO_AUTOINSTALL=1`.

### Non-persistent / quick alternative

If you don't care about persistence (e.g. a throwaway local box), just install into the active
Python that launches ComfyUI:

```bash
pip install -e .          # editable
# or
pip install -e ".[dev]"   # with test deps
```

First run may download the **Qwen3-4B tokenizer** from Hugging Face (for token counting).

### 4. API key in the node (your choice)

On **ZRef Describe Image**:

1. Set **provider** to `openai` (default).
2. Paste your key into **`openai_api_key`** on the node.

Do **not** commit workflows that contain the key. Anyone with the workflow JSON can read it.

**Alternative (more secure on shared pods):** leave the node field empty and set:

```bash
export OPENAI_API_KEY="sk-..."
```

before starting ComfyUI.

### 5. CLI (optional)

```bash
zref describe /path/to/ref.jpg --out ./out
```

### 6. HTTP API (optional)

```bash
uvicorn zref.api.server:app --host 0.0.0.0 --port 8765
```

## Option B — Only the library (no Comfy)

```bash
pip install -e .
python -c "from zref import describe_image_sync; print('ok')"
```

## Troubleshooting

| Issue | What to try |
|--------|----------------|
| Node says `zref package not found` | On RunPod use the persistent setup (Option A): `bash scripts/runpod_setup.sh`. Otherwise `pip install -e .` with **ComfyUI’s** Python, then restart Comfy. |
| Works, then gone after a fresh pod | You installed into the container (ephemeral). Run `scripts/runpod_setup.sh` so deps live in `/workspace/zref_deps` on the persistent volume. |
| OpenAI errors | Check key, billing, and model name (`ZREF_OPENAI_MODEL`, default `gpt-4o`). |
| HF tokenizer download fails | Set `HF_TOKEN` if needed; or set `ZREF_TOKENIZER_MODEL_ID` to a local path after caching once. |
