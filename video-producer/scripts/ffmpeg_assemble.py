#!/usr/bin/env python3
"""Generate a conservative FFmpeg concat command from edit/timeline.json.

This script does not attempt complex overlays. It creates a concat file and a
shell script for simple segment concatenation. More advanced timelines should be
assembled manually or by a dedicated editor/video-use workflow.
"""
from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate FFmpeg assembly script.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--output", default="exports/final.mp4", help="Output path relative to root")
    parser.add_argument("--dry-run", action="store_true", help="Only print the generated command")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    timeline_path = root / "edit/timeline.json"
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    video_track = next((t for t in timeline.get("tracks", []) if t.get("type") == "video"), None)
    if not video_track:
        raise SystemExit("timeline has no video track")

    concat_file = root / "edit/concat.txt"
    lines = []
    missing = []
    for item in video_track.get("items", []):
        src = root / item["src"]
        if not src.exists():
            missing.append(item["src"])
        lines.append(f"file '{src.as_posix()}'")
    concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    output_path = root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c",
        "copy",
        str(output_path),
    ]
    script_path = root / "edit/assembly_command.sh"
    script_path.write_text("#!/usr/bin/env bash\nset -euo pipefail\n" + " ".join(shlex.quote(c) for c in cmd) + "\n", encoding="utf-8")
    script_path.chmod(0o755)

    if missing:
        print("Cannot assemble yet; missing segment files:")
        for m in missing:
            print(f"- {m}")
        print(f"Wrote draft command: {script_path}")
        return 2

    print("Generated command:")
    print(" ".join(shlex.quote(c) for c in cmd))
    print(f"Wrote {script_path}")
    if not args.dry_run:
        print("Dry-run mode is recommended for agents. Execute the script manually or after approval.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
