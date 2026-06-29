#!/usr/bin/env python3
"""Sync segments/{seg}/index.html root data-duration from vo_timing.json total_sec."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def sync_segment_duration(root: Path, segment_id: str) -> dict:
    seg = segment_id.upper()
    vo_path = root / "segments" / seg / "vo_timing.json"
    html_path = root / "segments" / seg / "index.html"
    if not vo_path.exists():
        return {"synced": False, "reason": f"missing {vo_path.name}"}
    if not html_path.exists():
        return {"synced": False, "reason": f"missing {html_path.name}"}

    vo = json.loads(vo_path.read_text(encoding="utf-8-sig"))
    total = float(vo.get("total_sec") or 0)
    if total <= 0:
        return {"synced": False, "reason": "vo_timing total_sec is zero"}

    text = html_path.read_text(encoding="utf-8")
    matches = re.findall(r'data-duration="([0-9.]+)"', text)
    if not matches:
        return {"synced": False, "reason": "index.html missing data-duration"}

    old = float(matches[0])
    if abs(old - total) <= 0.001:
        return {"synced": False, "reason": "already in sync", "total_sec": total, "previous_sec": old}

    total_str = f"{total:.3f}".rstrip("0").rstrip(".")
    new_text = re.sub(r'data-duration="[0-9.]+"', f'data-duration="{total_str}"', text)
    html_path.write_text(new_text, encoding="utf-8")
    return {
        "synced": True,
        "total_sec": total,
        "previous_sec": old,
        "path": html_path.relative_to(root).as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync composition duration from vo_timing.json.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("segment_id", help="Segment id e.g. S001")
    args = parser.parse_args()

    result = sync_segment_duration(Path(args.root).resolve(), args.segment_id)
    if result.get("synced"):
        print(
            f"synced {result['path']}: {result['previous_sec']} -> {result['total_sec']}"
        )
    else:
        print(f"skip: {result.get('reason')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
