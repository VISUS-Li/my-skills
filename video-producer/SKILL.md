---
name: video-producer
description: "fact-locked video production workflow with default deep narrative scriptwriting: single-event or multi-point 来龙去脉, verified 秘辛, cause/incentive/conflict arcs, colloquial spoken 口播, claim ledgers, director compiler, IndexTTS2, HyperFrames/Remotion segments, and QC. Use for any 文案/口播/脚本 request — agent auto-runs depth research without user naming internal stages."
---

# Video Producer

Compatibility: requires file access and a shell for bundled scripts. Recommended runtime tools are ffmpeg, node 22+, and HyperFrames/Remotion/Motion Canvas when rendering. Optional tools are web search, ASR/whisper, yt-dlp, image generation, TTS, SFX/music generation or libraries, and manual editor finishing.

## Operating principle

Act as a **fact-locked director compiler**, not a generic video prompt writer.

Never jump from `idea/script -> visual description -> render` for serious videos. Use the enforced path:

`source cards -> claim ledger -> deep narrative map + thread ledger -> colloquial 口播 script -> narration beats -> director event graph -> sub-second beat timeline -> asset actor choreography -> event-bound audio cues -> segment prompt/code -> qc`

Treat aesthetics, motion, sound, and source accuracy as required deliverables. A good result is not only visually rich; it is also factually traceable, phrase-synced, and executable.

## Non-negotiable gates

- For factual videos, create `research/source_cards.jsonl`, `research/claim_ledger.csv`, and `research/factcheck_report.md` before final script approval.
- Do not let a source-backed sentence enter `script/voiceover.md` unless it has a `claim_id` such as `[C012]` and a claim ledger row.
- **Default script depth:** continuous **storytelling** not news ticker — each beat must **dwell** (enter/evidence/mechanism/landing) before the next; use `carry_forward` in spine; forbid 此外/据悉 hard cuts.
- Preserve qualifiers from sources: who, where, when, scope, draft/alleged/reported status, “as of” timing, nationality/location limits, and exceptions. Do not generalize a scoped source into a universal claim.
- For dense explainers, compile every narration phrase into timed events. One sentence should usually create 2-8 micro-events, not one static card.
- Do not render a segment until `script/beat_timeline.json`, `script/director_event_graph.json`, and `assets/asset_choreography_manifest.csv` exist for that segment.
- **VO-first timing:** plan narration at **~5 Chinese characters per second**; after TTS, run `measure_segment_vo.py` and bind segment duration to **actual WAV**, not equal shot splits or planned seconds alone.
- **Rich segments:** each segment needs `segments/<id>/vo_timing.json`, `micro_timing.json`, `segments/<id>/beat_asset_plan.csv`, **≥12 topic-specific SVG/icon assets**, **≥4 decorative plates**, **≥3 evidence stills** (`ref_*` / `stock_*`) in `segments/<id>/assets/ref/`, **≥1 `motion_*` real footage or screen recording**, and **≥2 `broll_*` Ken Burns** only as fill — Ken Burns alone does **not** satisfy the real-footage gate. Layered composition (ambient + midground + foreground/HUD), motion on **≥4 layers per beat**. Aim for **50–80% frame occupancy** and **≥15 choreographed motion actors** per segment. Reject static-card-only frames or beats with accidental empty zones.
- **口播-画面对齐（分层）：** ≥70% beats 在 `beat_asset_plan.csv` 中绑定 `ref_*` / `stock_*` / `motion_*` 或有效 `ref_embed` — 不必全是新闻截图。点名事件/报道 → `ref_*` + 来源卡；机制/场景 → `stock_*` / `gen_*` / `motion_*`；抽象过渡 → SVG+plate 可仅解释层。具体实体 beat 不能只有 SVG。见 `references/multimedia-asset-taxonomy.md` + `references/web-sourced-visual-assets.md`。
- **中文优先（美术资产）：** 生成、检索、描述美术资产时 **默认用中文** — 包括 image/SVG 生成 prompt、`media-use --intent`、素材库搜索词、`asset_choreography_manifest.csv` 的 `source_or_prompt`、以及 `visual_asset_brief.json` 的 `prompt` 字段。仅当素材本身必须是英文内容时保留英文（英文 UI 截图、代码窗口、品牌名、缩写、原文引用）；此时用中文描述构图与风格，英文只出现在素材本体或 overlay 文本层。
- Every important visual action must choose an event-bound SFX cue, deliberate silence, or explicit no-cue decision.
- Render exact Chinese text as programmatic text layers. Do not bake readable Chinese into generated raster images.
- **Project root:** before writing any artifact, complete **Step 0**. All paths below are relative to `PROJECT_DIR`. Never scatter video artifacts in the agent workspace root or the skill repo root.
- Do not copy a reference creator’s watermark, copyrighted assets, voice identity, exact phrasing, or branded opening/ending. Copy only structure, pacing, visual grammar, and quality bar.
## Multimedia evidence contract

