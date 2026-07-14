#!/usr/bin/env python3
"""Review Studio API — local web console for video-producer human gates."""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from beat_store import (  # noqa: E402
    default_segment as store_default_segment,
    director_beats as store_director_beats,
    ensure_micro_timing,
    list_beats as store_list_beats,
    patch_beat as store_patch_beat,
    sync_script_from_plan,
)
from review_core import (  # noqa: E402
    advancing_status,
    append_history,
    append_job_log,
    append_registry,
    check_render_allowed,
    content_hash,
    default_segment,
    load_regen_queue,
    load_stage_manifest,
    load_state,
    propagate_stale,
    read_registry_lines,
    registry_index,
    resolve_safe_path,
    save_regen_queue,
    save_state,
    utc_now,
    validate_stage_complete,
    validate_stage_dependencies,
)
from jobs import JobRunner  # noqa: E402
from beat_store import is_video_project  # noqa: E402
from workspace import workspace_mgr  # noqa: E402
from artifacts import (  # noqa: E402
    find_voiceover_path,
    list_stage_artifacts,
    read_artifact,
    resolve_asset_file,
    write_artifact,
)
from timing import (  # noqa: E402
    audio_summary,
    delete_beat_timing,
    patch_beat_timing,
    patch_micro_event,
    patch_timeline_settings,
    rebuild_timeline_vo,
    resolve_timeline_media,
    wav_duration_sec,
    build_timeline_model,
)
import preview_manager as preview_mgr  # noqa: E402
import tts as tts_api  # noqa: E402

SKILL_ROOT = ROOT
WEB_ROOT = Path(__file__).resolve().parents[1] / "web"


def _root() -> Path:
    try:
        return workspace_mgr.require_project()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

