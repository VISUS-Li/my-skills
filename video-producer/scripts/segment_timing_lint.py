#!/usr/bin/env python3
"""Lint segment VO timing: CPS bands, missing files, composition duration hints."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from beat_store import duration_from_time, list_beats  # noqa: E402


def planned_segment_duration(root: Path, segment_id: str) -> float:
    return sum(float(b.get("planned_sec") or 0) for b in list_beats(root, segment_id))


def lint_segment(
    root: Path,
    segment_id: str,
    *,
    fail_under: int = 80,
    audio_only: bool | None = None,
) -> dict:
    seg = segment_id.upper()
    score = 100
    issues: list[dict[str, object]] = []

    vo_path = root / "segments" / seg / "vo_timing.json"
    html = root / "segments" / seg / "index.html"
    composition_ready = html.exists()
    if audio_only is None:
        audio_only = not composition_ready

    if not vo_path.exists():
        issues.append({"message": f"missing {vo_path.name}", "penalty": 40})
    else:
        vo = json.loads(vo_path.read_text(encoding="utf-8-sig"))
        total_sec = float(vo.get("total_sec", 0))
        planned_sec = planned_segment_duration(root, seg)
        if planned_sec > 0 and total_sec > 0:
            drift = abs(total_sec - planned_sec) / planned_sec
            if drift > 0.10:
                issues.append({
                    "message": f"vo total {total_sec}s vs planned {planned_sec}s drift {drift:.0%} (>10%) — fix script/beats before render",
                    "penalty": 25,
                })

        for b in vo.get("beats", []):
            if b.get("source") == "planned":
                continue
            cps = float(b.get("cps", 0))
            locked = bool(b.get("locked"))
            if locked and (cps < 4.0 or cps > 6.0):
                issues.append({
                    "message": f"{b['beat_id']} locked beat cps={cps} outside 4.0-6.0 — unlock or re-cut VO",
                    "penalty": 20,
                })
            elif cps < 3.5 or cps > 7.5:
                issues.append({"message": f"{b['beat_id']} cps={cps} outside 3.5-7.5", "penalty": 8})
            elif cps < 4.0 or cps > 6.5:
                issues.append({"message": f"{b['beat_id']} cps={cps} review band", "penalty": 3})

        micro = root / "segments" / seg / "micro_timing.json"
        if not micro.exists():
            from beat_store import build_micro_timing_from_spec

            events = build_micro_timing_from_spec(root, seg)
            if events:
                micro.parent.mkdir(parents=True, exist_ok=True)
                micro.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not micro.exists():
            if audio_only:
                issues.append({
                    "message": "missing micro_timing.json (run audio_chain or build_review_bundle after measure_segment_vo)",
                    "penalty": 8,
                })
            else:
                issues.append({"message": "missing micro_timing.json", "penalty": 15})
        else:
            events = json.loads(micro.read_text(encoding="utf-8-sig"))
            event_list = events if isinstance(events, list) else events.get("events", [])
            min_events = 1 if audio_only else len(vo.get("beats", [])) * 3
            if len(event_list) < min_events:
                issues.append({
                    "message": f"low micro-event count: {len(event_list)}",
                    "penalty": 3 if audio_only else 10,
                })

        if composition_ready and not audio_only:
            text = html.read_text(encoding="utf-8")
            m = re.search(r'data-duration="([0-9.]+)"', text)
            if m:
                comp_dur = float(m.group(1))
                total = float(vo.get("total_sec", 0))
                if abs(comp_dur - total) > 0.15:
                    issues.append({
                        "message": f"index.html duration {comp_dur} != vo {total}",
                        "penalty": 20,
                    })
            else:
                issues.append({"message": "index.html missing data-duration", "penalty": 12})

    for item in issues:
        score -= int(item["penalty"])
    score = max(0, min(100, score))

    report = root / "segments" / seg / "timing_qc_report.md"
    lines = ["# Segment Timing QC", "", f"Score: {score}", "", "## Issues"]
    if issues:
        lines.extend([f"- (-{i['penalty']}) {i['message']}" for i in issues])
    else:
        lines.append("- none")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "score": score,
        "fail_under": fail_under,
        "passed": score >= fail_under,
        "issues": issues,
        "report_path": report.relative_to(root).as_posix(),
        "audio_only": audio_only,
        "composition_ready": composition_ready,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint segment VO sync readiness.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("segment_id", help="Segment id e.g. S001")
    parser.add_argument("--fail-under", type=int, default=80, help="Exit 1 if score below threshold")
    parser.add_argument(
        "--audio-only",
        action="store_true",
        help="Lint VO/CPS only; skip composition duration and asset checks",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Require composition checks even when index.html is missing",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    audio_only = True if args.audio_only else False if args.full else None
    result = lint_segment(
        root,
        args.segment_id,
        fail_under=args.fail_under,
        audio_only=audio_only,
    )
    print(f"Segment timing score: {result['score']}")
    print(f"Wrote {Path(args.root).resolve() / result['report_path']}")
    for item in result["issues"]:
        print(f"- (-{item['penalty']}) {item['message']}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
