# zref — Z-Image reference → prompt

Turn a **reference image** into a **natural-language prompt** tuned for **Z-Image / Z-Image Turbo** (DiT + **Qwen3-4B** text encoder): pose, wardrobe, lighting, camera/optics, color grade, and **non-AI-looking** photoreal cues.

**Install (RunPod / ComfyUI / local):** see **[docs/INSTALL.md](docs/INSTALL.md)**.  
**Create & push this repo to GitHub:** see **[docs/GITHUB_SETUP.md](docs/GITHUB_SETUP.md)** (GitHub CLI not required).

## Features

- **Structured extraction** via cloud VLMs (OpenAI, Anthropic, Gemini) with JSON schema validation
- **Token-budgeted compiler** (~512 encoder tokens) using the **Qwen3-4B** tokenizer
- **CLI**, **FastAPI** (`POST /describe`), **ComfyUI** nodes
- Optional **eval** harness (CLIP / DINOv2 similarity) — install with `pip install zref[eval]`

## Install

```bash
pip install -e ".[dev]"
```

Set API keys (never commit):

```bash
export OPENAI_API_KEY=...   # default provider uses OpenAI
export ANTHROPIC_API_KEY=... # optional
export GOOGLE_API_KEY=...   # optional (Gemini)
```

## CLI

```bash
zref describe path/to/ref.jpg --out ./out
zref describe ./refs/ --batch --preset editorial
```

## API

```bash
uvicorn zref.api.server:app --host 0.0.0.0 --port 8765
```

`POST /describe` — multipart `file` + optional `provider`, `preset`, `max_prompt_tokens`.

## ComfyUI

Copy `comfy/zref_prompt` into `ComfyUI/custom_nodes/` (see [comfy/zref_prompt/README.md](comfy/zref_prompt/README.md)).

## Z-Image notes

- Prefer **prose**, not tag-soup.
- **Turbo**: negative conditioning is weak; bake realism into the **positive** prompt.
- Default **max_prompt_tokens** is **480** (headroom under typical 512 truncation).

## Configuration

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` / `ZREF_OPENAI_API_KEY` | OpenAI |
| `ANTHROPIC_API_KEY` / `ZREF_ANTHROPIC_API_KEY` | Anthropic |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` / `ZREF_GOOGLE_API_KEY` | Gemini |
| `ZREF_DEFAULT_PROVIDER` | `openai` (default), `anthropic`, or `gemini` |
| `ZREF_MAX_PROMPT_TOKENS` | Default **480** |
| `ZREF_TOKENIZER_MODEL_ID` | HF id for token counting (default `Qwen/Qwen3-4B`) |
| `ZREF_CACHE_DIR` | Optional disk cache for VLM JSON |
| `ZREF_API_KEY` | Optional Bearer token for `POST /describe` |

## Layout

- Python package: [`src/zref/`](src/zref/)
- ComfyUI nodes (copy to `custom_nodes/`): [`comfy/zref_prompt/`](comfy/zref_prompt/)

## Eval (optional)

```bash
pip install -e ".[eval]"
```

Use `zref.eval.compare_pair(ref_pil, gen_pil)` for CLIP / DINOv2 cosine similarity.

## License

MIT
