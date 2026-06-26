# Assembly and QC

## Timeline Contract

`edit/timeline.json` should describe tracks rather than hard-code one ffmpeg command only:

```json
{
  "ratio": "9:16",
  "fps": 30,
  "resolution": "1080x1920",
  "tracks": [
    {"type":"video","items":[{"src":"segments/001_hook/render.mp4","start":0,"duration":12}]},
    {"type":"overlay","items":[{"src":"segments/001_hook/overlay.webm","start":0,"duration":12}]},
    {"type":"audio","items":[{"src":"audio/voiceover.wav","start":0,"volume_db":0}]},
    {"type":"subtitle","items":[{"src":"edit/captions.srt","start":0}]}
  ]
}
```

## Aesthetic QC

Before final render, run:

```bash
python scripts/aesthetic_score.py . --fail-under 72
```

Revise before final export if the report flags:

- text-only segments.
- missing art direction.
- missing shotlist/camera language.
- asset manifest too sparse.
- no depth layers or camera movement.
- unknown rights for final assets.

## Technical QC Checklist

Create `edit/qc_report.md` with:

- Duration: target vs actual.
- Resolution, fps, ratio.
- Missing files and broken paths.
- Claims without sources.
- Third-party assets with unknown rights.
- Captions: timing, typos, safe-area, readability.
- Audio: clipping, background music level, silence, loudness.
- Visuals: overflow, flicker, black frames, low contrast, title-safe area.
- Platform: cover readability, first 3 seconds, CTA, hashtags.

## Final Assembly Principles

- Build a dry-run command first.
- Do not overwrite final exports without preserving previous approved files.
- Keep source segment renders in `segments/` and final exports in `exports/`.
- Keep editor-specific project files out of final publish package unless requested.
