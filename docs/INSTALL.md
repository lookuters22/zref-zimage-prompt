# Install zref (RunPod, ComfyUI, local)

## What you need

- **Python 3.10+** (same environment as ComfyUI on RunPod).
- **OpenAI API key** if you use the default provider (you can paste it in the Comfy node instead of env vars).

## Option A — RunPod / server with ComfyUI

### 1. Clone this repo

```bash
git clone https://github.com/lookuters22/zref-zimage-prompt.git
cd zref-zimage-prompt
```

(Replace the URL with the repo URL `gh` prints after creation.)

### 2. Install the Python package into Comfy’s Python

Use the **same** `python` / `pip` that launches ComfyUI (often a venv in the template):

```bash
pip install -e .
```

For development/tests:

```bash
pip install -e ".[dev]"
```

First run may download the **Qwen3-4B tokenizer** from Hugging Face (for token counting).

### 3. Install the ComfyUI custom node

Copy the `comfy/zref_prompt` folder so it lives as:

`ComfyUI/custom_nodes/zref_prompt/`

Example from the repo root:

```bash
cp -r comfy/zref_prompt /path/to/ComfyUI/custom_nodes/
```

Restart ComfyUI. You should see **ZRef Describe Image** under category **zref**.

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
| Node says `zref package not found` | `pip install -e .` with **ComfyUI’s** Python, then restart Comfy. |
| OpenAI errors | Check key, billing, and model name (`ZREF_OPENAI_MODEL`, default `gpt-4o`). |
| HF tokenizer download fails | Set `HF_TOKEN` if needed; or set `ZREF_TOKENIZER_MODEL_ID` to a local path after caching once. |
