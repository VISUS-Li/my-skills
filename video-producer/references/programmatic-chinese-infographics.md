# Programmatic Chinese Infographics

Use this when a video contains readable Chinese labels, subtitles, UI text, diagrams, or educational explainers.

## Principle

Treat Chinese text as layout data, not image content. Text-to-image and text-to-video models can create attractive plates, but exact Chinese glyphs, punctuation, line breaks, and small UI labels remain too important to leave to pixel generation. Render text in code or a deterministic editor layer.

## Recommended rendering stack

- **Primary**: Remotion, Motion Canvas, SVG, HTML/CSS, Canvas, or HyperFrames for vector diagrams, captions, arrows, labels, and animated text.
- **Secondary**: Manim for mathematical/scientific diagrams where procedural geometry is useful.
- **Assembly**: FFmpeg for concat, overlays, captions, loudness normalization, and export.
- **Finishing**: CapCut/Jianying/DaVinci/Premiere only after the deterministic text and motion layers are locked.
- **Generative imagery**: GPT Image models, Seedream, Midjourney, Flux, Nano Banana, etc. only for no-text visual plates, textures, examples, thumbnails, backgrounds, or character/prop assets.

## Implementation rules

1. Split every scene into `background_plate`, `diagram_layer`, `text_layer`, `caption_layer`, and `audio_sync`.
2. Use image generation prompts that reserve blank space: “blank labels, no readable text, clean panels for later overlay.”
3. Keep a `text_manifest.json` with each text item: `id`, `content`, `font_role`, `position`, `max_width`, `start_sec`, `end_sec`, `animation`, and `proofread_status`.
4. Proofread `text_manifest.json` before render. No “final” export with `proofread_status != approved`.
5. Use fallback CJK fonts available on the target machine. Do not bundle commercial fonts unless licensing allows it.
6. For small labels, increase stroke/contrast rather than lowering font size. Avoid text below 18 px at 720p or 28 px at 1080p.
7. Export captions separately as SRT/ASS and also burn-in for short-video platforms when needed.

## Prompt pattern for no-text plates

`Create a clean vector-style educational illustration plate for [concept]. Use warm off-white background, rounded panels, teal/blue/green accents, soft shadows, subtle grid. Leave all labels blank; do not include any readable text, letters, numbers, or symbols. Reserve clear spaces where Chinese labels will be overlaid later.`

## Quality gate

Fail a scene if:

- exact readable Chinese appears only inside an AI-generated raster/video layer;
- text touches platform UI/safe-area boundaries;
- Chinese label sizes are inconsistent across related objects;
- labels do not have enough contrast against the plate;
- the caption and voiceover disagree;
- no text proofreading step is recorded.
