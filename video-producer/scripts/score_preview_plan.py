#!/usr/bin/env python3
"""Score the first-slice plan and write lightweight review metrics."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from validate_segment_spec import validate


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def video_duration(path: Path) -> float | None:
    if not path.exists():
        return None
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
        return float(out)
    except Exception:  # noqa: BLE001
        return None


def repair_suggestions(failures: list[str]) -> list[str]:
    suggestions: list[str] = []
    rules = [
        ("segment_coverage", "Fill the declared first-slice duration with timed shots before rendering."),
        ("hook_required", "Rewrite the first 3 seconds around a visible hook: keyword, proof, redbox, cursor, or contradiction."),
        ("micro_action_density", "Split long holds and add cursor, zoom, redbox, highlight, graph, or card actions every 0.8-1.5s."),
        ("macro_scene_reset_density", "Add a room change or clear visual reset around the 8-12s mark."),
        ("proof_choreography_required", "Direct proof assets with crop, push-in, redbox, cursor, zoom, highlight, or annotation."),
        ("audio_visual_sync_required", "Add motivated audio cues to keyword pops, redboxes, typing, transitions, and stamps."),
        ("visual_owner_variety", "Route beats to at least two distinct visual owners so the slice does not feel like one static board."),
        ("text-only visual_owner", "Replace text-card ownership with screenshot, diagram, terminal, graph, dashboard, or metaphor ownership."),
        ("delegation", "Add a bounded delegation contract: skill, purpose, inputs, outputs, and acceptance criteria."),
        ("complexity_budget", "Simplify the first slice: one style, 3-5 recipes, 1-3 renderers, and no more than two delegated slots."),
        ("first_slice_required", "Render only a 20-30s first slice, then review before expanding."),
        ("contact_sheet_missing", "Generate a contact sheet from the preview with scripts/build_contact_sheet.py when ffmpeg is available."),
    ]
    for failure in failures:
        for token, suggestion in rules:
            if token in failure and suggestion not in suggestions:
                suggestions.append(suggestion)
    return suggestions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outputs", type=Path, default=Path("outputs"))
    parser.add_argument("--fail-under", type=int, default=78)
    args = parser.parse_args()

    root = args.outputs
    review = root / "review"
    spec = load_json(root / "segment_spec.json", {})
    beats = load_json(root / "beat_plan.json", {})
    cues = load_json(root / "audio_cue_sheet.json", {"cues": []})

    failures: list[str] = []
    failures.extend(validate(spec, beats))

    preview = review / "preview.mp4"
    contact = review / "contact_sheet.jpg"
    if not preview.exists():
        failures.append("first_slice_required: outputs/review/preview.mp4 missing")
    else:
        dur = video_duration(preview)
        if dur is not None and not (20 <= dur <= 30.5):
            failures.append(f"first_slice_required: preview duration {dur:.2f}s is outside 20-30s")
    if not contact.exists():
        failures.append("contact_sheet_missing: outputs/review/contact_sheet.jpg missing")

    cue_actions = {str(item.get("visual_action", "")) for item in cues.get("cues", []) if isinstance(item, dict)}
    key_actions = []
    for shot in spec.get("shots", []) if isinstance(spec, dict) else []:
        for action in shot.get("visual_actions", []) if isinstance(shot, dict) else []:
            atype = str(action.get("type", ""))
            if action.get("sfx") or atype in cue_actions:
                continue
            if any(token in atype for token in ("keyword", "redbox", "terminal", "typing", "transition", "reset", "stamp")):
                key_actions.append(f"{shot.get('shot_id')}:{atype}")
    if key_actions:
        failures.append("audio_visual_sync_required: key actions lack cue: " + ", ".join(key_actions[:8]))

    score = 100
    score -= min(55, len(failures) * 8)
    if spec.get("style") in {"vibemotion-dev-demo", "ai-chapingjun-system-explainer", "git-motion-edu-metaphor"}:
        score += 3
    score = max(0, min(100, score))
    suggestions = repair_suggestions(failures)

    review.mkdir(parents=True, exist_ok=True)
    metrics = {
        "score": score,
        "pass": score >= args.fail_under and not failures,
        "fail_under": args.fail_under,
        "style": spec.get("style"),
        "duration": spec.get("duration"),
        "failure_count": len(failures),
        "repair_suggestions": suggestions,
        "checks": {
            "first_slice_required": preview.exists(),
            "review_studio_generated": (review / "review-studio" / "index.html").exists(),
            "contact_sheet": contact.exists(),
        },
    }
    (review / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if failures:
        body = "# Failed Checks\n\n" + "\n".join(f"- {item}" for item in failures) + "\n"
        if suggestions:
            body += "\n# Repair Suggestions\n\n" + "\n".join(f"- {item}" for item in suggestions) + "\n"
    else:
        body = "# Failed Checks\n\nNo blocking issues detected by automated checks. Human review still needs to judge style match, rhythm, and proof readability.\n"
    (review / "failed_checks.md").write_text(body, encoding="utf-8")

    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0 if metrics["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
