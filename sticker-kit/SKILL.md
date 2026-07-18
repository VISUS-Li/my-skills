---
name: sticker-kit
description: >-
  Plan and produce multi-style die-cut stickers, layered animated scenes, and
  continuity-safe motion: storyboard and state timelines, interaction contracts,
  per-element Wan I2V/FLF2V generation, chroma/luma-to-alpha video cutout,
  deterministic z-order/time/position composition, plus static UI sticker kits;
  preset styles (cozy scrapbook default, 8-bit pixel, colorful hex, flat vector,
  kawaii, watercolor, comic ink, neo-pop, clay, risograph, chalk, marker, doodle,
  vintage), identity locks, contact groups, VFX layers, and image-only fallback
  actions (~100–120 frames via acts + bridges). Use when
  the user wants 贴纸, sticker kit, 手绘贴纸风, 8bit/像素, 彩色海克斯, scrapbook UI,
  分镜动画, 多角色场景, Wan图生视频/首尾帧生视频, 元素拆分与合成, 透明视频素材,
  精灵图/帧动画, 连续帧防跳跃, 长动作/龟派气功/御剑, chroma-key, or sticker-kit.
---

# Sticker Kit (+ Layered Wan Motion)

Create static stickers or plan a full scene as **isolated animated element clips**
that are keyed to RGBA and composed on a deterministic timeline.

**Styles (switch anytime):** [styles.md](styles.md) — default `cozy-scrapbook`

Prompt templates: [style-reference.md](style-reference.md)

**Continuity / anti-morph (required for Mode D):** [continuity.md](continuity.md)

**Wan layered-video workflow (default for narrative motion):** [references/wan-layered-video.md](references/wan-layered-video.md)

**Image-only long actions (~100–120 frames, no video model):** [long-action.md](long-action.md)

## Style switcher

1. Default style id: **`cozy-scrapbook`**.
2. If the user picks another preset (id or alias in [styles.md](styles.md)), lock that `style_id` for the whole job.
3. Paste that preset’s **Master** + **Negatives** into every image prompt; regenerate the **anchor** after a mid-job style change.
4. Default chroma is `#00FF00`; choose blue/magenta when that color occurs in the subject. Use black+luma alpha for fire/glow.

| User says… | Resolve to |
|---|---|
| (none) / 暖奶油 / 手账 | `cozy-scrapbook` |
| 8bit / 像素 | `pixel-8bit` |
| 彩色海克斯 / hex | `hex-colorful` |
| 扁平 / vector | `flat-vector` |
| 卡哇伊 / pastel | `kawaii-pastel` |
| 水彩 | `watercolor` |
| 漫画 | `comic-ink` |
| 波普 / neo-pop | `neo-pop` |
| 软陶 / clay | `clay-soft` |
| 孔版 / riso | `risograph` |
| 粉笔 | `chalk-pastel` |
| 马克笔 | `marker-copic` |
| 线稿涂鸦 | `line-doodle` |
| 复古 / 70s | `retro-vintage` |

## Mode router

| User asks for… | Mode |
|---|---|
| Analyze reference video/screenshot style | A |
| Full app screen mockups | B |
| Static sticker kit | C |
| **Multi-element narrative / Wan available** | **D-Wan (default for motion)** |
| Single sprite / generated frames / no Wan | **D-Frames** |
| **Long / multi-phase move and only images** | **D-Long** → [long-action.md](long-action.md) |
| Static + motion | C and/or D-Wan |

Default output: user folder, else `./sticker-kit-output/`.

## Style lock (short)

- Active preset from [styles.md](styles.md) (default cozy scrapbook)
- Stickers/anchors/frames: solid chroma absent from subject; screens: preset Screen bg
- Die-cut readable silhouette; obey preset outline / border / shadow rules
- No photoreal; avoid glass / purple-neon chrome unless the chosen preset allows a controlled accent

---

## Mode A / B / C

- **A:** ffmpeg sample frames → vibe + map to closest preset id + prompts.  
- **B:** research → `9:16` screens with active style lock.  
- **C:** green sheets → `cutout_assets.py --mode green` → `split_parts.py`. Prefer one subject per image.

---

## Mode D-Wan — Layered narrative motion

Read [references/wan-layered-video.md](references/wan-layered-video.md) and
[references/wan-api.md](references/wan-api.md). Do not generate before the scene
plan and interaction contracts exist.

### D-Wan 0 — Plan story, shots, states

1. Convert the brief into story beats and shots. Keep one camera rule per shot.
2. Build an element registry and state timeline. A state contains one semantic
   action; split `attack → fall → rescue` into separate states.
