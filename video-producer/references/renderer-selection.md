# Renderer Selection

Choose the renderer per shot, not per whole project. The segment spec records the choice and reason through `renderer`, `component`, and `qa_notes`.

Video Producer is the composition skill. Remotion, HyperFrames, vibe-motion, Motion Canvas, GSAP/SVG, FFmpeg, TTS, screenshot/browser/terminal tools, and future video skills are shot suppliers. Keep the global story, style, timing, and review in Video Producer; delegate only bounded slots.

## Defaults

- Remotion: main timeline, multi-scene composition, subtitles, audio, TTS alignment, screen/code/terminal scenes, React component reuse, final render.
- HyperFrames: quick HTML/CSS/GSAP scenes, UI dashboards, kinetic cards, browser-previewable layouts, reviewable first-slice scenes.
- vibe-motion: high-quality reusable motion scenes or effect slots when a matching effect exists.
- Motion Canvas: teaching diagrams, code relationship animation, SVG graph growth, algorithm flows, precise educational timing.
- GSAP/SVG: local high-freedom motion, redbox draw, arrows, keyword actors, morphs, path travel, transition glue.
- FFmpeg: contact sheet, trim, stitch, transcode, audio mix, loudness, delivery encode.
- TTS/voice tools: narration generation after `beat_plan.json`; animation timing locks only after measured voice duration.

Default first-slice stack: Remotion as assembly timeline plus zero to two delegated slots. Add HyperFrames, vibe-motion, or Motion Canvas only when that slot would be visibly stronger than a local Remotion/SVG implementation.

## Selection Rules

- If the shot is the main assembly timeline, use Remotion.
- If the shot is a fast design-heavy scene that can live as HTML, use HyperFrames.
- If the shot is a code/terminal/browser/phone proof scene, use Remotion unless the project already has a HyperFrames component.
- If the shot teaches a diagram or graph step-by-step, use Motion Canvas or SVG/GSAP.
- If an external skill can render a stronger specific motion scene, call that skill and compose the result.
- If final outputs need format work, use FFmpeg instead of renderer-specific encoding hacks.

Avoid renderer soup. A first slice with five renderers usually means the plan is unfocused. Prefer one primary renderer and one specialized slot, then expand after review proves the style.

## Delegation Contract

Use `delegation` on a shot when another skill or renderer owns a bounded scene, effect, or asset. The contract must be small enough that the receiving skill can execute without rereading the whole project.

Required intent:

- `skill`: the skill/tool to invoke, such as `hyperframes`, `remotion-best-practices`, `vibe-director`, `motion-graphics`, `remotion-3d-ticker`, `svg-assembly-animator`, or a project-local renderer.
- `purpose`: one sentence describing the visual job, not the whole video.
- `input_artifacts`: only the files/assets the slot needs.
- `output_artifacts`: the files Video Producer expects back, usually MP4/WebM/PNG/SVG/HTML.
- `acceptance`: visible criteria: duration, readability, style guard, seekability, alpha, or audio sync.

Do not delegate vague instructions like "make this cool". Delegate a timed shot: style preset, shot recipe, start/end, visual owner, actions, audio cues, and output path.

For small shots, skip delegation and implement locally. Delegation is worth it only when it buys one of: better existing effect quality, faster preview, precise diagram control, reusable external component, or a renderer-specific capability.

## Style Guard

Different tools can drift into different visual worlds. Before accepting a delegated output, check:

- same style preset palette/background vocabulary;
- same text strategy and caption scale;
- compatible easing and transition density;
- no new decorative language that was not in the first-slice style DNA;
- proof assets remain readable after composition;
- duration and first/last frame support the neighboring transition.

## Input / Output Contract

Renderer input:

- `outputs/beat_plan.json`
- `outputs/segment_spec.json`
- `outputs/audio_cue_sheet.json`
- referenced assets under `outputs/assets/` or project-local asset folders

Renderer output for first slice:

- `outputs/review/preview.mp4`
- optional still frames under `outputs/review/frames/`
- logs or notes summarized into `outputs/review/metrics.json`
- delegated slot evidence summarized in `outputs/review/execution_trace.json`

## QA By Renderer

- Remotion: check subtitles do not cover proof, audio lines align, and components are responsive to target ratio.
- HyperFrames: verify seekable timeline or deterministic playback, no blank iframe/canvas, text fits on mobile and desktop.
- Motion Canvas/SVG: verify labels are readable, path direction matches narration, and concepts build step-by-step.
- FFmpeg: verify duration, codec, loudness, and contact sheet generation.
- Delegated skill slot: verify output exists, starts/ends cleanly, matches style DNA, and can be composed by the main timeline without hiding subtitles, proof, or SFX.
