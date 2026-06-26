# Director Segment Prompt Template

Segment ID: `[Sxx]`
Duration: `[seconds]`
Narrative goal: `[what viewer should understand]`
Emotional beat: `[curiosity / tension / clarity / proof / relief]`
Visual metaphor: `[machine / device / conveyor / scanner / map / lab / black box]`

## Final styleframe

Describe final frame composition before animation:

- Background:
- Midground hero:
- Foreground annotations:
- Text layers from `text_manifest.json`:
- Motion corridor:
- Safe areas:

## Timestamped beat table

| local time | narration phrase | visual action | assets | text ids | motion/easing | SFX cue |
|---:|---|---|---|---|---|---|
| 0.00-0.40 |  |  |  |  |  |  |

## Implementation notes

- Render all exact Chinese as programmatic text.
- Use asset IDs from `asset_choreography_manifest.csv`.
- Use named timeline labels from `beat_timeline.json`.
- Use SFX cue IDs from `audio/audio_cue_sheet.json`.
- No static card may hold longer than 1.8 seconds.
