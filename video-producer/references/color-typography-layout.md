# Color, Typography, Layout

Use this when creating `design/design.md`, `design/tokens.json`, thumbnails, styleframes, or HyperFrames compositions.

## Color system

Default ratio: **60/30/10**.

- 60% dominant base: background, room, paper, landscape, or main canvas.
- 30% support: cards, surfaces, secondary graphics, panels.
- 10% accent: key number, active node, CTA, contradiction, highlight.

Prefer role-based tokens over ad hoc colors:

- `background`, `surface`, `surfaceElevated`, `primary`, `secondary`, `accent`, `danger`, `success`, `text`, `mutedText`, `stroke`, `glow`.

Style recipes may override hues, but not hierarchy. A premium dark tech video can use cool blue/violet accents; a food product video can use warm red/orange/yellow; a guofeng video can use ink, rice paper, mineral green, cinnabar, gold.

## Typography

Use three levels per frame:

1. Display: key claim, hook, or CTA.
2. Support: proof, contrast label, or segment title.
3. Micro: data label, subtitle, source tag, UI annotation.

Rules:

- Keep titles under two lines.
- Keep support text under three lines.
- Use numeric/data type treatment for figures.
- For Chinese, prefer a clean modern CJK font for explainers; use calligraphic or Song-style only as accent in guofeng projects.
- Do not mix more than two font families unless the style recipe requires it.

## Layout and ratio allocation

Plan frame composition explicitly:

- 9:16 short video: reserve bottom safe area for captions; keep the main focal element in the upper/middle 70%.
- 16:9 video: use horizontal relationships: before/after, speaker + graphic, map + callout, data + conclusion.
- Talking-head overlay: subject 45%, graphics 40%, breathing space 15%.
- Data explanation: visualization 55%, headline 25%, labels/context 20%.
- Product promo: product hero 50%, benefit labels 30%, brand/CTA 20%.

## Composition patterns

Use these instead of generic centered cards:

- diagonal pipeline.
- split-screen before/after.
- bento grid with one hero tile and 2-4 support tiles.
- orbital annotations around a product/idea.
- timeline scroll with camera push.
- map/table/chart with progressive reveal.
- foreground frame + midground subject + background texture.
- vertical stack that transforms from chaos to system.

## Safe-area guidance

- 9:16: top 7%, bottom 9%, side 6% default safe area.
- Keep subtitles away from platform UI zones.
- Do not place small source text at the very bottom in mobile-first formats.
- For important CTA, use center-lower safe zone, not absolute bottom edge.
