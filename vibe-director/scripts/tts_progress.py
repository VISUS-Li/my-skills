#!/usr/bin/env python3
"""Shared TTS / audio-chain progress for Review Studio UI."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROGRESS_REL = "audio/stems/voice/generation_progress.json"


def progress_path(root: Path) -> Path:
    return root / PROGRESS_REL


def read_progress(root: Path, *, max_running_age_sec: int = 7200) -> dict[str, Any]:
    path = progress_path(root)
    if not path.exists():
        return {"status": "idle"}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {"status": "idle"}
    if not isinstance(data, dict):
        return {"status": "idle"}
    data.setdefault("status", "idle")
    if data.get("status") == "running" and data.get("updated_at"):
        try:
            updated = datetime.fromisoformat(str(data["updated_at"]).replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - updated.astimezone(timezone.utc)).total_seconds()
            if age > max_running_age_sec:
                return {"status": "idle", "stale": True, "previous": data}
        except ValueError:
            pass
    return data


def clear_progress(root: Path) -> None:
    path = progress_path(root)
    if path.exists():
        path.unlink()


def write_progress(root: Path, payload: dict[str, Any]) -> None:
    path = progress_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = dict(payload)
    body["updated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_progress(root: Path, **fields: Any) -> dict[str, Any]:
    current = read_progress(root, max_running_age_sec=999999)
    if current.get("status") == "idle" and "stale" not in current:
        current = {}
    current.update(fields)
    write_progress(root, current)
    return current
