#!/usr/bin/env python3
"""Stage readiness checks: required artifacts, beat contract, template leftovers, lint scripts."""
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path
from typing import Any

from review_core import load_json, load_stage_manifest, resolve_safe_path, skill_root

NARRATION_BEATS_COLUMNS = frozenset({
    "beat_id",
    "segment_id",
    "start_sec",
    "end_sec",
    "duration_sec",
    "narration",
    "char_count",
    "claim_ids",
    "semantic_action",
    "beat_type",
    "information_density",
    "spoken_focus",
    "visual_response_required",
    "visual_need",
    "sfx_intent",
})

TEMPLATE_MARKERS = (
    "示例：那一刻，房间里的吊灯先晃了起来。",
    "很多人第一反应，是打开地震预警 App。",
    "吊灯晃起来",
    "地震预警 App",
    "示例：先把问题摆出来。",
)

STAGE_CONTENT_GATES: dict[str, list[str]] = {
    "script": ["artifacts", "voiceover", "narration_content", "template_leftovers"],
    "design": ["artifacts"],
    "assets": ["artifacts", "beat_asset_alignment", "template_leftovers"],
    "director-plan": ["artifacts", "visual_sync_alignment", "template_leftovers"],
    "voice-and-sound": ["artifacts", "prosody_sync"],
    "segments": ["artifacts"],
    "assemble": ["artifacts"],
    "qc": ["artifacts"],
    "publish": ["artifacts"],
    "plan": ["artifacts"],
    "research": ["artifacts"],
    "fact-lock": ["artifacts"],
}


def scripts_dir() -> Path:
    return Path(__file__).resolve().parent


def read_csv_rows(path: Path, *, segment_id: str | None = None) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if segment_id and row.get("segment_id", "").upper() != segment_id.upper():
                continue
            rows.append(dict(row))
    return rows


def default_segment(root: Path) -> str:
    video = load_json(root / ".video" / "video.json")
    segments = video.get("segments")
    if isinstance(segments, list) and segments:
        first = segments[0]
        if isinstance(first, dict) and first.get("id"):
            return str(first["id"])
        if isinstance(first, str):
            return first
    storyboard = load_json(root / "script" / "storyboard.json")
    segs = storyboard.get("segments")
    if isinstance(segs, list) and segs:
        seg_id = segs[0].get("id") if isinstance(segs[0], dict) else None
        if seg_id:
            return str(seg_id)
    return "S001"


def resolve_required_artifacts(root: Path, stage_id: str, segment: str) -> list[str]:
    manifest = load_stage_manifest(root)
    meta = manifest.get("stages", {}).get(stage_id, {})
    paths: list[str] = []
    for pattern in meta.get("required_artifacts", []):
        rel = pattern.replace("{segment}", segment)
        paths.append(rel)
    return paths


def validate_required_artifacts(root: Path, stage_id: str, segment: str) -> list[str]:
    errors: list[str] = []
    for rel in resolve_required_artifacts(root, stage_id, segment):
        resolved = resolve_safe_path(root, rel)
        if not resolved or not resolved.exists():
            errors.append(f"{stage_id}: missing required artifact: {rel}")
            continue
        if resolved.is_file() and resolved.stat().st_size == 0:
            errors.append(f"{stage_id}: required artifact is empty: {rel}")
    return errors


def validate_narration_beats_schema(root: Path) -> list[str]:
    path = root / "script" / "narration_beats.csv"
    errors: list[str] = []
    if not path.exists():
        return ["script/narration_beats.csv missing"]
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            fieldnames = set(reader.fieldnames or [])
            missing = sorted(NARRATION_BEATS_COLUMNS - fieldnames)
            if missing:
                errors.append(
                    "script/narration_beats.csv missing columns: "
                    + ", ".join(missing)
                    + " (copy full schema from skill template; spoken_focus alone is not enough for Review Studio)"
                )
    except Exception as exc:  # noqa: BLE001
        errors.append(f"invalid narration_beats.csv: {exc}")
    return errors


def _planned_duration(row: dict[str, str]) -> float:
    raw = (row.get("duration_sec") or row.get("estimated_sec") or "").strip()
    if raw:
        return float(raw)
    start = float(row.get("start_sec") or 0)
    end = float(row.get("end_sec") or start)
    return max(0.0, end - start)


