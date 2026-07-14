# Audio Sync Grammar

Sound cues must have visual motivation. If there is no visible action, use silence or voice emphasis instead of random SFX.

## Cue Map

- `keyword_pop` -> `soft_pop`
- `redbox_focus` -> `click` or `marker`
- `terminal_typing` -> `keyboard_tick`
- `code_highlight` -> `soft_click` or `tick`
- `cursor_click` -> `click`
- `card_stack_enter` -> `soft_whoosh`
- `dashboard_count_up` -> `tick_rise`
- `git_node_pop` -> `node_pop`
- `branch_draw` -> `line_whoosh`
- `major_transition` -> `whip` or `whoosh`
- `timeline_rewind` -> `reverse_whoosh`
- `error_or_warning` -> `glitch` or `low_hit`
- `important_conclusion` -> `bass_hit` or `stamp`
- `phone_message_send` -> `send_click`
- `audio_waveform_marker` -> `tick`

## Timing Rules

- Place cue onset within 0.03-0.08 seconds of the visual action.
- Duck SFX under voice; never cover consonants in Chinese narration.
- Let major transitions breathe with a 0.15-0.35 second pause before or after the line when possible.
- Flower text appears on keyword stress, not after the phrase is over.
- Subtitles may appear slightly before voice, but flower text and proof highlights should hit with the spoken keyword.
- Use silence for serious turns, human-impact beats, or when the visual already has dense information.

## Cue Density

- Developer demo: light-medium, many small clicks/ticks, few bass hits.
- System explainer: medium-high, clicks and card whooshes, glitch only for warnings.
- Git/technical teaching: precise, node pops and typing ticks, no random cinematic booms.

## Common Failures

- SFX without visual action: remove it.
- Big hit on a minor word: downgrade to click or silence.
- Typing ticks under a dense sentence: lower volume or shorten.
- Every transition uses the same whoosh: alternate click, snap, wipe, silence, or shared-object motion.