app = FastAPI(title="Video Producer Review Studio", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

event_clients: set[WebSocket] = set()
job_runner = JobRunner()


async def broadcast_event(payload: dict[str, Any]) -> None:
    dead: list[WebSocket] = []
    for ws in list(event_clients):
        try:
            await ws.send_json(payload)
        except Exception:  # noqa: BLE001
            dead.append(ws)
    for ws in dead:
        event_clients.discard(ws)


def sync_broadcast(payload: dict[str, Any]) -> None:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(broadcast_event(payload))
    except RuntimeError:
        pass


job_runner._on_event = sync_broadcast  # type: ignore[method-assign]


class StageStatusBody(BaseModel):
    status: str
    note: str = ""


class AssetReviewBody(BaseModel):
    status: str
    note: str = ""


class BeatPatchBody(BaseModel):
    narration: str | None = None
    semantic_action: str | None = None


class BeatNarrationItem(BaseModel):
    beat_id: str
    narration: str


class BeatNarrationsSyncBody(BaseModel):
    beats: list[BeatNarrationItem] = Field(default_factory=list)


class RegenQueueBody(BaseModel):
    target_artifact_id: str
    action: str = "custom"
    reason: str = ""
    context: dict[str, Any] = Field(default_factory=dict)
    commands_suggested: list[str] = Field(default_factory=list)
    assigned_to: str = "cursor-agent"
    priority: int = 1


class RegenPatchBody(BaseModel):
    status: str
    note: str = ""


class JobRunBody(BaseModel):
    script: str
    args: list[str] = Field(default_factory=list)
    cwd: str | None = None


class WorkspaceRootBody(BaseModel):
    path: str
    scan_depth: int | None = None


class ProjectSwitchBody(BaseModel):
    path: str


class RevealPathBody(BaseModel):
    path: str


class ArtifactWriteBody(BaseModel):
    content: str
    note: str = ""


class TimingBeatPatchBody(BaseModel):
    duration_sec: float | None = None
    locked: bool | None = None
    playback_rate: float | None = Field(default=None, ge=0.25, le=2.0)
    disabled: bool | None = None


class TimelineSettingsPatchBody(BaseModel):
    master_playback_rate: float | None = Field(default=None, ge=0.25, le=2.0)


class MicroEventPatchBody(BaseModel):
    t: float


class VoiceoverWriteBody(BaseModel):
    content: str
    note: str = ""


class TtsConfigPatchBody(BaseModel):
    base_url: str | None = None
    webui_url: str | None = None
    emotion_control_method: str | None = None
    voice_reference: dict[str, Any] | None = None
    defaults: dict[str, Any] | None = None
    segment_emotion_vectors: dict[str, Any] | None = None


class RefSelectBody(BaseModel):
    path: str


def _default_segment() -> str:
    segments_dir = _root() / "segments"
    if segments_dir.exists():
        candidates = sorted(p.name for p in segments_dir.iterdir() if p.is_dir())
        if candidates:
            return candidates[0]
    return store_default_segment(_root())


def _list_segments() -> list[str]:
    segments_dir = _root() / "segments"
    if not segments_dir.exists():
        return [_default_segment()]
    ids = sorted(p.name for p in segments_dir.iterdir() if p.is_dir())
    return ids or [_default_segment()]


def _read_beats(segment: str) -> list[dict[str, Any]]:
    root = _root()
    rows = store_list_beats(root, segment)
    registry = registry_index(read_registry_lines(root))
    for merged in rows:
        beat_id = merged.get("beat_id", "")
        wav_rel = merged.get("vo_wav")
        if wav_rel:
            wav = root / wav_rel
            wav_dur = wav_duration_sec(wav)
            if wav_dur is not None:
                merged["wav_duration_sec"] = wav_dur
                vo = merged.get("vo") or {}
                vo_src = float(vo.get("source_duration_sec") or 0)
                if not vo_src or abs(vo_src - wav_dur) > 0.05:
                    merged["source_duration_sec"] = wav_dur
                    merged["vo"] = {**vo, "source_duration_sec": wav_dur}
        reg = registry.get(f"beat:{beat_id}", {})
        merged["review_status"] = reg.get("status", "review")
    return rows


def _create_job(script: str, args: list[str], cwd: Path, *, label: str = "") -> dict[str, Any]:
    job = job_runner.create(script, args, cwd, label=label)
    try:
        append_job_log(_root(), {
            "type": "job_started",
            "job_id": job.id,
            "label": label,
            "script": script,
            "args": args,
        })
    except Exception:  # noqa: BLE001
        pass
    return job_runner.to_dict(job)


TTS_JOB_PRESETS = frozenset({
    "indextts_segment",
    "indextts_beats",
    "indextts_beats_align",
    "audio_chain_tts",
})


def _tts_base_url_args() -> list[str]:
    try:
        cfg = tts_api.load_config(_root())
        base = str(cfg.get("base_url", "")).strip()
        if base.startswith("http"):
            if not base.endswith("/"):
                base = base.rstrip("/") + "/"
            return ["--base-url", base]
    except Exception:  # noqa: BLE001
        pass
    return []


def _job_presets(
    seg: str,
    beats: list[str] | None = None,
    *,
    force_tts: bool = False,
) -> dict[str, tuple[str, list[str], Path, str]]:
    root = _root()
    beat_args = ["--beats", *(beats or [])] if beats else []
    tts_url = _tts_base_url_args()
    tts_force = ["--force"] if force_tts else []
    chain_force = ["--force-tts"] if force_tts else []
    presets: dict[str, tuple[str, list[str], Path, str]] = {
        "segment_timing_lint": (
            sys.executable,
            [
                str(SCRIPTS / "segment_timing_lint.py"),
                str(root),
                seg,
                *([] if preview_mgr.composition_ready(root, seg) else ["--audio-only"]),
            ],
            root,
            "Segment timing lint",
        ),
        "measure_vo": (
            sys.executable,
            [str(SCRIPTS / "measure_segment_vo.py"), str(root), seg],
            root,
            "Measure VO durations",
        ),
        "build_composition": (
            sys.executable,
            [str(preview_mgr.resolve_composition_builder(root, seg) or root / "scripts" / f"build_{seg.lower()}_composition.py")],
            root,
            "Build composition HTML",
        ),
        "indextts_segment": (
            sys.executable,
            [str(SCRIPTS / "indextts2_generate.py"), str(root), "--segment", seg, "--concat", *tts_force, *tts_url],
            root,
            "IndexTTS2 full segment",
        ),
        "indextts_beats": (
            sys.executable,
            [str(SCRIPTS / "indextts2_generate.py"), str(root), "--segment", seg, *beat_args, "--concat", "--force", *tts_url],
            root,
            "IndexTTS2 selected beats",
        ),
        "indextts_beats_align": (
            sys.executable,
            [str(SCRIPTS / "audio_chain.py"), str(root), seg, *beat_args, "--force-tts", *tts_url],
            root,
            "IndexTTS2 beats + align",
        ),
        "audio_chain": (
            sys.executable,
            [str(SCRIPTS / "audio_chain.py"), str(root), seg, "--skip-tts"],
            root,
            "Audio chain (measure→micro→lint)",
        ),
        "audio_chain_tts": (
            sys.executable,
            [str(SCRIPTS / "audio_chain.py"), str(root), seg, *chain_force, *tts_url],
            root,
            "Audio chain (TTS→measure→micro→lint)",
        ),
        "audio_chain_build": (
            sys.executable,
            [str(SCRIPTS / "audio_chain.py"), str(root), seg, "--skip-tts", "--build"],
            root,
            "Audio chain + build composition",
        ),
        "render_draft": (
            "npx",
            ["hyperframes", "render", "--quality", "draft", "--output", "render.mp4", "--fps", "30"],
            root / "segments" / seg,
            "HyperFrames draft render",
        ),
    }
    return presets


def _stage_gate(stage_id: str, status: str, note: str) -> dict[str, Any]:
    dep_errors = validate_stage_dependencies(_root(), stage_id, target_status=status)
    if dep_errors and advancing_status(status):
        raise HTTPException(status_code=409, detail=dep_errors)
    if advancing_status(status):
        seg = default_segment(_root())
        stage_errors = validate_stage_complete(_root(), stage_id, segment=seg, run_scripts=True)
        if stage_errors:
            raise HTTPException(status_code=409, detail=stage_errors)
    state = load_state(_root())
    stages = state.setdefault("stages", {})
    stage = stages.setdefault(stage_id, {"status": "draft", "artifacts": []})
    previous = stage.get("status", "draft")
    if previous == "locked" and status != "locked":
        raise HTTPException(status_code=409, detail=f"stage {stage_id} is locked")
    stage["status"] = status
    stage["updated_at"] = utc_now()
    state["current_stage"] = stage_id
    save_state(_root(), state)
    append_history(_root(), {
        "type": "stage_gate",
        "stage": stage_id,
        "from": previous,
        "to": status,
        "note": note,
    })
    sync_broadcast({"type": "state_updated", "stage": stage_id, "status": status})
    return {"stage": stage_id, "from": previous, "to": status}


def _render_blocked_reason() -> str | None:
    errors = check_render_allowed(_root(), "segments")
    if errors:
        return errors[0]
    registry = registry_index(read_registry_lines(_root()))
    for row in registry.values():
        if row.get("status") in {"rejected", "stale"} and row.get("path", "").endswith((".svg", ".html", ".mp4")):
            return f"blocked by artifact {row.get('artifact_id')} ({row.get('status')})"
    return None


def _lite_project_video(root: Path) -> dict[str, Any]:
    outputs = root / "outputs"
    spec_path = outputs / "segment_spec.json"
    beat_path = outputs / "beat_plan.json"
    video: dict[str, Any] = {
        "title": root.name,
        "slug": root.name,
        "workflow": "director-lite",
        "outputs_dir": "outputs",
    }
    if spec_path.exists():
        try:
            spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
            video.update({
                "title": spec.get("title") or video["title"],
                "duration_sec": spec.get("duration") or 0,
                "style_keywords": [spec.get("style")] if spec.get("style") else [],
                "segment_id": spec.get("segment_id") or "S001",
            })
        except Exception:  # noqa: BLE001
            pass
    elif beat_path.exists():
        try:
            beats = json.loads(beat_path.read_text(encoding="utf-8-sig"))
            video.update({
                "duration_sec": beats.get("duration") or 0,
                "style_keywords": [beats.get("style")] if beats.get("style") else [],
            })
        except Exception:  # noqa: BLE001
            pass
    return video


def _lite_project_state(root: Path) -> dict[str, Any]:
    outputs = root / "outputs"
    has_beats = (outputs / "beat_plan.json").exists()
    has_spec = (outputs / "segment_spec.json").exists()
    has_bundle = (outputs / "review" / "review-studio" / "index.html").exists()
    if has_beats and has_spec:
        current_stage = "first-slice-review" if has_bundle else "first-slice-plan"
    else:
        current_stage = "script-only"
    return {
        "version": "director-lite",
        "current_stage": current_stage,
        "stages": {
            "script": {
                "status": "review" if (outputs / "script.md").exists() else "draft",
                "artifacts": ["outputs/script.md"],
            },
            "director-plan": {
                "status": "review" if has_beats and has_spec else "draft",
                "artifacts": ["outputs/beat_plan.json", "outputs/segment_spec.json"],
            },
            "voice-and-sound": {
                "status": "review" if (outputs / "audio_cue_sheet.json").exists() else "draft",
                "artifacts": ["outputs/audio_cue_sheet.json"],
            },
            "qc": {
                "status": "review" if (outputs / "review" / "metrics.json").exists() else "draft",
                "artifacts": ["outputs/review/metrics.json", "outputs/review/failed_checks.md"],
            },
        },
    }


@app.get("/api/workspace")
def get_workspace() -> dict[str, Any]:
    return workspace_mgr.snapshot()


@app.put("/api/workspace/root")
def put_workspace_root(body: WorkspaceRootBody) -> dict[str, Any]:
    try:
        snapshot = workspace_mgr.set_workspace(Path(body.path), scan_depth=body.scan_depth)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    sync_broadcast({"type": "workspace_updated", "workspace_root": snapshot.get("workspace_root")})
    if snapshot.get("current_project"):
        sync_broadcast({"type": "project_switched", "project": snapshot["current_project"]})
    return snapshot


@app.post("/api/workspace/scan")
def post_workspace_scan() -> dict[str, Any]:
    try:
        snapshot = workspace_mgr.scan()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    sync_broadcast({"type": "workspace_updated"})
    return snapshot


@app.post("/api/dialog/pick-directory")
def post_pick_directory(title: str = "选择文件夹") -> dict[str, Any]:
    """Open native folder picker (local server only)."""
    from pick_directory import pick_directory

    selected = pick_directory(title=title)
    if not selected:
        return {"cancelled": True, "path": None}
    return {"cancelled": False, "path": str(Path(selected).resolve())}


@app.post("/api/dialog/reveal-path")
def post_reveal_path(body: RevealPathBody) -> dict[str, Any]:
    """Open the system file manager at an asset path (local server only)."""
    from reveal_path import reveal_in_filesystem

    root = _root()
    rel = body.path.strip().replace("\\", "/").lstrip("/")
    if not rel:
        raise HTTPException(status_code=400, detail="path is required")

    resolved = resolve_asset_file(
        root,
        rel,
        asset_id=Path(rel).stem,
        segment_id=_segment_from_media_path(rel),
    )
    if resolved is None:
        resolved = resolve_safe_path(root, rel)
    if resolved is None:
        raise HTTPException(status_code=400, detail={"message": "path outside project", "path": rel})

    try:
        reveal_in_filesystem(resolved)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={"message": "path not found on disk", "path": rel},
        ) from exc

    if resolved.is_file():
        opened = str(resolved.parent)
        selected = str(resolved)
    elif resolved.is_dir():
        opened = str(resolved)
        selected = None
    else:
        opened = str(resolved.parent)
        selected = None
    return {"opened": opened, "selected": selected, "relative": rel}


