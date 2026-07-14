#!/usr/bin/env python3
"""Validate the lightweight Video Producer segment spec."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SHOT_RECIPES = {
    "dark_grid_intro",
    "light_grid_concept_board",
    "terminal_proof",
    "editor_code_zoom",
    "screenshot_pushin_redbox",
    "phone_chat_sequence",
    "git_graph_growth",
    "timeline_rewind",
    "dashboard_room",
    "critique_wall",
    "data_card_compare",
    "svg_metaphor_scene",
    "keyword_actor_pop",
    "before_after_split",
    "workflow_pipeline",
    "audio_waveform_sync",
    "conclusion_stamp",
}

RENDERERS = {"remotion", "hyperframes", "vibe-motion", "motion-canvas", "gsap-svg", "ffmpeg", "mixed"}
PROOF_ACTIONS = ("screenshot", "terminal", "code", "browser", "phone", "editor")
PROOF_DIRECTING = ("push", "crop", "redbox", "cursor", "zoom", "highlight", "annotation", "focus")
TEXT_ONLY_OWNERS = ("subtitle", "caption", "textcard", "text_card", "bigtext", "titlecard", "title_card")
DELEGATED_RENDERERS = {"vibe-motion", "motion-canvas", "mixed"}
HOOK_ACTIONS = ("hook", "keyword", "screenshot", "redbox", "terminal", "proof", "cursor", "zoom")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"invalid json: {path}: {exc}") from exc


def pair(value: Any, label: str, errors: list[str]) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != 2:
        errors.append(f"{label}: time must be [start,end]")
        return 0.0, 0.0
    try:
        start = float(value[0])
        end = float(value[1])
    except (TypeError, ValueError):
        errors.append(f"{label}: time values must be numbers")
        return 0.0, 0.0
    if end <= start:
        errors.append(f"{label}: end must be greater than start")
    return start, end


def validate(spec: dict[str, Any], beat_plan: dict[str, Any] | None = None) -> list[str]:
    errors: list[str] = []
    for key in ("version", "segment_id", "style", "duration", "first_slice", "shots"):
        if key not in spec:
            errors.append(f"missing required field: {key}")

    duration = float(spec.get("duration") or 0)
    if spec.get("first_slice") is True and not (20 <= duration <= 30):
        errors.append("first_slice duration must be 20-30 seconds")

    shots = spec.get("shots")
    if not isinstance(shots, list) or not shots:
        errors.append("shots must be a non-empty list")
        return errors

    referenced_beats: set[str] = set()
    action_times: list[float] = []
    macro_reset_times: list[float] = []
    proof_without_direction: list[str] = []
    visual_owners: set[str] = set()
    shot_ranges: list[tuple[str, float, float]] = []
    hook_actions: list[str] = []
    recipes_used: set[str] = set()
    renderers_used: set[str] = set()
    delegated_count = 0

    for shot in shots:
        if not isinstance(shot, dict):
            errors.append("shot entries must be objects")
            continue
        sid = str(shot.get("shot_id") or "<missing>")
        start, end = pair(shot.get("time"), sid, errors)
        shot_ranges.append((sid, start, end))
        shot_duration = max(0.0, end - start)
        if end > duration + 0.01:
            errors.append(f"{sid}: shot ends after segment duration")
        owner = str(shot.get("visual_owner") or "")
        if not owner:
            errors.append(f"{sid}: visual_owner required")
        else:
            visual_owners.add(owner)
            if shot_duration > 1.5 and any(token in owner.lower() for token in TEXT_ONLY_OWNERS):
                errors.append(f"{sid}: text-only visual_owner lasts {shot_duration:.2f}s; make picture carry the beat")
        if shot.get("recipe") not in SHOT_RECIPES:
            errors.append(f"{sid}: unknown or missing recipe {shot.get('recipe')!r}")
        else:
            recipes_used.add(str(shot.get("recipe")))
        renderer = str(shot.get("renderer") or "")
        if renderer not in RENDERERS:
            errors.append(f"{sid}: unknown or missing renderer {shot.get('renderer')!r}")
        else:
            renderers_used.add(renderer)
        delegation = shot.get("delegation")
        if renderer in DELEGATED_RENDERERS and not isinstance(delegation, dict):
            errors.append(f"{sid}: renderer {renderer} needs delegation contract")
        if isinstance(delegation, dict):
            delegated_count += 1
            for field in ("skill", "purpose", "acceptance"):
                if not delegation.get(field):
                    errors.append(f"{sid}: delegation missing {field}")
            outputs = delegation.get("output_artifacts")
            if not isinstance(outputs, list) or not outputs:
                errors.append(f"{sid}: delegation output_artifacts must be non-empty")
        beats = shot.get("narration_beats")
        if not isinstance(beats, list) or not beats:
            errors.append(f"{sid}: narration_beats must be non-empty")
        else:
            referenced_beats.update(str(item) for item in beats)
        actions = shot.get("visual_actions")
        if not isinstance(actions, list) or not actions:
            errors.append(f"{sid}: visual_actions must be non-empty")
            continue
        for action in actions:
            if not isinstance(action, dict):
                errors.append(f"{sid}: visual action must be object")
                continue
            at = action.get("at")
            try:
                t = float(at)
            except (TypeError, ValueError):
                errors.append(f"{sid}: action at must be numeric")
                continue
            if t < start - 0.01 or t > end + 0.01:
                errors.append(f"{sid}: action at {t} outside shot time [{start}, {end}]")
            action_times.append(t)
            atype = str(action.get("type") or "")
            if t <= 3.0 and any(token in atype.lower() for token in HOOK_ACTIONS):
                hook_actions.append(f"{sid}:{atype}")
            text = " ".join(str(action.get(k) or "") for k in ("type", "motion", "annotation"))
            if "macro_scene_reset" in atype or "reset" in atype:
                macro_reset_times.append(t)
            if any(token in atype.lower() for token in PROOF_ACTIONS) and not any(token in text.lower() for token in PROOF_DIRECTING):
                proof_without_direction.append(f"{sid}:{atype}")
        local_times = sorted(float(action.get("at") or 0) for action in actions if isinstance(action, dict) and isinstance(action.get("at"), (int, float)))
        if local_times:
            if local_times[0] - start > 1.55:
                errors.append(f"micro_action_density: {sid} has no action for first {local_times[0] - start:.2f}s")
            if end - local_times[-1] > 1.55:
                errors.append(f"micro_action_density: {sid} has no action for last {end - local_times[-1]:.2f}s")

    sorted_ranges = sorted(shot_ranges, key=lambda item: item[1])
    if sorted_ranges:
        first_sid, first_start, _ = sorted_ranges[0]
        if abs(first_start) > 0.05:
            errors.append(f"segment_coverage: first shot {first_sid} starts at {first_start:.2f}s, expected 0.00s")
        for (left_sid, _, left_end), (right_sid, right_start, _) in zip(sorted_ranges, sorted_ranges[1:]):
            if right_start - left_end > 0.05:
                errors.append(f"segment_coverage: gap {right_start - left_end:.2f}s between {left_sid} and {right_sid}")
            if left_end - right_start > 0.05:
                errors.append(f"segment_coverage: overlap {left_end - right_start:.2f}s between {left_sid} and {right_sid}")
        last_sid, _, last_end = sorted_ranges[-1]
        if duration and duration - last_end > 0.05:
            errors.append(f"segment_coverage: last shot {last_sid} ends at {last_end:.2f}s before duration {duration:.2f}s")
    if not hook_actions:
        errors.append("hook_required: first 3 seconds need a visual hook/proof action")
    if duration >= 12 and len(visual_owners) < 2:
        errors.append("visual_owner_variety: first slice needs at least two distinct visual owners")
    if spec.get("first_slice") is True:
        if len(recipes_used) > 5:
            errors.append(f"complexity_budget: first slice uses {len(recipes_used)} recipes; target 3-5")
        if len(renderers_used) > 3:
            errors.append(f"complexity_budget: first slice uses {len(renderers_used)} renderers; target 1-3")
        if delegated_count > 2:
            errors.append(f"complexity_budget: first slice has {delegated_count} delegated slots; target 0-2")

    action_times = sorted(set(round(t, 3) for t in action_times))
    for left, right in zip(action_times, action_times[1:]):
        if right - left > 1.55:
            errors.append(f"micro_action_density: gap {right - left:.2f}s between {left:.2f}s and {right:.2f}s")
    if duration >= 12 and not macro_reset_times:
        errors.append("macro_scene_reset_density: segment needs at least one macro reset")
    if proof_without_direction:
        errors.append("proof_choreography_required: " + ", ".join(proof_without_direction))

    if beat_plan:
        beats = beat_plan.get("beats", [])
        beat_ids = {str(item.get("beat_id")) for item in beats if isinstance(item, dict)}
        missing = sorted(beat_ids - referenced_beats)
        if missing:
            errors.append("beats not referenced by any shot: " + ", ".join(missing))
        for beat in beats:
            if not isinstance(beat, dict):
                continue
            bid = beat.get("beat_id", "<missing>")
            for field in ("voice_text", "keyword", "intent", "visual_owner", "visual_action", "subtitle_strategy"):
                if not beat.get(field):
                    errors.append(f"{bid}: missing {field}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("segment_spec", type=Path)
    parser.add_argument("--beat-plan", type=Path)
    args = parser.parse_args()

    spec = load_json(args.segment_spec)
    beat_plan = load_json(args.beat_plan) if args.beat_plan else None
    errors = validate(spec, beat_plan)
    if errors:
        print("FAILED")
        for item in errors:
            print(f"- {item}")
        return 1
    print(f"OK: {args.segment_spec}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
