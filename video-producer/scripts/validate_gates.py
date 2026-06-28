#!/usr/bin/env python3
"""CI gate: fail when progressed stages have unapproved upstream dependencies."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from review_core import check_render_allowed, validate_gates  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate stage dependency gates.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--stage", default=None, help="Check render/run permission for a stage")
    parser.add_argument("--quiet", action="store_true", help="Only print errors")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    if args.stage:
        errors = check_render_allowed(root, args.stage)
    else:
        errors = validate_gates(root)

    if errors:
        if not args.quiet:
            print("Gate validation failed:")
            for err in errors:
                print(f"- {err}")
        return 1
    if not args.quiet:
        print("Gate validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