Load `references/multimedia-asset-taxonomy.md` for every `assets` / `segment` stage.

**Taxonomy (mandatory prefixes):** `ref_*` traceable proof · `stock_*` related stills · `gen_*` AI UI mocks · `motion_*` real video/screen rec · `broll_*` Ken Burns on stills only.

**Beat binding:** `segments/<id>/beat_asset_plan.csv` — 4 assets + 2 motion verbs + optional `ref_embed` per beat; times from `vo_timing.json` after TTS.

**Processed embeds:** `ref/processed/*_1280x720` (full) and `*_640x360` (source_card slot); `video_types_report.json` required.

**Windows UTF-8:** never Write-tool Chinese SVG; use `rebuild_chinese.py` or Python `write_text(..., encoding='utf-8')`; run `verify_svg_utf8.py`.

**Segment gates (before render):**

```bash
python "$SKILL_DIR/scripts/measure_segment_vo.py" "$PROJECT_DIR" S001
python "$SKILL_DIR/scripts/build_micro_timing.py" "$PROJECT_DIR" S001
python "$SKILL_DIR/scripts/beat_asset_coverage_lint.py" "$PROJECT_DIR" S001 --fail-under 90
python "$SKILL_DIR/scripts/verify_svg_utf8.py" "$PROJECT_DIR/segments/S001/assets"
python "$SKILL_DIR/scripts/segment_timing_lint.py" "$PROJECT_DIR" S001 --full
```

**Assets checkpoint report:** separately count ref/stock/gen stills; `motion_*` vs `broll_*` video; beats with `ref_embed`; acquisition failures + fix commands.

- **Review Studio = human web console only:** `review-studio/` is a local FastAPI + static UI for humans to review/edit/preview. During normal video production, **do not read** `review-studio/web/*`, `review-studio/server/*`, or other Review Studio source — they are large and unrelated to artifact authoring; reading them wastes tokens. Agents interact via `PROJECT_DIR` artifacts (`.video/review_registry.jsonl`, `regen_queue.json`, `state.json`, etc.) and bundled `scripts/*.py` (`validate_gates.py`, `review_sync.py`, `regen_dispatch.py`). Load `references/review-studio-plan.md` or `review-studio/README.md` only when the user explicitly asks to **set up, run, or debug** Review Studio — not for routine script/research/segment work.

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
- `script/narrative_thread_map.json` — `story_scope`, master thread, insight layers, selective omissions, spine (**always** for scriptwriting).
- `research/thread_ledger.csv` — verified story links: entity↔entity (multi) or phase↔phase (single-event arc).
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
- `segments/<id>/vo_timing.json`, `segments/<id>/micro_timing.json`, `segments/<id>/beat_asset_plan.csv`, `segments/<id>/assets/*` (incl. `ref/processed/`, `video_types_report.json`), `segments/<id>/visual_asset_brief.json` (optional).
- `audio/audio_cue_sheet.json`, `audio/sfx_search_queries.json`, `audio/audio_mix_plan.json`, `audio/loudness_targets.json`, `audio/audio_rights_log.md`.

Execution and delivery:

- `segments/<id>/brief.md`, `segments/<id>/styleframe.md`, `segments/<id>/.hyperframes/expanded-prompt.md` or equivalent render code.
- `edit/timeline.json`, `edit/captions.srt`, `edit/qc_report.md`, `edit/aesthetic_report.md`, `edit/audio_qc_report.md`.
- `exports/publish_pack.md` and final video files.

## Workflow modes

**Auto-routing:** infer the smallest mode from the user request. Never ask “要不要跑某某阶段”. For any 文案 / 口播 / 脚本 / 深度 / 来龙去脉 request → load `references/deep-narrative-investigation.md` and produce depth artifacts automatically. Only skip depth when user **explicitly** says shallow/outline-only (`只要大纲`, `不要调研`).

Select mode:

