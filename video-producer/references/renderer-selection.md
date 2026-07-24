# Renderer and asset selection

Keep Remotion responsible for the final composition, timing, captions, audio,
and render. Choose another capability only when it produces a clearly bounded
scene, effect, or asset better than a native Remotion implementation.

## Default

Use Remotion directly for:

- Titles, captions, cards, lists, comparisons, timelines, charts, code,
  terminal, screenshots, UI focus, and simple SVG.
- MP4 B-roll, transparent images, PNG sequences, and pre-rendered clips.
- Voice, SFX, BGM, transitions, and final delivery.

Prefer frame-driven React components. Keep all media under the generated
project's `public/` directory and reference it from `video-plan.json`.

## Specialized asset producers

Use a specialized producer for one bounded deliverable when needed:

- Hand-drawn explanation clip or B-roll.
- Transparent sticker/character animation.
- SVG/logo reconstruction or procedural line animation.
- 3D globe, route, ticker, chat, or other proven procedural visual.
- A complex HTML/CSS/GSAP/WebGL scene that is not reasonable to port.

For difficult browser-based scenes, prefer pre-rendering a transparent or
ordinary clip and integrating it into Remotion. Do not create a parallel
feature-length timeline.

## Handoff contract

Specify:

- Scene ID and exact duration.
- Pixel dimensions and FPS.
- Required alpha, codec, or image-sequence format.
- Visual intent and primary attention target.
- In/out state for the transition.
- Expected file path under `public/`.
- Acceptance checks and a fallback.

Accept only an asset or a bounded component. Keep global time, captions, and
mix ownership in the master plan.

## Fallbacks

If an external result fails, substitute in this order:

1. Static image with native Remotion camera movement and annotations.
2. Ordinary B-roll with crop, highlight, or overlay.
3. Simplified native Remotion scene.

Continue the full video unless the missing result is essential to factual
accuracy or the requested concept.
