# Workflow

Use this workflow for pure-code knowledge videos, especially Chinese explainers, AI tool walkthroughs, technical concept breakdowns, developer demos, and vertical short videos.

## 1. Intake

Classify the source:

- `topic`: create the script from a prompt.
- `script`: improve structure, pacing, and visual hooks.
- `article`: extract claims, examples, and proof.
- `notes`: organize raw material into a narrative.
- `srt`: preserve timing where possible and group subtitles into scenes.
- `video-url` / `video-file`: run sibling `subtitle-extractor` to produce `outputs/subtitles/*.srt`, then continue as `srt`.
- `existing-storyboard`: validate, enrich, and route to renderers.

For `video-url` / `video-file`:

```bash
python ../subtitle-extractor/scripts/extract_subtitles.py "<url-or-file>" -o outputs/subtitles --lang zh
```

Capture title, platform, aspect ratio, duration target, audience, style preset, must-show concepts, forbidden claims, available assets, and whether the user wants checkpoints or full automation.

## 2. Script Planning

Create:

- `script.md`: narration with hook in the first 2 seconds.
- `section_plan.md`: sections with roles such as hook, setup, explanation, contrast, proof, and conclusion.

For Chinese short videos, keep sentences concrete and visual. Convert abstract claims into visible states, UI operations, diagrams, dashboards, timelines, or analogies.

## 3. Storyboard

Create:

- `storyboard.json`: machine-readable plan using `storyboard-schema.md`.
- `shotlist.md`: human-readable table with scene id, duration, narration, visual metaphor, shot type, renderer, effect candidates, and review notes.

Every scene must state what changes on screen. Do not approve a storyboard where scenes are just text cards.

## 4. Scene Specification

For each scene, create `scenes/<scene-id>/scene_spec.json` using `scene-spec-schema.md`.

The scene spec must include motion beats covering the full duration, emphasis words, caption style, renderer, preferred skills, fallback, and QA assumptions.

## 5. Renderer Selection

Use `renderer-selection.md`:

- HyperFrames for fast standalone HTML/CSS/GSAP scenes and previewable 3 to 20 second motion.
- Remotion for multi-scene timelines, subtitles, audio tracks, React architecture, and long-term maintainability.
- vibe-motion when an existing effect fits the shot.
- Manim only for math or algorithm scenes where coordinate precision matters.
- Custom code only after ruling out reusable effects and components.

## 6. Effect Selection

Use `effect-registry.md` before custom code. Put candidates into `effectCandidates`, including a short reason for empty candidates in `notes`.

## 7. Voiceover And Timing

When the video needs narration, use `tts-indextts.md` after scene specs and before locking preview timing.

Create or update:

- `audio/indextts2_config.json`.
- `audio/refs/narrator_ref.wav`.
- `script/narration_beats.csv`.
- Optional `audio/prosody_plan.csv`.

Generate voiceover:

```bash
python scripts/indextts2_generate.py . --segment S001 --concat
```

Then measure actual voice duration:

```bash
python scripts/measure_segment_vo.py . S001
```

Use `segments/S001/vo_timing.json` to align storyboard scene timing, scene specs, captions, and renderer timelines. Do not rely on equal shot splits after real TTS exists.

## 8. Preview Generation

Preview one representative scene first. Save:

- scene preview video or HTML preview.
- `contact-sheet.jpg`.
- `qa.md`.

Then scale to more scenes.

## 9. Human Review

Default to review checkpoints unless the user explicitly asks for full automation. Use the pattern: ask, confirm, execute, self-evaluate, persist.

## 10. Full Preview

Assemble `preview.mp4` before final. Generate `verify/montage.jpg` or per-scene contact sheets.

## 11. QA

Use `qa-checklist.md`. Check for slide-like scenes, stale frames, missing visual metaphors, captions covering main objects, renderer misuse, mismatched durations, abrupt shot boundaries, and storyboard/spec drift.

## 12. Fix And Final Render

Fix failed scenes, update `storyboard.json` and scene specs, rerender previews, rerun QA, then render `final.mp4`.

## Suggested Project Directory

```text
video-project/
├── project.md
├── brief.md
├── script.md
├── script/
│   └── narration_beats.csv
├── section_plan.md
├── storyboard.json
├── shotlist.md
├── scenes/
│   ├── s001/
│   │   ├── scene_spec.json
│   │   ├── source.tsx or index.html
│   │   ├── preview.mp4
│   │   ├── contact-sheet.jpg
│   │   └── qa.md
├── animations/
│   └── slot_<id>/
├── assets/
├── captions/
├── audio/
│   ├── indextts2_config.json
│   ├── refs/
│   │   └── narrator_ref.wav
│   └── stems/
│       └── voice/
├── verify/
│   ├── montage.jpg
│   ├── scene_contact_sheets/
│   ├── motion_density.json
│   └── qa_report.md
├── preview.mp4
└── final.mp4
```
