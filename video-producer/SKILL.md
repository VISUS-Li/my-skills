---
name: video-producer
description: "Director-grade video production skill for factual Chinese explainers, news/context videos, social issue narration, finance/tech explainers, and story-driven short videos. Use when Codex needs to create, revise, diagnose, or render videos/scripts where voice-to-picture precision, real evidence, screenshots, B-roll, dynamic text, data visualization, transitions, pacing, HyperFrames/Remotion implementation, TTS, sound design, or non-PPT editorial quality matters."
---

# Video Producer

Behave as a video director, not a template pipeline. The goal is a short video where the viewer sees the right thing at the exact moment the narration needs it: real footage for reality, screenshots for proof, diagrams for mechanisms, text for emphasis, charts for numbers, and a designed visual world that never feels like empty text on a plain background.

Default execution path:

`bootstrap -> research/fact lock -> script beats -> director decisions -> external asset selection + HyperFrames-native plan -> implementation -> director QC`

Do not jump from `script -> broad visual prompt -> render`.

Core principle: every visible thing is cast by the director. Actors, screenshots, B-roll, charts, icons, flower text, captions, layout modes, animations, ambient HyperFrames components, and silence/negative space are all optional tools. None are mandatory by default, and none are banned by default. Use them only when they serve the script beat, storyboard function, evidence need, emotional rhythm, or viewer comprehension.

## Bootstrap

Resolve `PROJECT_DIR` before writing artifacts.

- If the user provides a path, use it.
- Otherwise run `init_video_project.py` with `--name` only; it creates `~/projects/<slug>/` automatically.
- Never write project outputs into the skill repo root.

Initialize only when `.video/state.json` is absent:

```bash
python "$SKILL_DIR/scripts/init_video_project.py" \
  --name "<title>" \
  --input-type <idea|article|video|url|mixed> \
  --ratio <16:9|9:16> \
  --duration <seconds>

# Optional: override default ~/projects/<slug>/
#   --root "/path/to/custom-project-dir"

python "$SKILL_DIR/scripts/validate_stage.py" "$PROJECT_DIR" --stage plan
```

Tell the user the absolute `PROJECT_DIR`. Initial templates intentionally contain example narration rows; replace them before running full `validate_project.py` or advancing `script`. Do not mark `script` or later stages `review` until `validate_stage.py` exits 0 for that stage.

## Core Director Loop

For every segment and beat, make these decisions in order:

1. **Beat function:** fact, evidence, data, mechanism, scene, person, emotion, contrast, transition, or viewpoint.
2. **Audience need:** credibility, understanding, proof, scale, emotional entry, contrast, suspense, or closure.
3. **Visual owner:** the one asset/action that owns attention at this moment.
4. **Casting decision:** decide which visual actors are needed and which should stay out: person/scene, evidence screenshot, data object, text actor, icon/support actor, annotation, ambient world, SFX, or deliberate blank space.
5. **Shot and layout mode:** choose establish/insert/comparison/mechanism/reset/payoff and a layout mode (grid, vertical stack, asymmetric, diagonal, full-screen proof, split, or sparse). Do not default to left-right.
6. **Material choice:** real footage/photo, UI/web/document screenshot, external chart/data source, HyperFrames-native diagram/card/text/shape/chart, SVG annotation, ambient texture, or silence/black.
7. **Phrase binding:** map nouns, verbs, numbers, contrast words, and emotion words to visible events.
8. **Text choreography:** decide whether text should be absent, caption-only, keyword-level, number-hero, quote/card, sticker/flower-word, or viewpoint-line. Text is an actor; size, color, position, and timing must follow the narration rather than appearing as one flat sentence.
9. **Visual world:** choose the background system, support actors, icons/cards/charts, depth layers, and ambient motion that make the frame feel alive, or intentionally remove them for a reset/viewpoint beat.
10. **Density and rhythm:** decide whether this beat should be rich, readable-dense, medium, sparse, fast, slow, or silent.
11. **Transition anchor and motion preset:** carry color, shape, text, number, position, or motion direction into the next beat when possible; use a named preset when the action is a common entrance/exit/text/yield move.

Read `references/director-decision-system.md` before script beats, visual sync, asset selection, or revision.

## Required Artifacts

Keep the project reviewable. These files are the main creative contract:

