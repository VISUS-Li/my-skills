#!/usr/bin/env python3
"""Draft an audio cue sheet from a director-grade beat timeline.

This script creates beat-level cue candidates, not final sound design. The goal is
to force an explicit decision for each visible action: hit, tick, whoosh, ambience,
silence, or no cue.
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


def classify_sound(beat: dict[str, Any]) -> tuple[str, str, float, float, int]:
    text = words(beat).lower()
    if any(k in text for k in ["silence", "停顿", "留白", "drop"]):
        return "silence", "deliberate short silence or music dip before/after the reveal", 0.28, -99.0, 1
    if any(k in text for k in ["stamp", "盖章", "红章", "error", "错误", "x mark", "red x"]):
        return "sfx_impact", "dry rubber stamp hit with a tiny paper slap, short and punchy", 0.22, -10.0, 1
    if any(k in text for k in ["success", "green", "check", "通过", "勾", "完成"]):
        return "sfx_success", "small glassy success chime with soft high sparkle", 0.42, -13.0, 2
    if any(k in text for k in ["arrow", "pipeline", "conveyor", "流", "管线", "箭头"]):
        return "sfx_motion", "short data whoosh or conveyor tick following the arrow movement", 0.35, -16.0, 3
    if any(k in text for k in ["card", "panel", "卡片", "弹出", "snap", "切换"]):
        return "sfx_ui", "soft card snap with light paper/plastic tactile click", 0.18, -17.0, 3
    if any(k in text for k in ["device", "screen", "phone", "computer", "ui", "cursor", "手机", "电脑", "屏幕"]):
        return "sfx_ui", "clean modern UI tap or cursor tick, very short", 0.14, -18.0, 3
    if any(k in text for k in ["draw", "stroke", "line", "绘制", "描边", "扫描", "scan"]):
        return "sfx_texture", "light pencil/SVG stroke draw or scanner sweep, subtle", 0.38, -19.0, 4
    if any(k in text for k in ["robot", "machine", "机器", "processing", "处理", "module", "模块"]):
        return "sfx_mech", "tiny friendly robot servo or machine processing blip", 0.32, -18.0, 4
    if any(k in text for k in ["zoom", "push", "pan", "camera", "运镜", "推进", "转场"]):
        return "sfx_transition", "air-light motion whoosh matched to camera move", 0.45, -16.0, 3
    return "no_cue_or_micro_tick", "usually no cue; add only if the beat needs feedback under narration", 0.12, -22.0, 5


def make_cue(beat: dict[str, Any], index: int) -> dict[str, Any]:
    cue_type, concept, duration, gain, priority = classify_sound(beat)
    beat_id = str(beat.get("beat_id") or f"B{index+1:03d}")
    start = float(beat.get("start_sec", 0) or 0)
    if cue_type == "silence":
        track = "silence"
    elif cue_type.startswith("sfx"):
        track = "sfx"
    else:
        track = "sfx"
    return {
        "cue_id": f"SFX_{beat_id}",
        "type": cue_type,
        "track": track,
        "segment_id": str(beat.get("segment_id", "unknown")),
        "start_sec": round(start, 3),
        "duration_sec": round(duration, 3),
        "sync_anchor": f"{beat_id}: {str(beat.get('visual_action', 'visual action'))[:120]}",
        "role": "beat-level feedback synced to narration and visible motion",
        "sound_concept": concept,
        "search_terms": [],
        "generation_prompt": concept + "; short, clean, voice-safe, no copyrighted source",
        "source": "to_source_or_generate",
        "path_or_url": "",
        "gain_db": gain,
        "fade_in_ms": 5 if duration < 0.2 else 15,
        "fade_out_ms": 30 if duration < 0.4 else 80,
        "duck_under_voice": False,
        "priority": priority,
        "rights_status": "needed",
        "status": "planned",
        "notes": "Generated from script/beat_timeline.json; adjust by ear and remove decorative cues that fight narration."
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Draft beat-level audio cues from script/beat_timeline.json.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite audio/audio_cue_sheet.json")
    parser.add_argument("--append", action="store_true", help="Append to existing audio/audio_cue_sheet.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    timeline = load_json(root / "script" / "beat_timeline.json", {"beats": []})
    beats = timeline.get("beats", [])
    if not isinstance(beats, list) or not beats:
        print("No beats found in script/beat_timeline.json")
        return 1

    out = root / "audio" / "audio_cue_sheet.json"
    existing = load_json(out, {"version": "v001", "timebase": "seconds", "cues": []}) if out.exists() else {"version": "v001", "timebase": "seconds", "cues": []}
    if out.exists() and not (args.overwrite or args.append):
        print(f"Refusing to overwrite existing file: {out}")
        print("Use --overwrite to replace, or --append to add missing beat-level cues.")
        return 2

    new_cues = [make_cue(b, i) for i, b in enumerate(beats) if isinstance(b, dict)]
    if args.append and existing.get("cues"):
        seen = {str(c.get("cue_id")) for c in existing.get("cues", []) if isinstance(c, dict)}
        cues = list(existing.get("cues", [])) + [c for c in new_cues if c["cue_id"] not in seen]
    else:
        cues = new_cues

    result = {
        "version": "v001",
        "timebase": "seconds",
        "policy": {
            "voice_first": True,
            "beat_level_sync": True,
            "avoid_sfx_on_every_cut": True,
            "sfx_must_have_visual_anchor": True,
            "final_loudness_check_required": True
        },
        "cues": cues,
        "notes": [
            "This is a first-pass beat cue sheet. It must be listened to and simplified by a human/editorial pass.",
            "Keep only cues that clarify action, mark contrast, or add tactile feedback; delete ornamental noise."
        ]
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out} with {len(cues)} cues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
