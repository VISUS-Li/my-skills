---
name: video-producer
description: "fact-locked, director-level video production workflow for turning ideas, articles, source documents, podcasts, local/reference videos, research briefs, or raw footage into publishable videos. use when the user needs source-grounded scriptwriting with claim ledgers and citations, chinese/youtube/bilibili/douyin explainer scripts, 小白debug/hyperframes-style visual analysis, phrase-level storyboard, sub-second animation timeline, asset choreography, svg/icon/material planning, audio/sfx/music/tts cue binding, remotion/motion-canvas/hyperframes segment prompts, aesthetic qc, anti-ppt density checks, and final assembly/publish packs."
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
- Every important visual action must choose an event-bound SFX cue, deliberate silence, or explicit no-cue decision.
- Render exact Chinese text as programmatic text layers. Do not bake readable Chinese into generated raster images.
- Do not copy a reference creator’s watermark, copyrighted assets, voice identity, exact phrasing, or branded opening/ending. Copy only structure, pacing, visual grammar, and quality bar.

## Required project contract

At the start of a project, locate or create these artifacts. If missing, run or adapt `scripts/init_video_project.py`.

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
- `audio/audio_style_guide.md`, `audio/music_brief.md`, `audio/voice_profile.md`, `audio/tts_plan.json`.
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
15. `sound-design` — create event-bound SFX/music/TTS/mix artifacts.
16. `assets` / `audio-assets` — source/generate/select visual/audio assets and log rights.
17. `segment` — create one renderable segment with HyperFrames, Remotion, Motion Canvas, Manim, FFmpeg, or an editor.
18. `audio-mix` — run or adapt `scripts/ffmpeg_audio_mix.py` when local files exist.
19. `assemble` — build `edit/timeline.json`, captions, concat/mix scripts, and draft export.
20. `aesthetic-review` — run `scripts/aesthetic_score.py <project> --fail-under 72`.
21. `qc` — run validation, fact, beat, style, audio, rights, accessibility, and caption checks.
22. `publish` — create title options, cover text, description, hashtags, chapters, and cutdown ideas.
23. `revise` — modify the smallest upstream artifact and list downstream rebuild impact.
24. `resume` — inspect `.video/state.json` and continue from the next unapproved stage.

## Initialization

For a clean Chinese AI explainer / 小白debug-like project:

```bash
scripts/init_video_project.py --name "<title>" --recipe douyin-ai-explainer --ratio 16:9 --duration <seconds>
```

For generic video projects:

```bash
scripts/init_video_project.py --name "<title>" --ratio 9:16 --duration <seconds>
```

After initialization, run:

```bash
scripts/validate_project.py <project>
scripts/script_claim_lint.py <project> --fail-under 85
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

Load `references/director-compiler-os.md`, `references/director-micro-timeline-protocol.md`, `references/asset-choreography-and-frame-density.md`, `references/voice-synced-animation-design.md`, and `references/hyperframes-director-implementation.md` when the user wants richer animation, 小白debug/HyperFrames style, not-PPT output, or precise phrase/audio sync.

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

## Audio protocol

Load `references/sound-design-system.md`, `references/audio-cue-grammar.md`, `references/music-tts-voiceover.md`, `references/audio-assets-rights.md`, `references/mixing-qc.md`, and `references/sound-style-recipes.md` when the task mentions sound, SFX, music, BGM, TTS, voice, pacing, or “不带感”.

Rules:

- Voice clarity first. Music and SFX must duck under speech.
- Every important cue must anchor to `beat_timeline.json`; decorative whooshes without a beat are not allowed.
- Good cues for this style: UI click, card snap, stamp hit, error buzz, data tick, machine hum, terminal key, toggle tick, success chime, silence/drop.
- Log rights in `audio/audio_rights_log.md` and `assets/asset_manifest.csv` before final use.
- Run `scripts/audio_score.py <project> --fail-under 72` before final assembly.

## Segment / HyperFrames protocol

For each segment:

1. Read project art direction, tokens, storyboard, shotlist, text manifest, beat timeline, event graph, asset choreography, and cue sheet.
2. Write `segments/<id>/brief.md`, `segments/<id>/styleframe.md`, and `segments/<id>/.hyperframes/expanded-prompt.md` or equivalent render prompt/code.
3. The expanded prompt must include final composition, ratio allocation, exact text IDs, asset IDs, timestamped beat table, camera/parallax, easing, SFX cue IDs, and anti-PPT measures.
4. Build layout first, then animation. Do not hide weak composition behind transitions.
5. Use SVG/HTML/Canvas/component text for exact Chinese.
6. After render, update `segments/<id>/segment_report.md` with what worked, simplifications, open issues, aesthetic impact, and audio sync notes.

## Quality gates

Before final rendering or delivery, run the relevant commands:

```bash
scripts/validate_project.py <project>
scripts/script_claim_lint.py <project> --fail-under 85
scripts/beat_timeline_lint.py <project> --fail-under 80
scripts/aesthetic_score.py <project> --fail-under 72
scripts/audio_score.py <project> --fail-under 72
scripts/douyin_ai_explainer_score.py <project> --fail-under 78   # when using this recipe
```

If a score fails, revise the earliest upstream artifact instead of patching the final render. Use `scripts/dependency_report.py <changed_path>` to list downstream impact.

## Checkpoint behavior

Default to checkpoint mode: create or update one stage, write artifacts, run the applicable validators, summarize changes, and ask for review. Use autopilot only when the user explicitly asks to continue through all stages.

Never overwrite `approved` or `locked` artifacts. Create a versioned sibling such as `voiceover.v002.md` and update state only after approval.
