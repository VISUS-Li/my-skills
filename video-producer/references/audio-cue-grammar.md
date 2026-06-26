# Audio Cue Grammar

Use this when writing `audio/audio_cue_sheet.json` or SFX prompts.

## Cue schema
Each cue should include:

```json
{
  "cue_id": "S002_HIT_01",
  "type": "sfx_impact",
  "track": "sfx",
  "segment_id": "002_pipeline",
  "start_sec": 18.42,
  "duration_sec": 0.55,
  "sync_anchor": "shot 002B reveal: final workflow layer locks in",
  "role": "mark the reveal without overpowering narration",
  "sound_concept": "tight modern cinematic hit with short reverb tail",
  "search_terms": ["cinematic hit", "soft impact", "logo reveal"],
  "generation_prompt": "short modern cinematic impact, controlled low end, polished tech trailer style, 0.6 seconds",
  "source": "Pixabay / Mixkit / ElevenLabs SFX / owned library",
  "path_or_url": "assets/sfx/002_hit.wav",
  "gain_db": -10,
  "fade_in_ms": 10,
  "fade_out_ms": 80,
  "duck_under_voice": false,
  "priority": 2,
  "rights_status": "needed",
  "status": "planned",
  "notes": "Time by ear after render."
}
```

## Timing patterns
- Transition whoosh: starts 3-8 frames before the cut, peaks at or just after the cut.
- UI click: lands exactly on touch/cursor/text-lock event.
- Data tick: one short tick per meaningful value group, not every frame of number animation.
- Reveal hit: lands on final scale/opacity lock, not at animation start.
- Riser: starts before reveal; impact cue lands at reveal.
- Ambience: starts with scene and fades under transition.
- Sonic logo: lands with final logo/CTA; shorter is usually better.

## Density guidance
For short-form explainers:
- Hook: 2-4 cues in first 8-12 seconds, but keep voice clear.
- Explanation: 1 cue per major visual beat, not every line.
- Data/UI demo: small repeated motifs are acceptable if quiet and consistent.
- Emotional pause: mark intentional silence instead of filling space.
- Ending: one sonic logo or resolved hit, not multiple endings.

## Search term recipes
- Tech comparison: `subtle whoosh`, `digital glitch`, `UI click`, `data tick`, `soft impact`, `tech riser`.
- Product / food: `package crinkle`, `crunch`, `sizzle`, `spice sprinkle`, `whoosh`, `pop impact`.
- Guofeng / history: `paper rustle`, `brush stroke`, `bamboo wind`, `soft gong`, `water ripple`, `seal stamp`.
- Science / health: `soft pulse`, `microscope click`, `liquid drop`, `heartbeat low`, `lab ambience`.
- Logo animation: `particle shimmer`, `logo reveal`, `cinematic sweep`, `soft boom`, `sparkle tail`.

## Cue review questions
- What visual action caused this sound?
- Does it happen at the exact frame where the viewer expects it?
- Does it support the voice, or does it steal attention?
- Is the same sonic motif reused consistently?
- Is the cue necessary, or would silence be stronger?
