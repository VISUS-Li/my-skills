#!/usr/bin/env python3
"""Create or refresh script/shotlist.json from storyboard segment shots.

This is a pragmatic bootstrapper: it converts rich storyboard shots when present,
and creates a three-beat cinematic draft when a segment is still under-specified.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_SEQUENCE = [
    ("A", "establishing graphic", "eye-level", "slow_push_in", "rule_of_thirds", "set context"),
    ("B", "insert/detail", "slight high angle", "parallax_pan", "asymmetric split", "show proof or texture"),
    ("C", "wide reveal", "eye-level", "match_move", "center hero with supporting orbit", "complete the idea"),
]


def shot_from_storyboard(segment: dict[str, Any], shot: dict[str, Any], fallback_index: int) -> dict[str, Any]:
    shot_id = shot.get("id") or f"{segment['id']}_{fallback_index + 1:02d}"
    layers = shot.get("layers") or ["foreground accent", "main subject", "background texture"]
    foreground = layers[0] if len(layers) > 0 else "foreground accent"
    midground = layers[1] if len(layers) > 1 else "main subject"
    background = layers[2] if len(layers) > 2 else "background texture"
    return {
        "shot_id": shot_id,
        "segment_id": segment["id"],
        "duration_sec": float(shot.get("duration_sec") or max(1.5, float(segment.get("duration_sec", 6)) / 3)),
        "shot_size": shot.get("shot_size", "medium graphic"),
        "camera_angle": shot.get("camera_angle", "eye-level"),
        "camera_move": shot.get("camera_move", "slow_push_in"),
        "composition": shot.get("composition", "rule_of_thirds with clear focal hierarchy"),
        "foreground": foreground,
        "midground": midground,
        "background": background,
        "depth_cues": shot.get("depth_cues", ["scale", "shadow", "parallax"]),
        "focal_element": shot.get("focal_element", segment.get("title", segment["id"])),
        "text_area_percent": shot.get("text_area_percent", 25),
        "asset_ids": shot.get("asset_ids", segment.get("assets", [])),
        "edit_intent": shot.get("edit_intent", segment.get("segment_role", "advance the story")),
    }


def draft_shots(segment: dict[str, Any]) -> list[dict[str, Any]]:
    duration = float(segment.get("duration_sec", 9))
    durations = [round(duration * 0.28, 2), round(duration * 0.42, 2)]
    durations.append(round(max(1.0, duration - sum(durations)), 2))
    out = []
    for idx, (suffix, size, angle, move, comp, intent) in enumerate(DEFAULT_SEQUENCE):
        out.append({
            "shot_id": f"{segment['id']}_{suffix}",
            "segment_id": segment["id"],
            "duration_sec": durations[idx],
            "shot_size": size,
            "camera_angle": angle,
            "camera_move": move,
            "composition": comp,
            "foreground": "animated caption or accent element",
            "midground": segment.get("visual_metaphor") or segment.get("title", segment["id"]),
            "background": "palette-consistent texture, gradient, grid, image plate, or b-roll",
            "depth_cues": ["scale", "shadow", "parallax"],
            "focal_element": segment.get("title", segment["id"]),
            "text_area_percent": 25,
            "asset_ids": segment.get("assets", []),
            "edit_intent": intent,
        })
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build script/shotlist.json from script/storyboard.json")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing shotlist")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    storyboard_path = root / "script/storyboard.json"
    shotlist_path = root / "script/shotlist.json"
    if not storyboard_path.exists():
        raise SystemExit(f"missing storyboard: {storyboard_path}")
    if shotlist_path.exists() and not args.overwrite:
        try:
            existing = json.loads(shotlist_path.read_text(encoding="utf-8"))
            if existing.get("shots"):
                print(f"Shotlist already has {len(existing['shots'])} shots. Use --overwrite to regenerate.")
                return 0
        except Exception:
            pass
    storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
    shots = []
    for seg in storyboard.get("segments", []):
        if not isinstance(seg, dict) or not seg.get("id"):
            continue
        seg_shots = seg.get("shots")
        if isinstance(seg_shots, list) and seg_shots:
            shots.extend(shot_from_storyboard(seg, shot, i) for i, shot in enumerate(seg_shots) if isinstance(shot, dict))
        else:
            shots.extend(draft_shots(seg))
    result = {
        "version": storyboard.get("version", "v001"),
        "source": "script/storyboard.json",
        "notes": "Review and refine shot size, camera move, composition, and asset IDs before rendering.",
        "shots": shots,
    }
    shotlist_path.parent.mkdir(parents=True, exist_ok=True)
    shotlist_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {shotlist_path} with {len(shots)} shots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
