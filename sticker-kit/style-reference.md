# Style reference & prompt templates

**Preset catalog (switch styles here):** [styles.md](styles.md)  
Default style id: **`cozy-scrapbook`**. For any job, resolve `style_id` first, then paste that preset’s Master + Negatives below as `[MASTER …]` / `[NEGATIVES]`.

## Master style — screens / stickers

Do **not** hard-code cozy-only wording when another preset is active.  
Copy the active blocks from [styles.md](styles.md).

Fallback if styles.md is unavailable — cozy default:

**Screens**
```text
Mobile app UI, WeChat mini-program, warm cream paper-textured background #FDF8F0,
cozy kitchen scrapbook aesthetic, hand-drawn doodle stickers with thick dark outlines
and white sticker borders, soft sage green and tomato red accents, pill-shaped CTA buttons,
highly rounded cards, playful handwritten Chinese titles, soft diffused shadows,
generous whitespace, friendly lifestyle utility UI
```

**Stickers**
```text
Die-cut sticker, hand-drawn cozy scrapbook doodle, thick dark brown outline,
thick white sticker border, soft contact drop shadow, matte warm colors,
sage green and tomato red accents, cute slightly chunky shapes, flat 2D illustration,
consistent stroke weight
```

**Negatives (cozy fallback)**
```text
no dark mode, no neon glow, no glassmorphism, no cyberpunk, no hard black neo-brutalism,
no purple gradient, no photorealistic photos, no 3D metal render, no multi-character crowd,
no cream paper full-bleed scene behind stickers when chroma key is required
```

## Anchor prompt (Mode D1)

```text
Single character/object sticker ONLY, centered, neutral resting pose, full subject visible,
PURE solid chroma key green background exactly #00FF00, no gradients, no floor, no scene,
Style preset: [STYLE_ID],
[SUBJECT DESCRIPTION with every part named],
Topology lock: [TOPOLOGY SENTENCE — exact part counts, SEPARATE tools vs body mounts],
Lookalike parts must be visually distinct (different color/thickness/end-cap),
[MASTER STICKER STYLE from styles.md], white sticker border unless preset forbids,
soft shadow under subject only if preset allows,
[NEGATIVES from styles.md], do not fuse separate parts into one silhouette
```

## Sprite row prompt (Mode D2 light — engineered C)

Only when no lookalike props. Prefer keyframes otherwise.

```text
Horizontal sprite animation strip, exactly [N] equal frames in ONE row,
large pure #00FF00 gaps between cells, each cell same size,
SAME exact subject as the reference image (identity lock: colors, outline, proportions),
Style preset: [STYLE_ID] — keep style identical on EVERY cell,
Topology lock: [TOPOLOGY SENTENCE] — obey on EVERY cell, never merge/swap parts,
ONLY the pose changes across frames for action: [ACTION STAGES listed 1..N],
no camera move, no zoom drift, no morphing identity, sticker style,
PURE #00FF00 background everywhere outside stickers,
[MASTER STICKER STYLE], [NEGATIVES]
```

Pass `reference_image_paths=[anchor]`.

## Keyframe prompt (Mode D2 medium — preferred)

```text
Single sticker frame [K] of [N], micro-stage: [POSE DELTA ONLY vs previous],
Style preset: [STYLE_ID] — identical rendering to anchor,
Topology lock: [TOPOLOGY SENTENCE],
Color lock INVARIANT (do not recolor): [PART=COLOR, ...],
FREE channels ONLY: [pose / limb angles / weapon arc / hop] — everything else unchanged,
Part inventory: [MUST ALWAYS EXIST IDS], never add/remove/merge parts, never recolor parts,
SINGLE CRISP POSE ONLY — one body, one silhouette; NO motion blur, NO afterimages, NO ghost trail, NO multi-exposure, NO onion-skin,
same exact subject as reference images (anchor + previous frame), same scale, same outline thickness,
same camera framing, PURE solid #00FF00 background, centered, white sticker border,
[MASTER STICKER STYLE], [NEGATIVES]
```

Pass `reference_image_paths=[anchor]` then `[anchor, previous_accepted]` from frame 2.

## I2V notes (Mode D2 hard)

- Start frame = anchor (green or composited).
- Prompt motion only (camera locked or gentle track); do not re-describe appearance; keep Style preset id.
- Extract with ffmpeg; then same D3 pack pipeline.

## Screen / static sheet skeletons

Screens use the preset’s Screen bg; production stickers use `#00FF00`.

### Screen (9:16)

```text
Mobile UI screenshot, vertical 9:16, [PURPOSE], handwritten or preset-appropriate title, pill CTAs,
Style preset: [STYLE_ID], [MASTER STYLE — screens], [NEGATIVES]
```

### Static green sheet

```text
Isolated stickers on PURE #00FF00, large gaps, [ITEMS],
Style preset: [STYLE_ID], [MASTER STICKER STYLE], [NEGATIVES]
```

## Palette (cozy default tokens)

Other presets: use accents listed under that id in [styles.md](styles.md).

| Token | Hex |
|---|---|
| Paper | `#FDF8F0` |
| Sage | `#7CB342`–`#8FBC8F` |
| Tomato | `#E85D4C` |
| Text | `#3D3429` |
| Chroma | `#00FF00` |
