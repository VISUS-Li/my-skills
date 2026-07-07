#!/usr/bin/env python3
"""Batch voiceover via IndexTTS2 Gradio API (/gen_single)."""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

try:
    from gradio_client import handle_file
except ImportError:
    print("pip install gradio_client", file=sys.stderr)
    raise

from audio_ref_utils import convert_to_wav, is_riff_file, wav_path_for_ref  # noqa: E402
from beat_csv_utils import narration_char_count  # noqa: E402
from indextts2_connect import check_indextts_url, connect_client, load_base_url, normalize_base_url  # noqa: E402
from tts_progress import clear_progress, write_progress  # noqa: E402


def load_config(root: Path) -> dict:
    cfg_path = root / "audio/indextts2_config.json"
    if cfg_path.exists():
        return json.loads(cfg_path.read_text(encoding="utf-8-sig"))
    return {"base_url": "http://10.0.221.33:37191/", "voice_reference": {"path": "audio/refs/narrator_ref.wav"}}


def ensure_ref(client, ref_path: Path, example_index: int = 3) -> Path:
    if ref_path.exists():
        if ref_path.suffix.lower() == ".mp3":
            wav_path = ref_path.with_suffix(".wav")
            if not is_riff_file(wav_path):
                convert_to_wav(ref_path, wav_path)
            ref_path = wav_path
        if is_riff_file(ref_path) and ref_path.stat().st_size > 10_000:
            return ref_path
    ref_path.parent.mkdir(parents=True, exist_ok=True)
    ex = client.predict(example_index, api_name="/on_example_click")
    src = ex[0]["value"] if isinstance(ex[0], dict) else ex[0]
    shutil.copy2(src, ref_path)
    print(f"ref saved: {ref_path}")
    return ref_path


def emotion_sliders(cfg: dict, segment_id: str) -> tuple[float, ...]:
    vec = {"happy": 0.0, "angry": 0.0, "sad": 0.0, "afraid": 0.0,
           "disgusted": 0.0, "melancholic": 0.0, "surprised": 0.0, "calm": 0.65}
    seg_map = cfg.get("segment_emotion_vectors", {})
    for k, v in seg_map.get(segment_id, {}).items():
        vec[k] = v
    return tuple(vec[k] for k in ["happy", "angry", "sad", "afraid", "disgusted", "melancholic", "surprised", "calm"])


def extract_path(result) -> Path:
    if isinstance(result, dict):
        return Path(result.get("path") or result.get("value"))
    return Path(result)


def synthesize(client, ref, text: str, segment_id: str, cfg: dict, max_tokens: int) -> Path:
    emo = emotion_sliders(cfg, segment_id)
    d = cfg.get("defaults", {})
    result = client.predict(
        cfg.get("emotion_control_method", "Same as the voice reference"),
        ref,
        text,
        None,
        d.get("emo_weight", 0.65),
        *emo,
        "",
        d.get("emo_random", False),
        max_tokens,
        d.get("do_sample", True),
        d.get("top_p", 0.8),
        d.get("top_k", 30),
        d.get("temperature", 0.8),
        d.get("length_penalty", 0.0),
        d.get("num_beams", 3),
        d.get("repetition_penalty", 10.0),
        d.get("max_mel_tokens", 1500),
        api_name="/gen_single",
    )
    return extract_path(result)


