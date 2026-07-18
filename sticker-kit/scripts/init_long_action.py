#!/usr/bin/env python3
"""Scaffold an image-only long-action sticker-kit project from a template."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

TEMPLATES = {
    "kamehameha": "acts_kamehameha.json",
    "sword_fly": "acts_sword_fly.json",
    "sword-fly": "acts_sword_fly.json",
    "generic": "acts_generic_long.json",
    "long": "acts_generic_long.json",
}


def main() -> None:
    ap = argparse.ArgumentParser(description="Init Mode D-Long project folder")
    ap.add_argument("--template", default="generic", help="kamehameha | sword_fly | generic")
    ap.add_argument("--out", type=Path, required=True, help="Project output directory")
    ap.add_argument("--style-id", default=None, help="Override style_id in acts.json")
    ap.add_argument("--project-name", default=None, help="Override project name")
    args = ap.parse_args()

    skill_root = Path(__file__).resolve().parents[1]
    tmpl_name = TEMPLATES.get(args.template.replace("-", "_"), TEMPLATES.get(args.template))
    if not tmpl_name:
        raise SystemExit(f"unknown template {args.template!r}; choose: {', '.join(TEMPLATES)}")
    src = skill_root / "assets" / "templates" / tmpl_name
    if not src.exists():
        raise SystemExit(f"missing template file: {src}")

    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    acts = json.loads(src.read_text(encoding="utf-8"))
    if args.style_id:
        acts["style_id"] = args.style_id
    if args.project_name:
        acts["project"] = args.project_name

    (out / "acts.json").write_text(json.dumps(acts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    layers = acts.get("layers") or ["character"]
    for layer in layers:
        (out / "layers" / layer / "anchors").mkdir(parents=True, exist_ok=True)
    for act in acts.get("acts", []):
        aid = act["id"]
        for layer in layers:
            base = out / "acts" / aid / layer
            for sub in ("raw", "rgba", "ordered", "takes/take_a", "takes/take_b", "bridges"):
                (base / sub).mkdir(parents=True, exist_ok=True)

    (out / "ordered").mkdir(parents=True, exist_ok=True)
    (out / "motion").mkdir(parents=True, exist_ok=True)
    (out / "shared").mkdir(parents=True, exist_ok=True)

    readme = f"""# {acts.get('project', 'long-action')} (Mode D-Long)

style_id: `{acts.get('style_id')}`
target unique frames: {acts.get('target_unique_frames')} (+ bridge reserve {acts.get('bridge_reserve', 0)})
layers: {', '.join(layers)}
fps: {acts.get('fps', 12)}  hold: {acts.get('hold', 1)}

## Next steps

1. Write `shared/parts.json` (topology + color lock).
2. Generate `layers/character/anchors/anchor_greenscreen.png` (+ vfx anchor if layered).
3. `python scripts/expand_stages.py {out.as_posix()}/acts.json`
4. Per act / layer: GenerateImage micro-stages → cutout → ordered.
5. `qa_frames.py ... --write-bridges` → bridge gaps → re-QA.
6. `merge_acts.py` → optional `compose_layers.py` → `pack_motion.py --hold 1`.

See skill `long-action.md`.
"""
    (out / "README.md").write_text(readme, encoding="utf-8")
    print(f"OK scaffold → {out.resolve()}")
    print(f"  acts: {len(acts.get('acts', []))}  layers: {layers}")
    print(f"  template: {tmpl_name}")


if __name__ == "__main__":
    main()
