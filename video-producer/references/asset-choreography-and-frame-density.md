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

- Meaningful visual content: target **50–80%** of frame (raise from sparse layouts).
- Readable text: normally under 30% of frame.
- Negative space: intentional zones for movement, captions, or reveals; **never accidental emptiness** — fill with ambient grid, orbs, texture, or supporting icons.
- Layer count: **4–6 layers** in most active shots.
- Every scene should have at least one object larger than 18% of frame width **plus** ≥4 smaller supporting assets.
- Every diagram scene should include at least **6–8** small supporting assets or nodes unless it is a deliberate title drop.
- **Animation fill:** every 0.5–1.0s at least one asset changes state (enter/move/pulse/morph/exit); ambient layer never fully static >0.8s.

## Asset choreography manifest

`assets/asset_choreography_manifest.csv` columns:

```csv
asset_id,type,description,source_or_prompt,rights_status,layer,first_on_sec,last_on_sec,entrance,main_motion,exit,states,reused_in_segments,sfx_affordance,implementation_notes
```

**`description` 与 `source_or_prompt` 默认用中文**（英文 UI/代码素材可在 subject 中保留英文片段）。

Example:

```csv
clip_module,svg_component,竖向 CLIP 桥接模块，带状态指示灯,手绘 SVG：圆角模块+向量管道，科技科普配色,safe,midground,186.2,202.5,从右侧滑入+ overshoot,LED 闪烁+管道脉冲,缩小汇入流水线,"idle|processing|success",S05;S09,"soft machine hum; data tick",SVG group 渲染，中文标签走 text layer
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
