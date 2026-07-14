---
name: subtitle-extractor
description: "Extract timed subtitles/transcripts from YouTube, Bilibili, Douyin/TikTok, Xiaohongshu links, or local video/audio files. Prefer soft/auto captions via yt-dlp, then ASR via hyperframes Whisper. Use when the user pastes a video URL or file and asks for 字幕, transcript, SRT, VTT, 提取字幕, 视频转文字, speech-to-text, or captions from existing media."
---

# Subtitle Extractor

Turn a **video URL** or **local media file** into timed subtitles.

Default outputs (under `--out-dir`, default `outputs/subtitles/`):

```text
{title}.srt      # timed SubRip
{title}.txt      # plain transcript
{title}.json     # metadata + segments[{start,end,text}]
```

## When To Use

- User provides a YouTube / Bilibili / Douyin / TikTok / Xiaohongshu link and wants subtitles or spoken text.
- User provides a local `.mp4` / `.mkv` / `.mov` / `.webm` / audio file and wants SRT/TXT.
- `video-producer` or `vibe-director` needs a reference-video transcript before research, style DNA, or beat reconstruction.

Do **not** use this skill to design flower text / burn captions into a finished edit — that belongs to production skills (`video-producer`, `embedded-captions`, Remotion/HyperFrames).

## Dependencies

Required:

```bash
pip install -r requirements.txt   # yt-dlp
# ffmpeg + ffprobe on PATH (already common on this machine)
```

ASR fallback (when soft captions are missing — typical for Douyin / many local recordings):

1. **Recommended:** Node.js + `npx hyperframes` (uses local Whisper; for Chinese pass `--model small`, never `*.en`)
2. Optional: `pip install faster-whisper`
3. Optional: `OPENAI_API_KEY` + `pip install openai`

Load platform caveats only when a download fails: `references/platforms.md`.

## One Command

From this skill directory (or pass an absolute script path):

```bash
python scripts/extract_subtitles.py "<url-or-file>" -o outputs/subtitles
```

Useful flags:

```bash
# Prefer Chinese tracks when available
python scripts/extract_subtitles.py "URL" --lang zh -o outputs/subtitles

# Force speech recognition even if soft captions exist
python scripts/extract_subtitles.py "URL" --prefer asr --whisper-model small

# Bilibili / Douyin login walls
python scripts/extract_subtitles.py "URL" --cookies-from-browser chrome

# Choose ASR backend
python scripts/extract_subtitles.py "file.mp4" --asr-engine hyperframes --lang zh
```

Agent workflow:

1. Confirm source is a URL or an existing local path.
2. Create/use the project `outputs/subtitles/` (or the user-requested folder).
3. Run the script. On missing `yt-dlp`, install from `requirements.txt` then retry.
4. If the command fails with login / 412 / cookies errors, retry with `--cookies-from-browser chrome` (or ask for `cookies.txt`).
5. Report: title, method (`soft_sub` | `auto_cc` | `embedded` | `asr_*`), language, segment count, and absolute paths of `.srt` / `.txt` / `.json`.
6. Preview the first ~5 cue lines from the `.srt` (do not dump a huge transcript unless asked).

## Resolution Order

| Source | Pass 1 | Pass 2 |
|--------|--------|--------|
| YouTube / Bilibili URL | yt-dlp manual CC → auto CC | download audio → ASR |
| Douyin / TikTok / XHS URL | yt-dlp soft sub if any | download audio → ASR (usual path) |
| Local media | ffmpeg embedded subtitle stream | ASR on file |

Hard-burned captions (pixels only, no speech/soft track) are **out of scope** — tell the user OCR is not implemented.

## Integration With Video Producer / Vibe Director

When a director skill receives a reference URL/file and needs spoken content:

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

Consumption:

- `video-producer`: feed `.txt`/segments into research/script; use timings as beat hints (re-time after TTS).
- `vibe-director`: treat produced `.srt` as the `srt` intake mode in `references/workflow.md`.

Keep this skill responsible only for **extraction**. Style, flower text, and burn-in stay with the director/renderer.

## Output JSON Shape

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

## Failure Checklist

- `ModuleNotFoundError: yt_dlp` → `pip install -r requirements.txt`
- Empty soft captions on Douyin → expected; script should fall back to ASR
- Chinese ASR returned English → rerun with `--whisper-model small --lang zh` (never `small.en`)
- Bilibili 412 → `--cookies-from-browser chrome`
- No ffmpeg → install ffmpeg for embedded-sub extract and audio postprocess
