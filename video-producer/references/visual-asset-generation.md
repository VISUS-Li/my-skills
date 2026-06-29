# Visual Asset Generation Protocol

Use when segments look **too empty**, **PPT-like**, or user asks for icons, illustrations, AI images, SVG.

## 中文优先原则（生成与检索）

**默认用中文** 写所有美术相关 prompt、搜索词、brief 与 manifest 描述：

- Image model prompts、SVG 生成说明、`media-use --intent`、`heygen asset search` 查询词
- `assets/asset_choreography_manifest.csv` 的 `description` / `source_or_prompt`
- `visual_asset_brief.json` 的 `prompt` 字段
- Web 搜索视觉参考时的 query 与 `visual_moodboard.json` 备注

**例外 — 保留英文的部分：**

- 素材本体必须是英文时（英文 UI、终端命令、代码、品牌 logo 文字、原文截图）
- 此时 prompt **框架用中文**，仅 subject 中点名英文元素，例如：`扁平矢量浏览器窗口插画，地址栏留白，页面内为英文 GitHub 界面，无水印…`

**禁止：** 无必要地把整段 prompt 写成英文；中文科普/口播视频应让模型与素材库按中文语义检索。

Readable Chinese **never** goes into raster images — overlay via programmatic text layers (unchanged).

## Minimum asset budget (per segment)

**宁多勿少。** 目标是用资产与动画 **填满画面与时间轴**，不是「够用就行」。

| Asset type | Min count | Target (rich segments) | Notes |
|---|---:|---:|---|
| **Evidence stills** (`ref_*` / `stock_*`) | **3** | **5–8** | 绑定 `beat_ids` + `embed_*` |
| **`motion_*` real video / screen rec** | **1** | **2–3** | demo/发布/操作；trim 2–8s |
| **`broll_*` Ken Burns** | **0** | **2** | 补位 only；**不满足实拍门槛** |
| SVG icons (topic-specific) | 12 | 16–24 | stroke 2–4px; Chinese via code layers |
| Decorative PNG (transparent) | 4 | 6–8 | plates, blobs — **no readable Chinese** |
| UI/source primitives | 6 | 8–12 | cards, stamps, arrows, device frames |
| Background/ambient fillers | 3 | 5+ | grid, orbs — **always moving** |
| Motion actors | 15+ | 20+ | **every beat** ≥5 visible assets |

Per-beat checklist (`beat_asset_plan.csv`):

- 4 asset slots + 2 motion verbs + optional `ref_embed`
- ≥5 visible assets on screen
- ≥4 layers with independent motion
- Frame occupancy **50–80%**

Log `motion_type`, `embed_full`, `embed_card` in `assets/asset_manifest.csv`.

## Web-sourced real media（证据层，必做）

Load **`references/multimedia-asset-taxonomy.md`** and **`references/web-sourced-visual-assets.md`**.

1. Plan `beat_asset_plan.csv` before bulk gen.
2. Prefer URLs in `research/source_cards.jsonl`; **中文搜索** when unknown.
3. Save processed embeds under `segments/<id>/assets/ref/processed/`.
4. Fill `narration_beats.csv` → `source_visual` with manifest `asset_id`.

Quick routing:

| Need | Tool | Output |
|---|---|---|
| Known source URL | `curl -L` / Playwright | `ref_*` → processed 1280/640 |
| Related scene still | Unsplash/Pexels/Wikimedia | `stock_*` |
| UI mock | Image model / PIL | `gen_*` |
| Real footage | Screen rec / Pexels video-files | `motion_*` |
| Official demo clip | `yt-dlp` section trim | `motion_*` |
| Still missing video | ffmpeg zoompan | `broll_*` + `ken_burns` |

## Video sourcing ladder（mandatory order）

Agents must try in order and log failures in `video_types_report.json`:

1. **User screen recording** — settings, disk usage (`screen_recording`; highest trust).
2. **Pexels direct** — `videos.pexels.com/video-files/…` URL when available.
3. **Playwright** — open Pexels/Pixabay page, read `<video src>` (`playwright install chromium`).
4. **yt-dlp** — official short demo clip.
5. **Ken Burns fallback** — `motion_type=ken_burns`, file `broll_*`; never report as real B-roll.

QC artifact: `segments/<id>/assets/ref/processed/video_types_report.json`.

## Generation routing（解释层 + 装饰层）

