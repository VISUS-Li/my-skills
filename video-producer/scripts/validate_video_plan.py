#!/usr/bin/env python3
"""Validate structural, timing, and asset invariants in video-plan.json."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from video_plan_utils import load_json, media_path, resolve_project_and_plan, safe_relative_media_path


POSE_NAMES = {
    "full",
    "center",
    "close-left",
    "close-right",
    "wide-left",
    "wide-right",
    "card-left",
    "card-right",
    "offscreen-left",
    "offscreen-right",
}
POSE_FIELDS = {
    "scale",
    "tx",
    "ty",
    "insetT",
    "insetR",
    "insetB",
    "insetL",
    "radius",
    "border",
    "shadow",
    "background",
    "gradL",
    "gradR",
    "opacity",
}


def number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate(plan: dict[str, Any], project: Path, check_assets: bool) -> list[str]:
    errors: list[str] = []
    if plan.get("version") != 1:
        errors.append("version must equal 1")

    video = plan.get("video")
    if not isinstance(video, dict):
        return errors + ["video must be an object"]
    mode = video.get("timingMode")
    if mode not in {"voice", "music", "fixed"}:
        errors.append("video.timingMode must be voice, music, or fixed")
    for field in ("fps", "width", "height", "durationSec"):
        if not number(video.get(field)) or float(video[field]) <= 0:
            errors.append(f"video.{field} must be positive")
    fps = float(video.get("fps") or 30)
    duration = float(video.get("durationSec") or 0)
    tolerance = 1 / fps

    style = plan.get("style")
    if not isinstance(style, dict):
        errors.append("style must be an object")

    stage = plan.get("stage")
    subject = stage.get("subject") if isinstance(stage, dict) else None
    stage_pose_map = stage.get("poses", {}) if isinstance(stage, dict) else {}
    if not isinstance(stage_pose_map, dict):
        errors.append("stage.poses must be an object")
        stage_pose_map = {}
    for pose_name, target in stage_pose_map.items():
        label = f"stage.poses.{pose_name}"
        if not isinstance(pose_name, str) or not pose_name:
            errors.append("stage.poses keys must be non-empty strings")
            continue
        if not isinstance(target, dict):
            errors.append(f"{label} must be an object")
            continue
        for field, value in target.items():
            if field not in POSE_FIELDS:
                errors.append(f"{label}.{field} is unsupported")
            elif not number(value):
                errors.append(f"{label}.{field} must be numeric")
            elif field in {"scale", "radius"} and float(value) < 0:
                errors.append(f"{label}.{field} must be non-negative")
            elif field in {"border", "shadow", "background", "gradL", "gradR", "opacity"} and not (
                0 <= float(value) <= 1
            ):
                errors.append(f"{label}.{field} must be between 0 and 1")
            elif field.startswith("inset") and not (0 <= float(value) <= 100):
                errors.append(f"{label}.{field} must be between 0 and 100")
    available_pose_names = POSE_NAMES | set(stage_pose_map)

    scenes = plan.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        errors.append("scenes must be a non-empty array")
        scenes = []
    scene_ids: set[str] = set()
    for index, scene in enumerate(scenes):
        label = f"scenes[{index}]"
        if not isinstance(scene, dict):
            errors.append(f"{label} must be an object")
            continue
        scene_id = str(scene.get("id") or "")
        if not scene_id:
            errors.append(f"{label}.id is required")
        elif scene_id in scene_ids:
            errors.append(f"duplicate scene id: {scene_id}")
        scene_ids.add(scene_id)
        if not str(scene.get("type") or ""):
            errors.append(f"{label}.type is required")
        start = scene.get("startSec")
        length = scene.get("durationSec")
        if not number(start) or float(start) < 0:
            errors.append(f"{label}.startSec must be non-negative")
        if not number(length) or float(length) <= 0:
            errors.append(f"{label}.durationSec must be positive")
        if number(start) and number(length) and float(start) + float(length) > duration + tolerance:
            errors.append(f"{label} exceeds video.durationSec")
        if not isinstance(scene.get("props"), dict):
            errors.append(f"{label}.props must be an object")
        pose = scene.get("pose")
        if pose is not None and pose not in available_pose_names:
            errors.append(f"{label}.pose is unsupported: {pose}")
        if "continuousSubject" in scene and not isinstance(scene["continuousSubject"], bool):
            errors.append(f"{label}.continuousSubject must be boolean")
        if pose is not None and scene.get("continuousSubject") is False:
            errors.append(f"{label}.pose conflicts with continuousSubject=false")

    poses = plan.get("poses", [])
    has_scene_pose = any(isinstance(scene, dict) and scene.get("pose") for scene in scenes)
    has_subject_scene = any(
        isinstance(scene, dict)
        and (scene.get("continuousSubject") is True or bool(scene.get("pose")))
        for scene in scenes
    )
    if (poses or has_subject_scene) and not isinstance(subject, dict):
        errors.append("stage.subject is required when poses or scene.pose are used")
    if has_subject_scene and not poses and not has_scene_pose:
        errors.append("continuousSubject=true requires poses or scene.pose")
    if isinstance(subject, dict):
        subject_type = subject.get("type", "card")
        if subject_type not in {"card", "image", "video"}:
            errors.append("stage.subject.type must be card, image, or video")
        source = str(subject.get("src") or "")
        if subject_type == "image":
            if not safe_relative_media_path(source):
                errors.append("stage.subject.src must be a safe relative path for image subjects")
            elif check_assets and not media_path(project, source).exists():
                errors.append(f"stage.subject.src does not exist: {source}")
        if subject_type == "video":
            sources = {
                key: str(subject.get(key) or "")
                for key in ("src", "proxySrc", "masterSrc")
                if subject.get(key)
            }
            if not sources:
                errors.append("stage.subject video requires src, proxySrc, or masterSrc")
            for source_key, source_value in sources.items():
                if not safe_relative_media_path(source_value):
                    errors.append(
                        f"stage.subject.{source_key} must be a safe relative path for video subjects"
                    )
                elif check_assets and not media_path(project, source_value).exists():
                    errors.append(f"stage.subject.{source_key} does not exist: {source_value}")
        audio_mode = subject.get("audioMode", "muted")
        if audio_mode not in {"muted", "media"}:
            errors.append("stage.subject.audioMode must be muted or media")

    if not isinstance(poses, list):
        errors.append("poses must be an array")
        poses = []
    previous_pose_at = -1.0
    pose_times: set[float] = set()
    for index, pose in enumerate(poses):
        label = f"poses[{index}]"
        if not isinstance(pose, dict):
            errors.append(f"{label} must be an object")
            continue
        at_sec = pose.get("atSec")
        if not number(at_sec) or float(at_sec) < 0:
            errors.append(f"{label}.atSec must be non-negative")
        else:
            at_value = float(at_sec)
            if at_value + tolerance < previous_pose_at:
                errors.append("poses must be sorted by atSec")
            if at_value in pose_times:
                errors.append(f"duplicate pose atSec: {at_value:g}")
            if at_value > duration + tolerance:
                errors.append(f"{label} exceeds video.durationSec")
            previous_pose_at = at_value
            pose_times.add(at_value)
        if pose.get("pose") not in available_pose_names:
            errors.append(f"{label}.pose is unsupported: {pose.get('pose')}")
        transition = pose.get("transitionSec", 0)
        if not number(transition) or float(transition) < 0:
            errors.append(f"{label}.transitionSec must be non-negative")

    tracks = plan.get("voice", {}).get("tracks", [])
    beat_ids: set[str] = set()
    previous_end = 0.0
    for index, track in enumerate(tracks):
        label = f"voice.tracks[{index}]"
        beat_id = str(track.get("beatId") or "")
        if not beat_id:
            errors.append(f"{label}.beatId is required")
        elif beat_id in beat_ids:
            errors.append(f"duplicate beatId: {beat_id}")
        beat_ids.add(beat_id)
        start = float(track.get("startSec") or 0)
        length = float(track.get("durationSec") or 0)
        if length <= 0:
            errors.append(f"{label}.durationSec must be positive")
        if start + tolerance < previous_end:
            errors.append(f"{label} overlaps the preceding voice track")
        previous_end = max(previous_end, start + length)
        source = str(track.get("src") or "")
        if not safe_relative_media_path(source):
            errors.append(f"{label}.src must be a safe relative path")
        elif check_assets and not media_path(project, source).exists():
            errors.append(f"{label}.src does not exist: {source}")

    if mode == "voice" and not tracks:
        errors.append("timingMode=voice requires voice.tracks")
    if mode == "music" and not plan.get("musicBeats"):
        errors.append("timingMode=music requires musicBeats")
    for scene in scenes:
        for beat_id in scene.get("beatIds", []):
            if str(beat_id) not in beat_ids:
                errors.append(f"scene {scene.get('id')} references unknown beatId: {beat_id}")

    captions = plan.get("captions", {})
    page_ms = captions.get("combineTokensWithinMs", 1200)
    if not number(page_ms) or float(page_ms) < 250:
        errors.append("captions.combineTokensWithinMs must be at least 250")
    cues = captions.get("cues", [])
    for index, cue in enumerate(cues):
        label = f"captions.cues[{index}]"
        if not isinstance(cue, dict):
            errors.append(f"{label} must be an object")
            continue
        start = cue.get("startMs")
        end = cue.get("endMs")
        if not number(start) or not number(end) or float(start) < 0 or float(end) <= float(start or 0):
            errors.append(f"{label} has invalid startMs/endMs")
        if not str(cue.get("text") or "").strip():
            errors.append(f"{label}.text is empty")
        if number(end) and float(end) > duration * 1000 + tolerance * 1000:
            errors.append(f"{label} exceeds video.durationSec")
        words = cue.get("words", [])
        if not isinstance(words, list):
            errors.append(f"{label}.words must be an array")
            continue
        previous_word_end = float(start) if number(start) else 0
        for word_index, word in enumerate(words):
            word_label = f"{label}.words[{word_index}]"
            if not isinstance(word, dict):
                errors.append(f"{word_label} must be an object")
                continue
            word_start = word.get("startMs")
            word_end = word.get("endMs")
            if (
                not number(word_start)
                or not number(word_end)
                or float(word_start) < 0
                or float(word_end) <= float(word_start or 0)
            ):
                errors.append(f"{word_label} has invalid startMs/endMs")
                continue
            if number(start) and float(word_start) < float(start):
                errors.append(f"{word_label} starts before its caption cue")
            if number(end) and float(word_end) > float(end):
                errors.append(f"{word_label} ends after its caption cue")
            if float(word_start) < previous_word_end:
                errors.append(f"{word_label} overlaps the preceding word")
            previous_word_end = max(previous_word_end, float(word_end))
            if not str(word.get("text") or ""):
                errors.append(f"{word_label}.text is empty")

    media_items: list[tuple[str, str]] = []
    bgm = plan.get("audio", {}).get("bgm")
    if isinstance(bgm, dict):
        media_items.append(("audio.bgm.src", str(bgm.get("src") or "")))
    for index, cue in enumerate(plan.get("audio", {}).get("cues", [])):
        media_items.append((f"audio.cues[{index}].src", str(cue.get("src") or "")))
    for label, source in media_items:
        if not safe_relative_media_path(source):
            errors.append(f"{label} must be a safe relative path")
        elif check_assets and not media_path(project, source).exists():
            errors.append(f"{label} does not exist: {source}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", nargs="?", default="video-plan.json", help="Project root or plan path")
    parser.add_argument("--check-assets", action="store_true", help="Require referenced audio assets to exist")
    args = parser.parse_args()
    project, plan_path = resolve_project_and_plan(args.plan)
    errors = validate(load_json(plan_path), project, args.check_assets)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"valid video plan: {plan_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
