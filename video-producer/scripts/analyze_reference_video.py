#!/usr/bin/env python3
"""Analyze a local reference video for style matching.

Outputs ffprobe metadata, contact sheets, coarse scene-change times, color/layout
metrics, loudness metrics, and audio energy metrics. The script does not replace
human taste; it creates evidence for a reference-video style deconstruction.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path
from typing import Any

import numpy as np


def run(cmd: list[str], *, capture: bool = False, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=capture, check=check)


def require_bin(name: str) -> None:
    if not shutil.which(name):
        raise SystemExit(f"Missing required binary: {name}")


def ffprobe(video: Path) -> dict[str, Any]:
    proc = run([
        "ffprobe", "-v", "error", "-show_format", "-show_streams", "-print_format", "json", str(video)
    ], capture=True)
    return json.loads(proc.stdout)


def stream_of(meta: dict[str, Any], codec_type: str) -> dict[str, Any]:
    for s in meta.get("streams", []):
        if s.get("codec_type") == codec_type:
            return s
    return {}


def make_contact_sheet(video: Path, out: Path, fps_expr: str = "1/10", cols: int = 5, rows: int = 10) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(video),
        "-vf", f"fps={fps_expr},scale=320:-1,tile={cols}x{rows}",
        "-frames:v", "1", str(out)
    ])


def extract_frame(video: Path, t: float, out: Path) -> None:
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}",
        "-i", str(video), "-frames:v", "1", "-q:v", "2", str(out)
    ])


def make_key_contact(video: Path, duration: float, outdir: Path, out: Path, count: int = 30) -> list[float]:
    outdir.mkdir(parents=True, exist_ok=True)
    # Extract an evenly spaced low-resolution frame sample in one ffmpeg pass.
    # This is much faster than launching ffmpeg once per timestamp.
    fps_expr = f"{count}/{max(duration, 1):.3f}"
    pattern = outdir / "kf_%03d.jpg"
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(video),
        "-vf", f"fps={fps_expr},scale=640:-1", "-frames:v", str(count), str(pattern)
    ])
    frame_paths = sorted(outdir.glob("kf_*.jpg"))
    times = [round(min(duration - 0.2, i * duration / max(len(frame_paths) - 1, 1)), 3) for i in range(len(frame_paths))]
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return times
    thumbs = []
    for p, t in zip(frame_paths, times):
        im = Image.open(p).convert("RGB")
        im.thumbnail((320, 180))
        canvas = Image.new("RGB", (320, 205), "white")
        canvas.paste(im, ((320 - im.width) // 2, 0))
        ImageDraw.Draw(canvas).text((8, 184), f"{t:.1f}s", fill=(0, 0, 0))
        thumbs.append(canvas)
    cols = 5
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * 320, rows * 205), "white")
    for i, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((i % cols) * 320, (i // cols) * 205))
    sheet.save(out, quality=92)
    return times


def scene_times_from_frames(frame_paths: list[Path], times: list[float], threshold: float) -> list[float]:
    # Coarse scene-change proxy based on sampled frame differences.
    # threshold is re-used as a normalized sensitivity value, not FFmpeg's exact scene score.
    try:
        from PIL import Image
    except Exception:
        return []
    previous = None
    changes: list[float] = []
    for p, t in zip(frame_paths, times):
        im = Image.open(p).convert("L").resize((160, 90))
        arr = np.asarray(im, dtype=np.float32)
        if previous is not None:
            diff = float(np.mean(np.abs(arr - previous)) / 255.0)
            if diff > max(0.08, threshold * 0.35):
                changes.append(round(float(t), 3))
        previous = arr
    return changes

def color_metrics(frame_paths: list[Path]) -> dict[str, Any]:
    try:
        import cv2
    except Exception as exc:
        return {"error": f"opencv unavailable: {exc}"}
    rows = []
    for p in frame_paths:
        img = cv2.imread(str(p))
        if img is None:
            continue
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 80, 160)
        offwhite = np.mean((rgb[:, :, 0] > 215) & (rgb[:, :, 1] > 215) & (rgb[:, :, 2] > 205))
        accent = np.mean(hsv[:, :, 1] > 80)
        rows.append({
            "file": p.name,
            "brightness": float(np.mean(hsv[:, :, 2])),
            "saturation": float(np.mean(hsv[:, :, 1])),
            "offwhite_pct": float(offwhite * 100),
            "accent_pct": float(accent * 100),
            "edge_pct": float(np.mean(edges > 0) * 100),
        })
    if not rows:
        return {"frames": [], "aggregate": {}}
    keys = ["brightness", "saturation", "offwhite_pct", "accent_pct", "edge_pct"]
    agg = {k: round(float(np.mean([r[k] for r in rows])), 3) for k in keys}
    agg.update({f"{k}_p90": round(float(np.percentile([r[k] for r in rows], 90)), 3) for k in keys})
    return {"frames": [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()} for r in rows], "aggregate": agg}


def loudnorm(video: Path) -> dict[str, Any]:
    proc = run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(video),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"
    ], capture=True, check=False)
    match = re.search(r"\{\s*\"input_i\".*?\}\s*", proc.stderr or "", flags=re.S)
    if not match:
        return {"error": "loudnorm json not found"}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        return {"error": f"could not parse loudnorm json: {exc}"}


def extract_wav(video: Path, wav_path: Path, sr: int = 16000) -> None:
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(video),
        "-vn", "-ac", "1", "-ar", str(sr), "-sample_fmt", "s16", str(wav_path)
    ])


def audio_energy_metrics(wav_path: Path) -> dict[str, Any]:
    with wave.open(str(wav_path), "rb") as wf:
        sr = wf.getframerate()
        n = wf.getnframes()
        raw = wf.readframes(n)
    y = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    duration = len(y) / sr if sr else 0.0
    frame = max(1, int(sr * 1.0))
    hop = max(1, int(sr * 0.5))
    rms = []
    centroid = []
    for start in range(0, max(1, len(y) - frame + 1), hop):
        chunk = y[start:start + frame]
        if len(chunk) < frame:
            break
        r = float(np.sqrt(np.mean(chunk * chunk)) + 1e-12)
        rms.append(r)
        spec = np.abs(np.fft.rfft(chunk * np.hanning(len(chunk))))
        freqs = np.fft.rfftfreq(len(chunk), 1 / sr)
        centroid.append(float(np.sum(freqs * spec) / (np.sum(spec) + 1e-12)))
    rms_db = 20 * np.log10(np.array(rms) + 1e-12) if rms else np.array([])
    # approximate onset peaks from positive RMS jumps separated by at least 0.8s
    jumps = np.diff(rms_db) if len(rms_db) > 1 else np.array([])
    threshold = max(1.5, float(np.percentile(jumps, 80)) if len(jumps) else 1.5)
    peaks = []
    last = -999
    for i, j in enumerate(jumps, start=1):
        if j > threshold and i - last >= 2:
            peaks.append(i * 0.5)
            last = i
    silence = []
    in_silence = False
    start_s = 0.0
    for i, db in enumerate(rms_db):
        t = i * 0.5
        if db < -35 and not in_silence:
            in_silence = True
            start_s = t
        elif db >= -35 and in_silence:
            if t - start_s >= 0.25:
                silence.append((round(start_s, 3), round(t, 3)))
            in_silence = False
    return {
        "duration_sec": round(duration, 3),
        "rms_db_mean": round(float(np.mean(rms_db)), 3) if len(rms_db) else None,
        "rms_db_p10": round(float(np.percentile(rms_db, 10)), 3) if len(rms_db) else None,
        "rms_db_p90": round(float(np.percentile(rms_db, 90)), 3) if len(rms_db) else None,
        "rms_dynamic_range_p90_p10_db": round(float(np.percentile(rms_db, 90) - np.percentile(rms_db, 10)), 3) if len(rms_db) else None,
        "spectral_centroid_mean_hz": round(float(np.mean(centroid)), 3) if centroid else None,
        "approx_onset_peaks": len(peaks),
        "approx_onsets_per_min": round(float(len(peaks) / duration * 60), 3) if duration else None,
        "first_40_approx_onsets_sec": [round(float(t), 3) for t in peaks[:40]],
        "silence_regions_rms_below_minus35db": silence[:100],
        "silence_region_count": len(silence),
    }


def write_style_template(out: Path, metrics: dict[str, Any]) -> None:
    v = metrics.get("video", {})
    a = metrics.get("audio", {})
    text = f"""# Reference Video Style DNA

