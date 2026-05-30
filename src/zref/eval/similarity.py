"""Optional reference vs generated similarity (install `zref[eval]`)."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image


@dataclass
class SimilarityReport:
    clip_cosine: float | None = None
    dinov2_cosine: float | None = None
    notes: str = ""


def _to_rgb(pil: Image.Image) -> Image.Image:
    return pil.convert("RGB")


def clip_cosine_similarity(ref: Image.Image, gen: Image.Image) -> float:
    """Cosine similarity of CLIP image embeddings."""
    try:
        import open_clip
        import torch
    except ImportError as e:  # pragma: no cover
        raise ImportError("CLIP eval requires: pip install zref[eval]") from e

    model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
    model.eval()

    def embed(pil: Image.Image) -> "torch.Tensor":
        im = preprocess(_to_rgb(pil)).unsqueeze(0)
        with torch.no_grad():
            f = model.encode_image(im)
            f = f / f.norm(dim=-1, keepdim=True)
        return f

    a = embed(ref)
    b = embed(gen)
    return float((a * b).sum().item())


def dinov2_cosine_similarity(ref: Image.Image, gen: Image.Image) -> float:
    """Cosine similarity on a DINOv2 ViT via timm (feature mode)."""
    try:
        import timm
        import torch
        import torchvision.transforms as T
    except ImportError as e:  # pragma: no cover
        raise ImportError("DINO eval requires: pip install zref[eval]") from e

    names = [
        "vit_small_patch14_dinov2.lvd142m",
        "vit_small_patch14_reg4_dinov2.lvd142m",
    ]
    model = None
    for n in names:
        try:
            model = timm.create_model(n, pretrained=True, num_classes=0)
            break
        except Exception:
            continue
    if model is None:
        raise RuntimeError("No DINOv2 timm model could be loaded")

    model.eval()
    tfm = T.Compose(
        [
            T.Resize(224, interpolation=T.InterpolationMode.BICUBIC),
            T.CenterCrop(224),
            T.ToTensor(),
            T.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ]
    )

    def embed(pil: Image.Image) -> "torch.Tensor":
        t = tfm(_to_rgb(pil)).unsqueeze(0)
        with torch.no_grad():
            f = model(t)
            f = f / f.norm(dim=-1, keepdim=True)
        return f

    a = embed(ref)
    b = embed(gen)
    return float((a * b).sum().item())


def compare_pair(ref: Image.Image, gen: Image.Image) -> SimilarityReport:
    notes: list[str] = []
    clip_v: float | None = None
    dinov2_v: float | None = None
    try:
        clip_v = clip_cosine_similarity(ref, gen)
    except Exception as e:  # pragma: no cover
        notes.append(f"clip_skipped: {e}")
    try:
        dinov2_v = dinov2_cosine_similarity(ref, gen)
    except Exception as e:  # pragma: no cover
        notes.append(f"dinov2_skipped: {e}")
    return SimilarityReport(clip_cosine=clip_v, dinov2_cosine=dinov2_v, notes="; ".join(notes))
