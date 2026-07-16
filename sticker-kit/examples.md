# Usage examples

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
3. Slow tempo with **hold**: `pack_motion.py --hold 2` → `A,A,B,B,…`
4. Never put blend interpolate into `sheet.png`.
