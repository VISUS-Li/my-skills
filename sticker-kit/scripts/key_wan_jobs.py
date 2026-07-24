#!/usr/bin/env python3
"""批量把每个已生成 Wan 任务视频转到计划的 RGBA 目录。"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def main() -> None:
    ap = argparse.ArgumentParser(description="Batch key outputs described by wan_jobs.json")
    ap.add_argument("jobs", type=Path)
    ap.add_argument("--only", action="append", default=[])
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()

    doc = json.loads(args.jobs.read_text(encoding="utf-8"))
    root = args.jobs.parent.resolve()
    cutout = Path(__file__).resolve().with_name("cutout_video.py")
    selected = [j for j in doc.get("jobs", []) if not args.only or j["id"] in args.only]
    if not selected:
        raise SystemExit("no matching jobs")

    for index, job in enumerate(selected, start=1):
        video = resolve(root, job["output"])
        out = resolve(root, job["rgba_dir"])
        if not video.exists():
            raise SystemExit(f"missing raw video for {job['id']}: {video}")
        report = out / "key_report.json"
        if report.exists() and not args.force:
            print(f"[{index}/{len(selected)}] skip {job['id']} (key report exists)")
            continue
        matte = job.get("matte") or {"mode": "chroma", "color": "#00FF00"}
        command = [
            args.python,
            str(cutout),
            str(video),
            "-o",
            str(out),
            "--mode",
            str(matte.get("mode", "chroma")),
            "--pixel-grid",
            str(job.get("pixel_grid", 1)),
        ]
        if matte.get("mode", "chroma") == "chroma":
            command += ["--key-color", str(matte.get("color", "#00FF00"))]
        print(f"[{index}/{len(selected)}] key {job['id']}")
        subprocess.run(command, check=True)
    print(f"OK processed {len(selected)} job(s)")


if __name__ == "__main__":
    main()
