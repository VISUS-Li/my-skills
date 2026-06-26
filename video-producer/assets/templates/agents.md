# AGENTS.md

## Project Overview

This repository uses the Video Producer workflow. Treat intermediate artifacts as source of truth and preserve review checkpoints.

## Core Rules

- Do not jump from an idea directly to video rendering unless explicitly asked.
- Keep `.video/state.json` updated after every stage.
- Do not overwrite approved or locked outputs; create versioned drafts.
- Use `research/claim_ledger.csv` for factual videos.
- Every serious video must include art direction, shotlist, asset manifest, and aesthetic review before final render.
- Route segments to the smallest reliable engine: HyperFrames for motion graphics, editor/video-use for talking head, FFmpeg for assembly.

## Useful Commands

```bash
python skills/video-producer/scripts/init_video_project.py --name "my video" --input-type idea
python skills/video-producer/scripts/validate_project.py .
python skills/video-producer/scripts/storyboard_to_shotlist.py .
python skills/video-producer/scripts/aesthetic_score.py . --fail-under 72
python skills/video-producer/scripts/stage_gate.py . --stage storyboard --status review --note "ready for review"
python skills/video-producer/scripts/dependency_report.py --changed script/storyboard.json
python skills/video-producer/scripts/build_timeline.py .
python skills/video-producer/scripts/ffmpeg_assemble.py . --dry-run
```

## Reference-video and Chinese-text rules

- When a reference video is supplied, run `scripts/analyze_reference_video.py` and create `analysis/reference_video/style_dna.md` before rendering.
- For Chinese explainers, treat Chinese text as data: keep exact copy in `script/text_manifest.json` and render it through programmatic text layers, not generated images.
- Use the `douyin-ai-explainer` recipe for light-grid Chinese AI explainers, then run `scripts/douyin_ai_explainer_score.py` before final rendering.
