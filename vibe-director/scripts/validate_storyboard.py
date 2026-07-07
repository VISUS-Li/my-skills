#!/usr/bin/env python3
"""Validate a vibe-director storyboard.json file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


VALID_PLATFORMS = {"douyin", "bilibili", "x", "youtube", "other"}
VALID_ASPECTS = {"9:16", "16:9", "1:1", "4:5"}
VALID_SOURCE_MODES = {"topic", "script", "article", "srt", "notes", "existing-storyboard"}
VALID_RENDERERS = {"hyperframes", "remotion", "vibe-motion", "custom"}
VALID_STATUSES = {"draft", "planned", "generated", "reviewed", "approved", "rejected"}
VALID_SHOT_TYPES = {
    "kinetic-title",
    "chat",
    "terminal",
    "diagram",
    "ui-mockup",
    "graph",
    "timeline",
    "comparison",
    "dashboard",
    "caption-focus",
    "code-demo",
    "data-viz",
}


def is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise SystemExit(f"ERROR: file not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")


def require_mapping(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected object")
        return {}
    return value


def require_list(value: Any, path: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{path}: expected list")
        return []
    return value


def validate_video(video: dict[str, Any], errors: list[str]) -> None:
    required = [
        "title",
        "platform",
        "aspectRatio",
        "resolution",
        "fps",
        "targetDurationSec",
        "stylePreset",
        "sourceMode",
    ]
    for key in required:
        if key not in video:
            errors.append(f"video.{key}: missing required field")

    if "title" in video and not is_nonempty_string(video["title"]):
        errors.append("video.title: must be a non-empty string")
    if video.get("platform") not in VALID_PLATFORMS:
        errors.append(f"video.platform: must be one of {sorted(VALID_PLATFORMS)}")
    if video.get("aspectRatio") not in VALID_ASPECTS:
        errors.append(f"video.aspectRatio: must be one of {sorted(VALID_ASPECTS)}")
    if "resolution" in video and not is_nonempty_string(video["resolution"]):
        errors.append("video.resolution: must be a non-empty string like 1080x1920")
    if "fps" in video and not is_positive_number(video["fps"]):
        errors.append("video.fps: must be > 0")
    if "targetDurationSec" in video and not is_positive_number(video["targetDurationSec"]):
        errors.append("video.targetDurationSec: must be > 0")
    if "stylePreset" in video and not is_nonempty_string(video["stylePreset"]):
        errors.append("video.stylePreset: must be a non-empty string")
    if video.get("sourceMode") not in VALID_SOURCE_MODES:
        errors.append(f"video.sourceMode: must be one of {sorted(VALID_SOURCE_MODES)}")


def validate_sections(sections: list[Any], errors: list[str]) -> set[str]:
    ids: set[str] = set()
    for index, raw_section in enumerate(sections):
        path = f"sections[{index}]"
        section = require_mapping(raw_section, path, errors)
        section_id = section.get("id")
        if not is_nonempty_string(section_id):
            errors.append(f"{path}.id: must be a non-empty string")
        elif section_id in ids:
            errors.append(f"{path}.id: duplicate section id '{section_id}'")
        else:
            ids.add(section_id)

        if not is_nonempty_string(section.get("role")):
            errors.append(f"{path}.role: must be a non-empty string")
        if not is_nonempty_string(section.get("narrativeGoal")):
            errors.append(f"{path}.narrativeGoal: must be a non-empty string")
        if not is_positive_number(section.get("durationSec")):
            errors.append(f"{path}.durationSec: must be > 0")
    return ids


def validate_scenes(scenes: list[Any], section_ids: set[str], errors: list[str]) -> None:
    ids: set[str] = set()
    for index, raw_scene in enumerate(scenes):
        path = f"scenes[{index}]"
        scene = require_mapping(raw_scene, path, errors)

        scene_id = scene.get("id")
        if not is_nonempty_string(scene_id):
            errors.append(f"{path}.id: must be a non-empty string")
        elif scene_id in ids:
            errors.append(f"{path}.id: duplicate scene id '{scene_id}'")
        else:
            ids.add(scene_id)

        section_id = scene.get("sectionId")
        if not is_nonempty_string(section_id):
            errors.append(f"{path}.sectionId: must be a non-empty string")
        elif section_ids and section_id not in section_ids:
            errors.append(f"{path}.sectionId: unknown section id '{section_id}'")

        if "startSec" in scene and not isinstance(scene["startSec"], (int, float)):
            errors.append(f"{path}.startSec: must be a number")
        if not is_positive_number(scene.get("durationSec")):
            errors.append(f"{path}.durationSec: must be > 0")
        if not is_nonempty_string(scene.get("narration")):
            errors.append(f"{path}.narration: must be a non-empty string")
        if not is_nonempty_string(scene.get("visualMetaphor")):
            errors.append(f"{path}.visualMetaphor: must be a non-empty string")
        if scene.get("shotType") not in VALID_SHOT_TYPES:
            errors.append(f"{path}.shotType: must be one of {sorted(VALID_SHOT_TYPES)}")
        if scene.get("renderer") not in VALID_RENDERERS:
            errors.append(f"{path}.renderer: must be one of {sorted(VALID_RENDERERS)}")
        if scene.get("status") not in VALID_STATUSES:
            errors.append(f"{path}.status: must be one of {sorted(VALID_STATUSES)}")

        effect_candidates = scene.get("effectCandidates")
        if "effectCandidates" not in scene:
            errors.append(f"{path}.effectCandidates: missing required field")
        elif not isinstance(effect_candidates, list):
            errors.append(f"{path}.effectCandidates: must be a list")
        elif len(effect_candidates) == 0 and "why" not in str(scene.get("notes", "")).lower():
            errors.append(
                f"{path}.effectCandidates: empty list requires notes explaining why no existing effect fits"
            )

        for list_field in ("assetsNeeded", "sfxCues"):
            if list_field in scene and not isinstance(scene[list_field], list):
                errors.append(f"{path}.{list_field}: must be a list")


def validate_storyboard(data: Any) -> list[str]:
    errors: list[str] = []
    root = require_mapping(data, "$", errors)

    video = require_mapping(root.get("video"), "video", errors)
    sections = require_list(root.get("sections"), "sections", errors)
    scenes = require_list(root.get("scenes"), "scenes", errors)

    if video:
        validate_video(video, errors)
    section_ids = validate_sections(sections, errors)
    validate_scenes(scenes, section_ids, errors)

    if not sections:
        errors.append("sections: must contain at least one section")
    if not scenes:
        errors.append("scenes: must contain at least one scene")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a vibe-director storyboard.json file.")
    parser.add_argument("storyboard", type=Path, help="Path to storyboard.json")
    parser.add_argument("--quiet", action="store_true", help="Only print errors")
    args = parser.parse_args()

    data = load_json(args.storyboard)
    errors = validate_storyboard(data)

    if errors:
        print(f"FAIL: {args.storyboard} has {len(errors)} validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    if not args.quiet:
        scene_count = len(data.get("scenes", []))
        section_count = len(data.get("sections", []))
        print(f"PASS: {args.storyboard} is valid ({section_count} section(s), {scene_count} scene(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
