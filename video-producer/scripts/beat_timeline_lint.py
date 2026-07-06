#!/usr/bin/env python3
"""Lint director-grade beat timelines for dense, voice-synced explainer videos."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"Missing {path}"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except Exception as exc:
        return {}, [f"Invalid JSON {path}: {exc}"]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def words(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(words(v) for v in value)
    if isinstance(value, dict):
        return " ".join(words(v) for v in value.values())
    return str(value)


def event_presets(event: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("motion_preset_id", "text_preset_id"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
    for key in ("motion_preset_ids", "text_preset_ids"):
        value = event.get(key)
        if isinstance(value, list):
            values.extend(str(v).strip() for v in value if str(v).strip())
    motion = event.get("motion")
    if isinstance(motion, dict):
        value = motion.get("preset_id") or motion.get("motion_preset_id")
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
    return values


def load_known_presets(root: Path) -> set[str]:
    candidates = [
        root / "assets" / "micro_animation_palette.json",
        Path(__file__).resolve().parents[1] / "assets" / "templates" / "micro_animation_palette.json",
    ]
    known: set[str] = set()
    for path in candidates:
        palette, _ = load_json(path)
        if not isinstance(palette, dict):
            continue
        for section in ("motion_presets", "text_presets", "motion_tokens"):
            values = palette.get(section, {})
            if isinstance(values, dict):
                known.update(str(key) for key in values.keys())
    return known


def main() -> int:
    parser = argparse.ArgumentParser(description="Score script/beat_timeline.json and asset choreography density.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--fail-under", type=int, default=80, help="Fail if score is below threshold")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    timeline, errors = load_json(root / "script" / "beat_timeline.json")
    beats = timeline.get("beats", []) if isinstance(timeline, dict) else []
    narration_rows = read_csv(root / "script" / "narration_beats.csv")
    asset_rows = read_csv(root / "assets" / "asset_choreography_manifest.csv")
    cue_sheet, cue_errors = load_json(root / "audio" / "audio_cue_sheet.json")
    cues = cue_sheet.get("cues", []) if isinstance(cue_sheet, dict) else []
    known_presets = load_known_presets(root)

    issues: list[tuple[str, int]] = []
    issues.extend((e, 18) for e in errors)
    if cue_errors:
        issues.append(("audio/audio_cue_sheet.json missing or invalid; SFX anchors cannot be verified", 8))
    if not isinstance(beats, list) or not beats:
        issues.append(("script/beat_timeline.json must contain non-empty beats list", 28))
        beats = []
    if not narration_rows:
        issues.append(("script/narration_beats.csv missing; cannot verify each narration phrase has a visual response", 12))
    if not asset_rows:
        issues.append(("assets/asset_choreography_manifest.csv missing; cannot verify asset-level movement", 14))

    # Beat field completeness.
    required = ["beat_id", "segment_id", "start_sec", "end_sec", "narration", "intent", "beat_type", "visual_action", "assets", "text_ids", "motion", "sfx_cue_ids", "why_not_ppt"]
    for i, beat in enumerate(beats):
        if not isinstance(beat, dict):
            issues.append((f"beat {i} is not an object", 4))
            continue
        allow_empty_lists = {"text_ids", "sfx_cue_ids"}
        missing = [
            k for k in required
            if k not in beat
            or beat.get(k) in (None, "")
            or (beat.get(k) == [] and k not in allow_empty_lists)
        ]
        if missing:
            issues.append((f"{beat.get('beat_id', i)} missing required fields: {', '.join(missing)}", min(12, 2 * len(missing))))
        try:
            start = float(beat.get("start_sec"))
            end = float(beat.get("end_sec"))
            if end <= start:
                issues.append((f"{beat.get('beat_id', i)} end_sec must be greater than start_sec", 5))
            duration = end - start
            if duration > 1.8:
                issues.append((f"{beat.get('beat_id', i)} lasts {duration:.2f}s; split into phrase-level micro-events", 10))
            elif duration > 1.5 and "deliberate" not in str(beat.get("why_not_ppt", "")).lower():
                issues.append((f"{beat.get('beat_id', i)} lasts {duration:.2f}s; explain deliberate hold or split it", 5))
        except Exception:
            issues.append((f"{beat.get('beat_id', i)} start_sec/end_sec must be numeric", 5))
        visual_action = str(beat.get("visual_action", "")).lower()
        if visual_action in {"fade in", "fade", "show text", "static card"} or len(visual_action) < 18:
            issues.append((f"{beat.get('beat_id', i)} visual_action is too generic or PPT-like", 6))
        if "fade" in visual_action and not any(k in visual_action for k in ["draw", "transform", "slide", "snap", "stamp", "pulse", "zoom", "scan", "morph", "wipe"]):
            issues.append((f"{beat.get('beat_id', i)} uses fade without semantic motion", 4))
        presets = event_presets(beat)
        unknown_presets = sorted(p for p in presets if known_presets and p not in known_presets)
        if unknown_presets:
            issues.append((f"{beat.get('beat_id', i)} references unknown motion/text preset IDs: {', '.join(unknown_presets[:5])}", 6))
        if any(p.startswith("reactive.yield") for p in presets):
            guard_text = words(beat).lower()
            if not any(k in guard_text for k in ["must_show", "source", "table", "axis", "label", "readable", "detail", "hold"]):
                issues.append((f"{beat.get('beat_id', i)} uses yield preset without proof/readability guardrail", 6))

    # Gaps between beats.
    timed = []
    for beat in beats:
        if isinstance(beat, dict):
            try:
                timed.append((float(beat.get("start_sec")), float(beat.get("end_sec")), str(beat.get("beat_id", "?"))))
            except Exception:
                pass
    timed.sort()
    for (s1, e1, b1), (s2, e2, b2) in zip(timed, timed[1:]):
        gap = s2 - e1
        if gap > 1.8:
            issues.append((f"Long unchanged gap {gap:.2f}s between {b1} and {b2}; add micro-beats", 10))
        elif gap > 1.2:
            issues.append((f"Beat gap {gap:.2f}s between {b1} and {b2}; consider adding visual response", 4))

    # Narration coverage.
    beat_narration = words([b.get("narration") for b in beats if isinstance(b, dict)]).strip()
    if narration_rows and len(beats) < len(narration_rows):
        issues.append((f"Fewer timeline beats ({len(beats)}) than narration phrases ({len(narration_rows)})", 12))
    if narration_rows and not beat_narration:
        issues.append(("Timeline beats do not include narration text", 10))

    # Asset and cue references.
    asset_ids = {r.get("asset_id", "") for r in asset_rows}
    cue_ids = {str(c.get("cue_id", "")) for c in cues if isinstance(c, dict)}
    referenced_assets = set()
    referenced_cues = set()
    for beat in beats:
        if not isinstance(beat, dict):
            continue
        for a in beat.get("assets", []) if isinstance(beat.get("assets"), list) else []:
            referenced_assets.add(str(a))
        for c in beat.get("sfx_cue_ids", []) if isinstance(beat.get("sfx_cue_ids"), list) else []:
            referenced_cues.add(str(c))
    if asset_rows:
        missing_assets = sorted(a for a in referenced_assets if a and a not in asset_ids)
        if missing_assets:
            issues.append((f"Beat timeline references assets missing from choreography manifest: {', '.join(missing_assets[:8])}", 8))
    if cues:
        missing_cues = sorted(c for c in referenced_cues if c and c not in cue_ids and c.lower() not in {"none", "deliberate_silence"})
        if missing_cues:
            issues.append((f"Beat timeline references SFX cue IDs missing from cue sheet: {', '.join(missing_cues[:8])}", 8))

    # Score.
    penalty = sum(weight for _, weight in issues)
    score = max(0, 100 - penalty)
    # Event graph should exist for dense/director-grade projects.
    if not (root / "script" / "director_event_graph.json").exists():
        issues.append(("script/director_event_graph.json missing; event causality/attention graph not documented", 6))
        penalty = sum(weight for _, weight in issues)
        score = max(0, 100 - penalty)

    print(f"Beat timeline score: {score}/100")
    if issues:
        print("Issues:")
        for msg, weight in issues:
            print(f"- [{weight}] {msg}")
    else:
        print("No structural issues found. Human review for taste is still required.")
    return 1 if score < args.fail_under else 0


if __name__ == "__main__":
    raise SystemExit(main())
