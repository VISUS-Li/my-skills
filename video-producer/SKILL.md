---
name: video-producer
description: "Director-paced video production workflow for factual Chinese explainers, narration scripts, asset-driven HyperFrames/Remotion segments, IndexTTS2 voiceover, visual-sync planning, source-grounded assets, motion choreography, audio cues, and QC. Use when Codex needs to create, revise, diagnose, or render videos/scripts where pacing, voice-to-picture alignment, material selection, visual design, animation rhythm, or non-PPT production quality matters."
---

# Video Producer

Act as a **director compiler**. Do not jump from `idea/script -> prompt -> render`.

Default path:

`project bootstrap -> research/fact lock -> story voice -> director rhythm -> visual sync + assets -> motion/audio implementation -> QC`

The output must feel like a directed video: the viewer knows what to look at, has enough time to understand it, hears a human-like rhythm, and sees motion that clarifies rather than decorates.

## Step 0 - Project Bootstrap

Before writing any video artifact, resolve `PROJECT_DIR`.

- If the user provides a path, use it.
- Otherwise create `videos/<short-kebab-topic>/` under the current workspace.
- Never write `research/`, `script/`, `segments/`, `assets/`, `audio/`, or `exports/` in the skill repo root.

Initialize only when `.video/state.json` is absent:

```bash
python "$SKILL_DIR/scripts/init_video_project.py" \
  --name "<title>" \
  --root "$PROJECT_DIR" \
  --input-type <idea|article|video|url|mixed> \
  --ratio <16:9|9:16> \
  --duration <seconds> \
  [--recipe douyin-ai-explainer]

python "$SKILL_DIR/scripts/validate_project.py" "$PROJECT_DIR"
```

After init, tell the user the absolute `PROJECT_DIR`.

## Director Model

Every stage must answer one director question:

| Stage | Director question | Required artifact |
|---|---|---|
| story | What is the audience supposed to understand next? | `script/voiceover.md`, `script/narration_beats.csv` |
| rhythm | How long does the viewer need to hear, see, breathe, and absorb? | `audio/prosody_plan.csv`, `script/rhythm_map.json` |
| visual sync | What exact picture proves or explains this spoken phrase? | `script/visual_sync_plan.csv`, `segments/<id>/beat_asset_plan.csv` |
| assets | Is this material relevant, readable, legal, and safely cropped? | `assets/asset_selection_report.json`, `assets/asset_manifest.csv` |
| motion | Which one thing owns attention at each moment? | `script/beat_timeline.json`, `assets/asset_choreography_manifest.csv` |
| sound | What should be heard, ducked, paused, or silent? | `audio/audio_cue_sheet.json`, `audio/audio_mix_plan.json` |

Load `references/director-rhythm-system.md` whenever working on rhythm, visual sync, assets, animation, TTS, or segment implementation.

## Core Rules

- **VO-first, not equal splits:** plan from script, but bind final timings to measured WAV via `segments/<id>/vo_timing.json`.
- **Beat is not a shot:** one narration beat may contain several visual micro-events; one shot may span several beats.
- **Readable before flashy:** evidence screenshots, UI, charts, and source cards need enough hold time to be read.
- **One focal owner:** at any moment, one asset/action leads; secondary motion must support it.
- **Programmatic text:** exact Chinese text must be rendered as text/SVG/HTML layers, not baked into generated images.
- **Concrete beats need concrete media:** if a line names a person, product, document, event, UI, or action, bind `ref_*`, `stock_*`, `gen_*`, or `motion_*`, not only icons.
- **Assets are actors:** every visible asset needs a layer, role, entrance, main behavior, exit rule, and SFX affordance.
- **Motion explains verbs:** scan what is being checked, stamp what is rejected, connect what is related, transform what changes, hold what must be understood.
- **Human voice rhythm:** add pauses, emphasis, breath points, pace changes, and occasional natural phrasing before TTS generation.

## Workflow Modes

