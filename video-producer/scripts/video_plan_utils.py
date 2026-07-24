#!/usr/bin/env python3
"""Shared helpers for the unified video-plan toolchain."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def resolve_project_and_plan(value: str | Path) -> tuple[Path, Path]:
    candidate = Path(value).expanduser().resolve()
    if candidate.is_file() or candidate.suffix.lower() == ".json":
        return candidate.parent, candidate
    return candidate, candidate / "video-plan.json"


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"expected an object in {path}")
    return payload


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        temp_path = Path(temp_name)
        if temp_path.exists():
            temp_path.unlink()


def media_path(project: Path, source: str) -> Path:
    normalized = source.replace("\\", "/").lstrip("/")
    public_path = project / "public" / normalized
    if public_path.exists():
        return public_path
    return project / normalized


def safe_relative_media_path(value: str) -> bool:
    path = Path(value.replace("\\", "/"))
    return bool(value.strip()) and not path.is_absolute() and ".." not in path.parts
