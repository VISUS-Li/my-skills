# SVG UTF-8 on Windows（快速检查表）

Parent: `references/hyperframes-implementation.md`

## Do

- Python `write_text(..., encoding="utf-8")` or `rebuild_chinese.py`
- `<?xml version="1.0" encoding="UTF-8"?>` first line
- CJK `font-family` on every `<text>` with Chinese
- `python scripts/verify_svg_utf8.py segments/S001/assets` before segment gate

## Don't

- Agent Write tool / Notepad save for Chinese SVG
- UTF-8 with BOM
- Assume Git or editor "auto encoding" on Windows

## Fix mojibake

1. Delete broken SVG
2. Restore strings in `rebuild_chinese.py` LABELS
3. Re-run script; re-run `verify_svg_utf8.py`
