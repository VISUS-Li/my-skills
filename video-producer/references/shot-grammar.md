# Shot Grammar

Pick named recipes before coding. Each shot must have a recipe, visual owner, action list, and transition reason.

## Recipes

### `dark_grid_intro`
- Use for: opening hook, tool/world setup, developer mystery.
- Duration: 2-4 seconds.
- Elements: dark grid, large keyword actor, small proof thumbnail, pulse line.
- Motion/SFX: scale-blur keyword, grid pulse, soft pop, short whoosh.
- Errors: starting with a long subtitle; too many competing words.
- Renderer: Remotion or HyperFrames.

### `light_grid_concept_board`
- Use for: definitions, system maps, concept split.
- Duration: 3-6 seconds.
- Elements: light grid, cards, arrows, labels, small icons.
- Motion/SFX: card draw, arrow stroke, click.
- Errors: static diagram with no build sequence.
- Renderer: Motion Canvas, SVG/GSAP, HyperFrames.

### `terminal_proof`
- Use for: commands, install/run proof, logs, errors.
- Duration: 3-7 seconds.
- Elements: terminal window, command line, cursor, output highlights.
- Motion/SFX: typing ticks, line reveal, redbox/caret focus, click.
- Errors: tiny unreadable terminal, command pasted all at once.
- Renderer: Remotion or HyperFrames.

### `editor_code_zoom`
- Use for: code cause/effect, generated file, API call, config.
- Duration: 3-8 seconds.
- Elements: editor chrome, file tree, code highlight, minimap hint.
- Motion/SFX: push-in, line highlight, token glow, keyboard tick.
- Errors: entire code file on screen; no highlighted line.
- Renderer: Remotion, Motion Canvas, SVG/GSAP.

### `screenshot_pushin_redbox`
- Use for: product proof, UI evidence, web page claims.
- Duration: 3-6 seconds.
- Elements: screenshot, browser/device frame, redbox, cursor, label.
- Motion/SFX: slide/crop in, push-in, redbox draw, click/marker.
- Errors: raw screenshot centered with no guidance.
- Renderer: Remotion or HyperFrames.

### `phone_chat_sequence`
- Use for: user workflow, chat agent interaction, before/after prompt.
- Duration: 4-8 seconds.
- Elements: phone mockup, chat bubbles, input cursor, result card.
- Motion/SFX: bubble pop, typing, send click, small hit on answer.
- Errors: too many messages at once.
- Renderer: Remotion, HyperFrames.

### `git_graph_growth`
- Use for: branch, merge, version, snapshot, collaboration.
- Duration: 4-8 seconds.
- Elements: nodes, branch lines, commit labels, diff cards.
- Motion/SFX: node pop, line draw, click, light stamp.
- Errors: graph appears already complete.
- Renderer: Motion Canvas, SVG/GSAP, Remotion.

### `timeline_rewind`
- Use for: rollback, history, cause chain, before/after time jump.
- Duration: 3-6 seconds.
- Elements: timeline ruler, playhead, ghost frames, snapshot cards.
- Motion/SFX: reverse whoosh, tick marks, freeze hit.
- Errors: no readable before/after state.
- Renderer: Remotion, Motion Canvas.

### `dashboard_room`
- Use for: metrics, product state, system overview.
- Duration: 4-8 seconds.
- Elements: dashboard cards, chart, table, status pills, cursor.
- Motion/SFX: card stack enter, count-up, click, soft whoosh.
- Errors: fake metrics with no meaning; one-note card wall.
- Renderer: HyperFrames or Remotion.

### `critique_wall`
- Use for: pointing out mismatch, hallucination, weak claim, bad video pattern.
- Duration: 4-7 seconds.
- Elements: evidence thumbnails, red labels, compare line, warning badge.
- Motion/SFX: marker/click, glitch for actual warning, low hit.
- Errors: harsh decoration without evidence.
- Renderer: HyperFrames, Remotion.

### `data_card_compare`
- Use for: numbers, pricing, speed, capability comparisons.
- Duration: 3-6 seconds.
- Elements: two or three cards, number hero, axis labels, source tag.
- Motion/SFX: count-up, card snap, soft hit.
- Errors: numbers without source/context.
- Renderer: Remotion, HyperFrames.

### `svg_metaphor_scene`
- Use for: abstract mechanisms, mental models, hidden systems.
- Duration: 4-8 seconds.
- Elements: simple metaphor object, SVG path, labels, particles used sparingly.
- Motion/SFX: path draw, morph, pop, whoosh.
- Errors: metaphor unrelated to narration.
- Renderer: Motion Canvas, SVG/GSAP, HyperFrames.

### `keyword_actor_pop`
- Use for: key terms, hook phrase, contrast word, conclusion word.
- Duration: 1-3 seconds.
- Elements: one dominant word/phrase, small support symbol.
- Motion/SFX: scale blur, snap, soft pop.
- Errors: full sentence as huge text.
- Renderer: Remotion, HyperFrames, GSAP.

### `before_after_split`
- Use for: transformation, comparison, bad/good example.
- Duration: 3-7 seconds.
- Elements: split screen, wipe divider, labels, synced annotations.
- Motion/SFX: wipe, click, stamp on winner.
- Errors: two sides too similar; no visible change.
- Renderer: Remotion, HyperFrames.

### `workflow_pipeline`
- Use for: tool chain, agent workflow, input-to-output process.
- Duration: 5-10 seconds.
- Elements: nodes, arrows, small screenshots, terminal/code inserts.
- Motion/SFX: node pop, arrow travel, click, whoosh.
- Errors: too many nodes; no current-step focus.
- Renderer: Motion Canvas, SVG/GSAP, Remotion.

### `audio_waveform_sync`
- Use for: showing voice timing, beat alignment, sound design.
- Duration: 2-5 seconds.
- Elements: waveform, beat markers, action ticks, playhead.
- Motion/SFX: tick, pulse, small hit.
- Errors: decorative waveform unrelated to actions.
- Renderer: Remotion, HyperFrames.

### `conclusion_stamp`
- Use for: final take, warning, verdict, CTA.
- Duration: 2-4 seconds.
- Elements: verdict text, proof thumbnail behind it, stamp/seal.
- Motion/SFX: bass hit, stamp, short tail.
- Errors: conclusion text with no visual memory of proof.
- Renderer: Remotion, HyperFrames, GSAP.
