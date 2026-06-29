#!/usr/bin/env python3
"""Initialize a controllable, director-level video production project.

This script is intentionally dependency-free so it works in most coding-agent
sandboxes. It creates reviewable intermediate artifacts rather than generating
video directly.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


STAGES = [
    "plan",
    "ingest",
    "reference-analysis",
    "style-match",
    "research",
    "fact-lock",
    "narrative-script",
    "script",
    "art-direction",
    "storyboard",
    "beat-design",
    "director-compiler",
    "asset-choreography",
    "shot-design",
    "design",
    "assets",
    "sound-design",
    "audio-assets",
    "audio-mix",
    "segments",
    "assemble",
    "aesthetic-review",
    "qc",
    "publish",
]


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "untitled-video"


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def copy_template(template_name: str, target: Path, replacements: dict[str, object] | None = None, force: bool = False) -> None:
    src = skill_root() / "assets" / "templates" / template_name
    if not src.exists():
        raise FileNotFoundError(f"template not found: {src}")
    if target.exists() and not force:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix == ".json":
        data = json.loads(src.read_text(encoding="utf-8"))
        if replacements:
            data.update(replacements)
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        text = src.read_text(encoding="utf-8")
        if replacements:
            for key, value in replacements.items():
                text = text.replace("{{" + key + "}}", str(value))
        target.write_text(text, encoding="utf-8")



def scale_storyboard_to_duration(path: Path, target_duration: int) -> None:
    """Scale template segment durations so a newly initialized project validates."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        segments = data.get("segments", [])
        total = sum(float(seg.get("duration_sec", 0)) for seg in segments if isinstance(seg, dict))
        if not segments or total <= 0 or target_duration <= 0:
            return
        # If the template is already close enough, keep its editorial pacing.
        if total <= target_duration * 1.25 and total >= target_duration * 0.75:
            data["total_duration_sec"] = target_duration
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return
        scale = target_duration / total
        remaining = float(target_duration)
        for i, seg in enumerate(segments):
            if not isinstance(seg, dict):
                continue
            if i == len(segments) - 1:
                new_duration = max(1.0, round(remaining, 2))
            else:
                new_duration = max(1.0, round(float(seg.get("duration_sec", 1)) * scale, 2))
                remaining -= new_duration
            seg["duration_sec"] = new_duration
        data["total_duration_sec"] = target_duration
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception:
        return

