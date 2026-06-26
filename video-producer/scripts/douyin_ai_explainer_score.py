#!/usr/bin/env python3
"""Score readiness for the Douyin-style Chinese AI explainer recipe.

This gate catches projects that look complete on paper but will still fail the
reference style: dark-premium palette, no diagram primitives, Chinese text baked
into generated images, sparse captions, or unanchored SFX.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def is_light_hex(value: str) -> bool:
    m = re.fullmatch(r"#([0-9a-fA-F]{6})", value.strip())
    if not m:
        return False
    hx = m.group(1)
    r, g, b = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) >= 200


def text_policy_ok(root: Path, storyboard: dict[str, Any], design_text: str) -> bool:
    blob = json.dumps(storyboard, ensure_ascii=False).lower() + "\n" + design_text.lower()
    good = ["html", "svg", "canvas", "remotion", "motion canvas", "text layer", "文本层", "矢量"]
    bad = ["baked text", "generated chinese text", "ai生成中文", "图像模型生成文字", "raster text"]
    return any(g in blob for g in good) and not any(b in blob for b in bad)


def segment_primitives(seg: dict[str, Any]) -> set[str]:
    fields = [
        seg.get("visual_primitives"), seg.get("visuals"), seg.get("assets"),
        seg.get("visual_metaphor"), seg.get("explanation_metaphor"), seg.get("motion_grammar"),
    ]
    text = json.dumps(fields, ensure_ascii=False).lower()
    primitive_names = {
        "machine", "机器", "pipeline", "arrow", "箭头", "card", "卡片", "badge", "标签",
        "stamp", "印章", "network", "神经", "clip", "robot", "机器人", "mascot", "对比",
        "comparison", "scale", "天平", "progress", "grid", "glyph", "字形", "diffusion", "扩散",
    }
    return {p for p in primitive_names if p in text}


def main() -> int:
    parser = argparse.ArgumentParser(description="Score Douyin-style Chinese AI explainer readiness.")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--fail-under", type=int, default=78)
    args = parser.parse_args()
    root = Path(args.root).resolve()

    score = 100
    issues: list[tuple[str, int]] = []
    warnings: list[str] = []

    video = load_json(root / ".video/video.json", {})
    storyboard = load_json(root / "script/storyboard.json", {})
    tokens = load_json(root / "design/tokens.json", {})
    cues = load_json(root / "audio/audio_cue_sheet.json", {})
    design_text = read(root / "design/design.md") + "\n" + read(root / "design/art_direction.md")
    audio_text = read(root / "audio/audio_style_guide.md") + "\n" + read(root / "audio/music_brief.md")

    ratio = str(video.get("ratio") or video.get("aspect_ratio") or storyboard.get("ratio") or "")
    if ratio and ratio not in {"16:9", "9:16"}:
        warnings.append(f"Unusual ratio for this recipe: {ratio}; 16:9 is closest to the reference, 9:16 needs a deliberate adaptation.")

    style_blob = (str(video.get("style")) + " " + json.dumps(storyboard.get("visual_system", {}), ensure_ascii=False) + " " + design_text).lower()
    if not any(k in style_blob for k in ["douyin", "抖音", "ai explainer", "科普", "infographic", "信息图", "light grid", "浅色"]):
        issues.append(("Style recipe does not explicitly name the Douyin/light-grid AI explainer direction.", 10))
    if any(k in style_blob for k in ["dark glass", "premium dark", "dark tech", "黑金", "赛博朋克"]):
        issues.append(("Palette language still points to dark premium-tech; this reference needs light educational infographic.", 12))

    palette = tokens.get("palette", {}) if isinstance(tokens, dict) else {}
    bg = str(palette.get("background", ""))
    if bg and not is_light_hex(bg):
        issues.append((f"Background token is not light/off-white enough for the reference style: {bg}", 10))
    elif not bg:
        issues.append(("design/tokens.json missing palette.background", 6))

    if not text_policy_ok(root, storyboard, design_text):
        issues.append(("No strong Chinese text-layer policy found; exact Chinese must be HTML/SVG/Canvas/Remotion/Motion Canvas text layers.", 18))

    segments = storyboard.get("segments", []) if isinstance(storyboard, dict) else []
    if not segments:
        issues.append(("script/storyboard.json has no segments.", 20))
    else:
        weak_segments = []
        primitive_counts = []
        for seg in segments:
            primitives = segment_primitives(seg if isinstance(seg, dict) else {})
            primitive_counts.append(len(primitives))
            if len(primitives) < 4:
                weak_segments.append(str(seg.get("id", "unknown")))
        if weak_segments:
            issues.append(("Segments lack enough diagram primitives (need 4+ such as machine/card/arrow/badge/robot/network): " + ", ".join(weak_segments[:8]), 14))
        if len(segments) < 5 and float(storyboard.get("total_duration_sec", 0) or 0) > 60:
            warnings.append("Long explainer has few segments; consider 5-9 modules to keep the reference rhythm.")

    cue_list = cues.get("cues", []) if isinstance(cues, dict) else []
    if cue_list:
        anchored = [c for c in cue_list if isinstance(c, dict) and c.get("sync_anchor")]
        sfx = [c for c in cue_list if isinstance(c, dict) and str(c.get("type", "")).startswith("sfx")]
        if len(anchored) / max(1, len(cue_list)) < 0.85:
            issues.append(("Most audio cues need explicit sync_anchor tied to a visible diagram action.", 8))
        if not sfx:
            issues.append(("No SFX cues found; this recipe needs UI ticks, stamp hits, whooshes, or machine beeps anchored to motion.", 10))
    else:
        issues.append(("No audio cues; this style needs a cue sheet parallel to the animation storyboard.", 12))

    if not any(k in audio_text.lower() for k in ["ui", "click", "tick", "stamp", "beep", "whoosh", "subtitle", "caption", "bpm", "duck", "口播", "字幕"]):
        issues.append(("Audio style guide is not specific to fast Chinese infographic narration/SFX.", 8))

    for issue, penalty in issues:
        score -= penalty
    score = max(0, score)

    print(f"Douyin AI explainer score: {score}/100")
    if issues:
        print("Issues:")
        for issue, penalty in issues:
            print(f"- (-{penalty}) {issue}")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    return 0 if score >= args.fail_under else 2


if __name__ == "__main__":
    raise SystemExit(main())
