#!/usr/bin/env python3
"""Lint director rhythm: pacing, prosody, read time, and measured VO drift."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from beat_csv_utils import narration_char_count, planned_duration_sec


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def main() -> int:
    parser = argparse.ArgumentParser(description="Score director rhythm readiness.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--segment", default=None, help="Optional segment id e.g. S001")
    parser.add_argument("--fail-under", type=int, default=80)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    seg_filter = args.segment.upper() if args.segment else None
    score = 100
    issues: list[tuple[str, int]] = []

    narration_rows = read_csv(root / "script" / "narration_beats.csv")
    if seg_filter:
        narration_rows = [r for r in narration_rows if r.get("segment_id", "").upper() == seg_filter]
    if not narration_rows:
        issues.append(("missing narration beats for rhythm lint", 35))

    rhythm = load_json(root / "script" / "rhythm_map.json", {})
    rhythm_rows = rhythm.get("beats", []) if isinstance(rhythm, dict) else []
    rhythm_by_beat = {str(r.get("beat_id")): r for r in rhythm_rows if isinstance(r, dict)}
    prosody_rows = read_csv(root / "audio" / "prosody_plan.csv")
    prosody_by_beat = {r.get("beat_id", ""): r for r in prosody_rows}

    if not rhythm_rows:
        issues.append(("missing or empty script/rhythm_map.json; run build_director_rhythm.py", 25))
    if not prosody_rows:
        issues.append(("missing or empty audio/prosody_plan.csv; TTS will use flat raw text", 18))

    vo_by_beat: dict[str, dict[str, Any]] = {}
    segment_ids = sorted({r.get("segment_id", "").upper() for r in narration_rows if r.get("segment_id")})
    for seg in segment_ids:
        vo_path = root / "segments" / seg / "vo_timing.json"
        if vo_path.exists():
            vo = load_json(vo_path, {})
            for b in vo.get("beats", []):
                if isinstance(b, dict) and b.get("beat_id"):
                    vo_by_beat[str(b["beat_id"])] = b

    for row in narration_rows:
        bid = row.get("beat_id", "")
        if not bid:
            continue
        dur = planned_duration_sec(row)
        chars = narration_char_count(row)
        planned_cps = chars / dur if dur else 0
        rb = rhythm_by_beat.get(bid)
        pb = prosody_by_beat.get(bid)

        if not rb:
            issues.append((f"{bid}: missing rhythm_map entry", 8))
            continue
        if not rb.get("spoken_focus"):
            issues.append((f"{bid}: rhythm_map missing spoken_focus", 5))
        if not rb.get("focal_owner"):
            issues.append((f"{bid}: rhythm_map missing focal_owner", 5))
        try:
            read_time = float(rb.get("min_visual_read_time_sec") or 0)
            if read_time < 0.35:
                issues.append((f"{bid}: min_visual_read_time_sec too low ({read_time})", 5))
            if str(rb.get("beat_type", "")).lower() == "proof" and read_time < 1.0:
                issues.append((f"{bid}: proof beat needs at least 1.0s read time", 8))
            if read_time > dur + 0.6:
                issues.append((f"{bid}: read time {read_time:.2f}s exceeds planned beat {dur:.2f}s; slow VO or split beat", 8))
        except Exception:
            issues.append((f"{bid}: invalid min_visual_read_time_sec", 5))

        if planned_cps > 7.0:
            issues.append((f"{bid}: planned cps {planned_cps:.2f} too fast; split or slow the line", 8))
        elif planned_cps > 6.2:
            issues.append((f"{bid}: planned cps {planned_cps:.2f} review; may sound rushed", 4))
        elif planned_cps < 3.2 and dur > 1.2:
            issues.append((f"{bid}: planned cps {planned_cps:.2f} may drag unless it is a deliberate hold", 3))

        if not pb:
            issues.append((f"{bid}: missing prosody row", 6))
        else:
            if not (pb.get("tts_text") or "").strip():
                issues.append((f"{bid}: prosody tts_text is empty", 8))
            try:
                pre = int(float(pb.get("pre_pause_ms") or 0))
                post = int(float(pb.get("post_pause_ms") or 0))
            except ValueError:
                issues.append((f"{bid}: invalid pause values", 5))
                pre = post = 0
            if str(rb.get("beat_type", "")).lower() in {"proof", "reveal"} and pre + post < 250:
                issues.append((f"{bid}: proof/reveal beat has too little pause space ({pre + post}ms)", 5))
            if not (pb.get("emphasis_words") or "").strip():
                issues.append((f"{bid}: missing emphasis_words", 3))

        vb = vo_by_beat.get(bid)
        if vb:
            cps = float(vb.get("cps") or 0)
            if cps > 7.5:
                issues.append((f"{bid}: measured cps {cps:.2f} too fast", 10))
            elif cps > 6.5:
                issues.append((f"{bid}: measured cps {cps:.2f} review", 4))
            elif cps < 3.5 and float(vb.get("duration_sec") or 0) > 1.2:
                issues.append((f"{bid}: measured cps {cps:.2f} may be too slow", 4))

    for _, penalty in issues:
        score -= penalty
    score = max(0, min(100, score))

    out = root / "edit" / "director_rhythm_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Director Rhythm Report", "", f"Score: {score}", "", "## Issues"]
    if issues:
        lines.extend(f"- (-{p}) {m}" for m, p in issues)
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Fix upstream",
        "- Too fast: split `narration_beats.csv`, shorten text, or add prosody pauses.",
        "- Too slow: merge filler beats or reduce post-hold.",
        "- Not readable: increase `min_visual_read_time_sec`, pre-show the asset, or simplify the frame.",
    ])
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Director rhythm score: {score}")
    print(f"Wrote {out}")
    for msg, penalty in issues:
        print(f"- (-{penalty}) {msg}")
    return 0 if score >= args.fail_under else 1


if __name__ == "__main__":
    raise SystemExit(main())

