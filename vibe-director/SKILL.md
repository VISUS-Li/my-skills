---
name: vibe-director
description: pure-code video director skill for creating storyboard-driven, highly animated explainer videos with codex or claude code. use when the user wants to create, plan, storyboard, voice, review, or render short-form videos using remotion, hyperframes, gsap, svg, canvas, three.js, manim, ffmpeg, IndexTTS2 voiceover, or reusable agent skills such as vibe-motion. prioritizes director-level scripting, shot planning, effect selection, TTS timing alignment, preview review, and qa while avoiding black-box text-to-video models unless explicitly requested.
---

# Vibe Director

Use this skill as a lightweight director layer for pure-code explainer videos. The job is to turn a topic, script, notes, SRT, article, or existing storyboard into reviewable video plans and executable scene specs, then route implementation to the right renderer or existing effect skill.

## Default Workflow

1. Identify the input mode: topic, script, article, notes, SRT, video URL/file, or existing storyboard.
   - If the user provides a YouTube / Bilibili / Douyin / local video and needs spoken content, run sibling skill `subtitle-extractor` first, then continue in `srt` intake mode with `outputs/subtitles/*.srt`.
2. Draft or refine `script.md` and `section_plan.md`.
3. Produce `storyboard.json` plus a human-readable `shotlist.md`.
4. Produce `scene_spec.json` for each scene before writing animation code.
5. Select renderer and effects from references instead of inventing code first.
6. When voiceover is needed, prepare IndexTTS2 config, `script/narration_beats.csv`, beat WAVs, and measured voice timing before locking animation duration.
7. Generate one scene preview, contact sheet, and scene QA before scaling to the whole video.
8. Ask for human review at checkpoints unless the user explicitly asks for a fast automated run.
9. Render full preview, create contact sheets or montage, run QA, fix, then final render.

Never start by writing full animation code. First make the narrative structure, visual metaphors, storyboard, renderer choices, and motion beats inspectable.

## Reuse First

Prefer existing skills and component banks:

- Use HyperFrames for standalone HTML/CSS/GSAP scenes, fast previews, kinetic captions, UI mockups, cards, diagrams, shader transitions, and 3 to 20 second scenes.
- Use Remotion for multi-scene compositions, long timelines, subtitles, audio tracks, data-driven visuals, React component architecture, Studio props, Canvas, SVG, and Three.js.
- Use vibe-motion effects when a matching effect is the main visual. Treat them as slots that can be rendered and composed, not as copied source.
- Use GSAP for timeline, stagger, CustomEase, DrawSVG, MorphSVG, MotionPath, SplitText, and ScrambleText when HTML/SVG motion would otherwise feel stiff.
- Use custom code only when no suitable renderer, effect, or component bank fits. Keep custom components reusable.

## Reference Loading Map

- Read `references/workflow.md` for the end-to-end production flow and project directory.
- Read `references/storyboard-schema.md` when creating or validating `storyboard.json`.
- Read `references/scene-spec-schema.md` before implementing any scene.
- Read `references/renderer-selection.md` when choosing HyperFrames, Remotion, vibe-motion, Manim, or custom code.
- Read `references/effect-registry.md` when selecting effect candidates.
- Read `references/style-presets.md` for Chinese short-video visual presets, especially `zheda-cat-git-motion` and `ai-chapingjun-system-explainer`.
- Read `references/preview-review.md` before deciding whether to pause for review.
- Read `references/tts-indextts.md` when generating or aligning IndexTTS2 narration.
- Read `references/qa-checklist.md` before accepting a scene preview or final preview.
- Read `references/excluded-scope.md` when the task drifts into black-box video generation, raw footage editing, or social publishing.

## Quality Bar

Every scene must have a visual metaphor, renderer, shot type, effect candidates, and motion beats. Each narration sentence must map to visible action. Avoid scenes that are only subtitles over a static background unless they are very short punchlines.

For short-form explainer pacing, target a visible change every 1 to 1.5 seconds. For developer-tool videos, prefer local motion inside stable scenes: cursor movement, typing, highlights, zooms, graph growth, labels, and UI state changes.

## Preview And QA

Default checkpoints are script review, storyboard review, single-scene review, and whole-video review. Use `scripts/validate_storyboard.py` for storyboard checks, `scripts/probe_video.py` for video metadata, `scripts/sample_keyframes.py` for frame sampling, and `scripts/make_contact_sheet.py` for visual review evidence.

Do not call a render final until a preview and QA report exist, unless the user explicitly accepts the risk.
