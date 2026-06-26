# Sound Design System

Use this when a task mentions audio, SFX, BGM, music, TTS, voice, ambience, mixing, or when the video feels flat despite acceptable visuals.

## Director-level principle
Treat sound as a parallel storyboard. Every important visual beat should have one of these explicit choices:

1. **Sound hit** — a deliberate cue supports a cut, reveal, UI action, impact, product movement, number change, or CTA.
2. **Sound bed** — music, ambience, room tone, texture, drone, or rhythm supports the scene without calling attention to itself.
3. **Intentional silence** — absence of sound is used for contrast, tension, comedy, or emphasis.

Never add a whoosh to every cut. Good sound design is selective: it clarifies hierarchy, creates tactile movement, and makes the video feel edited rather than decorated.

## Layer stack
Use this priority order when planning and mixing:

1. **Voice / dialogue**: always intelligible; all other layers duck around it.
2. **Narrative SFX / Foley**: cues tied to story actions, important reveals, product moves, UI actions, or data changes.
3. **Music**: emotional pacing and continuity; never compete with voice.
4. **Ambience / texture**: space, world-building, subtle depth.
5. **Decorative ear candy**: sparkle, glitch, swells, micro-hits; use sparingly.

## Cue types
- `voice`: recorded human voice or TTS narration.
- `music`: BGM, stems, loops, rhythmic pulse, intro/outro motif.
- `sfx_transition`: whoosh, swish, whip, glitch, reverse, riser into scene changes.
- `sfx_impact`: hit, boom, braam, stamp, pop, logo reveal.
- `sfx_ui`: click, tap, tick, type, data blip, notification, cursor movement.
- `foley`: hand, object, fabric, food, packaging, footsteps, page turn.
- `ambience`: room tone, office, rain, crowd bed, wind, lab hum, guofeng paper/brush texture.
- `silence`: marked intentional gap; prevents agents from filling every space.
- `sonic_logo`: short final identity sound.

## Required artifacts
Create or update these before final assembly:

- `audio/audio_style_guide.md`: sonic identity and rules.
- `audio/music_brief.md`: BGM role, energy arc, search/generation prompts, rights.
- `audio/voice_profile.md`: voice persona, TTS provider, pronunciation dictionary.
- `audio/tts_plan.json`: line-level TTS generation plan.
- `audio/audio_cue_sheet.json`: cue timing, role, sync anchor, gain, rights, source.
- `audio/sfx_search_queries.json`: search/generation prompts by cue.
- `audio/audio_mix_plan.json`: track priorities, gain defaults, ducking, loudness.
- `audio/loudness_targets.json`: delivery profiles.
- `audio/audio_rights_log.md`: third-party asset proof.
- `edit/audio_qc_report.md`: audio gate result.

## High-quality placement heuristics
- Put SFX on **visible cause**: object enters, number lands, UI clicks, chart completes, logo locks up, camera accelerates, scene changes.
- Use **anticipation** for big reveals: a short riser or reverse swell can start before the visual hit; the impact lands exactly on the reveal.
- Use **micro-SFX** for tactile detail: type ticks, tiny clicks, food crackle, paper brush, button press.
- Use **ambience** to remove emptiness: low-level room tone, office hum, rain, street bed, paper texture, lab drone.
- Use **silence** before important lines: 200-600 ms of reduced music/SFX often makes the next line feel stronger.
- Use **motifs**: repeat a recognizable UI click, data tick, brush stroke, or brand shimmer across the video.
- Use **contrast**: do not keep constant high-energy music; create sections of restraint and release.

## Anti-patterns
- SFX on every text reveal.
- Loud whoosh on small movements.
- Music too bright under narration.
- Using only BGM and no tactile SFX.
- Using SFX with unknown rights in final output.
- No room tone or ambience under generated scenes.
- TTS with no pronunciation pass.
- Final mix normalized by peak only, with no loudness/true-peak check.
