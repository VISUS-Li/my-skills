#!/usr/bin/env python3
"""Measure actual VO durations per beat; write segments/<seg>/vo_timing.json."""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


def probe_dur(wav: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(wav)]
    )
    return float(json.loads(out)["format"]["duration"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure segment VO beat durations from WAV files.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("segment_id", help="Segment id e.g. S001")
    parser.add_argument("--beats-dir", default="audio/stems/voice/beats", help="Beat WAV directory")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    beats_dir = root / args.beats_dir
    seg = args.segment_id.upper()

    rows = []
    t = 0.0
    with (root / "script/narration_beats.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["segment_id"].upper() != seg:
                continue
            bid = row["beat_id"]
            wav = beats_dir / f"{bid}.wav"
            if not wav.exists():
                print(f"missing: {wav}", file=sys.stderr)
                return 1
            dur = probe_dur(wav)
            chars = int(row["char_count"])
            rows.append({
                "beat_id": bid,
                "start_sec": round(t, 3),
                "duration_sec": round(dur, 3),
                "end_sec": round(t + dur, 3),
                "char_count": chars,
                "cps": round(chars / dur, 2) if dur else 0,
                "planned_sec": float(row["duration_sec"]),
            })
            t += dur

    if not rows:
        print(f"no beats for segment {seg}", file=sys.stderr)
        return 1

    out = root / "segments" / seg / "vo_timing.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"segment_id": seg, "total_sec": round(t, 3), "beats": rows}
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for r in rows:
        print(f"{r['beat_id']} {r['start_sec']}-{r['end_sec']}s  {r['duration_sec']}s  {r['cps']} cps")
    print(f"total {payload['total_sec']} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
