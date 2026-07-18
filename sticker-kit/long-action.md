# Image-only long action (no video model)

Use when the user needs **≥8s / ~100–120 unique frames**, multi-phase moves
(e.g. 龟派气功, 御剑长飞, 连招), and **only GenerateImage** is available
(no I2V / video).

Companion to [continuity.md](continuity.md). If a video model appears later, prefer
its Hard path; this doc is the **image-only production path**.

## Why not one full sheet?

One GenerateImage call that paints an entire sprite sheet **does not** create a
timeline. Cells are parallel samples → identity drift + pose teleport get worse
as cell count rises. Sheet is an **export** (`pack_motion.py`), never the motion source.

Allowed one-shot strips: **prototype only** (≤8 cells, light idle). Production = per-frame
or **per-act row** (see below).

## Integrated pipeline (do this)

```
D0  Classify → if long / multi-phase / VFX → Mode D-Long (this doc)
D1  parts.json + Topology + Color lock + style_id
D1b Dual anchors: character_anchor (+ optional vfx_anchor) on #00FF00
D2  acts.json  → expand_stages.py → numbered micro-stages (~100–120 uniques)
D3  Per act, per layer:
      - generate 1 primary take (dual ref: [act_anchor or global_anchor, prev])
      - optional 2nd take into candidates/ (same stages)
      - pick_candidates.py if both takes exist
D4  qa_frames.py --write-bridges → GenerateImage bridges (1–3) → re-QA
D5  merge_acts.py → ordered global sequence
D6  compose_layers.py (character + vfx) if layered
D7  pack_motion.py --hold 1 (prefer real frames; hold≤2 only for pacing)
```

Scripts (this skill `scripts/`):

| Script | Role |
|---|---|
| `init_long_action.py` | Scaffold project + copy act template |
| `expand_stages.py` | `acts.json` → `stages.json` / per-act stage lists |
| `qa_frames.py --write-bridges` | Pose-jump report + bridge job JSON |
| `pick_candidates.py` | Choose lower-jump take per slot |
| `merge_acts.py` | Concatenate act folders → global `ordered/` |
| `compose_layers.py` | Alpha-composite character + vfx by frame index |

## Frame budget (image-only)

| Goal duration @ 12fps | Unique clean poses | Hold | Packed |
|---|---|---|---|
| ~4s (short) | 48–52 | 1 | ~50 |
| **~8–10s (long default)** | **100–120** | **1** | **100–120** |
| ~10s slower read | 80–100 | 2 | ~160–200 |

**Hold does not add action.** Prefer more unique micro-stages.

Split budget across acts (example 龟派气功 ≈ 120):

| Act id | Phase | Unique frames |
|---|---|---|
| `charge` | 站定 → 双手合掌蓄力 | 24 |
| `form` | 掌心能量球成形变大 | 28 |
| `fire` | 推出光束 + 身体后坐 | 36 |
| `recover` | 余波消散 → 收势 | 24 |
| *(bridges)* | QA 失败对之间 | +8–12 reserved |

## Acts file (`acts.json`)

```json
{
  "project": "kamehameha",
  "style_id": "cozy-scrapbook",
  "target_unique_frames": 112,
  "fps": 12,
  "hold": 1,
  "layers": ["character", "vfx"],
  "global_action_family": "kamehameha",
  "acts": [
    {
      "id": "charge",
      "title": "蓄力合掌",
      "unique_frames": 24,
      "action_class": "kamehameha_charge",
      "free_channels": ["arm_angle", "knee_bend", "torso_lean"],
      "vfx": {
        "enabled": true,
        "free_channels": ["seed_scale", "seed_glow_radius"],
        "must_never": ["full beam", "large orb bigger than head"]
      },
      "beat_summary": "hands rise → palms face → small seed appears → seed grows slightly"
    }
  ]
}
```

Rules:

- Each act has **one** `action_class` (no teleport into another class mid-act).
- Act N’s last accepted frame is the **seed ref** for act N+1 frame 1 (plus global anchor).
- Regenerate a whole act if identity collapses; do not “fix” by blending.

