---
name: video-producer
description: "Chinese AI/developer-tool video director skill for Codex, Claude Code, and Cursor. Use when producing, researching, scripting, revising, reviewing, or rendering short videos that need deep research, factual source locking, narrative depth, narration-beat timing, shot grammar, screenshots/code/terminal/UI proof choreography, motion design, sound cues, subtitles/flower text, Remotion/HyperFrames/vibe-motion/Motion Canvas/GSAP/FFmpeg/TTS routing, first-slice preview, and review-studio QA. Delegates reference YouTube/Bilibili/Douyin/local transcript extraction to subtitle-extractor."
---

# Video Producer

This skill is a director dispatcher, not a bureaucratic production pipeline. It turns a topic, script, reference video, product workflow, screen evidence, or technical idea into a tightly timed Chinese short video plan, renders a 20-30 second first slice, reviews it visually, repairs the plan, and only then expands to the full video.

Do not implement or render the full video before the first-slice preview passes review.

## Priority Stack

When instructions compete, obey this order:

1. **Story / VO coherence (analytical jobs)**: if the user asked for research,口播, or script-only, finish a kill-checklist-passing `outputs/script.md` before optimizing shots, metaphor boards, or first-slice polish. Do not sacrifice story continuity for visual checklists.
2. **First-slice proof**: once picture work starts, make the first 20-30 seconds reviewable before expanding the full video.
3. **Narration-to-picture binding**: every beat needs a visual owner and visible action.
4. **Style coherence**: use one style preset and one visual world per first slice.
5. **Rhythm**: visible micro actions every 0.8-1.5s and one macro reset around 8-12s.
6. **Renderer delegation**: call other skills only for bounded shot slots.
7. **Polish**: subtitles, flower text, SFX, transitions, and extra effects support the picture.

If complexity threatens execution, cut optional effects before cutting story, proof, timing, or review.

## Context Budget

Do not load every reference file. Load only what the current step needs:

- Always start from this `SKILL.md`.
- **Research + VO / script-only**: load `references/deep-research-and-script.md`, then `references/narrative-depth-copy.md` (SSOT) + `references/storyteller-fan-craft.md` + **1–2** transcripts from `references/storyteller-fan-corpus/` (`CATALOG.md`). Do **not** require `style-dna.md` / `shot-grammar.md` until beat planning starts.
- **Picture / first-slice work**: load `references/style-dna.md` and `references/shot-grammar.md` when writing `beat_plan.json` / `segment_spec.json`.
- Load `references/renderer-selection.md` only when choosing or delegating implementation.
- Load `references/audio-sync-grammar.md` only when writing or fixing `audio_cue_sheet.json`.
- Load `references/review-rubric.md` only before review, scoring, or repair.
- Use `assets/templates/example_*.json` only as shape examples; do not copy their content into a real project.

Default first-slice complexity: one style preset, 3-5 shot recipes, 4-8 narration beats, at most 1-2 delegated skill slots, and only the SFX that match visible actions.

## Director Dispatch Model

Treat Video Producer as the director layer above specialized skills and renderers. It owns the story thread, style DNA, beat timing, shot grammar, audio/visual sync, and review loop. It does not need to personally implement every effect.

For each shot, decide the best owner:

- **Remotion timeline**: assemble the first slice, subtitles, audio, SFX, screen/code/terminal scenes, and final render.
- **HyperFrames scene**: create HTML/CSS/GSAP UI rooms, dashboards, kinetic cards, browser-previewable explainers, and fast first-slice scenes.
- **vibe-motion or specific motion skills**: render a high-quality reusable effect, procedural scene, globe/route/ticker/assembly motion, or other slot when an installed skill already matches the shot.
- **Motion Canvas / SVG / GSAP**: build precise instructional diagrams, Git graphs, timelines, branches, flow maps, arrows, red boxes, morphs, and metaphor objects.
- **FFmpeg / audio tools / TTS**: measure voice, build contact sheets, mix/duck SFX, stitch local renders, transcode, and package delivery.
- **subtitle-extractor**: when the user supplies a reference YouTube / Bilibili / Douyin / local video and you need spoken text or timed cues, delegate extraction first. Do not invent transcripts.

When a shot is delegated, record the slot in `segment_spec.json`:

```json
"delegation": {"skill": "hyperframes", "purpose": "dashboard proof room", "input_artifacts": ["outputs/segment_spec.json"], "output_artifacts": ["segments/S001/proof_room.mp4"], "acceptance": "readable, seekable, same style"}
```

