# Usage examples

## Layered Wan story scene (default motion path)

User: `做一个像素勇士砍巨龙救公主的动态视频，Wan 已经可用`

→ **Mode D-Wan**, not a monolithic scene generation and not per-frame sprite generation.

```bash
python scripts/init_wan_scene.py --template dragon-rescue --out ./sticker-kit-output/dragon-rescue
# Create the endpoint images named by scene_plan.json, then:
python scripts/compile_wan_scene.py ./sticker-kit-output/dragon-rescue/scene_plan.json --strict-assets
python scripts/wan_generate.py ./sticker-kit-output/dragon-rescue/wan_jobs.json --dry-run
```

Element decisions:

- `warrior_sword` stays one actor group so the held sword cannot detach.
- `dragon`, `dragon_fire`, and `impact_vfx` are separate layers.
- The slash and hit share one interaction time.
- At the hug, individual warrior/princess layers end and
  `warrior_princess_pair` begins as one contact group.
- Castle/hills remain a static plate; trees may use one short loop.

Use FLF2V for slash, hit→defeated, and tied→freed. Use I2V for idle/reaction
loops. Key opaque actors from chroma and fire/glow from black+luma, then run
`compose_scene.py`.

## Pick / switch style

User: `用8bit像素风做一只跳跃的猫贴纸动画`  
→ Mode D, `style_id=pixel-8bit`, lock Master from [styles.md](styles.md).

User: `换成彩色海克斯`  
→ Regenerate **anchor** with `hex-colorful`, then re-derive frames (do not mix hex cells into an old cozy sheet).

User: `有哪些风格？`  
→ List the preset index table in [styles.md](styles.md).

## Continuity failure to avoid

Bad: wok frames where “spatula wooden handle” becomes “wok side handle” and the spatula loses its handle.  
Fix: Part Inventory + Topology Sentence + dual refs + denser stages + reject/regen ([continuity.md](continuity.md)).

## Motion with inventory (preferred)

User: `delivery scooter hop loop, smooth`

1. Lock style (default `cozy-scrapbook` unless specified).
2. Write parts.json (T-bar handlebars SEPARATE from cargo box; 2 wheels; headlight).
3. Anchor on green with all parts clear.
4. ~48–52 keyframes (or prototype 14–16), refs=[anchor] then [anchor,prev], QA each batch.
5. cutout → qa_frames.py → pack_motion --fps 12.

## Frame budget (no ghost sheets)

User: `动作太快 / 帧跳跃 / 要约 50 帧 / 不要重影`

1. Generate clean unique poses (single crisp pose each).
2. Prompt forbids afterimages / multi-exposure.
3. Slow tempo with **hold**: `pack_motion.py --hold 2` → `A,A,B,B,…` (only after uniques already continuous).
4. Never put blend interpolate into `sheet.png`.

## Long action without video (D-Long)

User: `没有视频模型，要做连贯的龟派气功，大约 8–10 秒 / 120 帧`

→ **Mode D-Long** ([long-action.md](long-action.md)), **not** one full sprite sheet, **not** 8 poses × hold 15.

```bash
python scripts/init_long_action.py --template kamehameha --out ./sticker-kit-output/kamehameha
python scripts/expand_stages.py ./sticker-kit-output/kamehameha/acts.json
```

1. `parts.json` + character_anchor (+ vfx_anchor).
2. Generate ~24+28+36+24 micro-frames **per act** with dual refs; optional take_b → `pick_candidates.py`.
3. `qa_frames.py --write-bridges` → GenerateImage bridges → re-QA.
4. `merge_acts.py` → `compose_layers.py` (character+vfx) → `pack_motion.py --hold 1`.

User: `御剑穿云要更长更顺`

→ `--template sword_fly` same pipeline; keep clouds as SEPARATE props in topology.

## Anti-pattern: one-shot full sheet

User: `能不能一张图画出完整 120 格 sheet 来保证连续？`

→ **No.** One image has no timeline; cells teleport worse at high cell counts. Sheet is **pack output only**. Production = per-frame / per-act micro-keys (+ bridges).
