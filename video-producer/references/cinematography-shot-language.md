# Cinematography and Shot Language

Use this when creating `script/storyboard.json`, `script/shotlist.json`, or segment expanded prompts.

## Shot size as narrative meaning

Use shot sizes deliberately:

- Establishing / wide: context, environment, scale, stakes.
- Medium: human clarity, explanation, balanced subject + context.
- Close-up / insert: proof, emotion, data, detail, product feature, key claim.
- Extreme close-up: shock, texture, mystery, micro detail.
- Wide reveal: synthesis, transformation, conclusion.

Even motion graphics should use shot sizes. A chart can have an establishing shot, an insert on a number, and a reveal of the final comparison.

## Camera movement menu

Pick movement based on meaning:

- slow push-in: importance, concentration, intimacy.
- pull-out: reveal system or context.
- lateral track / parallax pan: comparison, exploration, process.
- whip pan: energetic transition or contrast.
- orbital move: complexity, premium tech, product hero.
- rack focus / blur focus: shift attention between layers.
- dolly-in on stack: assembling logic, infrastructure, depth.
- match move: connect two related ideas across scenes.
- snap zoom: social-video emphasis; use sparingly.

## 2D / HyperFrames virtual camera

Simulate camera language with:

- parent container scale/translate.
- foreground elements moving faster than background.
- blur/opacity as rack focus.
- masks as camera wipes.
- depth shadows and z-index layers.
- scale and crop changes as shot-size changes.

## Continuity and edits

Every cut needs a reason:

- new information.
- emotional shift.
- proof/detail.
- contrast.
- rhythm break.
- CTA.

Avoid cutting between nearly identical compositions unless using deliberate jump-cut energy. For continuity, maintain spatial relationships across adjacent shots; if changing angle/composition, make it visually distinct enough to feel motivated.

## Shotlist minimum fields

Each shot in `script/shotlist.json` should include:

- `shot_id`, `segment_id`, `duration_sec`.
- `shot_size`, `camera_angle`, `camera_move`.
- `composition`, `foreground`, `midground`, `background`, `depth_cues`.
- `focal_element`, `text_area_percent`, `asset_ids`, `edit_intent`.

## Shot progression recipes

- Explainer: establish system → insert key detail → reveal simplified model.
- Product: mystery macro → hero reveal → feature inserts → CTA.
- Data: question → chart builds → anomaly insert → conclusion badge.
- Comparison: two-world establish → alternating detail inserts → matrix/reveal.
- Guofeng/history: scroll establish → ink detail → timeline drift → conclusion seal.