1. `plan` — create project plan and open questions from an idea.
2. `ingest` — organize transcripts, notes, source docs, footage, and media paths.
3. `reference-analysis` — analyze a provided reference video. Run `scripts/analyze_reference_video.py <video> --out analysis/reference_video` when feasible, inspect contact sheets, then fill style DNA.
4. `style-match` — convert style DNA into art direction, tokens, storyboard primitives, motion grammar, audio cue grammar, and QC gates.
5. `research` — create source cards and research brief.
6. `fact-lock` — create/validate `claim_ledger.csv`; run `scripts/script_claim_lint.py <project> --fail-under 85`.
7. `narrative-script` — **default script deliverable:** auto deep-dive (single or multi), fill `thread_ledger.csv` + `narrative_thread_map.json`, write `outline.md` + colloquial `voiceover.md`; run `thread_depth_lint.py` + `script_claim_lint.py`.
8. `script` — split approved voiceover into `narration_beats.csv`, `text_manifest.json`, on-screen text.
9. `art-direction` — create visual language: palette, type, layout, composition, material/icon/SVG strategy.
10. `storyboard` — design segment timings, metaphors, frame composition, shot intent, and asset needs.
11. `beat-design` — create phrase-level `narration_beats.csv`.
12. `director-compiler` — run `scripts/director_compiler.py <project> --overwrite` to scaffold micro-events, event graph, asset choreography, and cue candidates; then edit by taste.
13. `asset-choreography` — refine asset actor behavior and frame density.
14. `shot-design` — create or refresh `script/shotlist.json`; use `scripts/storyboard_to_shotlist.py` for a draft.
15. `sound-design` — create event-bound SFX/music/TTS/mix artifacts. **IndexTTS2:** load `references/indextts2-voice-protocol.md`; batch via `scripts/indextts2_generate.py`; measure via `scripts/measure_segment_vo.py`.
16. `assets` — **sub-stages (strict order):** `assets-evidence` (ref + stock + motion real footage) → `assets-explain` (SVG + gen UI + plates) → `assets-motion-fallback` (Ken Burns `broll_*` only for gaps) → `assets-bind` (`beat_asset_plan.csv` + choreography rebind to `vo_timing.json`). Log `motion_type`, `embed_full`, `embed_card` in `asset_manifest.csv`. Load `references/multimedia-asset-taxonomy.md`, `references/web-sourced-visual-assets.md`, `references/visual-asset-generation.md`.
17. `audio-assets` — TTS + **mandatory** `measure_segment_vo.py` → `build_micro_timing.py` → `segment_timing_lint.py`. VO total vs storyboard planned >10% → fix script or beats before segment render.
18. `segment` — create one renderable segment with HyperFrames, Remotion, Motion Canvas, Manim, FFmpeg, or an editor. **Required pipeline:** measure VO → build micro timing → `beat_asset_coverage_lint` + `verify_svg_utf8` → build beat-synced HTML → `segment_timing_lint.py --full` → render with embedded VO.
19. `audio-mix` — run or adapt `scripts/ffmpeg_audio_mix.py` when local files exist.
20. `assemble` — build `edit/timeline.json`, captions, concat/mix scripts, and draft export.
21. `aesthetic-review` — run `scripts/aesthetic_score.py <project> --fail-under 72`.
22. `qc` — run validation, fact, beat, style, audio, rights, accessibility, and caption checks.
23. `publish` — create title options, cover text, description, hashtags, chapters, and cutdown ideas.
24. `revise` — modify the smallest upstream artifact and list downstream rebuild impact.
25. `resume` — set `PROJECT_DIR` to the existing project (Step 0 skip-init path); inspect `.video/state.json` and continue from the next unapproved stage.

All workflow modes assume Step 0 is complete. Pass `"$PROJECT_DIR"` wherever a command shows `<project>`.

Post-init validators (run when the relevant stage starts, not only at the end):

```bash
python "$SKILL_DIR/scripts/validate_project.py" "$PROJECT_DIR"
python "$SKILL_DIR/scripts/thread_depth_lint.py" "$PROJECT_DIR" --fail-under 80
python "$SKILL_DIR/scripts/script_claim_lint.py" "$PROJECT_DIR" --fail-under 85
```

## Deep narrative investigation protocol

**Default for all scriptwriting** — one event or many. Load `references/deep-narrative-investigation.md` automatically; user never names this step.

**Mandatory behavior:**

