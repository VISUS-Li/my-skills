# 平台说明

## YouTube

- 人工软字幕与自动 CC 通常可用 yt-dlp 拉取。
- 视频为中文时优先 `zh-Hans` / `zh`；否则取可用的最佳轨。
- 除非年龄限制或区域锁定，否则很少需要 cookies。

## Bilibili

- 可能有人工 CC 与 AI 字幕（`ai-zh`）；弹幕不是字幕轨。
- 若 yt-dlp 返回 HTTP 412 / 需要登录，用以下方式重试：
  - `--cookies-from-browser chrome`（或 `edge`、`firefox`）
  - 或 `--cookies path/to/cookies.txt`
- 优先 `zh-CN` → `zh` → `ai-zh`。

## 抖音 / TikTok

- 原生软字幕不常见。
- 默认路径：下载音频 → ASR（`hyperframes transcribe` 或 faster-whisper）。
- 短链（`v.douyin.com/...`）可用；yt-dlp 会展开。
- 下载失败时，向用户要 cookies 或本地导出文件。

## 本地文件

1. 用 ffprobe 探测内嵌字幕流。
2. 用 ffmpeg 抽出首选轨 → SRT。
3. 若无内嵌轨，直接对文件做 ASR。

## 硬烧字幕

本 skill **不做**硬烧字幕 OCR。若只有烧录文字且语音缺失/不可用，报告限制，不要编造文本。
