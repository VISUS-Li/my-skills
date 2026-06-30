#!/usr/bin/env python3
"""Score director-level quality risks across a video project.

This heuristic catches common automated-video failures: PPT-like beats, empty
HyperFrames frames, boring backgrounds, SVG overuse, no real evidence, flat
text, screenshots that do not guide attention, constant density, missing
transition anchors, and overloaded emotional beats.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


REAL_PREFIXES = ("ref_", "motion_", "stock_", "screenshot_")
PROGRAMMATIC_PREFIXES = ("hf_", "text_", "chart_", "svg_", "ambient_")
BACKGROUND_HINTS = ("bg", "grid", "noise", "grain", "shadow", "ambient", "plate", "light", "map", "desk")
SUPPORT_HINTS = ("icon", "chip", "badge", "chart", "card", "source", "cursor", "frame", "stack", "bar", "arrow")
TEXT_PREFIXES = ("text_",)
SVG_HINTS = ("svg", "icon_", "arrow", "box", "ring", "connector", "bracket")
EVIDENCE_TYPES = {"evidence", "proof", "source", "data"}
SPARSE_TYPES = {"emotion", "viewpoint", "person", "transition", "reset"}


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


def split_ids(value: str) -> list[str]:
    return [x.strip() for x in re.split(r"[;|]", str(value or "")) if x.strip() and x.strip().lower() != "none"]


def beat_type(row: dict[str, str]) -> str:
    return (row.get("beat_type") or row.get("visual_intent") or row.get("retention_role") or "").strip().lower()


def asset_ids(row: dict[str, str]) -> list[str]:
    values: list[str] = []
    for key in ("asset_ids", "primary_asset", "secondary_asset", "accent_asset", "ambient_asset", "assets"):
        values.extend(split_ids(row.get(key, "")))
    return list(dict.fromkeys(values))


def has_real(ids: list[str]) -> bool:
    return any(a.lower().startswith(REAL_PREFIXES) for a in ids)


def has_programmatic(ids: list[str]) -> bool:
    return any(a.lower().startswith(PROGRAMMATIC_PREFIXES) for a in ids)


def has_background(ids: list[str]) -> bool:
    return any(any(h in a.lower() for h in BACKGROUND_HINTS) for a in ids)


def has_support_actor(ids: list[str]) -> bool:
    return any(any(h in a.lower() for h in SUPPORT_HINTS) for a in ids)


def text_only(ids: list[str]) -> bool:
    useful = [a.lower() for a in ids if a.lower() not in {"none", ""}]
    return bool(useful) and all(a.startswith(TEXT_PREFIXES) or a in {"hf_black"} for a in useful)


def svg_like(asset_id: str) -> bool:
    low = asset_id.lower()
    return any(h in low for h in SVG_HINTS)


def score_project(root: Path, fail_under: int) -> tuple[int, list[dict[str, object]]]:
    issues: list[dict[str, object]] = []
    score = 100

    narration = read_csv(root / "script" / "narration_beats.csv")
    sync = read_csv(root / "script" / "visual_sync_plan.csv")
    text_manifest = load_json(root / "script" / "text_manifest.json", {})
    beat_timeline = load_json(root / "script" / "beat_timeline.json", {})
    storyboard = load_json(root / "script" / "storyboard.json", {})

    if not narration:
        issues.append({"message": "missing narration beats; no phrase-level director decisions", "penalty": 25})
    if not sync:
        issues.append({"message": "missing visual sync plan; voice-to-picture cannot be judged", "penalty": 25})

    sync_by_beat = {r.get("beat_id", ""): r for r in sync}
    svg_only = 0
    real_count = 0
    bg_count = 0
    support_count = 0
    constant_density: list[str] = []
    missing_transition_anchor = 0
    flat_visuals = 0
    overloaded_sparse = 0
    empty_normal_beats = 0

    for row in narration:
        bid = row.get("beat_id", "")
        sr = sync_by_beat.get(bid, {})
        merged = {**row, **sr}
        ids = asset_ids(merged)
        btype = beat_type(merged)
        density = (row.get("information_density") or sr.get("density") or "").lower()
        if density:
            constant_density.append(density)

        is_sparse = btype in SPARSE_TYPES or density in {"low", "sparse"}
        if has_real(ids):
            real_count += 1
        if has_background(ids):
            bg_count += 1
        if has_support_actor(ids):
            support_count += 1

        if ids and all(svg_like(a) for a in ids):
            svg_only += 1
            if btype not in {"mechanism", "transition", "hook"}:
                issues.append({"message": f"{bid}: SVG-only visual strategy on {btype or 'unspecified'} beat", "penalty": 6})

        concrete_words = row.get("narration", "") + row.get("spoken_focus", "") + sr.get("visual_subject_desc", "")
        if re.search(r"App|网页|截图|表格|公告|官方|价格|公司|人物|地震|广告|VIP|手机|汽车|司机", concrete_words, re.I) and not ids:
            issues.append({"message": f"{bid}: concrete spoken phrase has no bound visual asset", "penalty": 8})

        if btype in EVIDENCE_TYPES:
            if not (sr.get("must_show_detail") or "").strip():
                issues.append({"message": f"{bid}: evidence/data beat lacks must_show_detail", "penalty": 6})
            attention_text = sr.get("acceptance_check", "") + sr.get("screen_content_desc", "")
            if not re.search(r"框|highlight|放大|crop|zoom|标注|label|source|来源|红|锁定|tap|pulse|chip", attention_text, re.I):
                issues.append({"message": f"{bid}: evidence beat does not describe attention guidance", "penalty": 5})

        if not is_sparse:
            if text_only(ids):
                empty_normal_beats += 1
            if has_programmatic(ids) and not has_background(ids):
                issues.append({"message": f"{bid}: HyperFrames-native beat lacks a designed background bed", "penalty": 4})
            if has_programmatic(ids) and not (has_support_actor(ids) or has_real(ids)):
                issues.append({"message": f"{bid}: HyperFrames-native beat lacks support actors such as icons/chips/cards/charts", "penalty": 4})

        if btype in SPARSE_TYPES and len(ids) >= 6:
            overloaded_sparse += 1

        if btype == "transition" and not (sr.get("transition_anchor") or sr.get("visual_intent") or "").strip():
            missing_transition_anchor += 1

        desc = " ".join([sr.get("visual_subject_desc", ""), sr.get("screen_content_desc", "")]).lower()
        if re.search(r"title|bullet|center card|标题|要点|居中卡片", desc) and not has_real(ids):
            flat_visuals += 1

    total = max(1, len(narration))
    if narration and real_count / total < 0.25:
        issues.append({"message": f"low reality texture: only {real_count}/{total} beats use ref/motion/stock assets", "penalty": 10})
    if narration and bg_count / total < 0.45:
        issues.append({"message": f"weak visual world: only {bg_count}/{total} beats declare background/grid/texture/depth components", "penalty": 10})
    if narration and support_count / total < 0.35:
        issues.append({"message": f"low support-actor density: only {support_count}/{total} beats include icons/chips/cards/charts/source frames", "penalty": 8})
    if empty_normal_beats:
        issues.append({"message": f"{empty_normal_beats} normal beats are effectively text-only or black-screen", "penalty": min(12, empty_normal_beats * 5)})
    if svg_only / total > 0.35:
        issues.append({"message": f"SVG overuse: {svg_only}/{total} beats are SVG-like", "penalty": 8})
    if len(set(constant_density)) <= 1 and len(constant_density) >= 5:
        issues.append({"message": "density does not vary across the piece", "penalty": 8})
    if missing_transition_anchor:
        issues.append({"message": f"{missing_transition_anchor} transition beats lack explicit transition anchors", "penalty": min(10, missing_transition_anchor * 4)})
    if flat_visuals:
        issues.append({"message": f"{flat_visuals} beats look PPT-like without concrete material", "penalty": min(12, flat_visuals * 4)})
    if overloaded_sparse:
        issues.append({"message": f"{overloaded_sparse} sparse/emotional beats appear overloaded", "penalty": min(10, overloaded_sparse * 4)})

    text_items = text_manifest.get("items", []) if isinstance(text_manifest, dict) else []
    if text_items:
        roles = {str(item.get("role", "")).lower() for item in text_items if isinstance(item, dict)}
        if len(roles - {"bottom_caption", "caption", ""}) < 2:
            issues.append({"message": "text system is mostly captions; add keyword, number_hero, quote_card, contrast_label, or viewpoint_line roles", "penalty": 8})
    else:
        issues.append({"message": "missing text_manifest items; dynamic text hierarchy cannot be reviewed", "penalty": 8})

    all_asset_ids: list[str] = []
    for row in sync:
        all_asset_ids.extend(asset_ids(row))
    for row in narration:
        all_asset_ids.extend(asset_ids(row))
    programmatic_count = sum(1 for aid in set(all_asset_ids) if aid.lower().startswith(PROGRAMMATIC_PREFIXES))
    if narration and programmatic_count < 6:
        issues.append({
            "message": "few HyperFrames-native components are planned; add background, cards, icons, chips, charts, masks, and text layers in segment code",
            "penalty": 6,
        })

    events = beat_timeline.get("beats", []) if isinstance(beat_timeline, dict) else []
    if events:
        generic_actions = 0
        rich_motion = 0
        for event in events:
            action = str(event.get("visual_action", "")).lower()
            if len(action) < 25 or action in {"show", "display", "fade in", "出现"}:
                generic_actions += 1
            if re.search(r"grid|icon|chip|chart|card|cursor|scan|pulse|draw|count|lock|settle|drift|红框|图标|图表|卡片|漂移|锁定", action, re.I):
                rich_motion += 1
        if generic_actions / max(1, len(events)) > 0.35:
            issues.append({"message": "beat_timeline has too many generic visual actions", "penalty": 8})
        if rich_motion == 0:
            issues.append({"message": "beat_timeline does not describe background/support actor motion", "penalty": 8})
    else:
        issues.append({"message": "beat_timeline has no micro-events", "penalty": 10})

    segments = storyboard.get("segments", []) if isinstance(storyboard, dict) else []
    if segments:
        shot_counts = [len(seg.get("shots", [])) for seg in segments if isinstance(seg, dict)]
        if shot_counts and sum(1 for count in shot_counts if count < 2) > len(shot_counts) / 2:
            issues.append({"message": "many storyboard segments have fewer than two shots; add establish/insert/payoff progression", "penalty": 8})

    for item in issues:
        score -= int(item["penalty"])
    score = max(0, min(100, score))
    return score, issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Director quality lint for non-PPT factual/story videos.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--fail-under", type=int, default=78)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    score, issues = score_project(root, args.fail_under)
    out = root / "edit" / "director_quality_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Director Quality Report", "", f"Score: {score}", "", "## Issues"]
    if issues:
        lines.extend(f"- (-{i['penalty']}) {i['message']}" for i in issues)
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Review Focus",
        "- Bind concrete narration to concrete material.",
        "- Build a visual world: grid/texture/depth, not plain empty backgrounds.",
        "- Add support actors: icons, chips, source cards, mini charts, cursors, badges.",
        "- Make screenshots perform: establish, focus, label, hold, exit.",
        "- Split dynamic text into roles beyond captions.",
        "- Vary density by section and use transition anchors between beats.",
    ])
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Director quality score: {score}")
    print(f"Wrote {out}")
    for item in issues:
        print(f"- (-{item['penalty']}) {item['message']}")
    return 0 if score >= args.fail_under else 1


if __name__ == "__main__":
    raise SystemExit(main())
