#!/usr/bin/env python3
"""Green-screen chroma key + optional rembg / near-white cutout → transparent PNG."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def chroma_key_green(
    img: Image.Image,
    key_rgb=(0, 255, 0),
    soft: float = 18.0,
    hard: float = 95.0,
) -> Image.Image:
    rgba = img.convert("RGBA")
    arr = np.asarray(rgba).astype(np.float32)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    kr, kg, kb = key_rgb

    dist = np.sqrt((r - kr) ** 2 + (g - kg) ** 2 + (b - kb) ** 2)
    greenness = g - np.maximum(r, b)
    is_screen = ((greenness > 35) & (g > 120)) | ((dist < 90) & (g > 150) & (greenness > 15))

    g_alpha = np.clip(1.0 - (greenness - 30) / 55.0, 0.0, 1.0)
    d_alpha = np.clip((dist - soft) / max(hard - soft, 1e-6), 0.0, 1.0)
    alpha = np.ones(g.shape, dtype=np.float32)
    alpha = np.where(is_screen, np.minimum(g_alpha, d_alpha), alpha)
    alpha = np.where(greenness > 80, 0.0, alpha)
    alpha = np.where(dist < soft, 0.0, alpha)

    out = arr.copy()
    out[..., 3] = alpha * 255.0
    edge = (out[..., 3] > 5) & (out[..., 3] < 250) & (greenness > 8)
    target = (r + b) * 0.5
    out[..., 1] = np.where(edge, np.minimum(g, target + 8), out[..., 1])
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def autocrop(img: Image.Image, pad: int = 8) -> Image.Image:
    bbox = img.split()[-1].getbbox()
    if not bbox:
        return img
    l, t, r, b = bbox
    return img.crop(
        (
            max(0, l - pad),
            max(0, t - pad),
            min(img.width, r + pad),
            min(img.height, b + pad),
        )
    )


def remove_white_bg(img: Image.Image, thresh: int = 245, soft: int = 12) -> Image.Image:
    rgba = img.convert("RGBA")
    arr = np.asarray(rgba).astype(np.float32)
    rgb = arr[..., :3]
    mn = rgb.min(axis=-1)
    mx = rgb.max(axis=-1)
    near_white = (mn >= thresh - soft) & ((mx - mn) < 18)
    alpha = np.ones(mn.shape, dtype=np.float32)
    alpha = np.where(near_white & (mn >= thresh), 0.0, alpha)
    mid = near_white & (mn < thresh)
    alpha = np.where(mid, np.clip((thresh - mn) / soft, 0, 1), alpha)
    grayish = ((mx - mn) < 12) & (mn > 200) & (mn < thresh)
    alpha = np.where(grayish, np.clip((thresh - mn) / 40.0, 0.05, 0.55), alpha)
    out = arr.copy()
    out[..., 3] = (alpha * 255).astype(np.float32)
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def try_rembg(img: Image.Image) -> Image.Image | None:
    try:
        from rembg import remove
    except Exception:
        return None
    try:
        return remove(img.convert("RGBA"))
    except Exception as exc:
        print(f"rembg failed ({exc}); falling back to near-white removal")
        return None


def process_one(path: Path, out_dir: Path, mode: str) -> Path:
    img = Image.open(path)
    stem = path.stem.lower()
    if mode == "green" or "greenscreen" in stem or "green" in stem:
        cut = chroma_key_green(img)
        tag = "chroma"
    elif mode == "rembg":
        cut = try_rembg(img)
        if cut is None:
            cut = remove_white_bg(img)
            tag = "white-fallback"
        else:
            tag = "rembg"
    else:
        if "green" in stem:
            cut = chroma_key_green(img)
            tag = "chroma"
        else:
            cut = try_rembg(img)
            if cut is None:
                cut = remove_white_bg(img)
                tag = "white-fallback"
            else:
                tag = "rembg"

    cut = autocrop(cut, pad=10)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{path.stem}_transparent_{tag}.png"
    cut.save(out, "PNG")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Cut green/white sticker sheets to transparent PNG")
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument(
        "-o",
        "--out",
        type=Path,
        default=Path("transparent_assets"),
        help="Output directory (default: ./transparent_assets)",
    )
    ap.add_argument("--mode", choices=["auto", "green", "rembg"], default="auto")
    args = ap.parse_args()

    outs = []
    for p in args.inputs:
        if not p.exists():
            print(f"skip missing: {p}")
            continue
        o = process_one(p, args.out, args.mode)
        print(f"OK [{args.mode}] {p.name} -> {o}")
        outs.append(o)
    print(f"done: {len(outs)} files -> {args.out.resolve()}")


if __name__ == "__main__":
    main()