3. Write interaction contracts with shared event times and contact points.
4. Separate local Wan motion from global compositor movement.
5. Save `scene_plan.json`; start from the generic or dragon-rescue template.

```bash
python scripts/init_wan_scene.py --template dragon-rescue --out OUT/dragon-rescue
python scripts/compile_wan_scene.py OUT/dragon-rescue/scene_plan.json --strict-assets
```

### D-Wan 1 — Choose correct element boundaries

- Group an actor with held/worn props (`warrior_sword`).
- Split VFX from bodies (`dragon` + `dragon_fire` + `impact_vfx`).
- Use separate actors for short contacts synchronized by an interaction contract.
- For sustained contact or intertwined limbs, replace the individuals with one
  temporary contact group (`warrior_princess_pair`).
- Keep distant architecture static; animate only layers whose motion reads.

### D-Wan 2 — Create endpoint images and jobs

Generate every endpoint on the same element canvas, same scale, same view, and
same identity/palette. Use a uniform chroma color absent from the subject; use
black for emissive VFX.

- I2V: stable state or loop (idle, breathing, wind, guard).
- FLF2V: controlled state transition (slash, upright→fallen, tied→freed).
- Prompt Wan for local motion only and require a locked camera and centered subject.

```bash
python scripts/wan_generate.py OUT/dragon-rescue/wan_jobs.json --dry-run
python scripts/wan_generate.py OUT/dragon-rescue/wan_jobs.json
```

### D-Wan 3 — Matte and composite

Wan MP4 has no alpha. Convert every clip to an RGBA PNG sequence with one union
crop for the whole clip. Never autocrop each frame independently.

```bash
# Batch uses each job's chroma/luma strategy; pixel-8bit defaults to grid 4.
python scripts/key_wan_jobs.py OUT/dragon-rescue/wan_jobs.json
# Or key one clip manually:
python scripts/cutout_video.py RAW.mp4 -o RGBA --mode chroma --key-color '#00FF00'
python scripts/compose_scene.py OUT/dragon-rescue/compiled_scene_plan.json \
  -o OUT/dragon-rescue/renders/final.mp4
```

Inspect isolated clips before final render. Regenerate only the failing state.
If a contact still fails after two takes, make it a contact group or hide the
join behind a designed VFX/foreground transition.

### D-Wan deliverables

Deliver `scene_plan.json`, `compiled_scene_plan.json`, `wan_jobs.json`, endpoint
images, raw Wan MP4s + metadata, RGBA sequences + key reports, composite frames,
and `final.mp4`.

---

## Mode D-Frames — Image-only continuity fallback

**Never** ship one-shot text-only sprite sheets as production when parts can morph.  
**Always** follow [continuity.md](continuity.md): Part Inventory → Topology Sentence → dense stages → dual refs → visual QA → pack only accepted frames.

### D0 — Classify + budget frames

| Diff | Method | Clean generated frames | Preview FPS |
|---|---|---|---|
| Light | Micro-keys | 24–32 | 10–12 |
| Medium | **Per-stage micro-keys** | **48–52** | 12 |
| **Long (image-only)** | **Acts + bridges (+ VFX layers)** | **100–120** | 12 |
| Hard (if video exists) | I2V extract clean frames | 48–120 | 12–15 |

**Route to D-Long** when any of: user wants ≥8s, ~100+ frames, multi-phase skill move, beam/orb VFX, or complains motion is too short/jumpy — **and** Wan/video generation is unavailable.

Do **not** fake length with `--hold 10` on 8 poses.

Each frame = **one crisp pose** (no afterimages). Pose teleports are hard fails.

**Do not** use blend/ffmpeg interpolate to fill the sheet. Details: [continuity.md](continuity.md), [long-action.md](long-action.md).

### D1 — Anchor + Part Inventory

1. Draft `parts.json` + Topology Sentence + Color lock ([continuity.md](continuity.md)); record `style_id`.
2. Generate anchor on `#00FF00`, **neutral**, every inventoried part **clearly separate**, using active style Master.
3. Cutout; reject fused anchors.
4. Save `anchor_greenscreen.*`, `parts.json`.

### D2 — Derive (anti-morph + anti-jump + anti-ghost)

1. Write micro-stages — one GenerateImage **per stage** (Medium ~48–52; Long → expand from `acts.json`).
2. Each prompt: Style preset + Topology + Color lock + FREE-only + delta-only + action-class lock +  
   **“Single crisp pose only. NO motion blur, NO afterimages, NO ghost trail, NO multi-exposure.”**
