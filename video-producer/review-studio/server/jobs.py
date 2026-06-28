#!/usr/bin/env python3
"""Background job runner for Review Studio."""
from __future__ import annotations

import subprocess
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


@dataclass
class JobRecord:
    id: str
    script: str
    args: list[str]
    cwd: str
    label: str = ""
    status: str = "queued"
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str | None = None


class JobRunner:
    def __init__(self, on_event: Callable[[dict[str, Any]], None] | None = None) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = threading.Lock()
        self._on_event = on_event

    def _emit(self, payload: dict[str, Any]) -> None:
        if self._on_event:
            self._on_event(payload)

    def create(self, script: str, args: list[str], cwd: Path, *, label: str = "") -> JobRecord:
        job = JobRecord(id=str(uuid.uuid4()), script=script, args=args, cwd=str(cwd), label=label)
        with self._lock:
            self._jobs[job.id] = job
        self._emit({"type": "job_progress", "job_id": job.id, "status": "queued"})
        thread = threading.Thread(target=self._run, args=(job.id,), daemon=True)
        thread.start()
        return job

    def _run(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = "running"
        self._emit({"type": "job_progress", "job_id": job_id, "status": "running"})
        cmd = [job.script, *job.args]
        try:
            proc = subprocess.run(
                cmd,
                cwd=job.cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            with self._lock:
                job.stdout = proc.stdout
                job.stderr = proc.stderr
                job.exit_code = proc.returncode
                job.status = "completed" if proc.returncode == 0 else "failed"
                job.completed_at = datetime.now(timezone.utc).isoformat()
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                job.stderr = str(exc)
                job.exit_code = 1
                job.status = "failed"
                job.completed_at = datetime.now(timezone.utc).isoformat()
        self._emit({"type": "job_progress", "job_id": job_id, "status": job.status, "exit_code": job.exit_code})

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self, limit: int = 50) -> list[JobRecord]:
        with self._lock:
            jobs = sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    def to_dict(self, job: JobRecord) -> dict[str, Any]:
        return {
            "id": job.id,
            "label": job.label,
            "script": job.script,
            "args": job.args,
            "cwd": job.cwd,
            "status": job.status,
            "exit_code": job.exit_code,
            "stdout_tail": job.stdout[-4000:],
            "stderr_tail": job.stderr[-4000:],
            "created_at": job.created_at,
            "completed_at": job.completed_at,
        }
