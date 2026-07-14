#!/usr/bin/env python3
"""Shared review registry, stale propagation, and lite stage helpers."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE_APPROVED = {"approved", "locked"}
ARTIFACT_STATUSES = {"draft", "review", "approved", "rejected", "stale", "locked"}
REGEN_STATUSES = {"pending", "in_progress", "completed", "failed"}

LITE_STAGE_MANIFEST: dict[str, Any] = {
    "version": "lite",
    "stages": {
        "script": {
            "label": "Script",
            "depends_on": [],
            "required_artifacts": ["outputs/script.md"],
            "optional_artifacts": ["research/factcheck_report.md", "research/claim_ledger.csv"],
        },
        "director-plan": {
            "label": "Beat Plan",
            "depends_on": ["script"],
            "required_artifacts": [
                "outputs/beat_plan.json",
                "outputs/segment_spec.json",
                "outputs/audio_cue_sheet.json",
            ],
            "optional_artifacts": [],
        },
        "voice": {
            "label": "Voice",
            "depends_on": ["director-plan"],
            "required_artifacts": ["segments/{segment}/vo_timing.json"],
            "optional_artifacts": [
                "audio/stems/voice/voiceover_full.wav",
                "segments/{segment}/micro_timing.json",
            ],
        },
        "review": {
            "label": "Review",
            "depends_on": ["director-plan"],
            "required_artifacts": [
                "outputs/review/metrics.json",
                "outputs/review/failed_checks.md",
            ],
            "optional_artifacts": [
                "outputs/review/preview.mp4",
                "outputs/review/contact_sheet.jpg",
                "outputs/review/review-studio/index.html",
            ],
        },
    },
}

IMPACT_MAP: dict[str, list[str]] = {
    "outputs/script.md": ["script", "director-plan"],
    "outputs/beat_plan.json": ["director-plan", "voice", "review"],
    "outputs/segment_spec.json": ["director-plan", "review"],
    "outputs/audio_cue_sheet.json": ["director-plan", "review"],
    "outputs/review/preview.mp4": ["review"],
    "outputs/review/metrics.json": ["review"],
    "segments/": ["voice", "review"],
    "audio/stems/voice/": ["voice", "review"],
}


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
    return LITE_STAGE_MANIFEST


def stage_dependencies(manifest: dict[str, Any], stage_id: str) -> list[str]:
    stage = manifest.get("stages", {}).get(stage_id, {})
    deps = stage.get("depends_on", [])
    return deps if isinstance(deps, list) else []


def default_segment(root: Path) -> str:
    from beat_store import default_segment as store_default_segment

    return store_default_segment(root)


def advancing_status(status: str) -> bool:
    return status in {"review", "approved", "locked", "rendered", "needs-revision"}


def validate_stage_complete(
    root: Path,
    stage_id: str,
    *,
    segment: str | None = None,
    run_scripts: bool = False,
) -> list[str]:
    del run_scripts
    manifest = load_stage_manifest(root)
    meta = manifest.get("stages", {}).get(stage_id, {})
    seg = segment or default_segment(root)
    errors: list[str] = []
    for pattern in meta.get("required_artifacts", []):
        rel = pattern.replace("{segment}", seg)
        path = root / rel.replace("\\", "/")
        if not path.exists():
            errors.append(f"missing required artifact: {rel}")
    return errors


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
        if line:
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
    return load_json(path) if path.exists() else {"version": "1", "items": []}


def save_regen_queue(root: Path, queue: dict[str, Any]) -> None:
    write_json(project_video_dir(root) / "regen_queue.json", queue)


def validate_stage_dependencies(
    root: Path,
    stage_id: str,
    *,
    target_status: str | None = None,
) -> list[str]:
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


def check_render_allowed(root: Path, stage_id: str = "review") -> list[str]:
    return validate_stage_dependencies(root, stage_id, target_status="review")


def resolve_safe_path(root: Path, rel_path: str) -> Path | None:
    candidate = (root / rel_path.replace("\\", "/")).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def impacted_stages(changed_path: str) -> list[str]:
    rel = changed_path.replace("\\", "/")
    found: list[str] = []
    for prefix, stages in IMPACT_MAP.items():
        if rel == prefix or rel.startswith(prefix):
            for stage in stages:
                if stage not in found:
                    found.append(stage)
    if not found and rel.startswith("outputs/"):
        found.append("review")
    return found or ["review"]


def stale_artifacts_for_change(root: Path, changed_path: str, segment_id: str = "S001") -> list[str]:
    rel = changed_path.replace("\\", "/")
    stale: list[str] = []
    if "beat_plan.json" in rel:
        from beat_store import load_beat_plan

        for beat in load_beat_plan(root).get("beats", []):
            if isinstance(beat, dict) and beat.get("beat_id"):
                stale.append(f"audio/stems/voice/beats/{beat['beat_id']}.wav")
        stale.extend([
            f"segments/{segment_id}/vo_timing.json",
            f"segments/{segment_id}/micro_timing.json",
            "outputs/review/preview.mp4",
            "outputs/review/metrics.json",
        ])
    elif rel.endswith(".svg") or "/assets/" in rel:
        stale.extend([
            f"segments/{segment_id}/index.html",
            f"segments/{segment_id}/render.mp4",
            "outputs/review/preview.mp4",
        ])
    elif "vo_timing.json" in rel or "micro_timing.json" in rel:
        stale.extend([
            f"segments/{segment_id}/index.html",
            f"segments/{segment_id}/render.mp4",
            "outputs/review/preview.mp4",
        ])
    elif rel.startswith("outputs/review/"):
        stale.append("outputs/review/metrics.json")
    return stale


def propagate_stale(
    root: Path,
    changed_path: str,
    *,
    note: str = "",
    segment_id: str = "S001",
) -> list[dict[str, Any]]:
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
    return registry_entries


def _stage_for_path(path: str, manifest: dict[str, Any]) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith("outputs/review/"):
        return "review"
    if normalized.startswith("outputs/"):
        return "director-plan"
    if normalized.startswith("segments/"):
        return "voice"
    if normalized.startswith("audio/"):
        return "voice"
    return "director-plan"


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
    manifest_dst = video_dir / "stage_manifest.json"
    if force or not manifest_dst.exists():
        write_json(manifest_dst, LITE_STAGE_MANIFEST)
    queue_dst = video_dir / "regen_queue.json"
    if force or not queue_dst.exists():
        write_json(queue_dst, {"version": "1", "items": []})
    for name in ("review_registry.jsonl", "history.jsonl", "job_log.jsonl"):
        path = video_dir / name
        if force or not path.exists():
            path.write_text("", encoding="utf-8")
