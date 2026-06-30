#!/usr/bin/env python3
"""Score whether a video project has enough aesthetic and cinematic planning.

This is not a substitute for human taste. It catches common agent failures:
empty frames, text-only segments, missing color hierarchy, no shot language,
no assets, no camera movement, and insufficient depth/layering.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def count_nonempty_palette(tokens: dict[str, Any]) -> int:
    palette = tokens.get("palette", {}) if isinstance(tokens, dict) else {}
    if not isinstance(palette, dict):
        return 0
    return sum(1 for v in palette.values() if isinstance(v, str) and v.strip())


def load_asset_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as f:
            return [row for row in csv.DictReader(f)]
    except Exception:
        return []


def filled_art_direction_lines(art_text: str) -> int:
    """Count lines that look intentionally filled rather than template placeholders."""
    count = 0
    placeholders = {"describe", "what should", "opening feeling", "midpoint feeling", "ending feeling"}
    for raw in art_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        low = line.lower()
        if any(p in low for p in placeholders):
            continue
        if line in {"-", "1.", "2.", "3."}:
            continue
        if ":" in line:
            value = line.split(":", 1)[1].strip()
            if value:
                count += 1
        elif line.startswith("-") and len(line.strip("- ")) > 8:
            count += 1
        elif len(line) > 30:
            count += 1
    return count


def score_design(root: Path, tokens: dict[str, Any], art_text: str, design_text: str) -> tuple[int, list[str], list[str]]:
    score = 0
    blockers: list[str] = []
    tips: list[str] = []
    palette_count = count_nonempty_palette(tokens)
    if palette_count >= 6:
        score += 8
    else:
        blockers.append("Palette is under-specified: provide at least 6 color roles in design/tokens.json.")
    if tokens.get("colorRatio") or re.search(r"60\s*/\s*30\s*/\s*10|60%", design_text + art_text):
        score += 5
    else:
        tips.append("Add a dominant/support/accent color ratio, usually 60/30/10.")
    if isinstance(tokens.get("typography"), dict) and len(tokens["typography"]) >= 3:
        score += 5
    else:
        blockers.append("Typography hierarchy is missing: define display/heading/body or equivalent levels.")
    if isinstance(tokens.get("layout"), dict) and tokens["layout"].get("safeArea"):
        score += 4
    else:
        tips.append("Add platform safe-area and focal zones to tokens.json.")
    if isinstance(tokens.get("motion"), dict) and tokens["motion"].get("cameraMoves"):
        score += 4
    else:
        tips.append("Add default camera moves and easing rules to tokens.json.")
    filled = filled_art_direction_lines(art_text)
    if filled >= 8:
        score += 4
    elif filled >= 4:
        score += 2
        tips.append("Art direction is partially filled; add more specific mood, assets, camera language, and do/do-not rules.")
    else:
        blockers.append("design/art_direction.md is still mostly a template: fill director statement, mood, style recipe, asset strategy, and do/do-not.")
    return score, blockers, tips


def segment_has_nontext_visual(seg: dict[str, Any]) -> bool:
    hay = " ".join(str(x).lower() for x in seg.get("visuals", []) + seg.get("assets", []))
    keywords = ["icon", "image", "photo", "screenshot", "chart", "map", "particle", "texture", "mock", "ui", "diagram", "b-roll", "video", "svg", "canvas"]
    return any(k in hay for k in keywords) or len(seg.get("assets", [])) >= 1


def score_storyboard(storyboard: dict[str, Any]) -> tuple[int, list[str], list[str]]:
    score = 0
    blockers: list[str] = []
    tips: list[str] = []
    segments = storyboard.get("segments", []) if isinstance(storyboard, dict) else []
    if not segments:
        return 0, ["Storyboard has no segments."], []
    rich_segments = 0
    shot_segments = 0
    asset_segments = 0
    for seg in segments:
        if not isinstance(seg, dict):
            continue
        seg_id = seg.get("id", "unknown")
        if seg.get("visual_metaphor") and seg.get("screen_ratio_allocation"):
            rich_segments += 1
        else:
            tips.append(f"{seg_id}: add visual_metaphor and screen_ratio_allocation.")
        shots = seg.get("shots")
        if isinstance(shots, list) and len(shots) >= 2:
            shot_segments += 1
        else:
            tips.append(f"{seg_id}: add at least two shots/visual beats.")
        if segment_has_nontext_visual(seg):
            asset_segments += 1
        else:
            blockers.append(f"{seg_id}: appears text-only; add icons, diagrams, screenshots, images, charts, or textures.")
        visuals = seg.get("visuals", [])
        if isinstance(visuals, list) and len(visuals) >= 3:
            pass
        else:
            tips.append(f"{seg_id}: visuals list is thin; aim for 3+ layers/elements.")
    total = max(1, len(segments))
    score += round(10 * rich_segments / total)
    score += round(10 * shot_segments / total)
    score += round(10 * asset_segments / total)
    if storyboard.get("narrative_arc"):
        score += 3
    if storyboard.get("visual_system"):
        score += 2
    return score, blockers, tips


def score_shotlist(shotlist: dict[str, Any]) -> tuple[int, list[str], list[str]]:
    score = 0
    blockers: list[str] = []
    tips: list[str] = []
    shots = shotlist.get("shots", []) if isinstance(shotlist, dict) else []
    if not shots:
        return 0, ["Shotlist has no shots. Run scripts/storyboard_to_shotlist.py and refine the result."], []
    complete = 0
    depth = 0
    camera_moves = set()
    sizes = set()
    for shot in shots:
        if not isinstance(shot, dict):
            continue
        required = ["shot_size", "camera_move", "composition", "foreground", "midground", "background", "edit_intent"]
        if all(shot.get(k) for k in required):
            complete += 1
        if shot.get("foreground") and shot.get("midground") and shot.get("background"):
            depth += 1
        if shot.get("camera_move"):
            camera_moves.add(str(shot["camera_move"]))
        if shot.get("shot_size"):
            sizes.add(str(shot["shot_size"]))
        if float(shot.get("text_area_percent") or 0) > 45:
            tips.append(f"{shot.get('shot_id','unknown')}: text area exceeds 45%; use only for deliberate typography shots.")
    n = max(1, len(shots))
    score += round(8 * complete / n)
    score += round(5 * depth / n)
    score += min(4, len(camera_moves))
    score += min(3, len(sizes))
    if len(camera_moves) < 2:
        tips.append("Use at least two camera move types across the video for rhythm variation.")
    if len(sizes) < 2:
        tips.append("Use at least two shot sizes, e.g. establishing + insert/close-up.")
    return score, blockers, tips


def score_assets(rows: list[dict[str, str]], segment_count: int) -> tuple[int, list[str], list[str]]:
    score = 0
    blockers: list[str] = []
    tips: list[str] = []
    usable = [r for r in rows if r.get("asset_id")]
    types = {r.get("type", "").strip().lower() for r in usable if r.get("type")}
    rights_unknown = [r.get("asset_id", "unknown") for r in usable if (r.get("rights_status", "").lower() in {"", "unknown", "needs-check"})]
    proof_types = {"photo", "screenshot", "broll", "video_clip", "image", "document"}
    proof_count = sum(1 for r in usable if r.get("type", "").strip().lower() in proof_types)
    if proof_count >= max(3, segment_count * 2):
        score += 6
    else:
        tips.append(
            f"Add web-sourced proof media: aim for at least {max(3, segment_count * 2)} "
            f"photo/screenshot/broll rows in asset_manifest (currently {proof_count}). "
            "See references/evidence-and-asset-sourcing.md."
        )
    min_planned = max(12, segment_count * 4)
    if len(usable) >= min_planned:
        score += 8
    else:
        tips.append(f"Asset manifest is sparse: aim for at least {min_planned} planned assets for {segment_count} segments.")
    if len(types) >= 4:
        score += 5
    else:
        tips.append("Use at least four asset types: icons, textures, screenshots/images, B-roll, SFX, charts, device frames, etc.")
    if usable:
        score += 3
    else:
        blockers.append("No assets are planned; add asset_manifest rows before rich rendering.")
    if rights_unknown:
        tips.append("Rights need review for: " + ", ".join(rights_unknown[:8]))
    else:
        score += 4
    return score, blockers, tips


def score_micro_timeline(root: Path) -> tuple[int, list[str], list[str]]:
    """Score whether the project has beat-level motion and asset choreography."""
    score = 0
    blockers: list[str] = []
    tips: list[str] = []
    beat_timeline = load_json(root / "script/beat_timeline.json", {})
    beat_list = beat_timeline.get("beats", []) if isinstance(beat_timeline, dict) else []
    choreography_rows = load_asset_rows(root / "assets/asset_choreography_manifest.csv")

    if isinstance(beat_list, list) and beat_list:
        score += 5
        specific = 0
        timed = []
        for beat in beat_list:
            if not isinstance(beat, dict):
                continue
            action = str(beat.get("visual_action", ""))
            if len(action) >= 28 and any(k in action.lower() for k in ["draw", "slide", "snap", "stamp", "pulse", "zoom", "scan", "morph", "wipe", "push", "arrow", "device", "card", "模块", "扫描", "绘制", "盖章", "推进", "卡片"]):
                specific += 1
            try:
                timed.append((float(beat.get("start_sec")), float(beat.get("end_sec"))))
            except Exception:
                pass
        if specific >= max(1, len(beat_list) // 2):
            score += 4
        else:
            tips.append("Beat timeline exists but visual_action is still too generic; describe the exact asset motion, state change, and why it clarifies narration.")
        timed.sort()
        long_gaps = [round(timed[i+1][0] - timed[i][1], 2) for i in range(len(timed)-1) if timed[i+1][0] - timed[i][1] > 1.8]
        if not long_gaps and len(timed) >= 2:
            score += 3
        elif long_gaps:
            tips.append("Beat timeline has long unchanged gaps over 1.8s: " + ", ".join(map(str, long_gaps[:6])))
    else:
        blockers.append("Missing script/beat_timeline.json with non-empty beats; dense explainers need phrase-level visual actions before rendering.")

    if choreography_rows:
        useful = [r for r in choreography_rows if r.get("asset_id") and r.get("first_on_sec") and r.get("main_motion")]
        if len(useful) >= max(3, len(beat_list) // 2 if isinstance(beat_list, list) else 3):
            score += 3
        else:
            tips.append("Asset choreography manifest is too thin; every persistent icon/device/card/SVG needs timing and motion path.")
    else:
        blockers.append("Missing assets/asset_choreography_manifest.csv; frames will likely feel empty or static.")
    return score, blockers, tips


def build_report(score: int, max_score: int, blockers: list[str], tips: list[str]) -> str:
    pct = round(score / max_score * 100)
    status = "PASS" if pct >= 72 and not blockers else "REVISE"
    lines = [
        "# Aesthetic Report",
        "",
        f"Status: {status}",
        f"Score: {pct}/100 ({score}/{max_score} raw)",
        "",
        "## Blockers",
    ]
    if blockers:
        lines.extend(f"- {b}" for b in blockers)
    else:
        lines.append("- None")
    lines.extend(["", "## Recommendations"])
    if tips:
        lines.extend(f"- {t}" for t in tips)
    else:
        lines.append("- None")
    lines.extend(["", "## Revision Targets", "- If the video feels empty: update storyboard visual_metaphor, shotlist depth layers, and asset_manifest first.", "- If the video feels ugly: update art_direction, tokens palette, and typography before segment code.", "- If the video feels like PPT: add shot-size variation, camera moves, parallax, real/illustrative assets, and cut reasons."])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Score visual richness and cinematic planning for a video project.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--fail-under", type=int, default=None, help="Exit 1 if score is below this percentage or blockers exist")
    parser.add_argument("--json", action="store_true", help="Also write edit/aesthetic_report.json")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    storyboard = load_json(root / "script/storyboard.json", {})
    shotlist = load_json(root / "script/shotlist.json", {})
    tokens = load_json(root / "design/tokens.json", {})
    art_text = read_text(root / "design/art_direction.md")
    design_text = read_text(root / "design/design.md")
    rows = load_asset_rows(root / "assets/asset_manifest.csv")
    segment_count = len(storyboard.get("segments", [])) if isinstance(storyboard, dict) else 0

    score = 0
    max_score = 115
    blockers: list[str] = []
    tips: list[str] = []
    part, b, t = score_design(root, tokens, art_text, design_text)
    score += part
    blockers.extend(b)
    tips.extend(t)
    part, b, t = score_storyboard(storyboard)
    score += part
    blockers.extend(b)
    tips.extend(t)
    part, b, t = score_shotlist(shotlist)
    score += part
    blockers.extend(b)
    tips.extend(t)
    part, b, t = score_assets(rows, segment_count)
    score += part
    blockers.extend(b)
    tips.extend(t)
    part, b, t = score_micro_timeline(root)
    score += part
    blockers.extend(b)
    tips.extend(t)
    score = max(0, min(max_score, score))

    pct = round(score / max_score * 100)
    report = build_report(score, max_score, blockers, tips)
    out = root / "edit/aesthetic_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(report)
    if args.json:
        (root / "edit/aesthetic_report.json").write_text(json.dumps({"score": pct, "blockers": blockers, "recommendations": tips}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.fail_under is not None and (pct < args.fail_under or blockers):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
