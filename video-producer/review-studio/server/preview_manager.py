#!/usr/bin/env python3
"""HyperFrames preview server lifecycle for Review Studio."""
from __future__ import annotations

import re
import socket
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

_lock = threading.Lock()
_sessions: dict[str, dict[str, Any]] = {}


def _session_key(root: Path, segment: str) -> str:
    return f"{root.resolve()}::{segment}"


def _pick_port(preferred: int = 3017) -> int:
    for port in (preferred, preferred + 1, preferred + 2, 0):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("127.0.0.1", port))
                return int(sock.getsockname()[1])
        except OSError:
            continue
    return preferred


def _parse_list_output(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        m = re.search(r"(https?://[^\s]+)", line)
        if m:
            rows.append({"url": m.group(1).rstrip("/")})
    return rows


def _probe_url(url: str) -> bool:
    try:
        import urllib.request

        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:  # noqa: BLE001
        return False


def composition_ready(root: Path, segment: str) -> bool:
    return (root / "segments" / segment / "index.html").is_file()


def composition_embed_url(segment: str) -> str:
    return f"/api/preview/composition/{segment}/index.html"


def hyperframes_status(root: Path, segment: str) -> dict[str, Any]:
    seg_dir = root / "segments" / segment
    key = _session_key(root, segment)
    with _lock:
        session = _sessions.get(key)

    studio_url = None
    running = False
    pid = None
    port = None

    if session:
        proc = session.get("process")
        port = session.get("port")
        studio_url = session.get("url")
        if proc and proc.poll() is None:
            running = True
            pid = proc.pid
        elif studio_url and _probe_url(studio_url):
            running = True
            pid = session.get("pid")
        else:
            with _lock:
                _sessions.pop(key, None)

    index_html = seg_dir / "index.html"
    ready = index_html.is_file()
    return {
        "composition_ready": ready,
        "composition_embed_url": composition_embed_url(segment) if ready else None,
        "index_html_path": str(index_html) if ready else None,
        "index_html_expected": str(index_html),
        "project_root": str(root.resolve()),
        "studio_running": running,
        "studio_url": studio_url if running else None,
        "studio_port": port,
        "studio_pid": pid,
        "segment_dir": str(seg_dir) if seg_dir.is_dir() else None,
    }


def _npx_executable() -> str:
    import shutil
    for name in ("npx", "npx.cmd", "npx.exe"):
        path = shutil.which(name)
        if path:
            return path
    raise FileNotFoundError("npx not found on PATH")


class CompositionNotReadyError(FileNotFoundError):
    """Raised when segments/{segment}/index.html has not been built yet."""

    def __init__(self, root: Path, segment: str) -> None:
        self.root = root
        self.segment = segment
        self.expected = root / "segments" / segment / "index.html"
        super().__init__(f"segments/{segment}/index.html missing")


def start_hyperframes_studio(root: Path, segment: str, *, port: int | None = None) -> dict[str, Any]:
    seg_dir = root / "segments" / segment
    if not composition_ready(root, segment):
        raise CompositionNotReadyError(root, segment)

    existing = hyperframes_status(root, segment)
    if existing.get("studio_running") and existing.get("studio_url"):
        return {**existing, "started": False, "message": "studio already running"}

    chosen = _pick_port(port or 3017)
    npx = _npx_executable()
    cmd = [npx, "hyperframes", "preview", "--port", str(chosen), "--no-open", str(seg_dir)]
    proc = subprocess.Popen(  # noqa: S603
        cmd,
        cwd=str(seg_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    url = f"http://127.0.0.1:{chosen}"
    key = _session_key(root, segment)
    with _lock:
        _sessions[key] = {
            "process": proc,
            "port": chosen,
            "url": url,
            "pid": proc.pid,
        }

    return {
        **hyperframes_status(root, segment),
        "started": True,
        "message": f"HyperFrames Studio starting on {url}",
    }


def stop_hyperframes_studio(root: Path, segment: str) -> dict[str, Any]:
    key = _session_key(root, segment)
    stopped = False
    with _lock:
        session = _sessions.pop(key, None)
    if session:
        proc = session.get("process")
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            stopped = True
    return {**hyperframes_status(root, segment), "stopped": stopped}


def stop_all() -> None:
    with _lock:
        keys = list(_sessions.keys())
    for key in keys:
        parts = key.rsplit("::", 1)
        if len(parts) == 2:
            root = Path(parts[0])
            segment = parts[1]
            stop_hyperframes_studio(root, segment)
