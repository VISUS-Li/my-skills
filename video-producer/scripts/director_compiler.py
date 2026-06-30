#!/usr/bin/env python3
"""Compile phrase-level narration beats into a director event timeline.

This is a deterministic scaffold, not a final creative pass. It prevents the
common failure of treating one sentence as one static slide by creating timed
micro-events, asset actor rows, an event graph, and SFX cue candidates.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"missing {path}")
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def load_visual_sync(root: Path) -> dict[str, dict[str, str]]:
    path = root / "script" / "visual_sync_plan.csv"
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        return {r.get("beat_id", ""): r for r in csv.DictReader(f) if r.get("beat_id")}


def load_beat_asset_plans(root: Path) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for path in (root / "segments").glob("*/beat_asset_plan.csv"):
        with path.open(newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                bid = row.get("beat_id", "")
                if bid:
                    out[bid] = row
    return out


def split_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return [x.strip() for x in re.split(r"[;,|]", str(value or "")) if x.strip()]


def planned_assets(row: dict[str, str], sync_row: dict[str, str], asset_row: dict[str, str]) -> list[str]:
    assets = split_list(sync_row.get("asset_ids", ""))
    for key in ["primary_asset", "secondary_asset", "accent_asset", "ambient_asset"]:
        value = (asset_row.get(key) or "").strip()
        if value and value.lower() != "none" and value not in assets:
            assets.append(value)
    return assets


def choose_assets(action: str, role: str) -> list[str]:
    text = f"{action} {role}".lower()
    zh = f"{action} {role}"
    if any(k in text for k in ["compare", "contrast"]) or any(k in zh for k in ["对比", "比较", "反差"]):
        return ["comparison_split", "arrow_pipeline", "status_badge"]
    if any(k in text for k in ["error", "fail", "risk", "warning"]) or any(k in zh for k in ["错误", "失败", "风险", "警告", "翻车"]):
        return ["wrong_output_card", "error_stamp", "shake_marker"]
    if any(k in text for k in ["proof", "source", "quote", "evidence"]) or any(k in zh for k in ["证明", "证据", "引用", "资料", "来源"]):
        return ["source_card", "highlight_box", "document_stack"]
    if any(k in text for k in ["mechanism", "explain", "process", "pipeline"]) or any(k in zh for k in ["机制", "解释", "流程", "处理", "转换"]):
        return ["hero_machine", "arrow_pipeline", "module_chip"]
    if any(k in text for k in ["hook", "question", "curiosity"]) or any(k in zh for k in ["悬念", "问题", "为什么"]):
        return ["question_card", "glitch_flash", "title_card"]
    if any(k in text for k in ["takeaway", "conclusion", "success"]) or any(k in zh for k in ["结论", "总结", "解决", "成功"]):
        return ["takeaway_card", "success_badge", "checklist"]
    return ["info_card", "focus_ring", "background_grid"]


def micro_event_specs(duration: float, action: str, role: str) -> list[tuple[str, str, str]]:
    if duration <= 0.75:
        return [
            ("attention_shift", "primary asset snaps in and claims the focal point", "pop"),
            ("semantic_motion", "highlight or arrow shows the spoken verb", "tick"),
        ]
    if duration <= 1.5:
        return [
            ("attention_shift", "asset entrance or camera punch-in", "pop"),
            ("semantic_motion", "process/action becomes visible", "tick"),
            ("emphasis", "badge, underline, or source highlight lands", "hit"),
        ]
    return [
        ("attention_shift", "asset entrance or layout split establishes context", "pop"),
        ("semantic_motion", "first part of the process is drawn or scanned", "tick"),
        ("transform", "object changes state or connects to next module", "data_tick"),
        ("emphasis", "stamp/check/source highlight confirms the phrase", "hit"),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile narration beats into beat_timeline, event graph, asset choreography, and cue candidates.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing target files")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    narration_rows = read_csv(root / "script" / "narration_beats.csv")
    visual_sync = load_visual_sync(root)
    beat_asset_plans = load_beat_asset_plans(root)
    timeline_path = root / "script" / "beat_timeline.json"
    event_graph_path = root / "script" / "director_event_graph.json"
    choreo_path = root / "assets" / "asset_choreography_manifest.csv"
    cue_path = root / "audio" / "audio_cue_sheet.json"

    for path in [timeline_path, event_graph_path, choreo_path, cue_path]:
        if path.exists() and not args.overwrite:
            raise SystemExit(f"target exists, pass --overwrite to replace: {path}")

    beats: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    choreo: dict[str, dict[str, Any]] = {}
    cues: list[dict[str, Any]] = []

    prev_event_id = ""
    for row_index, row in enumerate(narration_rows, 1):
        base_id = row.get("beat_id") or f"B{row_index:03d}"
        segment_id = row.get("segment_id") or "S01"
        try:
            start = float(row.get("start_sec") or 0)
            end = float(row.get("end_sec") or start + 1.0)
        except ValueError:
            start = float(row_index - 1)
            end = start + 1.0
        if end <= start:
            end = start + 1.0
        duration = end - start
        narration = row.get("narration", "")
        action = row.get("semantic_action", "")
        role = row.get("retention_role", "") or row.get("emotion", "")
        claim_ids = split_list(row.get("claim_ids", ""))
        text_ids = split_list(row.get("text_ids", ""))
        source_visual = row.get("source_visual", "")
        sync_row = visual_sync.get(base_id, {})
        asset_row = beat_asset_plans.get(base_id, {})
        assets = planned_assets(row, sync_row, asset_row) or choose_assets(action, role)
        if source_visual and source_visual.lower() not in {"none", "no", ""} and "source_card" not in assets:
            assets.append("source_card")
        spoken_focus = sync_row.get("spoken_focus") or row.get("spoken_focus") or action or narration[:16]
        visual_subject = sync_row.get("visual_subject_desc") or asset_row.get("visual_subject_desc") or "planned visual actor"
        screen_content = sync_row.get("screen_content_desc") or asset_row.get("screen_content_desc") or "frame content follows the spoken phrase"
        must_show = sync_row.get("must_show_detail") or asset_row.get("must_show_detail") or spoken_focus
        focal_owner = sync_row.get("focal_owner") or asset_row.get("primary_asset") or (assets[0] if assets else "info_card")

        specs = micro_event_specs(duration, action, role)
        step = duration / len(specs)
        for j, (event_type, visual, cue_kind) in enumerate(specs, 1):
            s = round(start + step * j - step, 3)
            e = round(start + step * j, 3)
            beat_id = f"{base_id}_E{j:02d}"
            primary_asset = focal_owner if j == 1 else (assets[min(j - 1, len(assets) - 1)] if assets else "info_card")
            cue_id = "deliberate_silence" if "silence" in row.get("sfx_intent", "").lower() else f"SFX_{beat_id}_{cue_kind.upper()}"
            beat = {
                "beat_id": beat_id,
                "segment_id": segment_id,
                "start_sec": s,
                "end_sec": e,
                "narration": narration,
                "claim_ids": claim_ids,
                "intent": role or sync_row.get("visual_intent") or "explain",
                "beat_type": event_type,
                "visual_action": f"{visual}; focal owner {primary_asset} shows '{spoken_focus}'. Screen: {screen_content}. Must remain visible: {must_show}.",
                "assets": assets,
                "text_ids": text_ids,
                "layout_zone": sync_row.get("layout_zone") or ("center" if j == 1 else "attention_path"),
                "camera": "micro_push_in" if j == 1 else "parallax_or_focus_shift",
                "motion": {
                    "entrance": "0.18-0.35s snap/slide with overshoot" if j == 1 else "inherits previous asset position",
                    "main": "draw/scan/pulse/morph the semantic action",
                    "exit": "none unless next beat changes scene",
                    "easing": "easeOutCubic for clarity; easeOutBack for tactile hits",
                },
                "sfx_cue_ids": [cue_id],
                "density_note": f"focal={primary_asset}; subject={visual_subject}; supporting layers stay secondary",
                "why_not_ppt": "visual sync plan defines a focal owner, screen content, readable detail, and timed asset behavior",
            }
            beats.append(beat)
            event_id = f"E{len(nodes)+1:04d}"
            nodes.append({
                "event_id": event_id,
                "beat_id": beat_id,
                "segment_id": segment_id,
                "time_range": [s, e],
                "event_type": event_type,
                "description": beat["visual_action"],
                "primary_asset": primary_asset,
                "claim_ids": claim_ids,
            })
            if prev_event_id:
                edges.append({
                    "from": prev_event_id,
                    "to": event_id,
                    "edge_type": "attention_edge",
                    "reason": "next timed event continues the narration attention path",
                })
            prev_event_id = event_id
            cues.append({
                "cue_id": cue_id,
                "type": "silence" if cue_id == "deliberate_silence" else "sfx",
                "segment_id": segment_id,
                "start_sec": s,
                "duration_sec": max(0.12, min(0.6, e - s)),
                "sync_anchor": beat_id,
                "role": event_type,
                "sound_concept": "intentional silence" if cue_id == "deliberate_silence" else f"short {cue_kind} synced to {primary_asset}",
                "search_prompt": "" if cue_id == "deliberate_silence" else f"clean UI {cue_kind}, short, soft, no music tail",
                "gain_db": -18 if cue_id != "deliberate_silence" else -99,
                "fade_in_ms": 10,
                "fade_out_ms": 80,
                "ducking": "duck music lightly, never mask voice",
                "path_or_url": "",
                "rights_status": "candidate_needed" if cue_id != "deliberate_silence" else "safe",
                "status": "draft",
            })

        first = start
        last = end
        for asset_id in assets:
            current = choreo.get(asset_id)
            if current:
                current["last_on_sec"] = max(float(current["last_on_sec"]), last)
                if segment_id not in str(current["reused_in_segments"]):
                    current["reused_in_segments"] = f"{current['reused_in_segments']};{segment_id}"
                continue
            choreo[asset_id] = {
                "asset_id": asset_id,
                "type": "svg_component",
                "description": f"director actor for {asset_id}",
                "source_or_prompt": "drawn SVG or programmatic component, no baked Chinese text",
                "rights_status": "safe",
                "layer": "midground" if asset_id not in {"background_grid", "glitch_flash"} else "background",
                "first_on_sec": round(first, 3),
                "last_on_sec": round(last, 3),
                "entrance": "snap/slide/draw in with 0.18-0.35s overshoot",
                "main_motion": "pulse, scan, morph, blink, or connect according to beat timeline",
                "exit": "fade/slide only when semantically leaving the scene",
                "states": "idle|active|emphasis|exit",
                "reused_in_segments": segment_id,
                "sfx_affordance": "pop; tick; hit; chime; deliberate_silence",
                "implementation_notes": "render as grouped vector/component actor controlled by beat_timeline.json",
            }

    timeline = {
        "version": "v002",
        "timebase": "seconds",
        "generated_by": "scripts/director_compiler.py",
        "policy": {
            "max_unchanged_hold_sec": 1.5,
            "normal_beat_spacing_sec": [0.3, 1.2],
            "every_narration_phrase_requires_visual_response": True,
            "sfx_must_have_visible_or_semantic_anchor": True,
            "programmatic_text_only": True,
            "claim_ids_required_for_factual_beats": True,
        },
        "beats": beats,
    }
    event_graph = {
        "version": "v001",
        "timebase": "seconds",
        "generated_by": "scripts/director_compiler.py",
        "nodes": nodes,
        "edges": edges,
    }
    existing_cues = load_json(cue_path, {"version": "v001", "timebase": "seconds", "cues": []})
    existing_cues["cues"] = cues

    timeline_path.parent.mkdir(parents=True, exist_ok=True)
    timeline_path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    event_graph_path.write_text(json.dumps(event_graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(choreo_path, list(choreo.values()), [
        "asset_id", "type", "description", "source_or_prompt", "rights_status", "layer", "first_on_sec", "last_on_sec", "entrance", "main_motion", "exit", "states", "reused_in_segments", "sfx_affordance", "implementation_notes",
    ])
    cue_path.parent.mkdir(parents=True, exist_ok=True)
    cue_path.write_text(json.dumps(existing_cues, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Compiled {len(narration_rows)} narration rows into {len(beats)} micro-events.")
    print(f"Wrote {timeline_path}")
    print(f"Wrote {event_graph_path}")
    print(f"Wrote {choreo_path}")
    print(f"Wrote {cue_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
