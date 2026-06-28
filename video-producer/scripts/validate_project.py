#!/usr/bin/env python3
"""Validate required files and basic schemas for a video production project."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


REQUIRED_FILES = [
    ".video/video.json",
    ".video/state.json",
    "script/creative_brief.md",
    "script/storyboard.json",
    "script/narration_beats.csv",
    "script/beat_timeline.json",
    "script/shotlist.json",
    "design/art_direction.md",
    "design/visual_moodboard.json",
    "design/design.md",
    "design/tokens.json",
    "assets/asset_manifest.csv",
    "assets/asset_choreography_manifest.csv",
    "audio/audio_style_guide.md",
    "audio/audio_cue_sheet.json",
    "audio/music_brief.md",
    "audio/voice_profile.md",
    "audio/tts_plan.json",
    "audio/sfx_search_queries.json",
    "audio/audio_mix_plan.json",
    "audio/loudness_targets.json",
    "audio/audio_rights_log.md",
    "research/source_cards.jsonl",
    "research/claim_ledger.csv",
    "research/factcheck_report.md",
    "script/voiceover.md",
    "script/director_event_graph.json",
    "edit/timeline.json",
    "edit/aesthetic_report.md",
    "edit/audio_qc_report.md",
]

VALID_STATUSES = {"draft", "review", "approved", "locked", "needs-revision", "rendered", "failed"}


def load_json(path: Path) -> tuple[dict, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except Exception as exc:  # noqa: BLE001 - validation script should show any parse issue
        return {}, [f"invalid json: {path}: {exc}"]


def validate_storyboard(root: Path) -> list[str]:
    errors: list[str] = []
    data, json_errors = load_json(root / "script/storyboard.json")
    errors.extend(json_errors)
    if errors:
        return errors
    segments = data.get("segments")
    if not isinstance(segments, list) or not segments:
        errors.append("script/storyboard.json must contain a non-empty segments list")
        return errors
    total = 0.0
    ids: set[str] = set()
    for i, seg in enumerate(segments):
        prefix = f"segment[{i}]"
        seg_id = seg.get("id")
        if not seg_id or not isinstance(seg_id, str):
            errors.append(f"{prefix} missing string id")
        elif seg_id in ids:
            errors.append(f"duplicate segment id: {seg_id}")
        else:
            ids.add(seg_id)
        duration = seg.get("duration_sec")
        if not isinstance(duration, (int, float)) or duration <= 0:
            errors.append(f"{prefix} must have positive duration_sec")
        else:
            total += float(duration)
        if not seg.get("engine"):
            errors.append(f"{prefix} missing engine")
        if seg.get("status") and seg.get("status") not in VALID_STATUSES:
            errors.append(f"{prefix} has invalid status: {seg.get('status')}")
        # Richness warnings are handled by aesthetic_score.py; this validator only checks basic schema.
        if "shots" in seg and not isinstance(seg.get("shots"), list):
            errors.append(f"{prefix} shots must be a list when present")
    target = data.get("total_duration_sec")
    if isinstance(target, (int, float)) and total > float(target) * 1.25:
        errors.append(f"storyboard segment total {total}s exceeds target by more than 25% ({target}s)")
    return errors


def validate_shotlist(root: Path) -> list[str]:
    errors: list[str] = []
    data, json_errors = load_json(root / "script/shotlist.json")
    errors.extend(json_errors)
    if errors:
        return errors
    shots = data.get("shots")
    if not isinstance(shots, list):
        errors.append("script/shotlist.json must contain shots list")
        return errors
    for i, shot in enumerate(shots):
        if not isinstance(shot, dict):
            errors.append(f"shot[{i}] must be an object")
            continue
        for key in ["shot_id", "segment_id", "duration_sec", "shot_size", "camera_move", "composition", "edit_intent"]:
            if key not in shot:
                errors.append(f"shot[{i}] missing {key}")
    return errors



def validate_audio_cue_sheet(root: Path) -> list[str]:
    errors: list[str] = []
    data, json_errors = load_json(root / "audio/audio_cue_sheet.json")
    errors.extend(json_errors)
    if errors:
        return errors
    cues = data.get("cues")
    if not isinstance(cues, list):
        errors.append("audio/audio_cue_sheet.json must contain cues list")
        return errors
    required = {"cue_id", "type", "segment_id", "start_sec", "duration_sec", "sync_anchor", "role", "sound_concept", "rights_status", "status"}
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            errors.append(f"cue[{i}] must be an object")
            continue
        missing = required - set(cue)
        if missing:
            errors.append(f"cue[{i}] missing fields: {', '.join(sorted(missing))}")
        if "start_sec" in cue and not isinstance(cue.get("start_sec"), (int, float)):
            errors.append(f"cue[{i}] start_sec must be numeric")
        if "duration_sec" in cue and (not isinstance(cue.get("duration_sec"), (int, float)) or cue.get("duration_sec", 0) <= 0):
            errors.append(f"cue[{i}] duration_sec must be positive numeric")
    return errors


def validate_audio_mix_plan(root: Path) -> list[str]:
    errors: list[str] = []
    data, json_errors = load_json(root / "audio/audio_mix_plan.json")
    errors.extend(json_errors)
    if errors:
        return errors
    target = data.get("target_loudness")
    if not isinstance(target, dict):
        errors.append("audio/audio_mix_plan.json missing target_loudness object")
    else:
        for key in ["integrated_lufs", "true_peak_db", "lra"]:
            if key not in target or not isinstance(target.get(key), (int, float)):
                errors.append(f"audio/audio_mix_plan.json target_loudness missing numeric {key}")
    tracks = data.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        errors.append("audio/audio_mix_plan.json must contain non-empty tracks list")
    return errors

def validate_state(root: Path) -> list[str]:
    errors: list[str] = []
    data, json_errors = load_json(root / ".video/state.json")
    errors.extend(json_errors)
    stages = data.get("stages", {})
    if not isinstance(stages, dict):
        return errors + [".video/state.json stages must be an object"]
    for name, meta in stages.items():
        status = meta.get("status") if isinstance(meta, dict) else None
        if status not in VALID_STATUSES:
            errors.append(f"stage {name} has invalid status: {status}")
    return errors


def validate_claim_ledger(root: Path) -> list[str]:
    path = root / "research/claim_ledger.csv"
    errors: list[str] = []
    try:
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            expected = {"claim_id", "claim", "claim_type", "source_ids", "source_urls", "supporting_quote", "source_context", "interpretation_guardrail", "script_sentence", "risk", "verification_status", "needs_manual_check", "video_location", "misread_check"}
            missing = expected - set(reader.fieldnames or [])
            if missing:
                errors.append(f"research/claim_ledger.csv missing columns: {', '.join(sorted(missing))}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"invalid claim ledger: {exc}")
    return errors


def validate_asset_manifest(root: Path) -> list[str]:
    path = root / "assets/asset_manifest.csv"
    errors: list[str] = []
    try:
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            expected = {"asset_id", "type", "source", "path_or_url", "segment_id", "role", "rights_status", "status", "notes"}
            optional = {"review_status", "beat_ids", "actor_id", "version", "last_regen_at"}
            missing = expected - set(reader.fieldnames or [])
            if missing:
                errors.append(f"assets/asset_manifest.csv missing columns: {', '.join(sorted(missing))}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"invalid asset manifest: {exc}")
    return errors


def _validate_gates(root: Path) -> list[str]:
    scripts_dir = Path(__file__).resolve().parent
    import sys

    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    try:
        from review_core import validate_gates

        return validate_gates(root)
    except Exception as exc:  # noqa: BLE001
        return [f"gate validation error: {exc}"]


def validate_narration_beats(root: Path) -> list[str]:
    path = root / "script/narration_beats.csv"
    errors: list[str] = []
    try:
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            expected = {"beat_id", "segment_id", "start_sec", "end_sec", "narration", "semantic_action", "visual_response_required", "sfx_intent"}
            missing = expected - set(reader.fieldnames or [])
            if missing:
                errors.append(f"script/narration_beats.csv missing columns: {', '.join(sorted(missing))}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"invalid narration beats: {exc}")
    return errors


def validate_beat_timeline(root: Path) -> list[str]:
    errors: list[str] = []
    data, json_errors = load_json(root / "script/beat_timeline.json")
    errors.extend(json_errors)
    if errors:
        return errors
    beats = data.get("beats")
    if not isinstance(beats, list) or not beats:
        errors.append("script/beat_timeline.json must contain a non-empty beats list")
        return errors
    required = {"beat_id", "segment_id", "start_sec", "end_sec", "narration", "intent", "beat_type", "visual_action", "assets", "text_ids", "motion", "sfx_cue_ids", "why_not_ppt"}
    for i, beat in enumerate(beats):
        if not isinstance(beat, dict):
            errors.append(f"beat[{i}] must be an object")
            continue
        missing = required - set(beat)
        if missing:
            errors.append(f"beat[{i}] missing fields: {', '.join(sorted(missing))}")
        if "start_sec" in beat and not isinstance(beat.get("start_sec"), (int, float)):
            errors.append(f"beat[{i}] start_sec must be numeric")
        if "end_sec" in beat and not isinstance(beat.get("end_sec"), (int, float)):
            errors.append(f"beat[{i}] end_sec must be numeric")
    return errors


def validate_asset_choreography(root: Path) -> list[str]:
    path = root / "assets/asset_choreography_manifest.csv"
    errors: list[str] = []
    try:
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            expected = {"asset_id", "type", "description", "source_or_prompt", "rights_status", "layer", "first_on_sec", "last_on_sec", "entrance", "main_motion", "exit", "states", "reused_in_segments", "sfx_affordance", "implementation_notes"}
            missing = expected - set(reader.fieldnames or [])
            if missing:
                errors.append(f"assets/asset_choreography_manifest.csv missing columns: {', '.join(sorted(missing))}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"invalid asset choreography manifest: {exc}")
    return errors



def validate_director_event_graph(root: Path) -> list[str]:
    errors: list[str] = []
    data, json_errors = load_json(root / "script/director_event_graph.json")
    errors.extend(json_errors)
    if errors:
        return errors
    nodes = data.get("nodes")
    edges = data.get("edges")
    if not isinstance(nodes, list):
        errors.append("script/director_event_graph.json must contain nodes list")
    if not isinstance(edges, list):
        errors.append("script/director_event_graph.json must contain edges list")
    if isinstance(nodes, list):
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                errors.append(f"director event node[{i}] must be an object")
                continue
            for key in ["event_id", "beat_id", "segment_id", "time_range", "event_type", "description", "primary_asset"]:
                if key not in node:
                    errors.append(f"director event node[{i}] missing {key}")
    return errors

def validate_timeline(root: Path) -> list[str]:
    errors: list[str] = []
    data, json_errors = load_json(root / "edit/timeline.json")
    errors.extend(json_errors)
    tracks = data.get("tracks")
    if not isinstance(tracks, list):
        errors.append("edit/timeline.json must contain tracks list")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a video production project.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    errors: list[str] = []

    for required in REQUIRED_FILES:
        if not (root / required).exists():
            errors.append(f"missing required file: {required}")

    if not errors:
        errors.extend(validate_state(root))
        errors.extend(validate_storyboard(root))
        errors.extend(validate_shotlist(root))
        errors.extend(validate_claim_ledger(root))
        errors.extend(validate_asset_manifest(root))
        errors.extend(validate_narration_beats(root))
        errors.extend(validate_beat_timeline(root))
        errors.extend(validate_director_event_graph(root))
        errors.extend(validate_asset_choreography(root))
        errors.extend(validate_timeline(root))
        errors.extend(validate_audio_cue_sheet(root))
        errors.extend(validate_audio_mix_plan(root))

    if errors:
        print("Validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    gate_errors = _validate_gates(root)
    if gate_errors:
        print("Gate validation failed:")
        for err in gate_errors:
            print(f"- {err}")
        return 1

    print("Validation passed.")
    print("For quality gates, also run: scripts/script_claim_lint.py <project> --fail-under 85, scripts/beat_timeline_lint.py <project> --fail-under 80, scripts/aesthetic_score.py <project> --fail-under 72, and scripts/audio_score.py <project> --fail-under 72")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
