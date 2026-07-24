#!/usr/bin/env python3
"""执行已编译的 Wan I2V/FLF2V 任务并保存可复现元数据。"""
from __future__ import annotations

import argparse
import json
import os
import time
from contextlib import ExitStack
from pathlib import Path
from urllib.parse import urljoin

import requests


def resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def preflight_health(base_url: str, timeout: int) -> str:
    """Fail fast when Wan is unreachable; tolerate deployments without /health."""
    url = base_url.rstrip("/") + "/health"
    try:
        response = requests.get(url, timeout=min(timeout, 15))
    except requests.RequestException as exc:
        raise RuntimeError(f"Wan preflight failed: {url}: {exc}") from exc
    if response.status_code in (404, 405):
        return f"health endpoint unsupported ({response.status_code}); generation endpoint not probed"
    if response.status_code >= 400:
        raise RuntimeError(f"Wan health failed: {url}: HTTP {response.status_code}")
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if isinstance(payload, dict):
        status = str(payload.get("status") or "").lower()
        if payload.get("ok") is False or status in {"down", "error", "failed", "unhealthy"}:
            raise RuntimeError(f"Wan health reported unavailable: {payload}")
    return f"health OK: HTTP {response.status_code}"


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
            headers={"Connection": "close"},
        )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") not in (None, "succeeded"):
        raise RuntimeError(f"{job['id']}: Wan returned {payload}")
    video_url = payload.get("video_url")
    if not video_url:
        raise RuntimeError(f"{job['id']}: response has no video_url: {payload}")

    # Give the API a moment to rebind after a long generate response.
    time.sleep(2.0)
    output.parent.mkdir(parents=True, exist_ok=True)
    download_url = urljoin(base_url.rstrip("/") + "/", video_url.lstrip("/"))
    video_response = None
    download_error: Exception | None = None
    for download_attempt in range(8):
        try:
            # Fresh connection — long generate responses often leave the socket unusable.
            video_response = requests.get(
                download_url,
                timeout=min(timeout, 300),
                headers={"Connection": "close"},
            )
            video_response.raise_for_status()
            if not video_response.content:
                raise RuntimeError(f"{job['id']}: downloaded video is empty")
            break
        except (requests.RequestException, RuntimeError) as exc:
            download_error = exc
            wait_sec = 2.0 * (download_attempt + 1)
            print(
                f"  download attempt {download_attempt + 1} failed: {exc}; "
                f"retry in {wait_sec:.1f}s",
                flush=True,
            )
            time.sleep(wait_sec)
            video_response = None
    if video_response is None:
        raise RuntimeError(
            f"{job['id']}: video download failed after generate succeeded "
            f"({payload.get('job_id')}: {video_url}): {download_error}"
        )
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
    ap.add_argument("--retries", type=int, default=2, help="Retries per failed network/generation call")
    ap.add_argument("--retry-wait", type=float, default=3.0)
    ap.add_argument("--continue-on-error", action="store_true")
    ap.add_argument("--skip-health", action="store_true")
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

    if not args.skip_health:
        try:
            print(preflight_health(base_url, args.timeout))
        except RuntimeError as exc:
            raise SystemExit(
                f"{exc}\nNo jobs were started. Restore Wan or re-plan the affected shot; "
                "do not replace narrative actor states with static images."
            ) from exc

    results = []
    report_path = root / "wan_run_report.json"
    for index, job in enumerate(selected, start=1):
        print(f"[{index}/{len(selected)}] {job['id']} ({job['mode']})")
        result = None
        for attempt in range(args.retries + 1):
            try:
                result = run_job(job, root, base_url, args.timeout, args.force)
                break
            except FileNotFoundError:
                raise
            except (requests.RequestException, RuntimeError, ValueError) as exc:
                if attempt >= args.retries:
                    result = {
                        "id": job["id"],
                        "status": "failed",
                        "attempts": attempt + 1,
                        "error": str(exc),
                    }
                    break
                wait_sec = max(0.0, args.retry_wait) * (attempt + 1)
                print(f"  attempt {attempt + 1} failed: {exc}; retry in {wait_sec:.1f}s")
                time.sleep(wait_sec)
        assert result is not None
        results.append(result)
        report = {
            "base_url": base_url,
            "source_jobs": str(args.jobs.resolve()),
            "complete": len(results) == len(selected) and all(r["status"] != "failed" for r in results),
            "results": results,
        }
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        if result["status"] == "failed":
            print(f"  FAILED after {result['attempts']} attempt(s): {result['error']}")
            if not args.continue_on_error:
                raise SystemExit(
                    f"Wan run stopped; partial outputs are recorded in {report_path}. "
                    "Rerun to resume completed jobs after service recovery."
                )
        else:
            print(f"  {result['status']} → {result['output']}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if any(result["status"] == "failed" for result in results):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