## Per-act row generation (not one mega-sheet)

For each act you may optionally generate a **horizontal strip of ≤8 cells** as a
*sketch*, then **discard it for production** and re-derive per-cell with dual refs.
Preferred production path: **one GenerateImage per micro-stage**.

When using a row strip as intermediate:

- Max **8** equal cells, huge `#00FF00` gaps
- Pass `[character_anchor]` (+ layout guide if you draw one)
- Extract cells → treat as **candidates only** → still run QA + bridges

## Micro-stage writing (anti-jump)

For each act with `N` frames, write `N` lines where each line is a **5–15%** delta:

```text
charge/01: arms at sides, knees soft
charge/02: arms lift 10° toward chest
...
charge/24: palms nearly touch, seed pea-sized between hands
```

Prompt every frame with:

- Style Master + Negatives
- Topology + Color lock (INVARIANT)
- FREE channels for **this act only**
- `delta only vs previous: …`
- `SINGLE CRISP POSE; NO motion blur / afterimages / multi-exposure`
- Refs: `[global_anchor, previous_accepted]` (act1 frame1: `[global_anchor]`)

Batch ≤4, visual QA each batch.

## VFX layering (required for beam / orb / aura)

Image models fuse glowing energy into sleeves/hair. Split layers:

| Layer | Contents | Anchor |
|---|---|---|
| `character` | Body, clothes, limbs — **no** beam/orb (or only tiny contact cue) | `character_anchor` |
| `vfx` | Energy seed / orb / beam / impact sparks only | `vfx_anchor` (or empty green + prop) |

Same frame index on both layers = same beat. After cutout:

```bash
python scripts/compose_layers.py \
  --character OUT/character/ordered \
  --vfx OUT/vfx/ordered \
  -o OUT/composited/ordered
```

Character prompts: `NO energy beam, NO glowing orb larger than a pea` during charge early frames.  
VFX prompts: `NO full body, NO face, only energy prop on #00FF00`.

## Candidate pool (optional but recommended)

Per act slot `k`, keep up to 2 takes:

```
acts/charge/takes/take_a/frame_01.png
acts/charge/takes/take_b/frame_01.png
```

```bash
python scripts/pick_candidates.py acts/charge/takes -o acts/charge/ordered
```

Picks the take sequence with lower mean consecutive pair-diff (and fewer ghosts).

## Bridges (mandatory when QA fails)

```bash
python scripts/qa_frames.py OUT/ordered \
  --max-scale-jitter 0.25 --max-pair-diff 0.22 --max-ghost 0.35 \
  --write-bridges OUT/bridge_jobs.json
```

For each `pose_jump` pair `(A,B)`, GenerateImage **1–3** in-betweens with refs
`[global_anchor, A]` and deltas that land toward B. Insert, renumber, re-QA.
**Never** use `interpolate_sequence.py` output as packed cells.

## Pack

```bash
python scripts/pack_motion.py OUT/ordered -o OUT/motion \
  --cell 512 --fps 12 --hold 1 --anchor bottom-center
```

Long actions: `--hold 1` default. Use `--hold 2` only if unique poses already
pass QA but playback feels rushed.

## Checklist (D-Long)

```
- [ ] Confirmed image-only (no video) → this protocol
- [ ] acts.json with budget summing to ~100–120 (+ bridge reserve)
- [ ] character_anchor (+ vfx_anchor if layered)
- [ ] Per-act micro-stages expanded (expand_stages.py)
- [ ] Dual refs; batch≤4; reject ghosts
- [ ] QA + bridges until pair-diff passes
- [ ] Layers composed if needed
- [ ] pack --hold 1 on clean uniques only
- [ ] No monolithic full-sheet as production source
```

## Templates

- `assets/templates/acts_kamehameha.json` — 龟派气功-class
- `assets/templates/acts_sword_fly.json` — 御剑穿云长飞
- `assets/templates/acts_generic_long.json` — blank 4-act scaffold

```bash
python scripts/init_long_action.py --template kamehameha --out ./sticker-kit-output/my-move
python scripts/expand_stages.py ./sticker-kit-output/my-move/acts.json
```
