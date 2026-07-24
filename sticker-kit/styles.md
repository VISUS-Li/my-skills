# 内置风格预设

**默认：** `cozy-scrapbook`  
**切换：** 用户点名预设 id / 别名，或说「换风格 / switch style / use pixel」。  
**整单锁定：** 把 `style_id` 写入工程 brief，并把该预设的 **Master sticker** + **Negatives** 贴进每条 GenerateImage 提示。
片段中途不要混预设，除非用户要求换风格（然后重做锚图）。

通用（所有预设，除非某预设覆盖）：

- 贴纸 / 锚图 / 帧：优先纯色色键 `#00FF00`（主体后无场景）
- 界面屏（Mode B）：用该预设的 **Screen bg**
- 模切剪影 + 小尺寸下可读描边
- [continuity.md](continuity.md) 的连续性规则始终适用
- 禁止写实 / 玻璃拟态 / 紫霓虹 UI chrome（除非预设明确允许受控高光）

---

## 预设索引

| id | 别名（中 / 英） | 一句话气质 |
|---|---|---|
| `cozy-scrapbook` | 暖奶油, 手账, scrapbook, cozy | 暖奶油手绘手账（**默认**） |
| `pixel-8bit` | 8bit, 像素, pixel art, NES | 块状 8-bit 像素精灵贴纸 |
| `hex-colorful` | 彩色海克斯, hex, honeycomb, hex tile | 明亮几何六边形 / 蜂窝贴纸 |
| `flat-vector` | 扁平矢量, flat icon, vector | 干净扁平矢量图标贴纸 |
| `kawaii-pastel` | 卡哇伊, pastel kawaii, chibi | 柔和粉彩卡哇伊 / Q 版贴纸 |
| `watercolor` | 水彩, wash painting | 柔和水彩晕染贴纸 |
| `comic-ink` | 漫画线稿, comic, ink | 粗线条漫画墨水贴纸 |
| `neo-pop` | 新波普, pop sticker, bold pop | 高对比波普 / 大胆图形贴纸 |
| `clay-soft` | 软陶, clay, claymation soft | 软哑光黏土玩具贴纸（非写实） |
| `risograph` | 孔版, riso, print grain | 颗粒孔版印刷贴纸 |
| `chalk-pastel` | 粉笔, chalk, crayon | 粉笔 / 蜡笔粉彩贴纸 |
| `marker-copic` | 马克笔, marker, Copic | 酒精马克笔速写贴纸 |
| `line-doodle` | 线稿涂鸦, doodle, ink doodle | 极简墨线涂鸦贴纸 |
| `retro-vintage` | 复古, vintage, 70s | 复古 70 年代徽章 / 怀旧贴纸 |

用户要的风格不在表中：选最接近预设，说明锁定了哪个 id，并可选用新 id 扩展本文件。

---

## `cozy-scrapbook`（默认）

**Screen bg：** `#FDF8F0` 奶油纸  
**Accent：** 鼠尾草绿 `#7CB342`–`#8FBC8F`，番茄红 `#E85D4C`，墨色 `#3D3429`

**Master — screens**
```text
Mobile app UI, WeChat mini-program, warm cream paper-textured background #FDF8F0,
cozy kitchen scrapbook aesthetic, hand-drawn doodle stickers with thick dark outlines
and white sticker borders, soft sage green and tomato red accents, pill-shaped CTA buttons,
highly rounded cards, playful handwritten Chinese titles, soft diffused shadows,
generous whitespace, friendly lifestyle utility UI
```

**Master — stickers**
```text
Die-cut sticker, hand-drawn cozy scrapbook doodle, thick dark brown outline,
thick white sticker border, soft contact drop shadow, matte warm colors,
sage green and tomato red accents, cute slightly chunky shapes, flat 2D illustration,
consistent stroke weight
```

**Negatives**
```text
no dark mode, no neon glow, no glassmorphism, no cyberpunk, no hard black neo-brutalism,
no purple gradient, no photorealistic photos, no 3D metal render, no multi-character crowd,
no cream paper full-bleed scene behind stickers when chroma key is required
```

---

## `pixel-8bit`