- `script/voiceover.md`: spoken script with claim IDs for factual lines.
- `script/narration_beats.csv`: **one row per beat** with full schema from the skill template (`narration`, `duration_sec`, `spoken_focus`, `semantic_action`, `visual_need`, `beat_type`, `information_density`, etc.). `spoken_focus` alone is not a substitute for `narration`; Review Studio and TTS read the `narration` column.
- `script/visual_sync_plan.csv`: exact picture-to-phrase decisions for **every** `beat_id` in `narration_beats.csv`, including focal owner, must-show detail, text treatment, transition anchor, and acceptance check.
- `assets/asset_selection_report.json`: external candidate assets scored for relevance, readability, crop safety, rights, and selected role.
- `assets/asset_manifest.csv`: final external assets and any programmatic components that need cross-segment tracking.
- `segments/<id>/beat_asset_plan.csv`: beat-level asset binding for **every** narration beat, including density target, focal owner, trim/crop policy, and readable hold time.
- `script/text_manifest.json`: dynamic text units, not whole sentences as one flat caption. Use optional `spans` and `motion_preset_id` when a line needs keyword-level timing, oversized words, color/stroke/shadow emphasis, or sticker/flower-word behavior.
- `script/beat_timeline.json`: timestamped micro-events for visual actions, text hits, camera moves, layout changes, yield/displacement moves, preset IDs, SFX, and optional `visual_cast` notes that name lead/support/withheld actors for complex beats.
- `audio/prosody_plan.csv` and `audio/audio_cue_sheet.json`: speech rhythm, pauses, emphasis, and event-anchored sound. `prosody_plan.csv` `tts_text` must mirror `narration_beats.csv` `narration`.
- `scripts/build_<segment>_composition.py`: the standard composition build entry for Review Studio and automation. For `S001`, this is `scripts/build_s001_composition.py`. Segment-local builders may be helper modules only; they must not be the only build entry.
- `segments/<id>/index.html`: the seekable HyperFrames composition generated by the standard builder. It must register `window.__timelines[segment]` and expose `window.initComposition`.

After `init_video_project.py`, **replace all template example rows** (earthquake/App demo beats). Never leave init-template text in narration, visual sync, or prosody files.

## Stage Hard Gates

Do not advance a stage to `review`, `approved`, `locked`, or `rendered` until validation passes.

**Before every stage advance**, run:

```bash
python "$SKILL_DIR/scripts/validate_stage.py" "$PROJECT_DIR" --stage <stage_id>
```

`stage_gate.py` and Review Studio enforce the same checks automatically.

| Stage | Hard checks (in addition to required files) |
|-------|-----------------------------------------------|
| `script` | `narration` column present; every beat has non-empty `narration` + timing; `voiceover.md` filled; no init-template leftovers |
| `assets` | `beat_asset_plan.csv` beat_ids match `narration_beats.csv`; no template leftovers |
| `director-plan` | `visual_sync_plan.csv` beat_ids match; `spoken_focus` aligned; `validation_scripts` pass |
| `voice-and-sound` | `prosody_plan.csv` `tts_text` matches each beat `narration` |

Workflow rule: finish `script` beats (with `narration` text split from `voiceover.md`) **before** `visual_sync_plan` / `beat_asset_plan` / `director_compiler.py`. Running the compiler on template rows propagates wrong timings into `beat_timeline.json`.

Example:

```bash
python "$SKILL_DIR/scripts/validate_stage.py" "$PROJECT_DIR" --stage script
python "$SKILL_DIR/scripts/stage_gate.py" "$PROJECT_DIR" --stage script --status review --note "beats + voiceover ready"
```

## Reference Loading

Load only what the task needs:

- **Director and material decisions:** `references/director-decision-system.md`
- **Phrase-to-picture and dynamic text:** `references/phrase-to-picture-binding.md`
- **Shot language, screenshot acting, density, transitions:** `references/editorial-shot-language.md`
- **Rich HyperFrames visual world:** `references/visual-world-and-richness.md`
- **Asset sourcing and rights:** `references/evidence-and-asset-sourcing.md`
- **Motion, presets, micro-events, and sound cues:** `references/motion-and-transition-grammar.md` and `assets/templates/micro_animation_palette.json`
- **Factual research and narrative script:** `references/factual-research-and-script.md`
- **HyperFrames-native generation and implementation:** `references/hyperframes-implementation.md`
- **Director QC rubric:** `references/director-quality-review.md`
- **Voice, TTS, and mix:** `references/audio-voice-and-mix.md`
- **Windows Chinese SVG:** `references/svg-utf8-windows.md`

## Factual Videos

For news, finance, tech, public-policy, health, social, or documentary-style videos:

