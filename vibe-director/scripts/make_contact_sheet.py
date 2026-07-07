#!/usr/bin/env python3
"""Create a contact sheet from images or a video."""

from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}


def require_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
    except ImportError:
        raise SystemExit("ERROR: Pillow is required. Install it with: python -m pip install Pillow")
    return Image, ImageDraw, ImageFont


def sample_video(video: Path, out_dir: Path, count: int) -> list[Path]:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ERROR: ffmpeg and ffprobe are required for video input.")
    script = Path(__file__).with_name("sample_keyframes.py")
    cmd = [sys.executable, str(script), str(video), str(out_dir), "--count", str(count), "--prefix", "sheet"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SystemExit(result.stdout + result.stderr)
    return sorted(out_dir.glob("sheet_*.jpg"))


def collect_inputs(inputs: list[Path], temp_dir: Path, frame_count: int) -> list[Path]:
    paths: list[Path] = []
    for item in inputs:
        if item.is_dir():
            paths.extend(sorted(path for path in item.iterdir() if path.suffix.lower() in IMAGE_EXTS))
        elif item.suffix.lower() in IMAGE_EXTS:
            paths.append(item)
        elif item.suffix.lower() in VIDEO_EXTS:
            video_dir = temp_dir / item.stem
            video_dir.mkdir(parents=True, exist_ok=True)
            paths.extend(sample_video(item, video_dir, frame_count))
        else:
            raise SystemExit(f"ERROR: unsupported input: {item}")
    if not paths:
        raise SystemExit("ERROR: no images found")
    return paths


def make_sheet(image_paths: list[Path], output: Path, columns: int, thumb_width: int, padding: int) -> None:
    Image, ImageDraw, ImageFont = require_pillow()
    thumbs = []
    label_height = 24
    for path in image_paths:
        with Image.open(path) as img:
            img = img.convert("RGB")
            ratio = thumb_width / img.width
            thumb_height = max(1, int(img.height * ratio))
            img = img.resize((thumb_width, thumb_height))
            thumbs.append((path, img.copy()))

    rows = math.ceil(len(thumbs) / columns)
    cell_width = thumb_width + padding * 2
    cell_height = max(img.height for _, img in thumbs) + label_height + padding * 2
    sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except OSError:
        font = ImageFont.load_default()

    for index, (path, img) in enumerate(thumbs):
        col = index % columns
        row = index // columns
        x = col * cell_width + padding
        y = row * cell_height + padding
        sheet.paste(img, (x, y))
        label = f"{index + 1:02d} {path.name}"
        draw.text((x, y + img.height + 4), label[:40], fill=(20, 20, 20), font=font)

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Make a contact sheet from images, directories, or videos.")
    parser.add_argument("inputs", type=Path, nargs="+", help="Image files, image directories, or video files")
    parser.add_argument("-o", "--output", type=Path, default=Path("contact-sheet.jpg"), help="Output image path")
    parser.add_argument("--columns", type=int, default=4, help="Grid columns, default 4")
    parser.add_argument("--thumb-width", type=int, default=320, help="Thumbnail width, default 320")
    parser.add_argument("--frame-count", type=int, default=10, help="Frames to sample per video input, default 10")
    parser.add_argument("--padding", type=int, default=12, help="Cell padding in pixels, default 12")
    args = parser.parse_args()

    if args.columns < 1:
        raise SystemExit("ERROR: --columns must be >= 1")

    with tempfile.TemporaryDirectory(prefix="vibe-director-sheet-") as temp:
        image_paths = collect_inputs(args.inputs, Path(temp), args.frame_count)
        make_sheet(image_paths, args.output, args.columns, args.thumb_width, args.padding)

    print(f"wrote contact sheet: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
