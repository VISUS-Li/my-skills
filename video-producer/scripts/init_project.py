#!/usr/bin/env python3
"""Create an isolated, self-contained Video Producer Remotion project."""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


FORMATS = {
    "vertical": (1080, 1920),
    "horizontal": (1920, 1080),
    "square": (1080, 1080),
}


def project_id(name: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip()).strip("-").lower()
    return value or "video-project"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Human-readable project name")
    parser.add_argument("--output", required=True, help="New project directory")
    parser.add_argument("--format", choices=sorted(FORMATS), default="vertical")
    parser.add_argument("--fps", type=float, default=30)
    args = parser.parse_args()

    if args.fps <= 0:
        raise ValueError("--fps must be positive")
    output = Path(args.output).expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing path: {output}")

    template = Path(__file__).resolve().parents[1] / "assets" / "remotion-template"
    if not template.is_dir():
        raise FileNotFoundError(f"missing Remotion template: {template}")
    shutil.copytree(
        template,
        output,
        ignore=shutil.ignore_patterns("node_modules", "renders", "out", ".cache", "__pycache__"),
    )

    plan_path = output / "video-plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    width, height = FORMATS[args.format]
    plan["video"].update(
        {
            "id": project_id(args.name),
            "fps": args.fps,
            "width": width,
            "height": height,
        }
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    (output / "script.md").write_text(
        f"# {args.name}\n\n## Brief\n\n## Script\n\n## Director notes\n",
        encoding="utf-8",
    )
    for relative in ("public/audio/voice", "public/audio/sfx", "public/audio/bgm", "public/media"):
        (output / relative).mkdir(parents=True, exist_ok=True)

    print(f"initialized project: {output}")
    print("next:")
    print(f"  1. Edit {output / 'script.md'}")
    print(f"  2. Edit {plan_path}")
    print(f"  3. python validate_video_plan.py {plan_path}")
    print(f"  4. cd {output} && npm ci && npm run typecheck && npm run qa:still")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
