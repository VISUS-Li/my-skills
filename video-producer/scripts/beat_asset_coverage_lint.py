#!/usr/bin/env python3
"""Lint beat-level asset binding with director-aware density rules.

This check intentionally avoids the old "every beat needs four assets" logic.
Evidence, data, and mechanism beats may need dense layered material; emotion,
viewpoint, and transition beats may be stronger when sparse. The script scores
whether the material choices match the beat's narrative function.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


REAL_PREFIXES = ("ref_", "motion_", "stock_", "screenshot_")
CONCRETE_PREFIXES = REAL_PREFIXES + ("gen_", "chart_")
PROGRAMMATIC_PREFIXES = ("hf_", "text_", "chart_", "svg_", "ambient_")
SVG_HINTS = ("svg", "icon_", "arrow", "box", "ring", "bracket", "connector")
EVIDENCE_TYPES = {"evidence", "proof", "event", "scene", "data"}
SPARSE_OK_TYPES = {"emotion", "viewpoint", "transition", "reset", "person"}
DENSE_TYPES = {"evidence", "proof", "data", "mechanism", "contrast"}


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def normalize_type(value: str) -> str:
    low = (value or "").strip().lower()
    aliases = {
        "source": "evidence",
        "source_visual": "evidence",
        "fact": "evidence",
        "proof": "evidence",
        "human": "person",
        "story": "person",
        "opinion": "viewpoint",
        "summary": "viewpoint",
        "hook": "hook",
    }
    return aliases.get(low, low)


def split_assets(row: dict[str, str]) -> list[str]:
    fields = [
        "primary_asset",
        "secondary_asset",
        "accent_asset",
        "ambient_asset",
        "asset_ids",
        "ref_embed",
    ]
    out: list[str] = []
    for field in fields:
        value = row.get(field, "")
        for part in re.split(r"[;|]", str(value)):
            part = part.strip()
            if part and part.lower() not in {"none", "null", "na"}:
                out.append(part)
    # keep order, dedupe
    seen: set[str] = set()
    deduped: list[str] = []
    for item in out:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def manifest_index(root: Path) -> dict[str, dict[str, str]]:
    return {
        row["asset_id"].strip(): row
        for row in load_csv(root / "assets" / "asset_manifest.csv")
        if row.get("asset_id", "").strip()
    }


def resolve_asset_path(root: Path, asset_id: str, manifest: dict[str, dict[str, str]]) -> Path | None:
    row = manifest.get(asset_id)
    if row:
        rel = (row.get("embed_full") or row.get("embed_card") or row.get("path_or_url") or "").strip()
        if rel and not rel.startswith(("http://", "https://")):
            p = root / rel.replace("\\", "/")
            if p.exists():
                return p
    for base in (root / "segments").glob("*/assets"):
        for ext in (".svg", ".png", ".jpg", ".jpeg", ".webp", ".mp4", ".webm", ".mov"):
            for sub in ("", "ref", "ref/processed", "ref/processed/stock"):
                candidate = base / sub / f"{asset_id}{ext}"
                if candidate.exists():
                    return candidate
    return None


def has_prefix(asset_ids: list[str], prefixes: tuple[str, ...]) -> bool:
    return any(asset.lower().startswith(prefix) for asset in asset_ids for prefix in prefixes)


def svg_like(asset_id: str, manifest: dict[str, dict[str, str]]) -> bool:
    low = asset_id.lower()
    row = manifest.get(asset_id, {})
    typ = (row.get("type") or row.get("motion_type") or "").lower()
    return "svg" in typ or any(hint in low for hint in SVG_HINTS)


def programmatic_like(asset_id: str, manifest: dict[str, dict[str, str]]) -> bool:
    low = asset_id.lower()
    if low.startswith(PROGRAMMATIC_PREFIXES):
        return True
    row = manifest.get(asset_id, {})
    typ = (row.get("type") or row.get("motion_type") or "").lower()
    return any(token in typ for token in ("text", "hyperframes", "programmatic", "svg_component", "css"))


def concrete_source_required(narration: dict[str, str], row: dict[str, str], beat_type: str = "") -> bool:
    if beat_type in SPARSE_OK_TYPES:
        return False
    source_visual = (narration.get("source_visual") or row.get("source_visual") or "").strip().lower()
    if source_visual and source_visual not in {"none", "no", "n/a", "na"}:
        return True
    text = " ".join(
        [
            narration.get("narration", ""),
            narration.get("spoken_focus", ""),
            row.get("visual_subject_desc", ""),
            row.get("screen_content_desc", ""),
        ]
    )
    # Common concrete indicators in Chinese factual videos.
    return bool(re.search(r"App|网页|截图|表格|公告|新闻|官方|价格|公司|人物|城市|地震|手机|汽车|司机|广告|VIP", text, re.I))


def lint_segment(root: Path, segment_id: str, *, fail_under: int = 85) -> dict:
    seg = segment_id.upper()
    issues: list[dict[str, object]] = []
    score = 100

    plan_path = root / "segments" / seg / "beat_asset_plan.csv"
    plan_rows = load_csv(plan_path)
    if not plan_rows:
        issues.append({"message": f"missing or empty {plan_path.relative_to(root).as_posix()}", "penalty": 45})
        return _report(root, seg, score, issues, fail_under)

    manifest = manifest_index(root)
    narration_rows = {
        row.get("beat_id", ""): row
        for row in load_csv(root / "script" / "narration_beats.csv")
        if row.get("segment_id", "").upper() == seg
    }
    sync_rows = {
        row.get("beat_id", ""): row
        for row in load_csv(root / "script" / "visual_sync_plan.csv")
        if row.get("segment_id", "").upper() == seg
    }

    total = len(plan_rows)
    real_beats = 0
    concrete_total = 0
    concrete_ok = 0
    svg_only_runs = 0
    previous_svg_only = False
    density_values: list[str] = []

    for row in plan_rows:
        bid = row.get("beat_id", "").strip()
        nar = narration_rows.get(bid, {})
        sync = sync_rows.get(bid, {})
        beat_type = normalize_type(nar.get("beat_type") or sync.get("visual_intent") or row.get("beat_type") or "")
        density = (nar.get("information_density") or row.get("density_target") or row.get("layer_count_target") or "").strip().lower()
        if density:
            density_values.append(density)
        assets = split_assets({**sync, **row})
        real = has_prefix(assets, REAL_PREFIXES)
        concrete = has_prefix(assets, CONCRETE_PREFIXES)
        svg_count = sum(1 for a in assets if svg_like(a, manifest))
        svg_only = bool(assets) and svg_count == len(assets)

        if real:
            real_beats += 1

        if concrete_source_required(nar, {**sync, **row}, beat_type):
            concrete_total += 1
            if real or concrete:
                concrete_ok += 1
            else:
                issues.append({
                    "message": f"{bid}: concrete spoken/source detail has no ref/motion/stock/gen/chart asset",
                    "penalty": 12,
                })

        if beat_type in EVIDENCE_TYPES and not real:
            issues.append({
                "message": f"{bid}: {beat_type or 'evidence'} beat lacks real/source-backed material",
                "penalty": 10,
            })

        if beat_type in DENSE_TYPES:
            if len(assets) < 2:
                issues.append({"message": f"{bid}: {beat_type} beat has too few visible actors for guided explanation", "penalty": 6})
            if not (row.get("must_show_detail") or sync.get("must_show_detail") or "").strip():
                issues.append({"message": f"{bid}: dense/evidence beat missing must_show_detail", "penalty": 5})

        if beat_type in SPARSE_OK_TYPES and len(assets) >= 5:
            issues.append({"message": f"{bid}: {beat_type} beat may be overloaded; sparse emotional beats should have a clear reason", "penalty": 5})

        if svg_only and beat_type not in {"transition", "mechanism", "hook"}:
            issues.append({"message": f"{bid}: SVG-only material on a non-abstract beat", "penalty": 8})

        if svg_only and previous_svg_only:
            svg_only_runs += 1
        previous_svg_only = svg_only

        for asset_id in assets:
            if programmatic_like(asset_id, manifest):
                continue
            if asset_id.startswith(("segments/", "assets/")):
                path = root / asset_id.replace("\\", "/")
                if not path.exists():
                    issues.append({"message": f"{bid}: asset path missing: {asset_id}", "penalty": 8})
                continue
            if asset_id not in manifest and resolve_asset_path(root, asset_id, manifest) is None:
                issues.append({"message": f"{bid}: asset not in manifest and file missing: {asset_id}", "penalty": 6})

        try:
            read_time = float(row.get("visual_read_time_sec") or sync.get("visual_read_time_sec") or 0)
            duration = float(row.get("duration_sec") or 0)
            if beat_type in DENSE_TYPES and read_time < 0.8:
                issues.append({"message": f"{bid}: readable dense beat has visual_read_time_sec below 0.8", "penalty": 5})
            if duration and read_time > duration + 0.4:
                issues.append({"message": f"{bid}: read time {read_time:.2f}s exceeds beat duration {duration:.2f}s", "penalty": 7})
        except ValueError:
            issues.append({"message": f"{bid}: invalid visual_read_time_sec", "penalty": 4})

    if svg_only_runs >= 2:
        issues.append({"message": "three or more adjacent beats are effectively SVG-only; add real material, screenshots, data, or a deliberate reset", "penalty": 12})

    if total >= 4:
        real_ratio = real_beats / total
        if real_ratio < 0.25:
            issues.append({
                "message": f"only {real_beats}/{total} beats use real/source-backed assets; factual explainers need more reality texture",
                "penalty": 12,
            })

    if concrete_total and concrete_ok < concrete_total:
        issues.append({
            "message": f"concrete beats with concrete assets: {concrete_ok}/{concrete_total}",
            "penalty": min(16, (concrete_total - concrete_ok) * 4),
        })

    if len(set(density_values)) <= 1 and total >= 5:
        issues.append({"message": "density is constant across many beats; vary dense evidence/data and sparse emotion/viewpoint sections", "penalty": 7})

    return _report(
        root,
        seg,
        score,
        issues,
        fail_under,
        extra={
            "beats_total": total,
            "beats_with_real_or_source": real_beats,
            "concrete_beats": concrete_total,
            "concrete_beats_ok": concrete_ok,
        },
    )


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
    lines = ["# Beat Asset Coverage QC", "", f"Score: {score}", "", "## Issues"]
    if issues:
        lines.extend(f"- (-{i['penalty']}) {i['message']}" for i in issues)
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Director Fixes",
        "- Concrete lines need concrete material before SVG annotation.",
        "- Evidence/data can be dense, but must name the readable detail and hold it.",
        "- Emotion/viewpoint beats may be sparse; remove clutter instead of adding layers.",
    ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "score": score,
        "fail_under": fail_under,
        "passed": score >= fail_under,
        "issues": issues,
        "report_path": report_path.relative_to(root).as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Director-aware lint for beat-level asset coverage and density.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("segment_id", help="Segment id e.g. S001")
    parser.add_argument("--fail-under", type=int, default=85)
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
