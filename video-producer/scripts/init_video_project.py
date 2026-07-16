#!/usr/bin/env python3
"""Initialize a lightweight video project using the outputs/ contract only."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "untitled-video"


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def template_path(name: str) -> Path:
    return skill_root() / "assets" / "templates" / name


def default_project_root(slug: str) -> Path:
    desktop = Path.home() / "Desktop"
    base = desktop if desktop.exists() else Path.home()
    return (base / slug).resolve()


def copy_json_template(name: str, target: Path, *, updates: dict | None = None, force: bool = False) -> None:
    src = template_path(name)
    if not src.exists():
        raise FileNotFoundError(f"template missing: {src}")
    if target.exists() and not force:
        return
    data = json.loads(src.read_text(encoding="utf-8"))
    if updates:
        data.update(updates)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a lightweight video-producer project.")
    parser.add_argument("--name", required=True, help="Human-readable project name")
    parser.add_argument("--root", default=None, help="Project directory (default: Desktop/<slug>)")
    parser.add_argument("--style", default="ai-chapingjun-system-explainer", help="Style preset id")
    parser.add_argument("--ratio", default="9:16", help="Aspect ratio")
    parser.add_argument("--duration", type=int, default=30, help="First-slice target duration (seconds)")
    parser.add_argument("--force", action="store_true", help="Overwrite scaffold files")
    parser.add_argument(
        "--deep",
        action="store_true",
        help="Scaffold depth research stubs (source_cards + event_genealogy); use for factual/analytical videos",
    )
    args = parser.parse_args()

    slug = slugify(args.name)
    root = Path(args.root).resolve() if args.root else default_project_root(slug)
    created_at = datetime.now(timezone.utc).isoformat()
    resolution = "1080x1920" if args.ratio == "9:16" else "1920x1080"

    directories = [
        "outputs/review/review-studio",
        "segments/S001",
        "audio/stems/voice/beats",
        "audio/refs",
        ".video",
        "logs",
    ]
    if args.deep:
        directories.append("research")
    for directory in directories:
        (root / directory).mkdir(parents=True, exist_ok=True)

    copy_json_template(
        "example_beat_plan.json",
        root / "outputs" / "beat_plan.json",
        updates={"style": args.style, "duration": args.duration, "title": args.name, "beats": []},
        force=args.force,
    )
    copy_json_template(
        "example_segment_spec.json",
        root / "outputs" / "segment_spec.json",
        updates={"segment_id": "s001", "style": args.style, "duration": args.duration, "first_slice": True, "shots": []},
        force=args.force,
    )
    copy_json_template(
        "example_audio_cue_sheet.json",
        root / "outputs" / "audio_cue_sheet.json",
        force=args.force,
    )

    script_path = root / "outputs" / "script.md"
    if not script_path.exists() or args.force:
        script_path.write_text(
            f"# {args.name}\n\n<!-- beat-plan-voice:start -->\n<!-- beat-plan-voice:end -->\n",
            encoding="utf-8",
        )

    review_stub = root / "outputs" / "review" / "failed_checks.md"
    if not review_stub.exists() or args.force:
        review_stub.write_text("# Failed Checks\n\n- plan-only scaffold; add beat_plan and segment_spec\n", encoding="utf-8")

    indextts = template_path("indextts2_config.json")
    if indextts.exists():
        dst = root / "audio" / "indextts2_config.json"
        if not dst.exists() or args.force:
            shutil.copy2(indextts, dst)
    else:
        legacy = skill_root() / "examples" / "legacy" / "templates" / "indextts2_config.json"
        if legacy.exists() and (not (root / "audio" / "indextts2_config.json").exists() or args.force):
            shutil.copy2(legacy, root / "audio" / "indextts2_config.json")

    state = {
        "version": "lite",
        "created_at": created_at,
        "current_stage": "script-only",
        "workflow": "outputs-contract",
        "deep_research": bool(args.deep),
    }
    video = {
        "title": args.name,
        "slug": slug,
        "ratio": args.ratio,
        "duration_sec": args.duration,
        "resolution": resolution,
        "style_keywords": [args.style],
        "outputs_dir": "outputs",
    }
    (root / ".video" / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / ".video" / "video.json").write_text(json.dumps(video, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    from review_core import init_review_files

    init_review_files(root, force=args.force)

    if args.deep:
        # Always-tier depth stubs only. claim_ledger / factcheck / thread_map are on-demand.
        research_files = {
            "research/source_cards.jsonl": "",
            "research/event_genealogy.md": (
                "# Event Genealogy\n\n"
                "- tip:\n"
                "- upstream:\n"
                "- timeline:\n"
                "- rule_substrate:\n"
                "- neighbor_strands:\n"
                "- still_unknown:\n"
                "- ordinary_impact:\n"
                "- dig_worthy:\n"
                "- viewer_harvest:\n"
                "- cast:\n"
            ),
        }
        for rel, content in research_files.items():
            path = root / rel
            if not path.exists() or args.force:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

    print(f"Initialized lite project: {root}")
    print("Next:")
    step = 1
    if args.deep:
        print(f"  {step}. Fill research/source_cards.jsonl and research/event_genealogy.md, then outputs/script.md")
        step += 1
        print(f"  {step}. python scripts/validate_research_lite.py --project {root}")
        step += 1
    else:
        print(f"  {step}. Write {root / 'outputs' / 'script.md'} (add --deep next time for research stubs)")
        step += 1
    print(f"  {step}. Write {root / 'outputs' / 'beat_plan.json'} and {root / 'outputs' / 'segment_spec.json'}")
    step += 1
    print(f"  {step}. python scripts/validate_segment_spec.py {root / 'outputs' / 'segment_spec.json'}")
    step += 1
    print(f"  {step}. python scripts/build_review_bundle.py --outputs {root / 'outputs'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
