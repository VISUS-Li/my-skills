#!/usr/bin/env python3
"""Sync asset_manifest review columns with on-disk assets and review registry."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from review_core import (  # noqa: E402
    append_registry,
    content_hash,
    init_review_files,
    load_stage_manifest,
    read_registry_lines,
    registry_index,
)


EXTENDED_COLUMNS = [
    "asset_id",
    "type",
    "source",
    "path_or_url",
    "segment_id",
    "role",
    "rights_status",
    "status",
    "review_status",
    "beat_ids",
    "actor_id",
    "version",
    "last_regen_at",
    "notes",
]


def discover_segment_assets(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    segments_dir = root / "segments"
    if not segments_dir.exists():
        return rows
    for segment_dir in sorted(segments_dir.iterdir()):
        if not segment_dir.is_dir():
            continue
        assets_dir = segment_dir / "assets"
        if not assets_dir.exists():
            continue
        segment_id = segment_dir.name
        for asset_path in sorted(assets_dir.glob("*")):
            if not asset_path.is_file():
                continue
            rel = asset_path.relative_to(root).as_posix()
            asset_id = asset_path.stem
            rows.append({
                "asset_id": asset_id,
                "type": asset_path.suffix.lstrip(".") or "file",
                "source": "generated",
                "path_or_url": rel,
                "segment_id": segment_id,
                "role": "icon",
                "rights_status": "self-created",
                "status": "ready",
                "review_status": "review",
                "beat_ids": "",
                "actor_id": "",
                "version": "1",
                "last_regen_at": "",
                "notes": "auto-discovered by review_sync",
            })
    return rows


def load_manifest_rows(root: Path) -> tuple[list[dict[str, str]], list[str]]:
    path = root / "assets" / "asset_manifest.csv"
    if not path.exists():
        return [], EXTENDED_COLUMNS
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or EXTENDED_COLUMNS)
        rows = [dict(row) for row in reader]
    for col in EXTENDED_COLUMNS:
        if col not in fieldnames:
            fieldnames.append(col)
    return rows, fieldnames


def discover_actors(root: Path, segment_id: str = "S001") -> list[dict[str, Any]]:
    import re

    rows: list[dict[str, Any]] = []
    scripts_dir = root / "scripts"
    if not scripts_dir.exists():
        return rows
    for scene_file in sorted(scripts_dir.glob("*_scenes.py")):
        text = scene_file.read_text(encoding="utf-8", errors="replace")
        rel = scene_file.relative_to(root).as_posix()
        for actor_id in sorted(set(re.findall(r'data-actor="([^"]+)"', text))):
            rows.append({
                "artifact_id": f"actor:{segment_id}:{actor_id}",
                "artifact_type": "actor",
                "path": rel,
                "stage": "segments",
                "segment_id": segment_id,
                "beat_ids": [],
                "actor_ids": [actor_id],
                "status": "review",
                "previous_status": "draft",
                "reviewer": "system",
                "reviewer_note": "discovered by review_sync",
                "version": 1,
            })
    return rows


def sync_manifest(root: Path, *, write: bool = True) -> dict:
    init_review_files(root)
    existing_rows, fieldnames = load_manifest_rows(root)
    by_path = {row.get("path_or_url", ""): row for row in existing_rows if row.get("path_or_url")}
    discovered = discover_segment_assets(root)
    registry = registry_index(read_registry_lines(root))
    added = 0
    updated = 0

    for item in discovered:
        path = item["path_or_url"]
        if path in by_path:
            row = by_path[path]
            if not row.get("review_status"):
                row["review_status"] = "review"
                updated += 1
            if row.get("status") == "pending" and Path(root / path).exists():
                row["status"] = "ready"
                updated += 1
        else:
            by_path[path] = item
            added += 1

        artifact_id = f"asset:{item['asset_id']}"
        resolved = root / path
        if artifact_id not in registry and resolved.exists():
            append_registry(root, {
                "artifact_id": artifact_id,
                "artifact_type": item["type"],
                "path": path,
                "stage": "assets",
                "segment_id": item["segment_id"],
                "beat_ids": [],
                "actor_ids": [],
                "status": "review",
                "previous_status": "draft",
                "reviewer": "system",
                "reviewer_note": "discovered by review_sync",
                "version": 1,
                "content_hash": content_hash(resolved),
            })

    seg = "S001"
    beats_path = root / "script" / "narration_beats.csv"
    if beats_path.exists():
        with beats_path.open(newline="", encoding="utf-8-sig") as handle:
            seg_ids = {row.get("segment_id") for row in csv.DictReader(handle) if row.get("segment_id")}
            if len(seg_ids) == 1:
                seg = next(iter(seg_ids))
    for actor in discover_actors(root, segment_id=seg):
        if actor["artifact_id"] not in registry:
            append_registry(root, actor)
            registry[actor["artifact_id"]] = actor

    merged = list(by_path.values())
    if write:
        out_path = root / "assets" / "asset_manifest.csv"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(merged)

    return {
        "manifest_rows": len(merged),
        "added": added,
        "updated": updated,
        "registry_rows": len(read_registry_lines(root)),
        "stages": len(load_stage_manifest(root).get("stages", {})),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync asset manifest and review registry from disk.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--dry-run", action="store_true", help="Report only; do not write")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    summary = sync_manifest(root, write=not args.dry_run)
    print(f"review_sync: rows={summary['manifest_rows']} added={summary['added']} updated={summary['updated']} registry={summary['registry_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
