#!/usr/bin/env python3
"""Lint segment VO timing: CPS bands, missing files, composition duration hints."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


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
        for b in vo.get("beats", []):
            if b.get("source") == "planned":
                continue
            cps = float(b.get("cps", 0))
            if cps < 3.5 or cps > 7.5:
                issues.append({"message": f"{b['beat_id']} cps={cps} outside 3.5-7.5", "penalty": 8})
            elif cps < 4.0 or cps > 6.5:
                issues.append({"message": f"{b['beat_id']} cps={cps} review band", "penalty": 3})

        micro = root / "segments" / seg / "micro_timing.json"
        if not micro.exists():
            if audio_only:
                issues.append({
                    "message": "missing micro_timing.json (optional in audio-only phase; run build_micro_timing)",
                    "penalty": 3,
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
                if ref_dir.is_dir():
                    ref_count = sum(
                        1
                        for a in ref_dir.iterdir()
                        if a.is_file() and a.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"}
                    )
                    clip_count = sum(
                        1
                        for a in ref_dir.iterdir()
                        if a.is_file() and a.suffix.lower() in {".mp4", ".webm", ".mov", ".mkv"}
                    )
                else:
                    clip_count = 0
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
                if ref_count < 2:
                    issues.append({
                        "message": f"only {ref_count} web-sourced ref photos in assets/ref/ (min 3 recommended; see web-sourced-visual-assets.md)",
                        "penalty": min(14, 6 + max(0, 3 - ref_count) * 3),
                    })
                if ref_dir.is_dir() and clip_count < 1:
                    issues.append({
                        "message": "no video clips in assets/ref/ (add broll when narration mentions demo/process/release)",
                        "penalty": 4,
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
