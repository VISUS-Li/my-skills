---
name: video-producer
description: "fact-locked, director-level video production workflow for turning ideas, articles, source documents, podcasts, local/reference videos, research briefs, or raw footage into publishable videos. use when the user needs source-grounded scriptwriting with claim ledgers and citations, chinese/youtube/bilibili/douyin explainer scripts, 小白debug/hyperframes-style visual analysis, phrase-level storyboard, sub-second animation timeline, IndexTTS2 voice clone/TTS, VO-measured timing (5 chars/sec), layered game-like composition, AI/SVG/icon asset generation, motion-life GSAP choreography, asset choreography, audio/sfx/music cue binding, remotion/motion-canvas/hyperframes segment prompts, aesthetic qc, anti-ppt density checks, and final assembly/publish packs."
---

# Video Producer

Compatibility: requires file access and a shell for bundled scripts. Recommended runtime tools are ffmpeg, node 22+, and HyperFrames/Remotion/Motion Canvas when rendering. Optional tools are web search, ASR/whisper, yt-dlp, image generation, TTS, SFX/music generation or libraries, and manual editor finishing.

## Operating principle

Act as a **fact-locked director compiler**, not a generic video prompt writer.

Never jump from `idea/script -> visual description -> render` for serious videos. Use the enforced path:

`source cards -> claim ledger -> colloquial retention script -> narration beats -> director event graph -> sub-second beat timeline -> asset actor choreography -> event-bound audio cues -> segment prompt/code -> qc`

Treat aesthetics, motion, sound, and source accuracy as required deliverables. A good result is not only visually rich; it is also factually traceable, phrase-synced, and executable.

## Non-negotiable gates

- For factual videos, create `research/source_cards.jsonl`, `research/claim_ledger.csv`, and `research/factcheck_report.md` before final script approval.
- Do not let a source-backed sentence enter `script/voiceover.md` unless it has a `claim_id` such as `[C012]` and a claim ledger row.
- Preserve qualifiers from sources: who, where, when, scope, draft/alleged/reported status, “as of” timing, nationality/location limits, and exceptions. Do not generalize a scoped source into a universal claim.
- For dense explainers, compile every narration phrase into timed events. One sentence should usually create 2-8 micro-events, not one static card.
- Do not render a segment until `script/beat_timeline.json`, `script/director_event_graph.json`, and `assets/asset_choreography_manifest.csv` exist for that segment.
- **VO-first timing:** plan narration at **~5 Chinese characters per second**; after TTS, run `measure_segment_vo.py` and bind segment duration to **actual WAV**, not equal shot splits or planned seconds alone.
- **Rich segments:** each segment needs `segments/<id>/vo_timing.json`, `micro_timing.json`, ≥6 SVG/icon assets, layered composition (ambient + midground + foreground/HUD), and motion on ≥3 layers per beat. Reject static-card-only frames.
- Every important visual action must choose an event-bound SFX cue, deliberate silence, or explicit no-cue decision.
- Render exact Chinese text as programmatic text layers. Do not bake readable Chinese into generated raster images.
- **Project root:** before writing any artifact, complete **Step 0**. All paths below are relative to `PROJECT_DIR`. Never scatter video artifacts in the agent workspace root or the skill repo root.
- Do not copy a reference creator’s watermark, copyrighted assets, voice identity, exact phrasing, or branded opening/ending. Copy only structure, pacing, visual grammar, and quality bar.

## Step 0 — Project bootstrap (ALWAYS first)

**Before any other stage** — including `plan`, `research`, or a single-file edit — resolve `PROJECT_DIR` and ensure the scaffold exists. Do not hand-create individual template files when `init_video_project.py` can scaffold them.

`SKILL_DIR` = absolute path to this skill root (the directory containing `scripts/` and `SKILL.md`).

**Resolve `PROJECT_DIR`:**

- User gave a path (e.g. `Use ./videos/my-explainer` or `D:\videos\opc-ai-douyin`) → use it.
- Otherwise → `videos/<project-name>/` under the agent workspace root.
- `<project-name>`: short kebab-case slug from the video title or topic. **Not** the workspace basename or a timestamp.

