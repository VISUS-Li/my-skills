#!/usr/bin/env python3
"""Review Studio workspace: multi-project discovery and hot-switch."""
from __future__ import annotations

import json
import sys
import threading
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from beat_store import is_video_project, load_beat_plan, load_segment_spec  # noqa: E402

CONFIG_DIR = Path.home() / ".video-producer"
CONFIG_PATH = CONFIG_DIR / "studio.json"
MAX_RECENT = 12


def project_summary(path: Path) -> dict[str, Any]:
    path = path.resolve()
    title = path.name
    slug = path.name
    current_stage = "plan-only"
    beat_plan = load_beat_plan(path)
    spec = load_segment_spec(path)
    if beat_plan.get("title"):
        title = str(beat_plan["title"])
    elif spec.get("segment_id"):
        title = f"{spec.get('segment_id')} · {path.name}"
    if (path / "outputs" / "review" / "review-studio" / "index.html").exists():
        current_stage = "first-slice-review"
    elif beat_plan.get("beats") and spec.get("shots"):
        current_stage = "first-slice-plan"
    elif (path / "outputs" / "script.md").exists():
        current_stage = "script-only"
    return {
        "path": str(path),
        "name": path.name,
        "title": title,
        "slug": slug,
        "current_stage": current_stage,
        "kind": "lite",
    }


def discover_projects(workspace: Path, *, max_depth: int = 2) -> list[dict[str, Any]]:
    workspace = workspace.resolve()
    found: dict[str, dict[str, Any]] = {}
    if is_video_project(workspace):
        summary = project_summary(workspace)
        found[summary["path"]] = summary
    if max_depth < 1:
        return sorted(found.values(), key=lambda item: item["title"].lower())

    queue: list[tuple[Path, int]] = [(workspace, 0)]
    seen_dirs: set[str] = {str(workspace)}
    while queue:
        current, depth = queue.pop(0)
        if depth >= max_depth:
            continue
        try:
            children = sorted(current.iterdir())
        except OSError:
            continue
        for child in children:
            if not child.is_dir():
                continue
            key = str(child.resolve())
            if key in seen_dirs:
                continue
            seen_dirs.add(key)
            if child.name.startswith(".") or child.name in {"node_modules", "__pycache__", "review-studio"}:
                continue
            if is_video_project(child):
                summary = project_summary(child)
                found[summary["path"]] = summary
            elif depth + 1 < max_depth:
                queue.append((child, depth + 1))
    return sorted(found.values(), key=lambda item: item["title"].lower())


class WorkspaceManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.workspace_root: Path | None = None
        self.current_project: Path | None = None
        self.scan_depth: int = 2
        self.recent_projects: list[str] = []
        self._load_config()

    def _load_config(self) -> None:
        if not CONFIG_PATH.exists():
            return
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
        except Exception:  # noqa: BLE001
            return
        ws = data.get("workspace_root")
        if ws:
            candidate = Path(ws)
            if candidate.exists():
                self.workspace_root = candidate.resolve()
        cp = data.get("current_project")
        if cp:
            candidate = Path(cp)
            if is_video_project(candidate):
                self.current_project = candidate.resolve()
        self.scan_depth = int(data.get("scan_depth") or 2)
        recent = data.get("recent_projects") or []
        self.recent_projects = [str(Path(p).resolve()) for p in recent if is_video_project(Path(p))][:MAX_RECENT]

    def save_config(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "workspace_root": str(self.workspace_root) if self.workspace_root else None,
            "current_project": str(self.current_project) if self.current_project else None,
            "scan_depth": self.scan_depth,
            "recent_projects": self.recent_projects[:MAX_RECENT],
        }
        CONFIG_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def require_project(self) -> Path:
        with self._lock:
            if self.current_project is None:
                raise ValueError("no project selected")
            return self.current_project

    def set_workspace(self, path: Path, *, scan_depth: int | None = None) -> dict[str, Any]:
        resolved = path.resolve()
        if not resolved.exists() or not resolved.is_dir():
            raise ValueError(f"workspace not found: {resolved}")
        with self._lock:
            self.workspace_root = resolved
            if scan_depth is not None:
                self.scan_depth = max(1, min(scan_depth, 5))
            projects = discover_projects(resolved, max_depth=self.scan_depth)
            if self.current_project is None and projects:
                self.current_project = Path(projects[0]["path"])
                self._remember_recent_locked(self.current_project)
            self.save_config()
            return self.snapshot_locked(projects)

    def scan(self) -> dict[str, Any]:
        with self._lock:
            if self.workspace_root is None:
                raise ValueError("workspace root not set")
            projects = discover_projects(self.workspace_root, max_depth=self.scan_depth)
            return self.snapshot_locked(projects)

    def switch_project(self, path: Path) -> dict[str, Any]:
        resolved = path.resolve()
        if not is_video_project(resolved):
            raise ValueError(f"not a video project (expected outputs/beat_plan.json or outputs/script.md): {resolved}")
        with self._lock:
            if self.current_project == resolved:
                return self.snapshot_light_locked()
            self.current_project = resolved
            self._remember_recent_locked(resolved)
            if self.workspace_root is None:
                self.workspace_root = resolved.parent
            self.save_config()
            return self.snapshot_light_locked()

    def _remember_recent_locked(self, path: Path) -> None:
        key = str(path.resolve())
        self.recent_projects = [key] + [p for p in self.recent_projects if p != key]
        self.recent_projects = self.recent_projects[:MAX_RECENT]

    def _recent_summaries_locked(self) -> list[dict[str, Any]]:
        recent: list[dict[str, Any]] = []
        for path_str in self.recent_projects:
            path = Path(path_str)
            if is_video_project(path):
                recent.append(project_summary(path))
        return recent

    def snapshot_light_locked(self) -> dict[str, Any]:
        recent = self._recent_summaries_locked()
        current = project_summary(self.current_project) if self.current_project else None
        projects: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in ([current] if current else []) + recent:
            if item and item["path"] not in seen:
                seen.add(item["path"])
                projects.append(item)
        return {
            "workspace_root": str(self.workspace_root) if self.workspace_root else None,
            "scan_depth": self.scan_depth,
            "current_project": current,
            "projects": projects,
            "recent_projects": recent,
        }

    def snapshot_locked(self, projects: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        if projects is None:
            projects = (
                discover_projects(self.workspace_root, max_depth=self.scan_depth)
                if self.workspace_root
                else []
            )
        recent = self._recent_summaries_locked()
        current = project_summary(self.current_project) if self.current_project else None
        return {
            "workspace_root": str(self.workspace_root) if self.workspace_root else None,
            "scan_depth": self.scan_depth,
            "current_project": current,
            "projects": projects,
            "recent_projects": recent,
        }

    def snapshot(self, *, scan: bool = False) -> dict[str, Any]:
        with self._lock:
            if scan:
                return self.snapshot_locked()
            return self.snapshot_light_locked()

    def bootstrap(self, *, workspace: Path | None = None, project: Path | None = None, scan_depth: int = 2) -> None:
        with self._lock:
            if workspace:
                self.workspace_root = workspace.resolve()
                self.scan_depth = scan_depth
            if project and is_video_project(project):
                self.current_project = project.resolve()
                self._remember_recent_locked(self.current_project)
            elif self.current_project is None and self.workspace_root:
                projects = discover_projects(self.workspace_root, max_depth=self.scan_depth)
                if projects:
                    self.current_project = Path(projects[0]["path"])
                    self._remember_recent_locked(self.current_project)
            self.save_config()


workspace_mgr = WorkspaceManager()
