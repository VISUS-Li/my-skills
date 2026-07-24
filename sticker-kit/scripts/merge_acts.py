#!/usr/bin/env python3
"""将分幕 ordered 帧合并为全局 ordered/ 序列。"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def list_frames(folder: Path) -> list[Path]:
    return sorted(folder.glob("frame_*.png"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("acts_json", type=Path, help="acts.json (defines act order)")
    ap.add_argument(
        "--layer",
        default="character",
        help="Which layer folder under each act to merge (default: character)",
    )
    ap.add_argument(
        "--acts-root",
        type=Path,
        default=None,
        help="Root containing acts/<id>/<layer>/ordered (default: dirname of acts.json)",
    )
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument(
        "--from-subdir",
        default="ordered",
        help="Subfolder name under act/layer (ordered|bridges-merged)",
    )
    args = ap.parse_args()

    data = json.loads(args.acts_json.read_text(encoding="utf-8"))
    root = args.acts_root or args.acts_json.parent
    args.out.mkdir(parents=True, exist_ok=True)

    # clear old frame_*.png
    for old in args.out.glob("frame_*.png"):
        old.unlink()

    idx = 1
    manifest_acts = []
    for act in data.get("acts", []):
        aid = act["id"]
        src_dir = root / "acts" / aid / args.layer / args.from_subdir
        frames = list_frames(src_dir)
        if not frames:
            raise SystemExit(f"no frames in {src_dir}")
        start = idx
        for f in frames:
            dst = args.out / f"frame_{idx:03d}.png"
            shutil.copy2(f, dst)
            idx += 1
        manifest_acts.append(
            {
                "id": aid,
                "start": start,
                "end": idx - 1,
                "count": len(frames),
                "source": str(src_dir),
            }
        )

    meta = {
        "layer": args.layer,
        "total": idx - 1,
        "acts": manifest_acts,
        "project": data.get("project"),
        "style_id": data.get("style_id"),
    }
    (args.out / "merge_manifest.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"OK merged {meta['total']} frames → {args.out.resolve()}")
    for a in manifest_acts:
        print(f"  {a['id']}: {a['start']:03d}-{a['end']:03d} ({a['count']})")


if __name__ == "__main__":
    main()