@app.post("/api/project/switch")
def post_project_switch(body: ProjectSwitchBody) -> dict[str, Any]:
    try:
        result = workspace_mgr.switch_project(Path(body.path))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    sync_broadcast({"type": "project_switched", "project": result["current_project"]})
    return result


@app.get("/api/project")
def get_project() -> dict[str, Any]:
    snapshot = workspace_mgr.snapshot()
    if workspace_mgr.current_project is None:
        return {
            "root": None,
            "video": {},
            "state": {},
            "current_stage": None,
            "render_blocked": None,
            "workspace": snapshot,
            "needs_project": True,
        }
    root = _root()
    video_path = root / ".video" / "video.json"
    state = load_state(root)
    if state:
        video = json.loads(video_path.read_text(encoding="utf-8-sig")) if video_path.exists() else {}
    else:
        state = _lite_project_state(root)
        video = _lite_project_video(root)
    return {
        "root": str(root),
        "video": video,
        "state": state,
        "current_stage": state.get("current_stage"),
        "render_blocked": _render_blocked_reason(),
        "workspace": snapshot,
        "needs_project": False,
    }


@app.get("/api/stages")
def get_stages() -> dict[str, Any]:
    manifest = load_stage_manifest(_root())
    state = load_state(_root())
    stages = state.get("stages", {})
    items = []
    for stage_id, meta in manifest.get("stages", {}).items():
        current = stages.get(stage_id, {})
        deps = meta.get("depends_on", [])
        blocked = []
        for dep in deps:
            dep_status = stages.get(dep, {}).get("status", "draft")
            if dep_status not in {"approved", "locked"}:
                blocked.append({"stage": dep, "status": dep_status})
        items.append({
            "id": stage_id,
            "label": meta.get("label", stage_id),
            "depends_on": deps,
            "downstream": meta.get("downstream", []),
            "status": current.get("status", "draft"),
            "artifacts": current.get("artifacts", []),
            "blocked_by": blocked,
            "required_count": len(meta.get("required_artifacts", [])),
            "required_ready": sum(
                1 for a in list_stage_artifacts(_root(), stage_id, _default_segment()) if a["exists"] and a["required"]
            ),
        })
    return {"stages": items}


@app.post("/api/stages/{stage_id}/status")
def post_stage_status(stage_id: str, body: StageStatusBody) -> dict[str, Any]:
    return _stage_gate(stage_id, body.status, body.note)


@app.get("/api/beats")
def get_beats(segment: str | None = None) -> dict[str, Any]:
    seg = segment or _default_segment()
    return {"segment_id": seg, "beats": _read_beats(seg)}