**Initialize when `$PROJECT_DIR/.video/state.json` is absent:**

```bash
PROJECT_DIR="${PROJECT_DIR:-videos/<project-name>}"
mkdir -p "$(dirname "$PROJECT_DIR")"

python "$SKILL_DIR/scripts/init_video_project.py" \
  --name "<title>" \
  --root "$PROJECT_DIR" \
  --input-type <idea|article|video|...> \
  --ratio <9:16|16:9> \
  --duration <seconds> \
  [--recipe douyin-ai-explainer]

python "$SKILL_DIR/scripts/validate_project.py" "$PROJECT_DIR"
```

Recipe selection:

- Chinese AI explainer / 小白debug / Douyin-Bilibili explainer → `--recipe douyin-ai-explainer --ratio 16:9`
- Generic short-form vertical → omit `--recipe`, use `--ratio 9:16`

**When `$PROJECT_DIR/.video/state.json` already exists** (user pointed at an existing project, or `resume` mode): skip init; read state and continue from the next unapproved stage.

**Constraints:**

- Never write `research/`, `script/`, `segments/`, or other video artifacts outside `PROJECT_DIR`.
- Never run `init_video_project.py` with `--root` set to the workspace root or skill repo root.
- Every shell command that touches project files should run with `PROJECT_DIR` as cwd or pass `"$PROJECT_DIR"` as the `<project>` argument to bundled scripts — never assume `.` is the project unless cwd is already `PROJECT_DIR`.
- After init, tell the user the absolute `PROJECT_DIR` path before proceeding.

Validation (stop and report if this fails):

```bash
test -f "$PROJECT_DIR/.video/state.json" && test -f "$PROJECT_DIR/.video/video.json" && echo ok || echo missing
```

## Required project contract

After Step 0, these artifacts live under `PROJECT_DIR`. The init script scaffolds most of them; fill or refine per stage — do not recreate the tree by hand.

Core state:

- `.video/video.json` — metadata, platform, duration, ratio, style, audio goals.
- `.video/state.json` — stage status and locked/approved artifacts.

Research and facts:

- `research/source_cards.jsonl` — one source card per source.
- `research/claim_ledger.csv` — one factual claim per row with source URLs, supporting quote/context, interpretation guardrail, script sentence, risk, and verification status.
- `research/factcheck_report.md` — generated plus manual fact review.
- `research/research_brief.md` — narrative research summary and open uncertainty.

Script and director compiler:

- `script/creative_brief.md`, `script/outline.md`, `script/voiceover.md`, `script/on_screen_text.md`.
- `script/retention_curve.json` — hook/tension/proof/mechanism/twist/takeaway structure.
- `script/narration_beats.csv` — phrase-level timing, semantic action, claim IDs, emotion, retention role, visual response, source visual, and SFX intent.
- `script/director_event_graph.json` — event causality, attention flow, proof edges, and audio/style edges.
- `script/beat_timeline.json` — sub-second director timeline. Every event maps narration to visual action, asset IDs, text IDs, camera, motion, SFX cue IDs, density note, and anti-PPT reason.
- `script/text_manifest.json` — exact captions, labels, titles, and rendered text IDs.

Visual/audio design:

- `design/art_direction.md`, `design/visual_moodboard.json`, `design/design.md`, `design/tokens.json`, `design/micro_animation_palette.json`.
- `script/storyboard.json`, `script/shotlist.json`.
- `assets/asset_manifest.csv` — source, path/URL, role, rights, status.
- `assets/asset_choreography_manifest.csv` — every visible asset as an actor: role, layer, on/off time, entrance, main motion, exit, states, SFX affordance.
- `audio/audio_style_guide.md`, `audio/music_brief.md`, `audio/voice_profile.md`, `audio/tts_plan.json`, `audio/indextts2_config.json` (when using IndexTTS2).
- `segments/<id>/vo_timing.json`, `segments/<id>/micro_timing.json`, `segments/<id>/assets/*`, `segments/<id>/visual_asset_brief.json` (optional).
- `audio/audio_cue_sheet.json`, `audio/sfx_search_queries.json`, `audio/audio_mix_plan.json`, `audio/loudness_targets.json`, `audio/audio_rights_log.md`.

