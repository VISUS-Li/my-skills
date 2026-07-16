#!/usr/bin/env python3
"""Validate depth-research skeleton (not VO prose quality).

Checks the always-tier artifacts from references/deep-research-and-script.md:
  - research/source_cards.jsonl OR a Sources section folded into outputs/script.md
  - research/event_genealogy.md OR a Genealogy section folded into outputs/script.md
  - outputs/script.md present and non-empty

Exit 0 when OK, 1 when blockers, 2 when usage error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


MIN_SCRIPT_CHARS = 80
GENEALOGY_HINTS = (
    "event genealogy",
    "来龙去脉",
    "viewer_harvest",
    "viewer harvest",
    "dig_worthy",
    "- tip:",
    "## genealogy",
    "## 来龙去脉",
)
SOURCE_HINTS = (
    "## sources",
    "## 来源",
    "source_cards",
    "http://",
    "https://",
)


def _nonempty_file(path: Path, *, min_chars: int = 1) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8-sig").strip()
    return len(text) >= min_chars


def _jsonl_has_rows(path: Path) -> bool:
    if not path.is_file():
        return False
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            return True
    return False


def _script_has_any(script: str, hints: tuple[str, ...]) -> bool:
    lower = script.lower()
    return any(h.lower() in lower for h in hints)


def _genealogy_file_usable(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8-sig")
    filled = 0
    for key in ("tip", "upstream", "timeline", "viewer_harvest", "dig_worthy"):
        # Same-line values only — do not let \s swallow newlines into the next bullet.
        m = re.search(rf"^-[ \t]*{key}[ \t]*:[ \t]*(.+?)$", text, flags=re.I | re.M)
        if m and m.group(1).strip():
            filled += 1
    if filled >= 2:
        return True
    # Free-form writeups: require substance AND at least one filled known key,
    # so empty scaffold bullets alone never pass.
    if filled < 1:
        return False
    body = re.sub(r"^#.*$", "", text, flags=re.M).strip()
    return len(body) >= 120


def validate_project(root: Path) -> list[str]:
    errors: list[str] = []
    script_path = root / "outputs" / "script.md"
    if not _nonempty_file(script_path, min_chars=MIN_SCRIPT_CHARS):
        errors.append(
            f"outputs/script.md missing or too short (<{MIN_SCRIPT_CHARS} chars after strip)"
        )
        script_text = ""
    else:
        script_text = script_path.read_text(encoding="utf-8-sig")

    cards = root / "research" / "source_cards.jsonl"
    has_sources = _jsonl_has_rows(cards) or (
        bool(script_text) and _script_has_any(script_text, SOURCE_HINTS)
    )
    if not has_sources:
        errors.append(
            "missing sources: fill research/source_cards.jsonl or fold a Sources section with URLs into outputs/script.md"
        )

    genealogy = root / "research" / "event_genealogy.md"
    has_genealogy = _genealogy_file_usable(genealogy) or (
        bool(script_text) and _script_has_any(script_text, GENEALOGY_HINTS)
    )
    if not has_genealogy:
        errors.append(
            "missing genealogy: fill research/event_genealogy.md (tip/upstream/…/harvest) "
            "or fold a Genealogy / 来龙去脉 section into outputs/script.md"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project",
        required=True,
        type=Path,
        help="Project root (contains outputs/ and optional research/)",
    )
    parser.add_argument(
        "--require-deep-flag",
        action="store_true",
        help="Skip with exit 0 if .video/state.json deep_research is not true",
    )
    args = parser.parse_args()
    root = args.project.resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    if args.require_deep_flag:
        state_path = root / ".video" / "state.json"
        deep = False
        if state_path.is_file():
            import json

            try:
                deep = bool(json.loads(state_path.read_text(encoding="utf-8-sig")).get("deep_research"))
            except json.JSONDecodeError:
                deep = False
        if not deep:
            print("deep_research flag not set; skipping research skeleton checks")
            return 0

    errors = validate_project(root)
    if errors:
        print("validate_research_lite: FAIL")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("validate_research_lite: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
