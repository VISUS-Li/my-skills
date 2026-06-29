#!/usr/bin/env python3
"""IndexTTS2 connectivity helpers."""
from __future__ import annotations

import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from pathlib import Path

try:
    from gradio_client import Client
except ImportError as exc:  # pragma: no cover
    raise SystemExit("pip install gradio_client") from exc


def normalize_base_url(base: str) -> str:
    url = str(base or "").strip()
    if not url.startswith("http"):
        raise ValueError(f"invalid IndexTTS base_url: {base!r}")
    return url.rstrip("/") + "/"


def check_indextts_url(base: str, *, timeout: float = 10.0) -> None:
    url = normalize_base_url(base) + "config"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                raise RuntimeError(f"IndexTTS HTTP {resp.status} at {url}")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"无法连接 IndexTTS：{url} ({exc})") from exc


def connect_client(base: str, *, timeout: float = 120.0) -> Client:
    normalized = normalize_base_url(base)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(Client, normalized)
        try:
            return future.result(timeout=timeout)
        except FutureTimeout as exc:
            raise RuntimeError(f"连接 IndexTTS 超时 ({int(timeout)}s)：{normalized}") from exc


def load_base_url(root: Path, override: str | None = None) -> str:
    if override:
        return normalize_base_url(override)
    cfg_path = root / "audio" / "indextts2_config.json"
    if cfg_path.exists():
        import json

        cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
        if cfg.get("base_url"):
            return normalize_base_url(str(cfg["base_url"]))
    return "http://127.0.0.1:7860/"
