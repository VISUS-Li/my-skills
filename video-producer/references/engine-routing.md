# Engine Routing

Assign each segment to the smallest reliable engine.

## HyperFrames

Use for:

- Data charts, comparison matrices, scorecards, dashboards.
- Product feature explainers, fake UI demos, website-to-video, app walkthrough visuals.
- Kinetic typography, subtitle emphasis, quote cards, title cards.
- Logo particles, SVG motion, Canvas effects, CSS/GSAP motion.
- Transition cards and chapter markers.

Avoid using HyperFrames as the only engine for long talking-head or nuanced documentary edits.

## video-use / editor workflow

Use for:

- Talking-head footage.
- Podcast/interview highlight cuts.
- Removing silences and filler words.
- Generating EDL-style rough cuts.
- Syncing captions to real speech.

## FFmpeg

Use for:

- Deterministic concat/overlay/transcode.
- Audio mix and loudness normalization.
- Burning captions.
- Exporting platform ratios or variants.

Prefer generating commands and dry-runs before overwriting output files.

## Remotion

Use for:

- React component video templates.
- High-volume batch rendering.
- When your visual system already exists as React components.

## Manual editor

Use for:

- Copyright-sensitive footage.
- Emotionally precise music/editing rhythm.
- Final human taste pass.
- Brand-critical launch videos.

## Routing Field Example

```json
{
  "id": "003_tool_matrix",
  "type": "comparison_chart",
  "engine": "hyperframes",
  "duration_sec": 24,
  "requires_review": true
}
```