def validate_narration_beats_content(root: Path, segment: str) -> list[str]:
    errors: list[str] = []
    rows = read_csv_rows(root / "script" / "narration_beats.csv", segment_id=segment)
    if not rows:
        errors.append(f"script/narration_beats.csv has no rows for segment {segment}")
        return errors
    for row in rows:
        bid = row.get("beat_id", "") or "?"
        narration = (row.get("narration") or "").strip()
        if not narration:
            errors.append(f"{bid}: narration is empty (Review Studio director page reads this column)")
        elif len(narration.replace(" ", "")) < 4:
            errors.append(f"{bid}: narration too short")
        if _planned_duration(row) <= 0:
            errors.append(f"{bid}: missing positive duration_sec or start_sec/end_sec")
        focus = (row.get("spoken_focus") or "").strip()
        if not focus:
            errors.append(f"{bid}: spoken_focus is empty")
    return errors


def validate_voiceover_present(root: Path) -> list[str]:
    path = root / "script" / "voiceover.md"
    if not path.exists():
        return ["script/voiceover.md missing"]
    text = path.read_text(encoding="utf-8-sig").strip()
    if len(text) < 80:
        return ["script/voiceover.md is empty or too short"]
    return []


def _template_narration_values() -> set[str]:
    template_path = skill_root() / "assets" / "templates" / "narration_beats.csv"
    values: set[str] = set()
    for row in read_csv_rows(template_path):
        narration = (row.get("narration") or "").strip()
        focus = (row.get("spoken_focus") or "").strip()
        if narration:
            values.add(narration)
        if focus:
            values.add(focus)
    return values


