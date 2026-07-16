# Continuity & anti-morph rules (Mode D)

These rules exist because image models **merge lookalike parts** across frames (e.g. spatula handle absorbed into wok as a permanent pan handle; limb count changes; wheels appear/disappear). Treat this as a first-class failure mode for **any** subject/action.

## Invariant vs free (critical)

Before generating, split attributes into two lists. Every frame prompt must include both.

| Channel | May change across frames? | Examples |
|---|---|---|
| **FREE (motion only)** | YES | joint angles, limb pose, jump height, weapon swing arc, squash/stretch of soft action lines |
| **INVARIANT (identity)** | NO | part colors, outline thickness, costume colors, hair color, number of limbs, which part is which, face placement, materials |

**Rule of thumb:** if it is not posed by the action stage, it must not drift.  
Color flicker (sage handlebars → red handlebars) is a **hard fail** — discard & regen. Same for sudden recolors of hair, shoes, weapon, or vehicle parts.

Write Color Lock as hex / plain names and paste into every prompt:

> Color lock (INVARIANT): hair=#3D3429, jacket=#E85D4C, pants=#5B7C99, shoes=#F5F0E6, sword blade=#C0C6D0, sword grip=#8B5A2B — never recolor.

## Mandatory before any motion generation

Lock **`style_id`** from [styles.md](styles.md) (default `cozy-scrapbook`) and keep it identical for the whole clip. Mid-job style changes require a new anchor.

Write a **Part Inventory** (save as `SUBJECT/parts.json` and paste into every prompt):

```json
{
  "subject": "short name",
  "style_id": "cozy-scrapbook",
  "must_always_exist": [
    {"id": "body", "desc": "...", "attach": "core", "color": "#..."},
    {"id": "tool_a", "desc": "SEPARATE movable tool — never fused to body", "attach": "held/resting", "color": "#..."}
  ],
  "must_never_appear": ["extra handles", "second tool", "text labels"],
  "lookalike_warnings": [
    "tool_a.handle must NEVER be redrawn as a body-mounted handle"
  ],
  "color_lock": {
    "part_id": "#hex or named color — INVARIANT"
  },
  "free_channels": ["pose", "limb angles", "weapon swing", "vertical hop"],
  "topology_lock": "exactly N wheels, M handles, K limbs — constant every frame"
}
```

Also invent a one-line **Topology Sentence** reused verbatim in every frame prompt, e.g.:

> Topology lock: ONE wok body + ONE small LEFT rim loop only + ONE separate spatula with its OWN wooden handle; spatula is NEVER a wok handle; wok has NO long side handle.

## Anchor rules (stronger)

1. Neutral pose where **every inventoried part is visible and unambiguously separate**.
2. If two parts look similar (two wooden sticks, two tubes, antenna vs sword), make them **visually distinct in the anchor** (different color, thickness, end-cap shape) so later frames cannot swap them.
3. Prefer “disassembled clarity” over cinematic overlap in the anchor.
4. Reject anchors that already fuse lookalike parts.

## Frame count & timing (avoid fast/jumpy loops)

**Default delivery target: ~48–52 frames**, each a **separately generated single pose**.  
Do **not** reach ~50 by blending / morphing two poses into one image.

| Difficulty | Generated frames (each = one clean pose) | Preview FPS | Goal duration |
|---|---|---|---|
| Light | 24–32 | 10–12 | ≥2.5s |
| Medium (default) | **48–52** | 12 | ≥4s |
| Hard (I2V extract) | extract 48–64 clean frames | 12–15 | ≥4s |

- Prefer **more GenerateImage micro-poses** over raising FPS on sparse keys.
- List **every micro-stage** before generating; each stage = **tiny delta** from previous (≈5–15% limb travel).
- **Pose-class lock**: pick one action class for the whole clip (`run_cycle` | `slash` | `idle_bob`). A frame that switches class (run → crouch/lunge/hand-on-ground) is a **hard fail**.
- Example bad jump (do not pack): run stride → mid-air leap → three-point crouch → run again.

## One pose per frame (no ghosts) — HARD RULE

Every packed sheet cell must show **exactly one opaque subject pose**.

**Forbidden in generation prompts and in post-process:**
- Motion blur / speed lines that duplicate the body
- Afterimages / ghost trails / multi-exposure / onion-skin look
- Pairwise RGBA **blend** interpolation
- ffmpeg/RIFE morph frames used as **sticker sheet** cells

**Required in every frame prompt:**
> Single crisp pose only. One body, one silhouette. NO motion blur, NO afterimages, NO ghost trail, NO multi-exposure, NO onion-skin.

If a generated image already shows layered ghosts: **discard & regen** — do not pack.

### Interpolation — NOT for production sticker sheets

| Use | Allowed? |
|---|---|
| Final `sheet.png` / `frames/` for HyperFrames-Remotion stickers | **No** — only real generated (or I2V-extracted) clean frames |
| Optional soft video preview the user explicitly asks for | Maybe (label as preview-only; keep separate from `motion/frames`) |

