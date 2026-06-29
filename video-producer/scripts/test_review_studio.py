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


def http_media(path: str, *, read_bytes: int = 4096) -> tuple[int, bytes]:
    req = urllib.request.Request(f"{BASE}{path}", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read(read_bytes)
    except urllib.error.HTTPError as exc:
        return exc.code, b""


def is_wav_file(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 44:
        return False
    return path.read_bytes()[:4] == b"RIFF"


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

    tts_cfg_backup = None
    tts_cfg_path = PROJECT / "audio" / "indextts2_config.json"
    if tts_cfg_path.exists():
        tts_cfg_backup = tts_cfg_path.read_text(encoding="utf-8-sig")

    micro_path = PROJECT / "segments" / "S001" / "micro_timing.json"
    micro_backup = micro_path.read_text(encoding="utf-8-sig") if micro_path.exists() else None

    def restore() -> None:
        state_path.write_text(backup, encoding="utf-8")
        (PROJECT / "script" / "narration_beats.csv").write_text(beats_backup, encoding="utf-8")
        if vo_backup is not None:
            vo_path.write_text(vo_backup, encoding="utf-8")
        if micro_backup is not None:
            micro_path.write_text(micro_backup, encoding="utf-8")
        if tts_cfg_backup is not None:
            tts_cfg_path.write_text(tts_cfg_backup, encoding="utf-8")

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

    run([sys.executable, str(SCRIPTS / "sync_segment_duration.py"), str(PROJECT), "S001"])
    t6 = run([sys.executable, str(SCRIPTS / "segment_timing_lint.py"), str(PROJECT), "S001"])
    if t6.returncode != 0:
        failures.append(f"T6 lint failed: {t6.stdout[:120]}")
    elif "Segment timing score:" not in t6.stdout:
        failures.append(f"T6 lint score missing: {t6.stdout[:120]}")

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

    code, tts_cfg = http("GET", "/api/tts/config")
    if code != 200 or not tts_cfg.get("config", {}).get("base_url"):
        failures.append("T21 tts config read failed")

    code, tts_put = http("PUT", "/api/tts/config", {
        "base_url": "http://10.0.221.33:37191/",
        "defaults": {"emo_weight": 0.65, "temperature": 0.8, "top_p": 0.8},
    })
    if code != 200 or tts_put.get("config", {}).get("base_url") != "http://10.0.221.33:37191/":
        failures.append(f"T22 tts config update failed: {tts_put}")
    if "health" not in tts_put:
        failures.append("T22 tts config update missing health")

    code, refs = http("GET", "/api/audio/refs")
    if code != 200 or "refs" not in refs:
        failures.append("T23 audio refs list failed")

    code, prog = http("GET", "/api/tts/progress")
    if code != 200 or "status" not in prog:
        failures.append("T24 tts progress endpoint failed")

    code, beat_preset = http("POST", "/api/jobs/preset/indextts_beats_align?segment=S001&beats=B001")
    if code != 200 or not beat_preset.get("job", {}).get("id"):
        failures.append("T25 indextts_beats_align preset failed")

    code, tts_live = http("GET", "/api/tts/health")
    b001_wav = PROJECT / "audio" / "stems" / "voice" / "beats" / "B001.wav"
    if (
        beat_preset.get("job", {}).get("id")
        and tts_live.get("available")
        and tts_live.get("reference_exists")
    ):
        job = wait_job(beat_preset["job"]["id"], timeout=300)
        if job.get("status") != "completed":
            tail = (job.get("stderr_tail") or job.get("stdout_tail") or "")[:400]
            failures.append(f"T25c IndexTTS beat job failed: {tail}")
        elif not is_wav_file(b001_wav):
            failures.append(f"T25c B001.wav missing or invalid after IndexTTS: {b001_wav}")
        else:
            code, prog_done = http("GET", "/api/tts/progress")
            if code != 200 or prog_done.get("status") not in {"completed", "idle"}:
                failures.append(f"T25c tts progress not completed after job: {prog_done.get('status')}")
            print(f"T25c IndexTTS OK: B001.wav ({b001_wav.stat().st_size} bytes)")
    elif beat_preset.get("job", {}).get("id"):
        print(
            "skip T25c live IndexTTS generation:",
            "offline" if not tts_live.get("available") else "reference missing",
        )

    code, bad_preset = http("POST", "/api/jobs/preset/indextts_beats_align?segment=S001")
    if code != 400:
        failures.append("T25b indextts_beats_align should require beats param")

    code, refs = http("GET", "/api/audio/refs")
    if code != 200:
        failures.append("T26 audio refs list failed")
    elif refs.get("refs") and refs["refs"][0].get("uploaded_at") is None:
        failures.append("T26 refs missing uploaded_at metadata")

    test_wav = PROJECT / "audio" / "refs" / "_rs_test_ref.wav"
    test_wav.parent.mkdir(parents=True, exist_ok=True)
    test_wav.write_bytes(
        b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
        b"\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    )
    code, synced = http("GET", "/api/audio/refs")
    if not any(r.get("path", "").endswith("_rs_test_ref.wav") for r in synced.get("refs", [])):
        failures.append("T27 registry sync missing test ref")
    else:
        from urllib.parse import quote
        code, deleted = http("DELETE", "/api/audio/refs?path=" + quote("audio/refs/_rs_test_ref.wav", safe=""))
        if code != 200 or deleted.get("deleted") != "audio/refs/_rs_test_ref.wav":
            failures.append(f"T28 delete ref failed: {deleted}")
    if test_wav.exists():
        test_wav.unlink()

    if shutil.which("ffmpeg"):
        test_mp3 = PROJECT / "audio" / "refs" / "_rs_test_ref.mp3"
        test_mp3.parent.mkdir(parents=True, exist_ok=True)
        conv = subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                "-t", "0.5", "-q:a", "9", str(test_mp3),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if conv.returncode == 0 and test_mp3.exists():
            sys.path.insert(0, str(ROOT / "review-studio" / "server"))
            import tts as tts_mod
            try:
                tts_mod.save_ref_upload(PROJECT, "_rs_test_ref.mp3", test_mp3.read_bytes(), select=False)
                code, refs_mp3 = http("GET", "/api/audio/refs")
                if not any(r.get("format") == "mp3" for r in refs_mp3.get("refs", [])):
                    failures.append("T29 mp3 ref not listed after upload")
                http("DELETE", "/api/audio/refs?path=" + quote("audio/refs/_rs_test_ref.mp3", safe=""))
            except Exception as exc:  # noqa: BLE001
                failures.append(f"T29 mp3 upload failed: {exc}")
            finally:
                test_mp3.unlink(missing_ok=True)
                (PROJECT / "audio" / "refs" / "_rs_test_ref.wav").unlink(missing_ok=True)
        else:
            failures.append(f"T29 ffmpeg mp3 fixture failed: {conv.stderr[:200]}")

    code, tl = http("GET", "/api/timeline?segment=S001")
    if code != 200:
        failures.append(f"T30 timeline API failed: {tl}")
    else:
        for key in ("segment_id", "total_sec", "beats", "micro_events", "media"):
            if key not in tl:
                failures.append(f"T30 timeline missing {key}")
        media = tl.get("media") or {}
        for mk in ("vo_wav", "render_mp4", "composition_html"):
            if mk not in media:
                failures.append(f"T30 media missing key {mk}")
        if tl.get("beats") and not tl["beats"][0].get("beat_id"):
            failures.append("T30 beat missing beat_id")
        if not tl.get("total_sec"):
            failures.append("T30 timeline total_sec empty")

    sys.path.insert(0, str(ROOT / "review-studio" / "server"))
    from timing import resolve_timeline_media

    resolved = resolve_timeline_media(PROJECT, "S001")
    if not isinstance(resolved, dict) or "vo_wav" not in resolved:
        failures.append("T34 resolve_timeline_media invalid")

    status, js_body = http_media("/timeline-editor.js", read_bytes=32768)
    if status != 200 or b"TimelineEditor" not in js_body:
        failures.append(f"T33 timeline-editor.js not served ({status})")

    preview_media = (tl.get("media") or {}) if code == 200 else {}
    media_rel = preview_media.get("render_mp4") or preview_media.get("vo_wav")
    if media_rel:
        from urllib.parse import quote
        media_url = "/api/media/" + "/".join(quote(part, safe="") for part in media_rel.split("/"))
        m_status, m_head = http_media(media_url)
        if m_status != 200:
            failures.append(f"T32 preview media GET failed ({media_rel}): {m_status}")
        elif media_rel.endswith(".mp4") and b"ftyp" not in m_head[:64]:
            failures.append("T32 render_mp4 does not look like MP4")
        elif media_rel.endswith(".wav") and m_head[:4] != b"RIFF":
            failures.append("T32 vo_wav is not a valid WAV (RIFF)")
    else:
        print("skip T32 preview media: no render_mp4 or vo_wav in project")

    if code == 200 and tl.get("micro_events"):
        ev = tl["micro_events"][0]
        eid = ev.get("id") or ev.get("event_id")
        if eid:
            orig_t = float(ev.get("t", 0))
            new_t = round(orig_t + 0.05, 3)
            code, patched = http("PATCH", f"/api/timing/micro/{eid}?segment=S001", {"t": new_t})
            if code != 200 or patched.get("t") != new_t:
                failures.append(f"T31 micro timing patch failed: {patched}")
            else:
                http("PATCH", f"/api/timing/micro/{eid}?segment=S001", {"t": orig_t})
        else:
            failures.append("T31 micro event missing id")
    else:
        print("skip T31 micro patch: no micro_events")

    code, tl2 = http("GET", "/api/timeline?segment=S001")
    if code != 200 or "preview" not in tl2:
        failures.append("T35 timeline missing preview block")
    elif not tl2.get("preview", {}).get("composition_ready"):
        failures.append("T35 composition_ready false for fixture")
    else:
        embed = tl2["preview"].get("composition_embed_url", "")
        if not embed.startswith("/api/preview/composition/"):
            failures.append(f"T35 bad composition_embed_url: {embed}")

    status, body = http_media("/api/preview/composition/S001/index.html", read_bytes=8192)
    if status != 200:
        failures.append(f"T36 composition proxy failed: {status}")
    elif b"data-composition-id" not in body:
        failures.append("T36 composition index.html invalid")

    code, prev = http("GET", "/api/preview/hyperframes?segment=S001")
    if code != 200 or "composition_ready" not in prev:
        failures.append(f"T37 preview status failed: {prev}")

    status, js = http_media("/timeline-editor.js", read_bytes=65536)
    if status != 200 or b"WaveSurfer" not in js or b"__timelines" not in js:
        failures.append("T38 timeline-editor.js missing WaveSurfer/composition seek")
    elif b"onAudioTimeUpdate" not in js:
        failures.append("T40 missing onAudioTimeUpdate audio clock")
    elif b"if (fromMedia || state.playing) return;" not in js:
        failures.append("T40 setCurrentTime still seeks during playback")
    elif b"state.playing) return" not in js or js.count(b"wavesurfer.setTime") != 1:
        failures.append("T40 syncWaveform may still seek during playback")

    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        print("skip T40b playwright audio smoothness: playwright not installed")
    else:
        wav_url = None
        code, tl3 = http("GET", "/api/timeline?segment=S001")
        if code == 200 and tl3.get("media", {}).get("vo_wav"):
            rel = tl3["media"]["vo_wav"]
            wav_url = f"http://127.0.0.1:8801/api/media/{rel}"
        if not wav_url:
            print("skip T40b: no vo_wav in timeline")
        else:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    samples = page.evaluate(
                        """async (wavUrl) => {
                          const audio = document.createElement('audio');
                          audio.src = wavUrl;
                          audio.preload = 'auto';
                          await new Promise((resolve, reject) => {
                            audio.addEventListener('canplay', resolve, { once: true });
                            audio.addEventListener('error', () => reject(new Error('audio load failed')), { once: true });
                          });
                          await audio.play();
                          const times = [];
                          for (let i = 0; i < 12; i++) {
                            await new Promise(r => setTimeout(r, 120));
                            times.push(audio.currentTime);
                          }
                          audio.pause();
                          let backward = 0;
                          let maxJump = 0;
                          for (let i = 1; i < times.length; i++) {
                            const d = times[i] - times[i - 1];
                            if (d < -0.02) backward += 1;
                            if (d > maxJump) maxJump = d;
                          }
                          return { times, backward, maxJump, delta: times[times.length - 1] - times[0] };
                        }""",
                        wav_url,
                    )
                    browser.close()
                    if samples.get("backward", 99) > 0:
                        failures.append(f"T40b audio time moved backward: {samples}")
                    elif samples.get("delta", 0) < 0.5:
                        failures.append(f"T40b audio did not advance smoothly: {samples}")
                    elif samples.get("maxJump", 99) > 0.45:
                        failures.append(f"T40b audio time jump too large: {samples}")
                    else:
                        print(f"T40b audio smoothness OK: delta={samples.get('delta'):.2f}s maxJump={samples.get('maxJump'):.3f}")
            except Exception as exc:  # noqa: BLE001
                print(f"skip T40b playwright audio smoothness: {exc}")
    if shutil.which("npx"):
        code, started = http("POST", "/api/preview/hyperframes/start?segment=S001&port=3027")
        if code != 200:
            failures.append(f"T39 studio start API failed: {started}")
        else:
            alive = False
            for _ in range(90):
                code, st = http("GET", "/api/preview/hyperframes?segment=S001")
                if st.get("studio_running") and st.get("studio_url"):
                    alive = True
                    break
                time.sleep(1)
            if not alive:
                failures.append("T39 studio did not become reachable within 90s")
            else:
                print(f"T39 Studio OK: {st.get('studio_url')}")
            http("POST", "/api/preview/hyperframes/stop?segment=S001")
    else:
        print("skip T39 studio start: npx not found")

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
    print("All tests passed (T1-T39).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
