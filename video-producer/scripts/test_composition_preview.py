#!/usr/bin/env python3
"""Validate HyperFrames composition HTML + Review Studio preview contract."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "review-studio" / "server" / "main.py"


def http_get(url: str, *, timeout: int = 30) -> tuple[int, bytes]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def validate_index_html(html: str) -> list[str]:
    failures: list[str] = []
    required = (
        "data-composition-id",
        "window.__timelines",
        "__timelines['S001']",
        "tl.to(scene, { autoAlpha: 1",
        "initComposition",
    )
    for marker in required:
        if marker not in html:
            failures.append(f"missing marker in index.html: {marker}")
    if "tl.set(scene, { autoAlpha: 1 }" in html:
        failures.append("deprecated dual-set autoAlpha pattern still present")
    return failures


def wait_server(base: str, timeout: int = 20) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            status, _ = http_get(f"{base}/api/project", timeout=2)
            if status == 200:
                return True
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.4)
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--segment", default="S001")
    parser.add_argument("--port", type=int, default=8812)
    parser.add_argument("--no-server", action="store_true", help="Only validate on-disk index.html")
    args = parser.parse_args()

    project = args.project.resolve()
    index_path = project / "segments" / args.segment / "index.html"
    failures: list[str] = []

    if not index_path.is_file():
        print(f"FAIL: {index_path} missing")
        return 1

    html = index_path.read_text(encoding="utf-8")
    failures.extend(validate_index_html(html))
    if failures:
        for item in failures:
            print(f"FAIL: {item}")
        return 1

    print(f"OK: static contract in {index_path}")

    if args.no_server:
        return 0

    base = f"http://127.0.0.1:{args.port}"
    proc = subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            str(SERVER),
            "--port",
            str(args.port),
            "--project",
            str(project),
        ],
        cwd=str(ROOT / "review-studio"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        if not wait_server(base):
            print("FAIL: review studio did not start")
            return 1

        status, timeline_raw = http_get(f"{base}/api/timeline?segment={args.segment}")
        if status != 200:
            print(f"FAIL: timeline API status {status}")
            return 1
        timeline = json.loads(timeline_raw.decode("utf-8"))
        preview = timeline.get("preview") or {}
        if not preview.get("composition_ready"):
            print("FAIL: composition_ready is false")
            return 1
        embed = preview.get("studio_embed_url") or ""
        if preview.get("studio_running") and not embed.endswith(f"#project/{args.segment}"):
            print(f"FAIL: bad studio_embed_url: {preview.get('studio_embed_url')}")
            return 1

        comp_url = preview.get("composition_embed_url") or f"/api/preview/composition/{args.segment}/index.html"
        status, body = http_get(f"{base}{comp_url}", timeout=60)
        if status != 200:
            print(f"FAIL: composition proxy status {status}")
            return 1
        failures.extend(validate_index_html(body.decode("utf-8", errors="replace")))
        if failures:
            for item in failures:
                print(f"FAIL: {item}")
            return 1

        print(f"OK: timeline + composition proxy for {project.name}/{args.segment}")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