@app.get("/api/beats/{beat_id}")
def get_beat(beat_id: str, segment: str | None = None) -> dict[str, Any]:
    seg = segment or _default_segment()
    for beat in _read_beats(seg):
        if beat.get("beat_id") == beat_id:
            micro_path = _root() / "segments" / seg / "micro_timing.json"
            micro_events: list[dict[str, Any]] = []
            if micro_path.exists():
                micro_raw = json.loads(micro_path.read_text(encoding="utf-8-sig"))
                micro_list = micro_raw if isinstance(micro_raw, list) else micro_raw.get("events", [])
                for event in micro_list:
                    if not isinstance(event, dict):
                        continue
                    parent = str(event.get("parent") or event.get("beat_id") or "")
                    if parent == beat_id:
                        micro_events.append(event)
            beat["micro_events"] = micro_events
            wav = _root() / "audio" / "stems" / "voice" / "beats" / f"{beat_id}.wav"
            beat["vo_wav"] = wav.relative_to(_root()).as_posix() if wav.exists() else None
            return beat
    raise HTTPException(status_code=404, detail=f"beat not found: {beat_id}")


def _apply_beat_plan_sync(root: Path, seg: str, beat_ids: set[str]) -> dict[str, Any]:
    script_path = sync_script_from_plan(root)
    stale: list[str] = []
    stale.extend(propagate_stale(root, "outputs/beat_plan.json", note=f"{len(beat_ids)} beats edited", segment_id=seg))
    for beat_id in beat_ids:
        stale.extend(propagate_stale(
            root,
            f"audio/stems/voice/beats/{beat_id}.wav",
            note=f"beat {beat_id} text changed",
            segment_id=seg,
        ))
    if script_path:
        stale.extend(propagate_stale(root, "outputs/script.md", note="script synced from beat_plan", segment_id=seg))
    stale.extend(propagate_stale(root, f"segments/{seg}/vo_timing.json", note="beat plan edited", segment_id=seg))
    stale.extend(propagate_stale(root, "outputs/review/preview.mp4", note="beat plan edited", segment_id=seg))
    stale.extend(propagate_stale(root, "outputs/review/metrics.json", note="beat plan edited", segment_id=seg))
    return {"script_path": script_path, "beat_ids": sorted(beat_ids), "stale": stale}