Execution and delivery:

- `segments/<id>/brief.md`, `segments/<id>/styleframe.md`, `segments/<id>/.hyperframes/expanded-prompt.md` or equivalent render code.
- `edit/timeline.json`, `edit/captions.srt`, `edit/qc_report.md`, `edit/aesthetic_report.md`, `edit/audio_qc_report.md`.
- `exports/publish_pack.md` and final video files.

## Workflow modes

Select the smallest mode that satisfies the request:

1. `plan` — create project plan and open questions from an idea.
2. `ingest` — organize transcripts, notes, source docs, footage, and media paths.
3. `reference-analysis` — analyze a provided reference video. Run `scripts/analyze_reference_video.py <video> --out analysis/reference_video` when feasible, inspect contact sheets, then fill style DNA.
4. `style-match` — convert style DNA into art direction, tokens, storyboard primitives, motion grammar, audio cue grammar, and QC gates.
5. `research` — create source cards and research brief.
6. `fact-lock` — create/validate `claim_ledger.csv`; run `scripts/script_claim_lint.py <project> --fail-under 85`.
7. `narrative-script` — write a source-grounded, colloquial, retention-focused script. Use claim IDs inline and reference links for editor checking.
8. `script` — create outline, voiceover, on-screen text, text manifest, and narration beats.
9. `art-direction` — create visual language: palette, type, layout, composition, material/icon/SVG strategy.
10. `storyboard` — design segment timings, metaphors, frame composition, shot intent, and asset needs.
11. `beat-design` — create phrase-level `narration_beats.csv`.
12. `director-compiler` — run `scripts/director_compiler.py <project> --overwrite` to scaffold micro-events, event graph, asset choreography, and cue candidates; then edit by taste.
13. `asset-choreography` — refine asset actor behavior and frame density.
14. `shot-design` — create or refresh `script/shotlist.json`; use `scripts/storyboard_to_shotlist.py` for a draft.
15. `sound-design` — create event-bound SFX/music/TTS/mix artifacts. **IndexTTS2:** load `references/indextts2-voice-protocol.md`; batch via `scripts/indextts2_generate.py`; measure via `scripts/measure_segment_vo.py`.
16. `assets` / `audio-assets` — source/generate/select visual/audio assets and log rights.
17. `segment` — create one renderable segment with HyperFrames, Remotion, Motion Canvas, Manim, FFmpeg, or an editor. **Required pipeline:** measure VO → build micro timing → generate layered assets → build beat-synced HTML → `segment_timing_lint.py` → render with embedded VO.
18. `audio-mix` — run or adapt `scripts/ffmpeg_audio_mix.py` when local files exist.
19. `assemble` — build `edit/timeline.json`, captions, concat/mix scripts, and draft export.
20. `aesthetic-review` — run `scripts/aesthetic_score.py <project> --fail-under 72`.
21. `qc` — run validation, fact, beat, style, audio, rights, accessibility, and caption checks.
22. `publish` — create title options, cover text, description, hashtags, chapters, and cutdown ideas.
23. `revise` — modify the smallest upstream artifact and list downstream rebuild impact.
24. `resume` — set `PROJECT_DIR` to the existing project (Step 0 skip-init path); inspect `.video/state.json` and continue from the next unapproved stage.

All workflow modes assume Step 0 is complete. Pass `"$PROJECT_DIR"` wherever a command shows `<project>`.

Post-init validators (run when the relevant stage starts, not only at the end):

```bash
python "$SKILL_DIR/scripts/validate_project.py" "$PROJECT_DIR"
python "$SKILL_DIR/scripts/script_claim_lint.py" "$PROJECT_DIR" --fail-under 85
```

## Fact-linked script protocol

Load `references/fact-linked-script-system.md` and `references/retention-storytelling-and-voice.md` when the topic is factual or the user asks for scriptwriting.