Fill this in after inspecting the generated contact sheets.

## Measured facts

- Duration: {v.get('duration_sec')} sec
- Format: {v.get('width')}x{v.get('height')}, {v.get('fps')} fps, ratio {v.get('display_aspect_ratio')}
- Audio loudness: integrated {a.get('loudnorm', {}).get('input_i')} LUFS, LRA {a.get('loudnorm', {}).get('input_lra')}, true peak {a.get('loudnorm', {}).get('input_tp')} dBTP
- Audio energy: mean RMS {a.get('energy', {}).get('rms_db_mean')} dB, p90-p10 range {a.get('energy', {}).get('rms_dynamic_range_p90_p10_db')} dB, approx onsets/min {a.get('energy', {}).get('approx_onsets_per_min')}

## Human deconstruction

### Narrative architecture

- Hook:
- Stakes:
- Explanation modules:
- Proof/examples:
- Solution/takeaway:
- CTA:

### Visual system

- Background/material:
- Palette roles:
- Typography/caption system:
- Composition patterns:
- Recurring assets/mascots/machines:
- Text safety rules:

### Motion and edit grammar

- Camera moves:
- Object motions:
- Transitions:
- Rhythm rules:
- Must-use primitives:

### Audio and voice

- Voice tone:
- Music bed:
- SFX palette:
- Silence/drop rules:
- Mix target:

