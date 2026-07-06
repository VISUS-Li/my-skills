# Editorial Shot Language

Use this when designing storyboard, shotlist, density, screenshot treatment, and transitions.

## Shot Types

- **Establishing shot:** gives context, place, system, or table before details.
- **Insert shot:** shows the exact proof/detail: UI button, ad slot, row, number, quote, face, product.
- **Cutaway:** breaks abstraction with reality: worker, driver, shop, room, street, factory.
- **Comparison shot:** keeps both sides visible long enough to judge.
- **Mechanism shot:** builds a system step by step with visible cause and effect.
- **Reset shot:** black, quiet footage, empty frame, or title line to change emotional temperature.
- **Payoff shot:** simplifies after complexity; leaves the viewer with a clear sentence or image.

Even motion graphics should use shot sizes: wide system, close-up number, insert evidence, pull-out conclusion.

## Density Control

Use density as a storytelling tool:

- Hook: focused, high impact, no confusing small text in the first second.
- Event scene: real-world texture first; overlays are minimal.
- Evidence: dense is acceptable, but readable; source, highlight, crop, label, hold.
- Data: dense chart/number/card combinations are acceptable; ensure scale and comparison are visible.
- Mechanism: medium-high; diagram builds in steps.
- Person/story: lower density; slower push, real details, fewer labels.
- Viewpoint: sparse; let typography, silence, or human image carry emotion.
- Transition: low density; one shared anchor should lead the eye.

Avoid a long run of one material language. After several charts, cut to people or products. After several screenshots, give a real scene or simplified diagram. After sparse emotion, return to proof if needed.

## Layout Choice

Choose layout by the beat's job, not by a house template:

- **Regular grid:** best for tables, comparisons, ranked lists, clear mechanisms, and anything where the viewer must scan categories.
- **Vertical stack:** best for phone UI, step-by-step evidence, comment/source stacks, and 9:16 explainers where the eye should travel top to bottom.
- **Asymmetric proof:** best when a screenshot, document, or footage owns most of the frame and text/labels live in one protected side zone.
- **Diagonal or offset composition:** useful for fast hooks, contrast, pressure, or social-video energy, but only if source labels and key details remain readable.
- **Full-screen proof:** use when authenticity matters more than packaging; add annotation, magnifier, or text only where it helps.
- **Sparse reset:** use for viewpoint, shock, or emotional temperature change.

The director plan should name the intended layout in `visual_sync_plan.layout_zone`, `screen_content_desc`, or `beat_timeline.layout_mode`. Avoid repeating the same layout for a long stretch unless the section is intentionally systematic.

## Transition Anchors

A strong transition carries one thing across the cut:

- color: red price becomes red chart label.
- shape: yellow circle becomes highlight bubble.
- number: "¥399" shrinks into chart endpoint.
- word: keyword becomes next title bar.
- object: phone screenshot slides out; table card enters from same direction.
- composition: focal point stays in the same screen zone.
- motion: left-to-right scroll becomes left-to-right timeline.
- sound: stamp hit or click lands on the visual lock.

Use effects only when they support semantic continuity. Hard cuts are fine when they are motivated by shock, correction, or emotional reset.

## Camera Language for 2D/HyperFrames

Simulate editing with:

- slow push-in for importance or emotional focus.
- pull-out for context or system reveal.
- lateral pan for comparison.
- snap zoom for a short social-video emphasis.
- rack focus by dimming/blurring non-active layers.
- mask wipe for reveal.
- match move when one asset becomes another.

Screenshots and proof media should move less than annotations. If the viewer must read it, animate the red box or label, not the entire screenshot.

Exception: use yield/reactive displacement when a new keyword, sticker, magnifier, or insert must enter the frame and would otherwise cover the `must_show_detail`. The proof object may shift 3-8% of frame width/height, scale slightly, or dim a non-critical area, but the move must preserve source labels, table headers, chart axes, faces, UI buttons, and readable hold time. If that cannot be guaranteed, move the text/annotation instead of the proof.

## Anti-PPT Fixes

If a beat feels like a slide:

- replace title+bullets with a spatial relation: table, timeline, map, before/after, stack, device, or source card.
- add one concrete asset for the claim.
- split the shot into establish -> insert -> conclusion.
- introduce a cutaway to real life.
- make text attach to objects rather than float centered.
- use a motivated camera move or transition anchor.
