# Web-Sourced Visual Assets（真实画面素材采集）

Use when asset prep **only produces SVG icons** but narration mentions **real people, products, events, documents, demos, or footage**. Goal: **口播说到什么，画面有对应的相关素材** — not only abstract vector decoration.

**Naming contract:** load `references/multimedia-asset-taxonomy.md` — use `ref_*` / `stock_*` / `gen_*` / `motion_*` / `broll_*` consistently.

## Principle

**SVG = 解释层；ref/stock/motion = 证据/相关层；gen = UI 示意层。** All layers cooperate; none replaces the others on concrete beats.

| Layer | Asset types | When |
|---|---|---|
| 解释层 | SVG icons, diagrams, arrows, device frames | 抽象机制、流程、对比结构 |
| 证据层 `ref_*` | 新闻图、官网截图、文档、时间线照片 | 点名事件、报道、官方口径 |
| 相关层 `stock_*` | 办公、支付、握手、机房氛围 | 机制/场景，不必是新闻 |
| 示意层 `gen_*` | AI/PIL UI mock | 设置页、路径示意、告警弹窗 |
| 实拍层 `motion_*` | 录屏、Pexels/Pixabay 实拍 | demo、操作、现场过程 |
| 补位层 `broll_*` | Ken Burns 静图动画 | 仅填空；**不算实拍** |
| 氛围层 | AI 纹理 plate、grid、粒子 | 填满背景，不替代证据 |

If a beat names something concrete and you only show a generic icon → **fail asset prep**.

## Beat → 素材映射（必做）

Before generating SVG batch:

1. Write `segments/<id>/beat_asset_plan.csv` (plan first).
2. Read `script/narration_beats.csv`, `script/voiceover.md`, and `research/claim_ledger.csv`.
3. For **each beat**, fill `source_visual` with the intended proof asset ID — `none` only for pure abstraction.
4. After TTS, **rebind** `start_sec` / `duration_sec` from `vo_timing.json`.
5. Create one manifest row per file with `beat_ids`, `motion_type`, `embed_full`, `embed_card`.

Example `source_visual` values:

```csv
ref_op26_launch_photo
stock_office_payment_scene
gen_wps_settings_mock
motion_typing_demo
broll_news_slow_push
none
```

## 搜索与下载顺序（中文 query 优先）

1. **Research 已有 URL** — `research/source_cards.jsonl` / claim 引用 → `ref_*`.
2. **官方来源** — press kit、README 截图 → `ref_*` or `screenshot_*` (legacy).
3. **Wikimedia / 政府档案** — 人物、地图 → `ref_*` + attribution.
4. **CC 图库** — Unsplash/Pexels 静图 → `stock_*`; 实拍视频 → `motion_*`.
5. **产品/UI 证明** — 浏览器截图 → `ref_*`; AI mock → `gen_*`.
6. **短视频** — 官方 demo、录屏 → `motion_*`; yt-dlp 短 clip; **禁止**无授权搬运整段解说.
7. **Ken Burns fallback** — ffmpeg zoompan → `broll_*` only after video ladder fails.

**搜索词用中文**，实体名可中英混写。

## 下载与落盘

```text
segments/S001/assets/
  ref/
    processed/
      ref_news_1280x720.jpg
      ref_news_640x360.jpg
      motion_typing_1280x720.mp4
      broll_chart_1280x720.mp4
      _raw/
      stock/
      video_types_report.json
  icon_*.svg
  rebuild_chinese.py
```

Naming:

- `ref_<topic>_*` — traceable proof
- `stock_<topic>_*` — related still
- `gen_<topic>_*` — synthetic UI
- `motion_<topic>_1280x720.mp4` — **real** video
- `broll_<topic>_1280x720.mp4` — Ken Burns only

## Rights（与 fact-lock 一致）

| Situation | rights_status | Final render? |
|---|---|---|
| 官方 press / 明确可商用 media kit | `licensed` or `royalty-free-ok` | ✅ after note |
| Wikimedia CC0 | `cc0-ok` | ✅ |
| Wikimedia CC-BY | `cc-by-attribution-ready` | ✅ with credit |
| 自己浏览器截图 | `self-created` | ✅ |
| 新闻图 license 不明 | `fair-use-reference-only` | ⚠️ 短镜头+来源标注 |
| 随机爬图、水印图 | `needs-check` | ❌ never final |
| 他人解说整段搬运 | `do-not-use-final` | ❌ |

## Minimum budget（per segment）

| Type | Min | Notes |
|---|---:|---|
| `ref_*` / `stock_*` stills | **3** | 证据 + 相关场景 |
| `motion_*` real video / screen rec | **1** | demo/操作/现场 |
| `broll_*` Ken Burns | **0–2** | 补位；不满足实拍门槛 |
| SVG icons | 12 | 见 `visual-asset-generation.md` |
| Beat alignment | **≥70%** | beats 有 ref/stock/motion 或 `ref_embed` |

## 画面用法（HyperFrames / segment）

- 证据图进 **source_card / #ref-image-slot**，640×360；禁止整屏糊满盖住字幕。
- `motion_*`：muted loop，裁到 beat 时长。
- `broll_*`：必须标注 `motion_type=ken_burns`；汇报时与实拍分开计数。
- `ref_embed` 支持 `still.jpg|clip.mp4` 混用。
- 中文标注走 programmatic text layer。

## Anti-patterns

- ❌ 把 Ken Burns 报成「实拍 B-roll」
- ❌ `source_visual=none` 填 everywhere
- ❌ metadata JSON 在但 `processed/` 无文件
- ❌ 编辑器直接写含中文的 SVG（Windows 乱码）

## Workflow hook（assets stage）

```text
narration_beats + claim_ledger
  → beat_asset_plan.csv（中文搜索词 + URL）
  → assets-evidence: ref + stock + motion → ref/processed/
  → video_types_report.json
  → assets-explain: SVG + gen + plates（rebuild_chinese.py）
  → assets-motion-fallback: broll_* 仅补空缺
  → assets-bind: choreography + beat_asset_coverage_lint
  → verify_svg_utf8 + segment_timing_lint --full
```

See also: `references/multimedia-asset-taxonomy.md`, `references/visual-asset-generation.md`.
