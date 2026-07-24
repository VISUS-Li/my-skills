# 风格参考与提示词模板

**预设目录（在此切换风格）：** [styles.md](styles.md)  
默认风格 id：**`cozy-scrapbook`**。任何任务先解析 `style_id`，再把该预设的 Master + Negatives
贴为 `[MASTER …]` / `[NEGATIVES]`。

## Master 风格 — 界面屏 / 贴纸

活动预设不是 cozy 时，**不要**写死 cozy 专用措辞。  
从 [styles.md](styles.md) 复制当前块。

styles.md 不可用时的回退 — cozy 默认：

**界面屏**
```text
Mobile app UI, WeChat mini-program, warm cream paper-textured background #FDF8F0,
cozy kitchen scrapbook aesthetic, hand-drawn doodle stickers with thick dark outlines
and white sticker borders, soft sage green and tomato red accents, pill-shaped CTA buttons,
highly rounded cards, playful handwritten Chinese titles, soft diffused shadows,
generous whitespace, friendly lifestyle utility UI
```

**贴纸**
```text
Die-cut sticker, hand-drawn cozy scrapbook doodle, thick dark brown outline,
thick white sticker border, soft contact drop shadow, matte warm colors,
sage green and tomato red accents, cute slightly chunky shapes, flat 2D illustration,
consistent stroke weight
```

**Negatives（cozy 回退）**
```text
no dark mode, no neon glow, no glassmorphism, no cyberpunk, no hard black neo-brutalism,
no purple gradient, no photorealistic photos, no 3D metal render, no multi-character crowd,
no cream paper full-bleed scene behind stickers when chroma key is required
```

## 锚图提示（Mode D1）

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

## 精灵行提示（Mode D2 轻量 — 工程化 C）

仅当无易混淆道具时。否则优先关键。

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

传入 `reference_image_paths=[anchor]`。

## 关键提示（Mode D2 中等 — 推荐）

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

传入 `reference_image_paths=[anchor]`，第 2 帧起用 `[anchor, previous_accepted]`。

## I2V 说明（Mode D2 难）

- 起始帧 = 锚图（绿幕或已合成）。
- 提示只写运动（机位锁定或轻跟踪）；不要重述外观；保留风格预设 id。
- 用 ffmpeg 抽帧；再走同一套 D3 打包流水线。

## 界面屏 / 静态拼版骨架

界面屏用预设 Screen 背景；生产贴纸用 `#00FF00`。

### 界面屏（9:16）

```text
Mobile UI screenshot, vertical 9:16, [PURPOSE], handwritten or preset-appropriate title, pill CTAs,
Style preset: [STYLE_ID], [MASTER STYLE — screens], [NEGATIVES]
```

### 静态绿幕拼版

```text
Isolated stickers on PURE #00FF00, large gaps, [ITEMS],
Style preset: [STYLE_ID], [MASTER STICKER STYLE], [NEGATIVES]
```

## 色板（cozy 默认令牌）

其他预设：用 [styles.md](styles.md) 该 id 下列出的强调色。

| 令牌 | Hex |
|---|---|
| Paper | `#FDF8F0` |
| Sage | `#7CB342`–`#8FBC8F` |
| Tomato | `#E85D4C` |
| Text | `#3D3429` |
| Chroma | `#00FF00` |
