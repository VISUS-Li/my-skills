#!/usr/bin/env python3
"""Timing patch helpers for Review Studio."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from review_core import append_history, propagate_stale, utc_now


def load_vo_timing(root: Path, segment: str) -> dict[str, Any]:
    path = root / "segments" / segment / "vo_timing.json"
    if not path.exists():
        return {"segment_id": segment, "total_sec": 0, "beats": []}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_vo_timing(root: Path, segment: str, data: dict[str, Any]) -> None:
    path = root / "segments" / segment / "vo_timing.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def recompute_starts(beats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    t = 0.0
    for beat in beats:
        dur = float(beat.get("duration_sec", 0))
        beat["start_sec"] = round(t, 3)
        beat["end_sec"] = round(t + dur, 3)
        chars = int(beat.get("char_count", 0))
        beat["cps"] = round(chars / dur, 2) if dur else 0
        t += dur
    return beats


def patch_beat_timing(
    root: Path,
    segment: str,
    beat_id: str,
    *,
    duration_sec: float | None = None,
    locked: bool | None = None,
) -> dict[str, Any]:
    data = load_vo_timing(root, segment)
    beats = data.get("beats", [])
    found = False
    for beat in beats:
        if beat.get("beat_id") != beat_id:
            continue
        found = True
        if duration_sec is not None:
            beat["duration_sec"] = round(duration_sec, 3)
            beat["source"] = "manual"
        if locked is not None:
            beat["locked"] = locked
        if duration_sec is not None or locked:
            beat.setdefault("source", "manual")
    if not found:
        raise KeyError(beat_id)

    beats = recompute_starts(beats)
    data["beats"] = beats
    data["total_sec"] = round(beats[-1]["end_sec"], 3) if beats else 0
    save_vo_timing(root, segment, data)

    rel = f"segments/{segment}/vo_timing.json"
    stale = propagate_stale(root, rel, note=f"manual timing patch {beat_id}", segment_id=segment)
    append_history(root, {
        "type": "timing_patched",
        "beat_id": beat_id,
        "segment_id": segment,
        "duration_sec": duration_sec,
        "locked": locked,
        "at": utc_now(),
    })
    return {"beat_id": beat_id, "vo_timing": data, "stale": stale}


def patch_micro_event(
    root: Path,
    segment: str,
    event_id: str,
    t: float,
) -> dict[str, Any]:
    path = root / "segments" / segment / "micro_timing.json"
    if not path.exists():
        raise FileNotFoundError(str(path))
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    events: list[dict[str, Any]]
    wrap_dict = False
    if isinstance(raw, list):
        events = raw
    else:
        events = raw.get("events", [])
        wrap_dict = True
    found = False
    for ev in events:
        eid = ev.get("id") or ev.get("event_id")
        if eid == event_id:
            ev["t"] = round(t, 3)
            ev["manual_override"] = True
            found = True
            break
    if not found:
        raise KeyError(event_id)

    if wrap_dict:
        raw["events"] = events
        path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        path.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    rel = f"segments/{segment}/micro_timing.json"
    stale = propagate_stale(root, rel, note=f"micro event {event_id} patched", segment_id=segment)
    return {"event_id": event_id, "t": t, "stale": stale}


def audio_summary(root: Path, segment: str) -> dict[str, Any]:
    vo = load_vo_timing(root, segment)
    beats = vo.get("beats", [])
    planned_total = sum(float(b.get("planned_sec", 0)) for b in beats)
    actual_total = float(vo.get("total_sec", 0))
    drift_beats = []
    for b in beats:
        planned = float(b.get("planned_sec", 0))
        actual = float(b.get("duration_sec", 0))
        drift = round(actual - planned, 3)
        cps = float(b.get("cps", 0))
        band = "ok"
        if cps < 3.5 or cps > 7.5:
            band = "fail"
        elif cps < 4.0 or cps > 6.5:
            band = "warn"
        if abs(drift) > 0.3:
            drift_beats.append({
                "beat_id": b.get("beat_id"),
                "planned_sec": planned,
                "duration_sec": actual,
                "drift_sec": drift,
                "cps": cps,
                "cps_band": band,
                "locked": bool(b.get("locked")),
            })
    return {
        "segment_id": segment,
        "planned_total_sec": round(planned_total, 3),
        "actual_total_sec": round(actual_total, 3),
        "drift_total_sec": round(actual_total - planned_total, 3),
        "beat_count": len(beats),
        "drift_beats": drift_beats,
    }
