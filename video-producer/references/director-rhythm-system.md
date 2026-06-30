# Director Rhythm System

Use this for pacing, voice-to-picture alignment, asset selection, and motion choreography. It is the controlling protocol for videos that feel too fast, too slow, poorly aligned, visually piled up, or AI-like.

## 1. Rhythm Is Comprehension Time

Do not measure rhythm only by cut frequency. A beat needs enough time for four things:

1. **Hear** - the spoken phrase is intelligible.
2. **Find** - the viewer's eye finds the focal object.
3. **Read** - text, UI, charts, or evidence can be understood.
4. **Absorb** - the meaning lands before the next idea.

Use `script/rhythm_map.json` to record these decisions.

### Timing Defaults

| Beat type | Speech feel | Visual behavior | Typical rule |
|---|---|---|---|
| hook | tight, energetic | fast entrance + clear focal object | no confusing detail in first 1s |
| proof | slower, anchored | source/evidence appears before or with claim | hold 1.0-2.5s depending on readability |
| mechanism | steady | diagram builds step by step | show the verb, not just a label |
| comparison | paced | both sides visible before verdict | do not switch before contrast is readable |
| reveal/twist | pause then hit | short pre-pause or scene reset | silence can carry the beat |
| transition | quick | bridge from previous visual to next | do not introduce new evidence here |

### Rhythm Fields

`script/rhythm_map.json` should contain one row per narration beat:

```json
{
  "beat_id": "B003",
  "segment_id": "S001",
  "narration": "注意，它这里说的不是所有用户。",
  "spoken_focus": "不是所有用户",
  "beat_type": "proof",
  "information_density": "high",
  "planned_duration_sec": 2.1,
  "min_visual_read_time_sec": 1.4,
  "visual_lead_in_sec": 0.15,
  "post_hold_sec": 0.35,
  "pace": "slow",
  "focal_owner": "ref_terms_source_card",
  "scene_reset": false,
  "director_note": "Source card enters before the限定词 is spoken; highlight holds after the sentence."
}
```

## 2. Prosody Comes Before TTS

Do not send raw narration directly to TTS when quality matters. First create `audio/prosody_plan.csv`.

Required columns:

```csv
beat_id,segment_id,tts_text,pace,pre_pause_ms,post_pause_ms,emphasis_words,breath_after,tone,allow_disfluency,director_note
```

Rules:

- Add 120-250ms `pre_pause_ms` before a reveal, correction, or source quote.
- Add 180-450ms `post_pause_ms` after dense proof, a punchline, or a visual reset.
- Use `pace=slow` for evidence, UI walkthroughs, numbers, names, and unfamiliar terms.
- Use `pace=quick` for connective phrases only if the picture is already clear.
- Use disfluency sparingly. Prefer natural short clauses over fake filler.
- Emphasis words should map to visible highlights or camera focus.

TTS generation may include silence padding around each beat. After any TTS regeneration, rerun measurement and micro-timing.

## 3. Visual Sync Is Semantic, Not Just Asset IDs

Every narration beat needs a visual contract in `script/visual_sync_plan.csv`.

Required columns:

```csv
beat_id,segment_id,spoken_focus,visual_intent,visual_subject_desc,screen_content_desc,must_show_detail,source_visual,asset_ids,visual_read_time_sec,focal_owner,layout_zone,pre_show_sec,post_hold_sec,mismatch_risk,acceptance_check
```

Use plain Chinese descriptions. The agent should be able to answer:

- What does the narrator say?
- What exactly is on screen?
- What detail must the viewer notice?
- Does this picture prove, explain, compare, or only decorate?
- How long must it stay visible?

If `spoken_focus` mentions a concrete entity, `source_visual` must bind a concrete asset: `ref_*`, `stock_*`, `gen_*`, `motion_*`, or a valid `ref_embed`.

## 4. Asset Selection Before Asset Use

Create `assets/asset_selection_report.json` before final asset binding. This is a judgement layer, not just a manifest.

Each candidate should include:

```json
{
  "asset_id": "ref_product_settings",
  "beat_ids": ["B006"],
  "source_url": "https://...",
  "content_description": "产品设置页截图，左侧导航和右侧开关清楚",
  "relevance_score": 5,
  "readability_score": 4,
  "crop_safety_score": 5,
  "rights_status": "self-created",
  "watermark_risk": "low",
  "trim_policy": "no_trim",
  "crop_anchor": "right settings toggle",
  "selected": true,
  "reject_reason": ""
}
```

Scoring:

- `5` = directly supports the line and is safe to show.
- `4` = useful with a crop, label, or source card.
- `3` = acceptable only as secondary support.
- `1-2` = do not use unless there is no alternative.

Selection rules:

- Do not crop away faces, document titles, UI buttons, chart axes, subtitles, logos, or source labels when those are the point of the beat.
- Use `no_trim` for still evidence that must be read.
- Use `trim_to_action` only when a video has dead time before/after the action.
- Use `loop_safe` for ambient real footage with no critical beginning/end.
- Use `ken_burns_fill` only for still-image filler; do not count it as real footage.

## 5. Composition Before Animation

Before animation, create a static layout that already communicates:

- one focal owner
- clear hierarchy between proof, mechanism, annotation, and HUD
- safe caption area
- enough frame occupancy without clutter
- readable text size and contrast

Layer roles:

| Layer | Purpose | Motion rule |
|---|---|---|
| ambient | canvas, grid, texture, light | slow, never distracting |
| proof | screenshot, document, real footage | stable enough to read |
| mechanism | diagram, machine, pipeline, comparison | builds the explanation |
| annotation | arrows, highlights, stamps, cursor | timed to spoken focus |
| HUD | captions, labels, status | readable, minimal movement |

## 6. Motion Choreography

Motion should reveal logic. It should not make everything busy.

For each micro-event, choose one dominant action:

- `scan` - checking or reading
- `highlight` - important word/detail
- `stamp` - verdict, mistake, failure
- `connect` - causal relation or handoff
- `split` - comparison
- `morph` - transformation
- `type` - UI/code/input
- `count` - numbers or ranking
- `hold` - deliberate comprehension pause
- `reset` - new scene, rhythm break

Rules:

- Only one primary asset performs the dominant action at a time.
- Secondary motion may continue as ambience or follow-through.
- Proof media should move less than explanatory SVGs.
- If a screenshot is being read, animate the highlight, not the whole screenshot.
- Use silence/drop for major reveals; do not whoosh every cut.

## 7. Stage Acceptance Checks

Before render, the agent should be able to say:

- The voice has planned pauses and measured durations.
- Each beat has a spoken focus and a matching visual subject.
- Evidence appears before or with the claim, not after it.
- Dense visuals have read time and post-hold.
- Assets were selected for relevance/readability/crop safety.
- Animation has one focal owner per moment.
- Captions and source cards remain readable.
- QC scripts pass or failures are explained with upstream fixes.

