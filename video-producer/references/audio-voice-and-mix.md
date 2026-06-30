# Audio, Voice, And Mix

Use this for prosody, TTS, SFX, music, and mix decisions.

## Prosody First

Create `audio/prosody_plan.csv` before TTS.

Required columns:

```csv
beat_id,segment_id,tts_text,pace,pre_pause_ms,post_pause_ms,emphasis_words,breath_after,tone,allow_disfluency,director_note
```

Guidelines:

- Slow down for evidence, UI, tables, names, unfamiliar terms, and numbers.
- Add a short pre-pause before reveal, contradiction, or black-screen viewpoint.
- Add post-hold after dense proof or a key judgment line.
- Emphasis words should map to visible highlights, text hits, or camera focus.

## TTS Timing

After generating voice:

```bash
python "$SKILL_DIR/scripts/measure_segment_vo.py" "$PROJECT_DIR" S001
python "$SKILL_DIR/scripts/build_micro_timing.py" "$PROJECT_DIR" S001
```

Use measured `vo_timing.json` as timing authority.

## Mix Rules

- Voice is priority 1.
- Use short, light SFX under dense narration.
- Duck music for stamps, hits, or reveals, but never bury voice.
- Avoid whoosh on every cut.
- Use silence deliberately for serious viewpoint or reset beats.

## Cue Sheet

Every cue needs a visible or semantic anchor:

- exact start/duration,
- beat ID,
- sync phrase,
- visual event,
- sound concept,
- gain/fade/ducking,
- rights status or generated asset note.
