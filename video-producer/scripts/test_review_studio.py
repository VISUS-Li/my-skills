#!/usr/bin/env python3
"""Integration tests for Review Studio (T1-T20)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
PROJECT = Path(r"c:\Users\11839\opc-ai-douyin-3min")
SERVER = ROOT / "review-studio" / "server" / "main.py"
BASE = "http://127.0.0.1:8801"
PORT = 8801


def run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def http(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{BASE}{path}", data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = resp.read().decode("utf-8")
            return resp.status, json.loads(payload) if payload else {}
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(payload)
        except json.JSONDecodeError:
            return exc.code, {"detail": payload}


def wait_job(job_id: str, timeout: int = 90) -> dict:
    for _ in range(timeout):
        code, data = http("GET", f"/api/jobs/{job_id}")
        if code == 200 and data.get("job", {}).get("status") in {"completed", "failed"}:
            return data["job"]
        time.sleep(1)
    return {}


def main() -> int:
    failures: list[str] = []

    if not PROJECT.exists():
        print(f"SKIP: fixture project missing: {PROJECT}")
        return 0

    state_path = PROJECT / ".video" / "state.json"
    backup = state_path.read_text(encoding="utf-8-sig")
    beats_backup = (PROJECT / "script" / "narration_beats.csv").read_text(encoding="utf-8-sig")
    vo_backup = None
    vo_path = PROJECT / "segments" / "S001" / "vo_timing.json"
    if vo_path.exists():
        vo_backup = vo_path.read_text(encoding="utf-8-sig")

    def restore() -> None:
        state_path.write_text(backup, encoding="utf-8")
        (PROJECT / "script" / "narration_beats.csv").write_text(beats_backup, encoding="utf-8")
        if vo_backup is not None:
            vo_path.write_text(vo_backup, encoding="utf-8")

    state = json.loads(backup)
    state["stages"]["script"]["status"] = "draft"
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    t1 = run([sys.executable, str(SCRIPTS / "validate_gates.py"), str(PROJECT)])
    restore()
    state_path.write_text(json.dumps(json.loads(backup), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if t1.returncode != 1:
        failures.append("T1 validate_gates should exit 1 when upstream draft")

    t2 = run([
        sys.executable, str(SCRIPTS / "stage_gate.py"), str(PROJECT),
        "--stage", "qc", "--status", "review", "--note", "test", "--require-deps-approved",
    ])
    if t2.returncode == 0:
        failures.append("T2 stage_gate should fail when qc deps not approved")

    proc = subprocess.Popen(
        [sys.executable, str(SERVER), "--workspace", str(PROJECT.parent), "--project", str(PROJECT), "--port", str(PORT)],
        cwd=str(SERVER.parent),
    )
    for _ in range(40):
        try:
            code, _ = http("GET", "/api/project")
            if code == 200:
                break
        except Exception:  # noqa: BLE001
            time.sleep(0.5)
    else:
        proc.kill()
        failures.append("Review Studio server failed to start")
        restore()
        return 1

    code, project = http("GET", "/api/project")
    if code != 200 or project.get("needs_project"):
        failures.append("T-api project endpoint failed or no project")

    code, ws = http("PUT", "/api/workspace/root", {"path": str(PROJECT.parent), "scan_depth": 2})
    if code != 200 or not ws.get("projects"):
        failures.append(f"T-workspace scan found no projects: {ws}")

    code, sw = http("POST", "/api/project/switch", {"path": str(PROJECT)})
    switched = str(Path(sw.get("current_project", {}).get("path", "")).resolve())
    if code != 200 or switched != str(PROJECT.resolve()):
        failures.append(f"T9 project switch failed: {sw}")

    code, beats = http("GET", "/api/beats?segment=S001")
    if code != 200 or len(beats.get("beats", [])) != 35:
        failures.append(f"T beats expected 35 got {len(beats.get('beats', []))}")

    if beats.get("beats"):
        b0 = beats["beats"][0]
        if "planned_sec" not in b0 or "cps_band" not in b0:
            failures.append("T10 beats missing planned_sec/cps_band fields")

    code, reject = http("POST", "/api/assets/icon_video/review", {"status": "rejected", "note": "test reject"})
    if code != 200:
        failures.append("T4 reject svg failed")
    code, reg = http("GET", "/api/registry")
    stale_paths = [r.get("path") for r in reg.get("artifacts", []) if r.get("status") == "stale"]
    if not any("render.mp4" in (p or "") for p in stale_paths):
        failures.append(f"T4 render.mp4 not stale: {stale_paths[:5]}")
    code, project2 = http("GET", "/api/project")
    if not project2.get("render_blocked"):
        failures.append("T4 render should be blocked after reject")

    http("POST", "/api/regen-queue", {
        "target_artifact_id": "asset:icon_video",
        "action": "regenerate_svg",
        "reason": "test",
        "commands_suggested": ["echo test"],
    })
    t5 = run([sys.executable, str(SCRIPTS / "regen_dispatch.py"), str(PROJECT), "--dry-run"])
    if "Pending queue items: 0" in t5.stdout:
        failures.append("T5 regen_dispatch should list queue items")

    t6 = run([sys.executable, str(SCRIPTS / "segment_timing_lint.py"), str(PROJECT), "S001"])
    if t6.returncode != 0 or "97" not in t6.stdout:
        failures.append(f"T6 lint score unexpected: {t6.stdout[:120]}")

    build_script = PROJECT / "scripts" / "build_s001_composition.py"
    if build_script.exists():
        t7 = run([sys.executable, str(build_script)], cwd=PROJECT)
        if t7.returncode != 0:
            failures.append(f"T7 build composition failed: {t7.stderr[:200]}")

    code, patch = http("PATCH", "/api/beats/B023?segment=S001", {"narration": "测试口播修改 B023"})
    if code != 200 or not patch.get("stale", {}).get("impacted_stages"):
        failures.append("T3 beat patch stale chain failed")
    restore()
    state_path.write_text(backup, encoding="utf-8")

    code, tts = http("GET", "/api/tts/health")
    if code != 200 or "available" not in tts:
        failures.append("T11 tts health endpoint failed")

    code, summary = http("GET", "/api/audio/summary?segment=S001")
    if code != 200 or summary.get("beat_count") != 35:
        failures.append(f"T12 audio summary failed: {summary}")

    code, preset = http("POST", "/api/jobs/preset/audio_chain?segment=S001")
    if code != 200 or not preset.get("job", {}).get("id"):
        failures.append("T13 audio_chain preset failed")
    else:
        job = wait_job(preset["job"]["id"])
        if job.get("status") != "completed":
            failures.append(f"T13 audio_chain job failed: {job.get('stderr_tail', '')[:200]}")

    code, timing = http("PATCH", "/api/timing/beats/B001?segment=S001", {"duration_sec": 4.5, "locked": True})
    if code != 200 or not timing.get("vo_timing"):
        failures.append("T14 timing patch failed")
    if vo_backup:
        vo_path.write_text(vo_backup, encoding="utf-8")

    code, stage_art = http("GET", "/api/stages/script/artifacts?segment=S001")
    if code != 200 or not stage_art.get("artifacts"):
        failures.append("T15 stage artifacts failed")

    code, vo = http("GET", "/api/script/voiceover")
    if code != 200 or not vo.get("content"):
        failures.append("T16 voiceover read failed")

    code, art = http("GET", "/api/artifacts/script/narration_beats.csv")
    if code != 200 or art.get("content") is None:
        failures.append("T17 artifact read failed")

    code, jobs = http("GET", "/api/jobs?limit=5")
    if code != 200 or "jobs" not in jobs:
        failures.append("T18 jobs list failed")

    ac = run([sys.executable, str(SCRIPTS / "audio_chain.py"), str(PROJECT), "S001", "--skip-tts"])
    if ac.returncode != 0:
        failures.append(f"T19 audio_chain CLI failed: {ac.stderr[:200]}")

    code, beat_detail = http("GET", "/api/beats/B001?segment=S001")
    if code != 200 or not beat_detail.get("micro_events"):
        failures.append("T20 beat detail micro_events missing")

    if shutil.which("npx"):
        try:
            hf = run(["npx", "hyperframes", "lint", "."], cwd=PROJECT / "segments" / "S001")
            if hf.returncode != 0:
                failures.append(f"T8 hyperframes lint failed: {hf.stderr[:200]}")
        except FileNotFoundError:
            print("skip T8: npx execution failed")
    else:
        print("skip T8: npx not found")

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()

    restore()

    if failures:
        print("FAILED:")
        for item in failures:
            print("-", item)
        return 1
    print("All tests passed (T1-T20).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
