#!/usr/bin/env python3
"""Report downstream stages likely affected by a changed artifact."""
from __future__ import annotations

import argparse
import json

RULES = [
    ("research/", ["script", "storyboard", "shot-design", "sound-design", "assets", "audio-assets", "segments", "audio-mix", "assemble", "aesthetic-review", "qc", "publish"]),
    ("script/creative_brief", ["art-direction", "storyboard", "shot-design", "sound-design", "assets", "audio-assets", "segments", "audio-mix", "assemble", "aesthetic-review", "publish"]),
    ("script/outline", ["voiceover", "storyboard", "shot-design", "sound-design", "segments", "audio-mix", "assemble", "aesthetic-review", "publish"]),
    ("script/voiceover", ["storyboard", "shot-design", "sound-design", "segments", "audio-mix", "assemble", "qc", "publish"]),
    ("script/storyboard", ["shot-design", "sound-design", "assets", "audio-assets", "segments", "audio-mix", "assemble", "aesthetic-review", "qc", "publish"]),
    ("script/shotlist", ["sound-design", "segments", "audio-mix", "assemble", "aesthetic-review", "qc", "publish"]),
    ("design/art_direction", ["design", "sound-design", "assets", "audio-assets", "segments", "audio-mix", "assemble", "aesthetic-review", "qc", "publish"]),
    ("design/visual_moodboard", ["design", "assets", "segments", "aesthetic-review", "publish"]),
    ("design/", ["segments", "assemble", "aesthetic-review", "qc", "publish"]),
    ("audio/audio_style_guide", ["audio-assets", "audio-mix", "assemble", "qc", "publish"]),
    ("audio/music_brief", ["audio-assets", "audio-mix", "assemble", "qc", "publish"]),
    ("audio/voice_profile", ["tts", "audio-assets", "audio-mix", "assemble", "qc", "publish"]),
    ("audio/tts_plan", ["tts", "audio-assets", "audio-mix", "assemble", "qc", "publish"]),
    ("audio/audio_cue_sheet", ["audio-assets", "segments", "audio-mix", "assemble", "qc", "publish"]),
    ("audio/sfx_search_queries", ["audio-assets", "audio-mix", "qc", "publish"]),
    ("audio/audio_mix_plan", ["audio-mix", "assemble", "qc", "publish"]),
    ("audio/audio_rights_log", ["qc", "publish"]),
    ("audio/", ["audio-assets", "audio-mix", "assemble", "qc", "publish"]),
    ("assets/asset_manifest", ["audio-assets", "segments", "audio-mix", "assemble", "aesthetic-review", "qc", "publish"]),
    ("assets/audio", ["audio-mix", "assemble", "qc", "publish"]),
    ("assets/music", ["audio-mix", "assemble", "qc", "publish"]),
    ("assets/sfx", ["audio-mix", "assemble", "qc", "publish"]),
    ("assets/", ["segments", "assemble", "qc", "publish"]),
    ("segments/", ["audio-mix", "assemble", "aesthetic-review", "qc", "publish"]),
    ("edit/timeline", ["audio-mix", "assemble", "qc", "publish"]),
    ("edit/aesthetic_report", ["segments", "qc", "publish"]),
    ("edit/audio_qc_report", ["audio-mix", "qc", "publish"]),
    ("edit/", ["qc", "publish"]),
    ("exports/publish", ["publish"]),
]


def impacted(path: str) -> list[str]:
    p = path.replace("\\", "/")
    impacts: list[str] = []
    for prefix, stages in RULES:
        if p.startswith(prefix):
            for stage in stages:
                if stage not in impacts:
                    impacts.append(stage)
    if not impacts:
        impacts = ["manual-review"]
    return impacts


def report_json(changed_paths: list[str]) -> dict:
    items = []
    for changed in changed_paths:
        items.append({"changed": changed, "impacted_stages": impacted(changed)})
    return {"changes": items}


def main() -> int:
    parser = argparse.ArgumentParser(description="Show downstream impact of changed video artifacts.")
    parser.add_argument("--changed", action="append", required=True, help="Changed path. Repeatable.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()
    if args.json:
        print(json.dumps(report_json(args.changed), ensure_ascii=False, indent=2))
        return 0
    for changed in args.changed:
        print(f"Changed: {changed}")
        print("Impacted stages:")
        for stage in impacted(changed):
            print(f"- {stage}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
