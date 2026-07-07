# Renderer Selection

Choose the renderer after the storyboard is drafted and before scene code exists.

## HyperFrames

Use when:

- The scene is standalone HTML/CSS/GSAP.
- Fast preview matters.
- Duration is 3 to 20 seconds.
- The shot is typography, UI mockup, card stack, social overlay, chat, simple diagram, kinetic caption, shader transition, or HTML layout.
- The scene can be tested independently through lint, preview, render, and contact sheet.

Avoid when:

- A long timeline needs shared state across many scenes.
- React component architecture is the maintainability center.
- Many props need Studio-style tuning.

## Remotion

Use when:

- The video is multi-scene or long-form.
- It needs a stable timeline, subtitle track, audio track, scene registry, props, or visual editing.
- The scene uses React components, complex SVG, Canvas, Three.js, charts, or data-driven animation.
- The project should be maintained and iterated over time.

Avoid when:

- A tiny isolated HTML scene would be faster in HyperFrames.
- The user only needs a quick single-shot preview.

## vibe-motion

Use when:

- A registry effect already fits the main visual.
- The effect can be rendered as a slot and composed into the video.
- The shot is terminal typing, chat, SVG assembly, logo motion, spotlight text, progress route, earth routes, or 3D ticker.

Avoid when:

- The effect would fight the chosen style preset.
- The scene needs custom narrative timing that the effect cannot expose.

## GSAP

Use GSAP inside HyperFrames, HTML, SVG, or custom web scenes when timing quality matters: timeline orchestration, stagger, CustomEase, DrawSVG, MorphSVG, MotionPath, SplitText, ScrambleText, or scroll-like camera moves.

Prefer GSAP over rigid CSS keyframes for multi-object choreography.

## Manim

Use only for math, algorithms, graphs, coordinate systems, geometric transforms, and proofs where exact geometric construction is the point.

## Custom Code

Use only after checking registry effects and component banks. Keep it reusable, document the reason, and include a fallback renderer.
