#!/usr/bin/env python3
"""IndexTTS config and reference-audio helpers for Review Studio."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from audio_ref_utils import (  # noqa: E402
    ffmpeg_available,
    is_riff_file,
    normalize_ref_audio,
    tts_ref_rel_path,
)
from tts_progress import clear_progress, read_progress, write_progress  # noqa: E402

CONFIG_REL = "audio/indextts2_config.json"
REFS_DIR_REL = "audio/refs"
REGISTRY_REL = "audio/refs/registry.json"
PROGRESS_REL = "audio/stems/voice/generation_progress.json"
UPLOAD_STATE_DIR = "audio/refs/.uploads"


def config_path(root: Path) -> Path:
    return root / CONFIG_REL


def load_config(root: Path) -> dict[str, Any]:
    path = config_path(root)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_config(root: Path, data: dict[str, Any]) -> Path:
    path = config_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def merge_config(existing: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    for key, value in patch.items():
        if value is None:
            continue
        if key in {"defaults", "voice_reference", "segment_emotion_vectors"} and isinstance(value, dict):
            base = dict(merged.get(key) or {})
            base.update(value)
            merged[key] = base
        else:
            merged[key] = value
    if patch.get("base_url") and not patch.get("webui_url"):
        merged["webui_url"] = patch["base_url"]
    return merged


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_ref_registry(root: Path) -> dict[str, Any]:
    path = root / REGISTRY_REL
    if not path.exists():
        return {"version": "1", "refs": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {"version": "1", "refs": []}
    if not isinstance(data.get("refs"), list):
        data["refs"] = []
    return data


def save_ref_registry(root: Path, data: dict[str, Any]) -> None:
    path = root / REGISTRY_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync_ref_registry(root: Path) -> dict[str, Any]:
    reg = load_ref_registry(root)
    by_path: dict[str, dict[str, Any]] = {
        str(item.get("path", "")).replace("\\", "/"): dict(item)
        for item in reg.get("refs", [])
        if item.get("path")
    }
    refs_dir = root / REFS_DIR_REL
    refs_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ("*.wav", "*.mp3"):
        for wav in sorted(refs_dir.glob(pattern)):
            rel = wav.relative_to(root).as_posix()
            stat = wav.stat()
            entry = by_path.get(rel, {})
            entry.setdefault("path", rel)
            entry.setdefault("name", wav.name)
            entry.setdefault("label", wav.stem)
            entry.setdefault("uploaded_at", datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat())
            entry.setdefault("source", "discovered")
            entry["size_bytes"] = stat.st_size
            entry["exists"] = True
            by_path[rel] = entry

    refs_list: list[dict[str, Any]] = []
    for rel, entry in by_path.items():
        path = root / rel
        entry["exists"] = path.exists()
        if path.exists():
            entry["size_bytes"] = path.stat().st_size
        refs_list.append(entry)
    refs_list.sort(key=lambda item: item.get("uploaded_at") or "", reverse=True)
    reg["refs"] = refs_list
    save_ref_registry(root, reg)
    return reg


def register_ref_entry(root: Path, rel_path: str, *, source: str = "upload") -> None:
    reg = sync_ref_registry(root)
    normalized = rel_path.replace("\\", "/")
    path = root / normalized
    now = _utc_now()
    found = False
    for item in reg.get("refs", []):
        if item.get("path") == normalized:
            item["uploaded_at"] = now
            item["source"] = source
            item["size_bytes"] = path.stat().st_size if path.exists() else item.get("size_bytes", 0)
            item["exists"] = path.exists()
            found = True
            break
    if not found:
        reg.setdefault("refs", []).insert(0, {
            "path": normalized,
            "name": path.name,
            "label": path.stem,
            "uploaded_at": now,
            "source": source,
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "exists": path.exists(),
        })
    save_ref_registry(root, reg)


def list_refs(root: Path) -> dict[str, Any]:
    cfg = load_config(root)
    selected = str((cfg.get("voice_reference") or {}).get("path", "audio/refs/narrator_ref.wav")).replace("\\", "/")
    reg = sync_ref_registry(root)
    items: list[dict[str, Any]] = []
    for entry in reg.get("refs", []):
        rel = str(entry.get("path", "")).replace("\\", "/")
        path = root / rel
        if not path.exists():
            continue
        fmt = path.suffix.lower().lstrip(".")
        if fmt == "wav":
            mp3_sibling = path.with_suffix(".mp3")
            if mp3_sibling.exists():
                mp3_rel = mp3_sibling.relative_to(root).as_posix()
                mp3_entry = next((e for e in reg.get("refs", []) if e.get("path") == mp3_rel), None)
                if mp3_entry and mp3_entry.get("source") == "upload":
                    continue
        tts_path = rel
        if fmt == "mp3":
            try:
                tts_path = tts_ref_rel_path(root, rel)
            except (FileNotFoundError, RuntimeError):
                tts_path = rel
        items.append({
            "name": entry.get("name") or path.name,
            "label": entry.get("label") or path.stem,
            "path": rel,
            "tts_path": tts_path,
            "format": fmt,
            "size_bytes": path.stat().st_size,
            "uploaded_at": entry.get("uploaded_at"),
            "source": entry.get("source", "discovered"),
            "selected": rel == selected,
        })
    return {
        "refs_dir": REFS_DIR_REL,
        "selected_path": selected,
        "refs": items,
    }


def select_ref(root: Path, rel_path: str) -> dict[str, Any]:
    normalized = rel_path.replace("\\", "/")
    if not normalized.startswith(REFS_DIR_REL + "/") or ".." in normalized:
        raise ValueError("reference path must be under audio/refs/")
    target = root / normalized
    if not target.exists():
        raise FileNotFoundError(normalized)
    cfg = load_config(root)
    cfg.setdefault("voice_reference", {})
    cfg["voice_reference"]["path"] = normalized
    try:
        cfg["voice_reference"]["tts_path"] = tts_ref_rel_path(root, normalized)
    except (FileNotFoundError, RuntimeError):
        cfg["voice_reference"].pop("tts_path", None)
    save_config(root, cfg)
    return {"selected_path": normalized, "config": cfg, "tts_path": cfg["voice_reference"].get("tts_path")}


def upload_state_path(root: Path, upload_id: str) -> Path:
    return root / UPLOAD_STATE_DIR / f"{upload_id}.json"


def write_upload_state(root: Path, upload_id: str, payload: dict[str, Any]) -> None:
    path = upload_state_path(root, upload_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({**payload, "upload_id": upload_id, "updated_at": _utc_now()}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def read_upload_state(root: Path, upload_id: str) -> dict[str, Any] | None:
    path = upload_state_path(root, upload_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return None


def clear_upload_state(root: Path, upload_id: str) -> None:
    path = upload_state_path(root, upload_id)
    if path.exists():
        path.unlink()


def save_ref_upload(
    root: Path,
    filename: str,
    data: bytes,
    *,
    select: bool = True,
    upload_id: str | None = None,
) -> dict[str, Any]:
    safe_name = Path(filename).name
    ext = safe_name.lower()
    if not (ext.endswith(".wav") or ext.endswith(".mp3")):
        raise ValueError("only .wav and .mp3 reference files are supported")
    if not safe_name or safe_name in {".", ".."}:
        raise ValueError("invalid filename")
    if len(data) < 16:
        raise ValueError("file too small to be a valid audio file")

    def progress(status: str, message: str, pct: int) -> None:
        if upload_id:
            write_upload_state(root, upload_id, {
                "status": status,
                "message": message,
                "progress": pct,
                "filename": safe_name,
            })

    progress("uploading", "正在保存文件…", 20)
    refs_dir = root / REFS_DIR_REL
    refs_dir.mkdir(parents=True, exist_ok=True)
    dest = refs_dir / safe_name
    dest.write_bytes(data)
    rel = dest.relative_to(root).as_posix()
    register_ref_entry(root, rel, source="upload")

    stem = Path(safe_name).stem
    wav_dest = refs_dir / f"{stem}.wav"
    tts_path = rel
    needs_normalize = dest.suffix.lower() == ".mp3" or not is_riff_file(dest) or dest.resolve() != wav_dest.resolve()

    if needs_normalize:
        if not ffmpeg_available():
            raise RuntimeError("需要安装 ffmpeg 才能转码 MP3 或规范化 WAV 参考音频")
        progress("converting", "ffmpeg 转码中，请稍候…", 55)
        if dest.suffix.lower() == ".mp3":
            normalize_ref_audio(dest, wav_dest)
        elif dest.resolve() == wav_dest.resolve():
            tmp = refs_dir / f".{stem}_norm.wav"
            normalize_ref_audio(dest, tmp)
            tmp.replace(wav_dest)
        else:
            normalize_ref_audio(dest, wav_dest)
        register_ref_entry(root, wav_dest.relative_to(root).as_posix(), source="converted")
        tts_path = wav_dest.relative_to(root).as_posix()
        progress("converting", "转码完成", 85)

    progress("finalizing", "写入配置…", 95)
    result: dict[str, Any] = {
        "path": rel,
        "tts_path": tts_path,
        "size_bytes": dest.stat().st_size,
        "format": dest.suffix.lower().lstrip("."),
    }
    if select:
        cfg = load_config(root)
        cfg.setdefault("voice_reference", {})
        cfg["voice_reference"]["path"] = rel
        cfg["voice_reference"]["tts_path"] = tts_path
        save_config(root, cfg)
        result["selected"] = True
        result["config"] = cfg
    progress("completed", "上传完成", 100)
    return result


def delete_ref(root: Path, rel_path: str) -> dict[str, Any]:
    normalized = rel_path.replace("\\", "/")
    if not normalized.startswith(REFS_DIR_REL + "/") or ".." in normalized:
        raise ValueError("reference path must be under audio/refs/")
    target = root / normalized
    if not target.exists():
        raise FileNotFoundError(normalized)

    cfg = load_config(root)
    selected = str((cfg.get("voice_reference") or {}).get("path", "")).replace("\\", "/")
    was_selected = selected == normalized or selected == str((cfg.get("voice_reference") or {}).get("tts_path", "")).replace("\\", "/")
    target.unlink()
    if target.suffix.lower() == ".mp3":
        wav_pair = target.with_suffix(".wav")
        if wav_pair.exists():
            wav_pair.unlink()
            normalized_wav = wav_pair.relative_to(root).as_posix()
            reg = sync_ref_registry(root)
            reg["refs"] = [item for item in reg.get("refs", []) if item.get("path") != normalized_wav]
            save_ref_registry(root, reg)

    reg = sync_ref_registry(root)
    reg["refs"] = [item for item in reg.get("refs", []) if item.get("path") != normalized]
    save_ref_registry(root, reg)

    new_selected = selected
    if was_selected:
        remaining = [item for item in list_refs(root)["refs"] if item.get("exists", True)]
        if remaining:
            new_selected = remaining[0]["path"]
            cfg.setdefault("voice_reference", {})
            cfg["voice_reference"]["path"] = new_selected
            save_config(root, cfg)
        else:
            new_selected = ""
            if cfg.get("voice_reference"):
                cfg["voice_reference"].pop("path", None)
                save_config(root, cfg)

    return {
        "deleted": normalized,
        "selected_path": new_selected,
        "refs": list_refs(root),
    }


def init_tts_job_progress(root: Path, *, segment: str, job_id: str, label: str) -> None:
    clear_progress(root)
    write_progress(root, {
        "status": "queued",
        "phase": "queued",
        "message": f"{label} · 任务已排队",
        "percent": 0,
        "segment_id": segment,
        "job_id": job_id,
        "done": 0,
        "total": 0,
    })


def health_check(root: Path) -> dict[str, Any]:
    cfg_path = config_path(root)
    if not cfg_path.exists():
        return {"available": False, "reason": "indextts2_config.json missing"}
    cfg = load_config(root)
    base_url = str(cfg.get("base_url", "")).rstrip("/") + "/"
    ref_rel = str((cfg.get("voice_reference") or {}).get("path", "audio/refs/narrator_ref.wav"))
    ref_path = root / ref_rel.replace("\\", "/")
    try:
        import urllib.request

        req = urllib.request.Request(f"{base_url}config", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                return {
                    "available": True,
                    "base_url": base_url,
                    "status": "online",
                    "reference_path": ref_rel.replace("\\", "/"),
                    "reference_exists": ref_path.exists(),
                }
    except Exception as exc:  # noqa: BLE001
        return {
            "available": False,
            "base_url": base_url,
            "reason": str(exc),
            "reference_path": ref_rel.replace("\\", "/"),
            "reference_exists": ref_path.exists(),
        }
    return {
        "available": False,
        "base_url": base_url,
        "reason": "unknown",
        "reference_path": ref_rel.replace("\\", "/"),
        "reference_exists": ref_path.exists(),
    }