**Screen bg：** `#1A1C2C` + 柔和 `#F4F0E6` 面板，或用户要浅色 UI 时用奶油 `#FDF8F0`  
**Accent：** 有限 NES 风格色板（最多约 8–16 色）

**Master — stickers**
```text
Die-cut sticker, authentic 8-bit pixel art sprite, visible pixel grid, chunky low-res shapes,
hard pixel edges, NO anti-aliasing, limited retro game palette, thick white pixelated sticker border,
flat pixel shading only (1–2 shades), cute readable silhouette at small size, retro game UI aesthetic
```

**Negatives**
```text
no smooth vector curves, no soft blur, no photoreal, no high-res painterly detail,
no anti-aliased edges, no gradients inside pixels, no 3D render, no cream paper scene behind subject
```

**动画注意：** 锁定像素比例；禁止亚像素变形；肢体步进优先整数感。

---

## `hex-colorful`

**Screen bg：** 柔和 `#F7F4EE` + 淡六边形网格水印  
**Accent：** 高饱和糖果六边形填充（青、芒果、紫、柠）— 按部件锁色

**Master — stickers**
```text
Die-cut sticker, colorful geometric hexagon / honeycomb motif, isometric-friendly hex tiles,
bright saturated flat fills, crisp dark outline, thick white sticker border, playful modern geometric
illustration, clean faceted shapes, optional small hex pattern accents on props, soft contact shadow
```

**Negatives**
```text
no photoreal, no noisy watercolor bleed, no chaotic non-hex clutter, no glassmorphism,
no purple neon glow storm, no multi-character crowd, no full-bleed scene behind chroma subject
```

---

## `flat-vector`

**Screen bg：** `#FAFAF7`  
**Accent：** 3–5 个品牌扁平色，高清晰度

**Master — stickers**
```text
Die-cut sticker, clean flat vector illustration, geometric simplified shapes, even stroke weight,
bold continuous outline, thick white sticker border, minimal shading (optional single flat shadow tone),
icon-ready silhouette, modern app-icon sticker aesthetic, crisp edges
```

**Negatives**
```text
no texture grain, no watercolor, no pixelation, no photoreal, no skeuomorphic gloss,
no busy gradients, no cream scrapbook paper behind chroma subject
```

---

## `kawaii-pastel`

**Screen bg：** `#FFF5F7` 腮红纸  
**Accent：** 粉彩粉、薄荷、黄油、淡紫（柔和）

**Master — stickers**
```text
Die-cut sticker, kawaii pastel chibi style, oversized head optional, big shiny eyes,
rounded soft shapes, thick dark outline, thick white sticker border, soft blush tones,
cute sticker pack aesthetic, flat fills with tiny highlight dots, friendly and sweet
```

**Negatives**
```text
no horror, no photoreal skin pores, no dark neo-brutalism, no harsh contrast crushing pastels,
no 3D metal, no crowded multi-character sheet cells
```

---

## `watercolor`

**Screen bg：** `#FBF7F0` 冷压纸触感  
**Accent：** 透明湿晕；部件色彩锁定用颜料名

**Master — stickers**
```text
Die-cut sticker, soft watercolor illustration, gentle pigment blooms and paper tooth,
loose but readable silhouette, light ink contour optional, thick white sticker border,
matte wet-on-wet color, cozy art-journal sticker, not photoreal
```

**Negatives**
```text
no hard vector flat only, no neon, no glassmorphism, no photoreal photo collage,
no muddy overworked brown sludge, no full scenic wash behind chroma subject
```

**动画注意：** 水彩晕染会伪装成变形 — 每帧强调拓扑 + 色彩锁定。

---

## `comic-ink`

**Screen bg：** `#FFFDF8`  
**Accent：** 近似 CMYK 原色 + 重黑

**Master — stickers**
```text
Die-cut sticker, bold comic-book ink illustration, thick black contours, clear ink weights,
flat cel color fills, optional halftone dots for shade, thick white sticker border,
dynamic graphic novel sticker, high readability at small size
```

**Negatives**
```text
no soft painterly blur, no photoreal, no watercolor wash dominance, no 3D render,
no cream scrapbook clutter behind chroma subject
```

---

## `neo-pop`

**Screen bg：** `#F2F0EA` + 硬偏移色块  
**Accent：** 一个响亮强调色（如 `#D4501F`）+ 黑 + 奶油

