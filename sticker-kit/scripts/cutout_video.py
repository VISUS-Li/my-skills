#!/usr/bin/env python3
"""Extract a Wan clip to a stable-canvas RGBA PNG sequence."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def parse_color(value: str) -> tuple[int, int, int]:
    text = value.strip().lstrip("#")
    if len(text) != 6:
        raise ValueError("color must be #RRGGBB")
    return tuple(int(text[i : i + 2], 16) for i in (0, 2, 4))


def smoothstep(value: np.ndarray, lo: float, hi: float) -> np.ndarray:
    t = np.clip((value - lo) / max(hi - lo, 1e-6), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def chroma_rgba(
    image: Image.Image,
    key_rgb: tuple[int, int, int],
    inner: float,
    outer: float,
    despill: float,
) -> Image.Image:
    arr = np.asarray(image.convert("RGB"), dtype=np.float32)
    key = np.asarray(key_rgb, dtype=np.float32)
    distance = np.linalg.norm(arr - key, axis=-1) / np.sqrt(3.0 * 255.0 * 255.0)
    alpha = smoothstep(distance, inner, outer)
    out = np.dstack((arr, alpha * 255.0))

    dominant = int(np.argmax(key))
    if key[dominant] > 220 and np.count_nonzero(key > 80) == 1 and despill > 0:
        other = [i for i in range(3) if i != dominant]
        neutral = np.maximum(arr[..., other[0]], arr[..., other[1]])
        edge = (alpha > 0.0) & (alpha < 1.0)
        reduced = arr[..., dominant] * (1.0 - despill) + neutral * despill
        out[..., dominant] = np.where(edge, np.minimum(arr[..., dominant], reduced), arr[..., dominant])
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def luma_rgba(image: Image.Image, black: float, white: float, gamma: float) -> Image.Image:
    arr = np.asarray(image.convert("RGB"), dtype=np.float32)
    luminance = np.max(arr, axis=-1) / 255.0
    alpha = smoothstep(luminance, black, white) ** max(gamma, 1e-3)
    return Image.fromarray(
        np.clip(np.dstack((arr, alpha * 255.0)), 0, 255).astype(np.uint8), "RGBA"
    )


def pixel_lock(image: Image.Image, grid: int) -> Image.Image:
    if grid <= 1:
        return image
    width, height = image.size
    small = image.resize(
        (max(1, round(width / grid)), max(1, round(height / grid))),
        Image.Resampling.NEAREST,
    )
    return small.resize((width, height), Image.Resampling.NEAREST)


def alpha_bbox(image: Image.Image, threshold: int = 8) -> tuple[int, int, int, int] | None:
    alpha = np.asarray(image.getchannel("A"))
    ys, xs = np.where(alpha > threshold)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def union_bbox(boxes: list[tuple[int, int, int, int]], size: tuple[int, int], pad: int) -> tuple[int, int, int, int]:
    if not boxes:
        return 0, 0, size[0], size[1]
    left = max(0, min(b[0] for b in boxes) - pad)
    top = max(0, min(b[1] for b in boxes) - pad)
    right = min(size[0], max(b[2] for b in boxes) + pad)
    bottom = min(size[1], max(b[3] for b in boxes) + pad)
    return left, top, right, bottom


def main() -> None:
    ap = argparse.ArgumentParser(description="Wan MP4 → stable RGBA PNG sequence")
    ap.add_argument("video", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--mode", choices=["chroma", "luma"], default="chroma")
    ap.add_argument("--key-color", default="#00FF00")
    ap.add_argument("--inner", type=float, default=0.06, help="Fully transparent chroma distance")
    ap.add_argument("--outer", type=float, default=0.24, help="Fully opaque chroma distance")
    ap.add_argument("--despill", type=float, default=0.75)
    ap.add_argument("--luma-black", type=float, default=0.02)
    ap.add_argument("--luma-white", type=float, default=0.35)
    ap.add_argument("--luma-gamma", type=float, default=1.0)
    ap.add_argument("--matte-median", type=int, choices=[0, 3, 5], default=3)
    ap.add_argument("--pixel-grid", type=int, default=1, help="Nearest-neighbor pixel block lock")
    ap.add_argument("--crop", choices=["union", "none"], default="union")
    ap.add_argument("--pad", type=int, default=12)
    ap.add_argument("--ffmpeg", default="ffmpeg")
    args = ap.parse_args()

    if not args.video.exists():
        raise SystemExit(f"missing video: {args.video}")
    if not shutil.which(args.ffmpeg):
        raise SystemExit(f"ffmpeg not found: {args.ffmpeg}")
    args.out.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="sticker-kit-key-") as temp_name:
        temp = Path(temp_name)
        command = [
            args.ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(args.video),
            "-vsync",
            "0",
            str(temp / "source_%05d.png"),
        ]
        subprocess.run(command, check=True)
        sources = sorted(temp.glob("source_*.png"))
        if not sources:
            raise SystemExit("ffmpeg extracted no frames")

        keyed: list[Path] = []
        boxes: list[tuple[int, int, int, int]] = []
        coverage: list[float] = []
        size = Image.open(sources[0]).size
        key_rgb = parse_color(args.key_color)
        for index, source in enumerate(sources, start=1):
            image = Image.open(source)
            if args.mode == "luma":
                rgba = luma_rgba(image, args.luma_black, args.luma_white, args.luma_gamma)
            else:
                rgba = chroma_rgba(image, key_rgb, args.inner, args.outer, args.despill)
            if args.matte_median:
                alpha = rgba.getchannel("A").filter(ImageFilter.MedianFilter(args.matte_median))
                rgba.putalpha(alpha)
            rgba = pixel_lock(rgba, args.pixel_grid)
            box = alpha_bbox(rgba)
            if box:
                boxes.append(box)
            coverage.append(float(np.mean(np.asarray(rgba.getchannel("A")) > 8)))
            path = temp / f"keyed_{index:05d}.png"
            rgba.save(path)
            keyed.append(path)

        crop_box = union_bbox(boxes, size, args.pad) if args.crop == "union" else (0, 0, *size)
        for old in args.out.glob("frame_*.png"):
            old.unlink()
        width = max(4, len(str(len(keyed))))
        for index, source in enumerate(keyed, start=1):
            image = Image.open(source).crop(crop_box)
            image.save(args.out / f"frame_{index:0{width}d}.png")

    report = {
        "source": str(args.video.resolve()),
        "mode": args.mode,
        "key_color": args.key_color if args.mode == "chroma" else None,
        "frame_count": len(keyed),
        "source_size": list(size),
        "crop_box": list(crop_box),
        "output_size": [crop_box[2] - crop_box[0], crop_box[3] - crop_box[1]],
        "alpha_coverage": {
            "min": min(coverage),
            "max": max(coverage),
            "mean": sum(coverage) / len(coverage),
        },
        "pixel_grid": args.pixel_grid,
    }
    (args.out / "key_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"OK {len(keyed)} RGBA frames → {args.out.resolve()}")
    print(f"crop={crop_box} coverage_mean={report['alpha_coverage']['mean']:.4f}")


if __name__ == "__main__":
    main()
