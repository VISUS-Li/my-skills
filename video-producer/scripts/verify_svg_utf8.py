#!/usr/bin/env python3
"""Verify SVG files are valid UTF-8 without BOM; flag mojibake / missing XML declaration."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_CJK = re.compile(r"[\u4e00-\u9fff]")
_MOJIBAKE = re.compile(r"[\ufffd]|(?:\?){3,}")
_XML_DECL = re.compile(r'<\?xml[^>]*encoding\s*=\s*["\']UTF-8["\']', re.I)


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        issues.append("UTF-8 BOM present")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        issues.append(f"invalid UTF-8: {exc}")
        return issues
    if _CJK.search(text):
        if not _XML_DECL.search(text[:200]):
            issues.append("Chinese text but missing <?xml ... encoding=\"UTF-8\"?> header")
        if "?" in text and _MOJIBAKE.search(text):
            issues.append("possible mojibake (replacement ? sequences)")
        if "font-family" not in text.lower() and "<text" in text.lower():
            issues.append("Chinese <text> without font-family stack")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify SVG UTF-8 encoding (Windows/Chinese safe).")
    parser.add_argument("paths", nargs="+", help="SVG files or directories")
    parser.add_argument("--fail-on-warn", action="store_true", help="Exit 1 on any issue")
    args = parser.parse_args()

    files: list[Path] = []
    for p in args.paths:
        path = Path(p).resolve()
        if path.is_dir():
            files.extend(sorted(path.rglob("*.svg")))
        elif path.suffix.lower() == ".svg":
            files.append(path)

    if not files:
        print("no SVG files found", file=sys.stderr)
        return 1

    bad = 0
    for f in files:
        issues = check_file(f)
        if issues:
            bad += 1
            print(f"FAIL {f}")
            for msg in issues:
                print(f"  - {msg}")
        else:
            print(f"OK   {f}")

    if bad:
        print(f"\n{ bad }/{len(files)} SVG files failed", file=sys.stderr)
        return 1
    print(f"all {len(files)} SVG files passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
