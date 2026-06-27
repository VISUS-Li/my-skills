# Voice Profile

## Narrator persona
- Persona:
- Language / accent: 普通话
- Energy: 6–8 / 10（解说型，非播音腔）
- Pace: **5 汉字/秒**（规划）；以实测 WAV 为准
- Emotional range:
- Delivery notes:

## TTS provider plan

- **Preferred:** **IndexTTS2**（Gradio WebUI + 参考音克隆）
- **Config:** `audio/indextts2_config.json`
- **Reference audio:** `audio/refs/narrator_ref.wav`（5–10s，无 BGM）
- **Batch script:** `python scripts/indextts2_generate.py . --segment S001 --concat`
- **Fallback:** edge-tts / 人声录制
- **Output:** `audio/stems/voice/beats/B*.wav` → `voiceover_full.wav`
- **AI voice disclosure:** 见 `audio/tts_plan.json`

## Post-TTS sync (required)

```bash
python scripts/measure_segment_vo.py . S001
python scripts/build_micro_timing.py . S001
python scripts/segment_timing_lint.py . S001
```

## Pronunciation dictionary
| Term | Pronunciation / note |
|---|---|

## Line-level performance notes
| Beat / time | Performance instruction |
|---|---|
