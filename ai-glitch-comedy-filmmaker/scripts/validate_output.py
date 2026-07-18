#!/usr/bin/env python3
"""Validate generated project JSON against schema and semantic skill rules."""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: jsonschema. Install it with `python -m pip install jsonschema`."
    ) from exc

BANNED_LAZY_WORDS = ("笑死", "太离谱", "逆天", "太抽象")
PLACEHOLDER_PATTERNS = (
    re.compile(r"^\s*VO\s*\d+\s*$", re.I),
    re.compile(r"可选\s*(VO|旁白|对白)?", re.I),
    re.compile(r"待(补|定|写)"),
    re.compile(r"TBD|TODO|optional", re.I),
    re.compile(r"此处.*(吐槽|旁白|对白)"),
)
TECH_TOKENS = ("chaos_level", "debug target", "threat_priority", "target=", "fixed_seed=")
VIDEO_TYPES = {"video_blueprint", "full_production"}


def text_is_placeholder(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in PLACEHOLDER_PATTERNS)


def semantic_errors(data: dict) -> list[str]:
    errors: list[str] = []

    if data.get("deliverable_type") != "research_report":
        packets = data.get("agent_execution", {}).get("task_packets", [])
        if len(packets) < 2:
            errors.append("agent_execution.task_packets: non-research outputs require at least 2 task packets")

    if data.get("game", {}).get("dimension") != "3d":
        errors.append("game.dimension: this skill requires 3d output")

    comedy_units = data.get("comedy", {}).get("units", [])
    for index, unit in enumerate(comedy_units):
        visual = unit.get("visual_contrast", "")
        if len(visual.strip()) < 12:
            errors.append(f"comedy.units.{index}.visual_contrast: describe a concrete visible 3D result")
        voiceover = unit.get("deadpan_voiceover", "")
        if any(word in voiceover for word in BANNED_LAZY_WORDS):
            errors.append(f"comedy.units.{index}.deadpan_voiceover: replace generic reaction words with a precise deadpan redefinition")
        if voiceover.strip() == visual.strip():
            errors.append(f"comedy.units.{index}.deadpan_voiceover: must not simply repeat the visible event")
        if text_is_placeholder(voiceover):
            errors.append(f"comedy.units.{index}.deadpan_voiceover: placeholder or optional text is forbidden")

    packets = data.get("agent_execution", {}).get("task_packets", [])
    if packets and not any(packet.get("parameter_table") for packet in packets):
        errors.append("agent_execution.task_packets: at least one packet must provide explicit parameters")

    for index, packet in enumerate(packets):
        if not packet.get("forbidden_changes"):
            errors.append(f"agent_execution.task_packets.{index}.forbidden_changes: required")
        if not packet.get("non_goals"):
            errors.append(f"agent_execution.task_packets.{index}.non_goals: required")
        if not packet.get("failure_examples"):
            errors.append(f"agent_execution.task_packets.{index}.failure_examples: required")
        if len(packet.get("acceptance_tests", [])) < 2:
            errors.append(f"agent_execution.task_packets.{index}.acceptance_tests: require at least 2 manual tests")

    if data.get("deliverable_type") in VIDEO_TYPES:
        project = data.get("project", {})
        duration = float(project.get("target_duration_sec") or 0)
        video = data.get("video", {})
        script = video.get("voiceover_script", [])
        boards = video.get("creative_storyboard", [])

        minimum_lines = max(6, math.ceil(duration / 25)) if duration else 6
        if len(script) < minimum_lines:
            errors.append(f"video.voiceover_script: {duration:.0f}s video requires at least {minimum_lines} full voiceover lines, found {len(script)}")

        all_voice_text = "".join(str(item.get("text", "")) for item in script)
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", all_voice_text))
        minimum_chars = math.ceil(duration / 60 * 120) if duration else 120
        if chinese_chars < minimum_chars:
            errors.append(f"video.voiceover_script: require at least {minimum_chars} Chinese characters for {duration:.0f}s, found {chinese_chars}")

        for i, item in enumerate(script):
            text = str(item.get("text", ""))
            if text_is_placeholder(text):
                errors.append(f"video.voiceover_script.{i}.text: placeholder/optional narration is forbidden")
            if item.get("end_sec", 0) <= item.get("start_sec", 0):
                errors.append(f"video.voiceover_script.{i}: end_sec must be greater than start_sec")

        if not boards:
            errors.append("video.creative_storyboard: required for video outputs")
        else:
            spoken_shots = 0
            for i, shot in enumerate(boards):
                content = shot.get("spoken_content", [])
                if content:
                    spoken_shots += 1
                role = shot.get("beat_role")
                shot_duration = float(shot.get("end_sec", 0)) - float(shot.get("start_sec", 0))
                if not content and not (role in {"visual_reveal", "reaction_hold", "final_button"} and shot_duration <= 3.0):
                    errors.append(f"video.creative_storyboard.{i}.spoken_content: long or non-reveal shots require actual narration/dialogue")
                for j, spoken in enumerate(content):
                    text = str(spoken.get("text", ""))
                    if text_is_placeholder(text):
                        errors.append(f"video.creative_storyboard.{i}.spoken_content.{j}.text: placeholders and optional lines are forbidden")
                audience_blob = " ".join(str(shot.get(k, "")) for k in ("visual", "player_action", "comic_turn", "transition"))
                for token in TECH_TOKENS:
                    if token.lower() in audience_blob.lower():
                        errors.append(f"video.creative_storyboard.{i}: technical token '{token}' belongs in technical_capture_plan")
            ratio = spoken_shots / len(boards)
            if ratio < 0.70:
                errors.append(f"video.creative_storyboard: at least 70% of shots need spoken content, found {ratio:.0%}")

        tech = video.get("technical_capture_plan", [])
        if not tech:
            errors.append("video.technical_capture_plan: required and separate from audience storyboard")

    quality = data.get("quality_check", {})
    false_keys = [key for key, value in quality.items() if key != "issues" and value is False]
    if false_keys and not quality.get("issues"):
        errors.append("quality_check.issues: explain how to fix every false quality gate")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_output.py <output.json>", file=sys.stderr)
        return 2

    output_path = Path(sys.argv[1]).expanduser().resolve()
    schema_path = Path(__file__).resolve().parent.parent / "references" / "output-schema.json"

    try:
        with output_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        print(f"Output file not found: {output_path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}", file=sys.stderr)
        return 1

    with schema_path.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)

    validator = Draft202012Validator(schema)
    schema_errors = sorted(validator.iter_errors(data), key=lambda error: list(error.absolute_path))
    semantic = semantic_errors(data)

    if schema_errors or semantic:
        total = len(schema_errors) + len(semantic)
        print(f"Validation failed with {total} error(s):", file=sys.stderr)
        for error in schema_errors:
            path = ".".join(str(part) for part in error.absolute_path) or "<root>"
            print(f"- {path}: {error.message}", file=sys.stderr)
        for error in semantic:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
