# Review Studio

Video Producer 本地审核控制台 — 一套服务管理多个视频项目，网页内切换，无需重启。

> **给 Agent：** 本目录是 **人类用的网页控制台**（FastAPI + 静态前端）。常规制片时不要读取 `web/`、`server/` 源码 — 直接读 **项目目录** `PROJECT_DIR` 下的 `.video/`、`script/`、`segments/` 等产物，并用 `scripts/validate_gates.py`、`review_sync.py`、`regen_dispatch.py`。仅在用户要求启动/调试 Review Studio 或修改本控制台本身时再读本 README。

完整规格：`../references/review-studio-plan.md`（人类/改 Studio 时用；常规制片不必读全文）

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

Tab：Pipeline · Script · 口播 & 配音 · Assets · Timeline（含预览） · Stage · Regen Queue · Jobs · QC · History

### 口播 & 配音（原 Beats + Audio 合并）

| 区域 | 功能 |
|------|------|
| **顶栏** | IndexTTS 状态、参考音、时长汇总、全局配音进度、整段 audio chain |
| **主表** | 逐 beat 编辑口播、试听、单条配音+对齐；筛选「需关注」偏差/CPS |
| **侧栏** | 参考音频库、IndexTTS 配置（可折叠） |

### 新功能（Phase 4–7）

| Tab | 功能 |
|-----|------|
| **Script** | 编辑 `voiceover.md` + beats 概览 |
| **口播 & 配音** | 逐 beat 口播编辑、参考音库、IndexTTS 配置、进度条、audio chain |
| **Stage** | 每 stage 产物列表、内联编辑 MD/CSV/JSON |
| **Timeline** | 合成页/成片/Studio 预览、口播波形轨、GSAP seek 同步、beat/微事件编辑 |
| **Jobs** | 后台任务列表与 log |
| **Beats** | （已合并至「口播 & 配音」） |

**Timeline / HyperFrames 预览 API：**

```bash
GET  /api/timeline?segment=S001              # 含 media + preview 块
GET  /api/preview/composition/S001/index.html # 同源合成页（GSAP seek）
GET  /api/preview/hyperframes?segment=S001   # Studio 状态
POST /api/preview/hyperframes/start?segment=S001&port=3017
POST /api/preview/hyperframes/stop?segment=S001
```

时间轴 Tab 支持四种预览：**合成页**（默认，iframe + `window.__timelines` seek）、**成片** MP4、**Studio** 热重载、**口播** WAV；波形轨与 playhead 联动。

**IndexTTS API：**

```bash
GET  /api/tts/config          # 读取 indextts2_config.json
PUT  /api/tts/config          # 更新 base_url / defaults / voice_reference
GET  /api/tts/health          # 探测 IndexTTS WebUI
GET  /api/tts/progress        # beat 级配音进度（generation_progress.json）
GET  /api/audio/refs          # 参考音频库（含 uploaded_at、选用状态）
POST /api/audio/refs/upload   # 上传参考 WAV / MP3（MP3 需 ffmpeg 自动转 WAV）
PUT  /api/audio/refs/select   # 切换当前参考音
DELETE /api/audio/refs?path=  # 删除参考音频
```

**Audio chain 预设（API / UI）：**

```bash
# 仅对齐（不 TTS）
POST /api/jobs/preset/audio_chain?segment=S001

# 完整链：TTS → measure → micro → lint
POST /api/jobs/preset/audio_chain_tts?segment=S001

# 仅整段 TTS（不对齐）
POST /api/jobs/preset/indextts_segment?segment=S001

# 单/多 beat 配音 + 对齐
POST /api/jobs/preset/indextts_beats_align?segment=S001&beats=B001,B002

# 对齐 + 重建 HTML
POST /api/jobs/preset/audio_chain_build?segment=S001
```

CLI：

```bash
python scripts/audio_chain.py <project> S001 --skip-tts
python scripts/audio_chain.py <project> S001          # 含 IndexTTS
python scripts/test_review_studio.py                # T1–T28
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
