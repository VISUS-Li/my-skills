#!/usr/bin/env python3
"""Probe video metadata with ffprobe."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any


def parse_rate(value: str | None) -> float | None:
    if not value or value == "0/0":
        return None
    try:
        return float(Fraction(value))
    except (ValueError, ZeroDivisionError):
        return None


def run_ffprobe(video: Path) -> dict[str, Any]:
    if shutil.which("ffprobe") is None:
        raise SystemExit("ERROR: ffprobe not found. Install FFmpeg and ensure ffprobe is on PATH.")
    if not video.exists():
        raise SystemExit(f"ERROR: file not found: {video}")

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,codec_name,avg_frame_rate,r_frame_rate:format=duration",
        "-of",
        "json",
        str(video),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SystemExit(f"ERROR: ffprobe failed:\n{result.stderr.strip()}")

    raw = json.loads(result.stdout)
    streams = raw.get("streams") or []
    if not streams:
        raise SystemExit("ERROR: no video stream found")
    stream = streams[0]
    duration_raw = (raw.get("format") or {}).get("duration")

    return {
        "path": str(video),
        "width": stream.get("width"),
        "height": stream.get("height"),
        "fps": parse_rate(stream.get("avg_frame_rate")) or parse_rate(stream.get("r_frame_rate")),
        "duration": float(duration_raw) if duration_raw is not None else None,
        "codec": stream.get("codec_name"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe video width, height, fps, duration, and codec.")
    parser.add_argument("video", type=Path, help="Path to video file")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of key-value lines")
    args = parser.parse_args()

    info = run_ffprobe(args.video)
    if args.json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        for key in ("path", "width", "height", "fps", "duration", "codec"):
            print(f"{key}: {info.get(key)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
