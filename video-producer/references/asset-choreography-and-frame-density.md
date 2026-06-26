# Asset Choreography and Frame Density

Use this when the frame looks empty, simplistic, or like a static slide.

## Asset-first workflow

Do not start by writing one large prompt. Start by planning assets:

1. Hero object: machine, phone, laptop, screenshot, document, robot, camera, product, chart.
2. Process objects: cards, arrows, connectors, modules, gauges, labels, chips, data packets.
3. Evidence objects: screenshots, generated examples, before/after panels, mini galleries.
4. Texture/depth: grid, paper grain, desk shadow, subtle noise, UI shadows, foreground particles.
5. Reaction objects: warning stamps, green ticks, mascot reaction, pulse rings, status lights.
6. Sound objects: each tactile object should have a possible cue: click, tick, snap, stamp, chime.

## Frame occupancy targets

For 16:9 social explainers:

- Meaningful visual content: target 35-70% of frame.
- Readable text: normally under 35% of frame.
- Negative space: intentional zones for movement, captions, or reveals; never accidental emptiness.
- Layer count: 3-5 layers in most active shots.
- Every scene should have at least one object larger than 18% of frame width.
- Every diagram scene should include at least 4 small supporting assets or nodes unless it is a title drop.

## Asset choreography manifest

`assets/asset_choreography_manifest.csv` columns:

```csv
asset_id,type,description,source_or_prompt,rights_status,layer,first_on_sec,last_on_sec,entrance,main_motion,exit,states,reused_in_segments,sfx_affordance,implementation_notes
```

Example:

```csv
clip_module,svg_component,vertical CLIP bridge module with status LEDs,drawn SVG,safe,midground,186.2,202.5,slide from right + overshoot,LED blink + vector pipe pulse,scale down into pipeline,"idle|processing|success",S05;S09,"soft machine hum; data tick",render as SVG group not raster text
```

## Anti-empty fixes

If a frame feels empty, use at least two:

- Add a device frame: phone/laptop/tablet/browser window with the content inside.
- Add a machine cutaway: show the mechanism rather than a label.
- Add foreground annotations: hand cursor, magnifier, arrow, callout tags.
- Add background structure: grid perspective, desk surface, pinned cards, faint pipeline.
- Add a visible process: incoming -> processing -> output.
- Add a mascot/robot reaction only when it clarifies emotion.
- Use a split-screen or before/after panel instead of a single centered card.
- Use card stacks and mini examples to show scale.
- Use a map/timeline/conveyor/orbit layout instead of bullets.

## Device-screen pattern

A strong explainer frame can place content inside a device:

- phone for platform/social examples.
- laptop/browser for tool/demo dashboards.
- tablet/whiteboard for teaching diagrams.
- camera/scanner box for OCR/vision model metaphors.
- black-box computer for proprietary/internal model sections.

Device screens should change during narration: typing, cursor taps, layers appearing, OCR boxes, scroll, data cards, status indicators.
