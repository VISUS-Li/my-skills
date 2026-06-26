# Stage Contracts

Use these contracts so every intermediate output is reviewable, editable, and resumable.

## Stage Status Values

- `draft`: generated but not ready for user review.
- `review`: ready for user/editor review.
- `approved`: approved for downstream use.
- `locked`: do not edit without explicit instruction.
- `needs-revision`: user or QC rejected this stage.
- `rendered`: media file produced successfully.
- `failed`: attempted but blocked by errors or missing inputs.

## Required Artifacts by Stage

| Stage | Required artifacts | Review question |
|---|---|---|
| plan | `script/creative_brief.md`, `.video/video.json` | Is the goal, audience, duration, format, angle, and emotional promise correct? |
| ingest | `research/transcript.*`, `research/input_inventory.md` | Is the input correctly captured and usable? |
| research | `research/source_cards.jsonl`, `research/claim_ledger.csv`, `research/research_brief.md` | Are the sources and claims credible enough? |
| script | `script/outline.md`, `script/voiceover.md`, `script/on_screen_text.md` | Does the story sound like a video, not an essay? |
| art-direction | `design/art_direction.md`, `design/visual_moodboard.json` | Does the video have a clear world, mood, palette, and visual metaphor? |
| storyboard | `script/storyboard.json` | Are timings, visuals, segment engines, visual metaphors, assets, and transitions right? |
| shot-design | `script/shotlist.json` | Does each segment have shot size, camera move, depth, composition, and edit intent? |
| design | `design/design.md`, `design/tokens.json` | Are color, type, layout, safe area, and motion rules implementable? |
| assets | `assets/asset_manifest.csv` | Are icons/images/B-roll/textures/SFX planned and rights recorded? |
| segment | `segments/<id>/render.mp4`, `segments/<id>/segment_report.md` | Does this segment communicate clearly and look rich enough? |
| assemble | `edit/timeline.json`, `edit/assembly_command.sh`, `exports/final*.mp4` | Does the whole video flow and sound right? |
| aesthetic-review | `edit/aesthetic_report.md` | Is the video visually rich enough to avoid empty/PPT-like output? |
| qc | `edit/qc_report.md` | Are facts, rights, captions, audio, visuals, and safe areas acceptable? |
| publish | `exports/publish_pack.md`, `exports/cover_brief.md` | Is the package ready for the target platforms? |

## Versioning Rule

When changing a reviewed artifact, create a numbered version:

- `script/voiceover.md` -> `script/voiceover.v002.md`
- `script/storyboard.json` -> `script/storyboard.v002.json`
- `script/shotlist.json` -> `script/shotlist.v002.json`
- `design/art_direction.md` -> `design/art_direction.v002.md`
- `design/design.md` -> `design/design.v002.md`

Then update `.video/state.json` only after the user/editor accepts the newer version.

## Dependency Impact

Use this downstream impact map when revising:

- Change research -> update script, storyboard, shot-design, assets, affected segments, assembly, publish.
- Change voiceover -> update storyboard timing, shotlist, captions, segment durations, audio mix, assembly.
- Change art direction -> update design tokens, asset manifest, all visual segments, snapshots, thumbnails.
- Change storyboard -> update shotlist, affected segments, timeline, captions, assembly.
- Change shotlist -> update affected segments, timeline, aesthetic review.
- Change asset manifest -> update affected segments, rights QC, final export.
- Change one segment -> update timeline and final export only.
- Change publish copy -> no video rebuild unless cover/title style affects visuals.
