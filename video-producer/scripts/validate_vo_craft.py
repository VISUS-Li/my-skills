#!/usr/bin/env python3
"""Lint analytical VO for teaching-deconstruction anti-patterns.

Flags phrases that push agents into stiff "名词课" voice instead of story entry.
Exit 0 when clean or only soft warnings; exit 1 when hard blockers found.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Hard blockers — almost always bad in analytical VO
HARD_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("teaching_deconstruction:你就记", re.compile(r"你就记")),
    ("teaching_deconstruction:别听成黑话", re.compile(r"别听成黑话")),
    ("teaching_deconstruction:别听成", re.compile(r"别听成")),
    ("teaching_deconstruction:你可以把它理解成", re.compile(r"你可以把它理解成")),
    ("teaching_deconstruction:你就当作", re.compile(r"你就当作")),
    ("teaching_deconstruction:简单来说就是", re.compile(r"简单来说就是")),
    ("channel_shell:欢迎收听", re.compile(r"欢迎收听")),
    ("channel_shell:点赞.*小铃铛|小铃铛", re.compile(r"小铃铛|点个赞|一键三连")),
]

# Soft warnings — overused connectors or lecture smells; do not alone fail
SOFT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("soft:所以呢_quota", re.compile(r"所以呢")),
    ("soft:但是呢_quota", re.compile(r"但是呢")),
    ("soft:那问题来了_quota", re.compile(r"那问题来了")),
    ("soft:大家注意_quota", re.compile(r"大家注意")),
    ("soft:你看_lecture", re.compile(r"你看[，,]")),
]

SOFT_QUOTA = {
    "soft:所以呢_quota": 4,
    "soft:但是呢_quota": 4,
    "soft:那问题来了_quota": 3,
    "soft:大家注意_quota": 3,
    "soft:你看_lecture": 4,
}


def _extract_vo(script: str) -> str:
    """Prefer VO section; else whole script body."""
    m = re.search(
        r"##\s*VO[^\n]*\n(.*?)(?=\n##\s|\Z)",
        script,
        flags=re.S | re.I,
    )
    if m:
        return m.group(1)
    return script


def lint_text(text: str) -> tuple[list[str], list[str]]:
    hard: list[str] = []
    soft: list[str] = []
    for label, pat in HARD_PATTERNS:
        hits = pat.findall(text)
        if hits:
            hard.append(f"{label} x{len(hits)}")
    for label, pat in SOFT_PATTERNS:
        hits = pat.findall(text)
        limit = SOFT_QUOTA.get(label, 3)
        if len(hits) > limit:
            soft.append(f"{label} x{len(hits)} (>{limit}; connectors are optional, not a quota)")
    return hard, soft


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True, help="Project root")
    parser.add_argument(
        "--script",
        type=Path,
        default=None,
        help="Optional path to script.md (default: <project>/outputs/script.md)",
    )
    args = parser.parse_args()
    script_path = args.script or (args.project.resolve() / "outputs" / "script.md")
    if not script_path.is_file():
        print(f"validate_vo_craft: FAIL\n  - missing {script_path}", file=sys.stderr)
        return 1

    raw = script_path.read_text(encoding="utf-8-sig")
    vo = _extract_vo(raw)
    hard, soft = lint_text(vo)

    if hard:
        print("validate_vo_craft: FAIL")
        for item in hard:
            print(f"  - BLOCK {item}")
        for item in soft:
            print(f"  - WARN {item}")
        print("Rewrite per references/narrative-depth-copy.md (story entry, not teaching deconstruction).")
        return 1

    print("validate_vo_craft: OK")
    for item in soft:
        print(f"  - WARN {item}")
    if not soft:
        print("  - no teaching-deconstruction anti-patterns detected in VO section")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
