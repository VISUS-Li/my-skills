#!/usr/bin/env python3
"""Artifact read/write helpers for Review Studio."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from review_core import (
    append_history,
    append_registry,
    content_hash,
    load_stage_manifest,
    propagate_stale,
    read_registry_lines,
    registry_index,
    resolve_safe_path,
    utc_now,
)

TEXT_EXTENSIONS = {".md", ".txt", ".csv", ".json", ".jsonl", ".srt", ".html", ".py", ".sh", ".yaml", ".yml"}


def resolve_artifact_pattern(root: Path, pattern: str, segment: str) -> str:
    return pattern.replace("{segment}", segment)


def list_stage_artifacts(root: Path, stage_id: str, segment: str = "S001") -> list[dict[str, Any]]:
    manifest = load_stage_manifest(root)
    meta = manifest.get("stages", {}).get(stage_id, {})
    registry = registry_index(read_registry_lines(root))
    items: list[dict[str, Any]] = []

    for pattern in meta.get("required_artifacts", []) + meta.get("optional_artifacts", []):
        rel = resolve_artifact_pattern(root, pattern, segment)
        resolved = resolve_safe_path(root, rel)
        exists = resolved is not None and resolved.exists()
        artifact_id = f"file:{rel}"
        reg = registry.get(artifact_id, {})
        items.append({
            "path": rel,
            "pattern": pattern,
            "exists": exists,
            "required": pattern in meta.get("required_artifacts", []),
            "review_status": reg.get("status", "review" if exists else "draft"),
            "artifact_id": artifact_id,
            "size_bytes": resolved.stat().st_size if exists and resolved else 0,
        })
    return items


def read_artifact(root: Path, rel_path: str) -> dict[str, Any]:
    resolved = resolve_safe_path(root, rel_path)
    if not resolved or not resolved.exists() or not resolved.is_file():
        raise FileNotFoundError(rel_path)
    suffix = resolved.suffix.lower()
    if suffix not in TEXT_EXTENSIONS:
        return {
            "path": rel_path,
            "content_type": "binary",
            "size_bytes": resolved.stat().st_size,
            "content": None,
        }
    text = resolved.read_text(encoding="utf-8-sig")
    parsed: Any = None
    if suffix == ".json":
        parsed = json.loads(text)
    elif suffix == ".csv":
        with resolved.open(newline="", encoding="utf-8-sig") as handle:
            parsed = list(csv.DictReader(handle))
    return {
        "path": rel_path,
        "content_type": suffix.lstrip(".") or "text",
        "content": text,
        "parsed": parsed,
        "size_bytes": len(text.encode("utf-8")),
    }


def write_artifact(root: Path, rel_path: str, content: str, *, note: str = "", segment_id: str = "S001") -> dict[str, Any]:
    resolved = resolve_safe_path(root, rel_path)
    if not resolved:
        raise ValueError(f"unsafe path: {rel_path}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(content, encoding="utf-8")
    stale = propagate_stale(root, rel_path, note=note or f"edited {rel_path}", segment_id=segment_id)
    append_registry(root, {
        "artifact_id": f"file:{rel_path}",
        "artifact_type": resolved.suffix.lstrip(".") or "file",
        "path": rel_path.replace("\\", "/"),
        "stage": "manual",
        "segment_id": segment_id,
        "status": "review",
        "previous_status": registry_index(read_registry_lines(root)).get(f"file:{rel_path}", {}).get("status", "draft"),
        "reviewer": "human",
        "reviewer_note": note,
        "content_hash": content_hash(resolved),
        "updated_at": utc_now(),
    })
    append_history(root, {"type": "artifact_edited", "path": rel_path, "note": note})
    return {"path": rel_path, "stale": stale}


def find_voiceover_path(root: Path) -> Path | None:
    script_dir = root / "script"
    if not script_dir.exists():
        return None
    versioned = sorted(script_dir.glob("voiceover.v*.md"), reverse=True)
    if versioned:
        return versioned[0]
    default = script_dir / "voiceover.md"
    return default if default.exists() else None


def resolve_asset_file(
    root: Path,
    path_or_url: str,
    *,
    asset_id: str = "",
    segment_id: str = "S001",
) -> Path | None:
    """Resolve a visual asset to an on-disk file, trying common fallbacks."""
    rel = (path_or_url or "").strip().replace("\\", "/")
    if rel.startswith(("http://", "https://", "//")):
        return None

    def try_path(candidate: str) -> Path | None:
        if not candidate:
            return None
        resolved = resolve_safe_path(root, candidate)
        if resolved and resolved.is_file():
            return resolved
        return None

    hit = try_path(rel)
    if hit:
        return hit

    stem = asset_id or (Path(rel).stem if rel else "")
    ext = Path(rel).suffix if rel and Path(rel).suffix else ""
    seg = segment_id or "S001"
    fallbacks: list[str] = []
    if stem:
        if ext:
            fallbacks.append(f"segments/{seg}/assets/{stem}{ext}")
        else:
            fallbacks.extend([
                f"segments/{seg}/assets/{stem}.svg",
                f"segments/{seg}/assets/{stem}.png",
                f"segments/{seg}/assets/{stem}.webp",
                f"segments/{seg}/assets/{stem}.mp4",
                f"segments/{seg}/assets/{stem}.webm",
                f"segments/{seg}/assets/{stem}.mov",
            ])
    if rel:
        fallbacks.append(f"assets/{Path(rel).name}")

    for candidate in fallbacks:
        hit = try_path(candidate)
        if hit:
            return hit
    return None
