# HyperFrames Director Implementation

Use this when converting director plans into HyperFrames/GSAP/HTML/CSS animation.

## Required input files

Before coding a segment, read:

- `script/beat_timeline.json`
- `script/text_manifest.json`
- `assets/asset_choreography_manifest.csv`
- `audio/audio_cue_sheet.json`
- `design/tokens.json`
- `design/design.md`
- `script/shotlist.json`

## Build order

1. Build final styleframe first: all layers, final layout, no animation.
2. Map every asset ID to a DOM/SVG/Canvas element.
3. Write named timeline labels from `beat_timeline.json`: `tl.addLabel('B012', 12.4)`.
4. Implement beat actions using labels, not arbitrary delays.
5. Attach captions and text from `text_manifest.json`, never baked into image plates.
6. Add SFX placeholders or cue markers using cue IDs.
7. Run lint/preview/render checks.

## Expanded prompt must include a timestamp table

For each segment, the prompt must contain rows like:

| local time | narration phrase | visual action | assets | text ids | motion/easing | sfx |
|---:|---|---|---|---|---|---|
| 0.00-0.32 | “为什么中文会翻车？” | failure gallery slams in, red stamp lands | fail_cards, red_stamp | cap_001 | scale 0.92->1, exit-ease stamp | stamp_thud |

## Implementation patterns

- Use SVG for icons, arrows, machines, labels, connectors, glyph outlines.
- Use CSS variables from `tokens.json` for all colors and spacing.
- Use transforms, masks, clip paths, stroke-dasharray, filters, and parallax layers.
- Use Canvas particles only for subtle accent effects; never for exact text.
- Use device mockups as reusable components with a `screenSlot` child.
- Use one timeline per segment, plus nested timelines for repeated cards/modules.

## Anti-PPT code rules

- Do not create a full-screen card with static text for longer than 1.8s.
- Do not use `fadeIn` as the only animation on a beat.
- Do not center all assets; compose with left/right zones, depth, and planned movement corridors.
- Do not animate every element equally; one hero action should dominate each beat.
- Use continuous objects across cuts when possible: arrow becomes pipe, card becomes output, phone becomes screenshot panel.
