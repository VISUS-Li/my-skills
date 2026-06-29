#!/usr/bin/env python3
"""Regenerate Chinese SVG assets with guaranteed UTF-8 (Windows-safe).

Do NOT edit Chinese SVG by hand in the IDE — run this script after changing LABELS.
"""
from __future__ import annotations

from pathlib import Path

# Edit LABELS then: python rebuild_chinese.py
LABELS: dict[str, str] = {
    "example_title": "示例标题",
    "example_caption": "来源：示例媒体",
}

FONT_STACK = '"Noto Sans SC", "Microsoft YaHei", "PingFang SC", sans-serif'


def svg_header() -> str:
    return '<?xml version="1.0" encoding="UTF-8"?>\n'


def write_example_card(out: Path) -> None:
    title = LABELS["example_title"]
    body = f"""{svg_header()}<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 360">
  <rect width="640" height="360" rx="16" fill="#F7F1E6" stroke="#1F2937" stroke-width="2"/>
  <text class="cn" x="32" y="64" font-size="28" font-weight="700" fill="#1F2937">{title}</text>
  <style>.cn {{ font-family: {FONT_STACK}; }}</style>
</svg>
"""
    out.write_text(body, encoding="utf-8")
    print(f"wrote {out}")


def main() -> int:
    assets = Path(__file__).resolve().parent
    write_example_card(assets / "card_example.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