def detect_template_leftovers(
    root: Path,
    segment: str,
    *,
    scopes: list[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    template_values = _template_narration_values()
    template_values.update(TEMPLATE_MARKERS)

    narr_rows = read_csv_rows(root / "script" / "narration_beats.csv", segment_id=segment)
    sync_rows = read_csv_rows(root / "script" / "visual_sync_plan.csv", segment_id=segment)
    prosody_rows = read_csv_rows(root / "audio" / "prosody_plan.csv", segment_id=segment)

    voiceover = ""
    vo_path = root / "script" / "voiceover.md"
    if vo_path.exists():
        voiceover = vo_path.read_text(encoding="utf-8-sig")

    active = set(scopes or ["narration_beats", "visual_sync_plan", "prosody_plan"])

    def check_field(file_label: str, beat_id: str, field: str, value: str) -> None:
        text = value.strip()
        if not text:
            return
        if text in template_values and text not in voiceover:
            errors.append(
                f"{file_label} {beat_id}.{field} still contains init template text: {text[:40]}…"
            )

    narr_focus = {
        (row.get("beat_id", ""), (row.get("spoken_focus") or "").strip())
        for row in narr_rows
        if row.get("beat_id")
    }

    if "narration_beats" in active:
        for row in narr_rows:
            bid = row.get("beat_id", "")
            check_field("narration_beats.csv", bid, "narration", row.get("narration", ""))
            check_field("narration_beats.csv", bid, "spoken_focus", row.get("spoken_focus", ""))

    if "visual_sync_plan" in active:
        for row in sync_rows:
            bid = row.get("beat_id", "")
            check_field("visual_sync_plan.csv", bid, "spoken_focus", row.get("spoken_focus", ""))
            sync_focus = (row.get("spoken_focus") or "").strip()
            if sync_focus and narr_focus and (bid, sync_focus) not in narr_focus:
                narr_match = next((f for b, f in narr_focus if b == bid), "")
                if narr_match and sync_focus != narr_match:
                    errors.append(
                        f"visual_sync_plan.csv {bid}: spoken_focus {sync_focus!r} "
                        f"does not match narration_beats.csv {narr_match!r} (likely unreplaced template)"
                    )

    if "prosody_plan" in active:
        for row in prosody_rows:
            bid = row.get("beat_id", "")
            check_field("prosody_plan.csv", bid, "tts_text", row.get("tts_text", ""))

    return errors


TEMPLATE_SCOPES: dict[str, list[str]] = {
    "script": ["narration_beats"],
    "assets": ["narration_beats"],
    "director-plan": ["narration_beats", "visual_sync_plan", "prosody_plan"],
    "voice-and-sound": ["prosody_plan"],
}


def validate_beat_id_alignment(
    root: Path,
    segment: str,
    *,
    plan_rel: str,
    plan_label: str,
) -> list[str]:
    errors: list[str] = []
    narr_ids = [
        row.get("beat_id", "")
        for row in read_csv_rows(root / "script" / "narration_beats.csv", segment_id=segment)
        if row.get("beat_id")
    ]
    if not narr_ids:
        return [f"no narration beats for segment {segment}"]
    plan_ids = [
        row.get("beat_id", "")
        for row in read_csv_rows(root / plan_rel, segment_id=segment)
        if row.get("beat_id")
    ]
    narr_set = set(narr_ids)
    plan_set = set(plan_ids)
    for bid in narr_ids:
        if bid not in plan_set:
            errors.append(f"{plan_label}: missing row for beat {bid} (narration_beats has {len(narr_ids)} beats)")
    for bid in plan_ids:
        if bid not in narr_set:
            errors.append(f"{plan_label}: extra row {bid} not in narration_beats.csv")
    return errors


def validate_prosody_sync(root: Path, segment: str) -> list[str]:
    errors: list[str] = []
    narr_by_beat = {
        row["beat_id"]: (row.get("narration") or "").strip()
        for row in read_csv_rows(root / "script" / "narration_beats.csv", segment_id=segment)
        if row.get("beat_id")
    }
    prosody_rows = read_csv_rows(root / "audio" / "prosody_plan.csv", segment_id=segment)
    prosody_by_beat = {
        row["beat_id"]: (row.get("tts_text") or "").strip()
        for row in prosody_rows
        if row.get("beat_id")
    }
    for beat_id, narration in narr_by_beat.items():
        tts = prosody_by_beat.get(beat_id, "")
        if not tts:
            errors.append(f"prosody_plan.csv: missing tts_text for {beat_id}")
        elif tts != narration:
            errors.append(f"prosody_plan.csv {beat_id}: tts_text does not match narration_beats narration")
    return errors


def _run_gate(name: str, root: Path, segment: str, stage_id: str = "") -> list[str]:
    if name == "artifacts":
        return []
    if name == "voiceover":
        return validate_voiceover_present(root)
    if name == "narration_schema":
        return validate_narration_beats_schema(root)
    if name == "narration_content":
        schema_errors = validate_narration_beats_schema(root)
        if schema_errors:
            return schema_errors
        return validate_narration_beats_content(root, segment)
    if name == "template_leftovers":
        scopes = TEMPLATE_SCOPES.get(stage_id, ["narration_beats"])
        return detect_template_leftovers(root, segment, scopes=scopes)
    if name == "beat_asset_alignment":
        return validate_beat_id_alignment(
            root,
            segment,
            plan_rel=f"segments/{segment}/beat_asset_plan.csv",
            plan_label=f"segments/{segment}/beat_asset_plan.csv",
        )
    if name == "visual_sync_alignment":
        return validate_beat_id_alignment(
            root,
            segment,
            plan_rel="script/visual_sync_plan.csv",
            plan_label="script/visual_sync_plan.csv",
        )
    if name == "prosody_sync":
        schema_errors = validate_narration_beats_schema(root)
        if schema_errors:
            return schema_errors
        return validate_prosody_sync(root, segment)
    return []


def validate_stage_readiness(root: Path, stage_id: str, segment: str | None = None) -> list[str]:
    """Return human-readable errors when a stage is not ready to advance."""
    seg = segment or default_segment(root)
    errors: list[str] = []
    errors.extend(validate_required_artifacts(root, stage_id, seg))
    for gate in STAGE_CONTENT_GATES.get(stage_id, ["artifacts"]):
        if gate == "artifacts":
            continue
        errors.extend(_run_gate(gate, root, seg, stage_id))
    return errors


def run_stage_validation_scripts(root: Path, stage_id: str, segment: str | None = None) -> list[str]:
    """Run stage_manifest validation_scripts synchronously; return errors on non-zero exit."""
    seg = segment or default_segment(root)
    manifest = load_stage_manifest(root)
    templates = manifest.get("stages", {}).get(stage_id, {}).get("validation_scripts", [])
    errors: list[str] = []
    for template in templates:
        parts = template.split()
        if not parts:
            continue
        script_name = parts[0]
        script_path = scripts_dir() / script_name
        if not script_path.exists():
            errors.append(f"{stage_id}: validation script missing: {script_name}")
            continue
        args = [sys.executable, str(script_path), str(root)]
        for part in parts[1:]:
            args.append(part.replace("{project}", str(root)).replace("{segment}", seg))
        result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            errors.append(f"{stage_id}: {script_name} failed (exit {result.returncode})")
            output = (result.stdout + "\n" + result.stderr).strip()
            for line in output.splitlines()[:8]:
                if line.strip():
                    errors.append(f"  {line.strip()}")
    return errors


def validate_stage_complete(
    root: Path,
    stage_id: str,
    *,
    segment: str | None = None,
    run_scripts: bool = True,
) -> list[str]:
    """Full stage gate: artifacts, content contract, and optional lint scripts."""
    errors = validate_stage_readiness(root, stage_id, segment)
    if run_scripts:
        errors.extend(run_stage_validation_scripts(root, stage_id, segment))
    return errors


def advancing_status(status: str) -> bool:
    return status in {"review", "approved", "locked", "rendered", "needs-revision"}
