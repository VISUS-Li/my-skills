# Evidence And Asset Sourcing

Use this when gathering, naming, selecting, and binding external assets. Do not use this stage for simple text, boxes, cards, labels, basic charts, or transition shapes that HyperFrames can generate directly.

## Asset Roles

| Prefix | Role | Examples |
|---|---|---|
| `ref_*` | traceable proof | official webpage, news screenshot, app page, table, statement, report |
| `motion_*` | real footage or screen recording | lamp shaking, factory, phone use, driver, app recording |
| `stock_*` | related real-world photo/clip | store, city, charging pile, phone counter, office |
| `gen_*` | generated explanatory plate/mockup | neutral UI mock, mechanism scene, conceptual illustration |
| `chart_*` | data visualization | line, bar, price card, comparison matrix |
| `text_*` | dynamic text unit | keyword, number hero, quote card |
| `svg_*` or descriptive component IDs | annotation/structure | red box, arrow, bracket, connector, mask |
| `ambient_*` | mood or texture | grain, grid, light, paper, desk |
| `hf_*` | HyperFrames-native component | card, phone frame, browser chrome, source slot, mask, transition shape |

Ken Burns on still images is fill, not real footage. Do not call it `motion_*`.

## What Does Not Belong In Asset Generation

Skip `assets/asset_selection_report.json` for material that is purely programmatic and has no sourcing or rights risk:

- text layers and viewpoint cards.
- color plates, cards, simple frames, source-card containers.
- red boxes, arrows, brackets, callouts, focus rings, scan lines.
- simple charts built from known data in code.
- counters, badges, price tags, labels, quote cards.
- CSS/HTML ambient backgrounds.
- transition masks and shape anchors.

Plan these in `visual_sync_plan.csv`, `text_manifest.json`, `beat_timeline.json`, and segment code. Optionally list reusable `hf_*` components in `asset_choreography_manifest.csv` for timing and motion, but do not pretend they are downloaded/generated external assets.

## Selection Criteria

Score candidates in `assets/asset_selection_report.json`:

- relevance: does it directly answer the spoken phrase?
- readability: can the viewer see the detail at final resolution?
- crop safety: can it be cropped without losing title, face, UI, chart axis, source label, or critical object?
- rights: self-created, public-domain/CC, licensed, source screenshot under editorial use, or blocked.
- performance potential: can it establish, focus, highlight, compare, or transition?

Reject assets that are vague, watermarked, unreadable, misleading, or merely atmospheric for an evidence beat.

## Concrete Beat Rule

If the line names a real-world thing, plan a real-world or source-backed asset first. Use generated imagery only when:

- the original cannot be shown safely,
- the scene is abstract or hypothetical,
- the generated plate is clearly illustrative,
- exact Chinese text is rendered programmatically above it.

## Asset Binding

Each visible external asset needs:

- role: proof, scene, mechanism, annotation, text, ambient, transition, sound.
- timing: first on, last on, hold/read time.
- crop/trim policy: `no_trim`, `trim_to_action`, `loop_safe`, `ken_burns_fill`.
- crop anchor: face, title, UI button, ad slot, table row, chart axis, object, or none.
- behavior: entrance, focus behavior, exit/storage.
- SFX affordance: click, tick, stamp, whoosh, chime, silence, no cue.

For HyperFrames-native components, the same behavior belongs in `beat_timeline.json` or `asset_choreography_manifest.csv`; no source URL, crop safety, or rights review is required beyond `self-created`.

## Web And Screenshot Practice

- Capture full context and a readable crop when possible.
- Preserve source URL/title/date in metadata or source card.
- For tables, capture full table first, then a crop or magnifier for the key row/column.
- For comments/social posts, anonymize when needed and do not fabricate public reaction.
- For product pages/prices, preserve currency, date/context, and avoid implying a current price without verification.

When current facts, prices, public figures, laws, product specs, or news are involved, browse or use official/current sources.