3. Refs: `[anchor]` then `[anchor, previous_accepted]`.
4. Batch ≤4, visual QA; **reject any ghosted/multi-exposure image**; regen before continuing.
5. To lengthen: **generate more real frames** or **bridge gaps**, never blend two frames into one cell.

### D-Long — Image-only long action (summary)

Full protocol: [long-action.md](long-action.md).

```bash
python scripts/init_long_action.py --template kamehameha --out OUT/my-move
python scripts/expand_stages.py OUT/my-move/acts.json
# generate per-act frames with dual refs → cutout → ordered
python scripts/qa_frames.py ACT/ordered --max-pair-diff 0.22 --max-ghost 0.35 \
  --write-bridges ACT/bridge_jobs.json
# GenerateImage bridges from bridge_jobs.json → insert → re-QA
python scripts/merge_acts.py OUT/my-move/acts.json --layer character -o OUT/my-move/ordered
# if VFX layer:
python scripts/compose_layers.py --character OUT/char/ordered --vfx OUT/vfx/ordered \
  -o OUT/composited/ordered
python scripts/pack_motion.py OUT/ordered -o OUT/motion --cell 512 --fps 12 --hold 1
```

### D3 — Pack (clean frames only)

```bash
python scripts/cutout_assets.py FRAMES/*greenscreen* --mode green -o OUT/rgba
python scripts/qa_frames.py OUT/ordered --max-scale-jitter 0.25 --max-pair-diff 0.22 --max-ghost 0.35
python scripts/pack_motion.py OUT/ordered -o OUT/motion --cell 512 --fps 12 --hold 1 --anchor bottom-center
```

`interpolate_sequence.py` is **preview-only**; never pack blend output into `motion/frames` or `sheet.png`.  
`--hold 2` only for pacing after uniques already pass QA — **not** a substitute for missing action.

Deliver: `frames/`, `sheet.png`, `manifest.json`, `preview.gif`, `parts.json` (+ `acts.json` / `stages.json` for D-Long).

### D4 — Compositor

HyperFrames (default) or Remotion consume `manifest.json`. Single-sticker bob/scale → Mode C + easing, not Mode D.

---

## Motion checklist

```
- [ ] Mode selected: D-Wan when endpoint video generation is available
- [ ] style_id locked (default cozy-scrapbook)
- [ ] D-Wan: story beats + shots + element state timeline written
- [ ] D-Wan: held props grouped; sustained contacts use contact groups
- [ ] D-Wan: interaction events share exact timing; camera locked in element clips
- [ ] D-Wan: chroma absent from subject; emissive VFX uses black+luma
- [ ] D-Wan: stable union crop; RGBA clips inspected before composition
- [ ] parts.json + Topology Sentence written
- [ ] Anchor shows all parts, lookalikes distinct
- [ ] Budget: Medium ~50 OR D-Long ~100–120 uniques (not hold-padded 8s)
- [ ] Dual ref used after frame 1 when possible
- [ ] Color lock + pose-class lock + no ghosting every batch
- [ ] No pose teleports; no one-shot full sheet as production source
- [ ] qa_frames.py passes (bridges generated if needed)
- [ ] pack_motion.py only on clean frames @ ~12fps, hold≤2
```

## Scripts

| Script | Role |
|---|---|
| `scripts/init_wan_scene.py` | Scaffold a layered Wan scene |
| `scripts/compile_wan_scene.py` | Validate scene/state plan → Wan jobs |
| `scripts/wan_generate.py` | Execute I2V/FLF2V jobs + save metadata |
| `scripts/cutout_video.py` | Wan MP4 → stable-canvas RGBA frames |
| `scripts/key_wan_jobs.py` | Batch matte all compiled Wan jobs |
| `scripts/compose_scene.py` | Time/z/transform composite → MP4 |
| `scripts/cutout_assets.py` | Chroma / white → RGBA |
| `scripts/split_parts.py` | Sheet → parts |
| `scripts/qa_frames.py` | Scale + pose-jump gate; `--write-bridges` |
| `scripts/interpolate_sequence.py` | Preview-only morph (do **not** pack) |
| `scripts/pack_motion.py` | Align → sheet + manifest + GIF |
| `scripts/init_long_action.py` | Scaffold D-Long project from template |
| `scripts/expand_stages.py` | `acts.json` → numbered micro-stages |
| `scripts/pick_candidates.py` | Choose lower-jump take_a/take_b |
| `scripts/merge_acts.py` | Concatenate acts → global ordered |
| `scripts/compose_layers.py` | Character + VFX composite |

Resolve via this skill’s absolute path. Examples: [examples.md](examples.md).
