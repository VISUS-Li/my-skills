#!/usr/bin/env python3
"""Run audio alignment chain: TTS (optional) -> measure -> micro_timing -> lint [-> build]."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from indextts2_connect import load_base_url  # noqa: E402
from segment_timing_lint import lint_segment  # noqa: E402
from sync_segment_duration import sync_segment_duration  # noqa: E402
from tts_progress import patch_progress, read_progress, write_progress  # noqa: E402


def run_step(label: str, cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    print(f"\n==> {label}")
    print(" ".join(cmd))
    proc = subprocess.run(
        cmd,
        cwd=cwd or Path.cwd(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.stderr:
        print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n", file=sys.stderr)
    if proc.returncode != 0:
        print(f"FAILED: {label} (exit {proc.returncode})", file=sys.stderr)
    return proc


def tts_failure_details(root: Path, proc: subprocess.CompletedProcess[str]) -> tuple[str, str | None]:
    prog = read_progress(root, max_running_age_sec=999999)
    err = prog.get("error")
    msg = prog.get("message")
    if err:
        return str(err), str(err)
    if msg and msg not in {"IndexTTS 配音失败", "queued"}:
        return str(msg), None
    tail = (proc.stderr or proc.stdout or "").strip().splitlines()
    if tail:
        return tail[-1][:240], None
    return "IndexTTS 配音失败", None


def chain_progress(root: Path, seg: str, *, phase: str, message: str, percent: int, status: str = "running") -> None:
    write_progress(root, {
        "status": status,
        "phase": phase,
        "message": message,
        "percent": percent,
        "segment_id": seg,
        "done": 0,
        "total": 0,
    })


def lint_issue_summary(issues: list[dict[str, object]], *, limit: int = 3) -> str:
    return "; ".join(str(i.get("message", "")) for i in issues[:limit] if i.get("message"))


def lint_progress_fields(result: dict) -> dict:
    return {
        "lint_score": result["score"],
        "lint_fail_under": result["fail_under"],
        "lint_issues": result["issues"],
        "lint_report": result["report_path"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run VO alignment chain for a segment.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("segment_id", nargs="?", default="S001", help="Segment id e.g. S001")
    parser.add_argument("--skip-tts", action="store_true", help="Skip IndexTTS generation")
    parser.add_argument("--beats", nargs="*", help="Only regenerate these beat_ids via TTS")
    parser.add_argument("--force-tts", action="store_true", help="Force TTS regen even if WAV exists")
    parser.add_argument("--skip-lint", action="store_true")
    parser.add_argument("--skip-sync", action="store_true", help="Skip syncing index.html duration before lint")
    parser.add_argument("--fail-under", type=int, default=80, help="Lint score threshold")
    parser.add_argument("--build", action="store_true", help="Run composition builder after timing")
    parser.add_argument("--base-url", default=None, help="IndexTTS2 base URL override")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    seg = args.segment_id.upper()
    py = sys.executable
    base_url = load_base_url(root, args.base_url)

    if not args.skip_tts:
        chain_progress(root, seg, phase="tts", message=f"IndexTTS 配音链启动 → {base_url}", percent=2)
        tts_cmd = [py, str(SCRIPTS / "indextts2_generate.py"), str(root), "--segment", seg, "--concat"]
        if args.beats:
            tts_cmd.extend(["--beats", *args.beats])
        if args.force_tts:
            tts_cmd.append("--force")
        tts_cmd.extend(["--base-url", base_url])
        tts_proc = run_step("IndexTTS2 generate", tts_cmd)
        if tts_proc.returncode != 0:
            message, error = tts_failure_details(root, tts_proc)
            patch_progress(
                root,
                status="failed",
                phase="tts",
                message=message,
                percent=read_progress(root, max_running_age_sec=999999).get("percent", 0),
                error=error or message,
            )
            return 1

    chain_progress(root, seg, phase="measure", message="测量实测时长…", percent=72)
    if run_step("Measure VO", [py, str(SCRIPTS / "measure_segment_vo.py"), str(root), seg]).returncode != 0:
        patch_progress(root, status="failed", phase="measure", message="测量时长失败", percent=72)
        return 1

    chain_progress(root, seg, phase="micro", message="对齐微事件…", percent=82)
    if run_step("Build micro timing", [py, str(SCRIPTS / "build_micro_timing.py"), str(root), seg]).returncode != 0:
        patch_progress(root, status="failed", phase="micro", message="微事件对齐失败", percent=82)
        return 1

    if not args.skip_sync:
        sync = sync_segment_duration(root, seg)
        if sync.get("synced"):
            msg = f"已同步合成页时长 {sync['previous_sec']}→{sync['total_sec']}"
            print(msg)
            chain_progress(root, seg, phase="sync", message=msg, percent=88)

    if not args.skip_lint:
        chain_progress(root, seg, phase="lint", message="时长质检…", percent=90)
        result = lint_segment(
            root,
            seg,
            fail_under=args.fail_under,
            audio_only=not (root / "segments" / seg / "index.html").exists(),
        )
        print(f"Segment timing score: {result['score']}")
        for item in result["issues"]:
            print(f"- (-{item['penalty']}) {item['message']}")
        lint_fields = lint_progress_fields(result)
        if not result["passed"]:
            summary = lint_issue_summary(result["issues"])
            patch_progress(
                root,
                status="failed",
                phase="lint",
                message=f"时长质检 {result['score']}/{args.fail_under} 未通过 · {summary}",
                percent=90,
                **lint_fields,
            )
            return 1
        patch_progress(
            root,
            status="running",
            phase="lint",
            message=f"时长质检通过 {result['score']}/{args.fail_under}",
            percent=92,
            **lint_fields,
        )

    if args.build:
        build = root / "scripts" / f"build_{seg.lower()}_composition.py"
        if not build.exists():
            print(f"skip build: {build} not found", file=sys.stderr)
        else:
            chain_progress(root, seg, phase="build", message="重建合成页…", percent=95)
            if run_step("Build composition", [py, str(build)], cwd=root).returncode != 0:
                patch_progress(root, status="failed", phase="build", message="重建合成失败", percent=95)
                return 1

    write_progress(root, {
        "status": "completed",
        "phase": "completed",
        "message": f"音频链完成 · {seg}",
        "percent": 100,
        "segment_id": seg,
    })
    print(f"\nAudio chain complete for {seg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
