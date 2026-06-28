#!/usr/bin/env python3
"""Shared review gate, registry, and stale-propagation utilities."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE_APPROVED = {"approved", "locked"}
ARTIFACT_STATUSES = {"draft", "review", "approved", "rejected", "stale", "locked"}
REGEN_STATUSES = {"pending", "in_progress", "completed", "failed"}


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def project_video_dir(root: Path) -> Path:
    return root / ".video"


def load_state(root: Path) -> dict[str, Any]:
    return load_json(project_video_dir(root) / "state.json")


def save_state(root: Path, state: dict[str, Any]) -> None:
    write_json(project_video_dir(root) / "state.json", state)


def load_stage_manifest(root: Path) -> dict[str, Any]:
    manifest_path = project_video_dir(root) / "stage_manifest.json"
    if manifest_path.exists():
        return load_json(manifest_path)
    template = skill_root() / "assets" / "templates" / "stage_manifest.json"
    if template.exists():
        return json.loads(template.read_text(encoding="utf-8"))
    return {"version": "1", "stages": {}}


def stage_dependencies(manifest: dict[str, Any], stage_id: str) -> list[str]:
    stage = manifest.get("stages", {}).get(stage_id, {})
    deps = stage.get("depends_on", [])
    return deps if isinstance(deps, list) else []


def content_hash(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def append_history(root: Path, event: dict[str, Any]) -> None:
    event = dict(event)
    event.setdefault("at", utc_now())
    history_path = project_video_dir(root) / "history.jsonl"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def read_registry_lines(root: Path) -> list[dict[str, Any]]:
    path = project_video_dir(root) / "review_registry.jsonl"
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def registry_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        artifact_id = row.get("artifact_id")
        if artifact_id:
            index[str(artifact_id)] = row
    return index


def append_registry(root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    entry = dict(entry)
    entry.setdefault("updated_at", utc_now())
    path = project_video_dir(root) / "review_registry.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    append_history(root, {"type": "registry_updated", "artifact_id": entry.get("artifact_id"), "status": entry.get("status")})
    return entry


def load_regen_queue(root: Path) -> dict[str, Any]:
    path = project_video_dir(root) / "regen_queue.json"
    if path.exists():
        return load_json(path)
    return {"version": "1", "items": []}


def save_regen_queue(root: Path, queue: dict[str, Any]) -> None:
    write_json(project_video_dir(root) / "regen_queue.json", queue)


def validate_stage_dependencies(
    root: Path,
    stage_id: str,
    *,
    target_status: str | None = None,
) -> list[str]:
    """Return errors when stage dependencies are not approved/locked."""
    manifest = load_stage_manifest(root)
    state = load_state(root)
    stages = state.get("stages", {})
    errors: list[str] = []
    advancing = target_status in {"review", "approved", "locked", "rendered", "needs-revision"}
    current = stages.get(stage_id, {}).get("status", "draft")
    should_check = advancing or current not in {"draft", "failed", None}
    if not should_check:
        return errors
    for dep in stage_dependencies(manifest, stage_id):
        dep_status = stages.get(dep, {}).get("status", "draft")
        if dep_status not in STAGE_APPROVED:
            errors.append(f"{stage_id} blocked: dependency {dep} is {dep_status}, needs approved|locked")
    return errors


def validate_gates(root: Path) -> list[str]:
    """CI gate: any progressed stage with unapproved upstream deps fails."""
    manifest = load_stage_manifest(root)
    state = load_state(root)
    stages = state.get("stages", {})
    errors: list[str] = []
    progressed = {"review", "approved", "locked", "rendered", "needs-revision"}
    for stage_id in manifest.get("stages", {}):
        meta = stages.get(stage_id, {})
        status = meta.get("status", "draft")
        if status not in progressed:
            continue
        errors.extend(validate_stage_dependencies(root, stage_id))
    return errors


def check_render_allowed(root: Path, stage_id: str = "segments") -> list[str]:
    """Hard block before render/downstream scripts."""
    return validate_stage_dependencies(root, stage_id, target_status="review")


def resolve_safe_path(root: Path, rel_path: str) -> Path | None:
    candidate = (root / rel_path.replace("\\", "/")).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def impacted_stages(changed_path: str) -> list[str]:
    from dependency_report import impacted

    return impacted(changed_path)


def stale_artifacts_for_change(root: Path, changed_path: str, segment_id: str = "S001") -> list[str]:
    """Return artifact paths that should become stale after a change."""
    rel = changed_path.replace("\\", "/")
    stale: list[str] = []
    if "narration_beats.csv" in rel:
        stale.extend([
            f"audio/stems/voice/beats/{beat}.wav" for beat in _beat_ids_from_csv(root)
        ])
        stale.extend([
            f"segments/{segment_id}/vo_timing.json",
            f"segments/{segment_id}/micro_timing.json",
            f"segments/{segment_id}/index.html",
            f"segments/{segment_id}/render.mp4",
        ])
    elif rel.endswith(".svg") or "/assets/" in rel:
        stale.extend([
            f"segments/{segment_id}/index.html",
            f"segments/{segment_id}/render.mp4",
        ])
    elif "vo_timing.json" in rel or "micro_timing.json" in rel:
        stale.extend([
            f"segments/{segment_id}/index.html",
            f"segments/{segment_id}/render.mp4",
        ])
    return stale


def _beat_ids_from_csv(root: Path) -> list[str]:
    path = root / "script" / "narration_beats.csv"
    if not path.exists():
        return []
    ids: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            beat_id = row.get("beat_id")
            if beat_id:
                ids.append(beat_id)
    return ids


def propagate_stale(
    root: Path,
    changed_path: str,
    *,
    note: str = "",
    segment_id: str = "S001",
) -> dict[str, Any]:
    """Mark downstream artifacts stale and downgrade impacted stages."""
    manifest = load_stage_manifest(root)
    state = load_state(root)
    stages = state.get("stages", {})
    impacted = impacted_stages(changed_path)
    artifact_paths = stale_artifacts_for_change(root, changed_path, segment_id=segment_id)

    registry_entries: list[dict[str, Any]] = []
    for artifact_path in artifact_paths:
        resolved = resolve_safe_path(root, artifact_path)
        if resolved and resolved.exists():
            artifact_id = f"file:{artifact_path}"
            entry = {
                "artifact_id": artifact_id,
                "artifact_type": resolved.suffix.lstrip(".") or "file",
                "path": artifact_path.replace("\\", "/"),
                "stage": _stage_for_path(artifact_path, manifest),
                "segment_id": segment_id,
                "status": "stale",
                "previous_status": registry_index(read_registry_lines(root)).get(artifact_id, {}).get("status", "draft"),
                "reviewer": "system",
                "reviewer_note": note or f"stale due to change in {changed_path}",
                "content_hash": content_hash(resolved),
            }
            registry_entries.append(append_registry(root, entry))

    for stage_id in impacted:
        if stage_id == "manual-review":
            continue
        meta = stages.setdefault(stage_id, {"status": "draft", "artifacts": []})
        if meta.get("status") == "locked":
            continue
        previous = meta.get("status", "draft")
        if previous in STAGE_APPROVED:
            meta["status"] = "needs-revision"
            meta["updated_at"] = utc_now()
            append_history(root, {
                "type": "stage_downgraded",
                "stage": stage_id,
                "from": previous,
                "to": "needs-revision",
                "note": note or f"stale due to {changed_path}",
            })

    save_state(root, state)
    return {"impacted_stages": impacted, "stale_artifacts": registry_entries}


def _stage_for_path(path: str, manifest: dict[str, Any]) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith("segments/"):
        return "segments"
    if normalized.startswith("audio/"):
        return "audio-assets"
    if normalized.startswith("edit/"):
        return "assemble"
    return "assets"


def append_job_log(root: Path, event: dict[str, Any]) -> None:
    event = dict(event)
    event.setdefault("at", utc_now())
    path = project_video_dir(root) / "job_log.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def init_review_files(root: Path, *, force: bool = False) -> None:
    video_dir = project_video_dir(root)
    video_dir.mkdir(parents=True, exist_ok=True)

    manifest_src = skill_root() / "assets" / "templates" / "stage_manifest.json"
    manifest_dst = video_dir / "stage_manifest.json"
    if manifest_src.exists() and (force or not manifest_dst.exists()):
        manifest_dst.write_text(manifest_src.read_text(encoding="utf-8"), encoding="utf-8")

    contract_src = skill_root() / "assets" / "templates" / "agent_contract.md"
    contract_dst = video_dir / "agent_contract.md"
    if contract_src.exists() and (force or not contract_dst.exists()):
        contract_dst.write_text(contract_src.read_text(encoding="utf-8"), encoding="utf-8")

    queue_dst = video_dir / "regen_queue.json"
    if force or not queue_dst.exists():
        template = skill_root() / "assets" / "templates" / "regen_queue.json"
        if template.exists():
            queue_dst.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            write_json(queue_dst, {"version": "1", "items": []})

    for name in ("review_registry.jsonl", "history.jsonl", "job_log.jsonl"):
        path = video_dir / name
        if force or not path.exists():
            path.write_text("", encoding="utf-8")
