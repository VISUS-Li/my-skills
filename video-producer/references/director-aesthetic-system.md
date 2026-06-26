# Director Aesthetic System

Use this when a video feels empty, generic, PPT-like, visually flat, or insufficiently cinematic.

## Director-first workflow

Before writing video code, answer these five questions in `design/art_direction.md`:

1. **What is the viewer supposed to feel?** Curiosity, urgency, trust, appetite, wonder, tension, relief.
2. **What is the central visual metaphor?** Factory, battlefield, microscope, marketplace, river, constellation, operating room, archive, etc.
3. **What is the world of the video?** Premium dark UI, warm documentary desk, Song-dynasty scroll, lab glass, street-food neon, enterprise war room.
4. **What changes over time?** A messy problem resolves, an object transforms, a map lights up, a stack gets assembled, a character discovers the answer.
5. **What must not happen?** Random icons, text-only cards, unmotivated transitions, generic gradients, unrelated stock footage.

## Aesthetic deliverables

Create or update these before segment production:

- `design/art_direction.md`: director statement, mood, style recipe, palette, camera language, material/texture, asset strategy.
- `design/visual_moodboard.json`: structured references to collect or generate.
- `design/tokens.json`: implementable design tokens.
- `script/storyboard.json`: every segment has visual metaphor, ratio allocation, visuals, assets, and shots.
- `script/shotlist.json`: shot size, camera move, depth layers, edit intent.
- `assets/asset_manifest.csv`: icons/images/B-roll/textures/SFX with rights status.

## Layering rules

A polished frame usually has 3-5 layers:

1. Background: gradient, texture, map, room, screenshot blur, paper, landscape, grid.
2. Midground: main card/object/chart/person/product.
3. Foreground: captions, labels, light streaks, particles, framing elements, bokeh, UI fragments.
4. Motion layer: lines, arrows, data marks, trails, camera move, parallax.
5. Sound/beat layer: whoosh, click, riser, impact, ambient bed.

## Visual hierarchy rules

- Choose one primary focal element per shot.
- Use contrast, scale, and grouping to direct attention.
- Limit each frame to three typography levels.
- If everything is bright, large, or moving, nothing is important.
- Use negative space as a design element, not as empty leftover space.

## Anti-PPT checklist

A scene is too PPT-like if it has:

- centered title + bullets + static card for more than one shot.
- no shot size variation.
- no depth or foreground/background separation.
- no specific images, icons, diagrams, screenshots, products, or textures.
- transitions that only fade between cards.
- too much readable text on screen.

Fix with:

- split the scene into establish/detail/reveal shots.
- add one concrete visual object per claim.
- add camera move, parallax, mask reveal, data morph, or match cut.
- replace bullet points with spatial relationships: before/after, pipeline, hierarchy, map, matrix, stack, timeline.
