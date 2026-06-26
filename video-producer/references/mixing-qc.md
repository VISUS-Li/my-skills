# Mixing and Audio QC

Use this before final assembly and after rendering.

## Required gates
1. `scripts/storyboard_to_audio_cues.py <project> --overwrite` if no cue sheet exists.
2. Fill cue paths and rights in `audio/audio_cue_sheet.json` and `assets/asset_manifest.csv`.
3. Run `scripts/audio_score.py <project> --fail-under 72`.
4. Generate a mix command with `scripts/ffmpeg_audio_mix.py <project>` when local cue files are available.
5. Render and listen to the first 10 seconds, each transition, each reveal, and the outro.
6. Run final loudness / clipping checks. Use FFmpeg `loudnorm` or a dedicated meter.

## FFmpeg concepts
- Use `amix` to combine multiple audio inputs into one track.
- Use `afade` / `acrossfade` for smooth entrances and exits.
- Use `sidechaincompress` or manual automation to duck music under voice.
- Use `loudnorm` for EBU R128-style loudness normalization with integrated loudness, loudness range, and true peak targets.
- Use `volumedetect`, `astats`, or external meters for diagnostics.

## Listening pass checklist
- Can every spoken word be understood on laptop and phone speakers?
- Are SFX aligned with visible causes?
- Are transition sounds varied enough, or is it repetitive?
- Is there at least one section with restraint/silence?
- Is the BGM emotionally correct for the topic?
- Do bass hits distort on small speakers?
- Does the outro feel intentionally resolved?
- Are all third-party audio rights recorded?

## Fixing common problems
- Voice masked by music: lower music, duck under voice, choose less busy track, or EQ music mids.
- Video still feels empty: add ambience/room tone and quiet tactile Foley, not more loud whooshes.
- Cheap template feel: reduce generic swooshes; use custom motifs tied to visual identity.
- Overwhelming: cut 30-50% of decorative cues; keep only story-linked cues.
- Robotic TTS: rewrite shorter lines, add performance instructions, adjust pauses and punctuation, or record human VO.
