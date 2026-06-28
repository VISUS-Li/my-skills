#!/usr/bin/env python3
"""Run audio alignment chain: TTS (optional) -> measure -> micro_timing -> lint [-> build]."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def run_step(label: str, cmd: list[str], *, cwd: Path | None = None) -> int:
    print(f"\n==> {label}")
    print(" ".join(cmd))
    proc = subprocess.run(cmd, cwd=cwd or Path.cwd())
    if proc.returncode != 0:
        print(f"FAILED: {label} (exit {proc.returncode})", file=sys.stderr)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run VO alignment chain for a segment.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("segment_id", nargs="?", default="S001", help="Segment id e.g. S001")
    parser.add_argument("--skip-tts", action="store_true", help="Skip IndexTTS generation")
    parser.add_argument("--beats", nargs="*", help="Only regenerate these beat_ids via TTS")
    parser.add_argument("--force-tts", action="store_true", help="Force TTS regen even if WAV exists")
    parser.add_argument("--skip-lint", action="store_true")
    parser.add_argument("--build", action="store_true", help="Run composition builder after timing")
    parser.add_argument("--base-url", default=None, help="IndexTTS2 base URL override")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    seg = args.segment_id.upper()
    py = sys.executable

    if not args.skip_tts:
        tts_cmd = [py, str(SCRIPTS / "indextts2_generate.py"), str(root), "--segment", seg, "--concat"]
        if args.beats:
            tts_cmd.extend(["--beats", *args.beats])
        if args.force_tts:
            tts_cmd.append("--force")
        if args.base_url:
            tts_cmd.extend(["--base-url", args.base_url])
        if run_step("IndexTTS2 generate", tts_cmd) != 0:
            return 1

    if run_step("Measure VO", [py, str(SCRIPTS / "measure_segment_vo.py"), str(root), seg]) != 0:
        return 1

    if run_step("Build micro timing", [py, str(SCRIPTS / "build_micro_timing.py"), str(root), seg]) != 0:
        return 1

    if not args.skip_lint:
        if run_step("Segment timing lint", [py, str(SCRIPTS / "segment_timing_lint.py"), str(root), seg]) != 0:
            return 1

    if args.build:
        build = root / "scripts" / f"build_{seg.lower()}_composition.py"
        if not build.exists():
            print(f"skip build: {build} not found", file=sys.stderr)
        elif run_step("Build composition", [py, str(build)], cwd=root) != 0:
            return 1

    print(f"\nAudio chain complete for {seg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
