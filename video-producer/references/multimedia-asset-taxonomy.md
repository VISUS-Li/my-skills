# Multimedia Asset Taxonomy（素材分类与命名契约）

Use when agents mix **news screenshots**, **stock photos**, **AI UI mocks**, **real footage**, and **Ken Burns stills** under vague `broll_*` / `ref_*` names. This reference is the **single naming and QC contract** for evidence-layer media.

## Four evidence prefixes + two video classes

| Prefix | Meaning | Typical source | Narration use |
|---|---|---|---|
| `ref_*` | Traceable proof (news, official site, doc screenshot) | Playwright capture, `og:image`, press kit | Named events, reports, official wording |
| `stock_*` | Related scene/concept still (not necessarily news) | Unsplash, Pexels stills, Wikimedia | Office, payment, handshake, chart mood |
| `gen_*` | AI/synthetic UI mock (English UI + Chinese overlay in code) | GPT Image, PIL mock | AppData, settings, disk alerts |
| `motion_*` | **Real** footage or screen recording | Pexels `video-files`, Pixabay, screen cap | Typing, datacenter, data flow |
| `broll_*` | **Ken Burns / still-image animation only** | ffmpeg `zoompan` on a still | Slow push on news still; diagram filler |

**Hard rule:** `motion_*` = real video. `broll_*` = animated still. Never call Ken Burns “实拍 B-roll” in manifests, checkpoints, or `segment_report.md`.

Legacy names (`screenshot_*`) remain valid but new assets should use `ref_*` for proof screenshots.

## Processed embed sizes（裁剪规格）

Under `segments/<id>/assets/ref/processed/`:

```text
ref/processed/
  *_1280x720.jpg|mp4     # full-frame embed / Ken Burns source / video
  *_640x360.jpg|mp4      # source_card slot (#ref-image-slot)
  _raw/                  # Playwright PNG / original download
  stock/                 # stock library originals before crop
  video_types_report.json
  beat_asset_coverage_report.json   # optional; written by beat_asset_coverage_lint.py
```

| Slot | Size | Usage |
|---|---|---|
| `embed_full` | 1280×720 | Hero proof, Ken Burns input, muted loop video |
| `embed_card` | 640×360 | `ref_frame_news.svg` / `source_card` inner image |

Evidence must **not** full-bleed over captions. Place inside device frames or `#ref-image-slot`.

Videos: default **muted loop**, trim to beat duration. GSAP Ken Burns applies to **still layers** only.

`ref_embed` in `beat_asset_plan.csv` supports `path_a|path_b` for mixed still + video on one beat.

## manifest fields（`assets/asset_manifest.csv`）

Required columns for evidence rows:

- `motion_type`: `real_footage` | `ken_burns` | `screen_recording` | `svg_only` | `still_photo`
- `embed_full`: path to 1280×720 processed file (if applicable)
- `embed_card`: path to 640×360 processed file (if applicable)

Naming:

- Real footage → `motion_<subject>_1280x720.mp4`
- Ken Burns → `broll_<subject>_1280x720.mp4` (never `motion_*`)
- Proof still → `ref_<subject>_1280x720.jpg` + optional `ref_<subject>_640x360.jpg`
- Stock still → `stock_<subject>_1280x720.jpg`
- AI UI mock → `gen_<subject>_1280x720.png`

## Beat-level binding（`beat_asset_plan.csv`）

Per-segment standard artifact: `segments/<id>/beat_asset_plan.csv`.

Plan **before** bulk download/generation. Times must come from `vo_timing.json` after TTS — not stale `narration_beats.csv` planned seconds.

Columns:

```csv
beat_id,start_sec,duration_sec,primary_asset,secondary_asset,accent_asset,ambient_asset,motion_primary,motion_secondary,source_visual,ref_embed,caption_hint,min_visible_assets,layer_count_target
```

Minimum per beat:

- 4 asset IDs (primary … ambient) — may include SVG for explain layer
- ≥2 motion verbs (`motion_primary`, `motion_secondary`)
- `ref_embed` when beat shows proof media (paths must exist on disk)

## Layered alignment（口播-画面，放宽但更精确）

| Narration type | Minimum visual |
|---|---|
| Named event / report / official quote | `ref_*` screenshot + source card |
| Mechanism / scene (disk, cloud sync, membership) | `stock_*` or `gen_*` or `motion_*`; SVG as support |
| Abstract transition (“不对”, “为什么”) | SVG + plate OK; `ref_embed` optional |
| How-to / settings walkthrough | `gen_*` UI + `motion_*` typing/screen rec preferred |

Gate: **≥70% beats** have `ref_*`, `stock_*`, or `motion_*` in the beat plan or `ref_embed` — not “≥70% must be news screenshots”.

Concrete-entity beats (`source_visual` ≠ `none` in `narration_beats.csv`) must bind at least one of `ref_*` / `stock_*` / `motion_*` — not SVG-only.

## Rich segment video budget（replaces vague “≥1 video clip”）

Per segment:

- **≥1 `motion_*`** real footage or screen recording
- **≥2 `broll_*`** Ken Burns clips allowed as **fill only**
- Ken Burns alone **does not** satisfy the real-footage requirement

## Windows / UTF-8（SVG 含中文）

Agents must **not** use editor Write tools for Chinese SVG. See `references/programmatic-chinese-infographics.md` → Windows UTF-8 section. Run:

```bash
python "$SKILL_DIR/scripts/verify_svg_utf8.py" "$PROJECT_DIR/segments/S001/assets"
```

## QC scripts

```bash
python "$SKILL_DIR/scripts/beat_asset_coverage_lint.py" "$PROJECT_DIR" S001 --fail-under 90
python "$SKILL_DIR/scripts/verify_svg_utf8.py" "$PROJECT_DIR/segments/S001/assets"
test -f "$PROJECT_DIR/segments/S001/assets/ref/processed/video_types_report.json"
```

## Checkpoint report（assets stage 结束必须主动汇报）

Agent must separate counts in the checkpoint summary:

1. Stills: `ref` / `stock` / `gen` counts
2. Video: `motion_*` real segments vs `broll_*` Ken Burns segments
3. Beats: X/Y with `ref_embed`; list beats that are SVG-only
4. Failures: Mixkit 403, Playwright not installed, etc. + user-fix commands

Do not say “21 visual assets done” when `processed/` only contains JSON metadata.

See also: `references/web-sourced-visual-assets.md`, `references/visual-asset-generation.md` (video sourcing ladder).