def scaffold_segment(root: Path, segment_id: str = "S001", *, force: bool = False) -> None:
    """Create per-segment asset dirs, beat plan, and UTF-8 SVG rebuild template."""
    seg = segment_id.upper()
    seg_dir = root / "segments" / seg
    for sub in (
        "assets/ref/processed/_raw",
        "assets/ref/processed/stock",
        "assets/ref/_candidates",
        ".hyperframes",
    ):
        (seg_dir / sub).mkdir(parents=True, exist_ok=True)

    copy_template("beat_asset_plan.csv", seg_dir / "beat_asset_plan.csv", force=force)
    copy_template("video_types_report.json", seg_dir / "assets" / "ref" / "processed" / "video_types_report.json", force=force)
    rebuild_src = skill_root() / "assets" / "templates" / "rebuild_chinese.py"
    rebuild_dst = seg_dir / "assets" / "rebuild_chinese.py"
    if not rebuild_dst.exists() or force:
        rebuild_dst.parent.mkdir(parents=True, exist_ok=True)
        rebuild_dst.write_text(rebuild_src.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a staged video production project with art direction, sound design, and quality gates.")
    parser.add_argument("--name", required=True, help="Human-readable video/project name")
    parser.add_argument("--root", default=None, help="Project directory. Defaults to slugified --name")
    parser.add_argument("--input-type", default="idea", choices=["idea", "audio", "video", "youtube", "url", "pdf", "article", "raw-video", "mixed"], help="Primary input type")
    parser.add_argument("--ratio", default="9:16", help="Target aspect ratio, e.g. 9:16 or 16:9")
    parser.add_argument("--duration", type=int, default=180, help="Target duration in seconds")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument("--resolution", default=None, help="Resolution, defaults from ratio")
    parser.add_argument("--platforms", default="douyin,bilibili,youtube", help="Comma-separated platform list")
    parser.add_argument("--style", default="", help="Comma-separated style keywords")
    parser.add_argument("--recipe", default="generic", choices=["generic", "douyin-ai-explainer"], help="Optional production recipe with stricter templates and gates")
    parser.add_argument("--aesthetic-score", type=int, default=72, help="Target aesthetic score before final render")
    parser.add_argument("--force", action="store_true", help="Overwrite existing template files")
    args = parser.parse_args()

    slug = slugify(args.name)
    root = Path(args.root or slug).resolve()
    resolution = args.resolution or ("1080x1920" if args.ratio == "9:16" else "1920x1080")
    platforms = [p.strip() for p in args.platforms.split(",") if p.strip()]
    style_keywords = [s.strip() for s in args.style.split(",") if s.strip()]
    if args.recipe == "douyin-ai-explainer" and not any("douyin-ai-explainer" in s for s in style_keywords):
        style_keywords.append("douyin-ai-explainer")

    for directory in [
        ".video",
        "inbox/raw_talking_head",
        "inbox/source_docs",
        "research",
        "script",
        "design/references",
        "design/styleframes",
        "segments",
        "assets/icons",
        "assets/images",
        "assets/screenshots",
        "assets/textures",
        "assets/video",
        "assets/broll",
        "assets/audio",
        "assets/music",
        "assets/sfx",
        "audio",
        "audio/candidates",
        "audio/refs",
        "audio/voice",
        "audio/music",
        "audio/sfx",
        "audio/stems",
        "audio/stems/voice/beats",
        "edit",
        "exports",
        "analysis/reference_video",
        "design/text",
        "logs",
    ]:
        (root / directory).mkdir(parents=True, exist_ok=True)

    created_at = datetime.now(timezone.utc).isoformat()
    copy_template(
        "video.json",
        root / ".video" / "video.json",
        {
            "title": args.name,
            "slug": slug,
            "input_type": args.input_type,
            "ratio": args.ratio,
            "duration_sec": args.duration,
            "fps": args.fps,
            "resolution": resolution,
            "platforms": platforms,
            "style_keywords": style_keywords,
            "created_at": created_at,
            "aesthetic_goals": {
                "richness": "layered, cinematic, non-PPT",
                "target_aesthetic_score": args.aesthetic_score,
                "review_required": True,
            },
            "audio_goals": {
                "sound_design": "intentional, synced, voice-first, emotionally supportive",
                "audio_score_required": True,
                "target_audio_score": 72,
            },
            "recipe": args.recipe,
            "text_policy": {
                "exact_chinese_text_layers_only": args.recipe == "douyin-ai-explainer",
                "forbid_generated_raster_chinese": args.recipe == "douyin-ai-explainer",
            },
        },
        args.force,
    )
    copy_template("state.json", root / ".video" / "state.json", {"created_at": created_at}, args.force)
    state_path = root / ".video" / "state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        stages = state.setdefault("stages", {})
        for stage in STAGES:
            stages.setdefault(stage, {"status": "draft", "artifacts": []})
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception:
        pass
    copy_template("creative_brief.md", root / "script" / "creative_brief.md", force=args.force)
    storyboard_template = "douyin_ai_explainer_storyboard.json" if args.recipe == "douyin-ai-explainer" else "storyboard.json"
    copy_template(storyboard_template, root / "script" / "storyboard.json", {"video_title": args.name, "total_duration_sec": args.duration}, args.force)
    scale_storyboard_to_duration(root / "script" / "storyboard.json", args.duration)
    copy_template("narration_beats.csv", root / "script" / "narration_beats.csv", force=args.force)
    copy_template("beat_timeline.json", root / "script" / "beat_timeline.json", force=args.force)
    copy_template("director_event_graph.json", root / "script" / "director_event_graph.json", force=args.force)
    copy_template("retention_curve.json", root / "script" / "retention_curve.json", force=args.force)
    copy_template("shotlist.json", root / "script" / "shotlist.json", force=args.force)
    copy_template("art_direction.md", root / "design" / "art_direction.md", force=args.force)
    copy_template("visual_moodboard.json", root / "design" / "visual_moodboard.json", force=args.force)
    copy_template("design.md", root / "design" / "design.md", force=args.force)
    tokens_template = "douyin_ai_explainer_tokens.json" if args.recipe == "douyin-ai-explainer" else "tokens.json"
    copy_template(tokens_template, root / "design" / "tokens.json", force=args.force)
    copy_template("asset_manifest.csv", root / "assets" / "asset_manifest.csv", force=args.force)
    copy_template("asset_choreography_manifest.csv", root / "assets" / "asset_choreography_manifest.csv", force=args.force)
    copy_template("text_manifest.json", root / "script" / "text_manifest.json", force=args.force)
    copy_template("micro_animation_palette.json", root / "design" / "micro_animation_palette.json", force=args.force)
    copy_template("reference_video_style_dna.md", root / "analysis" / "reference_video" / "style_dna.md", force=args.force)
    copy_template("timeline.json", root / "edit" / "timeline.json", {"ratio": args.ratio, "fps": args.fps, "resolution": resolution}, args.force)
    copy_template("audio_style_guide.md", root / "audio" / "audio_style_guide.md", force=args.force)
    copy_template("audio_cue_sheet.json", root / "audio" / "audio_cue_sheet.json", force=args.force)
    copy_template("music_brief.md", root / "audio" / "music_brief.md", force=args.force)
    copy_template("voice_profile.md", root / "audio" / "voice_profile.md", force=args.force)
    copy_template("tts_plan.json", root / "audio" / "tts_plan.json", force=args.force)
    copy_template("indextts2_config.json", root / "audio" / "indextts2_config.json", force=args.force)
    copy_template("sfx_search_queries.json", root / "audio" / "sfx_search_queries.json", force=args.force)
    copy_template("audio_mix_plan.json", root / "audio" / "audio_mix_plan.json", force=args.force)
    copy_template("loudness_targets.json", root / "audio" / "loudness_targets.json", force=args.force)
    copy_template("audio_rights_log.md", root / "audio" / "audio_rights_log.md", force=args.force)
    copy_template("audio_qc_report.md", root / "edit" / "audio_qc_report.md", force=args.force)
    copy_template("aesthetic_report.md", root / "edit" / "aesthetic_report.md", force=args.force)
    copy_template("publish_pack.md", root / "exports" / "publish_pack.md", force=args.force)
    copy_template("agents.md", root / "AGENTS.md", force=args.force)

    from review_core import init_review_files

    init_review_files(root, force=args.force)
    stage_manifest_src = skill_root() / "assets" / "templates" / "stage_manifest.json"
    if stage_manifest_src.exists():
        copy_template("stage_manifest.json", root / ".video" / "stage_manifest.json", force=args.force)

    cursor_rule = root / ".cursor" / "rules" / "video-factory.mdc"
    cursor_rule.parent.mkdir(parents=True, exist_ok=True)
    copy_template("cursor-rule.mdc", cursor_rule, force=args.force)

    seed_files = {
        "research/research_brief.md": "# Research Brief\n\n",
        "research/input_inventory.md": "# Input Inventory\n\n",
        "script/on_screen_text.md": "# On-screen Text\n\n",
        "script/beat_director_notes.md": "# Beat Director Notes\n\nUse this file to explain the creative rationale behind dense beat timing, frame occupancy, and sound sync choices.\n",
        "script/voiceover.md": (skill_root() / "assets" / "templates" / "voiceover.md").read_text(encoding="utf-8"),
        "script/outline.md": (skill_root() / "assets" / "templates" / "outline.md").read_text(encoding="utf-8"),
        "script/narrative_thread_map.json": (skill_root() / "assets" / "templates" / "narrative_thread_map.json").read_text(encoding="utf-8"),
        "research/thread_ledger.csv": (skill_root() / "assets" / "templates" / "thread_ledger.csv").read_text(encoding="utf-8"),
        "research/source_cards.jsonl": (skill_root() / "assets" / "templates" / "source_cards.jsonl").read_text(encoding="utf-8"),
        "research/claim_ledger.csv": (skill_root() / "assets" / "templates" / "claim_ledger.csv").read_text(encoding="utf-8"),
        "research/factcheck_report.md": (skill_root() / "assets" / "templates" / "factcheck_report.md").read_text(encoding="utf-8"),
        "edit/qc_report.md": "# QC Report\n\n",
        "edit/assembly_command.sh": "#!/usr/bin/env bash\nset -euo pipefail\n# Generated by ffmpeg_assemble.py\n",
        "edit/audio_mix_command.sh": "#!/usr/bin/env bash\nset -euo pipefail\n# Generated by ffmpeg_audio_mix.py\n",
    }
    for file_name, content in seed_files.items():
        path = root / file_name
        if not path.exists() or args.force:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            if path.suffix == ".sh":
                path.chmod(0o755)

    scaffold_segment(root, "S001", force=args.force)

    print(f"Initialized video project: {root}")
    if args.recipe == "douyin-ai-explainer":
        print("Recipe: douyin-ai-explainer. Next also run douyin_ai_explainer_score.py before rendering.")
    print(f"Next: fill {root / 'design' / 'art_direction.md'} and {root / 'audio' / 'audio_style_guide.md'}, then run validate_project.py, aesthetic_score.py, and audio_score.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
