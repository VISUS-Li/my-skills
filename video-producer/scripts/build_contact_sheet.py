#!/usr/bin/env python3
"""Build a contact sheet from the first-slice preview with FFmpeg."""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path


def sample_rate(value: str) -> Fraction:
    try:
        rate = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"invalid --fps value: {value}") from exc
    if rate <= 0:
        raise ValueError("--fps must be positive")
    return rate


def probe_duration(video: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=duration:format=duration",
        "-of",
        "json",
        str(video),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "ffprobe failed")
    try:
        payload = json.loads(proc.stdout)
        stream_duration = (payload.get("streams") or [{}])[0].get("duration")
        duration = float(stream_duration or payload["format"]["duration"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError("ffprobe did not return a valid duration") from exc
    if duration <= 0:
        raise RuntimeError("video duration must be positive")
    return duration


def tile_rows(duration: float, rate: Fraction, columns: int) -> int:
    if columns <= 0:
        raise ValueError("--cols must be positive")
    estimated_frames = max(1, math.ceil(duration * float(rate)))
    return math.ceil(estimated_frames / columns)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--out", type=Path, default=Path("outputs/review/contact_sheet.jpg"))
    parser.add_argument("--fps", default="1/3")
    parser.add_argument("--cols", type=int, default=5)
    parser.add_argument("--scale", type=int, default=320)
    args = parser.parse_args()

    if not args.video.exists():
        raise SystemExit(f"video missing: {args.video}")
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found")
    if not shutil.which("ffprobe"):
        raise SystemExit("ffprobe not found")
    if args.scale <= 0:
        raise SystemExit("--scale must be positive")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    try:
        rate = sample_rate(args.fps)
        rows = tile_rows(probe_duration(args.video), rate, args.cols)
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc
    vf = (
        f"fps={args.fps},"
        f"scale={args.scale}:-1:force_original_aspect_ratio=decrease,"
        f"tile={args.cols}x{rows}"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(args.video),
        "-vf",
        vf,
        "-frames:v",
        "1",
        "-update",
        "1",
        str(args.out),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr[-1000:])
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
