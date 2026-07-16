#!/usr/bin/env python3
"""Align RGBA frames to a shared pivot, pack sprite sheet + manifest + preview GIF."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


def list_frames(src: Path) -> list[Path]:
    if src.is_file():
        return [src]
    files: list[Path] = []
    for pat in ("frame_*.png", "part_*.png", "*_transparent_*.png", "*.png"):
        files = sorted(src.glob(pat))
        # skip sheets / previews if present in same folder
        files = [f for f in files if "sheet" not in f.stem.lower() and "preview" not in f.stem.lower()]
        if files:
            break
    # Prefer frame_ / part_ if mixed
    frames = [f for f in files if f.stem.startswith("frame_") or f.stem.startswith("part_")]
    return frames or files


def content_bbox(img: Image.Image, alpha_thresh: int = 16) -> tuple[int, int, int, int] | None:
    a = np.asarray(img.convert("RGBA"))[..., 3]
    ys, xs = np.where(a > alpha_thresh)
    if ys.size == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def place_on_cell(
    img: Image.Image,
    cell: int,
    anchor: str,
    margin: float = 0.08,
) -> Image.Image:
    rgba = img.convert("RGBA")
    bb = content_bbox(rgba)
    if bb is None:
        return Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
    x0, y0, x1, y1 = bb
    crop = rgba.crop((x0, y0, x1 + 1, y1 + 1))
    cw, ch = crop.size
    max_dim = int(cell * (1.0 - 2 * margin))
    scale = min(max_dim / max(cw, 1), max_dim / max(ch, 1), 1.0)
    nw, nh = max(1, int(cw * scale)), max(1, int(ch * scale))
    crop = crop.resize((nw, nh), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
    if anchor == "bottom-center":
        x = (cell - nw) // 2
        y = cell - nh - int(cell * margin)
    elif anchor == "center":
        x = (cell - nw) // 2
        y = (cell - nh) // 2
    else:
        raise ValueError(f"unknown anchor: {anchor}")
    canvas.alpha_composite(crop, (x, y))
    return canvas


def pack_sheet(frames: list[Image.Image], cols: int | None = None) -> tuple[Image.Image, list[dict]]:
    n = len(frames)
    if n == 0:
        raise ValueError("no frames")
    cell = frames[0].size[0]
    if cols is None:
        cols = min(n, 8)
    rows = (n + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cell, rows * cell), (0, 0, 0, 0))
    layout = []
    for i, fr in enumerate(frames):
        r, c = divmod(i, cols)
        x, y = c * cell, r * cell
        sheet.alpha_composite(fr, (x, y))
        layout.append({"index": i, "x": x, "y": y, "w": cell, "h": cell})
    return sheet, layout


def save_gif(frames: list[Image.Image], path: Path, fps: int) -> None:
    duration = max(1, int(1000 / max(fps, 1)))
    # GIF needs palette; composite on cream for preview readability
    cream = (253, 248, 240, 255)
    out = []
    for fr in frames:
        bg = Image.new("RGBA", fr.size, cream)
        bg.alpha_composite(fr)
        out.append(bg.convert("P", palette=Image.Palette.ADAPTIVE, colors=256))
    out[0].save(
        path,
        save_all=True,
        append_images=out[1:],
        duration=duration,
        loop=0,
        disposal=2,
    )


def expand_holds(paths: list[Path], hold: int, target_count: int | None) -> list[Path]:
    """Repeat each unique path `hold` times; optionally trim/pad to target_count."""
    hold = max(1, hold)
    expanded: list[Path] = []
    for p in paths:
        expanded.extend([p] * hold)
    if target_count is not None:
        if len(expanded) > target_count:
            expanded = expanded[:target_count]
        elif len(expanded) < target_count and expanded:
            # pad by holding the last pose (still no ghost blend)
            while len(expanded) < target_count:
                expanded.append(expanded[-1])
    return expanded


def main() -> None:
    ap = argparse.ArgumentParser(description="Align frames → sprite sheet + manifest + GIF")
    ap.add_argument("src", type=Path, help="Folder of RGBA frames or a single PNG")
    ap.add_argument("-o", "--out", type=Path, default=None)
    ap.add_argument("--cell", type=int, default=512)
    ap.add_argument("--fps", type=int, default=8)
    ap.add_argument("--anchor", choices=["bottom-center", "center"], default="bottom-center")
    ap.add_argument("--cols", type=int, default=None)
    ap.add_argument("--loop", action="store_true", default=True)
    ap.add_argument(
        "--hold",
        type=int,
        default=1,
        help="Play each unique pose N times before next (slows motion, no ghosts)",
    )
    ap.add_argument(
        "--target-count",
        type=int,
        default=None,
        help="Exact packed frame count after holds (trim/pad last pose)",
    )
    args = ap.parse_args()

    paths = list_frames(args.src)
    if not paths:
        raise SystemExit(f"no frames in {args.src}")
    unique_n = len(paths)
    paths = expand_holds(paths, args.hold, args.target_count)

    out = args.out or (args.src if args.src.is_dir() else args.src.parent)
    out.mkdir(parents=True, exist_ok=True)
    frames_dir = out / "frames"
    frames_dir.mkdir(exist_ok=True)
    for old in frames_dir.glob("frame_*.png"):
        old.unlink()

    aligned: list[Image.Image] = []
    frame_files: list[str] = []
    source_map: list[str] = []
    width = 3 if len(paths) >= 100 else 2
    # cache aligned cells by source path
    cache: dict[str, Image.Image] = {}
    for i, p in enumerate(paths, start=1):
        key = str(p.resolve())
        if key not in cache:
            cache[key] = place_on_cell(Image.open(p), args.cell, args.anchor)
        cell_img = cache[key]
        name = f"frame_{i:0{width}d}.png"
        cell_img.save(frames_dir / name)
        aligned.append(cell_img)
        frame_files.append(f"frames/{name}")
        source_map.append(p.name)
        print(f"aligned {p.name} -> {name}" + (f" (hold)" if args.hold > 1 else ""))

    sheet, layout = pack_sheet(aligned, cols=args.cols)
    sheet_path = out / "sheet.png"
    sheet.save(sheet_path)

    gif_path = out / "preview.gif"
    save_gif(aligned, gif_path, args.fps)

    manifest = {
        "cell": args.cell,
        "fps": args.fps,
        "loop": bool(args.loop),
        "anchor": args.anchor,
        "hold": args.hold,
        "unique_frame_count": unique_n,
        "pivot": {"x": args.cell // 2, "y": args.cell - int(args.cell * 0.08)}
        if args.anchor == "bottom-center"
        else {"x": args.cell // 2, "y": args.cell // 2},
        "frame_count": len(aligned),
        "frames": frame_files,
        "source_per_packed_frame": source_map,
        "sheet": "sheet.png",
        "sheet_layout": layout,
        "preview": "preview.gif",
    }
    man_path = out / "manifest.json"
    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"sheet -> {sheet_path}")
    print(f"gif   -> {gif_path}")
    print(
        f"manifest -> {man_path} ({unique_n} unique × hold {args.hold} → {len(aligned)} frames @ {args.fps}fps)"
    )


if __name__ == "__main__":
    main()
