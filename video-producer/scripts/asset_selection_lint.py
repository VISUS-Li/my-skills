#!/usr/bin/env python3
"""Lint asset_selection_report.json for relevance, readability, crop safety, and rights."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


BLOCKED_RIGHTS = {"", "unknown", "needs-check", "do-not-use-final", "copyrighted-reference-only", "noncommercial"}
BAD_WATERMARK = {"high", "present", "yes", "visible"}


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def read_manifest(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {r.get("asset_id", ""): r for r in csv.DictReader(f) if r.get("asset_id")}


def score_value(asset: dict[str, Any], key: str) -> int:
    try:
        return int(float(asset.get(key, 0)))
    except Exception:
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Score selected asset quality.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--fail-under", type=int, default=82)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report_path = root / "assets" / "asset_selection_report.json"
    payload = load_json(report_path, {})
    manifest = read_manifest(root / "assets" / "asset_manifest.csv")

    score = 100
    issues: list[tuple[str, int]] = []
    assets = payload.get("assets", []) if isinstance(payload, dict) else []
    if not isinstance(assets, list) or not assets:
        issues.append(("missing or empty assets/asset_selection_report.json", 40))
        assets = []

    selected = [a for a in assets if isinstance(a, dict) and bool(a.get("selected"))]
    if not selected:
        issues.append(("no selected assets; final asset binding has no quality basis", 25))

    for asset in selected:
        aid = str(asset.get("asset_id") or "unknown")
        beat_ids = asset.get("beat_ids") or []
        if not beat_ids:
            issues.append((f"{aid}: missing beat_ids", 6))
        if aid not in manifest:
            issues.append((f"{aid}: selected but missing from asset_manifest.csv", 8))
        for key in ["content_description", "trim_policy", "crop_anchor"]:
            if not str(asset.get(key) or "").strip():
                issues.append((f"{aid}: missing {key}", 5))
        rel = score_value(asset, "relevance_score")
        read = score_value(asset, "readability_score")
        crop = score_value(asset, "crop_safety_score")
        if rel < 4:
            issues.append((f"{aid}: relevance_score {rel} below 4", 10))
        if read < 4:
            issues.append((f"{aid}: readability_score {read} below 4", 8))
        if crop < 4:
            issues.append((f"{aid}: crop_safety_score {crop} below 4", 8))
        rights = str(asset.get("rights_status") or "").lower()
        if rights in BLOCKED_RIGHTS:
            issues.append((f"{aid}: blocked or unresolved rights_status={rights or 'empty'}", 10))
        watermark = str(asset.get("watermark_risk") or "").lower()
        if watermark in BAD_WATERMARK:
            issues.append((f"{aid}: watermark_risk={watermark}", 10))
        trim = str(asset.get("trim_policy") or "").lower()
        if trim not in {"no_trim", "trim_to_action", "loop_safe", "ken_burns_fill"}:
            issues.append((f"{aid}: invalid trim_policy={trim}", 5))
        if trim == "ken_burns_fill" and aid.lower().startswith("motion_"):
            issues.append((f"{aid}: motion_* cannot be ken_burns_fill; use broll_*", 10))

    for asset in assets:
        if not isinstance(asset, dict) or asset.get("selected"):
            continue
        if not str(asset.get("reject_reason") or "").strip():
            issues.append((f"{asset.get('asset_id', 'unknown')}: rejected asset missing reject_reason", 3))

    for _, penalty in issues:
        score -= penalty
    score = max(0, min(100, score))

    out = root / "edit" / "asset_selection_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Asset Selection QC", "", f"Score: {score}", "", "## Issues"]
    if issues:
        lines.extend(f"- (-{p}) {m}" for m, p in issues)
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Fix upstream",
        "- Replace low-relevance assets instead of hiding them behind motion.",
        "- Reprocess crops when important details are cut off.",
        "- Resolve rights and watermark risk before final render.",
    ])
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Asset selection score: {score}")
    print(f"Wrote {out}")
    for msg, penalty in issues:
        print(f"- (-{penalty}) {msg}")
    return 0 if score >= args.fail_under else 1


if __name__ == "__main__":
    raise SystemExit(main())

