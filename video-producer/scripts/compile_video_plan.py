#!/usr/bin/env python3
"""Compile measured timing into the single runtime video-plan.json."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from video_plan_utils import atomic_write_json, load_json, resolve_project_and_plan


def round3(value: float) -> float:
    return round(float(value), 3)


def end_sec(item: dict[str, Any]) -> float:
    return float(item.get("startSec") or 0) + float(item.get("durationSec") or 0)


def compile_voice(project: Path, plan: dict[str, Any], timing_name: str) -> None:
    voice = plan.setdefault("voice", {"mode": "per-beat", "tracks": []})
    tracks = voice.setdefault("tracks", [])
    timing_path = project / timing_name
    measured = {}
    if timing_path.exists():
        measured_payload = load_json(timing_path)
        measured = {str(row["beatId"]): row for row in measured_payload.get("tracks", [])}

    cursor = 0.0
    for track in tracks:
        beat_id = str(track.get("beatId") or "").strip()
        if not beat_id:
            raise ValueError("voice track is missing beatId")
        timing = measured.get(beat_id, {})
        duration = float(timing.get("durationSec") or track.get("durationSec") or 0)
        if duration <= 0:
            raise ValueError(f"voice track {beat_id} has no measured or declared duration")
        gap = max(0.0, float(track.get("gapAfterSec") or timing.get("gapAfterSec") or 0))
        track["startSec"] = round3(cursor)
        track["durationSec"] = round3(duration)
        track["gapAfterSec"] = round3(gap)
        cursor += duration + gap

    by_beat = {str(track["beatId"]): track for track in tracks}
    for scene in plan.get("scenes", []):
        beat_ids = [str(value) for value in scene.get("beatIds", [])]
        if not beat_ids:
            continue
        unknown = [beat_id for beat_id in beat_ids if beat_id not in by_beat]
        if unknown:
            raise ValueError(f"scene {scene.get('id')} references unknown beat(s): {', '.join(unknown)}")
        timing = scene.get("timing") or {}
        start = min(float(by_beat[beat_id]["startSec"]) for beat_id in beat_ids)
        end = max(end_sec(by_beat[beat_id]) for beat_id in beat_ids)
        start += float(timing.get("startOffsetSec") or 0)
        end += float(timing.get("endOffsetSec") or 0)
        if end <= start:
            raise ValueError(f"scene {scene.get('id')} compiles to a non-positive duration")
        scene["startSec"] = round3(max(0.0, start))
        scene["durationSec"] = round3(end - max(0.0, start))

    captions = plan.get("captions")
    if captions is not None and (captions.get("autoFromVoice") or not captions.get("cues")):
        captions["cues"] = [
            {
                "startMs": round(float(track["startSec"]) * 1000),
                "endMs": round(end_sec(track) * 1000),
                "text": str(track.get("text") or ""),
            }
            for track in tracks
            if str(track.get("text") or "").strip()
        ]


def compute_duration(plan: dict[str, Any]) -> float:
    ends = [end_sec(scene) for scene in plan.get("scenes", [])]
    ends.extend(end_sec(track) for track in plan.get("voice", {}).get("tracks", []))
    ends.extend(
        float(effect.get("atSec") or 0) + float(effect.get("durationSec") or 0)
        for effect in plan.get("effects", [])
    )
    ends.extend(
        float(cue.get("endMs") or 0) / 1000
        for cue in plan.get("captions", {}).get("cues", [])
    )
    for cue in plan.get("audio", {}).get("cues", []):
        ends.append(float(cue.get("atSec") or 0) + float(cue.get("durationSec") or 0))
    return max(ends or [float(plan.get("video", {}).get("durationSec") or 0)])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", default=".", help="Project root or video-plan.json")
    parser.add_argument(
        "--timing",
        default="audio/voice/timing.json",
        help="Measured voice timing path relative to project",
    )
    args = parser.parse_args()

    project, plan_path = resolve_project_and_plan(args.project)
    plan = load_json(plan_path)
    video = plan.setdefault("video", {})
    mode = str(video.get("timingMode") or "voice")
    if mode == "voice":
        compile_voice(project, plan, args.timing)
    elif mode == "music":
        if not plan.get("musicBeats"):
            raise ValueError("timingMode=music requires musicBeats")
    elif mode != "fixed":
        raise ValueError(f"unsupported timingMode: {mode}")

    duration = compute_duration(plan)
    if mode == "fixed":
        duration = max(duration, float(video.get("durationSec") or 0))
    if duration <= 0:
        raise ValueError("compiled video duration must be positive")
    video["durationSec"] = round3(duration)
    atomic_write_json(plan_path, plan)
    print(f"compiled {plan_path} ({mode}, {video['durationSec']}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