1. Set `story_scope`: `single` (one event → 前尘/博弈/转折/后果 arc) or `multi` (weave bullets into one chain).
2. Research **links** with sources — temporal (`prelude→trigger→aftermath`) or entity (`A↔B` cause/incentive/conflict). Each verified link → `thread_ledger.csv` + `claim_type=relationship`.
3. Fill `narrative_thread_map.json`: spine beats each with `dwell_layers`, `landing_line`, `carry_forward`.
4. Write `outline.md` + `voiceover.md` as **连续讲故事** — each beat: enter→evidence→mechanism→landing before next; no 新闻稿硬切（此外/据悉）.
5. Auto-run `thread_depth_lint.py` then `script_claim_lint.py` before delivering copy.

Skip only when user explicitly opts out of depth (`只要大纲`). If a link lacks evidence → `open_question`, say on camera, or cut — never invent.

## Fact-linked script protocol

Load `references/fact-linked-script-system.md` and `references/retention-storytelling-and-voice.md` when the topic is factual or the user asks for scriptwriting.

Write scripts in this order:

1. Build `source_cards.jsonl` from primary/high-quality sources where possible.
2. Build `claim_ledger.csv` before final voiceover. Include relationship rows for thread links.
3. **Always** complete `thread_ledger.csv` + `narrative_thread_map.json` (single-story or multi-weave).
4. Draft `script/outline.md` then `script/voiceover.md` — master thread first, selective omissions, 口播 texture.
5. Add references table mapping claim IDs to sources.
6. Auto-run `thread_depth_lint.py` + `script_claim_lint.py`.
7. Manually re-read high-risk sources before beat compilation.

Style target for Chinese scripts:

- Open with an immediately visible failure, contradiction, surprising detail, or misread correction.
- Use plain spoken Chinese with **research authority**: short clauses, source anchors (原文/公告/时间线), pauses before reveals — not speculative fillers like 你想啊/其实吧.
- Add judgment and drama from verified structure, not fabricated facts.
- Explain fresh context, incentives, timeline, and “很多人没注意到的限定词”.
- Do not copy any creator’s branded greeting or catchphrase.

## Director compiler protocol

Load `references/director-compiler-os.md`, `references/director-micro-timeline-protocol.md`, `references/asset-choreography-and-frame-density.md`, `references/voice-synced-animation-design.md`, `references/vo-sync-timing-protocol.md`, `references/motion-life-playbook.md`, `references/layered-composition-depth.md`, `references/multimedia-asset-taxonomy.md`, `references/visual-asset-generation.md`, `references/web-sourced-visual-assets.md`, and `references/hyperframes-director-implementation.md` when the user wants richer animation, 小白debug/HyperFrames style, not-PPT output, or precise phrase/audio sync.

Required process:

1. Split voiceover into `script/narration_beats.csv`. Each phrase should have `start_sec`, `end_sec`, `semantic_action`, `claim_ids`, `retention_role`, `visual_response_required`, `text_ids`, `sfx_intent`, and `source_visual`.
2. Run `scripts/director_compiler.py <project> --overwrite` to create a dense starting timeline.
3. Edit the generated `script/beat_timeline.json` creatively. Replace generic actions with concrete actions: scan, stamp, snap, morph, draw, split, pulse, flip, connect, type, count, shake, reveal.
4. Edit `assets/asset_choreography_manifest.csv` so every asset behaves like an actor.
5. Edit `audio/audio_cue_sheet.json` so cue IDs align with the beat timeline.
6. Run `scripts/beat_timeline_lint.py <project> --fail-under 80`.

Density rules:

- No normal frame should hold unchanged for more than 1.0 seconds.
- Every 0.3-1.2 seconds should have an attention, object, text, camera, background, or audio change.
- Every 5 seconds should contain a foreground event, a midground/object action, and a background/depth or camera change — **plus ≥5 visible assets on screen**.
- A segment is empty if meaningful visual content occupies less than about **50%** of the frame for over 1.0 seconds, unless documented as deliberate silence/drop.
- **Asset batch rule:** before segment render, list all beat-level asset needs; generate **≥12 icons + ≥4 plates** per segment in one pass.

## 小白debug / Douyin AI explainer recipe

Load `references/xiaobai-debug-style-dna.md`, `references/douyin-ai-explainer-style.md`, `references/programmatic-chinese-infographics.md`, and `references/tool-routing-for-ai-explainers.md` when the user references 小白debug, 抖音/B站 AI 科普, HyperFrames explainers, coding/tutorial explainers, or light-grid vector scenes.

Default style:

