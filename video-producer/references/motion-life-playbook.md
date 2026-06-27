# Motion Life Playbook

How to make explainer frames **feel alive** — synced to VO, not decoration.

Load with: `references/vo-sync-timing-protocol.md`, `references/layered-composition-depth.md`, `design/micro_animation_palette.json`.

## Core principle

**Every spoken beat = visible motion on ≥3 layers** (background + midground + foreground/HUD).

If the narrator talks for 4 seconds, something must change every **0.3–1.2s** (micro-events).

## Disney / motion-graphics principles (explainer adaptation)

| Principle | Explainer application | GSAP hint |
|---|---|---|
| **Squash & stretch** | stamp badges, icons landing | `scale: 1.2→1`, `back.out(1.4)` |
| **Anticipation** | before stamp / punchline | small `y: 8` wind-up 0.15s |
| **Staging** | one hero focal per micro-event | dim non-active columns |
| **Straight ahead vs pose** | beat clips = poses; micro = straight ahead | timeline labels per beat |
| **Follow-through** | shadow lag, chip overshoot | `"-=0.1"` overlap tweens |
| **Slow in / out** | never linear moves on UI | `power3.out`, `power2.inOut` |
| **Arc** | icons fly in curved path | `motionPath` or `bezier` |
| **Secondary action** | orb drift while card slides | parallel tweens `"<"` |
| **Timing** | heavy = slower; light = snappy | match VO cps |
| **Exaggeration** | VS badges, hot search tag | scale + color pulse |
| **Appeal** | rounded SVG, consistent stroke | design tokens |

Sources: [Adobe 12 principles](https://www.adobe.com/creativecloud/animation/discover/principles-of-animation.html), GSAP timeline sequencing ([Good Fella Lab](https://lab.good-fella.com/blog/gsap-timeline-tutorial)).

## Micro-event grammar (bind to `micro_timing.json`)

| beat_type | Visual | SFX |
|---|---|---|
| `attention_shift` | camera nudge ±2px, spark | pop |
| `semantic_motion` | arrow draw, scan line sweep | tick |
| `transform` | state morph, column highlight swap | data_tick |
| `emphasis` | stamp, scale punch, red flash chip | stamp_hit |

Schedule GSAP at `micro.t` — **never** only at clip start.

## Entrance / exit catalog

Use **different** entrances per beat to avoid monotony:

| Name | Use | GSAP |
|---|---|---|
| `snap_up` | labels | `from {y:40, opacity:0}` |
| `stamp_down` | verdict | `from {y:-80, scale:1.3}` + bounce |
| `slide_left` | source card | `from {x:-60}` |
| `pop_scale` | tags | `from {scale:0}` back.out |
| `draw_stroke` | connectors | SVG `strokeDashoffset` |
| `whip_out` | beat exit (last 0.2s) | `to {x:30, opacity:0}` fast |

Exits: only when next beat changes layout; otherwise **hold + micro-motion**.

## Continuous ambient motion (always on)

These run full segment duration on track 0:

- Grid subtle drift (`background-position` or slow `x`)
- 2–3 gradient orbs (`sine.inOut` yoyo)
- Horizontal **scan line** (top 15% → 85%, repeat)
- Slow **camera push** `scale 1.0→1.05` on `#root`

HyperFrames: ambient disables static-frame dedup — **expected** for rich segments.

## Speed & acceleration motifs

| Motif | When | Implementation |
|---|---|---|
| Speed lines | beat boundary | 3 lines, `opacity 0→0.6→0` 0.25s |
| Motion blur smear | fast tag fly-in | CSS `filter: blur(4px)` decay |
| Ease contrast | punchline | `power4.out` on enter, `power2.in` on settle |
| Stagger cascade | list of brands/chips | `stagger: 0.08` |
| Pulse loop | waiting / tension | `scale 1→1.03` yoyo during clause |

## Mini actors (characters without cringe)

- **32–64px SVG mascot** (robot, document, magnifier) — bob `y: ±6` loop
- **Walker along timeline** — `motionPath` between nodes at 1–2 px/frame
- **Floating icons** at frame corners with independent `rotation` drift

Keep mascots **neutral** for serious news topics.

## GSAP timeline architecture

```javascript
const tl = gsap.timeline({ paused: true, defaults: { ease: "power3.out" } });

// Labels at VO beat starts from vo_timing.json
tl.addLabel("B001", 0);
tl.addLabel("B002", 4.528);

// Beat B001 block
tl.from("#B001 .col", { y: 50, opacity: 0, stagger: 0.1, duration: 0.5 }, "B001");
tl.from("#B001 .vs", { scale: 0, stagger: 0.08, duration: 0.35, ease: "back.out(2)" }, "B001+=0.4");

// Micro events
MICRO.forEach(m => {
  tl.to("#root", { x: m.type === "emphasis" ? 4 : 2, duration: 0.08, yoyo: true, repeat: 1 }, m.t);
});
```

Rules:

- Build timeline **synchronously** at page load (HyperFrames determinism)
- Use **labels** + relative offsets (`"B002+=0.2"`), not floating delays
- `paused: true`; HyperFrames drives `totalTime`

## Audio-visual lock (embedded VO)

Embed segment WAV in composition root:

```html
<audio id="seg-vo" src="s001_vo.wav" data-start="0"></audio>
```

Visual times must match **same** `vo_timing.json` used to cut audio.

## Density lint (self-check)

Before render:

- [ ] Max unchanged hold ≤ **1.5s**
- [ ] ≥ **4 micro-events** per narration beat (or document exception)
- [ ] ≥ **6 SVG/icon assets** visible across segment
- [ ] ≥ **3 z-layers** with motion
- [ ] No beat clip duration deviates from VO > **0.05s**

Run: `python scripts/segment_timing_lint.py <project> S001`

## What “too simple” looks like (reject)

- Single card + caption for full 5s beat
- Only `opacity` fade
- Equal 6s shots with no VO measurement
- No icons; text-only frames
- Static grid background entire segment

## Further reading

- HyperFrames determinism: `hyperframes-core` skill — no `Math.random()` in visuals
- Voice sync fields: `references/voice-synced-animation-design.md`
- Asset actors: `references/asset-choreography-and-frame-density.md`