Write scripts in this order:

1. Build `source_cards.jsonl` from primary/high-quality sources where possible.
2. Build `claim_ledger.csv` before final voiceover. Include source URLs, supporting quote/context, and interpretation guardrail.
3. Draft `script/outline.md` with hook, twist, proof, mechanism, stakes, nuance, and takeaway.
4. Draft `script/voiceover.md` in spoken style with `[Cxxx]` tags on factual claims and `[OPINION]` markers on analysis.
5. Add a references table that maps claim IDs to source link text for editor verification.
6. Run `scripts/script_claim_lint.py <project> --fail-under 85`.
7. Manually re-read high-risk sources before beat compilation.

Style target for Chinese scripts:

- Open with an immediately visible failure, contradiction, surprising detail, or misread correction.
- Use plain spoken Chinese; avoid corporate/documentary stiffness.
- Add judgment and drama from verified structure, not fabricated facts.
- Explain fresh context, incentives, timeline, and “很多人没注意到的限定词”.
- Do not copy any creator’s branded greeting or catchphrase.

## Director compiler protocol

Load `references/director-compiler-os.md`, `references/director-micro-timeline-protocol.md`, `references/asset-choreography-and-frame-density.md`, `references/voice-synced-animation-design.md`, `references/vo-sync-timing-protocol.md`, `references/motion-life-playbook.md`, `references/layered-composition-depth.md`, `references/visual-asset-generation.md`, and `references/hyperframes-director-implementation.md` when the user wants richer animation, 小白debug/HyperFrames style, not-PPT output, or precise phrase/audio sync.

Required process:

1. Split voiceover into `script/narration_beats.csv`. Each phrase should have `start_sec`, `end_sec`, `semantic_action`, `claim_ids`, `retention_role`, `visual_response_required`, `text_ids`, `sfx_intent`, and `source_visual`.
2. Run `scripts/director_compiler.py <project> --overwrite` to create a dense starting timeline.
3. Edit the generated `script/beat_timeline.json` creatively. Replace generic actions with concrete actions: scan, stamp, snap, morph, draw, split, pulse, flip, connect, type, count, shake, reveal.
4. Edit `assets/asset_choreography_manifest.csv` so every asset behaves like an actor.
5. Edit `audio/audio_cue_sheet.json` so cue IDs align with the beat timeline.
6. Run `scripts/beat_timeline_lint.py <project> --fail-under 80`.

Density rules:

- No normal frame should hold unchanged for more than 1.5 seconds.
- Every 0.3-1.2 seconds should have an attention, object, text, camera, background, or audio change.
- Every 5 seconds should contain a foreground event, a midground/object action, and a background/depth or camera change.
- A segment is empty if meaningful visual content occupies less than about 28% of the frame for over 1.5 seconds, unless documented as deliberate silence/drop.

## 小白debug / Douyin AI explainer recipe

Load `references/xiaobai-debug-style-dna.md`, `references/douyin-ai-explainer-style.md`, `references/programmatic-chinese-infographics.md`, and `references/tool-routing-for-ai-explainers.md` when the user references 小白debug, 抖音/B站 AI 科普, HyperFrames explainers, coding/tutorial explainers, or light-grid vector scenes.

Default style:

- 16:9 light-grid teaching canvas mixed with real UI/code/browser/terminal proof shots.
- Programmatic Chinese subtitles in bottom pill; short labels and badges.
- Rounded SVG/card/icon style, simple mascot/robot optional, clear arrows and source cards.
- UI proof layer: settings panels, browser docs, code windows, terminal commands, highlight boxes, red arrows.
- Explanation layer: machine/pipeline/source-card/card-stack/comparison-split/error-stamp/success-badge.
- No single screenshot or card talked over for 10 seconds. Add highlight sweeps, cursor actions, punch-ins, callouts, crop changes, or diagram cutaways.

Useful transparent/vector assets:

