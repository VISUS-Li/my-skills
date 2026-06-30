# Visual World And Richness

Use this when a HyperFrames segment looks empty, text-heavy, visually boring, or less polished than a mature educational/news explainer.

## Baseline

HyperFrames-native does not mean sparse. It means the frame is built from live code layers that can be timed, animated, and restyled precisely.

Every non-deliberately-sparse HyperFrames beat should have:

- a designed background bed,
- one focal owner,
- at least two support actors,
- one attention guide,
- one text hierarchy element,
- subtle motion during holds.

## Light Educational Grid Style

For tech/finance/news explainers, a strong default is a light educational workspace:

- warm off-white or pale gray base,
- subtle grid or dot matrix,
- faint paper grain/noise,
- soft shadows under cards,
- red/yellow focus accents,
- black/dark text with one vivid accent color,
- rounded cards, browser/device frames, source cards,
- small icons, chips, arrows, badges, mini charts,
- bottom caption pill kept readable.

This can echo the structural grammar of tutorial explainers like "小白debug" without copying logos, exact assets, watermark, or identity.

Suggested native components:

- `hf_grid_bg`: off-white grid/dot matrix background.
- `hf_noise_grain`: subtle paper/noise overlay.
- `hf_card_stack`: layered rounded cards behind the proof.
- `hf_source_card`: browser/document/card frame with source label.
- `hf_icon_cluster`: small contextual icons around a mechanism.
- `hf_data_chip`: small metric/status chip.
- `chart_*`: mini line/bar/price chart generated in code.
- `hf_cursor`: pointer/tap/hover cue.
- `hf_scan_line`: scanning/focus sweep.
- `hf_red_box` / `hf_yellow_highlight`: attention lock.

## Layer Budget

Use a practical layer budget, not clutter:

- Sparse viewpoint: background + text + one subtle motion.
- Medium explanation: background + focal card/diagram + 2 support actors + caption.
- Evidence/data: background + screenshot/source + annotation + text label + data/icon support.
- Mechanism: background + modules/cards + arrows + icons + active text/number.

Avoid accidental empty quadrants. Use small chips, ghosted cards, grids, or icon clusters to fill space only when they support the topic.

## Motion Rhythm

A rich frame needs small visual life:

- background grid drifts slowly or has a light scan sweep.
- cards slide, settle, or stack.
- icons tick, pulse, or change state.
- charts draw or numbers count.
- cursor/tap highlights UI action.
- red/yellow focus marks lock on the spoken keyword.
- camera pushes/pans enough to create shot changes.

Do not animate everything. One focal actor moves meaningfully; support actors breathe quietly.

## Empty Frame Rejections

Reject these unless the beat is an intentional final viewpoint/reset:

- plain solid background with only centered text.
- white/black screen used for ordinary explanation.
- no icon, chart, screenshot, card, frame, photo, or diagram for more than one normal beat.
- all HyperFrames-native components are just text labels.
- background has no grid, texture, depth, light, or motion.
