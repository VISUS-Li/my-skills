# Motion And Transition Grammar

Use this when compiling beats into micro-events, animation, and sound.

## Verb-To-Motion Map

| Narration verb | Visual action |
|---|---|
| open / tap | phone frame appears, cursor/tap, page state changes |
| see / notice | scan line, focus ring, magnifier, red box lock |
| rise /涨 | number count-up, line climbs, red label lands |
| fall /降 | number drops, chart descends, green/blue cooling accent |
| compare | split screen, two columns enter before verdict |
| clarify | rumor dims, official source replaces it, label "澄清" lands |
| expose | mask wipe, spotlight, red stamp, zoom into hidden area |
| spread | cards duplicate, map/network expands |
| cost / pressure | bill/card/price stack grows, real-life cutaway slows |
| summarize | clutter exits, one sentence or image remains |

## Micro-Event Types

- `establish`: primary asset enters or scene context appears.
- `focus`: highlight, crop, magnifier, cursor, or camera push.
- `text_hit`: keyword, number, quote, or label lands on spoken word.
- `data_change`: counter, chart, price, or bar changes.
- `compare_shift`: attention moves between sides.
- `evidence_lock`: red box, bracket, source label, stamp.
- `yield`: existing focal object shifts, scales, or dims to make room for an entering keyword/insert without hiding proof.
- `text_store`: earlier flower text shrinks, moves aside, or becomes a chip so the next phrase can take focus without erasing context.
- `camera_move`: push, pull, pan, match move, snap zoom.
- `transition_bridge`: carry anchor into next shot.
- `hold`: deliberate readable or emotional pause.
- `reset`: black/quiet scene, silence, or low-density cut.

One micro-event should have one focal owner. Secondary layers can breathe, but should not compete.

## Preset Registry Contract

Use `assets/templates/micro_animation_palette.json` as the default registry for CapCut-like semantic presets. The plan should call preset IDs, not rewrite GSAP for common moves. The implementation still happens in HyperFrames/GSAP unless the user explicitly asks for a draft-editor workflow.

Preset fields may include:

- `motion_preset_id`: e.g. `entrance.soft_fade`, `entrance.short_slide_down`, `combo.blur_scale_in`, `text.keyword_pop`, `reactive.yield_left`.
- `params`: small overrides such as `distance_px`, `direction`, `duration_sec`, `stagger_sec`, `overshoot`, or `yield_px`.
- `sync_phrase`: narration phrase that the preset should land on.
- `focal_owner`: asset/text/component that owns the move.
- `yield_target`: object that should give way during reactive displacement.

Decision rules:

- Use entrance/exit presets for routine cards, labels, source stacks, and chapter moves.
- Use text presets only for actual emphasis: keywords, numbers, contrast labels, quotes, and viewpoint lines.
- Use reactive/yield presets when a new element must enter but the existing focal owner should remain visible.
- Use text store/yield presets when sequential flower words should accumulate, shrink, or make room instead of disappearing on every new phrase.
- Do not use a flashy preset to compensate for weak material selection. If the beat needs proof, source the proof first.
- If a preset would hide `must_show_detail`, change its direction/zone or reject it.

## Optional Node Safety

Micro-events are beat-specific. Do not run the same selector choreography across all beats unless every referenced node exists in every beat. If a beat has no `.hf-scan-line`, `.proof-img`, `.anim-proof`, or `.anim-diagram`, that beat must not schedule tweens against those selectors.

Implementation rule:

- Each micro-event names a focal owner and concrete selectors/components.
- The builder checks whether optional targets exist before adding a tween.
- Missing required targets are composition errors; missing optional targets are skipped intentionally.
- GSAP target warnings in Review Studio are failed QC, not harmless noise.

When the registry is insufficient and the task requires a complex custom motion grammar, load the external `hyperframes-animation` skill references selectively: start with its rules index for `reactive-displacement` or text/beat rules, and only load a blueprint such as `metric-video-text-pivot` when the segment specifically needs that show -> yield -> pivot structure. Do not load the whole external skill for routine fades/slides.

## Sound Binding

Use sound as punctuation, not wallpaper:

- click/tap for UI action.
- tick for data or scan.
- stamp for verdict, warning, rejection, or lock.
- whoosh for large camera moves only.
- chime for resolution/success.
- low hit/drop for serious reveal.
- silence for viewpoint, shock, or black-screen reset.
- `no_cue` when sound would clutter speech.

Voice is always priority. Duck music/SFX under voice; do not mask key words.

## Transition Design

Before cutting, ask what the eye can follow:

- Can a red keyword become the next title bar?
- Can a price number become a chart endpoint?
- Can an app screenshot slide out and a table slide in from the same direction?
- Can a highlighted ad slot become a red comparison label?
- Can a black-screen viewpoint reset end the evidence sequence?

If there is no useful anchor, use a motivated hard cut: contradiction, time jump, emotional reset, or new chapter.
