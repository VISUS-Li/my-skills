# Reference Video Analysis Protocol

Use this when the user provides a reference video and asks to imitate, match, reproduce, analyze, deconstruct, or improve a video style.

## Required first step

Before writing scripts, storyboard, prompts, or code, create a reference analysis package:

1. Run `scripts/analyze_reference_video.py <reference-video> --out analysis/reference_video` when local shell and ffmpeg are available.
2. Inspect the generated contact sheets and JSON metrics.
3. Write `analysis/reference_video/style_dna.md` with: narrative structure, visual system, motion grammar, audio/voice profile, caption system, asset vocabulary, and must-not-do rules.
4. Convert the style DNA into project artifacts: `design/art_direction.md`, `design/tokens.json`, `script/storyboard.json`, `script/shotlist.json`, `audio/audio_style_guide.md`, and `audio/audio_cue_sheet.json`.

Do not answer with generic advice such as “make it more dynamic.” Identify concrete frame-level rules and reusable primitives.

## Style DNA checklist

Capture these fields explicitly:

- **Format**: aspect ratio, resolution, fps, duration, average shot/section length.
- **Narrative architecture**: hook, stakes, model/mechanism, proof, solution, recap, CTA.
- **Frame grammar**: background material, composition patterns, text hierarchy, focal element placement, safe areas, watermark/caption behavior.
- **Asset vocabulary**: recurring characters, machines, cards, arrows, badges, stamps, textures, screenshots, image plates, icons, charts.
- **Motion grammar**: camera moves, object entrance, line drawing, progressive reveal, stamp/hit, diagram morph, parallax, zoom, transitions.
- **Audio grammar**: voice pacing, music energy, SFX cue density, silence usage, ducking, loudness targets, caption sync.
- **Production route**: what must be programmatic, what can be generated, what requires manual review.
- **Failure modes**: what would make the imitation look cheap, off-style, unreadable, or like a slideshow.

## Non-negotiables for reference-driven work

- Lock the visual recipe before segment rendering.
- Use one recurring visual universe rather than a new style per segment.
- Convert every abstract claim into a diagram action: pipeline, machine, balance, stack, map, compare, stamp, or transformation.
- For any frame with readable Chinese, render the final text as HTML/SVG/Canvas/Remotion/Motion Canvas text, not as baked text inside an AI-generated image.
- Use image/video generation only for background plates, examples, thumbnails, and non-readable illustrations unless the text is deliberately illegible.
- Create a style-specific quality gate. Generic aesthetic scoring is insufficient for imitation.
