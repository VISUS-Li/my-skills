#!/usr/bin/env python3
"""Validate one workflow stage before stage_gate review/approved."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from stage_validation import (  # noqa: E402
    default_segment,
    validate_stage_complete,
    validate_stage_readiness,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate stage readiness (artifacts + beat contract + lint).")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--stage", required=True, help="Stage id from stage_manifest.json (e.g. script, director-plan)")
    parser.add_argument("--segment", default=None, help="Segment id (default: first segment in video.json)")
    parser.add_argument("--skip-scripts", action="store_true", help="Skip validation_scripts from stage_manifest")
    parser.add_argument("--artifacts-only", action="store_true", help="Only check required_artifacts exist")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    segment = args.segment or default_segment(root)

    if args.artifacts_only:
        from stage_validation import validate_required_artifacts  # noqa: E402

        errors = validate_required_artifacts(root, args.stage, segment)
    else:
        errors = validate_stage_complete(
            root,
            args.stage,
            segment=segment,
            run_scripts=not args.skip_scripts,
        )

    if errors:
        print(f"Stage {args.stage} validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print(f"Stage {args.stage} validation passed (segment {segment}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
