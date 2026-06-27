#!/usr/bin/env python3
"""Scale beat_timeline micro-events to actual VO timing (segments/<seg>/micro_timing.json)."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build micro_timing.json from VO + beat_timeline.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("segment_id", help="Segment id e.g. S001")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    seg = args.segment_id.upper()
    vo_path = root / "segments" / seg / "vo_timing.json"
    if not vo_path.exists():
        print(f"run measure_segment_vo.py first: {vo_path}", file=sys.stderr)
        return 1

    vo = json.loads(vo_path.read_text(encoding="utf-8"))
    timeline = json.loads((root / "script/beat_timeline.json").read_text(encoding="utf-8"))
    beats_actual = {b["beat_id"]: b for b in vo["beats"]}

    planned_rows: dict[str, dict] = {}
    with (root / "script/narration_beats.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["segment_id"].upper() == seg:
                planned_rows[row["beat_id"]] = {
                    "start": float(row["start_sec"]),
                    "dur": float(row["duration_sec"]),
                }

    micro = []
    for ev in timeline.get("beats", []):
        if ev.get("segment_id", "").upper() != seg:
            continue
        parts = ev["beat_id"].rsplit("_", 1)
        if len(parts) != 2:
            continue
        parent, _ = parts
        if parent not in beats_actual or parent not in planned_rows:
            continue
        p = planned_rows[parent]
        rel = (float(ev["start_sec"]) - p["start"]) / p["dur"] if p["dur"] else 0
        rel = max(0.0, min(1.0, rel))
        actual_t = beats_actual[parent]["start_sec"] + rel * beats_actual[parent]["duration_sec"]
        micro.append({
            "id": ev["beat_id"],
            "t": round(actual_t, 3),
            "type": ev.get("beat_type", ""),
            "parent": parent,
            "visual_action": ev.get("visual_action", ""),
            "sfx_cue_ids": ev.get("sfx_cue_ids", []),
        })

    out = root / "segments" / seg / "micro_timing.json"
    out.write_text(json.dumps(micro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(micro)} events -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
