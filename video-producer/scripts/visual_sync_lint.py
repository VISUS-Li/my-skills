#!/usr/bin/env python3
"""Lint semantic voice-to-picture alignment for one segment."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


CONCRETE_PREFIXES = ("ref_", "stock_", "gen_", "motion_", "screenshot_")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def split_ids(value: str) -> list[str]:
    return [x.strip() for x in str(value or "").replace("|", ";").split(";") if x.strip()]


def has_concrete_asset(row: dict[str, str]) -> bool:
    fields = [
        row.get("source_visual", ""),
        row.get("asset_ids", ""),
        row.get("primary_asset", ""),
        row.get("secondary_asset", ""),
        row.get("ref_embed", ""),
    ]
    text = ";".join(fields).lower()
    return any(prefix in text for prefix in CONCRETE_PREFIXES) or "segments/" in text


def main() -> int:
    parser = argparse.ArgumentParser(description="Score visual sync for a segment.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("segment_id", help="Segment id e.g. S001")
    parser.add_argument("--fail-under", type=int, default=85)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    seg = args.segment_id.upper()
    score = 100
    issues: list[tuple[str, int]] = []

    sync_rows = [r for r in read_csv(root / "script" / "visual_sync_plan.csv") if r.get("segment_id", "").upper() == seg]
    narr_rows = [r for r in read_csv(root / "script" / "narration_beats.csv") if r.get("segment_id", "").upper() == seg]
    plan_rows = read_csv(root / "segments" / seg / "beat_asset_plan.csv")

    if not sync_rows:
        issues.append((f"missing visual sync rows for {seg}", 35))
    if not narr_rows:
        issues.append((f"missing narration beats for {seg}", 20))
    if not plan_rows:
        issues.append((f"missing segments/{seg}/beat_asset_plan.csv", 20))

    sync_by_beat = {r.get("beat_id", ""): r for r in sync_rows}
    plan_by_beat = {r.get("beat_id", ""): r for r in plan_rows}

    for nr in narr_rows:
        bid = nr.get("beat_id", "")
        if not bid:
            continue
        sr = sync_by_beat.get(bid)
        pr = plan_by_beat.get(bid, {})
        if not sr:
            issues.append((f"{bid}: missing visual_sync_plan row", 10))
            continue
        for field in ["spoken_focus", "visual_intent", "visual_subject_desc", "screen_content_desc", "acceptance_check"]:
            if not (sr.get(field) or "").strip():
                issues.append((f"{bid}: missing {field}", 5))
        if not (sr.get("must_show_detail") or "").strip():
            issues.append((f"{bid}: missing must_show_detail; crop/readability cannot be judged", 4))
        try:
            read_time = float(sr.get("visual_read_time_sec") or pr.get("visual_read_time_sec") or 0)
            duration = float(pr.get("duration_sec") or 0)
            if read_time < 0.35:
                issues.append((f"{bid}: visual_read_time_sec too low ({read_time})", 5))
            if duration and read_time > duration + 0.5:
                issues.append((f"{bid}: visual read time {read_time:.2f}s exceeds beat duration {duration:.2f}s", 8))
        except ValueError:
            issues.append((f"{bid}: invalid visual_read_time_sec", 5))

        source_visual = (nr.get("source_visual") or sr.get("source_visual") or pr.get("source_visual") or "none").strip().lower()
        is_concrete = source_visual not in {"", "none", "no"}
        if is_concrete and not (has_concrete_asset(sr) or has_concrete_asset(pr)):
            issues.append((f"{bid}: concrete source_visual={source_visual} but no concrete ref/stock/gen/motion asset bound", 12))

        if (sr.get("mismatch_risk") or "").strip().lower() in {"", "none"}:
            issues.append((f"{bid}: mismatch_risk should be explicitly assessed", 3))
        if not (sr.get("focal_owner") or pr.get("primary_asset") or "").strip():
            issues.append((f"{bid}: missing focal owner", 6))

        ref_embed = (pr.get("ref_embed") or "").strip()
        if ref_embed:
            for part in split_ids(ref_embed):
                path = root / part.replace("\\", "/")
                if not path.exists():
                    issues.append((f"{bid}: ref_embed file missing: {part}", 8))

    # Coverage check: visual sync rows should not be fewer than narration rows.
    if narr_rows and len(sync_rows) < len(narr_rows):
        issues.append((f"visual sync coverage {len(sync_rows)}/{len(narr_rows)} beats", 10))

    for _, penalty in issues:
        score -= penalty
    score = max(0, min(100, score))

    out = root / "edit" / f"visual_sync_{seg}_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Visual Sync Report", "", f"Segment: {seg}", f"Score: {score}", "", "## Issues"]
    if issues:
        lines.extend(f"- (-{p}) {m}" for m, p in issues)
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Fix upstream",
        "- If a beat is concrete, bind a concrete media layer before SVG decoration.",
        "- If the frame cannot be read in time, simplify it, pre-show it, or slow the voice.",
        "- If the screen content is vague, rewrite `screen_content_desc` before asset generation.",
    ])
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Visual sync score: {score}")
    print(f"Wrote {out}")
    for msg, penalty in issues:
        print(f"- (-{penalty}) {msg}")
    return 0 if score >= args.fail_under else 1


if __name__ == "__main__":
    raise SystemExit(main())

