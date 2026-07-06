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
EXPRESSIVE_TEXT_ROLES = {"keyword", "number_hero", "contrast_label", "quote_card", "evidence_label", "viewpoint_line"}
MOTION_WORDS = ("fade", "slide", "pop", "blur", "scale", "zoom", "wipe", "snap", "slam", "draw", "pulse")
YIELD_WORDS = ("yield", "reactive", "displacement", "make room", "gives way", "让位")
TEXT_STORE_WORDS = ("store", "chip", "stack", "shrink", "yield", "corner", "入栈", "缩小", "让位", "移到")
PROOF_PROTECTION_WORDS = ("must_show", "source", "table", "axis", "label", "readable", "detail", "crop", "hold")


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


def words(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(words(v) for v in value)
    if isinstance(value, dict):
        return " ".join(words(v) for v in value.values())
    return str(value)


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


def item_has_sync(item: dict[str, Any]) -> bool:
    if item.get("sync_phrase"):
        return True
    spans = item.get("spans")
    if isinstance(spans, list):
        return any(isinstance(span, dict) and span.get("sync_phrase") for span in spans)
    return False


def item_has_preset(item: dict[str, Any]) -> bool:
    if item.get("motion_preset_id") or item.get("text_preset_id"):
        return True
    spans = item.get("spans")
    if isinstance(spans, list):
        return any(
            isinstance(span, dict) and (span.get("motion_preset_id") or span.get("text_preset_id"))
            for span in spans
        )
    return False


def event_presets(event: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("motion_preset_id", "text_preset_id"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
    for key in ("motion_preset_ids", "text_preset_ids"):
        value = event.get(key)
        if isinstance(value, list):
            values.extend(str(v).strip() for v in value if str(v).strip())
    return values


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
    layout_values: list[str] = []
    concrete_visual_need = 0
    non_sparse_total = 0
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
        if not is_sparse:
            non_sparse_total += 1
        layout = (sr.get("layout_mode") or sr.get("layout_zone") or row.get("layout_mode") or "").strip().lower()
        if layout:
            layout_values.append(layout)
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
        if re.search(r"App|网页|截图|表格|公告|官方|价格|公司|人物|地震|广告|VIP|手机|汽车|司机", concrete_words, re.I):
            concrete_visual_need += 1
            if not ids:
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
    active_total = max(1, non_sparse_total)
    if concrete_visual_need >= 3 and real_count / max(1, concrete_visual_need) < 0.25:
        issues.append({"message": f"low concrete/reality casting: {concrete_visual_need} concrete beats, only {real_count} use ref/motion/stock assets", "penalty": 8})
    if non_sparse_total >= 3 and bg_count / active_total < 0.35:
        issues.append({"message": f"weak visual-world direction on active beats: only {bg_count}/{active_total} non-sparse beats declare background/grid/texture/depth components", "penalty": 8})
    if non_sparse_total >= 3 and support_count / active_total < 0.25:
        issues.append({"message": f"low support-actor casting on active beats: only {support_count}/{active_total} non-sparse beats include icons/chips/cards/charts/source frames", "penalty": 6})
    if empty_normal_beats:
        issues.append({"message": f"{empty_normal_beats} normal beats are effectively text-only or black-screen", "penalty": min(12, empty_normal_beats * 5)})
    if svg_only / total > 0.35:
        issues.append({"message": f"SVG overuse: {svg_only}/{total} beats are SVG-like", "penalty": 8})
    if len(set(constant_density)) <= 1 and len(constant_density) >= 5:
        issues.append({"message": "density does not vary across the piece", "penalty": 8})
    if len(set(layout_values)) <= 1 and len(layout_values) >= 5:
        issues.append({"message": "layout mode does not vary; director should justify a repeated layout or restage some beats", "penalty": 6})
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
        span_items = 0
        expressive_without_sync = 0
        expressive_without_preset = 0
        collision_unprotected = 0
        expressive_without_persistence = 0
        for item in text_items:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role", "")).lower()
            spans = item.get("spans")
            if isinstance(spans, list) and spans:
                span_items += 1
            if role in EXPRESSIVE_TEXT_ROLES:
                if not item_has_sync(item):
                    expressive_without_sync += 1
                if not item_has_preset(item):
                    expressive_without_preset += 1
                avoid_zones = item.get("avoid_zones")
                attached = item.get("attach_to") or item.get("position")
                if role in {"keyword", "evidence_label", "contrast_label"} and attached and not avoid_zones:
                    collision_unprotected += 1
                if not item.get("persistence_policy") and not item.get("previous_text_behavior"):
                    expressive_without_persistence += 1
        if expressive_without_sync:
            issues.append({"message": f"{expressive_without_sync} expressive text items lack sync_phrase/span timing", "penalty": min(8, expressive_without_sync * 3)})
        if expressive_without_preset:
            issues.append({"message": f"{expressive_without_preset} expressive text items lack motion/text preset IDs", "penalty": min(6, expressive_without_preset * 2)})
        if collision_unprotected:
            issues.append({"message": f"{collision_unprotected} attached text items lack avoid_zones for proof collision safety", "penalty": min(6, collision_unprotected * 2)})
        if expressive_without_persistence:
            issues.append({"message": f"{expressive_without_persistence} expressive text items do not say whether they hold, yield, store, stack, or intentionally exit", "penalty": min(6, expressive_without_persistence * 2)})
        if len(text_items) >= 4 and span_items == 0 and any(role in EXPRESSIVE_TEXT_ROLES for role in roles):
            issues.append({"message": "expressive text has no spans; use spans when a line needs mixed size/color/timing", "penalty": 5})
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
        common_motion_without_preset = 0
        preset_count = 0
        unsafe_yield = 0
        text_store_count = 0
        visual_cast_count = 0
        for event in events:
            action = str(event.get("visual_action", "")).lower()
            event_words = words(event).lower()
            presets = event_presets(event)
            if isinstance(event.get("visual_cast"), dict):
                visual_cast_count += 1
            layout = str(event.get("layout_mode") or event.get("layout_zone") or "").strip().lower()
            if layout:
                layout_values.append(layout)
            if presets:
                preset_count += 1
            if len(action) < 25 or action in {"show", "display", "fade in", "出现"}:
                generic_actions += 1
            if re.search(r"grid|icon|chip|chart|card|cursor|scan|pulse|draw|count|lock|settle|drift|红框|图标|图表|卡片|漂移|锁定", action, re.I):
                rich_motion += 1
            if any(word in action for word in MOTION_WORDS) and not presets:
                common_motion_without_preset += 1
            is_yield = any(p.startswith("reactive.yield") for p in presets) or any(word in event_words for word in YIELD_WORDS)
            if is_yield and not any(word in event_words for word in PROOF_PROTECTION_WORDS):
                unsafe_yield += 1
            if any(p.startswith("text.store") or p.startswith("text.yield") for p in presets) or any(word in event_words for word in TEXT_STORE_WORDS):
                text_store_count += 1
        if generic_actions / max(1, len(events)) > 0.35:
            issues.append({"message": "beat_timeline has too many generic visual actions", "penalty": 8})
        if rich_motion == 0:
            issues.append({"message": "beat_timeline does not describe background/support actor motion", "penalty": 8})
        if common_motion_without_preset / max(1, len(events)) > 0.4:
            issues.append({"message": "common fade/slide/pop/blur/scale moves are described without reusable preset IDs", "penalty": 5})
        if unsafe_yield:
            issues.append({"message": f"{unsafe_yield} yield/reactive moves do not state proof-readability or must-show protection", "penalty": min(8, unsafe_yield * 4)})
        if len(events) >= 3 and preset_count == 0:
            issues.append({"message": "beat_timeline uses no named motion/text presets; add IDs for reusable entrance, text, or yield moves where appropriate", "penalty": 4})
        if len(events) >= 3 and visual_cast_count == 0:
            issues.append({"message": "beat_timeline does not document visual casting; identify lead/support/withheld actors for complex segments", "penalty": 4})
        expressive_count = sum(
            1 for item in text_items
            if isinstance(item, dict) and str(item.get("role", "")).lower() in EXPRESSIVE_TEXT_ROLES
        )
        if expressive_count >= 3 and text_store_count == 0:
            issues.append({"message": "multiple expressive text items but no text store/yield behavior in beat_timeline", "penalty": 5})
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
        "- Split dynamic text into roles beyond captions; add spans, sync phrases, presets, and avoid zones when text acts on proof.",
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