| Need | Tool | Output |
|---|---|---|
| Icon set (consistent style) | **Hand-write SVG** or LLM → SVG code | `segments/S00x/assets/icon_*.svg` |
| Hero plate / texture | **Image model** (GPT Image, DALL·E, Flux, etc.) | PNG → `assets/images/` |
| Transparent sticker/mascot | Image model + **rembg** or native alpha prompt | PNG transparent |
| Reference mood | Web search + moodboard | `design/visual_moodboard.json` |
| Stock fallback | Mixkit/Pixabay (manual if CDN 403) | logged in rights log |

## Image model prompt template (no text in image)

**用中文写 prompt**（下列为模板；`[主题]`、`[具体物体]` 填中文；若主体含英文 UI，在 subject 中点名英文部分）：

```text
扁平矢量信息图插画，用于 [主题] 科普解说视频。
风格：暖色浅网格画布 #F7F1E6，柔和蓝/琥珀色点缀，圆角卡片，轻微投影，
抖音/B站科技科普风，16:9 构图，层次丰富、画面饱满。
主体：[具体物体 — 如：纸尿裤分层结构、报纸版面、抽象公章图形、数据管道模块]。
禁止任何可读文字、logo、水印；不要写实婴儿照片。
透明或干净背景，便于后期叠加中文文本层与 HUD。
```

English-only fallback (when the image model ignores Chinese — rare):

```text
Flat vector infographic for [TOPIC]. Same style constraints. NO readable text.
```

## SVG generation template (preferred for icons)

Ask the model for **valid SVG** only — **brief 用中文**：

```text
生成 128×128 SVG 图标：[主题/物体，中文描述].
风格：2–4px 描边，圆角端点，配色 #2563EB #F59E0B #22C55E #EF4444 #1F2937。
禁止内嵌文字。viewBox="0 0 128 128"。单文件，无脚本。
输出完整可运行的 SVG 代码。
```

Validate: open in browser; run through HyperFrames compile.

## Segment asset folder layout

```
segments/S001/
  assets/
    rebuild_chinese.py
    ref/
      processed/
        ref_press_1280x720.jpg
        ref_press_640x360.jpg
        motion_demo_1280x720.mp4
        broll_news_1280x720.mp4
        video_types_report.json
    icon_newspaper.svg
    s001_hero_plate.png
  beat_asset_plan.csv
  visual_asset_brief.json
  index.html
  vo_timing.json
  s001_vo.wav
```

## visual_asset_brief.json (optional)

```json
{
  "segment_id": "S001",
  "style_refs": ["design/tokens.json", "design/art_direction.md"],
  "assets": [
    {"id": "icon_newspaper", "type": "svg", "prompt": "...", "path": "assets/icon_newspaper.svg", "layer": "midground", "motion": "stamp_hit"}
  ]
}
```

## Rights

| Source | rights_status |
|---|---|
| Hand-written SVG | `cleared` |
| Project-generated PNG (no third-party) | `cleared` |
| Stock / AI with license | `cleared` after license check |
| Unknown web scrape | `candidate_needed` — **never final** |

## Anti-patterns

- ❌ 口播讲真实事件/产品，画面只有 SVG 图标、没有 `ref/` 证据图
- ❌ One full-screen card for entire beat
- ❌ Reusing same icon 4× without transform/state change
- ❌ Baking Chinese into PNG (use programmatic text layers)
- ❌ 16:9 photo backgrounds that compete with captions

## Research enrichment (design layer)

Before asset gen for factual segments:

1. **用中文搜索** 主题视觉：官方 logo 仅作抽象形状参考，时间线照片 → 优先 **diagram 化**
2. Pull 3–5 reference layouts (game HUD, infographic, news explainer) into `design/visual_moodboard.json` — **notes 字段用中文**
3. Note **must-not-copy** (watermarks, brand packs)
4. From each narration beat, derive **≥2 new asset ideas** before coding — batch-generate in one pass rather than one icon at a time

## media-use / 素材库检索

When using `media-use resolve` or HeyGen asset search:

```bash
# ✅ 中文 intent（默认）
node resolve.mjs --type icon --intent "圆角描边火箭发射图标，科技科普风，透明背景" --project .

# ✅ 混合：中文描述 + 英文本体
node resolve.mjs --type image --intent "浅色网格背景上的 VS Code 代码窗口，界面为英文，留白供字幕" --project .

# ❌ 避免无必要的全英文
node resolve.mjs --type icon --intent "rocket launch icon" --project .
```

See `references/layered-composition-depth.md` for how assets stack.