Infer the smallest mode from the request. Do not ask the user to name stages.

1. `plan` - create `creative_brief.md` and `.video/video.json`.
2. `research` - source cards, claim ledger, research brief.
3. `script` - outline, spoken voiceover, claim IDs, on-screen text.
4. `beat-design` - phrase-level `narration_beats.csv`; include semantic action and spoken focus.
5. `director-rhythm` - run or refine:

```bash
python "$SKILL_DIR/scripts/build_director_rhythm.py" "$PROJECT_DIR" --write-prosody
python "$SKILL_DIR/scripts/director_rhythm_lint.py" "$PROJECT_DIR" --fail-under 80
```

6. `visual-sync` - fill `script/visual_sync_plan.csv` and segment `beat_asset_plan.csv`; run:

```bash
python "$SKILL_DIR/scripts/visual_sync_lint.py" "$PROJECT_DIR" S001 --fail-under 85
```

7. `assets` - gather/select assets using `references/multimedia-asset-taxonomy.md`, `references/web-sourced-visual-assets.md`, and `references/visual-asset-generation.md`; run:

```bash
python "$SKILL_DIR/scripts/asset_selection_lint.py" "$PROJECT_DIR" --fail-under 82
python "$SKILL_DIR/scripts/beat_asset_coverage_lint.py" "$PROJECT_DIR" S001 --fail-under 90
```

8. `sound-design` - generate or revise `prosody_plan`, TTS, cue sheet, mix plan.
9. `director-compiler` - run `director_compiler.py`, then manually improve generic actions.
10. `segment` - build HyperFrames/Remotion/Motion Canvas from `vo_timing.json`, `rhythm_map.json`, `visual_sync_plan.csv`, `micro_timing.json`, assets, choreography, and cue sheet.
11. `assemble` - create `edit/timeline.json`, captions, mix, draft export.
12. `qc` - run validation, rhythm, visual sync, asset, timing, aesthetic, audio, rights, and caption checks.
13. `revise` - change the earliest upstream artifact and list downstream rebuild impact.
14. `resume` - read `.video/state.json`, continue from the next unapproved stage.

## Factual Script Rules

For factual videos, load:

- `references/deep-narrative-investigation.md`
- `references/fact-linked-script-system.md`
- `references/retention-storytelling-and-voice.md`

Required:

- `research/source_cards.jsonl`
- `research/claim_ledger.csv`
- `research/factcheck_report.md`
- claim IDs in factual voiceover lines
- `research/thread_ledger.csv` and `script/narrative_thread_map.json` for deep narrative work

Do not invent causal links. If a link lacks evidence, mark it as an open question, say the uncertainty on camera, or cut it.

## Rhythm & Voice Rules

Load `references/director-rhythm-system.md`, `references/vo-sync-timing-protocol.md`, and `references/music-tts-voiceover.md`.

Required order:

```bash
python "$SKILL_DIR/scripts/build_director_rhythm.py" "$PROJECT_DIR" --write-prosody
python "$SKILL_DIR/scripts/indextts2_generate.py" "$PROJECT_DIR" --segment S001 --concat
python "$SKILL_DIR/scripts/measure_segment_vo.py" "$PROJECT_DIR" S001
python "$SKILL_DIR/scripts/build_micro_timing.py" "$PROJECT_DIR" S001
python "$SKILL_DIR/scripts/director_rhythm_lint.py" "$PROJECT_DIR" --segment S001 --fail-under 80
python "$SKILL_DIR/scripts/segment_timing_lint.py" "$PROJECT_DIR" S001
```

Targets:

- spoken Chinese: usually 4.2-5.8 characters/sec after pauses
- dense evidence or UI: slower or longer visual hold
- hook: faster visual change, not necessarily faster speech
- proof: image appears before or with the claim, remains long enough to read
- reveal/twist: short pre-pause or post-hold is preferred over more animation

## Visual Sync & Assets

Load:

