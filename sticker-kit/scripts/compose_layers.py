#!/usr/bin/env python3
"""按索引 alpha 合成角色 + 特效 ordered 帧（同一枢轴格）。"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def list_frames(folder: Path) -> list[Path]:
    files = sorted(folder.glob("frame_*.png"))
    if not files:
        raise SystemExit(f"no frame_*.png in {folder}")
    return files


def place_centered(src: Image.Image, cell: int) -> Image.Image:
    rgba = src.convert("RGBA")
    # fit inside cell keeping aspect
    max_dim = int(cell * 0.92)
    scale = min(max_dim / max(rgba.width, 1), max_dim / max(rgba.height, 1), 1.0)
    nw, nh = max(1, int(rgba.width * scale)), max(1, int(rgba.height * scale))
    rgba = rgba.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
    x = (cell - nw) // 2
    y = (cell - nh) // 2
    canvas.alpha_composite(rgba, (x, y))
    return canvas


def main() -> None:
    ap = argparse.ArgumentParser(description="Composite character + vfx layer sequences")
    ap.add_argument("--character", type=Path, required=True)
    ap.add_argument("--vfx", type=Path, required=True)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--cell", type=int, default=512)
    ap.add_argument(
        "--vfx-offset",
        default="0,0",
        help="Optional x,y pixel offset for vfx on top of character cell",
    )
    args = ap.parse_args()

    char_frames = list_frames(args.character)
    vfx_frames = list_frames(args.vfx)
    n = min(len(char_frames), len(vfx_frames))
    if len(char_frames) != len(vfx_frames):
        print(
            f"WARN: character={len(char_frames)} vfx={len(vfx_frames)}; composing first {n}"
        )

    ox, oy = [int(x) for x in args.vfx_offset.split(",")]
    args.out.mkdir(parents=True, exist_ok=True)

    width = max(3, len(str(n)))
    for i in range(n):
        base = place_centered(Image.open(char_frames[i]), args.cell)
        overlay = place_centered(Image.open(vfx_frames[i]), args.cell)
        if ox or oy:
            shifted = Image.new("RGBA", (args.cell, args.cell), (0, 0, 0, 0))
            shifted.alpha_composite(overlay, (ox, oy))
            overlay = shifted
        base.alpha_composite(overlay)
        out_name = f"frame_{i+1:0{width}d}.png"
        base.save(args.out / out_name, "PNG")

    print(f"OK composited {n} frames → {args.out.resolve()}")


if __name__ == "__main__":
    main()
