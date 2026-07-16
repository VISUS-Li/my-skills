# Review Rubric

Run review after the first-slice preview. The goal is to decide whether to repair the slice or scale to the full video.

## Required Checks

1. `first_slice_required`: no full-video implementation before a 20-30 second preview exists.
2. `visual_owner_required`: every narration beat has a visual owner.
3. `micro_action_density`: visible action every 0.8-1.5 seconds.
4. `macro_scene_reset_density`: obvious room/reset every 8-12 seconds.
5. `no_static_text_overuse`: no text-only static frame longer than 1.5 seconds.
6. `proof_choreography_required`: screenshots, code, terminal, browser, and phone views are directed with movement or annotation.
7. `audio_visual_sync_required`: key visual actions have sound cues or intentional silence.
8. `subtitle_not_main_visual`: subtitles are not the only information carrier.
9. `review_studio_generated`: review page exists after preview.
10. `complexity_budget`: first slice stays focused: one style, 3-5 recipes, 1-3 renderers, no more than two delegated slots.

## Script Depth Checks (when deep research path is used)

Run against `outputs/script.md` and research locks before expanding beyond the first slice.  
**Criteria and examples:** only `references/narrative-depth-copy.md`.  
**Research skeleton:** `references/deep-research-and-script.md` + `scripts/validate_research_lite.py`.

### Blockers (fail → repair plan before full video)

1. `causal_river_required` — tip → what happened → jam/unknown → takeaway; story continuity, not topic-bucket menus
2. `instant_comprehension_required` — people/companies/numbers land via background + impact in the same talk turn
3. `oral_chat_required` — read-aloud like telling a friend a story; no gold-sentence / outline / lesson-talk
4. `no_teaching_deconstruction` — ban `你就记` / `别听成黑话` / `别听成` / `你可以把它理解成` / `你就当作` style name-explainers (see `validate_vo_craft.py`)
5. `no_channel_mimicry` — no like/bell/Discord/paid/outro host catchphrases

### Strong guidance (record in failed_checks; usually do not alone block a high visual score)

6. `selective_deep_dig` — at most 1–2 seams get mechanism + scene + return
7. `cast_when_multi_actor` — role/power/pressure + identity bits when actors matter
8. `epistemic_split_preferred` — fact / inference / unknown when mixed
9. `no_clever_framework_spine` — abstract metaphor/tax buckets must not replace the causal river

Items 4–5 are hard content bans when detected; items 6–9 are repair prompts unless they collapse a hard gate above.

## Style Score

Score 0-100:

- 20: reference style match and coherent visual world.
- 20: narration-to-picture binding.
- 15: proof choreography and asset readability.
- 15: motion rhythm and micro/macro action density.
- 10: audio/visual sync.
- 10: subtitles and flower text support the scene without stealing it.
- 10: technical readiness for full-video expansion.

Pass target: 78. Below 78, repair the slice. Below 65, repair the plan before touching renderer code.

Script-depth **blockers** above are plan blockers even if the visual score is high.

## Repair Mapping

- Static: add action events, split long shots, insert camera movement.
- Weak style: change preset, background, recipes, palette, and transition vocabulary.
- Disconnected narration: bind each beat to a visual owner and action.
- Dull proof: add crop, redbox, cursor, zoom, highlight, source label.
- Weak audio: add motivated cues to key visual actions.
- Subtitle-heavy: convert nouns/numbers/processes into visual actors.
- Slow: reduce shot duration and add macro reset.
- Too flashy: remove effects that do not serve a keyword, proof point, or transition.
- Too complex: reduce renderers, merge similar recipes, and keep only delegated slots that are visibly stronger than local implementation.
- Depth blockers: rewrite VO per narrative-depth-copy Three Hard Gates; fix research lock per deep-research-and-script.
- Jargon fog / clever framework / stiff lecture / teaching deconstruction: rewrite for story river + résumé-style name entry; sample 1–2 StorytellerFan transcripts; run `validate_vo_craft.py`.
