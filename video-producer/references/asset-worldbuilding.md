# Asset Worldbuilding

Use this when a video lacks images, icons, texture, B-roll, product shots, or visual specificity.

## Asset roles

Each asset should have a narrative role:

- proof: screenshot, quote card, chart, document crop, product UI.
- atmosphere: texture, room, landscape, lab, paper, gradient, street, device.
- explanation: icon, diagram, map, flow line, pointer, simplified object.
- emotion: human face, hands, food macro, reaction, abstract metaphor.
- rhythm: particles, light streaks, SFX, animated lines, transitions.

Avoid assets that only decorate. If an image does not clarify, prove, set mood, or create rhythm, replace it.

## Minimum density

For serious videos:

- Plan at least 2 assets per major segment.
- Use at least 3 asset types across the whole video: icons, screenshots/images, textures, B-roll, charts, SFX, particles, product mockups.
- Keep icon style consistent: stroke width, corner radius, fill behavior, color role.
- Keep images in one visual world: same color treatment, crop logic, contrast, grain, border, or frame treatment.

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

When generating images for a video, specify:

- style recipe and palette.
- camera distance and angle.
- focal subject.
- background/texture.
- negative prompts for clutter, random text, unrelated logos.
- how it will be cropped for 9:16 or 16:9.

## Icon strategy

For motion graphics, prefer SVG icons or programmatic shapes. Use one system:

- outline rounded tech icons.
- solid pictograms.
- hand-drawn ink icons.
- 3D clay objects.
- flat editorial symbols.

Do not mix icon packs randomly.
