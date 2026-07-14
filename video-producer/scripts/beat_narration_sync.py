#!/usr/bin/env python3
"""Sync voice_text edits from beat_plan into outputs/script.md."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from beat_store import sync_script_from_plan  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    path = sync_script_from_plan(root)
    if not path:
        print("outputs/script.md missing")
        return 1
    print(f"synced voice lines to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