The receiving skill may choose its own implementation details, but it must honor the style preset, shot time range, visual owner, action list, and audio cue contract. If a delegated scene does not match the style world, repair the slot or reroute it; do not paper over mismatch with a transition.

## Operating Principle

Every narration beat must cause a visible action. Subtitles help comprehension; they are never the main picture. The main picture should be a directed mix of screenshots, code, terminal, browser, phone UI, charts, SVG metaphors, keyword actors, cursor actions, highlights, camera moves, and sound-driven transitions.

Prefer fewer artifacts with harder constraints:

```text
outputs/
  script.md
  beat_plan.json
  segment_spec.json
  audio_cue_sheet.json
  review/
    preview.mp4
    contact_sheet.jpg
    metrics.json
    failed_checks.md
    execution_trace.json
    review-studio/
```

`segment_spec.json` is the contract between direction and implementation. If it is vague, repair it before writing animation code.

## Required Workflow

1. Understand the target video, audience, reference style, format, duration, and available proof assets.
2. If the user provides a reference video URL or local media and you need its spoken content, timing, or quoteable lines, run `subtitle-extractor` before beat planning:

```bash
python ../subtitle-extractor/scripts/extract_subtitles.py "<url-or-file>" -o outputs/subtitles --lang zh
```

Write a delegation note when used:

```json
"delegation": {"skill": "subtitle-extractor", "purpose": "timed transcript from reference video", "input_artifacts": ["inputs/reference.url"], "output_artifacts": ["outputs/subtitles/*.srt", "outputs/subtitles/*.json"], "acceptance": "non-empty timed segments"}
```

Prefer soft/auto captions over ASR. Feed `outputs/subtitles/*.txt` / segments into research and script; treat cue times as hints only and re-measure after TTS.

3. If the topic needs facts, judgment, product analysis, web evidence, or a non-shallow argument, run the deep research/script loop in `references/deep-research-and-script.md` and produce a kill-checklist-passing `outputs/script.md` **before** beat planning. If the user only asked for口播/script, **stop after script + research validate** (record picture-stage skips in `failed_checks.md`).
4. Only when moving to picture work: choose one style preset from `references/style-dna.md`, then select 3-5 shot recipes from `references/shot-grammar.md`.
5. Write `outputs/beat_plan.json` (and refine `outputs/script.md` if beat edits change VO) with second-level narration beats.
6. Write `outputs/segment_spec.json` for the first 20-30 seconds only. Each shot must include renderer/skill ownership, start/end time, camera, visual owner, action list, text strategy, transition reason, and acceptance notes.
7. Write `outputs/audio_cue_sheet.json` from beat keywords and visual actions. Do not add SFX that lack visible motivation.
8. Validate the plan:

```bash
python scripts/validate_segment_spec.py outputs/segment_spec.json
python scripts/score_preview_plan.py --outputs outputs
```

9. Render only the first slice with the selected renderer(s) or delegated skill slots. Prefer the simplest renderer set that can make the slice rich enough.
10. Build `outputs/review/contact_sheet.jpg` and `outputs/review/review-studio/`.
11. Review the first slice. Fix the earliest responsible artifact: research, script, beat plan, segment spec, audio cues, assets, renderer implementation, or edit.
12. After review passes, extend `segment_spec.json` and implementation to the full video.

When a new project is needed, create it on the user's Desktop by default. If Desktop is unavailable, create it under the user's home directory. Do not default to writing projects inside the skill repository.

## Deep Research And Script

Use when facts, judgment, product/industry analysis, or non-shallow argument matter. Skip for pure motion tests, logo stings, UI demos with no claims, or user scripts that ask for no research.

**Load together:** `references/deep-research-and-script.md` (search + lock) and `references/narrative-depth-copy.md` (VO SSOT). For analytical VO, also load `references/storyteller-fan-craft.md` and sample **1–2** corpus transcripts. Do not restate VO gates here.

Default depth artifacts (tiered — do not invent a paperwork pile):

```text
# always on depth jobs
research/source_cards.jsonl
research/event_genealogy.md    # tip/upstream/timeline/dig/harvest; cast may live here
outputs/script.md

# on demand
research/claim_ledger.csv           # many claims / easy to get wrong
research/factcheck_report.md        # dispute / skip log
script/narrative_thread_map.json    # long / multi-strand only
research/thread_ledger.csv          # multi-strand only
```

Small jobs may fold source lock + genealogy into sections inside `outputs/script.md`. Constraints stay the same.

Scaffold with `--deep` when initializing:

```bash
python scripts/init_video_project.py --name "..." --deep
python scripts/validate_research_lite.py --project /path/to/project
```

