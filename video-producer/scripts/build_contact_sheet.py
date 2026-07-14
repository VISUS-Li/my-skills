#!/usr/bin/env python3
"""Build a contact sheet from the first-slice preview with FFmpeg."""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


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

    args.out.parent.mkdir(parents=True, exist_ok=True)
    vf = f"fps={args.fps},scale={args.scale}:-1:force_original_aspect_ratio=decrease,tile={args.cols}x"
    cmd = ["ffmpeg", "-y", "-i", str(args.video), "-vf", vf, "-frames:v", "1", str(args.out)]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr[-1000:])
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
