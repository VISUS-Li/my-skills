# Layered Composition & Depth

Use when user wants ** richer frames**, **overlap**, **parallax**, or **game-like** hierarchy (NOT dark AAA — light explainer HUD).

## Z-layer model (HyperFrames)

| Track / z-index band | Layer name | Contents | Motion |
|---|---|---|---|
| 0 | `ambient-bed` | grid, gradient orbs, hero plate PNG | slow drift, scan line |
| 1 | `background-actors` | large soft shapes, map silhouettes | parallax 0.3× camera |
| 2 | `midground-cards` | source cards, diagrams, comparison columns | slide, stamp, morph |
| 3 | `foreground-actors` | icons, arrows, stamps, mascots | snap, bounce, follow-through |
| 4 | `hud-ui` | captions, badges, disclaimer | minimal move; always readable |
| 5 | `fx-overlay` | sparks, speed lines, particles (sparse) | short bursts on micro-events |

**Rule:** at least **4 visible depth layers** every beat; **overlap allowed** — cards may cover 10–20% of neighbors for depth. **Fill the frame:** ambient + midground + foreground should together cover **50–80%** of the canvas; use supporting icons, chips, and texture at edges to avoid accidental empty margins.

## HyperFrames implementation

```html
<!-- background track -->
<section data-track-index="0" data-start="0" data-duration="40.763">...</section>
<!-- beat clips track 1+ -->
<section id="B001" data-track-index="2" data-start="0" data-duration="4.527">...</section>
```

Use `position:absolute` + explicit `z-index` from tokens:

```css
.layer-bg { z-index: 0; }
.layer-mid { z-index: 10; }
.layer-fg  { z-index: 20; }
.layer-hud { z-index: 30; }
```

## Parallax camera (subtle)

On `#root` or a `.stage` wrapper:

```javascript
tl.to("#stage", { scale: 1.06, duration: segmentDuration, ease: "none" }, 0);
tl.to(".layer-bg", { y: -20, duration: segmentDuration, ease: "none" }, 0);
tl.to(".layer-fg", { y: 12, duration: segmentDuration, ease: "none" }, 0);
```

Micro-beats: `x: ±4` shake on emphasis events (from `micro_timing.json`).

## Game-adjacent patterns (light explainer)

Borrow **HUD grammar**, not fantasy art:

| Pattern | Explainer use |
|---|---|
| Floating chips | keyword tags, brand names |
| Corner brackets | focus frame on evidence |
| XP-style progress | timeline fill, chapter roadmap |
| Hit sparks | micro-event on stamp |
| Speed lines | transition between beats (0.3s) |
| Mini walker mascot | 32–64px SVG icon with bob walk between nodes |

## Overlap & collision

- Allow **intentional** overlap: front card casts shadow on rear card
- Use `data-layout-allow-overflow` on HyperFrames inspect when entrance anim exceeds box
- Keep caption pill **never overlapped** by motion (bottom safe zone 10%)

## Style search workflow

Before coding segment:

1. Web search: `"[主题] 信息图 动效 设计"` / `"科普 HUD 界面"` — **中文 query 优先**
2. Save 3 references to `design/visual_moodboard.json` (URLs + notes)
3. Extract: palette, corner radius, shadow depth, icon stroke — **not** literal copy

## Composition checklist (per beat)

- [ ] Background still moving (orb/scan/grid) — never static >0.8s
- [ ] Midground primary actor changes state
- [ ] Foreground accent (icon/stamp/arrow) animates — **≥2 foreground accents** on dense beats
- [ ] HUD caption updates
- [ ] Optional FX on micro-event only
- [ ] **≥5 distinct assets visible** on screen (excluding caption text)
- [ ] No accidental empty quadrant — fill with texture, grid, or small icons

## Anti-patterns

- ❌ Flat single-layer centered text
- ❌ All elements same scale entire segment
- ❌ Full-screen opaque overlay blocking grid
- ❌ Z-fighting: two elements same z-index flickering
