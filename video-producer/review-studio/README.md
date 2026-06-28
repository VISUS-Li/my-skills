# Review Studio

Video Producer 本地审核控制台 — 一套服务管理多个视频项目，网页内切换，无需重启。

完整规格：`../references/review-studio-plan.md`

## 安装

```bash
pip install -r review-studio/requirements.txt
```

## 启动

```bash
# 推荐：指定工作区（扫描其下所有 video 项目）
python review-studio/server/main.py --workspace D:\videos --port 8787

# 指定工作区 + 默认打开的项目
python review-studio/server/main.py \
  --workspace C:\Users\11839 \
  --project c:\Users\11839\opc-ai-douyin-3min \
  --port 8787
```

Windows PowerShell：

```powershell
.\review-studio\start.ps1 -Workspace D:\videos
.\review-studio\start.ps1 -Workspace C:\Users\11839 -Project c:\Users\11839\opc-ai-douyin-3min
```

浏览器打开：**http://127.0.0.1:8787**

## 网页操作

页头工作区栏：

| 控件 | 说明 |
|------|------|
| **工作区根目录** + **浏览…** | 选包含多个项目的父文件夹，自动扫描 |
| **扫描** | 重新扫描当前工作区 |
| **当前项目** 下拉 | 切换项目（不重启服务） |
| **打开路径** + **浏览…** | 直接选单个项目目录（含 `.video/state.json`） |
| **切换** | 手输绝对路径打开项目 |

Tab：Pipeline · Script · Beats · Audio · Assets · Timeline · Preview · Stage · Regen Queue · Jobs · QC · History

### 新功能（Phase 4–7）

| Tab | 功能 |
|-----|------|
| **Script** | 编辑 `voiceover.md` + beats 概览 |
| **Audio** | IndexTTS 状态、计划 vs 实测时长、一键 audio chain |
| **Stage** | 每 stage 产物列表、内联编辑 MD/CSV/JSON |
| **Timeline** | 计划/实测双轨、拖拽调整 beat duration、点击 micro-event |
| **Jobs** | 后台任务列表与 log |
| **Beats** | Beat 详情抽屉、单 beat TTS、manual duration |

**Audio chain 预设（API / UI）：**

```bash
# 仅对齐（不 TTS）
POST /api/jobs/preset/audio_chain?segment=S001

# 完整链：TTS → measure → micro → lint
POST /api/jobs/preset/audio_chain_tts?segment=S001

# 对齐 + 重建 HTML
POST /api/jobs/preset/audio_chain_build?segment=S001
```

CLI：

```bash
python scripts/audio_chain.py <project> S001 --skip-tts
python scripts/audio_chain.py <project> S001          # 含 IndexTTS
python scripts/test_review_studio.py                # T1–T20
```

## 项目识别

目录下存在 `.video/state.json` 即视为 video 项目。用 `scripts/init_video_project.py` 创建的项目均符合。

## 配置持久化

```
~/.video-producer/studio.json
```

保存：`workspace_root`、`current_project`、`recent_projects`（最近 12 个）

## 架构说明

| 位置 | 内容 |
|------|------|
| `video-producer/review-studio/` | 网页 + API（**只维护一份**） |
| `video-producer/scripts/` | gate、sync、lint 脚本 |
| `<项目>/` | `.video/`、`script/`、`segments/` 等**数据** |

**不要**把 `review-studio/` 复制到每个视频项目里。

## 相关 CLI

```bash
python scripts/validate_gates.py <project>      # 检查 stage 依赖 gate
python scripts/review_sync.py <project>         # 同步 asset registry
python scripts/regen_dispatch.py <project> --dry-run
python scripts/test_review_studio.py            # 集成测试 T1–T8
```

## 启动参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `--workspace` | — | 工作区根目录 |
| `--project` | — | 初始当前项目（可选） |
| `--scan-depth` | 2 | 扫描子目录深度（1–5） |
| `--port` | 8787 | HTTP 端口 |
| `--host` | 127.0.0.1 | 监听地址 |