This is a `script-only draft` until the lite review contract exists (`beat_plan` / `segment_spec` / `audio_cue_sheet` / review stubs). Plan-only may omit `preview.mp4`; record that in `failed_checks.md`. Do not call a project review-ready when it only has `outputs/script.md`.

**Three VO hard gates** (details only in `narrative-depth-copy.md`):

1. **Story thread** — tip → what happened → jam/unknown → takeaway; one coherent line, not topic-bucket menus.
2. **Instant comprehension** — people/companies/numbers land via background + impact in the same talk turn; story entry, not teaching deconstruction (`你就记` / `别听成黑话` / …).
3. **Oral human feel** — read-aloud like 老范跟朋友讲热新闻; natural reactions + TTS-friendly punctuation; no outline/lesson-talk; **no skill/meta phrasing in spoken body** (`大白话` / `活人味` / `因果河` / unexplained short metaphors).

Also: every factual claim needs source / uncertainty / deletion; no invented causality. **Selective dig:** pick **1–2 expand beats per short script** by tip impact, knowledge yield, and evidence — not by expanding every named actor (see `deep-research-and-script.md` dig rubric). **Visual proof tags belong at beat-planning time** — do not force metaphors or shot recipes while the VO story is still broken. Default voice = 老范讲故事式讲解（广度/深度/聊天节奏；学故事债与人物出场；不学频道壳；不学教辅拆词）。

Optional craft lint after drafting VO:

```bash
python scripts/validate_vo_craft.py --project /path/to/project
```

Record skipped depth checks in `factcheck_report.md` or `failed_checks.md`; do not silently skip depth for factual/analytical videos.

## First-Slice Gate

The first deliverable is a 20-30 second golden slice containing the hook, at least one proof/action scene, one macro visual reset, and a clear audio/visual rhythm sample.

Hard blockers before full-video work:

- `outputs/review/preview.mp4` exists or the user explicitly asks for plan-only output.
- `outputs/review/contact_sheet.jpg` exists when `ffmpeg` is available.
- `outputs/review/metrics.json` and `outputs/review/failed_checks.md` exist.
- `outputs/review/review-studio/index.html` exists.
- `failed_checks.md` has no unresolved first-slice blockers.

## Segment Spec Contract

Use `assets/templates/segment_spec.schema.json` as the source of truth. A segment contains:

- `segment_id`, `style`, `duration`, `first_slice`
- `shots[]` with `shot_id`, `[start,end]`, `recipe`, `renderer`, `component`, optional `delegation`, `visual_owner`, `camera`, `narration_beats`, `visual_actions`, `text_strategy`, `transition_out`, `qa_notes`
- each visual action has `at`, `type`, optional `text`, `asset`, `motion`, `sfx`, `annotation`

Every beat in `beat_plan.json` must be referenced by at least one shot and must have:

- `beat_id`
- `time`
- `voice_text`
- `keyword`
- `intent`
- `visual_owner`
- `visual_action`
- `subtitle_strategy`
- optional but recommended `audio_cue`

## Renderer / Skill Selection

Read `references/renderer-selection.md` before implementation.

- Use Remotion for the main timeline, subtitles, audio tracks, React components, screen/code/terminal scenes, and final render.
- Use HyperFrames for fast HTML/CSS/GSAP scenes, complex UI boards, kinetic typography, cards, dashboards, and reviewable browser previews.
- Use vibe-motion when a high-quality motion scene or local effect already matches the shot.
- Use Motion Canvas for code teaching, SVG diagrams, algorithm flow, graph growth, and precise instructional animation.
- Use GSAP/SVG for local expressive motion, keyword actors, arrows, red boxes, graph edges, morphs, and transitions.
- Use FFmpeg for contact sheets, transcode, audio mix, trim, stitch, and delivery formats.
- Use TTS/voice tools only after beat timing is inspectable; remeasure voice before locking animation.
- Use `subtitle-extractor` for reference-video transcripts (YouTube / Bilibili / Douyin / local). It owns extraction only; Video Producer still owns beats, flower text, and burn-in.
- When using another skill, pass only the slot contract, style preset, required assets, and expected output. Keep Video Producer responsible for the global timeline and final review.

## Review Studio

Review Studio reads and writes the same `outputs/` contract as the rest of the skill.

Static bundle:

```bash
python scripts/build_review_bundle.py --outputs outputs
```

Full local app (TTS, beat edit, timeline):

```bash
python review-studio/server/main.py --project /path/to/project --port 8787
```

Review Studio uses:

