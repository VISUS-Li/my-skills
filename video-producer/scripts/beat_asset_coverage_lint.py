#!/usr/bin/env python3
"""Lint per-beat asset binding: existence, diversity, evidence layer, VO timing sync."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

EVIDENCE_PREFIXES = ("ref_", "stock_", "gen_", "motion_", "broll_", "screenshot_")
REAL_EVIDENCE_PREFIXES = ("ref_", "stock_", "motion_", "screenshot_")


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def manifest_index(root: Path) -> dict[str, dict[str, str]]:
    rows = load_csv(root / "assets" / "asset_manifest.csv")
    idx: dict[str, dict[str, str]] = {}
    for row in rows:
        aid = (row.get("asset_id") or "").strip()
        if aid:
            idx[aid] = row
    return idx


def resolve_asset_path(root: Path, asset_id: str, manifest: dict[str, dict[str, str]]) -> Path | None:
    if not asset_id or asset_id.lower() in {"none", ""}:
        return None
    row = manifest.get(asset_id)
    if row:
        rel = (row.get("embed_full") or row.get("embed_card") or row.get("path_or_url") or "").strip()
        if rel and not rel.startswith("http"):
            p = root / rel.replace("\\", "/")
            if p.exists():
                return p
    # glob by id prefix under segment assets
    for base in (root / "segments").glob("*/assets"):
        for ext in (".svg", ".png", ".jpg", ".jpeg", ".webp", ".mp4", ".webm", ".mov"):
            candidate = base / f"{asset_id}{ext}"
            if candidate.exists():
                return candidate
            for sub in ("ref", "ref/processed", "ref/processed/stock"):
                candidate = base / sub / f"{asset_id}{ext}"
                if candidate.exists():
                    return candidate
    return None


def is_svg_only(asset_id: str) -> bool:
    if not asset_id or asset_id.lower() == "none":
        return True
    low = asset_id.lower()
    if low.startswith("icon_") or low.endswith(".svg"):
        return True
    return not any(low.startswith(p) for p in EVIDENCE_PREFIXES)


def has_real_evidence(asset_ids: list[str]) -> bool:
    return any(
        (a or "").lower().startswith(p)
        for a in asset_ids
        for p in REAL_EVIDENCE_PREFIXES
    )


def lint_segment(root: Path, segment_id: str, *, fail_under: int = 90) -> dict:
    seg = segment_id.upper()
    score = 100
    issues: list[dict[str, object]] = []

    plan_path = root / "segments" / seg / "beat_asset_plan.csv"
    if not plan_path.exists():
        issues.append({"message": f"missing {plan_path.relative_to(root).as_posix()}", "penalty": 50})
        return _report(root, seg, score, issues, fail_under)

    plan_rows = load_csv(plan_path)
    if not plan_rows:
        issues.append({"message": "beat_asset_plan.csv is empty", "penalty": 40})
        return _report(root, seg, score, issues, fail_under)

    manifest = manifest_index(root)
    narration = {
        r["beat_id"]: r
        for r in load_csv(root / "script" / "narration_beats.csv")
        if r.get("segment_id", "").upper() == seg
    }

    vo_by_beat: dict[str, dict] = {}
    vo_path = root / "segments" / seg / "vo_timing.json"
    if vo_path.exists():
        vo = json.loads(vo_path.read_text(encoding="utf-8-sig"))
        vo_by_beat = {b["beat_id"]: b for b in vo.get("beats", [])}

    asset_slots = ("primary_asset", "secondary_asset", "accent_asset", "ambient_asset")
    combos: list[tuple[str, str, str, str]] = []
    beats_with_embed = 0
    beats_with_evidence = 0
    concrete_total = 0
    concrete_ok = 0

    for row in plan_rows:
        bid = row.get("beat_id", "")
        assets = [(row.get(k) or "").strip() for k in asset_slots]
        if len([a for a in assets if a and a.lower() != "none"]) < 4:
            issues.append({"message": f"{bid}: fewer than 4 bound assets", "penalty": 6})

        for k in asset_slots:
            aid = (row.get(k) or "").strip()
            if not aid or aid.lower() == "none":
                continue
            if aid not in manifest and resolve_asset_path(root, aid, manifest) is None:
                issues.append({"message": f"{bid}: {k}={aid} not in manifest and file missing", "penalty": 8})

        m1 = (row.get("motion_primary") or "").strip()
        m2 = (row.get("motion_secondary") or "").strip()
        if not m1 or not m2:
            issues.append({"message": f"{bid}: need motion_primary and motion_secondary", "penalty": 4})

        ref_embed = (row.get("ref_embed") or "").strip()
        if ref_embed:
            beats_with_embed += 1
            for part in ref_embed.split("|"):
                part = part.strip()
                if not part:
                    continue
                p = root / part.replace("\\", "/")
                if not p.is_file():
                    issues.append({"message": f"{bid}: ref_embed missing {part}", "penalty": 10})

        if has_real_evidence(assets) or ref_embed:
            beats_with_evidence += 1

        nar = narration.get(bid, {})
        source_visual = (nar.get("source_visual") or row.get("source_visual") or "none").strip().lower()
        if source_visual != "none":
            concrete_total += 1
            if has_real_evidence(assets):
                concrete_ok += 1
            elif all(is_svg_only(a) for a in assets if a):
                issues.append({
                    "message": f"{bid}: concrete beat (source_visual={source_visual}) has only SVG-layer assets",
                    "penalty": 12,
                })

        if bid in vo_by_beat:
            vb = vo_by_beat[bid]
            try:
                start = float(row.get("start_sec") or 0)
                dur = float(row.get("duration_sec") or 0)
            except ValueError:
                start, dur = 0.0, 0.0
            if abs(start - float(vb["start_sec"])) > 0.08:
                issues.append({
                    "message": f"{bid}: start_sec {start} != vo_timing {vb['start_sec']}",
                    "penalty": 6,
                })
            if abs(dur - float(vb["duration_sec"])) > 0.08:
                issues.append({
                    "message": f"{bid}: duration_sec {dur} != vo_timing {vb['duration_sec']}",
                    "penalty": 6,
                })
        elif vo_path.exists():
            issues.append({
                "message": f"{bid}: missing from vo_timing.json — rebind times after measure_segment_vo",
                "penalty": 5,
            })

        combos.append(tuple(assets))

    # no 3 consecutive identical 4-asset combos
    for i in range(len(combos) - 2):
        if combos[i] == combos[i + 1] == combos[i + 2] and any(combos[i]):
            issues.append({
                "message": f"beats {plan_rows[i]['beat_id']}–{plan_rows[i+2]['beat_id']}: identical 4-asset combo x3",
                "penalty": 8,
            })

    total = len(plan_rows)
    evidence_ratio = beats_with_evidence / total if total else 0
    if evidence_ratio < 0.70:
        issues.append({
            "message": f"only {beats_with_evidence}/{total} beats have ref/stock/motion/embed ({evidence_ratio:.0%} < 70%)",
            "penalty": min(20, int((0.70 - evidence_ratio) * 40)),
        })

    if concrete_total and concrete_ok < concrete_total:
        issues.append({
            "message": f"concrete beats with real evidence: {concrete_ok}/{concrete_total}",
            "penalty": min(15, (concrete_total - concrete_ok) * 5),
        })

    vtr = root / "segments" / seg / "assets" / "ref" / "processed" / "video_types_report.json"
    if not vtr.exists():
        issues.append({"message": "missing assets/ref/processed/video_types_report.json", "penalty": 6})

    return _report(root, seg, score, issues, fail_under, extra={
        "beats_total": total,
        "beats_with_embed": beats_with_embed,
        "beats_with_evidence": beats_with_evidence,
        "evidence_ratio": round(evidence_ratio, 3),
    })


def _report(
    root: Path,
    seg: str,
    score: int,
    issues: list[dict[str, object]],
    fail_under: int,
    extra: dict | None = None,
) -> dict:
    for item in issues:
        score -= int(item["penalty"])
    score = max(0, min(100, score))

    report_path = root / "segments" / seg / "assets" / "ref" / "processed" / "beat_asset_coverage_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "segment_id": seg,
        "score": score,
        "passed": score >= fail_under,
        "issues": issues,
        **(extra or {}),
    }
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_path = root / "segments" / seg / "beat_asset_coverage_qc.md"
    lines = [
        "# Beat Asset Coverage QC",
        "",
        f"Score: {score}",
        "",
        "## Issues",
    ]
    if issues:
        lines.extend(f"- (-{i['penalty']}) {i['message']}" for i in issues)
    else:
        lines.append("- none")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "score": score,
        "fail_under": fail_under,
        "passed": score >= fail_under,
        "issues": issues,
        "report_path": report_path.relative_to(root).as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint beat-level asset coverage and binding.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("segment_id", help="Segment id e.g. S001")
    parser.add_argument("--fail-under", type=int, default=90, help="Exit 1 if score below threshold")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    result = lint_segment(root, args.segment_id, fail_under=args.fail_under)
    print(f"Beat asset coverage score: {result['score']}")
    print(f"Wrote {root / result['report_path']}")
    for item in result["issues"]:
        print(f"- (-{item['penalty']}) {item['message']}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
