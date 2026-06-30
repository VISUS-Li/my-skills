#!/usr/bin/env python3
"""Build script/rhythm_map.json and optionally draft audio/prosody_plan.csv.

This converts narration beats into director timing decisions: pace, read time,
lead-in, post-hold, and focal ownership. It is a scaffold for human/agent taste,
not a substitute for review.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from beat_csv_utils import narration_char_count, planned_duration_sec


PACE_BY_TYPE = {
    "hook": "normal",
    "proof": "slow",
    "mechanism": "normal",
    "compare": "normal",
    "reveal": "slow",
    "transition": "quick",
    "takeaway": "normal",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def parse_asset_plan(root: Path) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for path in (root / "segments").glob("*/beat_asset_plan.csv"):
        for row in read_csv(path):
            bid = (row.get("beat_id") or "").strip()
            if bid:
                out[bid] = row
    return out


def load_prosody(path: Path) -> dict[str, dict[str, str]]:
    return {(r.get("beat_id") or "").strip(): r for r in read_csv(path) if r.get("beat_id")}


def infer_beat_type(row: dict[str, str]) -> str:
    explicit = (row.get("beat_type") or "").strip().lower()
    if explicit:
        return explicit
    role = f"{row.get('retention_role', '')} {row.get('semantic_action', '')}".lower()
    zh = f"{row.get('retention_role', '')} {row.get('semantic_action', '')}"
    if any(k in role for k in ["hook", "question"]):
        return "hook"
    if any(k in role for k in ["proof", "source", "quote"]) or any(k in zh for k in ["证据", "来源", "证明", "引用"]):
        return "proof"
    if any(k in role for k in ["compare", "contrast"]) or any(k in zh for k in ["对比", "比较"]):
        return "compare"
    if any(k in role for k in ["reveal", "twist"]) or any(k in zh for k in ["转折", "揭示", "反转"]):
        return "reveal"
    if any(k in role for k in ["transition"]) or any(k in zh for k in ["过渡", "承接"]):
        return "transition"
    if any(k in role for k in ["takeaway", "conclusion"]) or any(k in zh for k in ["总结", "结论"]):
        return "takeaway"
    return "mechanism"


def density(row: dict[str, str], chars: int, duration: float) -> str:
    explicit = (row.get("information_density") or "").strip().lower()
    if explicit:
        return explicit
    cps = chars / duration if duration else 0
    if cps > 6.2 or any(x in row.get("narration", "") for x in "0123456789%"):
        return "high"
    if cps < 3.8:
        return "low"
    return "medium"


def read_time(beat_type: str, info_density: str, asset_row: dict[str, str] | None) -> float:
    raw = (asset_row or {}).get("visual_read_time_sec") or ""
    try:
        if raw:
            return max(0.3, float(raw))
    except ValueError:
        pass
    base = {
        "hook": 0.7,
        "proof": 1.4,
        "mechanism": 1.0,
        "compare": 1.2,
        "reveal": 1.0,
        "transition": 0.5,
        "takeaway": 1.0,
    }.get(beat_type, 1.0)
    if info_density == "high":
        base += 0.35
    elif info_density == "low":
        base -= 0.2
    return round(max(0.35, base), 2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build director rhythm map from narration beats and asset plans.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--write-prosody", action="store_true", help="Create/update audio/prosody_plan.csv from narration beats")
    parser.add_argument("--overwrite-prosody", action="store_true", help="Overwrite existing prosody rows instead of preserving them")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    beats = read_csv(root / "script" / "narration_beats.csv")
    if not beats:
        raise SystemExit("missing or empty script/narration_beats.csv")

    asset_by_beat = parse_asset_plan(root)
    prosody_path = root / "audio" / "prosody_plan.csv"
    existing_prosody = {} if args.overwrite_prosody else load_prosody(prosody_path)

    rhythm_beats: list[dict[str, Any]] = []
    prosody_rows: list[dict[str, Any]] = []
    t_by_segment: dict[str, float] = {}
    for row in beats:
        bid = (row.get("beat_id") or "").strip()
        if not bid:
            continue
        seg = (row.get("segment_id") or "S001").upper()
        dur = planned_duration_sec(row)
        chars = narration_char_count(row)
        btype = infer_beat_type(row)
        info = density(row, chars, dur)
        asset_row = asset_by_beat.get(bid, {})
        prosody = existing_prosody.get(bid, {})
        pace = (prosody.get("pace") or PACE_BY_TYPE.get(btype, "normal")).strip()
        pre_pause = int(float(prosody.get("pre_pause_ms") or (180 if btype in {"proof", "reveal"} else 80 if btype == "mechanism" else 0)))
        post_pause = int(float(prosody.get("post_pause_ms") or (320 if info == "high" or btype in {"proof", "reveal"} else 160)))
        spoken_focus = row.get("spoken_focus") or asset_row.get("caption_hint") or row.get("semantic_action") or row.get("narration", "")[:16]
        focal_owner = asset_row.get("focal_owner") or asset_row.get("primary_asset") or "primary_visual_actor"
        min_read = read_time(btype, info, asset_row)
        lead = round(pre_pause / 1000, 3)
        hold = round(post_pause / 1000, 3)
        start = t_by_segment.get(seg, 0.0)
        t_by_segment[seg] = start + dur

        rhythm_beats.append({
            "beat_id": bid,
            "segment_id": seg,
            "narration": row.get("narration", ""),
            "spoken_focus": spoken_focus,
            "beat_type": btype,
            "information_density": info,
            "planned_start_sec": round(start, 3),
            "planned_duration_sec": round(dur, 3),
            "char_count": chars,
            "planned_cps": round(chars / dur, 2) if dur else 0,
            "min_visual_read_time_sec": min_read,
            "visual_lead_in_sec": lead,
            "post_hold_sec": hold,
            "pace": pace,
            "focal_owner": focal_owner,
            "scene_reset": btype in {"reveal"} or row.get("retention_role", "").lower() == "reset",
            "director_note": prosody.get("director_note") or f"{spoken_focus} must be visible and readable; {focal_owner} owns attention.",
        })

        if args.write_prosody:
            existing = existing_prosody.get(bid, {})
            prosody_rows.append({
                "beat_id": bid,
                "segment_id": seg,
                "tts_text": existing.get("tts_text") or row.get("narration", ""),
                "pace": pace,
                "pre_pause_ms": pre_pause,
                "post_pause_ms": post_pause,
                "emphasis_words": existing.get("emphasis_words") or spoken_focus,
                "breath_after": existing.get("breath_after") or ("yes" if post_pause >= 250 else "no"),
                "tone": existing.get("tone") or btype,
                "allow_disfluency": existing.get("allow_disfluency") or "no",
                "director_note": existing.get("director_note") or "",
            })

    payload = {
        "version": "v001",
        "timebase": "seconds",
        "generated_by": "scripts/build_director_rhythm.py",
        "policy": {
            "voice_first": True,
            "rhythm_is_comprehension_time": True,
            "one_focal_owner_per_moment": True,
            "evidence_needs_read_time": True,
        },
        "beats": rhythm_beats,
    }
    out = root / "script" / "rhythm_map.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(rhythm_beats)} rhythm beats -> {out}")

    if args.write_prosody:
        write_csv(prosody_path, prosody_rows, [
            "beat_id", "segment_id", "tts_text", "pace", "pre_pause_ms", "post_pause_ms",
            "emphasis_words", "breath_after", "tone", "allow_disfluency", "director_note",
        ])
        print(f"wrote {len(prosody_rows)} prosody rows -> {prosody_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