**Master — stickers**
```text
Die-cut sticker, bold neo-pop graphic sticker, chunky shapes, hard high-contrast colors,
heavy black outline, thick white sticker border, slightly playful brutal graphic energy,
flat fills, poster-sticker attitude, still cute and UI-usable (not angry meme chaos)
```

**Negatives**
```text
no photoreal, no soft cozy watercolor, no glassmorphism, no purple neon chrome,
no illegible clutter, no multi-character crowds
```

---

## `clay-soft`

**Screen bg：** `#F5F1EA`  
**Accent：** 软玩具塑料感；哑光、圆润

**Master — stickers**
```text
Die-cut sticker, soft matte clay / polymer-clay toy look, rounded chunky forms,
subtle soft shading (not photoreal), thick white sticker border, gentle studio-like light,
cute collectible figure sticker, simplified facial features if any, clean silhouette
```

**Negatives**
```text
no real clay fingerprints photo, no shallow-DOF photo, no SSS skin realism, no metal 3D,
no glassmorphism, no busy diorama background behind chroma subject
```

---

## `risograph`

**Screen bg：** `#F6F1E7`  
**Accent：** 有限双色/三色（如豆红 + 青绿）

**Master — stickers**
```text
Die-cut sticker, risograph print aesthetic, grainy ink texture, slight misregistration of color layers,
limited duotone or tritone palette, soft halftone dots, thick white sticker border,
indie zine sticker vibe, matte paper print look
```

**Negatives**
```text
no glossy digital UI chrome, no photoreal, no smooth vector-only perfection,
no neon glow, no full photographic scene behind chroma subject
```

---

## `chalk-pastel`

**Screen bg：** 深色板 `#2B2B2B`（界面），或用户要求时用奶油纸  
**Accent：** 粉尘粉笔粉彩

**Master — stickers**
```text
Die-cut sticker, chalk and soft pastel crayon drawing, dusty pigment texture on dark or cream,
slightly rough stroke edges, thick white sticker border, playful blackboard / craft sticker look,
readable silhouette, not photoreal chalk photo
```

**Negatives**
```text
no photoreal chalkboard photo, no wet oil paint, no neon, no glassmorphism,
no ultra-smooth vector only
```

---

## `marker-copic`

**Screen bg：** `#FFFCF7` 马克笔纸  
**Accent：** 鲜艳马克笔染料；色彩锁定要严

**Master — stickers**
```text
Die-cut sticker, alcohol marker / Copic illustration, expressive ink under-drawing,
broad marker strokes with layered shading, vibrant clean colors, thick white sticker border,
concept-art sticker energy, controlled edges for cutout
```

**Negatives**
```text
no photoreal, no watercolor blooms as primary, no pixel art, no 3D render,
no messy uncontained scribbles that break die-cut silhouette
```

---

## `line-doodle`

**Screen bg：** `#FDF8F0`  
**Accent：** 主要为墨线 + 1–2 点缀色

**Master — stickers**
```text
Die-cut sticker, minimal hand ink doodle, playful continuous line, sparse fills,
thick dark outline, thick white sticker border, airy whitespace inside shapes,
notebook doodle sticker, consistent stroke weight
```

**Negatives**
```text
no heavy texture, no photoreal, no dense comic hatching overload, no 3D,
no neon, no multi-character crowd
```

---

## `retro-vintage`

**Screen bg：** `#F3E6C8` 旧纸  
**Accent：** 芥末、鳄梨绿、焦橙、褪青

**Master — stickers**
```text
Die-cut sticker, retro 1970s vintage badge / travel sticker, slightly faded print colors,
soft paper wear optional, bold period typography only if requested, thick white sticker border,
nostalgic graphic illustration, clean die-cut silhouette
```

**Negatives**
```text
no modern glass UI, no neon cyberpunk, no photoreal, no purple gradient chrome,
no cluttered collage behind chroma subject
```

---

## 提示注入片段

贴在每条生成提示末尾：

```text
Style preset: [STYLE_ID]. [MASTER STICKER OR SCREEN BLOCK]. [NEGATIVES].
Keep identity and topology locked; only FREE motion channels may change across frames.
```