To get ~50 frames: **generate clean poses** (or extract from I2V), then optionally **hold-duplicate** for pacing.  
Never “fake” in-betweens by blending two sticker frames — that creates the ghosting the user rejects.

## Pacing with frame holds (slow motion without ghosts)

If playback feels too fast even with many unique poses, **repeat each accepted frame N times** before advancing (hold).

Example: unique poses `A B C` with `--hold 2` → pack order `A A B B C C`.  
Playback: finish showing A, show A again, then B — slower, still one crisp pose per cell (no ghost).

| Goal | Unique clean poses | Hold | Packed frames |
|---|---|---|---|
| ~50 @ slower pace | 17–25 | 2–3 | ≈50 |
| ~50 denser motion | 48–52 | 1 | ≈50 |

```bash
python scripts/pack_motion.py OUT/ordered -o OUT/motion --cell 512 --fps 12 --hold 2
# 25 uniques × hold 2 → 50 packed frames
```

Prefer hold over blend. Prefer more unique poses when jumps remain; use hold when poses are already continuous but tempo is too fast.

## Derive rules (anti-jump)

1. **Always** `reference_image_paths = [anchor]` at minimum.
2. From frame 2 onward prefer **`[anchor, previous_accepted_frame]`** (dual ref) so topology drifts less.
3. Every prompt must include:
   - Style preset id + Master/Negatives from [styles.md](styles.md)
   - Topology Sentence (verbatim)
   - **Color lock (INVARIANT)** — list each part’s color; say “do not recolor”
   - Part Inventory short form
   - Explicit FREE list: “ONLY change: [pose channels]”
   - Explicit: “do not add/remove/merge parts; do not recolor; only FREE channels may change”
   - Stage micro-diff vs previous (“delta only: spatula rotates +8°, food rises slightly”)
4. Prefer **medium keyframe set** (one image per stage) over sprite-row when lookalike parts exist.
5. Sprite-row only for light motion **and** after a strong inventory lock; still QA every cell.
6. Generate in **small batches** (e.g. 4), QA, then continue — do not fire all 16 blind.

## Post-frame QA (reject & regen)

After each frame (or each batch), **read the image** and check:

- [ ] Every `must_always_exist` part is present
- [ ] No `must_never_appear` part appeared
- [ ] Lookalike warnings not violated (no merge/swap)
- [ ] Limb/wheel/handle **counts** match topology_lock
- [ ] **Colors match Color Lock** (no part recolored — especially lookalike sticks/bars/handles)
- [ ] Subject scale/camera roughly match previous (±20% bbox height)
- [ ] **Pose class unchanged** (still the same action; no crouch/leap teleport mid-run)
- [ ] Motion delta is **small** vs previous (limbs moved a little, not a new stance)
- [ ] Only FREE channels changed vs previous accepted frame
- [ ] **No ghosting** — single silhouette, no afterimage / multi-exposure layers

If any check fails: **discard**, regenerate with stronger Topology + Color lock + dual refs + “delta only from previous frame” + “single crisp pose, no afterimages”. Do not pack failed frames.

Automated jump gate (silhouette diff; still requires visual QA):

```bash
python scripts/qa_frames.py OUT/ordered --max-scale-jitter 0.25 --max-pair-diff 0.22
```

If `--max-pair-diff` fails between `frame_N` and `frame_N+1`: generate **1–3 bridge frames** with dual ref `[anchor, frame_N]` before continuing.

Optional automated size-jitter gate:

```bash
python scripts/qa_frames.py OUT/ordered --max-scale-jitter 0.25
```

Fails loudly if silhouette height jumps too much (weak proxy — never skips visual QA).

## Known morph patterns (extend mentally to any subject)

| Pattern | Example | Prevention |
|---|---|---|
| Tool handle → body handle | Spatula becomes wok handle | Distinct colors; “SEPARATE tool”; forbid long wok handle |
| Limb merge/split | Arm count 2→1 | Topology “exactly 2 arms” |
| Wheel gain/loss | Car 4→3 wheels | “exactly 4 wheels every frame” |
| Prop teleport | Sword disappears | must_always_exist |
| Style reboot | Colors redefine | Dual ref + “same palette as anchor” |
| Camera pop | Zoom in mid-loop | “same scale, same framing” |
| Tool↔body swap | Spatula handle becomes pan handle | Distinct colors; SEPARATE tool; forbid body-mounted long handle |
| Limb hallucination | Arms/hands appear on vehicles/tools | Explicit “inanimate / NO arms NO person”; reject frame |
| Face drift | Eyes vanish or relocate | If anchor has a painted face, inventory it and demand every frame |
| Unexpected anchor traits | Model invents a face on cargo | Lock invented traits into `parts.json` going forward — never ignore them |

## Delivery

Only pack frames that passed QA. Note regen counts in the handoff so the user knows continuity was enforced.
