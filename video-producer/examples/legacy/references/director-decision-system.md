# Director Decision System

Use this as the controlling creative layer. The question is never "what template fits this beat?" The question is "what does the viewer need at this exact spoken phrase?"

## Beat Function Matrix

| Beat function | Viewer need | Preferred visual owner | Density | Common failure |
|---|---|---|---|---|
| Hook | shock, curiosity, premise | one striking real scene, headline, number, or high-impact card | focused | busy intro collage |
| Event scene | reality and stakes | real footage/photo, CCTV-like clip, location, product, person | medium | icon replacing reality |
| Evidence | proof and trust | app/web/doc/comment/table screenshot in a source-card world | high but readable | screenshot pasted without zoom/highlight |
| Data | scale and trend | number hero, chart, price card, table compare, data chips | high | chart as small decoration |
| Mechanism | understanding causality | HyperFrames diagram, process map, split-screen, device simulation, icon/card system | medium-high | labels without visible action |
| Person/story | empathy and lived impact | real B-roll, face/hands/back view, street, workplace, bill, device in use | low-medium | abstract chart during human moment |
| Contrast | difference and judgment | two-column comparison, before/after, price vs cost, normal vs VIP | medium-high | one side appears too late |
| Transition | orientation | shared color/shape/word/number/motion from previous beat | low-medium | random effect or hard cut |
| Viewpoint | emotional landing | quiet footage, sparse dynamic text, black reset, human cutaway | low | continuing to pile evidence |

## Material Selection Principle

Let content need choose the material:

- Use **real footage/photos** for danger, social reality, people, products, places, work, consumption, and emotion.
- Use **UI/app/web/document/comment/table screenshots** for evidence, dispute, source, wording, membership comparison, official explanation, or public reaction.
- Use **HyperFrames-native generation** for hidden mechanisms, cause chains, market structure, workflow, simple charts, data cards, text cards, quote cards, UI containers, labels, callouts, color fields, and transition anchors.
- Use **dynamic text** for key words, numbers, contrast terms, quotes, hot takes, and final viewpoint lines.
- Use **SVG/HTML/CSS annotations** for red boxes, arrows, brackets, labels, connectors, masks, chart marks, and transition anchors. Do not let them replace real-world subjects.
- Use **charts/data cards** for price, proportion, growth, decline, costs, ranking, and time.
- Use **ambient texture** to create a visual world: grid, grain, desk, map, UI grid, soft light, shadow. It is not evidence, but it prevents empty frames.
- Use **silence/pause/SFX** to make actions land: screenshot paste-in, red-box lock, number jump, stamp, or black-screen reset.

## Director Casting Principle

Treat each beat like a small scene with casting and blocking:

- **Lead actor:** the one thing the viewer must follow now: proof screenshot, face, product, number, chart endpoint, keyword, hand action, document line, or empty silence.
- **Supporting actors:** optional helpers such as icons, chips, source cards, cards, cursors, labels, ambient grids, stickers, or SFX. Cast them only when they clarify, add rhythm, or guide attention.
- **Background world:** optional but usually helpful for normal explainer beats. It can be a grid, desk, source wall, UI surface, street texture, dark reset, or nothing, depending on the scene.
- **Negative space:** also a director choice. Use it for suspense, emotional landing, viewpoint, or to protect readable proof. Do not use it because no visual idea was chosen.
- **Animation:** movement should express action, attention, comparison, transfer, pressure, or transition. Do not animate every layer just to avoid stillness.
- **Text persistence:** when a new keyword/flower-word enters, decide what happens to the previous one: hold, shrink, move aside, stack, store as chip, or exit. Accidental disappearance is not a director decision.

No actor type is required in every beat. No actor type is forbidden in every beat. The director's job is to decide what earns screen time, what stays off screen, and when a previous actor should yield focus to a new one.

## Director-To-Implementation Handoff

Before any segment code is written, the director plan must name:

- the `visual_cast` for complex beats: lead actor, support actors, withheld actors, and reason;
- `text_treatment` and `text_manifest` IDs for expressive text, including span-level emphasis when useful;
- `previous_text_behavior` for sequential flower text;
- `motion_preset_id` / `text_preset_id` for common moves;
- `must_show_detail` and `avoid_zones` whenever text or reactive displacement is near proof;
- the standard builder target: `scripts/build_<segment>_composition.py`.

Do not skip directly from script to `index.html`. If the implementation has no `visual_sync_plan`, `beat_timeline`, `text_manifest`, and `micro_animation_palette` mapping, it is not director-led.

## Visual World Requirement

Do not let HyperFrames-native scenes collapse into text on an empty background. For most explanation/evidence/data beats, build a designed world:

- background bed: off-white grid, dot matrix, paper grain, soft light, desk surface, map, or muted UI grid.
- support actors: icons, chips, mini cards, source stacks, chart fragments, cursor, badges, progress bars.
- depth: foreground annotation, midground proof/card, background texture.
- motion: grid drift, card settle, chart draw, icon tick, cursor tap, red-box lock.

Use sparse black/white text screens only for deliberate hook, reset, or final viewpoint beats.

## Director Decision Fields

Add these ideas to beat planning even if the local CSV has different column names:

- `beat_function`: hook, event, evidence, data, mechanism, person, contrast, transition, viewpoint.
- `audience_need`: credibility, comprehension, proof, scale, empathy, contrast, suspense, closure.
- `visual_owner`: the primary thing the eye should follow.
- `material_mix`: real, screenshot, external_data, hf_chart, hf_diagram, hf_card, hf_icon, dynamic_text, annotation, ambient, silence.
- `visual_world`: e.g. light_grid_workspace, source_desk, data_wall, street_cutaway, black_reset.
- `support_actors`: icons, chips, mini charts, cards, cursor, badges, source stack.
- `density`: sparse, medium, rich, readable_dense.
- `transition_anchor`: color, shape, word, number, object, position, motion, or none.
- `director_risk`: why this could become PPT, empty, generic, misleading, or unreadable.

## HyperFrames vs External Asset Decision

Ask this before asset generation:

- Does it need real-world truth, source provenance, a face/place/product, photographic texture, or copyrighted/rights review? Use external assets.
- Is it text, a simple shape, a label, a card, a frame, a chart from known values, a mask, a highlight, icon, chip, or transition anchor? Generate it in HyperFrames.
- Does the beat need exact timing with the voice? Prefer HyperFrames-native text/shape/chart layers because they can hit the word exactly.
- Would exporting it as PNG/SVG make iteration slower or risk baked Chinese text? Keep it in HyperFrames.

## Examples

- "地震" should first look like a real danger: shaking lamp, room items moving, surveillance clip, news scene. Add minimal text.
- "打开地震预警 App" should show the app or a phone frame. When the line says "广告", push into the ad area and lock a red box on it.
- "普通模式 / 勿扰模式 / VIP" should show the full table, then crop or magnify the relevant row/column as the words are spoken.
- "内存涨价影响手机价格" can move from chip/wafer footage to a rising line, then to a real product page or price card.
- "司机压力" should not stay as a chart. Cut to night road, car interior, charging pile, bill, or tired hand on a steering wheel.
- A normal explainer beat should not be just text on a blank background. Add a light grid bed, source-card container, icons/chips, mini chart, and subtle motion if the topic can support it.
- A strong viewpoint line can remove most material, but that should feel like a deliberate reset after richer evidence or story beats.

## Anti-Template Rule

Do not force every beat to have the same number of layers, the same red box, the same card, the same actor type, or the same transition. A mature edit varies density, material language, layout, and motion according to section function, while maintaining a coherent visual world. The failure mode is not "too few elements" or "too many elements" in isolation; the failure is using elements without a director reason, or leaving the frame empty when the script needs visual work.
