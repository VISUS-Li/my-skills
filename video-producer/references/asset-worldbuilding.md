# Asset Worldbuilding

Use this when a video lacks images, icons, texture, B-roll, product shots, or visual specificity.

## Asset roles

Each asset should have a narrative role:

- proof: **web-sourced photo, screenshot, video clip, quote card, chart, document crop, product UI** — prefer downloaded `ref/` files tied to `beat_ids`.
- atmosphere: texture, room, landscape, lab, paper, gradient, street, device.
- explanation: icon, diagram, map, flow line, pointer, simplified object.
- emotion: human face, hands, food macro, reaction, abstract metaphor.
- rhythm: particles, light streaks, SFX, animated lines, transitions.

Avoid assets that only decorate. If an image does not clarify, prove, set mood, or create rhythm, replace it.

## Minimum density

For serious videos — **画面与动画都要填满**，且 **口播有实指就要有 ref 画面**:

- **First:** map each concrete narration beat → web search (中文) → download to `segments/<id>/assets/ref/` (see `web-sourced-visual-assets.md`).
- Plan at least **4–6 assets per major segment** (ref photos/clips + icons + plates + UI primitives combined).
- Per rendered segment: **≥3 ref photos/screenshots**, **≥1 video clip when script mentions demo/process**, **≥12 SVG/icons**, **≥4 plates/textures**, **≥15 choreographed motion actors** (see `visual-asset-generation.md`).
- Use at least **4 asset types** across the whole video: icons, **web ref photos/clips**, textures, B-roll, charts, particles, product mockups, device frames.
- Keep icon style consistent: stroke width, corner radius, fill behavior, color role.
- Keep images in one visual world: same color treatment, crop logic, contrast, grain, border, or frame treatment.
- **Batch workflow:** list beat-level ref downloads first, then SVG/plates in one pass — avoid SVG-only prep.

## Asset manifest columns

Use `assets/asset_manifest.csv`:

`asset_id,type,source,path_or_url,segment_id,role,rights_status,status,notes`

Rights status values:

- `self-created`
- `generated`
- `licensed`
- `public-domain`
- `fair-use-reference-only`
- `needs-check`
- `do-not-use-final`

Do not use `needs-check` or `do-not-use-final` assets in final render.

## Prompting generated images

When generating images for a video, specify — **prompt 默认中文**：

- style recipe and palette（中文描述风格与色板）
- camera distance and angle（机位与景别）
- focal subject（主体，英文 UI 可点名）
- background/texture（背景/纹理，用于填满画面边缘）
- negative prompts: 杂乱、随机文字、无关 logo、画面空洞
- how it will be cropped for 9:16 or 16:9
- **density note:** 构图应预留多个叠加位（卡片、箭头、角标），避免单物体居中大量留白

Example:

```text
暖色浅网格背景上的抽象数据管道插画，16:9，多个圆角模块与连接箭头，
层次丰富、边缘有装饰光斑，无任何可读文字，供后期叠加中文 HUD。
```

## Icon strategy

For motion graphics, prefer SVG icons or programmatic shapes. Use one system:

- outline rounded tech icons.
- solid pictograms.
- hand-drawn ink icons.
- 3D clay objects.
- flat editorial symbols.

Do not mix icon packs randomly.
