# Director Quality Review

Use this before final render or when a draft feels automated.

## Review Questions

For each important beat:

- Did the key noun, verb, number, contrast word, or emotion word get a visible response?
- Is the visual owner obvious within one glance?
- Is the material type chosen by audience need rather than by a default template?
- Did the director cast the right actors for this beat, and leave out actors that would distract?
- If this is a factual beat, is there a source-backed or real-world asset?
- If this is a screenshot/table, does it establish context, focus attention, and hold long enough?
- If this is a data beat, is the number or trend large enough to matter?
- If this is a person/emotion beat, did the edit slow down and reduce clutter?
- Is SVG helping with annotation/structure instead of pretending to be the real subject?
- Does the transition have a color, shape, word, number, position, object, motion, or sound anchor?
- Does expressive text behave like a timed actor rather than a whole sentence pasted onto the frame?
- When new flower text enters, did previous expressive text intentionally hold, yield, store, stack, or exit instead of vanishing by accident?
- Does flower text use word/span/character hierarchy, outline, stroke, shadow, color, or selective backing according to emphasis instead of one paragraph-level border for everything?
- If a preset is used, does it serve the beat function and land on the intended spoken phrase?
- If a yield/reactive displacement move occurs, does it protect `must_show_detail` and keep the proof readable?
- Does the segment HTML satisfy the Review Studio seek contract: standard root builder, paused timeline, `window.__timelines[segment]`, guarded GSAP targets, and visible runtime errors?
- Across the segment, do layout, material, density, and motion vary with the story instead of repeating one empty/default composition?

## Failure Modes To Flag

- **PPT-like:** centered title, bullets, card stack, no shot-size change, no real material.
- **Empty HyperFrames:** plain background with only text, no designed grid/texture/depth/support actors.
- **Undirected emptiness:** blank space used because no scene was chosen, not because the beat needs suspense, readability, reset, or emotion.
- **Over-cast beat:** footage, screenshot, icons, chips, flower text, chart, and SFX all compete without one clear lead actor.
- **Boring background:** flat color field used for normal explanation without grid, light, cards, icons, chart fragments, or motion.
- **Too SVG:** long sequence of icons, lines, and shapes for concrete events.
- **No reality:** public/social/financial topic has no people, places, products, UI, documents, or B-roll.
- **Flat text:** whole sentence rendered as one same-size subtitle or card.
- **Untimed flower text:** large/stroked/shadowed words appear without sync phrase, hierarchy, or reason.
- **Vanishing flower text:** each new phrase deletes the previous phrase with no director reason, losing useful context and creating empty rhythm.
- **Boxed subtitle habit:** every expressive line is a bordered paragraph instead of span-level scale, color, stroke, outline, or selective backing.
- **Decorative collision:** sticker/keyword/label covers a source label, table row, chart axis, UI button, face, or the declared must-show detail.
- **Wasted HyperFrames:** simple text, boxes, frames, charts, or transition shapes were exported as static assets instead of being generated, timed, and animated natively.
- **Screenshot paste:** evidence shown but no crop, highlight, label, source, or readable hold.
- **Wrong yield:** proof media shifts or scales for style but loses context, crops the detail, or makes the viewer reread while narration has moved on.
- **Preset soup:** repeated fade/slide/pop effects with no semantic difference between evidence, data, emotion, and transition beats.
- **Seek contract failure:** Review Studio口播继续但合成页卡在 `t=0`, usually because JS threw before `window.__timelines[segment]` registered or because the child page relied on `tl.play()`.
- **Raw GSAP selector warnings:** micro-events target nodes that are absent in that beat, such as `.hf-scan-line` or `.anim-proof`, without optional-target guards.
- **Same-scene loop:** many adjacent beats reuse the same layout/material/motion even though the script function has changed.
- **Constant density:** every beat equally busy or equally sparse.
- **No transition anchor:** adjacent shots cut with unrelated colors, motion, layout, and keywords.
- **Emotion overload:** viewpoint/person beats still crowded with charts and callouts.
- **Data hidden:** prices/percentages/rankings stay small or are only spoken.
- **Late proof:** evidence appears after the claim has already passed.

## Pass Standard

A draft is ready only if:

- concrete claims have concrete visuals,
- abstract mechanisms have visible actions,
- text has hierarchy and timing,
- layout mode changes when the beat function changes, without losing a coherent visual world,
- visual actors are cast by beat function rather than forced in or excluded globally,
- named presets, if used, are bound to focal owners and spoken phrases,
- HyperFrames-native components are used for simple programmatic visuals,
- screenshots and tables are directed,
- footage/screenshots/diagrams/text/charts are balanced across the piece,
- backgrounds have a deliberate visual system and subtle motion,
- normal beats include support actors such as icons, chips, cards, charts, or source stacks,
- density changes by section,
- transitions guide the eye,
- sound supports rather than competes with voice,
- the final emotional beat has room to land.