- `terminal_panel`, `vscode_window`, `browser_window`, `settings_panel`, `file_tree`, `code_card`
- `red_arrow`, `yellow_highlight_box`, `scan_line`, `cursor_pointer`
- `error_stamp`, `success_badge`, `warning_chip`, `question_card`
- `document_card`, `source_card`, `api_card`, `skill_card`, `notebook_card`
- `robot_mascot`, `gear_module`, `pipe_arrow`, `switch_toggle`, `progress_bar`

For this recipe, also run:

```bash
scripts/douyin_ai_explainer_score.py <project> --fail-under 78
```

## Reference-video protocol

When a reference video is provided:

1. Run `scripts/analyze_reference_video.py <reference-video> --out analysis/reference_video` when runtime allows.
2. Inspect `key_contact.jpg`, `contact_10s.jpg`, and `reference_metrics.json`. Use measurements as evidence, not a substitute for taste.
3. Fill `analysis/reference_video/style_dna.md` with narrative, visual, motion, audio, and must-copy/must-avoid rules.
4. Copy those constraints into `design/art_direction.md`, `design/tokens.json`, `script/storyboard.json`, `script/shotlist.json`, `script/beat_timeline.json`, `assets/asset_choreography_manifest.csv`, and `audio/audio_cue_sheet.json`.
5. Add a style-specific QC note. A polished video that misses the reference grammar fails.

## IndexTTS2 voice protocol

Load `references/indextts2-voice-protocol.md` when the user has IndexTTS2 WebUI or asks for voice clone / reference-audio TTS.

Workflow:

```bash
# 1. Configure audio/indextts2_config.json (base_url, ref wav)
python scripts/indextts2_generate.py <project> --segment S001 --concat
python scripts/measure_segment_vo.py <project> S001
python scripts/build_micro_timing.py <project> S001
python scripts/segment_timing_lint.py <project> S001
```

Rules:

- Reference audio: 5–10s clean speech, no BGM; validate RIFF before batch.
- Segment emotion vectors live in `indextts2_config.json`; default calm explainer tone.
- **Never** set HyperFrames clip duration from `shotlist.json` alone — use `vo_timing.json` total.
- Target **4–6 cps** per beat; flag outside band in timing lint.

## VO sync & motion-life protocol

Load `references/vo-sync-timing-protocol.md` and `references/motion-life-playbook.md`.

Rules:

- Plan beats at **5 汉字/秒**; after TTS, **re-time everything** from measured WAV.
- Each beat clip duration = `vo_timing.beats[].duration_sec` (tolerance ≤ 0.05s).
- Schedule GSAP from `micro_timing.json` at absolute `t` — not only clip starts.
- Per beat: ≥4 micro-events, ≥3 moving layers, different entrance patterns.
- Continuous ambient motion on track 0 (grid drift, orbs, scan line, slow camera push).
- Embed segment VO WAV in composition; visual times must match same `vo_timing.json`.

## Layered composition & asset generation

Load `references/layered-composition-depth.md` and `references/visual-asset-generation.md`.

Before segment render:

1. Search topic for visual metaphors, UI patterns, game-HUD references (document in `design/art_direction.md`).
2. Create `segments/<id>/assets/` with ≥6 SVG icons + 1–2 decorative PNG plates (transparent where possible).
3. Use image models for **non-text** plates only; all Chinese via programmatic layers.
4. Stack layers with z-index, overlap, parallax, drop shadows — aim for game-like depth, not flat PPT.
5. Optional: `segments/<id>/visual_asset_brief.json` from template.

## Audio protocol

Load `references/sound-design-system.md`, `references/audio-cue-grammar.md`, `references/music-tts-voiceover.md`, `references/indextts2-voice-protocol.md`, `references/audio-assets-rights.md`, `references/mixing-qc.md`, and `references/sound-style-recipes.md` when the task mentions sound, SFX, music, BGM, TTS, voice, pacing, or “不带感”.

Rules:

