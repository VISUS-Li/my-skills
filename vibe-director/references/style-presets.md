# Style Presets

Use presets as direction, not as hard templates. Keep the storyboard specific to the actual topic.

## zheda-cat-git-motion

Use for:

- Git
- AI coding
- developer workflow
- terminal, browser, editor, and agent demos
- technical explainers

Visual language:

- Dark or black-and-white grid background.
- Low saturation and high edge density.
- Terminal, editor, browser UI, Git graph, chat bubbles.
- Screenshot zooms and highlights.
- Optional 3D phone or app mockup.
- Analogies such as "Git is not a save button, it is a time machine", iceberg diagrams, Mario/Linux style contrast, branch maps.

Motion:

- Fewer large scene changes, more local motion inside stable scenes.
- Cursor movement, typing, graph growth, zoom-in, callout, highlight, UI state change.
- One small visible change every 1 to 1.5 seconds.

Recommended effects:

- vibe-motion/claude-typer
- vibe-motion/wechat-2d-render
- vibe-motion/svg-assembly-animator
- vibe-motion/ruler-progress-render
- light spotlight title only for punchy openings
- GSAP stagger and DrawSVG path growth

QA emphasis:

- Avoid becoming a static screen recording.
- Keep captions off the code or graph focal point.
- Make every metaphor operational, not decorative.

## ai-chapingjun-system-explainer

Use for:

- AI tool analysis
- product critique
- workflow breakdown
- system explainer
- LLM or agent architecture

Visual language:

- More visual motif changes across sections.
- Blue minimal opening, dark analysis panels, waveform, dashboard, cards, charts, architecture diagrams, product UI, web screenshots, critique interface.
- Each section should feel like a different room in the same system.

Motion:

- More large transitions than `zheda-cat-git-motion`.
- Cards, graphs, dashboards, UI mockups, node graphs, and data waves.
- No long pure-text passages.
- Every narration sentence needs visual action.

Recommended effects:

- kinetic typography
- SVG architecture assembly
- dashboard graph animation
- spotlight reveal
- node graph
- abstract data waves
- HyperFrames data-viz and shader transitions
- Remotion charts for reusable data sections

QA emphasis:

- Distinct section motifs must not feel random.
- Critique panels should add structure beyond repeating narration.
- Use screenshots only when they are readable and legally usable.

## Custom Preset Template

Define:

- topic fit
- visual language
- background system
- object vocabulary
- motion vocabulary
- caption rules
- section transition rules
- recommended registry effects
- fail conditions
