#!/usr/bin/env python3
"""Create a first-pass audio cue sheet from storyboard and shot list.

This does not generate audio. It creates reviewable cue decisions so an agent or
editor can source/generate the right sound at the right moment.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def words(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(words(v) for v in value)
    if isinstance(value, dict):
        return " ".join(words(v) for v in value.values())
    return str(value)


def classify_transition(text: str) -> tuple[str, str]:
    t = text.lower()
    if any(k in t for k in ["glitch", "故障", "扫描", "scan", "digital", "tech"]):
        return "sfx_transition", "tight digital glitch swipe, short, clean, not harsh"
    if any(k in t for k in ["blur", "crossfade", "fade", "雾", "soft", "dream"]):
        return "sfx_transition", "soft airy whoosh into gentle dissolve"
    if any(k in t for k in ["impact", "hit", "爆", "reveal", "亮相", "cta"]):
        return "sfx_impact", "short cinematic hit with controlled low end"
    return "sfx_transition", "subtle motion whoosh matched to visual transition"


def cue(cue_id: str, cue_type: str, start: float, duration: float, segment_id: str, role: str, prompt: str, *,
        priority: int = 3, gain_db: float = -12.0, source: str = "to_source_or_generate", sync_anchor: str = "visual beat") -> dict[str, Any]:
    return {
        "cue_id": cue_id,
        "type": cue_type,
        "track": "music" if cue_type == "music" else ("ambience" if cue_type == "ambience" else "sfx"),
        "segment_id": segment_id,
        "start_sec": round(start, 3),
        "duration_sec": round(max(duration, 0.05), 3),
        "sync_anchor": sync_anchor,
        "role": role,
        "sound_concept": prompt,
        "search_terms": [],
        "generation_prompt": prompt,
        "source": source,
        "path_or_url": "",
        "gain_db": gain_db,
        "fade_in_ms": 20 if duration < 1.5 else 250,
        "fade_out_ms": 60 if duration < 1.5 else 350,
        "duck_under_voice": cue_type in {"music", "ambience"},
        "priority": priority,
        "rights_status": "needed",
        "status": "planned",
        "notes": "Review timing by ear before final mix."
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Draft audio/audio_cue_sheet.json from storyboard and shotlist.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing cue sheet")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    out = root / "audio" / "audio_cue_sheet.json"
    if out.exists() and not args.overwrite:
        print(f"Refusing to overwrite existing file: {out}")
        print("Use --overwrite or create audio/audio_cue_sheet.v002.json")
        return 2

    storyboard = load_json(root / "script" / "storyboard.json", {"segments": []})
    shotlist = load_json(root / "script" / "shotlist.json", {"shots": []})
    shots_by_seg: dict[str, list[dict[str, Any]]] = {}
    for shot in shotlist.get("shots", []):
        if isinstance(shot, dict):
            shots_by_seg.setdefault(str(shot.get("segment_id", "unknown")), []).append(shot)

    cues: list[dict[str, Any]] = []
    current = 0.0
    total_duration = 0.0
    segments = storyboard.get("segments", [])
    for seg_index, seg in enumerate(segments):
        if not isinstance(seg, dict):
            continue
        seg_id = str(seg.get("id", f"segment_{seg_index+1:03d}"))
        duration = float(seg.get("duration_sec", 0) or 0)
        total_duration += duration
        seg_text = words(seg)

        # Segment-level music/ambience bed.
        if seg_index == 0:
            cues.append(cue(
                "M001", "music", current, max(duration, 12.0), seg_id,
                "establish emotional bed and pacing",
                "music bed matching the video style, restrained under narration, clear pulse but not distracting",
                priority=4, gain_db=-20, source="music_source_or_generated"
            ))
        if any(k in seg_text.lower() for k in ["guofeng", "山水", "nature", "forest", "street", "office", "kitchen", "实验", "lab", "product"]):
            cues.append(cue(
                f"A{seg_index+1:03d}", "ambience", current, duration, seg_id,
                "add space and texture so the scene is not silent/flat",
                "subtle ambience bed derived from the visual world, barely audible under voice",
                priority=5, gain_db=-28, source="ambience_source_or_generated", sync_anchor="scene world"
            ))

        # Shots create movement, reveal, UI, and data cues.
        shot_start = current
        for shot_index, shot in enumerate(shots_by_seg.get(seg_id, [])):
            shot_dur = float(shot.get("duration_sec", 0) or 0)
            shot_text = words(shot).lower()
            if any(k in shot_text for k in ["push", "zoom", "pan", "dolly", "orbit", "parallax", "move", "运镜", "推进", "横移"]):
                cues.append(cue(
                    f"S{seg_index+1:03d}_{shot_index+1:02d}_MOVE", "sfx_transition", shot_start, 0.45, seg_id,
                    "make camera movement tactile",
                    "very short airy whoosh synced to camera move, light high-frequency tail",
                    priority=3, gain_db=-16, sync_anchor=str(shot.get("shot_id", "shot start"))
                ))
            if any(k in shot_text for k in ["reveal", "transform", "cta", "contrast", "proof", "impact", "亮相", "揭示", "转折"]):
                cues.append(cue(
                    f"S{seg_index+1:03d}_{shot_index+1:02d}_HIT", "sfx_impact", shot_start + min(0.35, max(shot_dur * 0.18, 0)), 0.65, seg_id,
                    "mark important reveal without overpowering narration",
                    "polished impact hit, tight transient, controlled low end, short reverb tail",
                    priority=2, gain_db=-10, sync_anchor=str(shot.get("shot_id", "reveal beat"))
                ))
            if any(k in shot_text for k in ["ui", "click", "interface", "cursor", "dashboard", "screen", "code", "chart", "data", "number", "数字", "图表"]):
                cues.append(cue(
                    f"S{seg_index+1:03d}_{shot_index+1:02d}_UI", "sfx_ui", shot_start + min(0.25, max(shot_dur * 0.12, 0)), 0.18, seg_id,
                    "support interface/data interaction",
                    "clean tactile UI click or data tick, modern, not cartoonish",
                    priority=3, gain_db=-18, sync_anchor=str(shot.get("shot_id", "ui/data beat"))
                ))
            shot_start += shot_dur if shot_dur > 0 else duration / max(len(shots_by_seg.get(seg_id, [])), 1)

        # Segment exit transition cue, except final unless explicitly present.
        transition_text = str(seg.get("transition_out") or seg.get("transition") or "")
        if transition_text and seg_index < len(segments) - 1:
            ctype, prompt = classify_transition(transition_text)
            cues.append(cue(
                f"T{seg_index+1:03d}", ctype, max(current + duration - 0.35, current), 0.55, seg_id,
                "motivate scene transition",
                prompt,
                priority=2, gain_db=-14, sync_anchor="transition_out"
            ))
        current += duration

    # End tag / sonic logo.
    if total_duration > 15 and segments:
        cues.append(cue(
            "END_LOGO", "sfx_logo", max(total_duration - 1.2, 0), 1.0, str(segments[-1].get("id", "final")),
            "give the video an intentional sonic ending",
            "short brand-safe sonic logo, warm final shimmer or soft resolved hit",
            priority=2, gain_db=-11, source="sonic_logo_source_or_generated", sync_anchor="final CTA/logo"
        ))

    result = {
        "version": "v001",
        "timebase": "seconds",
        "policy": {
            "voice_first": True,
            "do_not_use_unlicensed_assets": True,
            "avoid_sfx_on_every_cut": True,
            "final_loudness_check_required": True
        },
        "cues": cues,
        "notes": [
            "This is a draft. The editor/agent must listen and adjust timing/gain by ear.",
            "Do not finalize cues with rights_status=needed or do-not-use-final."
        ]
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out} with {len(cues)} planned cues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
