#!/usr/bin/env python3
"""Score sound-design readiness before final assembly.

This is a lightweight deterministic gate. It cannot judge taste by listening, but
it catches common failures: no cue sheet, no music plan, random unlicensed SFX,
no mix targets, no ducking, or cues that are too sparse/dense.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

REQUIRED_AUDIO_FILES = [
    "audio/audio_style_guide.md",
    "audio/audio_cue_sheet.json",
    "audio/music_brief.md",
    "audio/voice_profile.md",
    "audio/audio_mix_plan.json",
    "audio/loudness_targets.json",
    "audio/audio_rights_log.md",
]

BLOCKED_RIGHTS = {"unknown", "needed", "needs-check", "do-not-use-final", "noncommercial", "copyrighted-reference-only"}


def load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except Exception as exc:  # noqa: BLE001
        return {}, [f"invalid json: {path}: {exc}"]


def count_non_template_text(path: Path) -> int:
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8")
    ignored = {"#", "-", "|", "---", "yes", "no", "unknown", "TBD", "todo", "TODO"}
    words = [w.strip(" :-|*/\t") for w in text.replace("\n", " ").split()]
    return len([w for w in words if w and w not in ignored and "{{" not in w and "}}" not in w])


def main() -> int:
    parser = argparse.ArgumentParser(description="Score audio design readiness.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--fail-under", type=int, default=72, help="Exit non-zero if score is below this threshold")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    score = 100
    issues: list[tuple[str, int]] = []
    warnings: list[str] = []

    for rel in REQUIRED_AUDIO_FILES:
        if not (root / rel).exists():
            issues.append((f"missing required audio file: {rel}", 12))

    for rel in ["audio/audio_style_guide.md", "audio/music_brief.md", "audio/voice_profile.md"]:
        p = root / rel
        if p.exists() and count_non_template_text(p) < 60:
            issues.append((f"{rel} appears too sparse or template-like", 8))

    cue_sheet, errors = load_json(root / "audio/audio_cue_sheet.json") if (root / "audio/audio_cue_sheet.json").exists() else ({}, [])
    for err in errors:
        issues.append((err, 15))
    cues = cue_sheet.get("cues", []) if isinstance(cue_sheet, dict) else []
    if not isinstance(cues, list) or not cues:
        issues.append(("audio/audio_cue_sheet.json must contain non-empty cues list", 18))
        cues = []

    cue_types = {str(c.get("type", "")) for c in cues if isinstance(c, dict)}
    cue_tracks = {str(c.get("track", "")) for c in cues if isinstance(c, dict)}
    if cues:
        if "music" not in cue_tracks and not any("music" in t for t in cue_types):
            issues.append(("no music cue or explicit no-music decision recorded", 8))
        if not any(t.startswith("sfx") for t in cue_types):
            issues.append(("no SFX cues planned", 12))
        if "ambience" not in cue_tracks and not any("ambience" in t for t in cue_types):
            warnings.append("no ambience cue; acceptable for stark/minimal videos, but often makes videos feel empty")
        required_fields = {"cue_id", "type", "segment_id", "start_sec", "duration_sec", "sync_anchor", "role", "sound_concept", "gain_db", "rights_status", "status"}
        for i, c in enumerate(cues):
            if not isinstance(c, dict):
                issues.append((f"cue[{i}] is not an object", 10))
                continue
            missing = required_fields - set(c)
            if missing:
                issues.append((f"cue[{i}] missing fields: {', '.join(sorted(missing))}", 4))
            try:
                start = float(c.get("start_sec", 0))
                dur = float(c.get("duration_sec", 0))
                if start < 0 or dur <= 0:
                    issues.append((f"cue[{i}] has invalid timing", 5))
            except Exception:
                issues.append((f"cue[{i}] has non-numeric timing", 5))
            rights = str(c.get("rights_status", "unknown")).lower()
            if str(c.get("status", "planned")).lower() in {"selected", "ready", "final"} and rights in BLOCKED_RIGHTS:
                issues.append((f"cue[{i}] is selected/final but rights_status is {rights}", 10))

    storyboard, _ = load_json(root / "script/storyboard.json") if (root / "script/storyboard.json").exists() else ({"segments": []}, [])
    segments = storyboard.get("segments", []) if isinstance(storyboard, dict) else []
    seg_count = len(segments) if isinstance(segments, list) else 0
    if seg_count and len(cues) < max(3, seg_count):
        issues.append((f"cue density too low: {len(cues)} cues for {seg_count} segments", 10))
    if seg_count and len(cues) > max(18, seg_count * 7):
        warnings.append(f"cue density may be too high: {len(cues)} cues for {seg_count} segments; avoid whoosh-on-every-cut")

    mix, mix_errors = load_json(root / "audio/audio_mix_plan.json") if (root / "audio/audio_mix_plan.json").exists() else ({}, [])
    for err in mix_errors:
        issues.append((err, 10))
    target = mix.get("target_loudness", {}) if isinstance(mix, dict) else {}
    if target:
        try:
            lufs = float(target.get("integrated_lufs"))
            tp = float(target.get("true_peak_db"))
            if not (-24 <= lufs <= -12):
                issues.append((f"integrated_lufs target {lufs} is outside typical web/video range", 6))
            if tp > -0.5:
                issues.append((f"true_peak_db {tp} is too close to clipping", 8))
        except Exception:
            issues.append(("target_loudness values must be numeric", 6))
    else:
        issues.append(("audio_mix_plan.json missing target_loudness", 8))

    # Asset manifest cross-check for audio rights.
    asset_path = root / "assets/asset_manifest.csv"
    if asset_path.exists():
        with asset_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                asset_type = str(row.get("type", "")).lower()
                if asset_type in {"audio", "music", "sfx", "voice", "ambience"}:
                    status = str(row.get("status", "")).lower()
                    rights = str(row.get("rights_status", "unknown")).lower()
                    if status in {"selected", "ready", "final"} and rights in BLOCKED_RIGHTS:
                        issues.append((f"audio asset {row.get('asset_id')} selected/final with blocked rights_status={rights}", 10))

    for msg, penalty in issues:
        score -= penalty
    score = max(0, min(100, score))

    report = root / "edit" / "audio_qc_report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Audio QC Report",
        "",
        f"Audio score: {score}",
        "",
        "## Blocking / scored issues",
    ]
    if issues:
        lines.extend([f"- (-{penalty}) {msg}" for msg, penalty in issues])
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings"])
    if warnings:
        lines.extend([f"- {w}" for w in warnings])
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Next actions",
        "- Fix scored issues before final render.",
        "- After assets are selected, listen through transitions and key reveals; adjust cue timing by ear.",
        "- Run final loudness / clipping checks after rendering the audio mix.",
        "",
    ])
    report.write_text("\n".join(lines), encoding="utf-8")

    print(f"Audio score: {score}")
    print(f"Wrote {report}")
    for msg, penalty in issues:
        print(f"- (-{penalty}) {msg}")
    for w in warnings:
        print(f"- warning: {w}")
    if score < args.fail_under:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
