#!/usr/bin/env python3
"""Validate HyperFrames composition HTML + Review Studio preview contract."""
from __future__ import annotations

import argparse
import json
import re
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


def validate_index_html(html: str, *, segment: str = "S001") -> list[str]:
    failures: list[str] = []
    timeline_markers = (
        f"__timelines['{segment}']",
        f'__timelines["{segment}"]',
        f"__timelines[SEGMENT_ID]",
    )
    required = (
        "data-composition-id",
        "window.__timelines",
        "initComposition",
        "__compositionErrors",
        "paused: true",
        "data-build-entry",
    )
    recommended = (
        "safeTargets",
        "addFromIfPresent",
        "addToIfPresent",
        "composition-error-overlay",
    )
    for marker in required:
        if marker not in html:
            failures.append(f"missing marker in index.html: {marker}")
    if not any(marker in html for marker in timeline_markers):
        failures.append(f"missing segment timeline registration marker for {segment}")
    for marker in recommended:
        if marker not in html:
            failures.append(f"missing preview safety helper/marker in index.html: {marker}")
    if "tl.set(scene, { autoAlpha: 1 }" in html and "tl.to(scene, { autoAlpha: 1" in html:
        failures.append("deprecated dual-set autoAlpha pattern still present")
    if re.search(r"\(\s*el\s*\)\s*=>\s*el\.dataset", html):
        failures.append("GSAP property callback appears to use (el) => el.dataset; use (index, target) => target.dataset")
    if re.search(r"\btl\.(?:from|to|fromTo)\(\s*['\"]\.", html):
        failures.append("raw class selector passed directly to tl.from/to/fromTo; guard optional targets with safeTargets/add*IfPresent")
    if re.search(r"\b(?:tl|timeline)\.play\s*\(", html):
        failures.append("composition timeline calls play(); Review Studio drives preview by seeking .time(t)")
    return failures


def validate_builder_contract(project: Path, segment: str) -> list[str]:
    seg = segment.lower()
    builders = [
        project / "scripts" / f"build_{seg}_composition.py",
        project / "scripts" / "build_segment_index.py",
    ]
    if any(path.is_file() for path in builders):
        return []
    segment_builders = sorted((project / "segments" / segment / "scripts").glob("build*.py"))
    if segment_builders:
        rels = ", ".join(str(path.relative_to(project)) for path in segment_builders[:3])
        return [
            f"missing standard root composition builder scripts/build_{seg}_composition.py "
            f"(found segment-local builder only: {rels})"
        ]
    return [f"missing standard composition builder: scripts/build_{seg}_composition.py"]


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


def validate_runtime_with_playwright(url: str, segment: str) -> list[str]:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        print("SKIP: playwright not installed; runtime composition JS check not run")
        return []

    failures: list[str] = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as exc:  # noqa: BLE001
            reason = str(exc).splitlines()[0]
            print(f"SKIP: playwright browser unavailable; runtime composition JS check not run ({reason})")
            return []
        page = browser.new_page()
        console_errors: list[str] = []
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))
        page.on(
            "console",
            lambda msg: console_errors.append(msg.text) if msg.type in {"error", "warning"} else None,
        )
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(300)
        state = page.evaluate(
            """(segment) => {
              const tl = window.__timelines && window.__timelines[segment];
              return {
                hasTimeline: !!tl,
                paused: !!(tl && tl.paused && tl.paused()),
                duration: tl && tl.duration ? tl.duration() : 0,
                errors: window.__compositionErrors || []
              };
            }""",
            segment,
        )
        browser.close()
    if not state.get("hasTimeline"):
        failures.append(f"runtime did not register window.__timelines[{segment!r}]")
    if not state.get("paused"):
        failures.append("runtime timeline is not paused; Review Studio expects seek-only control")
    if float(state.get("duration") or 0) <= 0:
        failures.append("runtime timeline duration is zero")
    if state.get("errors"):
        failures.append("runtime composition errors: " + " | ".join(map(str, state["errors"][:3])))
    target_warnings = [msg for msg in console_errors if "GSAP target" in msg or "target not found" in msg.lower()]
    if target_warnings:
        failures.append("runtime GSAP target warnings: " + " | ".join(target_warnings[:3]))
    hard_errors = [msg for msg in console_errors if "GSAP target" not in msg and "target not found" not in msg.lower()]
    if hard_errors:
        failures.append("runtime console errors: " + " | ".join(hard_errors[:3]))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_arg", nargs="?", type=Path, help="Project root")
    parser.add_argument("--project", type=Path, default=None)
    parser.add_argument("--segment", default="S001")
    parser.add_argument("--port", type=int, default=8812)
    parser.add_argument("--no-server", action="store_true", help="Only validate on-disk index.html")
    parser.add_argument("--skip-browser", action="store_true", help="Skip Playwright runtime JS check")
    parser.add_argument("--allow-missing-builder", action="store_true", help="Do not require scripts/build_<segment>_composition.py")
    args = parser.parse_args()

    project_arg = args.project or args.project_arg
    if not project_arg:
        parser.error("project root is required")
    project = project_arg.resolve()
    index_path = project / "segments" / args.segment / "index.html"
    failures: list[str] = []

    if not args.allow_missing_builder:
        failures.extend(validate_builder_contract(project, args.segment))

    if not index_path.is_file():
        print(f"FAIL: {index_path} missing")
        for item in failures:
            print(f"FAIL: {item}")
        return 1

    html = index_path.read_text(encoding="utf-8")
    failures.extend(validate_index_html(html, segment=args.segment))
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
        failures.extend(validate_index_html(body.decode("utf-8", errors="replace"), segment=args.segment))
        if not args.skip_browser:
            failures.extend(validate_runtime_with_playwright(f"{base}{comp_url}", args.segment))
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
