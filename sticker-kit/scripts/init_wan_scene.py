#!/usr/bin/env python3
"""Scaffold a Wan layered-video project from a reusable scene template."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


TEMPLATES = {
    "generic": "scene_plan_generic.json",
    "dragon-rescue": "scene_plan_dragon_rescue.json",
    "dragon_rescue": "scene_plan_dragon_rescue.json",
}


def main() -> None:
    ap = argparse.ArgumentParser(description="Initialize Mode D-Wan project")
    ap.add_argument("--template", choices=sorted(TEMPLATES), default="generic")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--project-name", default=None)
    ap.add_argument("--style-id", default=None)
    args = ap.parse_args()

    skill_root = Path(__file__).resolve().parents[1]
    source = skill_root / "assets" / "templates" / TEMPLATES[args.template]
    plan = json.loads(source.read_text(encoding="utf-8"))
    if args.project_name:
        plan["project"]["name"] = args.project_name
    if args.style_id:
        plan["project"]["style_id"] = args.style_id

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    for folder in (
        "assets/backgrounds",
        "assets/elements",
        "renders/raw",
        "renders/rgba",
        "renders/composite_frames",
    ):
        (out / folder).mkdir(parents=True, exist_ok=True)
    (out / "scene_plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"OK Wan scene scaffold → {out.resolve()}")
    print("next: replace asset placeholders, then run compile_wan_scene.py")


if __name__ == "__main__":
    main()
