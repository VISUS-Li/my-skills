#!/usr/bin/env python3
"""Measure voice assets with ffprobe and write audio/voice/timing.json."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from video_plan_utils import atomic_write_json, load_json, media_path, resolve_project_and_plan


def probe_duration(path: Path) -> float:
    if not shutil.which("ffprobe"):
        raise RuntimeError("ffprobe is required to measure voice assets")
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"ffprobe failed for {path}")
    duration = float(json.loads(proc.stdout)["format"]["duration"])
    if duration <= 0:
        raise ValueError(f"voice asset has no positive duration: {path}")
    return duration


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", default=".", help="Project root or video-plan.json")
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Keep declared durations for missing files instead of failing",
    )
    parser.add_argument(
        "--output",
        default="audio/voice/timing.json",
        help="Timing output path relative to the project",
    )
    args = parser.parse_args()

    project, plan_path = resolve_project_and_plan(args.project)
    plan = load_json(plan_path)
    tracks = plan.get("voice", {}).get("tracks", [])
    if not tracks:
        raise ValueError("video-plan.json has no voice.tracks to measure")

    measured: list[dict[str, object]] = []
    cursor = 0.0
    for track in tracks:
        beat_id = str(track.get("beatId") or "").strip()
        source = str(track.get("src") or "").strip()
        if not beat_id or not source:
            raise ValueError("every voice track requires beatId and src")
        path = media_path(project, source)
        if path.exists():
            duration = probe_duration(path)
            timing_source = "measured"
        elif args.allow_missing and float(track.get("durationSec") or 0) > 0:
            duration = float(track["durationSec"])
            timing_source = "declared"
        else:
            raise FileNotFoundError(f"missing voice asset for {beat_id}: {path}")
        gap = max(0.0, float(track.get("gapAfterSec") or 0))
        row = {
            "beatId": beat_id,
            "src": source,
            "startSec": round(cursor, 3),
            "durationSec": round(duration, 3),
            "endSec": round(cursor + duration, 3),
            "gapAfterSec": round(gap, 3),
            "source": timing_source,
        }
        measured.append(row)
        cursor += duration + gap

    output = project / args.output
    atomic_write_json(
        output,
        {
            "version": 1,
            "totalSec": round(max(0.0, cursor - float(measured[-1]["gapAfterSec"])), 3),
            "tracks": measured,
        },
    )
    print(f"measured {len(measured)} voice track(s) -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
