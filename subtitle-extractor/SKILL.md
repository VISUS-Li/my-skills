---
name: subtitle-extractor
description: >-
  从 YouTube、Bilibili、抖音/TikTok、小红书链接或本地视频/音频提取带时间轴的字幕/文稿。
  优先用 yt-dlp 软字幕/自动字幕，再回退 hyperframes Whisper ASR。
  在用户粘贴视频 URL 或文件并要求字幕、transcript、SRT、VTT、提取字幕、视频转文字、
  speech-to-text，或从已有媒体取 captions 时使用。
---

# 字幕提取器

把**视频 URL** 或**本地媒体文件**转成带时间轴的字幕。

默认输出（在 `--out-dir` 下，默认 `outputs/subtitles/`）：

```text
{title}.srt      # 带时间的 SubRip
{title}.txt      # 纯文本文稿
{title}.json     # 元数据 + segments[{start,end,text}]
```

## 何时使用

- 用户给出 YouTube / Bilibili / 抖音 / TikTok / 小红书链接，要字幕或口播文字。
- 用户给出本地 `.mp4` / `.mkv` / `.mov` / `.webm` / 音频，要 SRT/TXT。
- `video-producer` 或 `vibe-director` 需要参考视频文稿，再做调研、风格 DNA 或节拍重建。

**不要**用本 skill 设计花字 / 把字幕烧进成片——那属于制作类 skill（`video-producer`、`embedded-captions`、Remotion/HyperFrames）。

## 依赖

必需：

```bash
pip install -r requirements.txt   # yt-dlp
# PATH 上要有 ffmpeg + ffprobe（本机通常已有）
```

ASR 回退（无软字幕时——抖音与多数本地录屏常见）：

1. **推荐：** Node.js + `npx hyperframes`（本地 Whisper；中文用 `--model small`，勿用 `*.en`）
2. 可选：`pip install faster-whisper`
3. 可选：`OPENAI_API_KEY` + `pip install openai`

仅在下载失败时再加载平台说明：`references/platforms.md`。

## 一条命令

在本 skill 目录执行（或传脚本绝对路径）：

```bash
python scripts/extract_subtitles.py "<url-or-file>" -o outputs/subtitles
```

常用参数：

```bash
# 有中文轨时优先中文
python scripts/extract_subtitles.py "URL" --lang zh -o outputs/subtitles

# 即使有软字幕也强制语音识别
python scripts/extract_subtitles.py "URL" --prefer asr --whisper-model small

# Bilibili / 抖音登录墙
python scripts/extract_subtitles.py "URL" --cookies-from-browser chrome

# 选择 ASR 后端
python scripts/extract_subtitles.py "file.mp4" --asr-engine hyperframes --lang zh
```

Agent 工作流：

1. 确认来源是 URL 或已有本地路径。
2. 创建/使用工程 `outputs/subtitles/`（或用户指定目录）。
3. 跑脚本。缺 `yt-dlp` 时先装 `requirements.txt` 再重试。
4. 若遇登录 / 412 / cookies 错误，用 `--cookies-from-browser chrome` 重试（或索要 `cookies.txt`）。
5. 汇报：标题、方法（`soft_sub` | `auto_cc` | `embedded` | `asr_*`）、语言、段数，以及 `.srt` / `.txt` / `.json` 的绝对路径。
6. 预览 `.srt` 前约 5 条 cue（除非用户要求，否则不要倾倒整篇文稿）。

## 解析顺序

| 来源 | 第一轮 | 第二轮 |
|--------|--------|--------|
| YouTube / Bilibili URL | yt-dlp 人工 CC → 自动 CC | 下载音频 → ASR |
| 抖音 / TikTok / 小红书 URL | yt-dlp 软字幕（若有） | 下载音频 → ASR（常见路径） |
| 本地媒体 | ffmpeg 内嵌字幕流 | 对文件做 ASR |

硬烧字幕（仅像素、无语音/软轨）**不在范围**——告知用户未实现 OCR。

## 与 Video Producer / Vibe Director 集成

导演 skill 收到参考 URL/文件且需要口播内容时：

```json
"delegation": {
  "skill": "subtitle-extractor",
  "purpose": "timed transcript from reference video",
  "input_artifacts": ["inputs/reference.url"],
  "output_artifacts": [
    "outputs/subtitles/*.srt",
    "outputs/subtitles/*.json"
  ],
  "acceptance": "non-empty timed segments; soft_sub/auto_cc preferred over ASR"
}
```

消费方式：

- `video-producer`：把 `.txt`/segments 喂给调研/脚本；时间轴作节拍提示（TTS 后需重测）。
- `vibe-director`：把产出的 `.srt` 当作 `references/workflow.md` 中的 `srt` 入口模式。

本 skill **只负责提取**。风格、花字、烧录仍归导演/渲染器。

## 输出 JSON 形状

```json
{
  "source": "https://...",
  "platform": "youtube",
  "title": "...",
  "method": "soft_sub",
  "language": "zh-Hans",
  "segment_count": 42,
  "files": {"srt": "...", "txt": "...", "json": "..."},
  "segments": [{"index": 1, "start": 0.0, "end": 1.6, "text": "..."}]
}
```

## 失败检查清单

- `ModuleNotFoundError: yt_dlp` → `pip install -r requirements.txt`
- 抖音软字幕为空 → 正常；脚本应回退 ASR
- 中文 ASR 吐出英文 → 用 `--whisper-model small --lang zh` 重跑（勿用 `small.en`）
- Bilibili 412 → `--cookies-from-browser chrome`
- 无 ffmpeg → 安装 ffmpeg，用于内嵌字幕抽取与音频后处理
