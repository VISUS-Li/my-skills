---
name: video-producer
description: Produce complete, reviewable videos from a brief, source material, script, narration, or music using one Remotion timeline and one video-plan.json runtime contract. Use for research-backed scripting, narration timing, scene direction, captions, SFX/BGM, mixed visual media, local scene repair, preview QA, and final MP4 rendering.
---

# Video Producer

Own the work from brief to final render. Use Remotion as the only final
timeline and `video-plan.json` as its only runtime truth.

## Core rules

1. Keep `script.md` human-readable and keep all executable timing in one
   `video-plan.json`.
2. Choose one timing owner per project: measured voice, music beats, or a
   fixed duration.
3. Convert seconds to frames only inside Remotion.
4. Let external capabilities produce bounded scenes, effects, or assets.
   Return every result to the Remotion master.
5. Render deterministically. Drive motion from frames; do not use wall-clock
   animation, built-in randomness, or render-time network requests.
6. Keep ordinary captions in the master caption track. Do not repeat the same
   line as scene text unless it serves a distinct visual purpose.
7. Repair a scene, cue, or asset locally when possible. Do not regenerate the
   whole video for a local defect.
8. Inspect stills and previews visually before final rendering.

## Workflow

1. Confirm the audience, platform, aspect ratio, target duration, available
   evidence, narration source, and delivery format. Make reasonable defaults
   when these do not materially change the result.
2. Research only when the subject requires factual support. Read
   `references/deep-research-and-script.md` for research and source locking.
   For narrative analysis, also read `references/narrative-depth-copy.md` and
   `references/storyteller-fan-craft.md`; sample only the corpus entries
   needed for the current script.
3. Write or revise `script.md`. Split narration into semantic beats: a claim,
   fact, turn, contrast, example, reaction, or conclusion.
4. Initialize an isolated project:

   ```powershell
   python scripts/init_project.py --name "<name>" --output "<new-directory>"
   ```

5. Read `references/video-plan.md`. Author scenes and media references in the
   generated `video-plan.json`.
6. For voice-led work, generate or place voice files, then run:

   ```powershell
   python scripts/measure_voice.py "<project>"
   python scripts/compile_video_plan.py "<project>"
   python scripts/validate_video_plan.py "<project>\video-plan.json" --check-assets
   ```

   Re-run these commands after replacing any voice beat. Do not hand-update a
   second timeline.
7. Use the built-in Remotion scenes first. Read
   `references/renderer-selection.md` only when a shot needs a specialized
   asset or effect. Preserve a simpler native Remotion fallback.
8. Add captions, visible-action SFX, and restrained BGM in the plan. Bind
   scene-local actions to local seconds or known word times.
9. Validate and review:

   ```powershell
   Push-Location "<project>"
   npm ci
   npm run typecheck
   npm run qa:still
   npm run render:preview
   npm run qa:contact-sheet
   Pop-Location
   ```

10. Inspect the stills, contact sheet, and preview for safe areas, fonts, scene coverage,
    media fit, alpha, captions, transitions, and audio balance. Fix only the
    failing scope, then run `npm run render`.

## Scene direction

Give each scene one primary attention target. Change scenes when the visual
owner, medium, evidence type, location, or argument phase changes. Do not cut
on a mechanical interval.

Use a global base theme for typography, captions, safe areas, and accent
color. Allow scenes and imported media to keep a local look when a motivated
transition, sound bridge, or shared color keeps the whole coherent.

Use the included scene wrappers for hook, talk, list, compare, timeline,
ordinary MP4 B-roll, transparent PNG, and PNG sequences. Add a new component
and local prop validation for a genuinely new high-frequency scene; do not
build a registry platform.

## Reference routing

- Runtime plan, timing, scene shapes, and commands:
  `references/video-plan.md`
- Research and source locking:
  `references/deep-research-and-script.md`
- Narrative voice:
  `references/narrative-depth-copy.md`
- Storytelling craft and selective corpus sampling:
  `references/storyteller-fan-craft.md`
- Visual style analysis:
  `references/style-dna.md`
- Shot ideas only, translated into plan scenes:
  `references/shot-grammar.md`
- Specialized renderer and asset routing:
  `references/renderer-selection.md`
- Audio and cue direction:
  `references/audio-sync-grammar.md`
- Review heuristics:
  `references/review-rubric.md`

Treat the old schemas, scripts, Review Studio, and `examples/legacy/` as
migration references only. Do not make them runtime dependencies for a new
project.