```text
outputs/beat_plan.json          # SSOT for voice_text and beat metadata
outputs/segment_spec.json       # shots and visual_actions
outputs/script.md               # long-form script (synced from beat_plan on edit)
segments/{seg}/vo_timing.json   # measured TTS durations (runtime)
segments/{seg}/micro_timing.json
audio/stems/voice/beats/*.wav   # TTS output
outputs/review/*                # preview, metrics, static bundle
```

There is no `script/narration_beats.csv` in the lite workflow. All beat reads and writes go through `scripts/beat_store.py`.

## Quality Rules

- Every 0.8-1.5 seconds: one visible micro action.
- Every 8-12 seconds: one macro scene reset or obvious visual room change.
- A static text-only frame must not last longer than 1.5 seconds.
- Two consecutive narration beats must not share the same static picture.
- The first slice must cover the full declared duration; do not leave the last seconds unspecified.
- Every abstract concept must become a screenshot, chart, UI state, metaphor object, flow, timeline, code/terminal action, or animated diagram.
- Screenshots cannot be merely placed on screen; they need push-in, crop, redbox, cursor, zoom, highlight, annotation, or before/after choreography.
- Key visual actions need sound cues or intentional silence.
- Renderer changes need a visual reason: new room, new proof type, new metaphor, or a delegated effect that is visibly stronger than local code.
- Sound effects must never fight the voice.
- Hook within the first 3 seconds: one clear question, contradiction, proof moment, or visual surprise.

## Failure Repair Loop

Fix the specific failure instead of regenerating the whole video:

- Too static: add micro actions to `segment_spec.json`.
- Not like reference style: change style preset, shot recipes, background system, proof assets, transitions, and sound density.
- Voice and picture disconnected: add `visual_owner`, `visual_action`, and shot binding for the beat.
- Boring screenshot: add push-in, crop, redbox, cursor, zoom, blur focus, or source-stack motion.
- Weak sound: add cues for keyword pops, red boxes, typing, transitions, and conclusion hits.
- Subtitle is carrying the scene: move information into visual owner, chart, UI, SVG, or flower text.
- Pacing drags: shorten shots, split beats, add macro reset.
- Too noisy: delete decorative effects that do not serve a keyword, proof point, or transition.

## Scripts

Only these scripts are part of the active workflow:

| Script | Purpose |
|--------|---------|
| `init_video_project.py` | Scaffold lite project; add `--deep` for research stubs |
| `validate_research_lite.py` | Depth skeleton: sources + genealogy + script |
| `validate_vo_craft.py` | Soft/hard lint: teaching-deconstruction anti-patterns in VO |
| `sync_storyteller_fan_corpus.py` | Refresh StorytellerFan txt corpus from `outputs/subtitles/StorytellerFan` |
| `validate_segment_spec.py` | Validate `segment_spec.json` + `beat_plan.json` |
| `score_preview_plan.py` | Score first slice → `metrics.json` / `failed_checks.md` |
| `build_review_bundle.py` | Static Review Studio bundle + runtime sync |
| `build_contact_sheet.py` | FFmpeg contact sheet from preview |
| `beat_store.py` | Library: read/write `outputs/beat_plan.json` |
| `beat_narration_sync.py` | Sync beat voice lines → `outputs/script.md` |
| `indextts2_generate.py` | TTS per beat from `voice_text` |
| `indextts2_connect.py` | IndexTTS connectivity helper |
| `measure_segment_vo.py` | Measure WAV → `vo_timing.json` |
| `audio_chain.py` | TTS → measure → micro_timing → lint |
| `segment_timing_lint.py` | VO/CPS timing QC |
| `sync_segment_duration.py` | Sync composition duration from VO |
| `review_core.py` | Registry, stale propagation, lite stages |
| `regen_dispatch.py` | Print regen queue tasks |
| `tts_progress.py` | TTS job progress for Review Studio |
| `audio_ref_utils.py` | Reference audio helpers |

Do not use scripts under `examples/legacy/` for new projects.

## References

- Style presets: `references/style-dna.md`
- Deep research (search + locks): `references/deep-research-and-script.md`
- Narrative depth copy (VO SSOT, 老范口播默认): `references/narrative-depth-copy.md`
- StorytellerFan craft + corpus (analytical VO: sample 1–2 transcripts): `references/storyteller-fan-craft.md` + `references/storyteller-fan-corpus/`
- Reusable shot recipes: `references/shot-grammar.md`
- Audio/visual cue rules: `references/audio-sync-grammar.md`
- Renderer routing: `references/renderer-selection.md`
- Review scoring and checks: `references/review-rubric.md`
- Schemas and minimal examples: `assets/templates/`
- Legacy archived material (**do not load for new projects**): `examples/legacy/`
