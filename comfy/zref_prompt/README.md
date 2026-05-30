# zref_prompt (ComfyUI)

Custom nodes that call the **`zref`** Python package: reference **IMAGE** tensor → **positive** / **negative** / **schema JSON** strings for Z-Image (Qwen3-4B text encoder).

## Install

1. Install `zref` into the **same Python** ComfyUI uses:

   ```bash
   pip install -e /path/to/this/repo
   ```

2. Copy this folder to `ComfyUI/custom_nodes/zref_prompt/` (so `__init__.py` lives there).

3. Set **`OPENAI_API_KEY`** in the environment (default provider is OpenAI), or use Anthropic/Gemini keys / node fields if you switch provider.

## Nodes

- **ZRef Describe Image** — `IMAGE` + provider/preset/max tokens → `STRING` outputs.

## Z-Image Turbo note

Negative prompts have **little effect** on Turbo. Prefer baking realism into the **positive** string; for negative you can use **ConditioningZeroOut** on the negative input per upstream guidance.
