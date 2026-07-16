# Built-in style presets

**Default:** `cozy-scrapbook`  
**Switch:** user names a preset id / alias, or says「换风格 / switch style / use pixel」.  
**Lock for a job:** write `style_id` into the project brief and paste that preset’s **Master sticker** + **Negatives** into every GenerateImage prompt. Do not mix presets mid-clip unless the user asks for a style change (then regenerate the anchor).

Universal (all presets unless a preset overrides):

- Stickers / anchors / frames: prefer solid chroma `#00FF00` (no scene behind subject)
- Screens (Mode B): use the preset’s **Screen bg**
- Die-cut silhouette + readable outline at small size
- Continuity rules in [continuity.md](continuity.md) always apply
- Never photoreal / glassmorphism / purple-neon UI chrome (unless a preset explicitly allows a controlled glow)

---

## Preset index

| id | Aliases (CN / EN) | One-line vibe |
|---|---|---|
| `cozy-scrapbook` | 暖奶油, 手账, scrapbook, cozy | Warm cream hand-drawn scrapbook (**default**) |
| `pixel-8bit` | 8bit, 像素, pixel art, NES | Chunky 8-bit pixel sprite sticker |
| `hex-colorful` | 彩色海克斯, hex, honeycomb, hex tile | Bright geometric hex / honeycomb sticker |
| `flat-vector` | 扁平矢量, flat icon, vector | Clean flat vector icon sticker |
| `kawaii-pastel` | 卡哇伊, pastel kawaii, chibi | Soft pastel kawaii / chibi sticker |
| `watercolor` | 水彩, wash painting | Soft watercolor wash sticker |
| `comic-ink` | 漫画线稿, comic, ink | Bold comic-book ink sticker |
| `neo-pop` | 新波普, pop sticker, bold pop | High-contrast pop / bold graphic sticker |
| `clay-soft` | 软陶, clay, claymation soft | Soft matte clay toy sticker (not photoreal) |
| `risograph` | 孔版, riso, print grain | Grainy risograph print sticker |
| `chalk-pastel` | 粉笔, chalk, crayon | Chalk / crayon pastel sticker |
| `marker-copic` | 马克笔, marker, Copic | Alcohol-marker sketch sticker |
| `line-doodle` | 线稿涂鸦, doodle, ink doodle | Minimal ink doodle sticker |
| `retro-vintage` | 复古, vintage, 70s | Retro 70s badge / vintage sticker |

If the user asks for a style not listed: pick the closest preset, say which id you locked, and optionally extend this file with a new id.

---

## `cozy-scrapbook` (default)

**Screen bg:** `#FDF8F0` cream paper  
**Accent:** sage `#7CB342`–`#8FBC8F`, tomato `#E85D4C`, ink `#3D3429`

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

**Screen bg:** `#1A1C2C` with soft `#F4F0E6` panels, or cream `#FDF8F0` if user wants light UI  
**Accent:** limited NES-like palette (max ~8–16 colors)

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

**Motion note:** keep pixel scale locked; forbid sub-pixel morph; prefer integer-looking limb steps.

---

## `hex-colorful`

**Screen bg:** soft `#F7F4EE` with subtle hex grid watermark  
**Accent:** saturated candy hex fills (cyan, mango, violet, lime) — lock colors per part

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

**Screen bg:** `#FAFAF7`  
**Accent:** 3–5 brand-flat colors, high clarity

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

**Screen bg:** `#FFF5F7` blush paper  
**Accent:** pastel pink, mint, butter, lavender (soft)

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

**Screen bg:** `#FBF7F0` cold-press paper feel  
**Accent:** transparent wet washes; keep part Color lock as pigment names

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

**Motion note:** watercolor bleed can fake morph — emphasize Topology + Color lock every frame.

---

## `comic-ink`

**Screen bg:** `#FFFDF8`  
**Accent:** CMYK-ish primaries + heavy blacks

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

**Screen bg:** `#F2F0EA` with hard offset blocks  
**Accent:** one loud accent (e.g. `#D4501F`) + black + cream

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

**Screen bg:** `#F5F1EA`  
**Accent:** soft toy plastics; matte, rounded

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

**Screen bg:** `#F6F1E7`  
**Accent:** limited duotone/tritone (e.g. soy red + teal)

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

**Screen bg:** deep board `#2B2B2B` for screens, or cream paper if requested  
**Accent:** dusty chalk pastels

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

**Screen bg:** `#FFFCF7` marker paper  
**Accent:** vibrant marker dyes; keep Color lock strict

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

**Screen bg:** `#FDF8F0`  
**Accent:** mostly ink + 1–2 spot colors

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

**Screen bg:** `#F3E6C8` aged paper  
**Accent:** mustard, avocado, burnt orange, faded teal

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

## Prompt injection snippet

Paste at the end of every generation prompt:

```text
Style preset: [STYLE_ID]. [MASTER STICKER OR SCREEN BLOCK]. [NEGATIVES].
Keep identity and topology locked; only FREE motion channels may change across frames.
```
