# IndexTTS2 Voice Protocol

Use when the user has **IndexTTS2** (Gradio WebUI) for Chinese narration, voice cloning, or batch beat-level TTS.

## When to use

- User provides IndexTTS2 URL (e.g. `http://10.0.221.33:37191/`)
- User wants **reference-audio cloning** instead of cloud TTS
- Project language is **zh-CN** explainer / documentary

## Required project files

| File | Purpose |
|---|---|
| `audio/indextts2_config.json` | base_url, voice ref, emotion defaults |
| `audio/voice_profile.md` | persona, pronunciation, disclosure |
| `audio/tts_plan.json` | segment/beat batch plan |
| `audio/stems/voice/beats/B*.wav` | per-beat WAV from IndexTTS2 |
| `audio/stems/voice/voiceover_full.wav` | concatenated master (optional) |
| `segments/<id>/s<id>_vo.wav` | segment slice for HyperFrames embed |
| `segments/<id>/vo_timing.json` | **actual** durations from ffprobe |

## API discovery (Gradio)

```bash
curl -s http://HOST:PORT/gradio_api/info | jq '.named_endpoints["/gen_single"]'
curl -s http://HOST:PORT/config
```

Primary endpoint: **`/gen_single`**

Typical parameters (IndexTTS 2.0):

1. `emo_control_method` — `"Same as the voice reference"` (default)
2. `prompt` — reference audio filepath (5–15s clean clip)
3. `text` — narration string for this beat
4. `emo_ref_path` — optional emotion reference audio
5. `emo_weight` — 0.65 default
6. emotion vector sliders (Happy…Calm) — segment-tuned
7. generation params: `max_text_tokens_per_segment`, `temperature`, `top_p`, etc.

Returns: audio filepath → copy to `audio/stems/voice/beats/{beat_id}.wav`

## Voice reference workflow

1. **Preferred:** user supplies `audio/refs/narrator_ref.wav` (5–10s, no music, minimal reverb)
2. **Fallback:** fetch built-in example via `/on_example_click` (example index from WebUI config)
3. Store ref path in `audio/indextts2_config.json`
4. Re-use same ref for all beats unless user requests per-segment emotion ref

## Batch generation

```bash
python scripts/indextts2_generate.py <project> --base-url http://HOST:PORT/
python scripts/indextts2_generate.py <project> --beats B001 B022   # single beat retry
python scripts/indextts2_generate.py <project> --concat             # voiceover_full.wav
```

Dependencies: `pip install gradio_client`

## Emotion by segment (suggested defaults)

| retention_role | Calm | Surprised | Notes |
|---|---:|---:|---|
| hook | 0.55 | 0.15 | slightly urgent |
| mechanism / proof | 0.70 | 0.05 | steady |
| twist | 0.50 | 0.20 | tension up |
| takeaway | 0.80 | 0.00 | calm close |

## Sync rule (critical)

**Never** set HyperFrames clip duration from `shotlist.json` equal splits.

After TTS:

```bash
python scripts/measure_segment_vo.py <project> S001
python scripts/build_micro_timing.py <project> S001
```

Composition `data-duration` = sum of **measured** beat WAV durations.

## Rights & disclosure

- IndexTTS2 is user-hosted; log deployment license in `audio/audio_rights_log.md`
- If voice cloned from a real person → require user consent
- Disclosure text in `audio/tts_plan.json` → on-screen footer if required

## Failure modes

| Symptom | Fix |
|---|---|
| `AppError` FileData meta | use `handle_file()` from gradio_client; ref must be valid WAV |
| ref file is HTML/404 | re-download ref; validate `RIFF` header |
| beats too fast vs plan | acceptable if ~5 cps; re-gen with slower emotion or shorter sentences |
| beats too slow | split narration_beats.csv into shorter phrases |
