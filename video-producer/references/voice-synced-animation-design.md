# Voice-Synced Animation Design

Use this when building a video where every sentence should have a corresponding visual and sound cue.

## Chinese pacing rule

- **Planning target:** ~**5 Chinese characters per second** (one short clause ≈ 1s).
- **Authority after TTS:** `segments/<id>/vo_timing.json` from `measure_segment_vo.py` — never equal shot splits.
- **Acceptable band:** 4–6 cps per beat; lint flags outside 3.5–7.5.
- Segment composition duration = sum of measured beat WAV durations (±0.05s).

Load `references/vo-sync-timing-protocol.md` for the full measurement pipeline.

## Timing method

1. Generate TTS beats → measure with ffprobe → write `vo_timing.json`.
2. Scale `beat_timeline.json` micro-events → `micro_timing.json`.
3. Split voiceover into phrase beats, not just paragraphs.
4. For each phrase, mark the semantic verb: show, compare, enter, transform, reject, reveal, prove, summarize.
5. Create a visual response for that verb **on ≥3 layers** with motion at micro-event times.
6. Create an SFX decision for the visual response: hit, click, tick, whoosh, stamp, chime, silence, or no cue.
7. Render with a programmatic timeline (GSAP labels + absolute `t`) so timestamps track VO without rewriting scenes.

## Cue timing defaults

- Subtitle pop: 40-80ms before or exactly on the spoken phrase.
- UI tap / card snap: on consonant or emphasized word.
- Arrow pulse / data tick: starts 80-150ms after the visual appears.
- Stamp hit / error badge: on the word expressing failure/error/不行/错/鬼画符.
- Success chime: 100-180ms after green tick appears.
- Whoosh: starts 80-120ms before a large camera/scene move and ends after movement settles.
- Silence/drop: 0.2-0.5s before a major reveal or title reset.

## Mix rules

- Voice remains priority 1.
- Dense speech: use high-frequency-light, short SFX under -16 dB to -22 dB.
- Big stamp/hit: duck music briefly, not voice.
- Avoid a whoosh on every cut; use clicks/ticks/snaps for small information beats.
- Design a motif: e.g., robot blink tick, vector pulse, red stamp thud, green check chime.

## Sync fields for cue sheet

Every cue should include:

- `start_sec`, `duration_sec`, `segment_id`, `beat_id`.
- `sync_anchor`: exact visual event and spoken phrase.
- `sound_concept`: sound in plain language.
- `generation_prompt` or `search_terms`.
- `gain_db`, `fade_in_ms`, `fade_out_ms`, `duck_under_voice`.
- `rights_status` and source/candidate path.
