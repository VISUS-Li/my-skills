#!/usr/bin/env python3
"""
仅预览用的变形辅助。禁止把输出打进生产贴纸表。

混合/ffmpeg 帧会产生残影（一格多姿态）。交付精灵表/GIF 时，请用 GenerateImage
生成每个姿态（或从 I2V 抽帧）。

光流无法修复姿态瞬移 — 先跑 qa_frames --max-pair-diff。
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


def list_frames(folder: Path) -> list[Path]:
    files = sorted(folder.glob("frame_*.png"))
    if not files:
        files = sorted(folder.glob("*.png"))
    return [f for f in files if "sheet" not in f.stem.lower() and "preview" not in f.stem.lower()]


def composite_cream(src: Path, dst: Path, cream=(253, 248, 240)) -> None:
    im = Image.open(src).convert("RGBA")
    bg = Image.new("RGBA", im.size, cream + (255,))
    bg.alpha_composite(im)
    bg.convert("RGB").save(dst, "PNG")


def blend_pair(a: Image.Image, b: Image.Image, t: float) -> Image.Image:
    a = a.convert("RGBA")
    b = b.convert("RGBA")
    if a.size != b.size:
        b = b.resize(a.size, Image.Resampling.LANCZOS)
    aa = np.asarray(a).astype(np.float32)
    bb = np.asarray(b).astype(np.float32)
    out = aa * (1.0 - t) + bb * t
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def pairwise_expand(frames: list[Path], inserts: int) -> list[Image.Image]:
    """Insert `inserts` blends between each consecutive pair (not after last)."""
    imgs = [Image.open(p).convert("RGBA") for p in frames]
    out: list[Image.Image] = []
    for i in range(len(imgs)):
        out.append(imgs[i])
        if i >= len(imgs) - 1:
            break
        for k in range(1, inserts + 1):
            t = k / (inserts + 1)
            out.append(blend_pair(imgs[i], imgs[i + 1], t))
    return out


def try_ffmpeg(frames: list[Path], factor: int, fps_in: int) -> list[Path] | None:
    if shutil.which("ffmpeg") is None:
        return None
    fps_out = fps_in * factor
    tmp = Path(tempfile.mkdtemp(prefix="interp_"))
    cream_dir = tmp / "cream"
    cream_dir.mkdir()
    for i, f in enumerate(frames):
        composite_cream(f, cream_dir / f"{i:04d}.png")
    out_dir = tmp / "out"
    out_dir.mkdir()
    # Use image2 explicitly; mi_mode=blend is more robust than mci on sparse stickers
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "image2",
        "-framerate",
        str(fps_in),
        "-i",
        str(cream_dir / "%04d.png"),
        "-vf",
        f"minterpolate=fps={fps_out}:mi_mode=blend",
        str(out_dir / "f%04d.png"),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    outs = sorted(out_dir.glob("f*.png"))
    if r.returncode != 0 or not outs:
        print("ffmpeg interpolate unavailable or empty; using pairwise blend fallback")
        if r.stderr:
            print(r.stderr[-800:])
        return None
    return outs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--factor", type=int, default=2, choices=[2, 3, 4])
    ap.add_argument("--fps-in", type=int, default=8)
    ap.add_argument("--target-count", type=int, default=50)
    ap.add_argument("--method", choices=["auto", "ffmpeg", "blend"], default="auto")
    args = ap.parse_args()

    frames = list_frames(args.src)
    if len(frames) < 2:
        print("need ≥2 frames", file=sys.stderr)
        sys.exit(2)

    args.out.mkdir(parents=True, exist_ok=True)
    for old in args.out.glob("frame_*.png"):
        old.unlink()

    # inserts between pairs so total ≈ n + (n-1)*inserts ≈ target
    n = len(frames)
    inserts = max(1, args.factor - 1)
    # Prefer inserts that land near target_count
    if args.target_count:
        # n + (n-1)*k ≈ target → k ≈ (target-n)/(n-1)
        inserts = max(1, round((args.target_count - n) / max(n - 1, 1)))

    method = args.method
    saved: list[Image.Image] = []

    if method in ("auto", "ffmpeg"):
        ff = try_ffmpeg(frames, args.factor, args.fps_in)
        if ff:
            imgs = [Image.open(p).convert("RGBA") for p in ff]
            if args.target_count and len(imgs) > args.target_count:
                idxs = [
                    round(i * (len(imgs) - 1) / (args.target_count - 1))
                    for i in range(args.target_count)
                ]
                imgs = [imgs[i] for i in idxs]
            saved = imgs
            print(f"method=ffmpeg count={len(saved)}")

    if not saved:
        saved = pairwise_expand(frames, inserts)
        if args.target_count and len(saved) > args.target_count:
            idxs = [
                round(i * (len(saved) - 1) / (args.target_count - 1))
                for i in range(args.target_count)
            ]
            saved = [saved[i] for i in idxs]
        # If still short, bump inserts
        while len(saved) < (args.target_count or 0) and inserts < 8:
            inserts += 1
            saved = pairwise_expand(frames, inserts)
            if args.target_count and len(saved) > args.target_count:
                idxs = [
                    round(i * (len(saved) - 1) / (args.target_count - 1))
                    for i in range(args.target_count)
                ]
                saved = [saved[i] for i in idxs]
                break
        print(f"method=blend inserts={inserts} count={len(saved)}")

    width = 3 if len(saved) >= 100 else 2
    for i, im in enumerate(saved, start=1):
        im.save(args.out / f"frame_{i:0{width}d}.png")
    print(f"OK: {n} keys → {len(saved)} frames → {args.out}")


if __name__ == "__main__":
    main()
