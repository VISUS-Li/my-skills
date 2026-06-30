#!/usr/bin/env python3
"""Lint segment VO timing: CPS bands, missing files, composition duration hints."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

from beat_csv_utils import planned_duration_sec  # noqa: E402


def planned_segment_duration(root: Path, segment_id: str) -> float:
    """Sum planned beat durations from narration_beats.csv for one segment."""
    path = root / "script" / "narration_beats.csv"
    if not path.exists():
        return 0.0
    total = 0.0
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("segment_id", "").upper() == segment_id.upper():
                total += planned_duration_sec(row)
    return total


def count_motion_assets(assets_dir: Path) -> tuple[int, int]:
    """Return (motion_real_count, broll_ken_burns_count) from ref tree."""
    motion = 0
    broll = 0
    ref = assets_dir / "ref"
    if not ref.is_dir():
        return 0, 0
    for p in ref.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".mp4", ".webm", ".mov", ".mkv"}:
            continue
        name = p.name.lower()
        if name.startswith("motion_"):
            motion += 1
        elif name.startswith("broll_"):
            broll += 1
    return motion, broll


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
            if audio_only:
                issues.append({
                    "message": "missing micro_timing.json (run build_micro_timing.py after measure_segment_vo)",
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

            assets_dir = root / "segments" / seg / "assets"
            if assets_dir.exists():
                assets = list(assets_dir.glob("*"))
                svg_count = sum(1 for a in assets if a.suffix.lower() == ".svg")
                png_count = sum(1 for a in assets if a.suffix.lower() in {".png", ".webp"})
                ref_dir = assets_dir / "ref"
                ref_count = 0
                stock_count = 0
                if ref_dir.is_dir():
                    processed = ref_dir / "processed"
                    search_root = processed if processed.is_dir() else ref_dir
                    for a in search_root.rglob("*"):
                        if not a.is_file():
                            continue
                        if a.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                            continue
                        if a.name.lower().startswith("stock_"):
                            stock_count += 1
                        elif a.name.lower().startswith(("ref_", "screenshot_")):
                            ref_count += 1
                motion_count, broll_count = count_motion_assets(assets_dir)
                evidence_stills = ref_count + stock_count
                if svg_count < 12:
                    issues.append({
                        "message": f"only {svg_count} SVG assets (min 12 recommended for rich segments)",
                        "penalty": min(16, 8 + (12 - svg_count)),
                    })
                if png_count < 2:
                    issues.append({
                        "message": f"only {png_count} decorative plates (min 2 recommended)",
                        "penalty": 4,
                    })
                if evidence_stills < 3:
                    issues.append({
                        "message": f"only {evidence_stills} ref/stock stills in processed/ (min 3; see evidence-and-asset-sourcing.md)",
                        "penalty": min(14, 6 + max(0, 3 - evidence_stills) * 3),
                    })
                if motion_count < 1:
                    issues.append({
                        "message": "no motion_* real video in assets/ref/ (Ken Burns broll_* does not count)",
                        "penalty": 10,
                    })
                if broll_count < 1 and motion_count < 2:
                    issues.append({
                        "message": f"motion_*={motion_count}, broll_*={broll_count} — consider Ken Burns fill after real footage",
                        "penalty": 2,
                    })
                vtr = ref_dir / "processed" / "video_types_report.json"
                if ref_dir.is_dir() and not vtr.is_file():
                    issues.append({
                        "message": "missing assets/ref/processed/video_types_report.json",
                        "penalty": 6,
                    })

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
