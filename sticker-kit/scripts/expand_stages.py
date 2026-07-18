#!/usr/bin/env python3
"""Expand acts.json into per-act numbered micro-stage lists (stages.json + .md)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def lerp_label(i: int, n: int, beats: list[dict]) -> str:
    for b in beats or []:
        lo, hi = b.get("span") or [1, n]
        if lo <= i <= hi:
            # progress inside beat
            return str(b.get("desc") or "micro step")
    return "micro step"


def expand_act(act: dict) -> list[dict]:
    n = int(act["unique_frames"])
    beats = act.get("stage_beats") or []
    summary = act.get("beat_summary") or ""
    stages = []
    for i in range(1, n + 1):
        t = (i - 1) / max(n - 1, 1)
        stages.append(
            {
                "index": i,
                "id": f"{act['id']}_{i:02d}",
                "action_class": act.get("action_class"),
                "progress": round(t, 4),
                "delta_hint": lerp_label(i, n, beats),
                "free_channels": act.get("free_channels") or ["pose"],
                "vfx_free": (act.get("vfx") or {}).get("free_channels") or [],
                "prompt_stub": (
                    f"Act {act['id']} frame {i}/{n} (~{int(t*100)}%). "
                    f"Delta only: {lerp_label(i, n, beats)}. "
                    f"Action class lock: {act.get('action_class')}. "
                    f"Overall beat: {summary}"
                ),
            }
        )
    return stages


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("acts_json", type=Path)
    ap.add_argument(
        "-o",
        "--out-dir",
        type=Path,
        default=None,
        help="Default: same directory as acts.json",
    )
    args = ap.parse_args()

    acts_path: Path = args.acts_json
    data = json.loads(acts_path.read_text(encoding="utf-8"))
    out_dir = args.out_dir or acts_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    all_stages: dict = {
        "project": data.get("project"),
        "style_id": data.get("style_id"),
        "topology_lock": data.get("topology_lock"),
        "target_unique_frames": data.get("target_unique_frames"),
        "acts": {},
    }

    md_lines = [
        f"# Stages — {data.get('project')}",
        "",
        f"style_id: `{data.get('style_id')}`",
        f"topology: {data.get('topology_lock')}",
        "",
    ]

    total = 0
    for act in data.get("acts", []):
        stages = expand_act(act)
        all_stages["acts"][act["id"]] = {
            "title": act.get("title"),
            "unique_frames": act.get("unique_frames"),
            "action_class": act.get("action_class"),
            "stages": stages,
        }
        total += len(stages)
        act_dir = out_dir / "acts" / act["id"]
        act_dir.mkdir(parents=True, exist_ok=True)
        (act_dir / "stages.json").write_text(
            json.dumps(all_stages["acts"][act["id"]], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        md_lines.append(f"## Act `{act['id']}` — {act.get('title')} ({len(stages)} frames)")
        md_lines.append("")
        for s in stages:
            md_lines.append(f"- `{s['id']}`: {s['delta_hint']}")
        md_lines.append("")

    all_stages["expanded_total"] = total
    (out_dir / "stages.json").write_text(
        json.dumps(all_stages, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "stages.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    target = int(data.get("target_unique_frames") or total)
    print(f"OK expanded {total} stages (target {target}) → {out_dir / 'stages.json'}")
    if total < target - int(data.get("bridge_reserve") or 0):
        print(
            f"WARN: expanded {total} < target {target}; add frames to acts or rely on bridges",
            flush=True,
        )


if __name__ == "__main__":
    main()