@app.patch("/api/beats/{beat_id}")
def patch_beat(beat_id: str, body: BeatPatchBody, segment: str | None = None) -> dict[str, Any]:
    seg = segment or _default_segment()
    root = _root()
    existing = next((b for b in _read_beats(seg) if b.get("beat_id") == beat_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail=f"beat not found: {beat_id}")
    narration_changed = False
    if body.narration is not None and (existing.get("narration") or "") != body.narration:
        narration_changed = True
    updated = store_patch_beat(
        root,
        beat_id,
        voice_text=body.narration,
        intent=body.semantic_action,
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"beat not found: {beat_id}")
    sync: dict[str, Any] = {}
    if narration_changed:
        sync = _apply_beat_plan_sync(root, seg, {beat_id})
    append_registry(root, {
        "artifact_id": f"beat:{beat_id}",
        "artifact_type": "beat",
        "path": "outputs/beat_plan.json",
        "stage": "director-plan",
        "segment_id": seg,
        "beat_ids": [beat_id],
        "status": "review",
        "previous_status": "approved",
        "reviewer": "human",
        "reviewer_note": "voice_text edited via Review Studio",
    })
    sync_broadcast({"type": "registry_updated", "beat_id": beat_id})
    return {"beat_id": beat_id, "stale": sync.get("stale", []), "sync": sync}


@app.post("/api/beats/sync-narrations")
def post_beats_sync_narrations(body: BeatNarrationsSyncBody, segment: str | None = None) -> dict[str, Any]:
    """Persist UI narration edits to beat_plan.json before bulk TTS."""
    seg = segment or _default_segment()
    root = _root()
    if not body.beats:
        return {"updated": 0, "sync": {}}

    updates = {item.beat_id: item.narration for item in body.beats}
    changed_ids: set[str] = set()
    for beat in _read_beats(seg):
        beat_id = beat.get("beat_id", "")
        if beat_id in updates and (beat.get("narration") or "") != updates[beat_id]:
            store_patch_beat(root, beat_id, voice_text=updates[beat_id])
            changed_ids.add(beat_id)
    if not changed_ids:
        return {"updated": 0, "sync": {}}

    sync = _apply_beat_plan_sync(root, seg, changed_ids)
    sync_broadcast({"type": "registry_updated", "beat_ids": sorted(changed_ids)})
    return {"updated": len(changed_ids), "beat_ids": sorted(changed_ids), "stale": sync.get("stale", []), "sync": sync}


def _segment_from_media_path(file_path: str) -> str:
    parts = file_path.replace("\\", "/").split("/")
    if len(parts) >= 2 and parts[0] == "segments":
        return parts[1]
    return _default_segment()


def _enrich_asset_row(root: Path, row: dict[str, str]) -> dict[str, Any]:
    asset_id = row.get("asset_id", "")
    segment_id = row.get("segment_id") or _default_segment()
    path_or_url = row.get("path_or_url") or ""
    resolved = resolve_asset_file(
        root,
        path_or_url,
        asset_id=asset_id,
        segment_id=segment_id,
    )
    item: dict[str, Any] = dict(row)
    item["exists"] = resolved is not None
    item["size_bytes"] = resolved.stat().st_size if resolved else 0
    if resolved:
        item["media_path"] = resolved.relative_to(root).as_posix()
    elif path_or_url and not path_or_url.startswith(("http://", "https://", "//")):
        item["media_path"] = path_or_url.replace("\\", "/")
    else:
        item["media_path"] = None
    return item


@app.get("/api/assets")
def get_assets(segment: str | None = None, status: str | None = None) -> dict[str, Any]:
    root = _root()
    path = root / "assets" / "asset_manifest.csv"
    if not path.exists():
        return {"assets": []}
    registry = registry_index(read_registry_lines(root))
    assets: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if segment and row.get("segment_id") not in {segment, segment.replace("S001", "S01")}:
                continue
            asset_id = row.get("asset_id", "")
            reg = registry.get(f"asset:{asset_id}", {})
            review_status = row.get("review_status") or reg.get("status", "review")
            if status and review_status != status:
                continue
            item = _enrich_asset_row(root, dict(row))
            item["review_status"] = review_status
            item["registry"] = reg
            assets.append(item)
    return {"assets": assets}


@app.post("/api/assets/{asset_id}/review")
def post_asset_review(asset_id: str, body: AssetReviewBody) -> dict[str, Any]:
    manifest_path = _root() / "assets" / "asset_manifest.csv"
    asset_row: dict[str, str] | None = None
    if manifest_path.exists():
        with manifest_path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                if row.get("asset_id") == asset_id:
                    asset_row = dict(row)
                    break
    rel_path = (asset_row or {}).get("path_or_url") or f"segments/{_default_segment()}/assets/{asset_id}.svg"
    resolved = resolve_safe_path(_root(), rel_path)
    entry = append_registry(_root(), {
        "artifact_id": f"asset:{asset_id}",
        "artifact_type": (asset_row or {}).get("type", "svg"),
        "path": rel_path,
        "stage": "assets",
        "segment_id": (asset_row or {}).get("segment_id") or _default_segment(),
        "status": body.status,
        "previous_status": registry_index(read_registry_lines(_root())).get(f"asset:{asset_id}", {}).get("status", "review"),
        "reviewer": "human",
        "reviewer_note": body.note,
        "content_hash": content_hash(resolved) if resolved else "",
        "invalidates": [
            f"segments/{_default_segment()}/index.html",
            f"segments/{_default_segment()}/render.mp4",
        ],
    })
    if body.status == "rejected":
        segment_id = (asset_row or {}).get("segment_id") or _default_segment()
        propagate_stale(_root(), rel_path, note=body.note, segment_id=segment_id)
        for invalidate_path in [
            f"segments/{segment_id}/index.html",
            f"segments/{segment_id}/render.mp4",
        ]:
            resolved = resolve_safe_path(_root(), invalidate_path)
            if resolved and resolved.exists():
                append_registry(_root(), {
                    "artifact_id": f"file:{invalidate_path}",
                    "artifact_type": resolved.suffix.lstrip(".") or "file",
                    "path": invalidate_path,
                    "stage": "segments",
                    "segment_id": segment_id,
                    "status": "stale",
                    "previous_status": registry_index(read_registry_lines(_root())).get(f"file:{invalidate_path}", {}).get("status", "approved"),
                    "reviewer": "system",
                    "reviewer_note": f"invalidated by reject {asset_id}",
                    "content_hash": content_hash(resolved),
                })
    if manifest_path.exists() and asset_row:
        rows: list[dict[str, str]] = []
        fieldnames: list[str] = []
        with manifest_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            fieldnames = list(reader.fieldnames or [])
            if "review_status" not in fieldnames:
                fieldnames.append("review_status")
            for row in reader:
                if row.get("asset_id") == asset_id:
                    row["review_status"] = body.status
                rows.append(dict(row))
        with manifest_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    sync_broadcast({"type": "registry_updated", "artifact_id": f"asset:{asset_id}", "status": body.status})
    return {"entry": entry}


@app.get("/api/registry")
def get_registry() -> dict[str, Any]:
    rows = list(registry_index(read_registry_lines(_root())).values())
    return {"artifacts": rows}


@app.get("/api/regen-queue")
def get_regen_queue_api() -> dict[str, Any]:
    return load_regen_queue(_root())


@app.post("/api/regen-queue")
def post_regen_queue(body: RegenQueueBody) -> dict[str, Any]:
    queue = load_regen_queue(_root())
    item = {
        "id": f"rq-{utc_now()[:10].replace('-', '')}-{len(queue.get('items', [])) + 1:03d}",
        "status": "pending",
        "priority": body.priority,
        "target_artifact_id": body.target_artifact_id,
        "action": body.action,
        "assigned_to": body.assigned_to,
        "reason": body.reason,
        "context": body.context,
        "commands_suggested": body.commands_suggested,
        "created_at": utc_now(),
        "completed_at": None,
    }
    queue.setdefault("items", []).append(item)
    save_regen_queue(_root(), queue)
    sync_broadcast({"type": "regen_queue_updated", "item_id": item["id"]})
    return {"item": item}


@app.patch("/api/regen-queue/{item_id}")
def patch_regen_queue(item_id: str, body: RegenPatchBody) -> dict[str, Any]:
    queue = load_regen_queue(_root())
    for item in queue.get("items", []):
        if item.get("id") == item_id:
            item["status"] = body.status
            if body.status in {"completed", "failed"}:
                item["completed_at"] = utc_now()
            if body.note:
                item["note"] = body.note
            save_regen_queue(_root(), queue)
            return {"item": item}
    raise HTTPException(status_code=404, detail="queue item not found")


@app.get("/api/segments")
def get_segments_list() -> dict[str, Any]:
    return {"segments": _list_segments(), "default": _default_segment()}


@app.get("/api/publish")
def get_publish() -> dict[str, Any]:
    path = _root() / "exports" / "publish_pack.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="publish_pack.md missing")
    return {"path": "exports/publish_pack.md", "content": path.read_text(encoding="utf-8-sig")}


@app.post("/api/jobs/preset/{preset_name}")
def post_job_preset(
    preset_name: str,
    segment: str | None = None,
    beats: str | None = None,
    force_tts: bool = False,
) -> dict[str, Any]:
    seg = segment or _default_segment()
    beat_list = [b.strip() for b in beats.split(",") if b.strip()] if beats else None
    if preset_name in {"indextts_beats", "indextts_beats_align"} and not beat_list:
        raise HTTPException(status_code=400, detail="beats query param required for beat-level TTS presets")
    presets = _job_presets(seg, beat_list, force_tts=force_tts)
    if preset_name not in presets:
        raise HTTPException(status_code=404, detail=f"unknown preset: {preset_name}")
    if preset_name in {"render_draft", "render_hq"}:
        blocked = _render_blocked_reason()
        if blocked:
            raise HTTPException(status_code=409, detail=f"render blocked: {blocked}")
    script, args, cwd, label = presets[preset_name]
    if preset_name == "build_composition":
        builder = preview_mgr.resolve_composition_builder(_root(), seg)
        if not builder:
            raise HTTPException(
                status_code=404,
                detail=f"composition builder missing for {seg} (expected build_{seg.lower()}_composition.py or build_segment_index.py)",
            )
        args = [str(builder)]
    if preset_name == "render_draft" and not cwd.exists():
        raise HTTPException(status_code=404, detail=f"segment dir missing: {cwd}")
    job = _create_job(script, args, cwd, label=label)
    if preset_name in TTS_JOB_PRESETS:
        tts_api.init_tts_job_progress(_root(), segment=seg, job_id=str(job["id"]), label=label)
    return {"job": job}


@app.get("/api/director/beats")
def get_director_beats(segment: str | None = None) -> dict[str, Any]:
    seg = segment or _default_segment()
    beats = store_director_beats(_root(), seg)
    registry = registry_index(read_registry_lines(_root()))
    for beat in beats:
        reg = registry.get(f"beat:{beat.get('beat_id')}", {})
        beat["review_status"] = reg.get("status", "review")
    return {"segment_id": seg, "beats": beats}


@app.get("/api/timeline")
def get_timeline(segment: str | None = None) -> dict[str, Any]:
    seg = segment or _default_segment()
    root = _root()
    ensure_micro_timing(root, seg)
    vo_path = root / "segments" / seg / "vo_timing.json"
    micro_path = root / "segments" / seg / "micro_timing.json"
    beats = _read_beats(seg)
    vo = json.loads(vo_path.read_text(encoding="utf-8-sig")) if vo_path.exists() else {}
    micro_raw = json.loads(micro_path.read_text(encoding="utf-8-sig")) if micro_path.exists() else []
    micro_events = micro_raw if isinstance(micro_raw, list) else micro_raw.get("events", [])
    total = float(vo.get("total_sec") or 0)
    if not total and beats:
        total = sum(float(b.get("actual_sec") or b.get("planned_sec") or 0) for b in beats)
    video_path = root / ".video" / "video.json"
    ratio = "16:9"
    resolution = ""
    if video_path.exists():
        video_meta = json.loads(video_path.read_text(encoding="utf-8-sig"))
        ratio = video_meta.get("ratio") or ratio
        resolution = video_meta.get("resolution") or ""
    return {
        "segment_id": seg,
        "ratio": ratio,
        "resolution": resolution,
        "total_sec": round(total, 3) if total else None,
        "master_playback_rate": float(vo.get("master_playback_rate") or 1.0),
        "beats": beats,
        "micro_events": micro_events,
        "media": resolve_timeline_media(root, seg),
        "preview": preview_mgr.hyperframes_status(root, seg),
        **build_timeline_model(root, seg, beats, micro_events),
    }


@app.get("/api/preview/hyperframes")
def get_hyperframes_preview(segment: str | None = None) -> dict[str, Any]:
    seg = segment or _default_segment()
    return preview_mgr.hyperframes_status(_root(), seg)


def _composition_missing_detail(root: Path, segment: str, message: str) -> dict[str, str]:
    expected = root / "segments" / segment / "index.html"
    return {
        "message": message,
        "project_root": str(root.resolve()),
        "expected_path": str(expected),
        "segment_dir": str(root / "segments" / segment),
        "hint": "请在 Review Studio 选择视频项目，并在时间轴点击「重建合成」生成 index.html；Studio 需 POST 启动",
    }


@app.get("/api/preview/hyperframes/start")
def get_hyperframes_preview_start_hint(segment: str | None = None) -> dict[str, Any]:
    """Diagnostic GET — composition status before POST start."""
    seg = segment or _default_segment()
    root = _root()
    status = preview_mgr.hyperframes_status(root, seg)
    if not status.get("composition_ready"):
        raise HTTPException(
            status_code=404,
            detail=_composition_missing_detail(root, seg, f"segments/{seg}/index.html missing"),
        )
    return {
        **status,
        "method": "POST",
        "hint": "合成页已就绪；请用 POST 启动 HyperFrames Studio",
    }


@app.post("/api/preview/hyperframes/start")
def post_hyperframes_preview_start(segment: str | None = None, port: int | None = None) -> dict[str, Any]:
    seg = segment or _default_segment()
    root = _root()
    try:
        return preview_mgr.start_hyperframes_studio(root, seg, port=port)
    except preview_mgr.CompositionNotReadyError as exc:
        raise HTTPException(
            status_code=404,
            detail=_composition_missing_detail(root, seg, str(exc)),
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/preview/hyperframes/stop")
def post_hyperframes_preview_stop(segment: str | None = None) -> dict[str, Any]:
    seg = segment or _default_segment()
    return preview_mgr.stop_hyperframes_studio(_root(), seg)


@app.get("/api/preview/composition/{segment}/{file_path:path}")
def get_composition_asset(segment: str, file_path: str) -> FileResponse:
    root = _root()
    seg_dir = root / "segments" / segment
    if not seg_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"segment not found: {segment}")
    rel = file_path or "index.html"
    resolved = resolve_safe_path(seg_dir, rel)
    if not resolved or not resolved.is_file():
        raise HTTPException(status_code=404, detail=f"asset not found: {rel}")
    import mimetypes

    ext = resolved.suffix.lower()
    mime_overrides = {
        ".svg": "image/svg+xml",
        ".webp": "image/webp",
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mov": "video/quicktime",
        ".m4v": "video/x-m4v",
        ".json": "application/json",
        ".html": "text/html; charset=utf-8",
        ".htm": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".woff2": "font/woff2",
    }
    media_type = mime_overrides.get(ext) or mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
    return FileResponse(resolved, media_type=media_type, headers={"Content-Disposition": "inline"})


@app.post("/api/jobs/run")
def post_job_run(body: JobRunBody) -> dict[str, Any]:
    if "render" in body.script.lower() or "hyperframes" in " ".join(body.args).lower():
        blocked = _render_blocked_reason()
        if blocked:
            raise HTTPException(status_code=409, detail=f"render blocked: {blocked}")
    cwd = Path(body.cwd) if body.cwd else _root()
    if not cwd.is_absolute():
        cwd = (_root() / cwd).resolve()
    job = job_runner.create(body.script, body.args, cwd)
    return {"job": job_runner.to_dict(job)}


@app.get("/api/jobs")
def get_jobs(limit: int = 30) -> dict[str, Any]:
    return {"jobs": [job_runner.to_dict(j) for j in job_runner.list_jobs(limit)]}


@app.get("/api/tts/health")
def get_tts_health() -> dict[str, Any]:
    return tts_api.health_check(_root())


@app.get("/api/tts/config")
def get_tts_config() -> dict[str, Any]:
    root = _root()
    path = tts_api.config_path(root)
    if not path.exists():
        raise HTTPException(status_code=404, detail="indextts2_config.json missing")
    return {"path": tts_api.CONFIG_REL, "config": tts_api.load_config(root)}


@app.put("/api/tts/config")
def put_tts_config(body: TtsConfigPatchBody) -> dict[str, Any]:
    root = _root()
    existing = tts_api.load_config(root)
    if not existing and not body.base_url:
        raise HTTPException(status_code=400, detail="base_url required when creating new config")
    patch = body.model_dump(exclude_none=True)
    merged = tts_api.merge_config(existing, patch)
    if not merged.get("base_url"):
        raise HTTPException(status_code=400, detail="base_url is required")
    if not str(merged["base_url"]).startswith("http"):
        raise HTTPException(status_code=400, detail="base_url must start with http")
    if not str(merged["base_url"]).endswith("/"):
        merged["base_url"] = str(merged["base_url"]).rstrip("/") + "/"
    if not merged.get("webui_url"):
        merged["webui_url"] = merged["base_url"]
    tts_api.save_config(root, merged)
    append_history(root, {
        "type": "tts_config_updated",
        "path": tts_api.CONFIG_REL,
        "base_url": merged.get("base_url"),
        "at": utc_now(),
    })
    return {
        "path": tts_api.CONFIG_REL,
        "config": merged,
        "health": tts_api.health_check(root),
    }


@app.get("/api/tts/progress")
def get_tts_progress() -> dict[str, Any]:
    return tts_api.read_progress(_root())


@app.get("/api/audio/refs")
def get_audio_refs() -> dict[str, Any]:
    return tts_api.list_refs(_root())


@app.put("/api/audio/refs/select")
def put_audio_ref_select(body: RefSelectBody) -> dict[str, Any]:
    try:
        result = tts_api.select_ref(_root(), body.path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    append_history(_root(), {
        "type": "tts_ref_selected",
        "path": result["selected_path"],
        "at": utc_now(),
    })
    return result


@app.post("/api/audio/refs/upload")
async def post_audio_ref_upload(
    file: UploadFile = File(...),
    select: bool = True,
) -> dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename required")
    lower = file.filename.lower()
    if not lower.endswith((".wav", ".mp3")):
        raise HTTPException(status_code=400, detail="only .wav and .mp3 files are supported")
    data = await file.read()
    if len(data) < 16:
        raise HTTPException(status_code=400, detail="file too small to be a valid audio file")

    root = _root()
    upload_id = str(uuid.uuid4())
    filename = Path(file.filename).name
    tts_api.write_upload_state(root, upload_id, {
        "status": "queued",
        "message": "已接收，准备处理…",
        "progress": 5,
        "filename": filename,
    })

    def worker() -> None:
        try:
            result = tts_api.save_ref_upload(
                root, filename, data, select=select, upload_id=upload_id,
            )
            tts_api.write_upload_state(root, upload_id, {
                "status": "completed",
                "message": "上传完成",
                "progress": 100,
                "filename": filename,
                "result": result,
            })
            append_history(root, {
                "type": "tts_ref_uploaded",
                "path": result["path"],
                "upload_id": upload_id,
                "at": utc_now(),
            })
        except Exception as exc:  # noqa: BLE001
            tts_api.write_upload_state(root, upload_id, {
                "status": "failed",
                "message": str(exc),
                "progress": 0,
                "filename": filename,
                "error": str(exc),
            })

    threading.Thread(target=worker, daemon=True).start()
    return {"upload_id": upload_id, "status": "queued", "filename": filename}


@app.get("/api/audio/refs/upload/{upload_id}")
def get_audio_ref_upload_status(upload_id: str) -> dict[str, Any]:
    state = tts_api.read_upload_state(_root(), upload_id)
    if not state:
        raise HTTPException(status_code=404, detail="upload not found")
    return state


@app.delete("/api/audio/refs")
def delete_audio_ref(path: str) -> dict[str, Any]:
    try:
        result = tts_api.delete_ref(_root(), path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    append_history(_root(), {
        "type": "tts_ref_deleted",
        "path": result["deleted"],
        "at": utc_now(),
    })
    return result


@app.get("/api/audio/summary")
def get_audio_summary(segment: str | None = None) -> dict[str, Any]:
    seg = segment or _default_segment()
    root = _root()
    summary = audio_summary(root, seg)
    summary["tts"] = tts_api.health_check(root)
    summary["refs"] = tts_api.list_refs(root)
    summary["progress"] = tts_api.read_progress(root)
    return summary


@app.patch("/api/timing/beats/{beat_id}")
def patch_timing_beat(beat_id: str, body: TimingBeatPatchBody, segment: str | None = None) -> dict[str, Any]:
    seg = segment or _default_segment()
    try:
        result = patch_beat_timing(
            _root(), seg, beat_id,
            duration_sec=body.duration_sec,
            locked=body.locked,
            playback_rate=body.playback_rate,
            disabled=body.disabled,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    sync_broadcast({"type": "registry_updated", "beat_id": beat_id})
    return result


@app.delete("/api/timing/beats/{beat_id}")
def delete_timing_beat(beat_id: str, segment: str | None = None) -> dict[str, Any]:
    seg = segment or _default_segment()
    try:
        result = delete_beat_timing(_root(), seg, beat_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    sync_broadcast({"type": "registry_updated", "beat_id": beat_id, "deleted": True})
    return result


@app.patch("/api/timeline/settings")
def patch_timeline_settings_api(body: TimelineSettingsPatchBody, segment: str | None = None) -> dict[str, Any]:
    seg = segment or _default_segment()
    result = patch_timeline_settings(_root(), seg, master_playback_rate=body.master_playback_rate)
    sync_broadcast({"type": "timeline_settings", "segment_id": seg})
    return result


@app.post("/api/timeline/rebuild-vo")
def post_timeline_rebuild_vo(segment: str | None = None) -> dict[str, Any]:
    seg = segment or _default_segment()
    try:
        result = rebuild_timeline_vo(_root(), seg)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except subprocess.CalledProcessError as exc:
        raise HTTPException(status_code=500, detail=f"ffmpeg failed: {exc.stderr.decode(errors='replace')[:400]}") from exc
    sync_broadcast({"type": "timeline_vo_rebuilt", "segment_id": seg})
    return result


@app.patch("/api/timing/micro/{event_id}")
def patch_timing_micro(event_id: str, body: MicroEventPatchBody, segment: str | None = None) -> dict[str, Any]:
    seg = segment or _default_segment()
    try:
        result = patch_micro_event(_root(), seg, event_id, body.t)
    except (KeyError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    sync_broadcast({"type": "registry_updated", "event_id": event_id})
    return result


@app.get("/api/stages/{stage_id}/artifacts")
def get_stage_artifacts(stage_id: str, segment: str | None = None) -> dict[str, Any]:
    seg = segment or _default_segment()
    manifest = load_stage_manifest(_root())
    if stage_id not in manifest.get("stages", {}):
        raise HTTPException(status_code=404, detail=f"unknown stage: {stage_id}")
    return {"stage_id": stage_id, "segment_id": seg, "artifacts": list_stage_artifacts(_root(), stage_id, seg)}


@app.get("/api/artifacts/{file_path:path}")
def get_artifact(file_path: str) -> dict[str, Any]:
    try:
        return read_artifact(_root(), file_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/api/artifacts/{file_path:path}")
def put_artifact(file_path: str, body: ArtifactWriteBody, segment: str | None = None) -> dict[str, Any]:
    seg = segment or _default_segment()
    try:
        result = write_artifact(_root(), file_path, body.content, note=body.note, segment_id=seg)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    sync_broadcast({"type": "registry_updated", "path": file_path})
    return result


@app.get("/api/script/voiceover")
def get_voiceover() -> dict[str, Any]:
    path = find_voiceover_path(_root())
    if not path:
        raise HTTPException(status_code=404, detail="voiceover not found")
    rel = path.relative_to(_root()).as_posix()
    return {"path": rel, "content": path.read_text(encoding="utf-8-sig")}


@app.put("/api/script/voiceover")
def put_voiceover(body: VoiceoverWriteBody) -> dict[str, Any]:
    path = find_voiceover_path(_root()) or (_root() / "script" / "voiceover.md")
    rel = path.relative_to(_root()).as_posix()
    result = write_artifact(_root(), rel, body.content, note=body.note or "voiceover edited")
    sync_broadcast({"type": "registry_updated", "path": rel})
    return result


@app.post("/api/stages/{stage_id}/validate")
def post_stage_validate(stage_id: str, segment: str | None = None) -> dict[str, Any]:
    seg = segment or _default_segment()
    manifest = load_stage_manifest(_root())
    meta = manifest.get("stages", {}).get(stage_id, {})
    scripts = meta.get("validation_scripts", [])
    if not scripts:
        return {"stage_id": stage_id, "skipped": True, "reason": "no validation_scripts"}
    results = []
    for template in scripts:
        parts = template.split()
        script_name = parts[0].replace("{project}", str(_root())).replace("{segment}", seg)
        script_path = SCRIPTS / script_name if not Path(script_name).is_absolute() else Path(script_name)
        args = [str(script_path), str(_root())]
        for part in parts[1:]:
            args.append(part.replace("{project}", str(_root())).replace("{segment}", seg))
        job = _create_job(sys.executable, args, _root(), label=f"validate {stage_id}")
        results.append(job)
    return {"stage_id": stage_id, "jobs": results}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    job = job_runner.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return {"job": job_runner.to_dict(job)}


@app.get("/api/history")
def get_history(limit: int = 100) -> dict[str, Any]:
    path = _root() / ".video" / "history.jsonl"
    if not path.exists():
        return {"events": []}
    lines = [line for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    events = [json.loads(line) for line in lines[-limit:]]
    return {"events": events}


@app.get("/api/dependency")
def get_dependency(changed: str) -> dict[str, Any]:
    from review_core import impacted_stages, stale_artifacts_for_change

    seg = _default_segment()
    report = {
        "changed": changed,
        "impacted_stages": impacted_stages(changed),
        "stale_artifacts": stale_artifacts_for_change(_root(), changed, segment_id=seg),
    }
    return report


@app.get("/api/media/{file_path:path}")
def get_media(file_path: str) -> FileResponse:
    root = _root()
    rel = file_path.replace("\\", "/").lstrip("/")
    resolved = resolve_safe_path(root, rel)
    if not resolved or not resolved.is_file():
        resolved = resolve_asset_file(
            root,
            rel,
            asset_id=Path(rel).stem,
            segment_id=_segment_from_media_path(rel),
        )
    if not resolved or not resolved.is_file():
        raise HTTPException(
            status_code=404,
            detail={
                "message": "file not found",
                "path": rel,
                "project_root": str(root.resolve()),
            },
        )
    import mimetypes

    ext = resolved.suffix.lower()
    mime_overrides = {
        ".svg": "image/svg+xml",
        ".webp": "image/webp",
        ".wav": "audio/wav",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mov": "video/quicktime",
        ".m4v": "video/x-m4v",
        ".json": "application/json",
        ".jsonl": "application/x-ndjson",
        ".md": "text/markdown; charset=utf-8",
        ".csv": "text/csv; charset=utf-8",
        ".html": "text/html; charset=utf-8",
        ".htm": "text/html; charset=utf-8",
    }
    media_type = mime_overrides.get(ext) or mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
    return FileResponse(resolved, media_type=media_type, headers={"Content-Disposition": "inline"})


@app.websocket("/api/events")
async def events_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    event_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        event_clients.discard(websocket)


if WEB_ROOT.exists():
    app.mount("/", StaticFiles(directory=str(WEB_ROOT), html=True), name="web")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Review Studio server.")
    parser.add_argument(
        "--workspace",
        default=None,
        help="Root folder to scan for video projects (subdirs with .video/state.json)",
    )
    parser.add_argument("--project", default=None, help="Initial video project (optional)")
    parser.add_argument("--scan-depth", type=int, default=2, help="Workspace scan depth (1-5)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve() if args.workspace else None
    project = Path(args.project).resolve() if args.project else None
    if project and not is_video_project(project):
        raise SystemExit(f"not a video project: {project / '.video/state.json'}")
    workspace_mgr.bootstrap(
        workspace=workspace,
        project=project,
        scan_depth=max(1, min(args.scan_depth, 5)),
    )
    if workspace_mgr.current_project:
        print(f"Review Studio project: {workspace_mgr.current_project}")
    elif workspace_mgr.workspace_root:
        print(f"Review Studio workspace: {workspace_mgr.workspace_root} (pick a project in UI)")
    else:
        print("Review Studio started — set workspace root in the web UI")

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
