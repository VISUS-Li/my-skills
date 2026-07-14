# Platform Notes

## YouTube

- Soft/manual captions and auto-generated CC are usually available via yt-dlp.
- Prefer `zh-Hans` / `zh` when the video is Chinese; otherwise take the best available track.
- Cookies are rarely required unless the video is age-restricted or region-locked.

## Bilibili

- Manual CC and AI captions (`ai-zh`) may exist; danmaku is not a subtitle track.
- If yt-dlp returns HTTP 412 / login required, retry with:
  - `--cookies-from-browser chrome` (or `edge`, `firefox`)
  - or `--cookies path/to/cookies.txt`
- Prefer `zh-CN` → `zh` → `ai-zh`.

## Douyin / TikTok

- Native soft subtitles are uncommon.
- Default path: download audio → ASR (`hyperframes transcribe` or faster-whisper).
- Short share links (`v.douyin.com/...`) are fine; yt-dlp expands them.
- If download fails, ask the user for cookies or a local file export.

## Local files

1. Probe embedded subtitle streams with ffprobe.
2. Extract the preferred track with ffmpeg → SRT.
3. If no embedded track, run ASR on the file directly.

## Burned-in (hard) subtitles

This skill does **not** OCR hard-burned captions. If only burned text exists and speech is absent/unusable, report the limitation instead of inventing text.