def load_beats(root: Path, segment_id: str | None) -> list[dict]:
    rows = []
    with (root / "script/narration_beats.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if segment_id and row["segment_id"].upper() != segment_id.upper():
                continue
            rows.append(row)
    return rows


def load_prosody(root: Path) -> dict[str, dict[str, str]]:
    path = root / "audio" / "prosody_plan.csv"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {row.get("beat_id", ""): row for row in csv.DictReader(f) if row.get("beat_id")}


def load_last_generated_text(root: Path) -> dict[str, str]:
    """Latest successful TTS text per beat from generation_manifest.jsonl."""
    path = root / "audio/stems/voice/generation_manifest.jsonl"
    latest: dict[str, str] = {}
    if not path.exists():
        return latest
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("status") != "ok":
            continue
        beat_id = row.get("beat_id")
        text = row.get("tts_text")
        if beat_id and isinstance(text, str):
            latest[str(beat_id)] = text
    return latest


def should_skip_existing_wav(
    *,
    force: bool,
    wav_path: Path,
    current_text: str,
    last_generated: dict[str, str],
    beat_id: str,
) -> bool:
    if force:
        return False
    if not wav_path.exists() or wav_path.stat().st_size <= 1000:
        return False
    previous_text = last_generated.get(beat_id)
    if previous_text is None:
        return False
    return previous_text == current_text


def pause_ms(row: dict[str, str], key: str) -> int:
    try:
        return max(0, int(float(row.get(key) or 0)))
    except ValueError:
        return 0


def concat_wav(files: list[Path], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    lst = out.with_suffix(".txt")
    lst.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in files), encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)], check=True)


def collect_segment_beat_wavs(root: Path, segment_id: str, beats_dir: Path) -> tuple[list[Path], list[str]]:
    """All beat WAV paths for a segment in narration order (not limited to this run's --beats filter)."""
    paths: list[Path] = []
    missing: list[str] = []
    for row in load_beats(root, segment_id):
        bid = row["beat_id"]
        wav = beats_dir / f"{bid}.wav"
        if wav.exists() and wav.stat().st_size > 1000:
            paths.append(wav)
        else:
            missing.append(bid)
    return paths, missing


def publish_segment_vo_copies(root: Path, segment_id: str, master: Path) -> None:
    """Mirror master VO to paths used by HyperFrames embed and Review Studio."""
    seg = segment_id.upper()
    for rel in (f"audio/voice/{seg}_vo.wav", f"segments/{seg}/{seg.lower()}_vo.wav"):
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(master, dest)
        print(f"segment vo: {dest}")


def pad_wav_with_silence(src: Path, out: Path, pre_ms: int, post_ms: int) -> None:
    if pre_ms <= 0 and post_ms <= 0:
        shutil.copy2(src, out)
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    inputs: list[str] = []
    labels: list[str] = []
    input_index = 0
    if pre_ms > 0:
        inputs.extend(["-f", "lavfi", "-t", f"{pre_ms / 1000:.3f}", "-i", "anullsrc=r=48000:cl=mono"])
        labels.append(f"[{input_index}:a]")
        input_index += 1
    inputs.extend(["-i", str(src)])
    labels.append(f"[{input_index}:a]")
    input_index += 1
    if post_ms > 0:
        inputs.extend(["-f", "lavfi", "-t", f"{post_ms / 1000:.3f}", "-i", "anullsrc=r=48000:cl=mono"])
        labels.append(f"[{input_index}:a]")
    filt = "".join(labels) + f"concat=n={len(labels)}:v=0:a=1[a]"
    subprocess.run(
        ["ffmpeg", "-y", *inputs, "-filter_complex", filt, "-map", "[a]", "-ac", "1", "-ar", "48000", str(out)],
        check=True,
    )


