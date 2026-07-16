---
name: sticker-kit
description: >-
  Multi-style die-cut sticker kit for UI mockups AND continuity-safe motion:
  preset styles (cozy scrapbook default, 8-bit pixel, colorful hex, flat vector,
  kawaii, watercolor, comic ink, neo-pop, clay, risograph, chalk, marker, doodle,
  vintage), identity-locked anchors, part-inventory anti-morph, dense keyframes,
  green-screen cutout, pivot sheets + GIF/MP4 for HyperFrames/Remotion. Use when
  the user wants 贴纸, sticker kit, 手绘贴纸风, 8bit/像素, 彩色海克斯, scrapbook UI,
  精灵图/帧动画, 锚图派生, 连续帧防跳跃, chroma-key, or sticker-kit (legacy: cozy-sticker-ui).
---

# Sticker Kit (+ Motion)

Multi-style **die-cut stickers** for static UI overlays and **continuity-safe** motion (anchor → dense frames → sheet / GIF / MP4).

**Styles (switch anytime):** [styles.md](styles.md) — default `cozy-scrapbook`  
Prompt templates: [style-reference.md](style-reference.md)  
**Continuity / anti-morph (required for Mode D):** [continuity.md](continuity.md)

## Style switcher

1. Default style id: **`cozy-scrapbook`**.
2. If the user picks another preset (id or alias in [styles.md](styles.md)), lock that `style_id` for the whole job.
3. Paste that preset’s **Master** + **Negatives** into every image prompt; regenerate the **anchor** after a mid-job style change.
4. Chroma for stickers/frames stays `#00FF00` unless the user explicitly waives cutout.

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
| **Action / sprite / multi-frame** | **D (default for motion)** |
| Static + motion | C and/or D |

Default output: user folder, else `./sticker-kit-output/`.

## Style lock (short)

- Active preset from [styles.md](styles.md) (default cozy scrapbook)
- Stickers/anchors/frames: solid `#00FF00` preferred; screens: preset Screen bg
- Die-cut readable silhouette; obey preset outline / border / shadow rules
- No photoreal; avoid glass / purple-neon chrome unless the chosen preset allows a controlled accent

---

## Mode A / B / C

- **A:** ffmpeg sample frames → vibe + map to closest preset id + prompts.  
- **B:** research → `9:16` screens with active style lock.  
- **C:** green sheets → `cutout_assets.py --mode green` → `split_parts.py`. Prefer one subject per image.

---

## Mode D — Motion with continuity

**Never** ship one-shot text-only sprite sheets as production when parts can morph.  
**Always** follow [continuity.md](continuity.md): Part Inventory → Topology Sentence → dense stages → dual refs → visual QA → pack only accepted frames.

### D0 — Classify + budget frames

**Production default: ~50 packed frames.** Sparse 12–14 frame loops are prototypes only.

| Diff | Method | Clean generated frames | Preview FPS |
|---|---|---|---|
| Light | Micro-keys | 24–32 | 10–12 |
| Medium | **Per-stage micro-keys** (default) | **48–52** | 12 |
| Hard | I2V extract clean frames | 48–64 | 12–15 |

Each frame = **one crisp pose** (no afterimages). Pose teleports (run→crouch) are hard fails.  
**Do not** use blend/ffmpeg interpolate to fill the sheet — that causes ghosting. Details: [continuity.md](continuity.md).

### D1 — Anchor + Part Inventory

1. Draft `parts.json` + Topology Sentence + Color lock ([continuity.md](continuity.md)); record `style_id`.
2. Generate anchor on `#00FF00`, **neutral**, every inventoried part **clearly separate**, using active style Master.
3. Cutout; reject fused anchors.
4. Save `anchor_greenscreen.*`, `parts.json`.

### D2 — Derive (anti-morph + anti-jump + anti-ghost)

1. Write **~48–52 micro-stages** (medium) — one GenerateImage (or I2V extract) **per stage**.
2. Each prompt: Style preset + Topology + Color lock + FREE-only + delta-only + action-class lock +  
   **“Single crisp pose only. NO motion blur, NO afterimages, NO ghost trail, NO multi-exposure.”**
3. Refs: `[anchor]` then `[anchor, previous_accepted]`.
4. Batch ≤4, visual QA; **reject any ghosted/multi-exposure image**; regen before continuing.
5. To go from 17→50: **generate more real frames**, never blend two frames into one cell.

Hard path: I2V → ffmpeg extract **individual** frames → same QA / pack (still no blend sheet).

### D3 — Pack (clean frames only)

```bash
python scripts/cutout_assets.py FRAMES/*greenscreen* --mode green -o OUT/rgba
# order accepted CLEAN frames as frame_01.png …
python scripts/qa_frames.py OUT/ordered --max-scale-jitter 0.25 --max-pair-diff 0.22 --max-ghost 0.35
# if pair-diff fails: generate bridge frames with GenerateImage — do NOT blend
# Slow playback without ghosts: repeat each pose (--hold 2 → A,A,B,B,…)
python scripts/pack_motion.py OUT/ordered -o OUT/motion --cell 512 --fps 12 --hold 2 --anchor bottom-center
```

`interpolate_sequence.py` is **preview-only**; never pack blend output into `motion/frames` or `sheet.png`.  
Use `--hold 2`/`3` to slow motion (same crisp pose twice) when targeting ~50 packed frames.

Deliver: `frames/` (clean, may include holds), `sheet.png`, `manifest.json`, `preview.gif`, `parts.json`.

### D4 — Compositor

HyperFrames (default) or Remotion consume `manifest.json`. Single-sticker bob/scale → Mode C + easing, not Mode D.

---

## Motion checklist

```
- [ ] style_id locked (default cozy-scrapbook)
- [ ] parts.json + Topology Sentence written
- [ ] Anchor shows all parts, lookalikes distinct
- [ ] Stage list **~48–52 real poses** (medium)
- [ ] Dual ref used after frame 1 when possible
- [ ] **Color lock** + **pose-class lock** + **no ghosting** every batch
- [ ] No pose teleports; no blend/morph sheet cells
- [ ] `qa_frames.py --max-pair-diff 0.22` passes (or GenerateImage bridges)
- [ ] `pack_motion.py` only on clean frames @ ~12fps
```

## Scripts

| Script | Role |
|---|---|
| `scripts/cutout_assets.py` | Chroma / white → RGBA |
| `scripts/split_parts.py` | Sheet → parts |
| `scripts/qa_frames.py` | Scale + consecutive pose-jump gate |
| `scripts/interpolate_sequence.py` | Preview-only morph (do **not** pack into sticker sheet) |
| `scripts/pack_motion.py` | Align → sheet + manifest + GIF |

Resolve via this skill’s absolute path. Examples: [examples.md](examples.md).
