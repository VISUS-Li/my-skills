#!/usr/bin/env python3
"""Sync narration edits from narration_beats.csv to downstream script/audio artifacts."""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

RS_SYNC_START = "<!-- rs-beat-narration:start -->"
RS_SYNC_END = "<!-- rs-beat-narration:end -->"

PROSODY_COLUMNS = [
    "beat_id",
    "segment_id",
    "tts_text",
    "pace",
    "pre_pause_ms",
    "post_pause_ms",
    "emphasis_words",
    "breath_after",
    "tone",
    "allow_disfluency",
    "director_note",
]


def read_beats_csv(root: Path, segment_id: str | None = None) -> list[dict[str, str]]:
    path = root / "script" / "narration_beats.csv"
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if segment_id and row.get("segment_id", "").upper() != segment_id.upper():
                continue
            rows.append(dict(row))
    return rows


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sync_prosody_tts_text(
    root: Path,
    *,
    segment_id: str,
    beat_ids: set[str] | None = None,
) -> int:
    """Mirror narration_beats narration into audio/prosody_plan.csv tts_text."""
    beats_path = root / "script" / "narration_beats.csv"
    prosody_path = root / "audio" / "prosody_plan.csv"
    if not beats_path.exists():
        return 0

    beats = read_beats_csv(root, segment_id)
    narration_by_beat = {
        row["beat_id"]: (row.get("narration") or "").strip()
        for row in beats
        if row.get("beat_id")
    }
    if beat_ids is not None:
        narration_by_beat = {bid: text for bid, text in narration_by_beat.items() if bid in beat_ids}

    rows: list[dict[str, str]] = []
    fieldnames = list(PROSODY_COLUMNS)
    if prosody_path.exists():
        with prosody_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            fieldnames = list(reader.fieldnames or PROSODY_COLUMNS)
            rows = [dict(row) for row in reader]
    for col in PROSODY_COLUMNS:
        if col not in fieldnames:
            fieldnames.append(col)

    by_beat = {row.get("beat_id", ""): row for row in rows if row.get("beat_id")}
    updated = 0
    for beat_id, narration in narration_by_beat.items():
        row = by_beat.get(beat_id)
        if row is None:
            row = {
                "beat_id": beat_id,
                "segment_id": segment_id,
                "tts_text": narration,
                "pace": "normal",
                "pre_pause_ms": "0",
                "post_pause_ms": "160",
                "emphasis_words": "",
                "breath_after": "",
                "tone": "neutral",
                "allow_disfluency": "false",
                "director_note": "synced from Review Studio narration edit",
            }
            rows.append(row)
            by_beat[beat_id] = row
            updated += 1
        elif (row.get("tts_text") or "").strip() != narration:
            row["tts_text"] = narration
            updated += 1

    if updated:
        _write_csv(prosody_path, fieldnames, rows)
    return updated


def _render_voiceover_sync_block(beats: list[dict[str, str]]) -> str:
    lines = [
        RS_SYNC_START,
        "",
        "> 以下内容由 Review Studio 口播 & 配音页自动同步，以 `narration_beats.csv` 为准。",
        "",
    ]
    for row in beats:
        beat_id = row.get("beat_id", "")
        narration = (row.get("narration") or "").strip()
        if not beat_id or not narration:
            continue
        lines.append(f"<!-- beat:{beat_id} -->")
        lines.append(narration)
        lines.append("")
    lines.append(RS_SYNC_END)
    return "\n".join(lines).rstrip() + "\n"


def sync_voiceover_from_beats(root: Path, segment_id: str) -> str | None:
    """Update voiceover.md synced section from narration_beats for one segment."""
    beats = read_beats_csv(root, segment_id)
    if not beats:
        return None

    script_dir = root / "script"
    versioned = sorted(script_dir.glob("voiceover.v*.md"), reverse=True)
    vo_path = versioned[0] if versioned else script_dir / "voiceover.md"
    if not vo_path.exists():
        vo_path = script_dir / "voiceover.md"

    block = _render_voiceover_sync_block(beats)
    if vo_path.exists():
        content = vo_path.read_text(encoding="utf-8-sig")
    else:
        content = "# Voiceover\n\n"

    pattern = re.compile(
        re.escape(RS_SYNC_START) + r"[\s\S]*?" + re.escape(RS_SYNC_END) + r"\n?",
    )
    if pattern.search(content):
        content = pattern.sub(block, content, count=1)
    else:
        content = content.rstrip() + "\n\n" + block

    vo_path.parent.mkdir(parents=True, exist_ok=True)
    vo_path.write_text(content, encoding="utf-8")
    return vo_path.relative_to(root).as_posix()


def invalidate_beat_vo_wav(root: Path, beat_id: str) -> bool:
    """Remove stale beat WAV so TTS regenerates after narration change."""
    wav = root / "audio" / "stems" / "voice" / "beats" / f"{beat_id}.wav"
    if wav.exists():
        wav.unlink()
        return True
    return False


def sync_narration_downstream(
    root: Path,
    *,
    segment_id: str,
    beat_ids: set[str] | None = None,
    invalidate_vo: bool = True,
) -> dict[str, Any]:
    """Sync prosody + voiceover after narration_beats edits."""
    prosody_updates = sync_prosody_tts_text(root, segment_id=segment_id, beat_ids=beat_ids)
    voiceover_path = sync_voiceover_from_beats(root, segment_id)
    removed_wavs: list[str] = []
    if invalidate_vo and beat_ids:
        for beat_id in beat_ids:
            if invalidate_beat_vo_wav(root, beat_id):
                removed_wavs.append(beat_id)
    return {
        "prosody_updates": prosody_updates,
        "voiceover_path": voiceover_path,
        "removed_vo_wavs": removed_wavs,
    }
