# IndexTTS2 Voiceover

Use this reference when `vibe-director` needs Chinese narration generated with IndexTTS2. The implementation mirrors the `video-producer` workflow: config in `audio/`, reference voice in `audio/refs/`, beat-level CSV input, progress JSON, concatenated segment WAV, then measured timing.

## Project Files

Required:

```text
audio/indextts2_config.json
audio/refs/narrator_ref.wav
script/narration_beats.csv
```

Generated:

```text
audio/stems/voice/beats/<beat_id>.wav
audio/stems/voice/voiceover_full.wav
audio/stems/voice/generation_manifest.jsonl
audio/stems/voice/generation_progress.json
audio/voice/<SEGMENT>_vo.wav
segments/<SEGMENT>/<segment>_vo.wav
segments/<SEGMENT>/vo_timing.json
```

Templates bundled with this skill:

```text
assets/templates/indextts2_config.json
assets/templates/tts_plan.json
```

Copy the templates into a video project when starting TTS. The default `base_url` is `http://10.0.221.33:37191/`.

## Health Check

IndexTTS2 is online when:

```text
GET {base_url}config
```

returns HTTP 200. The helper `scripts/indextts2_connect.py` uses the same check and normalizes URLs with a trailing slash.

Minimal check:

```bash
python -c "from pathlib import Path; import sys; sys.path.insert(0, 'scripts'); from indextts2_connect import check_indextts_url, load_base_url; root=Path('.'); base=load_base_url(root); check_indextts_url(base); print(base, 'online')"
```

## Config

Use:

```json
{
  "base_url": "http://10.0.221.33:37191/",
  "voice_reference": {
    "path": "audio/refs/narrator_ref.wav",
    "example_index": 3
  }
}
```

`voice_reference.path` should point to a clean 5 to 10 second WAV. MP3 references may be converted to WAV when FFmpeg is available.

## Beat CSV

`scripts/indextts2_generate.py` reads `script/narration_beats.csv`.

Required columns:

```csv
segment_id,beat_id,narration
S001,S001_B001,Git 不是保存按钮。
S001,S001_B002,它更像代码的时间机器。
```

Recommended columns:

```csv
segment_id,beat_id,start_sec,end_sec,duration_sec,char_count,narration
```

Mapping rule for `vibe-director`:

- Treat a renderable section or scene group as a segment such as `S001`.
- Treat narration clauses as beats such as `S001_B001`.
- Keep beat order identical to the storyboard and scene specs.
- If a scene has multiple narration beats, keep all beats in the same scene's segment and map them back in scene notes.

## Optional Prosody Plan

`audio/prosody_plan.csv` may override TTS text and pauses.

Useful columns:

```csv
beat_id,tts_text,pre_pause_ms,post_pause_ms
S001_B001,Git 不是保存按钮。,0,120
```

## Generate

Generate a whole segment and concatenate it:

```bash
python scripts/indextts2_generate.py . --segment S001 --concat
```

Regenerate selected beats:

```bash
python scripts/indextts2_generate.py . --segment S001 --beats S001_B002 S001_B003 --concat --force
```

Override the service URL:

```bash
python scripts/indextts2_generate.py . --base-url http://10.0.221.33:37191/ --segment S001 --concat
```

## Progress

`indextts2_generate.py` writes progress through `scripts/tts_progress.py` to:

```text
audio/stems/voice/generation_progress.json
```

Expected phases:

- `preflight`
- `connecting`
- `reference`
- `generating`
- `concat`
- `completed`

Beat-level fields:

- `beats`
- `beat_status`
- `completed_beats`
- `current_beat`

Statuses include `running`, `completed`, and `failed`; individual beats use `pending`, `running`, `done`, or `failed`.

## Measure And Align

After TTS:

```bash
python scripts/measure_segment_vo.py . S001
```

This writes:

```text
segments/S001/vo_timing.json
```

Use measured duration to update:

- `storyboard.json` scene start and duration.
- each `scene_spec.json` motion beats.
- caption timings.
- HyperFrames or Remotion timeline durations.

Do not lock final animation timing from planned text duration once measured voiceover exists.

## Review Studio Presets

If a project later connects to a Review Studio like `video-producer`, mirror these preset meanings:

- `indextts_segment`: run `indextts2_generate.py . --segment <SEGMENT> --concat`.
- `indextts_beats`: run selected beat regeneration with `--beats ... --concat --force`.
- `indextts_beats_align`: regenerate selected beats, measure VO, and rebuild timing.

`vibe-director` v1 does not bundle the Review Studio server. Keep the scripts and file contracts compatible so a UI can call the same commands later.
