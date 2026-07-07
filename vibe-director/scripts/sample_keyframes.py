#!/usr/bin/env python3
"""Sample evenly spaced frames from a video with ffmpeg."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def ffprobe_duration(video: Path) -> float:
    if shutil.which("ffprobe") is None:
        raise SystemExit("ERROR: ffprobe not found. Install FFmpeg and ensure ffprobe is on PATH.")
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(video),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SystemExit(f"ERROR: ffprobe failed:\n{result.stderr.strip()}")
    duration = (json.loads(result.stdout).get("format") or {}).get("duration")
    if duration is None:
        raise SystemExit("ERROR: could not read video duration")
    return float(duration)


def sample_frames(video: Path, out_dir: Path, count: int, prefix: str) -> list[Path]:
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ERROR: ffmpeg not found. Install FFmpeg and ensure ffmpeg is on PATH.")
    if not video.exists():
        raise SystemExit(f"ERROR: file not found: {video}")
    if count < 1:
        raise SystemExit("ERROR: --count must be >= 1")

    duration = ffprobe_duration(video)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    for index in range(count):
        timestamp = duration * (index + 0.5) / count
        output = out_dir / f"{prefix}_{index + 1:02d}.jpg"
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            f"{timestamp:.3f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(output),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise SystemExit(f"ERROR: ffmpeg failed at {timestamp:.3f}s:\n{result.stderr.strip()}")
        paths.append(output)

    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Sample evenly spaced key review frames from a video.")
    parser.add_argument("video", type=Path, help="Path to video file")
    parser.add_argument("out_dir", type=Path, help="Directory for sampled JPG frames")
    parser.add_argument("--count", type=int, default=10, help="Number of frames to sample, default 10")
    parser.add_argument("--prefix", default="frame", help="Output filename prefix")
    args = parser.parse_args()

    paths = sample_frames(args.video, args.out_dir, args.count, args.prefix)
    print(f"wrote {len(paths)} frame(s) to {args.out_dir}")
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