- `references/director-rhythm-system.md`
- `references/multimedia-asset-taxonomy.md`
- `references/web-sourced-visual-assets.md`
- `references/visual-asset-generation.md`
- `references/layered-composition-depth.md`

Every beat should include:

- `spoken_focus`: the phrase or idea the audience must catch
- `visual_subject_desc`: what is visibly on screen
- `screen_content_desc`: what the asset/frame actually contains
- `must_show_detail`: detail that must remain uncropped/readable
- `visual_read_time_sec`: minimum time needed to understand the frame
- `trim_policy`: `no_trim`, `trim_to_action`, `loop_safe`, or `ken_burns_fill`
- `crop_anchor`: face, UI button, document title, chart axis, logo, object, or none

Do not full-bleed proof screenshots over captions. Place proof media inside source cards, device frames, document frames, or a clearly labeled evidence slot.

## Motion & HyperFrames

Load:

- `references/director-compiler-os.md`
- `references/hyperframes-director-implementation.md`
- `references/motion-life-playbook.md`
- `references/voice-synced-animation-design.md`
- `references/layered-composition-depth.md`

Before coding:

1. Build a static styleframe/layout first.
2. Assign each beat one focal owner.
3. Schedule micro-events from `segments/<id>/micro_timing.json`.
4. Use `rhythm_map.json` to add lead-in, hold, and scene-reset timing.
5. Keep HUD captions readable and outside motion collisions.

Reject:

- one centered card for a full beat
- fade-only animation
- all elements moving with equal intensity
- evidence shown after the line that refers to it
- motion that hides the detail the narrator is discussing

## Quality Gates

Run the relevant gates before final render:

```bash
python "$SKILL_DIR/scripts/validate_project.py" "$PROJECT_DIR"
python "$SKILL_DIR/scripts/thread_depth_lint.py" "$PROJECT_DIR" --fail-under 80
python "$SKILL_DIR/scripts/script_claim_lint.py" "$PROJECT_DIR" --fail-under 85
python "$SKILL_DIR/scripts/director_rhythm_lint.py" "$PROJECT_DIR" --fail-under 80
python "$SKILL_DIR/scripts/visual_sync_lint.py" "$PROJECT_DIR" S001 --fail-under 85
python "$SKILL_DIR/scripts/asset_selection_lint.py" "$PROJECT_DIR" --fail-under 82
python "$SKILL_DIR/scripts/beat_timeline_lint.py" "$PROJECT_DIR" --fail-under 80
python "$SKILL_DIR/scripts/beat_asset_coverage_lint.py" "$PROJECT_DIR" S001 --fail-under 90
python "$SKILL_DIR/scripts/segment_timing_lint.py" "$PROJECT_DIR" S001 --full
python "$SKILL_DIR/scripts/aesthetic_score.py" "$PROJECT_DIR" --fail-under 72
python "$SKILL_DIR/scripts/audio_score.py" "$PROJECT_DIR" --fail-under 72
```

For Douyin/Bilibili AI explainers, also run:

```bash
python "$SKILL_DIR/scripts/douyin_ai_explainer_score.py" "$PROJECT_DIR" --fail-under 78
```

## Checkpoint Behavior

Default to checkpoint mode: finish one stage, write artifacts, run the stage validators, and summarize what changed.

When revising, change the earliest responsible artifact:

- voice too fast -> `voiceover.md`, `narration_beats.csv`, `prosody_plan.csv`
- picture late/early -> `rhythm_map.json`, `visual_sync_plan.csv`, `beat_timeline.json`
- bad or irrelevant media -> `asset_selection_report.json`, `asset_manifest.csv`
- ugly/flat frames -> `art_direction.md`, `tokens.json`, `shotlist.json`, `asset_choreography_manifest.csv`
- chaotic animation -> `beat_timeline.json`, `micro_timing.json`, `audio_cue_sheet.json`

Never overwrite approved or locked artifacts. Create versioned siblings and update state only after approval.

