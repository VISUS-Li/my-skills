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

try:
    from gradio_client import Client, handle_file
except ImportError:
    print("pip install gradio_client", file=sys.stderr)
    raise


def load_config(root: Path) -> dict:
    cfg_path = root / "audio/indextts2_config.json"
    if cfg_path.exists():
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    return {"base_url": "http://127.0.0.1:7860/", "voice_reference": {"path": "audio/refs/narrator_ref.wav"}}


def ensure_ref(client: Client, ref_path: Path, example_index: int = 3) -> Path:
    if ref_path.exists() and ref_path.stat().st_size > 50_000 and ref_path.read_bytes()[:4] == b"RIFF":
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


def concat_wav(files: list[Path], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    lst = out.with_suffix(".txt")
    lst.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in files), encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)], check=True)


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
    base = args.base_url or cfg.get("base_url", "http://127.0.0.1:7860/")
    ref_rel = cfg.get("voice_reference", {}).get("path", "audio/refs/narrator_ref.wav")
    ref_path = root / ref_rel
    example_index = int(cfg.get("voice_reference", {}).get("example_index", 3))

    beats = load_beats(root, args.segment)
    if args.beats:
        wanted = set(args.beats)
        beats = [b for b in beats if b["beat_id"] in wanted]

    out_dir = root / "audio/stems/voice/beats"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = root / "audio/stems/voice/generation_manifest.jsonl"

    client = Client(base)
    ref_path = ensure_ref(client, ref_path, example_index)
    ref = handle_file(str(ref_path))

    generated: list[Path] = []
    with manifest.open("a", encoding="utf-8") as log:
        for row in beats:
            bid = row["beat_id"]
            out = out_dir / f"{bid}.wav"
            if not args.force and out.exists() and out.stat().st_size > 1000:
                print(f"skip {bid}")
                generated.append(out)
                continue
            text = row["narration"].strip()
            seg = row["segment_id"]
            max_tok = min(600, max(80, int(row["char_count"]) * 3))
            print(f"gen {bid} ({len(text)} chars)")
            try:
                src = synthesize(client, ref, text, seg, cfg, max_tok)
                shutil.copy2(src, out)
                generated.append(out)
                log.write(json.dumps({"beat_id": bid, "status": "ok"}, ensure_ascii=False) + "\n")
            except Exception as exc:  # noqa: BLE001
                print(f"FAIL {bid}: {exc}", file=sys.stderr)
                return 1
            time.sleep(args.sleep)

    if args.concat and generated:
        master = root / "audio/stems/voice/voiceover_full.wav"
        concat_wav(generated, master)
        print(f"master: {master}")

    print(f"done: {len(generated)} beats")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