- Voice clarity first. Music and SFX must duck under speech.
- Every important cue must anchor to `beat_timeline.json`; decorative whooshes without a beat are not allowed.
- Good cues for this style: UI click, card snap, stamp hit, error buzz, data tick, machine hum, terminal key, toggle tick, success chime, silence/drop.
- Log rights in `audio/audio_rights_log.md` and `assets/asset_manifest.csv` before final use.
- Run `scripts/audio_score.py <project> --fail-under 72` before final assembly.

## Segment / HyperFrames protocol

For each segment:

1. Read project art direction, tokens, storyboard, shotlist, text manifest, beat timeline, event graph, asset choreography, cue sheet, **`vo_timing.json`**, **`micro_timing.json`**.
2. Generate assets per `references/visual-asset-generation.md`; write `segments/<id>/assets/*`.
3. Write `segments/<id>/brief.md`, `segments/<id>/styleframe.md`, and `segments/<id>/.hyperframes/expanded-prompt.md` or equivalent render prompt/code.
4. Build `segments/<id>/index.html` (or HyperFrames composition) with:
   - `data-duration` = `vo_timing.total_sec`
   - One beat container per narration beat, sized to actual VO duration
   - GSAP labels at beat starts; micro-events at `micro_timing.t`
   - Embedded `<audio src="<id>_vo.wav">` cut from beat WAVs
   - Layer stack: ambient / midground / foreground / HUD (see `layered-composition-depth.md`)
5. Run `scripts/segment_timing_lint.py <project> <id>` before render.
6. Build layout first, then animation. Do not hide weak composition behind transitions.
7. Use SVG/HTML/Canvas/component text for exact Chinese.
8. After render, update `segments/<id>/segment_report.md` with CPS per beat, asset count, layer notes, and sync verification.

## Quality gates

Before final rendering or delivery, run the relevant commands:

```bash
scripts/validate_project.py <project>
scripts/script_claim_lint.py <project> --fail-under 85
scripts/beat_timeline_lint.py <project> --fail-under 80
scripts/aesthetic_score.py <project> --fail-under 72
scripts/audio_score.py <project> --fail-under 72
scripts/douyin_ai_explainer_score.py <project> --fail-under 78   # when using this recipe
python scripts/segment_timing_lint.py <project> S001             # per segment before render
```

If a score fails, revise the earliest upstream artifact instead of patching the final render. Use `scripts/dependency_report.py <changed_path>` to list downstream impact.

## Review Studio & human gates

Load `references/review-studio-plan.md` when the user wants per-stage or per-asset approval before continuing, a local web UI to review beats/assets/renders, or a rejected-asset → agent regen workflow.

**Architecture:** one Review Studio codebase in the skill repo serves **all** video projects. Each project only stores data under `.video/`, `script/`, `segments/`, etc. Do **not** copy `review-studio/` into project directories.

**Quick start:**

```bash
pip install -r review-studio/requirements.txt

# Multi-project: set workspace, switch projects in the browser (no restart)
python review-studio/server/main.py --workspace D:\videos --port 8787

# Workspace + default project
python review-studio/server/main.py --workspace C:\Users\11839 --project c:\Users\11839\opc-ai-douyin-3min

# Windows helper
.\review-studio\start.ps1 -Workspace D:\videos
```

Open http://127.0.0.1:8787 — use **浏览…** to pick workspace/project folders, **扫描** to discover projects, dropdown to switch.

User guide: `review-studio/README.md`

**CLI gates (any project path):**

```bash
python scripts/validate_gates.py <project>
python scripts/review_sync.py <project>
python scripts/regen_dispatch.py <project> --dry-run
python scripts/test_review_studio.py
```

**Review Studio extended tabs:** Script Lab, Audio Lab (IndexTTS + alignment chain), Stage Detail (artifact editor), Timeline Editor (manual timing), Jobs panel. See `review-studio/README.md`.

## Checkpoint behavior

Default to checkpoint mode: complete Step 0 first, then create or update one stage under `PROJECT_DIR`, write artifacts, run the applicable validators, summarize changes, and ask for review. Use autopilot only when the user explicitly asks to continue through all stages.

Never overwrite `approved` or `locked` artifacts. Create a versioned sibling such as `voiceover.v002.md` and update state only after approval.