1. Build `research/source_cards.jsonl`, `research/claim_ledger.csv`, and `research/factcheck_report.md`.
2. Give each factual claim a `claim_id`.
3. Prefer real-world assets for real-world claims: official pages, app screens, tables, product pages, charts, photos, footage, public statements, or news screenshots.
4. If evidence is uncertain, say the uncertainty, mark the row, or cut the claim.

Load `references/factual-research-and-script.md`.

## Visual Sync Rules

- Concrete nouns need concrete pictures. If the line names an app, company, person, price, product, document, place, or event, first look for a real asset or screenshot.
- Use HyperFrames natively for simple generative material: dynamic text, color blocks, cards, device/browser frames, red boxes, arrows, callouts, background texture, simple charts, counters, quote cards, labels, masks, and transition shapes. Do not create these in the asset generation stage unless they must be exported/reused as standalone files.
- A HyperFrames-native beat should still be visually rich when the content calls for it: use a designed background bed, cards/frames, icons, small charts, source stacks, cursor/focus tools, and micro-motion. "Native" does not mean "only text."
- SVG is usually annotation, structure, connection, or transition glue. It should often be inline HyperFrames/SVG/HTML/CSS, not a separately generated asset, and should not become the default subject for real events.
- Screenshots must perform: show full context, push into the important area, highlight with a red box/label/magnifier, hold long enough to read, then exit or shrink into an evidence stack.
- Data must perform: number/price/percent can become the largest element; charts should build or compare, not appear as decoration.
- Text must perform: split important words, numbers, contrast terms, quotes, and emotion lines into separate text units with size, color, position, and timing.
- Text is optional but, when used, should be directed like an actor: attach it to a proof/detail when possible, let key words be larger than support words, use stroke/shadow/color only for real emphasis, and reveal by phrase/keyword when narration rhythm benefits from it.
- Layout follows beat function. Use regular grids for comparison, tables, and systematic mechanisms; use vertical, asymmetric, diagonal, or full-screen proof compositions when they better protect the focal owner or make a social-video frame feel less static.
- Actors/support material are optional but should create variety across the film. A mature explainer alternates proof, data, mechanism, human texture, text emphasis, and quiet space according to the script instead of repeating one empty or one busy composition.
- Use yield/reactive displacement only when a new text/annotation/insert must enter without covering `must_show_detail`. Proof screenshots and tables should usually stay stable; if they move, the move must preserve source labels, critical rows, axes, and readable hold.
- Emotion and viewpoint beats may deliberately remove visual clutter: black screen, white text, a human cutaway, night street, back view, or low-saturation quiet footage can be stronger than another chart.

## Rhythm Rules

- Plan from narration, but bind final timings to measured voice files (`segments/<id>/vo_timing.json`) after TTS.
- Evidence, UI, tables, and charts need readable hold time and often slower speech.
- Hooks can be visually sharp but must have one clear focal object in the first second.
- Person/life-impact sections should breathe: fewer overlays, slower push, more real texture.
- Transitions should use semantic continuity: shared color, shape, word, number, composition zone, or motion direction.

## Implementation

Before coding a segment:

1. Create or update a static styleframe/layout that already communicates the focal owner, background world, support actors, and hierarchy.
2. Mark `hf_*`, `text_*`, `chart_*`, `svg_*`, and `ambient_*` items that will be generated directly in HyperFrames code instead of external asset files.
3. Load `assets/templates/micro_animation_palette.json` or the project-local copy and map `motion_preset_id` / `text_preset_id` to GSAP timeline helpers. Preset names are semantic contracts; implementation can vary by layout as long as timing and focal ownership are preserved.
4. Bind micro-events from `script/beat_timeline.json` to voice timing.
5. Implement exact Chinese text as HTML/SVG/canvas text layers, not baked into generated images. Support `text_manifest.items[].spans[]` for mixed size/color/stroke/shadow/timing inside one spoken line.
6. Keep captions, source labels, table rows, chart axes, and UI details readable.
7. Use sound only where it has a visual or semantic anchor: click, tick, stamp, whoosh, chime, silence, or no cue.

For HyperFrames, load `references/hyperframes-implementation.md`.

### Review Studio Composition Contract

Review Studio's composition preview loads `segments/<id>/index.html` in an iframe and drives the picture by calling `compIframe.contentWindow.__timelines[segment].time(t)` from the audio clock. Do not rely on `tl.play()` or autoplay. The timeline must be paused and seekable.

Hard requirements:

- Build through `scripts/build_<segment>_composition.py`. For `S001`, keep `scripts/build_s001_composition.py` as the primary entry; if a rich segment helper exists under `segments/<id>/scripts/`, call it from the root builder instead of replacing the root builder.
- Generated HTML must include `data-composition-id`, `data-build-entry`, `window.initComposition`, `window.__timelines`, `window.__timelines[segment]`, and `window.__compositionErrors`.
- Register `window.__timelines[segment] = tl` inside `initComposition()` before adding risky optional tweens, so runtime errors are visible and the preview contract exists.
- Create the GSAP timeline with `paused: true`; never call `play()` in composition HTML. Review Studio seeks frames; audio playback belongs to the parent page.
- Guard optional selectors. Use helper functions such as `safeTargets()`, `addFromIfPresent()`, and `addToIfPresent()` before `tl.from()` / `tl.to()` for beat-specific nodes. A beat that lacks `.hf-scan-line`, `.proof-img`, `.anim-proof`, or `.anim-diagram` must not emit GSAP target warnings.
- GSAP property callbacks receive `(index, target, targets)`. For dataset-driven values, write `width: (index, target) => target.dataset.pct`, never `width: (el) => el.dataset.pct`.
- Surface runtime errors in `window.__compositionErrors` and an on-frame error overlay. Silent failures before timeline registration are not acceptable.

Before handing a segment to review, run:

```bash
python "$SKILL_DIR/scripts/test_composition_preview.py" "$PROJECT_DIR" --segment S001 --no-server
python "$SKILL_DIR/scripts/test_composition_preview.py" "$PROJECT_DIR" --segment S001
```

The second command also validates the Review Studio proxy and, when Playwright is installed, checks that the iframe runtime actually registers a paused timeline with nonzero duration.

## Quality Gates

Run the relevant checks before final render. Stage advances (`stage_gate.py --status review|approved`) **fail automatically** if these are not satisfied:

```bash
python "$SKILL_DIR/scripts/validate_stage.py" "$PROJECT_DIR" --stage <stage_id>
python "$SKILL_DIR/scripts/validate_project.py" "$PROJECT_DIR"
python "$SKILL_DIR/scripts/script_claim_lint.py" "$PROJECT_DIR" --fail-under 85
python "$SKILL_DIR/scripts/visual_sync_lint.py" "$PROJECT_DIR" S001 --fail-under 85
python "$SKILL_DIR/scripts/beat_asset_coverage_lint.py" "$PROJECT_DIR" S001 --fail-under 85
python "$SKILL_DIR/scripts/beat_timeline_lint.py" "$PROJECT_DIR" --fail-under 80
python "$SKILL_DIR/scripts/director_quality_lint.py" "$PROJECT_DIR" --fail-under 78
python "$SKILL_DIR/scripts/test_composition_preview.py" "$PROJECT_DIR" --segment S001 --no-server
python "$SKILL_DIR/scripts/aesthetic_score.py" "$PROJECT_DIR" --fail-under 72
python "$SKILL_DIR/scripts/audio_score.py" "$PROJECT_DIR" --fail-under 72
```

Director QC must catch aesthetic failures, not only missing fields: PPT-like shots, SVG overuse, empty/plain backgrounds, text-only frames, no icons/charts/support actors, no real-world texture, unbound keywords, screenshots that do not guide attention, flat whole-sentence text, flower text that vanishes without a director reason, decorative text that hides proof, constant density, transition hard cuts with no anchor, preset calls with no semantic purpose, Review Studio seek-contract failures, GSAP target warnings, and emotion beats overloaded with evidence.

Load `references/director-quality-review.md` when diagnosing or revising.

## Revision Rule

Fix the earliest responsible artifact:

- wrong fact -> `research/claim_ledger.csv`, `source_cards.jsonl`, `voiceover.md`
- wrong visual strategy -> `narration_beats.csv`, `visual_sync_plan.csv`
- weak or generic external material -> `asset_selection_report.json`, `asset_manifest.csv`
- weak HyperFrames-native material -> `text_manifest.json`, `visual_sync_plan.csv`, `beat_timeline.json`, segment code
- flat text -> `text_manifest.json`, `beat_timeline.json`, segment code
- chaotic or late animation -> `beat_timeline.json`, `audio_cue_sheet.json`, segment code
- poor pacing -> `prosody_plan.csv`, `vo_timing.json`, `rhythm_map.json`
- ugly frame -> `art_direction.md`, `tokens.json`, `shotlist.json`

Never overwrite approved or locked artifacts without creating a versioned sibling or explicitly updating stage state.