def progress_payload(
    *,
    status: str,
    segment_id: str | None,
    phase: str,
    message: str,
    percent: int,
    done: int,
    total: int,
    beat_ids: list[str],
    beat_status: dict[str, str],
    completed_beats: list[str],
    current_beat: str | None = None,
    error: str | None = None,
) -> dict:
    payload = {
        "status": status,
        "phase": phase,
        "message": message,
        "percent": percent,
        "segment_id": segment_id,
        "current_beat": current_beat,
        "done": done,
        "total": total,
        "beats": beat_ids,
        "beat_status": beat_status,
        "completed_beats": completed_beats,
    }
    if error:
        payload["error"] = error
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate VO beats via IndexTTS2")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--segment", default=None, help="Only beats in segment e.g. S001")
    parser.add_argument("--beats", nargs="*", help="Only these beat_ids")
    parser.add_argument("--concat", action="store_true")
    parser.add_argument("--force", action="store_true", help="Regenerate even if WAV exists")
    parser.add_argument("--sleep", type=float, default=0.3)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    cfg = load_config(root)
    base = load_base_url(root, args.base_url)
    ref_rel = cfg.get("voice_reference", {}).get("tts_path") or cfg.get("voice_reference", {}).get("path", "audio/refs/narrator_ref.wav")
    example_index = int(cfg.get("voice_reference", {}).get("example_index", 3))

    beats = load_beats(root, args.segment)
    prosody = load_prosody(root)
    last_generated = load_last_generated_text(root)
    if args.beats:
        wanted = set(args.beats)
        beats = [b for b in beats if b["beat_id"] in wanted]

    beat_ids = [row["beat_id"] for row in beats]
    total = len(beats)
    beat_status = {bid: "pending" for bid in beat_ids}
    completed_beats: list[str] = []

    clear_progress(root)
    write_progress(root, progress_payload(
        status="running",
        segment_id=args.segment,
        phase="preflight",
        message=f"检测 IndexTTS 服务 {base}",
        percent=1,
        done=0,
        total=total,
        beat_ids=beat_ids,
        beat_status=beat_status,
        completed_beats=completed_beats,
    ))

    try:
        check_indextts_url(base, timeout=10.0)
    except RuntimeError as exc:
        write_progress(root, progress_payload(
            status="failed",
            segment_id=args.segment,
            phase="preflight",
            message=str(exc),
            percent=0,
            done=0,
            total=total,
            beat_ids=beat_ids,
            beat_status=beat_status,
            completed_beats=completed_beats,
            error=str(exc),
        ))
        print(str(exc), file=sys.stderr)
        return 1

    write_progress(root, progress_payload(
        status="running",
        segment_id=args.segment,
        phase="connecting",
        message=f"正在连接 IndexTTS {base}",
        percent=3,
        done=0,
        total=total,
        beat_ids=beat_ids,
        beat_status=beat_status,
        completed_beats=completed_beats,
    ))

    try:
        client = connect_client(base, timeout=120.0)
    except RuntimeError as exc:
        write_progress(root, progress_payload(
            status="failed",
            segment_id=args.segment,
            phase="connecting",
            message=str(exc),
            percent=0,
            done=0,
            total=total,
            beat_ids=beat_ids,
            beat_status=beat_status,
            completed_beats=completed_beats,
            error=str(exc),
        ))
        print(str(exc), file=sys.stderr)
        return 1

    try:
        ref_path = wav_path_for_ref(root, str(ref_rel).replace("\\", "/"))
    except (FileNotFoundError, RuntimeError):
        ref_path = root / str(ref_rel).replace("\\", "/")

    write_progress(root, progress_payload(
        status="running",
        segment_id=args.segment,
        phase="reference",
        message="加载参考音频…",
        percent=5,
        done=0,
        total=total,
        beat_ids=beat_ids,
        beat_status=beat_status,
        completed_beats=completed_beats,
    ))

    try:
        ref_path = ensure_ref(client, ref_path, example_index)
        ref = handle_file(str(ref_path))
    except Exception as exc:  # noqa: BLE001
        write_progress(root, progress_payload(
            status="failed",
            segment_id=args.segment,
            phase="reference",
            message=f"参考音频失败：{exc}",
            percent=0,
            done=0,
            total=total,
            beat_ids=beat_ids,
            beat_status=beat_status,
            completed_beats=completed_beats,
            error=str(exc),
        ))
        print(f"ref FAIL: {exc}", file=sys.stderr)
        return 1

    out_dir = root / "audio/stems/voice/beats"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = root / "audio/stems/voice/generation_manifest.jsonl"

    generated: list[Path] = []
    done = 0
    with manifest.open("a", encoding="utf-8") as log:
        for row in beats:
            bid = row["beat_id"]
            beat_status[bid] = "running"
            pct = 5 + int((done / max(total, 1)) * 90)
            write_progress(root, progress_payload(
                status="running",
                segment_id=args.segment,
                phase="generating",
                message=f"正在生成 {bid} ({done + 1}/{total})",
                percent=pct,
                done=done,
                total=total,
                beat_ids=beat_ids,
                beat_status=dict(beat_status),
                completed_beats=list(completed_beats),
                current_beat=bid,
            ))
            out = out_dir / f"{bid}.wav"
            p = prosody.get(bid, {})
            text = (p.get("tts_text") or row["narration"]).strip()
            if should_skip_existing_wav(
                force=args.force,
                wav_path=out,
                current_text=text,
                last_generated=last_generated,
                beat_id=bid,
            ):
                print(f"skip {bid}")
                generated.append(out)
                done += 1
                beat_status[bid] = "done"
                completed_beats.append(bid)
                continue
            if out.exists() and out.stat().st_size > 1000 and not args.force:
                print(f"regen {bid} (text changed)")
            seg = row["segment_id"]
            max_tok = min(600, max(80, narration_char_count(row) * 3))
            pre = pause_ms(p, "pre_pause_ms")
            post = pause_ms(p, "post_pause_ms")
            print(f"gen {bid} ({len(text)} chars, pause {pre}+{post}ms)")
            try:
                src = synthesize(client, ref, text, seg, cfg, max_tok)
                raw = out.with_name(f"{out.stem}.__raw__.wav")
                shutil.copy2(src, raw)
                pad_wav_with_silence(raw, out, pre, post)
                try:
                    raw.unlink()
                except OSError:
                    pass
                generated.append(out)
                log.write(json.dumps({
                    "beat_id": bid,
                    "status": "ok",
                    "tts_text": text,
                    "pre_pause_ms": pre,
                    "post_pause_ms": post,
                }, ensure_ascii=False) + "\n")
                last_generated[bid] = text
                done += 1
                beat_status[bid] = "done"
                completed_beats.append(bid)
            except Exception as exc:  # noqa: BLE001
                print(f"FAIL {bid}: {exc}", file=sys.stderr)
                beat_status[bid] = "failed"
                write_progress(root, progress_payload(
                    status="failed",
                    segment_id=args.segment,
                    phase="generating",
                    message=f"{bid} 生成失败：{exc}",
                    percent=pct,
                    done=done,
                    total=total,
                    beat_ids=beat_ids,
                    beat_status=dict(beat_status),
                    completed_beats=list(completed_beats),
                    current_beat=bid,
                    error=str(exc),
                ))
                return 1
            time.sleep(args.sleep)

    if args.concat:
        segment_id = (args.segment or (beats[0]["segment_id"] if beats else "")).upper()
        concat_files, missing = collect_segment_beat_wavs(root, segment_id, out_dir) if segment_id else ([], [])
        if missing:
            preview = ", ".join(missing[:8])
            suffix = f" (+{len(missing) - 8} more)" if len(missing) > 8 else ""
            print(f"warn: {len(missing)} beats missing WAV, skipped in concat: {preview}{suffix}", file=sys.stderr)
        if not concat_files:
            print("concat skipped: no beat WAV files for segment", file=sys.stderr)
        else:
            write_progress(root, progress_payload(
                status="running",
                segment_id=args.segment or segment_id,
                phase="concat",
                message=f"拼接整段配音 ({len(concat_files)} beats)…",
                percent=98,
                done=done,
                total=total,
                beat_ids=beat_ids,
                beat_status=dict(beat_status),
                completed_beats=list(completed_beats),
            ))
            master = root / "audio/stems/voice/voiceover_full.wav"
            concat_wav(concat_files, master)
            print(f"master: {master} ({len(concat_files)} beats)")
            if segment_id:
                publish_segment_vo_copies(root, segment_id, master)

    write_progress(root, progress_payload(
        status="completed",
        segment_id=args.segment,
        phase="completed",
        message=f"配音完成 {done}/{total} beats",
        percent=100,
        done=done,
        total=total,
        beat_ids=beat_ids,
        beat_status=dict(beat_status),
        completed_beats=list(completed_beats),
    ))
    print(f"done: {len(generated)} beats")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
