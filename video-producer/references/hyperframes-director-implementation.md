# HyperFrames Director Implementation

Use this when converting director plans into HyperFrames/GSAP/HTML/CSS animation.

## Required input files

Before coding a segment, read:

- `script/beat_timeline.json`
- `segments/<id>/vo_timing.json` — **authoritative clip durations**
- `segments/<id>/micro_timing.json` — scaled micro-events at absolute `t`
- `script/text_manifest.json`
- `assets/asset_choreography_manifest.csv`
- `audio/audio_cue_sheet.json`
- `design/tokens.json`
- `design/design.md`
- `script/shotlist.json` — intent only; **not** duration source after VO exists

## Build order

1. Run `measure_segment_vo.py` and `build_micro_timing.py` for the segment.
2. Generate layered assets in `segments/<id>/assets/` (SVG icons, PNG plates — see `visual-asset-generation.md`).
3. Build final styleframe first: all layers (ambient / midground / foreground / HUD), final layout, overlap and z-index, no animation.
4. Map every asset ID to a DOM/SVG/Canvas element with explicit `z-index` and layer class.
5. Write named timeline labels from `vo_timing.json` beat starts: `tl.addLabel('B001', 0)`.
6. Schedule micro-events from `micro_timing.json` at absolute `t`.
7. Implement beat actions using labels + relative offsets (`"B002+=0.2"`), not arbitrary delays or equal shot splits.
8. Set root `data-duration` to `vo_timing.total_sec`; embed segment VO WAV.
9. Attach captions and text from `text_manifest.json`, never baked into image plates.
10. Add continuous ambient motion (grid, orbs, scan line, camera push) per `motion-life-playbook.md`.
11. Add SFX placeholders or cue markers using cue IDs.
12. Run `segment_timing_lint.py`, then lint/preview/render checks.

## Expanded prompt must include a timestamp table

For each segment, the prompt must contain rows like:

| local time | narration phrase | visual action | assets | text ids | motion/easing | sfx |
|---:|---|---|---|---|---|---|
| 0.00-0.32 | “为什么中文会翻车？” | failure gallery slams in, red stamp lands | fail_cards, red_stamp | cap_001 | scale 0.92->1, exit-ease stamp | stamp_thud |

## Implementation patterns

- **Layer stack:** `#layer-ambient` (z:0), `#layer-mid` (z:10), `#layer-fg` (z:20), `#layer-hud` (z:30) — overlapping elements, parallax, drop shadows.
- Use SVG for icons, arrows, machines, labels, connectors, glyph outlines.
- Use CSS variables from `tokens.json` for all colors and spacing.
- Use transforms, masks, clip paths, stroke-dasharray, filters, and parallax layers.
- Use Canvas particles only for subtle accent effects; never for exact text.
- Use device mockups as reusable components with a `screenSlot` child.
- Use one timeline per segment, plus nested timelines for repeated cards/modules.
- **Motion-life:** vary entrances per beat; stagger cascades; speed lines at boundaries; mini mascot bob loops (see `motion-life-playbook.md`).

## Anti-PPT code rules

- Do not create a full-screen card with static text for longer than 1.8s.
- Do not use `fadeIn` as the only animation on a beat.
- Do not center all assets; compose with left/right zones, depth, and planned movement corridors.
- Do not animate every element equally; one hero action should dominate each beat.
- Use continuous objects across cuts when possible: arrow becomes pipe, card becomes output, phone becomes screenshot panel.
