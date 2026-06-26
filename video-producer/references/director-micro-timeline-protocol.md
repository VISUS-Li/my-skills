# Director Micro-Timeline Protocol

Use this when a video feels like PPT, empty, slow, or disconnected from narration. The goal is to convert every spoken phrase into a controllable, timestamped visual and audio event.

## Required artifacts

Create these before any HyperFrames/Remotion/Motion Canvas implementation:

- `script/narration_beats.csv`: phrase-level script timing.
- `script/beat_timeline.json`: sub-second director timeline.
- `assets/asset_choreography_manifest.csv`: every asset's entrance, movement, exit, layer, and reuse.
- `audio/audio_cue_sheet.json`: SFX and music cues anchored to visible beats.

## Beat density rules

For an explainer longer than 30 seconds:

- Normal beat spacing: 0.4-1.2s.
- Maximum unchanged hold: 1.8s.
- First 8 seconds: at least 5 visible events and 2 composition changes.
- Every narration sentence: at least one visual response.
- Every 5 seconds: at least 1 foreground action, 1 midground diagram/object action, and 1 background/depth/camera change.
- Every 8-12 seconds: one larger scene reset, reveal, transition, or rhythm break.

A beat is valid only if it changes meaning or attention. Opacity-only fade-ins are not enough unless paired with a semantic action.

## Beat taxonomy

Use these beat types in `beat_timeline.json`:

- `setup`: establishes the visual world or problem.
- `new_asset`: introduces a card, device, icon, screenshot, mascot, machine, or diagram node.
- `draw`: line, connector, arrow, brush, route, boundary, or OCR box is drawn.
- `focus`: camera push, spotlight, magnifier, halo, crop, or dimming directs attention.
- `compare`: split-screen, before/after, A/B card, scale, score, or rank.
- `transform`: text becomes vector, noise becomes image, card enters machine, icon morphs.
- `proof`: screenshot, chart, model diagram, product panel, benchmark, example gallery.
- `error`: red stamp, warning triangle, shake, glitch, crossed badge.
- `success`: green tick, badge, chime, confetti micro-burst.
- `transition`: match cut, whip, mask wipe, zoom-through, conveyor handoff.
- `hold`: intentional pause, documented with why it helps comprehension.

## Required JSON fields

Each beat in `script/beat_timeline.json` must include:

```json
{
  "beat_id": "B012",
  "segment_id": "S02",
  "start_sec": 12.4,
  "end_sec": 13.1,
  "narration": "这一步先把文字变成向量",
  "intent": "explain semantic embedding",
  "beat_type": "transform",
  "visual_action": "Chinese text card slides into CLIP module and exits as vector bars",
  "assets": ["text_card_prompt", "clip_module", "vector_bars"],
  "text_ids": ["caption_012", "label_clip"],
  "layout_zone": "center-left to center-right",
  "camera": "subtle push-in 1.0 to 1.05",
  "motion": {
    "entrance": "card snap-in from left, 0.32s",
    "main": "mask-reveal vector bars, 0.48s",
    "exit": "none",
    "easing": "standard productive"
  },
  "sfx_cue_ids": ["SFX_012_TICK", "SFX_012_VECTOR"],
  "density_note": "frame has background grid, main CLIP module, side labels, bottom caption",
  "why_not_ppt": "visualizes conversion rather than showing bullet text"
}
```

## Narration-to-visual mapping

For each sentence, identify the verb and make that verb visible:

- “输入 / 放进 / 喂给” -> card/phone/file enters a machine or slot.
- “识别 / 看懂 / 解析” -> scanner beam, OCR boxes, magnifier, highlight sweep.
- “转换 / 编码 / 嵌入” -> text turns into bars, nodes, coordinates, tiles.
- “比较 / 匹配 / 对齐” -> split screen, magnets, bridge, lock-in connector.
- “错误 / 不会 / 混乱” -> red stamp, jitter, crossed badge, misaligned glyphs.
- “稳定 / 提升 / 解决” -> green check, gauge fill, clean output, snap-to-grid.
- “为什么 / 原因” -> question mark becomes machine cutaway or zoom into mechanism.

## Human review checklist

Before rendering, answer:

1. What changes visually during every spoken sentence?
2. Which asset owns the viewer's attention at each second?
3. What enters, exits, transforms, or reacts in each 0.4-1.2s interval?
4. Are SFX attached to visible actions rather than arbitrary whooshes?
5. Can the segment still be understood if captions are muted and the viewer only sees the diagrams?
