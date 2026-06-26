# Director Compiler OS

Use this when the user wants non-PPT, 小白debug/HyperFrames-level, phrase-synced explanatory animation.

## Purpose

The skill must behave like a compiler, not a moodboard generator. Never allow this shortcut:

`script -> broad visual description -> render`

Use this enforced path instead:

`fact-locked script -> narration beats -> director event graph -> sub-second beat timeline -> asset choreography -> audio cue binding -> segment render prompt/code -> QC`

## Compiler stages

1. **Fact lock**: Every factual assertion gets a `claim_id`. The voiceover may be colloquial and dramatic, but claims must trace to source cards and claim ledger rows.
2. **Retention rewrite**: Rewrite the argument into a hook, tension, proof, mechanism, reversal, and takeaway. Use plain spoken Chinese when the video is Chinese.
3. **Beat decomposition**: Split each sentence into 1-4 phrase rows in `script/narration_beats.csv`. A phrase is normally 0.4-1.8s.
4. **Event compilation**: Compile each phrase into 2-8 micro events. Each event has timecode, intent, visual action, asset IDs, motion, camera, SFX cue IDs, and reason why it is not PPT.
5. **Asset actor pass**: Every asset must have a role, behavior, on/off time, entrance, main motion, exit, states, layer, and SFX affordance.
6. **Audio binding pass**: Every important action chooses a cue, silence, or explicit `no_cue`. Cues are anchored to a visual or semantic event.
7. **Implementation prompt/code pass**: Render prompts must include the timestamped event table, not only a style paragraph.
8. **QC gates**: Run project validation, claim lint, beat lint, aesthetic score, audio score, and style-specific score.

## Sentence-to-event density

Use these defaults unless the user requests slower documentary pacing:

- Hook sentence: 4-8 events, 0.2-0.7s spacing.
- Explanation sentence: 3-6 events, 0.4-1.2s spacing.
- Proof/source sentence: 3-5 events, include a citation/source card visual.
- Transition sentence: 2-4 events, include a camera or layout shift.
- Takeaway sentence: 3-5 events, include checklist/build-up/conclusion chime.

A normal explainer sentence must not become one static card. If the voice line lasts longer than 1.5s, split it into micro events.

## Required event fields

Every row in `script/beat_timeline.json` should include:

- `beat_id`, `segment_id`, `start_sec`, `end_sec`
- `narration`, `claim_ids`, `intent`, `beat_type`
- `visual_action` as a specific verb: stamp, scan, slide, morph, draw, pulse, zoom, flip, connect, type, count, wipe, compare, reveal, collapse
- `assets` using IDs from `assets/asset_choreography_manifest.csv`
- `text_ids` using IDs from `script/text_manifest.json`
- `layout_zone`, `camera`, `motion`, `sfx_cue_ids`
- `density_note`, `why_not_ppt`

## Event graph logic

Create `script/director_event_graph.json` for dense videos. Use it to preserve causality:

- `attention_edge`: tells the viewer where to look next.
- `cause_edge`: event B happens because event A happened.
- `proof_edge`: source card or quote supports a claim.
- `audio_edge`: sound reinforces a visual hit.
- `style_edge`: an event exists to match reference-video rhythm.

## Hard stop rules

Do not proceed to segment rendering when any of these are true:

- A factual script has no populated `research/claim_ledger.csv`.
- Voiceover includes unsupported factual claims.
- `script/beat_timeline.json` has fewer beats than `script/narration_beats.csv`.
- Any normal beat holds unchanged for more than 1.5s without a documented deliberate hold.
- Important exact Chinese is baked into a generated image.
- `assets/asset_choreography_manifest.csv` is missing actor behavior.
- `audio/audio_cue_sheet.json` has scene-level cues but no event-level anchors.
