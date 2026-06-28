#!/usr/bin/env python3
"""Update a stage status in .video/state.json without destroying history."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from review_core import append_history, validate_stage_dependencies  # noqa: E402

VALID_STATUSES = {"draft", "review", "approved", "locked", "needs-revision", "rendered", "failed"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Update stage status.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--stage", required=True, help="Stage name")
    parser.add_argument("--status", required=True, choices=sorted(VALID_STATUSES), help="New status")
    parser.add_argument("--artifact", action="append", default=[], help="Artifact path to attach to stage")
    parser.add_argument("--note", default="", help="Status note")
    parser.add_argument(
        "--require-deps-approved",
        action="store_true",
        help="Fail if direct upstream stages are not approved|locked",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.require_deps_approved or args.status in {"review", "approved", "locked", "rendered"}:
        dep_errors = validate_stage_dependencies(root, args.stage, target_status=args.status)
        if dep_errors:
            for err in dep_errors:
                print(err)
            return 1
    state_path = root / ".video/state.json"
    if not state_path.exists():
        raise SystemExit(f"missing state file: {state_path}")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    stages = state.setdefault("stages", {})
    stage = stages.setdefault(args.stage, {"status": "draft", "artifacts": []})
    previous = stage.get("status")
    if previous == "locked" and args.status != "locked":
        raise SystemExit(f"stage {args.stage} is locked; unlock explicitly by editing state.json or creating a new version")
    artifacts = stage.setdefault("artifacts", [])
    for artifact in args.artifact:
        if artifact not in artifacts:
            artifacts.append(artifact)
    stage["status"] = args.status
    stage["updated_at"] = datetime.now(timezone.utc).isoformat()
    history = state.setdefault("history", [])
    history.append({
        "stage": args.stage,
        "from": previous,
        "to": args.status,
        "note": args.note,
        "artifacts": args.artifact,
        "at": stage["updated_at"],
    })
    state["current_stage"] = args.stage
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    append_history(root, {
        "type": "stage_gate",
        "stage": args.stage,
        "from": previous,
        "to": args.status,
        "note": args.note,
        "artifacts": args.artifact,
    })
    print(f"{args.stage}: {previous} -> {args.status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
