#!/usr/bin/env python3
"""Print agent-readable regen queue tasks and suggested commands."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from review_core import load_regen_queue, read_registry_lines, registry_index  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Dispatch regen queue tasks for agents.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--dry-run", action="store_true", help="Print suggested commands only")
    parser.add_argument("--status", default="pending", help="Filter queue status")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    queue = load_regen_queue(root)
    registry = registry_index(read_registry_lines(root))
    items = [item for item in queue.get("items", []) if item.get("status") == args.status]
    rejected = [row for row in registry.values() if row.get("status") == "rejected"]

    print(f"Project: {root}")
    print(f"Pending queue items: {len(items)}")
    print(f"Rejected artifacts: {len(rejected)}")
    for item in items:
        print("\n---")
        print(json.dumps(item, ensure_ascii=False, indent=2))
        commands = item.get("commands_suggested") or []
        if args.dry_run and commands:
            print("Suggested commands:")
            for cmd in commands:
                print(f"  {cmd}")
    for row in rejected:
        print("\n--- rejected artifact ---")
        print(json.dumps({
            "artifact_id": row.get("artifact_id"),
            "path": row.get("path"),
            "note": row.get("reviewer_note"),
        }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