- 16:9 light-grid teaching canvas mixed with real UI/code/browser/terminal proof shots.
- Programmatic Chinese subtitles in bottom pill; short labels and badges.
- Rounded SVG/card/icon style, simple mascot/robot optional, clear arrows and source cards.
- `UI proof layer`: settings panels, browser docs, code windows, terminal commands, highlight boxes, red arrows — use **downloaded screenshots** in `assets/ref/` when showing real products/sites, not only drawn mockups.
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
- Per beat: ≥4 micro-events, ≥4 moving layers, different entrance patterns.
- Continuous ambient motion on track 0 (grid drift, orbs, scan line, slow camera push).
- Embed segment VO WAV in composition; visual times must match same `vo_timing.json`.

## Layered composition & asset generation

Load `references/layered-composition-depth.md` and `references/visual-asset-generation.md`.

Before segment render:

1. **Plan:** fill `segments/<id>/beat_asset_plan.csv` from narration + `vo_timing.json` (after TTS).
2. **Evidence pass:** ref + stock + motion (`assets-evidence`) → `ref/processed/` at 1280×720 and 640×360; write `video_types_report.json`.
3. **Explain pass:** SVG + gen UI + plates (`assets-explain`); Chinese SVG via `rebuild_chinese.py` only.
4. **Fallback:** Ken Burns `broll_*` only for beats still missing embed (`assets-motion-fallback`).
5. **Bind:** update `asset_choreography_manifest.csv`; run `beat_asset_coverage_lint.py` + `verify_svg_utf8.py`.
6. Search topic for visual metaphors — **中文 moodboard** in `design/art_direction.md`.
7. **≥12 SVG + ≥4 plates + ≥3 evidence stills + ≥1 motion_* + ≥2 broll_* fill**; each beat ≥5 visible assets moving.
8. Optional: `visual_asset_brief.json` with Chinese `prompt`, `source_url`, `motion_type`.

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
2. **Multimedia pass:** taxonomy + `beat_asset_plan.csv` per `references/multimedia-asset-taxonomy.md`; gates: `beat_asset_coverage_lint`, `verify_svg_utf8`, `video_types_report.json`.
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
scripts/thread_depth_lint.py <project> --fail-under 80
scripts/script_claim_lint.py <project> --fail-under 85
scripts/beat_timeline_lint.py <project> --fail-under 80
scripts/aesthetic_score.py <project> --fail-under 72
scripts/audio_score.py <project> --fail-under 72
scripts/douyin_ai_explainer_score.py <project> --fail-under 78   # when using this recipe
python scripts/segment_timing_lint.py <project> S001 --full
python scripts/beat_asset_coverage_lint.py <project> S001 --fail-under 90
python scripts/verify_svg_utf8.py <project>/segments/S001/assets
```

If a score fails, revise the earliest upstream artifact instead of patching the final render. Use `scripts/dependency_report.py <changed_path>` to list downstream impact.

## Review Studio & human gates

Review Studio is a **human-facing web console** (orchestrator + reviewer UI). It is **not** part of the agent authoring contract — agents should not traverse or read its implementation to “understand the workflow.”

Load `references/review-studio-plan.md` **only** when the user wants to set up Review Studio, debug the local server, or design the human approval workflow — not when writing scripts, researching, or building segments.

**Agent read boundary (token guard):**

| Read | Do not read (unless user asks to fix Review Studio itself) |
|------|--------------------------------------------------------------|
| `PROJECT_DIR/.video/*` (`state.json`, `review_registry.jsonl`, `regen_queue.json`, `studio.json`) | `review-studio/web/*` (`app.js`, `styles.css`, `timeline-editor.js`, …) |
| `PROJECT_DIR/script/`, `segments/`, `assets/`, … | `review-studio/server/*` (`main.py`, `artifacts.py`, `timing.py`, …) |
| `scripts/validate_gates.py`, `review_sync.py`, `regen_dispatch.py`, `test_review_studio.py` | Full `references/review-studio-plan.md` (800+ lines) unless human-gate setup is the task |

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

**After `assets` stage**, the summary must include (not a single opaque asset count):

1. Stills: `ref_*` / `stock_*` / `gen_*` counts with paths under `ref/processed/`
2. Video: `motion_*` real segments vs `broll_*` Ken Burns — reported separately
3. Beats: X/Y with `ref_embed` in `beat_asset_plan.csv`; list SVG-only concrete beats
4. Failures: acquisition errors (Mixkit 403, Playwright missing, etc.) + commands the user can run

Never overwrite `approved` or `locked` artifacts. Create a versioned sibling such as `voiceover.v002.md` and update state only after approval.
