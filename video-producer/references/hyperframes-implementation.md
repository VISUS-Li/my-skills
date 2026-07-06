# HyperFrames Implementation

Use this when turning the director plan into HTML/CSS/JS segments. HyperFrames is not just a renderer for prebuilt assets; it is the preferred generator for lightweight visual material that benefits from precise timing, typography, layout, and motion.

## HyperFrames-Native First

Generate these directly in HyperFrames code instead of the external asset generation stage:

- exact Chinese text, subtitles, title cards, viewpoint lines, quote cards, comment stickers.
- color blocks, plates, cards, glass panels, device/browser frames, source-card containers.
- red boxes, brackets, arrows, masks, magnifiers, cursors, scan lines, focus rings.
- simple charts, data cards, counters, price tags, table overlays, timeline bars.
- ambient CSS textures, grids, noise overlays, light sweeps, paper/desk surfaces when they are not factual media.
- transition anchors: shared circles, bars, numbers, words, masks, and motion paths.

Use external assets only when the material needs real-world truth, photographic texture, source provenance, manual drawing quality, or a reusable raster/video file.

Suggested ID convention:

- `hf_*`: HyperFrames-native component or shape.
- `text_*`: text unit from `script/text_manifest.json`.
- `chart_*`: data visualization generated in code unless tied to an external chart screenshot.
- `svg_*`: inline SVG annotation or exported SVG only when needed.
- `ambient_*`: CSS/native texture unless it points to a real file.

These IDs may appear in `visual_sync_plan.csv`, `beat_asset_plan.csv`, and `beat_timeline.json` without corresponding files on disk when they are clearly programmatic.

## Rich Frame Baseline

For normal explanation, evidence, or data beats, the default is not a plain background. Build a rich but readable frame:

- background bed: `hf_grid_bg`, `hf_noise_grain`, `hf_light_sweep`, `hf_soft_shadow`.
- focal object: screenshot, card stack, chart, diagram, device frame, or real footage.
- support actors: `hf_icon_cluster`, `hf_data_chip`, `chart_*`, `hf_source_card`, `hf_cursor`, badges.
- attention guide: red box, yellow highlight, arrow, scan line, magnifier, or label.
- motion: at least one meaningful micro-action every 0.5-1.2s unless the beat is a deliberate hold.

The light educational grid style is a safe default for tech/news explainers: warm off-white grid, subtle grain, rounded cards, small icons, red/yellow accents, dark readable Chinese text, and bottom caption pill.

## Build Order

1. Read `vo_timing.json`, `visual_sync_plan.csv`, `beat_asset_plan.csv`, `text_manifest.json`, `beat_timeline.json`, and `audio_cue_sheet.json`.
2. Create a static layout/styleframe first. It should work as a still image before animation.
3. Load the motion/text preset registry (`micro_animation_palette.json`) and create small GSAP helper functions for the preset IDs used by this segment.
4. Implement layers: ambient, scene/proof, mechanism/data, annotation, dynamic text, HUD/captions, FX.
5. Add GSAP or deterministic timeline labels from voice timing.
6. Add micro-events at absolute times. Do not rely on random delays.
7. Verify screenshots, captions, source labels, and chart axes at target resolution.

## Standard Build Entry

Use the project-level builder as the source of truth:

- `scripts/build_s001_composition.py` for `S001`.
- `scripts/build_<segment>_composition.py` for other segments.
- `scripts/build_segment_index.py` only as a generic fallback.

Do not make `segments/<id>/scripts/build_rich_segment.py` the only entry. If a segment-local rich builder is useful, the root builder must call it and still write `segments/<id>/index.html`.

The builder must be idempotent: running it should rebuild the same segment HTML without overwriting unrelated assets or replacing a rich composition with a simple fallback.

## Review Studio Seek Contract

The Review Studio composition tab does not let the child iframe run freely. The parent page loads `segments/<id>/index.html` and seeks the child timeline with:

```js
compIframe.contentWindow.__timelines[segment].time(t);
```

Therefore the composition HTML must:

- expose `window.initComposition`;
- initialize `window.__timelines = window.__timelines || {}`;
- register `window.__timelines[segment] = tl`;
- create `tl` with `gsap.timeline({ paused: true })`;
- avoid `tl.play()` / autoplay in the child frame;
- expose `window.__compositionErrors` and an on-frame error overlay.

Register the timeline before risky optional animation code. If a later tween fails, the preview should show an explicit error rather than silently freezing at `t=0`.

## Layer Roles

