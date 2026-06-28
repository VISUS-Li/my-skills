# Video Project Agent Contract

## 启动前必读
1. `.video/state.json` — 当前 stage 与各 stage status
2. `.video/review_registry.jsonl` — 最新 artifact status（按 artifact_id 取最后一条）
3. `.video/regen_queue.json` — status=pending|in_progress 的任务
4. `.video/stage_manifest.json` — stage 依赖与必需产物

## 禁止
- 修改 status=approved|locked 的文件内容（除非用户显式 unlock）
- 在 upstream stage ≠ approved 时运行下游脚本（如未 approved segment 就 render）
- 跳过 stage_gate 直接写 state.json（必须用 stage_gate.py 或 Review Studio API）

## 允许
- 处理 regen_queue 中 assigned_to 匹配的任务
- 处理 review_registry 中 status=rejected 的 artifact
- 创建版本化 draft：*.v004.md, render_draft_v2.mp4

## 完成后必须
1. 更新 artifact → status=review（不是 approved，除非用户明确说 auto-approve）
2. regen_queue item → completed，附 note
3. append `.video/history.jsonl`
4. 若涉及 VO/beat 变更，重跑 measure → micro_timing → lint
5. 运行 dependency stale 传播

## 命令优先级（segment 视觉驳回）
edit asset → build_composition → hyperframes lint → (人工 review) → render

## Review Studio

一套服务管理多个项目；用户在网页切换当前项目，Agent 读写**当前项目目录**下的 `.video/` 文件。

```bash
pip install -r review-studio/requirements.txt
python review-studio/server/main.py --workspace D:\videos --port 8787
# 详见 review-studio/README.md

python scripts/validate_gates.py <project>
python scripts/review_sync.py <project>
python scripts/regen_dispatch.py <project> --dry-run
```