### Production implications

- Programmatic layers:
- Generative assets:
- Manual finishing:
- Quality gates:
"""
    out.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a reference video for reusable style DNA.")
    parser.add_argument("video", help="Local video file")
    parser.add_argument("--out", default="analysis/reference_video", help="Output directory")
    parser.add_argument("--scene-threshold", type=float, default=0.35)
    args = parser.parse_args()

    require_bin("ffmpeg")
    require_bin("ffprobe")
    video = Path(args.video).expanduser().resolve()
    if not video.exists():
        raise SystemExit(f"Video not found: {video}")
    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    meta = ffprobe(video)
    vs = stream_of(meta, "video")
    aud = stream_of(meta, "audio")
    duration = float(meta.get("format", {}).get("duration") or vs.get("duration") or aud.get("duration") or 0.0)
    fps = None
    if vs.get("avg_frame_rate") and vs.get("avg_frame_rate") != "0/0":
        num, den = vs["avg_frame_rate"].split("/")
        fps = round(float(num) / float(den), 3) if float(den) else None

    key_dir = out / "keyframes"
    key_times = make_key_contact(video, duration, key_dir, out / "key_contact.jpg")
    shutil.copyfile(out / "key_contact.jpg", out / "contact_10s.jpg")
    frame_paths = sorted(key_dir.glob("*.jpg"))
    scenes = scene_times_from_frames(frame_paths, key_times, args.scene_threshold)

    wav = out / "audio_mono_16k.wav"
    extract_wav(video, wav)

    metrics = {
        "source": str(video),
        "video": {
            "width": vs.get("width"),
            "height": vs.get("height"),
            "display_aspect_ratio": vs.get("display_aspect_ratio"),
            "fps": fps,
            "codec": vs.get("codec_name"),
            "duration_sec": round(duration, 3),
            "bit_rate": vs.get("bit_rate"),
            "keyframe_sample_times_sec": key_times,
            "scene_threshold": args.scene_threshold,
            "scene_change_times_sec": [round(t, 3) for t in scenes],
            "scene_change_count": len(scenes),
        },
        "audio": {
            "codec": aud.get("codec_name"),
            "sample_rate": aud.get("sample_rate"),
            "channels": aud.get("channels"),
            "bit_rate": aud.get("bit_rate"),
            "loudnorm": loudnorm(wav),
            "energy": audio_energy_metrics(wav),
        },
        "visual_metrics": color_metrics(frame_paths),
        "outputs": {
            "contact_10s": str(out / "contact_10s.jpg"),
            "key_contact": str(out / "key_contact.jpg"),
            "keyframes_dir": str(key_dir),
            "style_dna_template": str(out / "style_dna.md"),
        },
    }
    (out / "reference_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_style_template(out / "style_dna.md", metrics)
    print(f"Wrote {out / 'reference_metrics.json'}")
    print(f"Wrote {out / 'contact_10s.jpg'}")
    print(f"Wrote {out / 'key_contact.jpg'}")
    print(f"Wrote {out / 'style_dna.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