- Ambient: texture, grid, light, low-motion background. Prefer CSS/HTML unless a real image/video texture is needed.
- Scene/proof: real footage, screenshot, document, table, product page, photo.
- Mechanism/data: chart, diagram, process, comparison matrix. Prefer HyperFrames-native HTML/SVG/canvas for simple charts and data cards.
- Annotation: red box, arrow, bracket, cursor, magnifier. Prefer inline SVG/CSS in HyperFrames.
- Dynamic text: keyword, number hero, quote, contrast label.
- HUD: subtitle/source labels; minimal movement.
- FX: short burst only for emphasis or transition.

## Timing Rules

- Proof appears before or with the claim.
- Highlight lands on the spoken keyword.
- Readable UI/table/chart details get post-hold.
- Emotion and viewpoint beats may use deliberate stillness.
- Segment duration must match measured audio, not equal splits.

## Text Rules

- Render exact Chinese text as HTML/SVG/canvas text.
- Generated images may contain no critical Chinese wording.
- Keep bottom captions out of proof details.
- Do not cover ad slots, table rows, chart labels, or source names with decorative text.
- Support `text_manifest.items[].spans[]` when a line mixes hero words and support words. Spans may have independent timing, class names, preset IDs, colors, stroke/shadow, and attachment targets.
- Use CSS text stroke, layered shadows, gradient fills, masks, and sticker-like backing only as live text styling. Do not rasterize Chinese flower words into images.
- Bind text hits to `vo_timing.json` or `sync_phrase`; a keyword should land on or just before the spoken word, not at an arbitrary segment midpoint.

## Preset Implementation

Treat preset IDs as semantic contracts:

- `entrance.*` and `exit.*` helpers should set opacity/transform/filter and return a GSAP tween/timeline.
- `text.*` helpers should animate the text layer and, when needed, its stroke/shadow/backing layer together.
- `reactive.yield_*` helpers should animate both the entering object and the yielding target in the same labeled timeline.
- Presets may be parameterized per beat, but do not change the focal owner or cover `must_show_detail` without updating the director plan.
- Optional beat-specific DOM nodes must be guarded. Do not pass raw class selector strings directly into `tl.from()`, `tl.to()`, or `tl.fromTo()` for nodes that may not exist in every beat. Use `safeTargets()` / `addFromIfPresent()` / `addToIfPresent()` or equivalent.
- GSAP functional values receive `(index, target, targets)`. For dataset-driven animation, write `width: (index, target) => target.dataset.pct || "0%"`. `width: (el) => el.dataset.pct` is wrong because `el` is the index.

Recommended markup:

```html
<div class="text-unit text-keyword"
  data-text-id="text_cost_push"
  data-motion-preset="text.keyword_pop"
  data-sync-phrase="成本">
  <span data-span-id="support">不是涨价</span>
  <span data-span-id="hero">成本</span>
</div>
```

For yield moves, keep proof layers readable:

```js
applyPreset("reactive.yield_left", {
  entrant: ".text-keyword",
  yieldTarget: ".proof-card",
  mustShowSelector: ".source-label, .table-header, .chart-axis",
  maxShiftPct: 8
});
```

Safe selector pattern:

```js
function safeTargets(selector, opts = {}) {
  const targets = gsap.utils.toArray(selector);
  if (!targets.length && opts.required) reportCompositionError(`Missing ${selector}`);
  return targets;
}

function addToIfPresent(tl, selector, vars, at) {
  const targets = safeTargets(selector);
  if (targets.length) tl.to(targets, vars, at);
}
```

## Native Component Quality

HyperFrames-native material should be designed, not default-browser-looking:

- use design tokens for color, radius, spacing, shadow, stroke width, and type scale.
- give every generated component a motion role: enter, focus, transform, hold, exit, or transition bridge.
- use real layout systems: grids, flex rows, absolute zones, masks, and safe areas.
- split text into hierarchy: caption, keyword, number hero, quote, label, viewpoint.
- animate the property that carries meaning: number count, row highlight, red-box lock, chart endpoint, mask reveal.
- keep components responsive to the target ratio; do not rely on viewport-scaled font sizes.

## Implementation Rejections

Reject:

- one centered card for the whole beat.
- plain background with only text for a normal explanation beat.
- fade-only animation for every cut.
- screenshots used as unreadable wallpaper.
- all layers moving equally.
- SVG icons replacing real-world scenes.
- exporting simple text/boxes/cards as separate image files when HyperFrames can render them more precisely.
- proof shown after the narrator already made the claim.
- preset-driven motion that ignores the focal owner, `must_show_detail`, or voice timing.
- segment HTML that relies on autoplay instead of the Review Studio seek contract.
- raw GSAP selectors or one-size-fits-all micro-events that warn on beats without matching nodes.
