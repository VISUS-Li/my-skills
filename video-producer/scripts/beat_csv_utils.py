#!/usr/bin/env python3
"""Helpers for script/narration_beats.csv (supports legacy and director-compiler schemas)."""
from __future__ import annotations


def narration_char_count(row: dict[str, str]) -> int:
    raw = (row.get("char_count") or "").strip()
    if raw:
        return int(float(raw))
    text = (row.get("narration") or "").strip()
    return len(text.replace(" ", ""))


def planned_duration_sec(row: dict[str, str]) -> float:
    raw = (row.get("duration_sec") or "").strip()
    if raw:
        return float(raw)
    start = float(row.get("start_sec") or 0)
    end = float(row.get("end_sec") or start)
    return max(0.01, end - start)
