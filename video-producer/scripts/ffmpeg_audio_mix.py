#!/usr/bin/env python3
"""Generate a deterministic FFmpeg command draft for audio cue mixing.

The script only uses cues whose path_or_url points to an existing local file. It
writes edit/audio_mix_command.sh and can optionally run it with --execute.
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from pathlib import Path
from typing import Any


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def db_to_linear(db: float) -> float:
    return 10 ** (db / 20)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create FFmpeg audio mix command from audio_cue_sheet.json.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--output", default="edit/final_audio_mix.wav", help="Output audio path inside project")
    parser.add_argument("--execute", action="store_true", help="Run the generated command")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    cue_sheet = load_json(root / "audio" / "audio_cue_sheet.json", {"cues": []})
    mix_plan = load_json(root / "audio" / "audio_mix_plan.json", {})
    cues = [c for c in cue_sheet.get("cues", []) if isinstance(c, dict)]

    usable: list[dict[str, Any]] = []
    missing: list[str] = []
    for c in cues:
        rel = str(c.get("path_or_url", "")).strip()
        if not rel:
            continue
        p = Path(rel)
        if not p.is_absolute():
            p = root / p
        if p.exists() and p.is_file():
            usable.append({**c, "_abs_path": str(p)})
        else:
            missing.append(rel)

    out = root / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    script_path = root / "edit" / "audio_mix_command.sh"
    if not usable:
        script_path.write_text(
            "#!/usr/bin/env bash\nset -euo pipefail\n"
            "echo 'No local audio assets with path_or_url were found in audio/audio_cue_sheet.json.'\n",
            encoding="utf-8",
        )
        script_path.chmod(0o755)
        print(f"No usable local audio cue files. Wrote placeholder {script_path}")
        if missing:
            print("Missing cue assets:")
            for m in missing:
                print(f"- {m}")
        return 2

    inputs = []
    chains = []
    labels = []
    for i, c in enumerate(usable):
        inputs += ["-i", c["_abs_path"]]
        start_ms = int(round(float(c.get("start_sec", 0)) * 1000))
        duration = max(float(c.get("duration_sec", 0.1)), 0.05)
        gain = db_to_linear(float(c.get("gain_db", -12)))
        fade_in = max(int(c.get("fade_in_ms", 20)), 0) / 1000
        fade_out = max(int(c.get("fade_out_ms", 60)), 0) / 1000
        label = f"a{i}"
        labels.append(f"[{label}]")
        filters = [f"[{i}:a]aresample=48000,atrim=0:{duration:.3f},asetpts=PTS-STARTPTS,volume={gain:.6f}"]
        if fade_in > 0:
            filters.append(f"afade=t=in:st=0:d={fade_in:.3f}")
        if fade_out > 0 and duration > fade_out:
            filters.append(f"afade=t=out:st={max(duration - fade_out, 0):.3f}:d={fade_out:.3f}")
        filters.append(f"adelay={start_ms}:all=1")
        filters.append(f"apad")
        filters.append(f"atrim=0:{max(float(c.get('start_sec', 0)) + duration + 2, duration + 2):.3f}")
        chains.append(",".join(filters) + f"[{label}]")

    target = mix_plan.get("target_loudness", {}) if isinstance(mix_plan, dict) else {}
    lufs = float(target.get("integrated_lufs", -16))
    tp = float(target.get("true_peak_db", -1.0))
    lra = float(target.get("lra", 11))
    mix_filter = "".join(chains) + ";" + "".join(labels) + f"amix=inputs={len(labels)}:duration=longest:dropout_transition=0:normalize=0,loudnorm=I={lufs}:TP={tp}:LRA={lra}[out]"
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", mix_filter, "-map", "[out]", str(out)]

    quoted = " ".join(shlex.quote(x) for x in cmd)
    script_path.write_text(f"#!/usr/bin/env bash\nset -euo pipefail\n{quoted}\n", encoding="utf-8")
    script_path.chmod(0o755)
    print(f"Wrote {script_path}")
    print(f"Output: {out}")
    if missing:
        print("Skipped missing cue assets:")
        for m in missing:
            print(f"- {m}")
    if args.execute:
        return subprocess.call(cmd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
