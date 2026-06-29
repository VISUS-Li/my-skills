# Web-Sourced Visual Assets（真实画面素材采集）

Use when asset prep **only produces SVG icons** but narration mentions **real people, products, events, documents, demos, or footage**. Goal: **口播说到什么，画面尽量有对应的真实素材** — not only abstract vector decoration.

## Principle

**SVG = 解释层；真实图片/视频 = 证据层。** Both are required for factual explainers.

| Layer | Asset types | When |
|---|---|---|
| 解释层 | SVG icons, diagrams, arrows, device frames | 抽象机制、流程、对比结构 |
| 证据层 | 新闻图、产品截图、官方海报、会议片段、文档扫描、地图、时间线照片 | 口播点名具体人物/公司/事件/产品/原文/现场 |
| 氛围层 | AI 纹理 plate、grid、粒子 | 填满背景，不替代证据 |

If a beat names something concrete and you only show a generic icon → **fail asset prep**.

## Beat → 素材映射（必做）

Before generating SVG batch:

1. Read `script/narration_beats.csv`, `script/voiceover.md`, and `research/claim_ledger.csv`.
2. For **each beat**, fill `source_visual` with the intended proof asset ID or search target — not `none` when the phrase mentions a real entity.
3. Create one manifest row per downloaded file in `assets/asset_manifest.csv` with `beat_ids` linking back.

Example `source_visual` values:

```csv
ref_op26_launch_photo
screenshot_github_readme
broll_demo_keynote_clip
wikimedia_timeline_map
none
```

`none` only for pure abstraction beats (定义、比喻、总结 checklist).

## 搜索与下载顺序（中文 query 优先）

1. **Research 已有 URL** — `research/source_cards.jsonl` / claim 引用的官网、新闻、论文配图 → 直接下载。
2. **官方来源** — press kit、产品媒体页、GitHub README 截图、App Store 预览、开发者文档 diagram（注意 license）。
3. **Wikimedia Commons / 政府公开档案** — 人物、历史事件、地图；记录 license 与 attribution。
4. **CC 图库 / 视频库** — Pexels、Pixabay、Mixkit、Coverr（视频 B-roll）；`rights_status=royalty-free-ok`。
5. **产品/UI 证明** — 自己用浏览器截图（`self-created`）或下载官方 demo GIF/MP4。
6. **短视频片段** — 官方发布会、官方 YouTube/B站账号 demo；用 `yt-dlp` 裁短 clip，**禁止**无授权搬运他人解说/二次创作整段。

**搜索词用中文**，实体名可中英混写，例如：

- `OpenAI GPT-4o 发布会 官方 截图`
- `某某事件 新华社 照片 site:gov.cn`
- `Wikimedia Commons [人物名] portrait`

## 下载与落盘

Project layout (per segment):

```text
segments/S001/assets/
  ref/                          # 网络采集的真实素材（优先放这里）
    ref_press_photo_001.jpg
    screenshot_product_ui.png
    broll_keynote_demo_004.mp4
  icon_*.svg                    # 矢量解释层
  s001_hero_plate.png           # AI 装饰 plate（非证据）
```

Naming: `ref_<topic>_<nnn>.<ext>` | `screenshot_<app>_<nnn>.png` | `broll_<subject>_<nnn>.mp4`

Download commands (examples):

```bash
# 已知 URL（来自 source_cards）
curl -L -o "$PROJECT_DIR/segments/S001/assets/ref/ref_official_001.jpg" "https://..."

# 官方 YouTube/B站 demo — 短 clip，写 rights
yt-dlp -f "bv*[height<=720]+ba/b[height<=720]" \
  --download-sections "*00:01:20-00:01:35" \
  -o "$PROJECT_DIR/segments/S001/assets/ref/broll_demo_001.%(ext)s" \
  "https://www.youtube.com/watch?v=..."

# 浏览器截图：手动或 Playwright；保存到 ref/ 并登记 manifest
```

After download:

- Verify file opens (image dimensions / video duration via `ffprobe`).
- Write `assets/asset_manifest.csv` row: `type=photo|screenshot|broll|video_clip`, `source=<url>`, `rights_status`, `beat_ids`.
- Save evidence: copy license page snippet or Wikimedia attribution to `assets/rights_evidence/<asset_id>.txt` when required.

## Rights（与 fact-lock 一致）

| Situation | rights_status | Final render? |
|---|---|---|
| 官方 press / 明确可商用 media kit | `licensed` or `royalty-free-ok` | ✅ after note |
| Wikimedia CC0 | `cc0-ok` | ✅ |
| Wikimedia CC-BY | `cc-by-attribution-ready` | ✅ with credit |
| 自己浏览器截图（说明用途） | `self-created` | ✅ |
| 新闻图/社交图，来源清楚但 license 不明 | `fair-use-reference-only` | ⚠️ 短镜头+来源标注；高风险需人工 gate |
| 随机爬图、水印图、未知来源 | `needs-check` | ❌ never final |
| 他人解说/整段搬运 | `do-not-use-final` | ❌ |

Do not skip download because rights are unclear — download to `ref/_candidates/`, mark `needs-check`, and surface in Review Studio for approval.

## Minimum budget（per segment，与 SVG 并行）

| Type | Min | Notes |
|---|---:|---|
| Web photo / screenshot (`ref/`) | **3** | 对应口播中的具体名词 |
| Video clip / screen recording | **1** | 当口播提到 demo、发布、现场、操作过程 |
| SVG icons | 12 | 见 `visual-asset-generation.md` |
| 口播-画面对齐 | **≥70%** beats | 有具体内容的 beat 必须在 manifest 中有 `ref_*` 或 `screenshot_*` |

## 画面用法（HyperFrames / segment）

- 证据素材放在 **midground `source_card` / `texture_plate` / device frame 内**，不要整屏糊图盖住字幕。
- 视频 clip：2–8s loop 或 trim 到 beat 时长；加 Ken Burns、crop punch-in、highlight box — **still animate**, don't static dump.
- 同一 ref 图可复用，但需 **不同 crop/motion/state**（`asset_choreography_manifest.csv`）。
- 中文标注仍走 programmatic text layer；新闻图上的原文字保留为「证据」而非重新 OCR 生成。

## Anti-patterns

- ❌ 整段视频只有 SVG 图标，口播却在讲真实公司/事件/产品
- ❌ `source_visual=none` 填 everywhere
- ❌ 只用 AI 生成图冒充新闻照片/产品真机
- ❌ 下载后不登记 manifest / beat_ids
- ❌ 水印图、营销号搬运图直接上最终成片

## Workflow hook（assets stage）

```text
narration_beats + claim_ledger
  → 列出 beat_visual 清单（中文搜索词 + 优先 URL）
  → 下载到 segments/<id>/assets/ref/
  → 更新 asset_manifest + asset_choreography（proof layer）
  → 再批量生成 SVG / plates
  → segment_timing_lint + 人工 Review Studio 证据 tab
```

See also: `references/visual-asset-generation.md`, `references/research-factcheck.md`, `references/audio-assets-rights.md` (rights field parity).
