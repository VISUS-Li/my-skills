# Video Project Agent Contract

## 启动前必须读

1. `.video/state.json` - 当前 stage 与各 stage status。
2. `.video/review_registry.jsonl` - 最新 artifact status，按 `artifact_id` 取最后一条。
3. `.video/regen_queue.json` - `status=pending|in_progress` 的任务。
4. `.video/stage_manifest.json` - stage 依赖与必需产物。

## 禁止

- 修改 `status=approved|locked` 的文件内容，除非用户明确 unlock。
- 在 upstream stage 尚未 `approved` 时运行下游脚本，例如未 approved segment 就 render。
- 跳过 `stage_gate.py` 或 Review Studio API 直接改 `.video/state.json`。
- 为常规制片任务读取 `review-studio/` 源码。Review Studio 是给人用的网页控制台；agent 应只读当前 `PROJECT_DIR` 下的产物，并使用 `scripts/validate_gates.py`、`scripts/review_sync.py`、`scripts/regen_dispatch.py` 同步状态。
- 绕过标准合成入口，只使用 `segments/<id>/scripts/build_rich_segment.py` 生成页面。
- 生成依赖 `tl.play()` 自动播放的 segment HTML。Review Studio 合成页通过父页面 seek `window.__timelines[segment].time(t)` 驱动画面。

## 允许

- 处理 regen_queue 中 `assigned_to` 匹配的任务。
- 处理 review_registry 中 `status=rejected` 的 artifact。
- 创建版本化 draft，例如 `.v004.md`、`render_draft_v2.mp4`。
- 在 `scripts/build_<segment>_composition.py` 中调用 segment-local helper，但 root builder 必须保留。

## 完成后必须

1. 运行 `python scripts/validate_stage.py <project> --stage <stage_id>`，exit 0 后才可以 `stage_gate.py --status review|approved`。
2. 更新 artifact 到 `status=review`，不是 `approved`，除非用户明确说 auto-approve。
3. regen_queue item 标记为 `completed` 并附 note。
4. append `.video/history.jsonl`。
5. 若涉及 VO/beat 变更，重跑 measure -> build_micro_timing -> beat_asset_coverage_lint -> segment_timing_lint。
6. 含中文 SVG 后跑 `verify_svg_utf8.py`。
7. 运行 dependency stale 传播。

## narration_beats 硬性要求

- 必须使用 skill 模板完整列，包括 `narration`、`duration_sec`；不能只写 `spoken_focus` 元数据。
- `narration` 列是 Review Studio 导演页和 TTS 的唯一 beat 口播来源。
- 写完 `voiceover.md` 后，必须把全文拆进 `narration_beats.csv` 每行 `narration`。
- `visual_sync_plan.csv` / `beat_asset_plan.csv` 的 `beat_id` 必须与 `narration_beats.csv` 一一对应，不能保留 init 模板示例行。

## segment 合成硬性要求

- 标准入口：`scripts/build_s001_composition.py`，其他段落为 `scripts/build_<segment>_composition.py`。
- 输出：`segments/<id>/index.html`。
- HTML 必须包含 `data-composition-id`、`data-build-entry`、`window.initComposition`、`window.__timelines[segment]`、`window.__compositionErrors`。
- GSAP timeline 必须 `paused: true`，由 Review Studio seek 驱动，不能在 iframe 内自动 `play()`。
- optional DOM 节点必须先检查再 tween；不存在 `.hf-scan-line`、`.proof-img`、`.anim-proof`、`.anim-diagram` 时不能产生 GSAP target warning。
- GSAP functional value 用 `(index, target) => target.dataset.xxx`，不要写 `(el) => el.dataset.xxx`。
- 交付 review 前运行 `python scripts/test_composition_preview.py <project> --segment S001 --no-server`；有服务预览时再运行不带 `--no-server` 的版本。

## 命令优先级（segment 视觉驱动）

`edit asset -> build_composition -> test_composition_preview -> hyperframes lint -> human review -> render`

## Review Studio

一套服务管理多个项目；用户在网页切换当前项目。Agent 读写当前项目目录下的 `.video/` 文件。

```bash
pip install -r review-studio/requirements.txt
python review-studio/server/main.py --workspace D:\videos --port 8787

python scripts/validate_gates.py <project>
python scripts/review_sync.py <project>
python scripts/regen_dispatch.py <project> --dry-run
```
