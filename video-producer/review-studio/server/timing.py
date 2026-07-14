#!/usr/bin/env python3
"""Timing patch helpers for Review Studio."""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from review_core import append_history, propagate_stale, utc_now

MIN_PLAYBACK_RATE = 0.25
MAX_PLAYBACK_RATE = 2.0


def wav_duration_sec(path: Path) -> float | None:
    """Read WAV duration from file header."""
    if not path.is_file():
        return None
    try:
        import wave

        with wave.open(str(path), "rb") as handle:
            rate = handle.getframerate()
            if rate <= 0:
                return None
            return round(handle.getnframes() / float(rate), 3)
    except Exception:
        return None


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
    dur = float(beat.get("duration_sec") or 0)
    if dur > 0:
        return round(dur, 3)
    src = float(beat.get("source_duration_sec") or 0)
    if src <= 0:
        return 0.0
    rate = float(beat.get("playback_rate") or 1.0) or 1.0
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
            beat["duration_sec"] = new_dur
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


def _ffmpeg_render_timeline_clip(in_path: Path, out_path: Path, *, duration: float, rate: float) -> None:
    """Render one beat clip for timeline concat, honoring trim duration and playback speed."""
    rate = clamp_playback_rate(rate)
    duration = max(0.05, float(duration))
    source_take = max(0.05, duration * rate)
    filters: list[str] = []
    remaining = rate
    while remaining > 2.0 + 1e-6:
        filters.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5 - 1e-6:
        filters.append("atempo=0.5")
        remaining /= 0.5
    if abs(remaining - 1.0) > 0.001:
        filters.append(f"atempo={remaining:.4f}")
    cmd = [
        "ffmpeg",
        "-y",
        "-t",
        f"{source_take:.3f}",
        "-i",
        str(in_path),
    ]
    if filters:
        cmd.extend(["-filter:a", ",".join(filters)])
    cmd.extend(["-ac", "1", "-ar", "48000", str(out_path)])
    subprocess.run(cmd, check=True, capture_output=True)


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
            duration = beat_timeline_duration(beat)
            out = tmp_path / f"{bid}_timeline.wav"
            _ffmpeg_render_timeline_clip(src_wav, out, duration=duration, rate=rate)
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


PROGRAMMATIC_TYPES = frozenset({
    "hyperframes_component",
    "text_layer",
    "ambient",
})


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build_timeline_model(
    root: Path,
    segment: str,
    beats: list[dict[str, Any]],
    micro_events: list[dict[str, Any]],
) -> dict[str, Any]:
    """Unified multi-track timeline for Review Studio UI."""
    seg = segment.upper()
    vo = load_vo_timing(root, seg)
    vo_beats = {
        str(b["beat_id"]): b
        for b in vo.get("beats", [])
        if isinstance(b, dict) and b.get("beat_id")
    }

    audio_clips: list[dict[str, Any]] = []
    video_clips: list[dict[str, Any]] = []
    for row in beats:
        if row.get("disabled"):
            continue
        beat_id = str(row.get("beat_id", ""))
        vo_row = row.get("vo") or vo_beats.get(beat_id, {})
        start = float(vo_row.get("start_sec") or row.get("start_sec") or 0)
        dur = float(vo_row.get("duration_sec") or row.get("actual_sec") or row.get("duration_sec") or 0)
        if dur <= 0:
            continue
        end = round(start + dur, 3)
        audio_clips.append({
            "id": beat_id,
            "beat_id": beat_id,
            "start": round(start, 3),
            "end": end,
            "duration_sec": round(dur, 3),
            "wav": row.get("vo_wav"),
            "playback_rate": float(row.get("playback_rate") or vo_row.get("playback_rate") or 1),
            "wav_duration_sec": row.get("wav_duration_sec"),
            "label": str(row.get("narration") or "")[:48],
        })
        video_clips.append({
            "id": f"scene_{beat_id}",
            "beat_id": beat_id,
            "start": round(start, 3),
            "end": end,
            "label": row.get("spoken_focus") or row.get("beat_type") or beat_id,
        })

    manifest_rows: dict[str, dict[str, str]] = {}
    for item in _read_csv(root / "assets" / "asset_manifest.csv"):
        aid = item.get("asset_id", "")
        if aid:
            manifest_rows[aid] = item

    asset_clips: list[dict[str, Any]] = []
    spec_path = root / "outputs" / "segment_spec.json"
    if spec_path.exists():
        spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
        for shot in spec.get("shots", []) if isinstance(spec, dict) else []:
            if not isinstance(shot, dict):
                continue
            shot_start = float((shot.get("time") or [0, 0])[0])
            shot_end = float((shot.get("time") or [0, 0])[1]) if isinstance(shot.get("time"), list) else shot_start
            for action in shot.get("visual_actions", []):
                if not isinstance(action, dict):
                    continue
                asset_id = (action.get("asset") or "").strip()
                if not asset_id:
                    continue
                at = shot_start + float(action.get("at") or 0)
                asset_clips.append({
                    "id": asset_id,
                    "beat_id": (shot.get("narration_beats") or [""])[0],
                    "start": round(at, 3),
                    "end": round(min(shot_end, at + 0.5), 3),
                    "kind": action.get("type", "asset"),
                    "path": asset_id,
                    "programmatic": False,
                    "role": "shot_action",
                })

    micro_by_id = {
        str(ev.get("id") or ev.get("event_id")): ev
        for ev in micro_events
        if isinstance(ev, dict)
    }
    plan_dur_by_beat = {
        str(row.get("beat_id", "")): float(row.get("planned_sec") or row.get("duration_sec") or 1)
        for row in beats
    }
    event_clips: list[dict[str, Any]] = []
    for ev in micro_events:
        if not isinstance(ev, dict):
            continue
        event_id = str(ev.get("id") or ev.get("event_id", ""))
        start = float(ev.get("t", 0))
        parent = str(ev.get("parent") or "")
        plan_dur = plan_dur_by_beat.get(parent, 1.0) or 1.0
        if parent in vo_beats:
            parent_dur = float(vo_beats[parent].get("duration_sec", plan_dur)) or plan_dur
            scale = parent_dur / plan_dur if plan_dur else 1.0
            event_dur = round(0.35 * scale, 3)
        else:
            event_dur = 0.35
        event_clips.append({
            "id": event_id,
            "parent": parent,
            "start": round(start, 3),
            "end": round(start + event_dur, 3),
            "visual_action": ev.get("visual_action") or ev.get("type", ""),
            "assets": [ev.get("text")] if ev.get("text") else [],
            "beat_type": ev.get("type", ""),
        })

    return {
        "timebase": "vo_timing",
        "tracks": [
            {"id": "A1", "type": "audio", "label": "口播", "clips": audio_clips},
            {"id": "V1", "type": "video", "label": "画面", "clips": video_clips},
            {"id": "V2", "type": "asset", "label": "素材", "clips": asset_clips},
            {"id": "E1", "type": "event", "label": "导演事件", "clips": event_clips},
        ],
    }
