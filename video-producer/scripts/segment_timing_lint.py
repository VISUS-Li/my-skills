#!/usr/bin/env python3
"""Lint segment VO timing: CPS bands, missing files, composition duration hints."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint segment VO sync readiness.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("segment_id", help="Segment id e.g. S001")
    parser.add_argument("--fail-under", type=int, default=80, help="Exit 1 if score below threshold")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    seg = args.segment_id.upper()
    score = 100
    issues: list[tuple[str, int]] = []

    vo_path = root / "segments" / seg / "vo_timing.json"
    if not vo_path.exists():
        issues.append((f"missing {vo_path}", 40))
    else:
        vo = json.loads(vo_path.read_text(encoding="utf-8"))
        for b in vo.get("beats", []):
            cps = float(b.get("cps", 0))
            if cps < 3.5 or cps > 7.5:
                issues.append((f"{b['beat_id']} cps={cps} outside 3.5-7.5", 8))
            elif cps < 4.0 or cps > 6.5:
                issues.append((f"{b['beat_id']} cps={cps} review band", 3))

        micro = root / "segments" / seg / "micro_timing.json"
        if not micro.exists():
            issues.append(("missing micro_timing.json", 15))
        else:
            events = json.loads(micro.read_text(encoding="utf-8"))
            if len(events) < len(vo.get("beats", [])) * 3:
                issues.append((f"low micro-event count: {len(events)}", 10))

        html = root / "segments" / seg / "index.html"
        if html.exists():
            text = html.read_text(encoding="utf-8")
            m = re.search(r'data-duration="([0-9.]+)"', text)
            if m:
                comp_dur = float(m.group(1))
                total = float(vo.get("total_sec", 0))
                if abs(comp_dur - total) > 0.15:
                    issues.append((f"index.html duration {comp_dur} != vo {total}", 20))
            else:
                issues.append(("index.html missing data-duration", 12))
        else:
            issues.append((f"missing segments/{seg}/index.html", 10))

        assets = list((root / "segments" / seg / "assets").glob("*")) if (root / "segments" / seg / "assets").exists() else []
        svg_count = sum(1 for a in assets if a.suffix.lower() == ".svg")
        if svg_count < 4:
            issues.append((f"only {svg_count} SVG assets (min 4 recommended)", 8))

    for msg, pen in issues:
        score -= pen
    score = max(0, min(100, score))

    report = root / "segments" / seg / "timing_qc_report.md"
    lines = ["# Segment Timing QC", "", f"Score: {score}", "", "## Issues"]
    if issues:
        lines.extend([f"- (-{p}) {m}" for m, p in issues])
    else:
        lines.append("- none")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Segment timing score: {score}")
    print(f"Wrote {report}")
    for m, p in issues:
        print(f"- (-{p}) {m}")
    return 1 if score < args.fail_under else 0


if __name__ == "__main__":
    raise SystemExit(main())
