#!/usr/bin/env python3
"""Build edit/timeline.json from script/storyboard.json and rendered segment files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a timeline from storyboard segments.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--segment-filename", default="render.mp4", help="Expected render filename inside each segment folder")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    video = json.loads((root / ".video/video.json").read_text(encoding="utf-8"))
    storyboard = json.loads((root / "script/storyboard.json").read_text(encoding="utf-8"))
    audio_cues_path = root / "audio" / "audio_cue_sheet.json"
    audio_cues = json.loads(audio_cues_path.read_text(encoding="utf-8")).get("cues", []) if audio_cues_path.exists() else []

    start = 0.0
    video_items = []
    missing = []
    for seg in storyboard.get("segments", []):
        seg_id = seg["id"]
        duration = float(seg.get("duration_sec", 0))
        src = Path("segments") / seg_id / args.segment_filename
        if not (root / src).exists():
            missing.append(str(src))
        video_items.append({
            "src": str(src),
            "start": round(start, 3),
            "duration": duration,
            "segment_id": seg_id,
            "engine": seg.get("engine", "unknown"),
        })
        start += duration

    timeline = {
        "version": storyboard.get("version", "v001"),
        "ratio": video.get("ratio", "9:16"),
        "fps": video.get("fps", 30),
        "resolution": video.get("resolution", "1080x1920"),
        "duration_sec": round(start, 3),
        "tracks": [
            {"type": "video", "items": video_items},
            {"type": "audio", "items": [c for c in audio_cues if isinstance(c, dict)]},
            {"type": "subtitle", "items": []},
        ],
        "missing_segment_files": missing,
    }
    out = root / "edit/timeline.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    if missing:
        print("Missing segment files:")
        for m in missing:
            print(f"- {m}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
