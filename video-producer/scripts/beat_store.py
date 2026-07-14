#!/usr/bin/env python3
"""Single source of truth for narration beats: outputs/beat_plan.json."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def beat_plan_path(root: Path) -> Path:
    return root / "outputs" / "beat_plan.json"


def segment_spec_path(root: Path) -> Path:
    return root / "outputs" / "segment_spec.json"


def vo_timing_path(root: Path, segment: str) -> Path:
    return root / "segments" / segment.upper() / "vo_timing.json"


def micro_timing_path(root: Path, segment: str) -> Path:
    return root / "segments" / segment.upper() / "micro_timing.json"


def char_count(text: str) -> int:
    return len((text or "").replace(" ", ""))


def duration_from_time(value: Any) -> float:
    if isinstance(value, list) and len(value) == 2:
        try:
            return max(0.0, round(float(value[1]) - float(value[0]), 3))
        except (TypeError, ValueError):
            return 0.0
    return 0.0


def load_beat_plan(root: Path) -> dict[str, Any]:
    path = beat_plan_path(root)
    if not path.exists():
        return {"version": "1", "style": "", "duration": 0, "beats": []}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_beat_plan(root: Path, data: dict[str, Any]) -> None:
    path = beat_plan_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_segment_spec(root: Path) -> dict[str, Any]:
    path = segment_spec_path(root)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def default_segment(root: Path) -> str:
    spec = load_segment_spec(root)
    seg = str(spec.get("segment_id") or "S001").upper()
    return seg if seg.startswith("S") else "S001"


def beat_by_id(plan: dict[str, Any], beat_id: str) -> dict[str, Any] | None:
    for beat in plan.get("beats", []):
        if isinstance(beat, dict) and str(beat.get("beat_id", "")).lower() == beat_id.lower():
            return beat
    return None


def list_beats(root: Path, segment: str | None = None) -> list[dict[str, Any]]:
    """Unified beat rows for Review Studio and TTS."""
    plan = load_beat_plan(root)
    seg = (segment or default_segment(root)).upper()
    vo_path = vo_timing_path(root, seg)
    vo_beats: dict[str, dict[str, Any]] = {}
    if vo_path.exists():
        vo_data = json.loads(vo_path.read_text(encoding="utf-8-sig"))
        for beat in vo_data.get("beats", []):
            if isinstance(beat, dict) and beat.get("beat_id"):
                vo_beats[str(beat["beat_id"]).lower()] = beat

    rows: list[dict[str, Any]] = []
    for beat in plan.get("beats", []):
        if not isinstance(beat, dict):
            continue
        bid = str(beat.get("beat_id") or "")
        if not bid:
            continue
        t = beat.get("time") or [0, 0]
        start = float(t[0]) if isinstance(t, list) and len(t) >= 1 else 0.0
        planned = duration_from_time(t)
        voice = str(beat.get("voice_text") or "")
        vo = vo_beats.get(bid.lower(), {})
        actual = float(vo.get("duration_sec") or 0)
        merged: dict[str, Any] = {
            "segment_id": seg,
            "beat_id": bid,
            "start_sec": start,
            "duration_sec": planned,
            "planned_sec": planned,
            "actual_sec": actual if actual else None,
            "drift_sec": round(actual - planned, 3) if actual and planned else None,
            "narration": voice,
            "voice_text": voice,
            "spoken_focus": beat.get("keyword", ""),
            "keyword": beat.get("keyword", ""),
            "semantic_action": beat.get("intent", ""),
            "intent": beat.get("intent", ""),
            "visual_owner": beat.get("visual_owner", ""),
            "visual_action": beat.get("visual_action", ""),
            "visual_need": beat.get("visual_action", ""),
            "beat_type": beat.get("intent", ""),
            "information_density": "medium",
            "char_count": char_count(voice),
            "audio_cue": beat.get("audio_cue", ""),
            "subtitle_strategy": beat.get("subtitle_strategy", ""),
            "playback_rate": float(vo.get("playback_rate") or 1.0),
            "source_duration_sec": float(vo.get("source_duration_sec") or actual or 0) or None,
            "disabled": bool(vo.get("disabled")),
            "vo": vo,
        }
        cps = float(vo.get("cps") or 0)
        if not cps and merged["char_count"] and actual:
            cps = merged["char_count"] / actual
        merged["cps_band"] = _cps_band(cps) if cps else "unknown"
        wav = root / "audio" / "stems" / "voice" / "beats" / f"{bid}.wav"
        merged["vo_wav"] = wav.relative_to(root).as_posix() if wav.exists() else None
        rows.append(merged)
    return rows


def _cps_band(cps: float) -> str:
    if cps < 3.5 or cps > 7.5:
        return "fail"
    if cps < 4.0 or cps > 6.5:
        return "warn"
    return "ok"


def patch_beat(
    root: Path,
    beat_id: str,
    *,
    voice_text: str | None = None,
    intent: str | None = None,
    visual_action: str | None = None,
) -> dict[str, Any] | None:
    plan = load_beat_plan(root)
    found = beat_by_id(plan, beat_id)
    if not found:
        return None
    if voice_text is not None:
        found["voice_text"] = voice_text
    if intent is not None:
        found["intent"] = intent
    if visual_action is not None:
        found["visual_action"] = visual_action
    save_beat_plan(root, plan)
    return found


def sync_script_from_plan(root: Path) -> str | None:
    """Append synced voice lines to outputs/script.md if a marker block exists."""
    script_path = root / "outputs" / "script.md"
    if not script_path.exists():
        return None
    lines = [str(b.get("voice_text") or "").strip() for b in load_beat_plan(root).get("beats", []) if isinstance(b, dict)]
    block = "\n\n".join(line for line in lines if line)
    text = script_path.read_text(encoding="utf-8-sig")
    start = "<!-- beat-plan-voice:start -->"
    end = "<!-- beat-plan-voice:end -->"
    if start in text and end in text:
        before, rest = text.split(start, 1)
        _, after = rest.split(end, 1)
        text = f"{before}{start}\n{block}\n{end}{after}"
    else:
        text = text.rstrip() + f"\n\n{start}\n{block}\n{end}\n"
    script_path.write_text(text, encoding="utf-8")
    return str(script_path)


def build_micro_timing_from_spec(root: Path, segment: str | None = None) -> list[dict[str, Any]]:
    spec = load_segment_spec(root)
    seg = (segment or default_segment(root)).upper()
    events: list[dict[str, Any]] = []
    for shot in spec.get("shots", []) if isinstance(spec, dict) else []:
        if not isinstance(shot, dict):
            continue
        parents = shot.get("narration_beats") or []
        parent = str(parents[0]) if parents else ""
        for idx, action in enumerate(shot.get("visual_actions", []), start=1):
            if not isinstance(action, dict):
                continue
            event_id = f"{shot.get('shot_id', 'shot')}_ev{idx:03d}"
            events.append({
                "id": event_id,
                "event_id": event_id,
                "t": float(action.get("at") or 0),
                "type": action.get("type", ""),
                "visual_action": action.get("type", ""),
                "parent": parent,
                "segment_id": seg,
                "text": action.get("text", ""),
                "sfx": action.get("sfx", ""),
            })
    return events


def ensure_micro_timing(root: Path, segment: str | None = None) -> Path:
    seg = (segment or default_segment(root)).upper()
    path = micro_timing_path(root, seg)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        events = build_micro_timing_from_spec(root, seg)
        path.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def director_beats(root: Path, segment: str | None = None) -> list[dict[str, Any]]:
    beats = list_beats(root, segment)
    enriched: list[dict[str, Any]] = []
    for beat in beats:
        item = dict(beat)
        item["visual_sync"] = {
            "spoken_focus": beat.get("keyword", ""),
            "focal_owner": beat.get("visual_owner", ""),
            "must_show_detail": beat.get("visual_action", ""),
        }
        item["asset_plan"] = {}
        item["focal_owner"] = beat.get("visual_owner", "")
        item["primary_asset"] = ""
        item["density_target"] = beat.get("information_density", "medium")
        enriched.append(item)
    return enriched


def is_video_project(root: Path) -> bool:
    root = root.resolve()
    outputs = root / "outputs"
    return (
        (outputs / "beat_plan.json").is_file()
        or (outputs / "segment_spec.json").is_file()
        or (outputs / "script.md").is_file()
    )
