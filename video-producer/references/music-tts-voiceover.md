# Music, TTS, and Voiceover

Use this for narration, TTS, BGM, and music selection.

## Voice-first workflow
1. Lock or draft `script/voiceover.md`.
2. Create `audio/voice_profile.md` with persona, language, pace, pronunciation, and provider.
3. Create `audio/tts_plan.json` with line or paragraph chunks.
4. **IndexTTS2 (preferred for Chinese explainers):** configure `audio/indextts2_config.json`, place reference WAV in `audio/refs/`, run `scripts/indextts2_generate.py`.
5. Generate or record voice → `audio/stems/voice/beats/B*.wav`.
6. **Measure actual timing:** `scripts/measure_segment_vo.py <project> S001` → `segments/S001/vo_timing.json`.
7. Re-scale micro-events: `scripts/build_micro_timing.py <project> S001`.
8. Align captions, storyboard, and segment HTML to **measured** duration (target **5 汉字/秒**, band 4–6).
9. Add music and SFX only after voice timing is known.

## IndexTTS2 (voice clone + TTS)

Load `references/indextts2-voice-protocol.md` for full API details.

- **WebUI:** Gradio at user-provided URL (e.g. `http://host:37191/`).
- **API:** `/gen_single` via `gradio_client`.
- **Reference:** 5–10s clean clip → `audio/refs/narrator_ref.wav`.
- **Batch:** `python scripts/indextts2_generate.py . --segment S001 --concat`.
- **Emotion:** segment vectors in `indextts2_config.json`; default calm explainer.
- **Post-batch:** always run `measure_segment_vo.py` before segment render.

## TTS provider routing
- **IndexTTS2:** preferred for Chinese AI explainers with reference voice clone; local/self-hosted WebUI.
- Human voice: best for brand-critical videos, nuanced emotion, and personal channels.
- OpenAI TTS: strong general option; useful when promptable style, tone, speed, intonation, or multilingual narration matters.
- ElevenLabs: use for premium narration, voice cloning where consent and policy are clear, music/SFX integration.
- Google TTS: strong localization and many voice/language options.
- edge-tts: practical free/local-ish workflow for Chinese drafts.
- Piper: offline/local fallback where quality is acceptable and privacy/cost matters.

Always disclose AI-generated voice when the chosen provider or policy requires it.

## Music selection
Choose music by function, not taste only:
- Hook: pulse, tension, instant context.
- Explanation: minimal bed with room for voice.
- Proof/demo: rhythmic clarity; avoid melody that competes with speech.
- Emotional / documentary: texture and pacing more than beat.
- CTA: short resolution or identity motif.

## Music prompt template
```text
Generate/find an instrumental music bed for a [platform] video about [topic].
Mood: [3 adjectives].
BPM: [range].
Instruments: [list].
Structure: [hook energy] -> [explanation restraint] -> [CTA resolution].
Must avoid: vocals, busy melody under narration, harsh cymbals, copyrighted references.
Duration: [seconds].
```

## Voice performance template
```text
Read in [language/accent]. Tone: [confident / warm / urgent / documentary / playful].
Pace: [fast/medium/slow], with a slight pause after [key phrase].
Emphasize: [keywords].
Avoid: robotic monotone, overacting, excessive breathiness.
```

## Practical mix defaults
- If voice is present, music should be ducked or manually lowered under every sentence.
- Leave space around key words and big reveals.
- Use EQ or choose darker music if narration feels masked.
- For short-form social video, prioritize intelligibility on phone speakers.
