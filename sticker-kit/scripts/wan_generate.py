#!/usr/bin/env python3
"""Execute compiled Wan I2V / FLF2V jobs and save reproducible metadata."""
from __future__ import annotations

import argparse
import json
import os
from contextlib import ExitStack
from pathlib import Path
from urllib.parse import urljoin

import requests


def resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def run_job(job: dict, root: Path, base_url: str, timeout: int, force: bool) -> dict:
    output = resolve(root, job["output"])
    metadata = output.with_suffix(".json")
    if output.exists() and not force:
        return {"id": job["id"], "status": "skipped", "output": str(output)}

    mode = job["mode"]
    endpoint = "/generate/flf2v" if mode == "flf2v" else "/generate/i2v"
    image_fields = (
        {"start_image": job["start_image"], "end_image": job["end_image"]}
        if mode == "flf2v"
        else {"image": job["start_image"]}
    )
    for field, value in image_fields.items():
        path = resolve(root, value)
        if not path.exists():
            raise FileNotFoundError(f"{job['id']}: missing {field}: {path}")

    data = {
        key: job[key]
        for key in (
            "prompt",
            "negative_prompt",
            "width",
            "height",
            "length",
            "fps",
            "steps",
            "cfg",
            "seed",
        )
        if key in job and job[key] not in (None, "")
    }
    with ExitStack() as stack:
        files = {
            field: stack.enter_context(resolve(root, value).open("rb"))
            for field, value in image_fields.items()
        }
        response = requests.post(
            base_url.rstrip("/") + endpoint,
            files=files,
            data=data,
            timeout=timeout,
        )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") not in (None, "succeeded"):
        raise RuntimeError(f"{job['id']}: Wan returned {payload}")
    video_url = payload.get("video_url")
    if not video_url:
        raise RuntimeError(f"{job['id']}: response has no video_url: {payload}")

    output.parent.mkdir(parents=True, exist_ok=True)
    video_response = requests.get(urljoin(base_url.rstrip("/") + "/", video_url.lstrip("/")), timeout=timeout)
    video_response.raise_for_status()
    output.write_bytes(video_response.content)
    record = {
        "job": job,
        "request_url": base_url.rstrip("/") + endpoint,
        "response": payload,
        "output": str(output.resolve()),
        "bytes": output.stat().st_size,
    }
    metadata.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"id": job["id"], "status": "succeeded", "output": str(output)}


def main() -> None:
    ap = argparse.ArgumentParser(description="Run Wan jobs from wan_jobs.json")
    ap.add_argument("jobs", type=Path)
    ap.add_argument("--base-url", default=None, help="Overrides WAN_BASE_URL and job file")
    ap.add_argument("--only", action="append", default=[], help="Run only matching job id; repeatable")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    doc = json.loads(args.jobs.read_text(encoding="utf-8"))
    root = args.jobs.parent.resolve()
    base_url = args.base_url or os.environ.get("WAN_BASE_URL") or doc.get("base_url")
    if not base_url:
        raise SystemExit("missing base URL; use --base-url or WAN_BASE_URL")
    selected = [j for j in doc.get("jobs", []) if not args.only or j["id"] in args.only]
    if not selected:
        raise SystemExit("no matching jobs")

    if args.dry_run:
        preview = []
        for job in selected:
            preview.append(
                {
                    "id": job["id"],
                    "mode": job["mode"],
                    "endpoint": "/generate/flf2v" if job["mode"] == "flf2v" else "/generate/i2v",
                    "start_image": job.get("start_image"),
                    "end_image": job.get("end_image"),
                    "length": job.get("length"),
                    "fps": job.get("fps"),
                    "output": job.get("output"),
                }
            )
        print(json.dumps({"base_url": base_url, "jobs": preview}, ensure_ascii=False, indent=2))
        return

    results = []
    for index, job in enumerate(selected, start=1):
        print(f"[{index}/{len(selected)}] {job['id']} ({job['mode']})")
        results.append(run_job(job, root, base_url, args.timeout, args.force))
        print(f"  {results[-1]['status']} → {results[-1]['output']}")
    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
