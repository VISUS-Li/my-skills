# Visual Asset Generation Protocol

Use when segments look **too empty**, **PPT-like**, or user asks for icons, illustrations, AI images, SVG.

## Minimum asset budget (per segment)

| Asset type | Min count | Notes |
|---|---:|---|
| SVG icons (topic-specific) | 6 | stroke 2–4px, rounded, no text inside raster |
| Decorative PNG (transparent) | 2 | plates, blobs, mascots — **no readable Chinese** |
| UI/source primitives | 3 | cards, stamps, arrows from design system |
| Motion actors | 8+ | must move during narration |

Log everything in `assets/asset_manifest.csv` with `rights_status`.

## Generation routing

| Need | Tool | Output |
|---|---|---|
| Icon set (consistent style) | **Hand-write SVG** or LLM → SVG code | `segments/S00x/assets/icon_*.svg` |
| Hero plate / texture | **Image model** (GPT Image, DALL·E, Flux, etc.) | PNG → `assets/images/` |
| Transparent sticker/mascot | Image model + **rembg** or native alpha prompt | PNG transparent |
| Reference mood | Web search + moodboard | `design/visual_moodboard.json` |
| Stock fallback | Mixkit/Pixabay (manual if CDN 403) | logged in rights log |

## Image model prompt template (no text in image)

```text
Flat vector infographic illustration for [TOPIC] explainer video.
Style: light warm grid canvas #F7F1E6, soft blue/amber accents, rounded cards,
subtle depth shadows, douyin/B站 tech explainer, 16:9 composition.
Subject: [concrete objects — e.g. diaper layers, newspaper, government seal abstract].
NO text, NO logos, NO watermarks, NO baby-photo realism.
Transparent or clean background for overlay use.
```

## SVG generation template (preferred for icons)

Ask the model for **valid SVG** only:

```text
Create a 128x128 SVG icon: [subject].
Style: 2-4px stroke, round caps, colors #2563EB #F59E0B #22C55E #EF4444 #1F2937.
No embedded text. viewBox="0 0 128 128". Single file, no scripts.
```

Validate: open in browser; run through HyperFrames compile.

## Segment asset folder layout

```
segments/S001/
  assets/
    icon_newspaper.svg
    icon_diaper.svg
    s001_hero_plate.png
  visual_asset_brief.json   # optional manifest
  index.html
  vo_timing.json
  s001_vo.wav
```

## visual_asset_brief.json (optional)

```json
{
  "segment_id": "S001",
  "style_refs": ["design/tokens.json", "design/art_direction.md"],
  "assets": [
    {"id": "icon_newspaper", "type": "svg", "prompt": "...", "path": "assets/icon_newspaper.svg", "layer": "midground", "motion": "stamp_hit"}
  ]
}
```

## Rights

| Source | rights_status |
|---|---|
| Hand-written SVG | `cleared` |
| Project-generated PNG (no third-party) | `cleared` |
| Stock / AI with license | `cleared` after license check |
| Unknown web scrape | `candidate_needed` — **never final** |

## Anti-patterns

- ❌ One full-screen card for entire beat
- ❌ Reusing same icon 4× without transform/state change
- ❌ Baking Chinese into PNG (use programmatic text layers)
- ❌ 16:9 photo backgrounds that compete with captions

## Research enrichment (design layer)

Before asset gen for factual segments:

1. Search topic visuals: official logos **as abstract shapes only**, timeline photos → prefer **diagrams**
2. Pull 2–3 reference layouts (game HUD, infographic, news explainer) into `design/visual_moodboard.json`
3. Note **must-not-copy** (watermarks, brand packs)

See `references/layered-composition-depth.md` for how assets stack.
