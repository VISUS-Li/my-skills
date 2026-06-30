#!/usr/bin/env python3
"""Timing patch helpers for Review Studio."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from review_core import append_history, propagate_stale, utc_now

MIN_PLAYBACK_RATE = 0.25
MAX_PLAYBACK_RATE = 2.0


def load_vo_timing(root: Path, segment: str) -> dict[str, Any]:
    path = root / "segments" / segment / "vo_timing.json"
    if not path.exists():
        return {"segment_id": segment, "total_sec": 0, "beats": []}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_vo_timing(root: Path, segment: str, data: dict[str, Any]) -> None:
    path = root / "segments" / segment / "vo_timing.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clamp_playback_rate(rate: float) -> float:
    return round(max(MIN_PLAYBACK_RATE, min(MAX_PLAYBACK_RATE, rate)), 3)


def ensure_beat_edit_fields(beat: dict[str, Any]) -> dict[str, Any]:
    dur = float(beat.get("duration_sec") or 0)
    if not beat.get("source_duration_sec"):
        rate = float(beat.get("playback_rate") or 1.0) or 1.0
        beat["source_duration_sec"] = round(dur * rate, 3) if dur else dur
    beat.setdefault("playback_rate", 1.0)
    beat.setdefault("disabled", False)
    return beat


def beat_timeline_duration(beat: dict[str, Any]) -> float:
    ensure_beat_edit_fields(beat)
    if beat.get("disabled"):
        return 0.0
    src = float(beat.get("source_duration_sec") or beat.get("duration_sec") or 0)
    rate = float(beat.get("playback_rate") or 1.0) or 1.0
    if src <= 0:
        return 0.0
    return round(src / clamp_playback_rate(rate), 3)


def recompute_starts(beats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    t = 0.0
    for beat in beats:
        ensure_beat_edit_fields(beat)
        if beat.get("disabled"):
            beat["duration_sec"] = 0.0
            beat["start_sec"] = round(t, 3)
            beat["end_sec"] = round(t, 3)
            beat["cps"] = 0.0
            continue
        dur = beat_timeline_duration(beat)
        beat["duration_sec"] = dur
        beat["start_sec"] = round(t, 3)
        beat["end_sec"] = round(t + dur, 3)
        chars = int(beat.get("char_count", 0))
        beat["cps"] = round(chars / dur, 2) if dur else 0
        t += dur
    return beats


def _save_vo_and_stale(root: Path, segment: str, data: dict[str, Any], *, note: str) -> list[str]:
    save_vo_timing(root, segment, data)
    rel = f"segments/{segment}/vo_timing.json"
    return propagate_stale(root, rel, note=note, segment_id=segment)


def patch_beat_timing(
    root: Path,
    segment: str,
    beat_id: str,
    *,
    duration_sec: float | None = None,
    locked: bool | None = None,
    playback_rate: float | None = None,
    disabled: bool | None = None,
) -> dict[str, Any]:
    data = load_vo_timing(root, segment)
    beats = data.get("beats", [])
    found = False
    for beat in beats:
        if beat.get("beat_id") != beat_id:
            continue
        found = True
        ensure_beat_edit_fields(beat)
        if disabled is not None:
            beat["disabled"] = bool(disabled)
            beat["source"] = "manual"
        if playback_rate is not None:
            beat["playback_rate"] = clamp_playback_rate(float(playback_rate))
            beat["source"] = "manual"
        if duration_sec is not None:
            new_dur = max(0.05, round(float(duration_sec), 3))
            src = float(beat.get("source_duration_sec") or beat.get("duration_sec") or new_dur)
            if src <= 0:
                src = new_dur
            beat["source_duration_sec"] = round(src, 3)
            beat["playback_rate"] = clamp_playback_rate(src / new_dur)
            beat["source"] = "manual"
        if locked is not None:
            beat["locked"] = locked
        if duration_sec is not None or locked or playback_rate is not None or disabled is not None:
            beat.setdefault("source", "manual")
    if not found:
        raise KeyError(beat_id)

    beats = recompute_starts(beats)
    data["beats"] = beats
    enabled = [b for b in beats if not b.get("disabled")]
    data["total_sec"] = round(enabled[-1]["end_sec"], 3) if enabled else 0
    stale = _save_vo_and_stale(root, segment, data, note=f"manual timing patch {beat_id}")
    append_history(root, {
        "type": "timing_patched",
        "beat_id": beat_id,
        "segment_id": segment,
        "duration_sec": duration_sec,
        "playback_rate": playback_rate,
        "disabled": disabled,
        "locked": locked,
        "at": utc_now(),
    })
    return {"beat_id": beat_id, "vo_timing": data, "stale": stale}


def delete_beat_timing(root: Path, segment: str, beat_id: str) -> dict[str, Any]:
    return patch_beat_timing(root, segment, beat_id, disabled=True, locked=True)


def patch_timeline_settings(
    root: Path,
    segment: str,
    *,
    master_playback_rate: float | None = None,
) -> dict[str, Any]:
    data = load_vo_timing(root, segment)
    if master_playback_rate is not None:
        data["master_playback_rate"] = clamp_playback_rate(float(master_playback_rate))
    stale = _save_vo_and_stale(root, segment, data, note="timeline playback settings")
    append_history(root, {
        "type": "timeline_settings",
        "segment_id": segment,
        "master_playback_rate": data.get("master_playback_rate"),
        "at": utc_now(),
    })
    return {
        "segment_id": segment,
        "master_playback_rate": float(data.get("master_playback_rate") or 1.0),
        "vo_timing": data,
        "stale": stale,
    }


def _ffmpeg_atempo(in_path: Path, out_path: Path, rate: float) -> None:
    """Apply playback rate via ffmpeg atempo (0.5–2.0 per filter; chain if needed)."""
    rate = clamp_playback_rate(rate)
    if abs(rate - 1.0) < 0.001:
        shutil.copy2(in_path, out_path)
        return
    filters: list[str] = []
    remaining = rate
    while remaining > 2.0 + 1e-6:
        filters.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5 - 1e-6:
        filters.append("atempo=0.5")
        remaining /= 0.5
    filters.append(f"atempo={remaining:.4f}")
    filt = ",".join(filters)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(in_path), "-filter:a", filt, "-ac", "1", "-ar", "48000", str(out_path)],
        check=True,
        capture_output=True,
    )


def rebuild_timeline_vo(root: Path, segment: str) -> dict[str, Any]:
    """Rebuild master VO from beat WAVs honoring disabled clips and per-beat speed."""
    data = load_vo_timing(root, segment)
    beats_dir = root / "audio" / "stems" / "voice" / "beats"
    seg = segment.upper()
    temp_files: list[Path] = []
    concat_inputs: list[Path] = []
    with tempfile.TemporaryDirectory(prefix="vo_rebuild_") as tmp:
        tmp_path = Path(tmp)
        for beat in data.get("beats", []):
            ensure_beat_edit_fields(beat)
            if beat.get("disabled"):
                continue
            bid = beat.get("beat_id", "")
            src_wav = beats_dir / f"{bid}.wav"
            if not src_wav.exists():
                continue
            rate = float(beat.get("playback_rate") or 1.0) or 1.0
            if abs(rate - 1.0) < 0.001:
                concat_inputs.append(src_wav)
            else:
                out = tmp_path / f"{bid}_rate.wav"
                _ffmpeg_atempo(src_wav, out, rate)
                temp_files.append(out)
                concat_inputs.append(out)
        if not concat_inputs:
            raise FileNotFoundError("no enabled beat WAV files to concat")

        master = root / "audio" / "stems" / "voice" / "voiceover_full.wav"
        lst = master.with_suffix(".txt")
        lst.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in concat_inputs), encoding="utf-8")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(master)],
            check=True,
            capture_output=True,
        )
        for rel in (f"audio/voice/{seg}_vo.wav", f"segments/{seg}/{seg.lower()}_vo.wav"):
            dest = root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(master, dest)

    beats = recompute_starts(list(data.get("beats", [])))
    data["beats"] = beats
    enabled = [b for b in beats if not b.get("disabled")]
    data["total_sec"] = round(enabled[-1]["end_sec"], 3) if enabled else 0
    stale = _save_vo_and_stale(root, segment, data, note="timeline VO rebuild")
    return {
        "segment_id": segment,
        "vo_wav": master.relative_to(root).as_posix(),
        "beat_count": len(concat_inputs),
        "total_sec": data["total_sec"],
        "stale": stale,
    }


def patch_micro_event(
    root: Path,
    segment: str,
    event_id: str,
    t: float,
) -> dict[str, Any]:
    path = root / "segments" / segment / "micro_timing.json"
    if not path.exists():
        raise FileNotFoundError(str(path))
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    events: list[dict[str, Any]]
    wrap_dict = False
    if isinstance(raw, list):
        events = raw
    else:
        events = raw.get("events", [])
        wrap_dict = True
    found = False
    for ev in events:
        eid = ev.get("id") or ev.get("event_id")
        if eid == event_id:
            ev["t"] = round(t, 3)
            ev["manual_override"] = True
            found = True
            break
    if not found:
        raise KeyError(event_id)

    if wrap_dict:
        raw["events"] = events
        path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        path.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    rel = f"segments/{segment}/micro_timing.json"
    stale = propagate_stale(root, rel, note=f"micro event {event_id} patched", segment_id=segment)
    return {"event_id": event_id, "t": t, "stale": stale}


def resolve_timeline_media(root: Path, segment: str) -> dict[str, str | None]:
    """Resolve preview media paths relative to project root."""
    vo_candidates = [
        root / "audio" / "voice" / f"{segment}_vo.wav",
        root / "audio" / "stems" / "voice" / "voiceover_full.wav",
        root / "segments" / segment / f"{segment}_vo.wav",
    ]
    vo_path = next((p for p in vo_candidates if p.exists()), None)
    mp4 = root / "segments" / segment / "render.mp4"
    html = root / "segments" / segment / "index.html"
    return {
        "vo_wav": vo_path.relative_to(root).as_posix() if vo_path else None,
        "render_mp4": mp4.relative_to(root).as_posix() if mp4.exists() else None,
        "composition_html": html.relative_to(root).as_posix() if html.exists() else None,
    }


def audio_summary(root: Path, segment: str) -> dict[str, Any]:
    vo = load_vo_timing(root, segment)
    beats = vo.get("beats", [])
    planned_total = sum(float(b.get("planned_sec", 0)) for b in beats)
    actual_total = float(vo.get("total_sec", 0))
    drift_beats = []
    for b in beats:
        planned = float(b.get("planned_sec", 0))
        actual = float(b.get("duration_sec", 0))
        drift = round(actual - planned, 3)
        cps = float(b.get("cps", 0))
        band = "ok"
        if cps < 3.5 or cps > 7.5:
            band = "fail"
        elif cps < 4.0 or cps > 6.5:
            band = "warn"
        if abs(drift) > 0.3:
            drift_beats.append({
                "beat_id": b.get("beat_id"),
                "planned_sec": planned,
                "duration_sec": actual,
                "drift_sec": drift,
                "cps": cps,
                "cps_band": band,
                "locked": bool(b.get("locked")),
            })
    return {
        "segment_id": segment,
        "planned_total_sec": round(planned_total, 3),
        "actual_total_sec": round(actual_total, 3),
        "drift_total_sec": round(actual_total - planned_total, 3),
        "beat_count": len(beats),
        "drift_beats": drift_beats,
    }
