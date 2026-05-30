"""Typer CLI."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from PIL import Image

from zref.config import ProviderName, get_settings
from zref.logging import configure_logging
from zref.pipeline import describe_image, serialize_result

app = typer.Typer(no_args_is_help=True, help="Z-Image reference → prompt toolkit")


def _mime_for_path(p: Path) -> str:
    suf = p.suffix.lower()
    if suf in (".jpg", ".jpeg"):
        return "image/jpeg"
    if suf == ".png":
        return "image/png"
    if suf == ".webp":
        return "image/webp"
    return "image/jpeg"


def _load_image(path: Path) -> tuple[bytes, str]:
    mime = _mime_for_path(path)
    if mime == "image/jpeg":
        return path.read_bytes(), mime
    im = Image.open(path).convert("RGB")
    import io

    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=92)
    return buf.getvalue(), "image/jpeg"


@app.command("describe")
def describe_cmd(
    path: Path = typer.Argument(..., exists=True, help="Image file or directory"),
    out: Path = typer.Option(Path("out"), "--out", "-o", help="Output directory"),
    batch: bool = typer.Option(False, "--batch", "-b", help="Treat path as directory of images"),
    provider: ProviderName | None = typer.Option(None, "--provider", "-p"),
    preset: str = typer.Option("default", "--preset"),
    max_tokens: int | None = typer.Option(None, "--max-tokens"),
    no_cache: bool = typer.Option(False, "--no-cache"),
) -> None:
    configure_logging()
    s = get_settings()
    paths: list[Path]
    if batch:
        exts = {".jpg", ".jpeg", ".png", ".webp"}
        paths = sorted([p for p in path.iterdir() if p.suffix.lower() in exts])
        if not paths:
            raise typer.BadParameter(f"No images found in {path}")
    else:
        paths = [path]

    async def run_one(p: Path) -> None:
        data, mime = _load_image(p)
        res = await describe_image(
            data,
            mime,
            settings=s,
            provider=provider,
            preset=preset,
            max_prompt_tokens=max_tokens,
            use_cache=not no_cache,
        )
        serialize_result(res, out, p.stem)
        typer.echo(f"Wrote {out / (p.stem + '.txt')} ({res.token_count} tokens)")

    async def run_all() -> None:
        for p in paths:
            await run_one(p)

    asyncio.run(run_all())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
