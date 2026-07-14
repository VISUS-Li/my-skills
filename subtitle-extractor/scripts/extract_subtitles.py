#!/usr/bin/env python3
"""Extract timed subtitles from a video URL or local media file.

Priority:
  1) Soft / auto captions via yt-dlp (URLs) or embedded tracks via ffmpeg (local)
  2) ASR via hyperframes Whisper, then optional faster-whisper / OpenAI API
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".webm", ".avi", ".m4v", ".flv", ".ts"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}

LANG_PREFERENCE = [
    "zh-Hans",
    "zh-CN",
    "zh",
    "zh-Hant",
    "zh-TW",
    "ai-zh",
    "en",
    "en-US",
    "en-GB",
]


def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=check,
    )


def which(name: str) -> str | None:
    return shutil.which(name)


def ensure_yt_dlp():
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        die(
            "yt-dlp is not installed. Run:\n"
            "  pip install -r subtitle-extractor/requirements.txt"
        )


def detect_platform(source: str) -> str:
    if is_url(source):
        host = urlparse(source).netloc.lower()
        if "youtu" in host:
            return "youtube"
        if "bilibili" in host or "b23.tv" in host:
            return "bilibili"
        if "douyin" in host or "iesdouyin" in host:
            return "douyin"
        if "tiktok" in host:
            return "tiktok"
        if "xiaohongshu" in host or "xhslink" in host:
            return "xiaohongshu"
        return "web"
    return "local"


def is_url(source: str) -> bool:
    return source.startswith(("http://", "https://"))


def slugify(text: str, fallback: str = "subtitle") -> str:
    text = (text or "").strip()
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", text)
    text = re.sub(r"\s+", "_", text)
    text = text.strip("._")
    return (text[:80] or fallback)


def ts_to_seconds(ts: str) -> float:
    ts = ts.strip().replace(",", ".")
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return float(parts[0])


def seconds_to_srt_ts(sec: float) -> str:
    if sec < 0:
        sec = 0.0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    if ms == 1000:
        s += 1
        ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def strip_tags(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"[ \t]+", " ", text).strip()


def parse_srt(content: str) -> list[dict[str, Any]]:
    blocks = re.split(r"\n\s*\n", content.replace("\r\n", "\n").strip())
    segments: list[dict[str, Any]] = []
    for block in blocks:
        lines = [ln for ln in block.split("\n") if ln.strip() != ""]
        if len(lines) < 2:
            continue
        # optional index line
        idx = 0
        if re.fullmatch(r"\d+", lines[0].strip()):
            idx = int(lines[0].strip())
            lines = lines[1:]
        if not lines or "-->" not in lines[0]:
            continue
        start_s, end_s = [p.strip() for p in lines[0].split("-->")]
        # drop optional position cues after end stamp
        end_s = end_s.split()[0]
        text = strip_tags("\n".join(lines[1:]))
        if not text:
            continue
        segments.append(
            {
                "index": idx or (len(segments) + 1),
                "start": ts_to_seconds(start_s),
                "end": ts_to_seconds(end_s),
                "text": text,
            }
        )
    for i, seg in enumerate(segments, 1):
        seg["index"] = i
    return segments


def parse_vtt(content: str) -> list[dict[str, Any]]:
    content = content.replace("\r\n", "\n")
    content = re.sub(r"^WEBVTT[^\n]*\n", "", content)
    content = re.sub(r"\nNOTE[^\n]*\n(?:.*?\n)*?\n", "\n", content, flags=re.MULTILINE)
    blocks = re.split(r"\n\s*\n", content.strip())
    segments: list[dict[str, Any]] = []
    seen_texts: list[str] = []
    for block in blocks:
        lines = [ln for ln in block.split("\n") if ln.strip() != ""]
        if not lines:
            continue
        if "-->" not in lines[0] and len(lines) > 1 and "-->" in lines[1]:
            lines = lines[1:]
        if not lines or "-->" not in lines[0]:
            continue
        start_s, end_s = [p.strip() for p in lines[0].split("-->")]
        end_s = end_s.split()[0]
        text = strip_tags("\n".join(lines[1:]))
        # YouTube auto VTT often repeats rolling text; keep only net-new phrase ends
        if not text:
            continue
        if seen_texts and text == seen_texts[-1]:
            continue
        if seen_texts and text.startswith(seen_texts[-1]):
            text = text[len(seen_texts[-1]) :].strip()
        seen_texts.append(strip_tags("\n".join(lines[1:])))
        if not text:
            continue
        segments.append(
            {
                "index": len(segments) + 1,
                "start": ts_to_seconds(start_s),
                "end": ts_to_seconds(end_s),
                "text": text,
            }
        )
    return segments


def segments_to_srt(segments: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for i, seg in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(f"{seconds_to_srt_ts(seg['start'])} --> {seconds_to_srt_ts(seg['end'])}")
        lines.append(seg["text"])
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def segments_to_txt(segments: list[dict[str, Any]]) -> str:
    return "\n".join(seg["text"] for seg in segments).strip() + "\n"


def load_subtitle_file(path: Path) -> list[dict[str, Any]]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".vtt" or raw.lstrip().startswith("WEBVTT"):
        return parse_vtt(raw)
    return parse_srt(raw)


def prefer_lang(available: list[str], requested: str | None) -> str | None:
    if not available:
        return None
    if requested and requested != "auto":
        # exact / prefix match
        for cand in available:
            if cand.lower() == requested.lower() or cand.lower().startswith(requested.lower() + "-"):
                return cand
        # zh request should accept Chinese family
        if requested.lower().startswith("zh"):
            for pref in LANG_PREFERENCE:
                if pref.lower().startswith("zh") and pref in available:
                    return pref
            for cand in available:
                if "zh" in cand.lower() or "ai-zh" in cand.lower():
                    return cand
    for pref in LANG_PREFERENCE:
        if pref in available:
            return pref
    return available[0]


def write_outputs(
    out_dir: Path,
    stem: str,
    segments: list[dict[str, Any]],
    meta: dict[str, Any],
) -> dict[str, str]:
    if not segments:
        die("No subtitle segments produced.")
    out_dir.mkdir(parents=True, exist_ok=True)
    srt_path = out_dir / f"{stem}.srt"
    txt_path = out_dir / f"{stem}.txt"
    json_path = out_dir / f"{stem}.json"
    srt_path.write_text(segments_to_srt(segments), encoding="utf-8")
    txt_path.write_text(segments_to_txt(segments), encoding="utf-8")
    payload = {
        **meta,
        "files": {
            "srt": str(srt_path.resolve()),
            "txt": str(txt_path.resolve()),
            "json": str(json_path.resolve()),
        },
        "segment_count": len(segments),
        "segments": segments,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload["files"]


def ydl_base_opts(out_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "outtmpl": str(out_dir / "%(id)s.%(ext)s"),
        "paths": {"home": str(out_dir)},
    }
    if args.cookies:
        opts["cookiefile"] = args.cookies
    if args.cookies_from_browser:
        opts["cookiesfrombrowser"] = (args.cookies_from_browser,)
    if args.proxy:
        opts["proxy"] = args.proxy
    return opts


def extract_url_soft_subs(
    url: str,
    out_dir: Path,
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], dict[str, Any]] | None:
    ensure_yt_dlp()
    import yt_dlp

    work = out_dir / "_ydl_work"
    work.mkdir(parents=True, exist_ok=True)

    info_opts = ydl_base_opts(work, args)
    info_opts["skip_download"] = True
    with yt_dlp.YoutubeDL(info_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    title = info.get("title") or info.get("id") or "video"
    video_id = str(info.get("id") or "video")
    subs = info.get("subtitles") or {}
    auto = info.get("automatic_captions") or {}
    manual_langs = list(subs.keys())
    auto_langs = list(auto.keys())

    meta_base = {
        "source": url,
        "platform": detect_platform(url),
        "title": title,
        "video_id": video_id,
        "available_subtitles": manual_langs,
        "available_auto_captions": auto_langs,
    }

    chosen_lang = None
    method = None
    if manual_langs:
        chosen_lang = prefer_lang(manual_langs, args.lang)
        method = "soft_sub"
        write_auto = False
    elif auto_langs:
        chosen_lang = prefer_lang(auto_langs, args.lang)
        method = "auto_cc"
        write_auto = True
    else:
        return None

    if not chosen_lang:
        return None

    dl_opts = ydl_base_opts(work, args)
    dl_opts.update(
        {
            "skip_download": True,
            "writesubtitles": not write_auto,
            "writeautomaticsub": write_auto,
            "subtitleslangs": [chosen_lang],
            "subtitlesformat": "vtt/srt/best",
        }
    )
    with yt_dlp.YoutubeDL(dl_opts) as ydl:
        ydl.download([url])

    candidates = sorted(work.glob(f"{video_id}*.vtt")) + sorted(work.glob(f"{video_id}*.srt"))
    if not candidates:
        # some extractors use title-based names
        candidates = sorted(work.glob("*.vtt")) + sorted(work.glob("*.srt"))
    if not candidates:
        return None

    sub_path = candidates[0]
    segments = load_subtitle_file(sub_path)
    meta = {
        **meta_base,
        "method": method,
        "language": chosen_lang,
        "raw_subtitle_file": str(sub_path),
    }
    return segments, meta


def download_audio(url: str, out_dir: Path, args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    ensure_yt_dlp()
    import yt_dlp

    work = out_dir / "_audio_work"
    work.mkdir(parents=True, exist_ok=True)
    opts = ydl_base_opts(work, args)
    opts.update(
        {
            "format": "bestaudio/best",
            "outtmpl": str(work / "%(id)s.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ],
        }
    )
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    title = info.get("title") or info.get("id") or "video"
    video_id = str(info.get("id") or "video")
    wavs = list(work.glob(f"{video_id}*.wav")) or list(work.glob("*.wav"))
    if not wavs:
        # postprocessor may have failed; take any downloaded media
        media = [
            p
            for p in work.iterdir()
            if p.suffix.lower() in VIDEO_EXTS | AUDIO_EXTS
        ]
        if not media:
            die("Audio download produced no media file.")
        audio_path = media[0]
    else:
        audio_path = wavs[0]
    return audio_path, {
        "source": url,
        "platform": detect_platform(url),
        "title": title,
        "video_id": video_id,
    }


def extract_embedded_subs(media: Path, out_dir: Path, lang: str | None) -> tuple[list[dict[str, Any]], dict[str, Any]] | None:
    if not which("ffprobe") or not which("ffmpeg"):
        return None
    probe = run(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-select_streams",
            "s",
            "-show_entries",
            "stream=index,codec_name:stream_tags=language,title",
            "-of",
            "json",
            str(media),
        ],
        check=False,
    )
    if probe.returncode != 0:
        return None
    data = json.loads(probe.stdout or "{}")
    streams = data.get("streams") or []
    if not streams:
        return None

    chosen_idx = 0
    chosen_lang = None
    if lang and lang != "auto":
        for i, stream in enumerate(streams):
            tags = stream.get("tags") or {}
            stream_lang = (tags.get("language") or "").lower()
            if stream_lang.startswith(lang.lower()[:2]):
                chosen_idx = i
                chosen_lang = tags.get("language")
                break
    else:
        tags = (streams[0].get("tags") or {})
        chosen_lang = tags.get("language")

    tmp_srt = out_dir / f"_embedded_{media.stem}.srt"
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(media),
            "-map",
            f"0:s:{chosen_idx}",
            "-c:s",
            "srt",
            str(tmp_srt),
        ],
        check=False,
    )
    if ext.returncode != 0 or not tmp_srt.exists():
        return None
    segments = load_subtitle_file(tmp_srt)
    meta = {
        "source": str(media.resolve()),
        "platform": "local",
        "title": media.stem,
        "method": "embedded",
        "language": chosen_lang or "unknown",
        "raw_subtitle_file": str(tmp_srt),
    }
    return segments, meta


def asr_hyperframes(media: Path, out_dir: Path, lang: str | None, model: str) -> tuple[list[dict[str, Any]], dict[str, Any]] | None:
    if not which("npx"):
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    srt_path = out_dir / f"_asr_{media.stem}.srt"
    # Avoid silent English translation of Chinese speech.
    whisper_model = model
    if whisper_model.endswith(".en") and (not lang or not lang.startswith("en")):
        whisper_model = whisper_model[: -len(".en")] or "small"
    if lang in (None, "auto") and not whisper_model.endswith(".en"):
        pass  # auto-detect
    cmd = [
        "npx",
        "--yes",
        "hyperframes",
        "transcribe",
        str(media),
        "--model",
        whisper_model,
        "--to",
        "srt",
        "-o",
        str(srt_path),
        "--dir",
        str(out_dir),
        "--json",
    ]
    if lang and lang != "auto":
        cmd.extend(["--language", lang.split("-")[0]])
    print(f"[asr] hyperframes: {' '.join(cmd)}", file=sys.stderr)
    proc = run(cmd, check=False)
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout, file=sys.stderr)
        return None
    if not srt_path.exists():
        # hyperframes may write beside input or into --dir
        alt = list(out_dir.glob("*.srt"))
        if not alt:
            return None
        srt_path = alt[0]
    segments = load_subtitle_file(srt_path)
    return segments, {
        "method": "asr_hyperframes",
        "language": lang or "auto",
        "whisper_model": whisper_model,
        "raw_subtitle_file": str(srt_path),
    }


def asr_faster_whisper(media: Path, lang: str | None, model: str) -> tuple[list[dict[str, Any]], dict[str, Any]] | None:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    print(f"[asr] faster-whisper model={model}", file=sys.stderr)
    wm = WhisperModel(model, device="cpu", compute_type="int8")
    language = None if not lang or lang == "auto" else lang.split("-")[0]
    segments_iter, info = wm.transcribe(str(media), language=language, vad_filter=True)
    segments: list[dict[str, Any]] = []
    for i, seg in enumerate(segments_iter, 1):
        text = (seg.text or "").strip()
        if not text:
            continue
        segments.append(
            {
                "index": i,
                "start": float(seg.start),
                "end": float(seg.end),
                "text": text,
            }
        )
    return segments, {
        "method": "asr_faster_whisper",
        "language": getattr(info, "language", language or "auto"),
        "whisper_model": model,
    }


def asr_openai(media: Path, lang: str | None) -> tuple[list[dict[str, Any]], dict[str, Any]] | None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None
    client = OpenAI(api_key=api_key, base_url=os.environ.get("OPENAI_API_BASE") or None)
    model = os.environ.get("TRANSCRIBE_MODEL", "whisper-1")
    print(f"[asr] openai model={model}", file=sys.stderr)
    # Prefer a wav/mp3 under size limits; pass file directly when small enough.
    with media.open("rb") as f:
        kwargs: dict[str, Any] = {
            "model": model,
            "file": f,
            "response_format": "verbose_json",
            "timestamp_granularities": ["segment"],
        }
        if lang and lang != "auto":
            kwargs["language"] = lang.split("-")[0]
        result = client.audio.transcriptions.create(**kwargs)
    segments: list[dict[str, Any]] = []
    raw_segments = getattr(result, "segments", None) or []
    for i, seg in enumerate(raw_segments, 1):
        text = (getattr(seg, "text", None) or seg.get("text") if isinstance(seg, dict) else "") or ""
        text = text.strip()
        if not text:
            continue
        start = float(getattr(seg, "start", None) if not isinstance(seg, dict) else seg.get("start") or 0)
        end = float(getattr(seg, "end", None) if not isinstance(seg, dict) else seg.get("end") or start)
        segments.append({"index": i, "start": start, "end": end, "text": text})
    if not segments and getattr(result, "text", None):
        segments = [{"index": 1, "start": 0.0, "end": 0.0, "text": result.text.strip()}]
    return segments, {
        "method": "asr_openai",
        "language": lang or getattr(result, "language", "auto"),
        "whisper_model": model,
    }


def run_asr(media: Path, out_dir: Path, args: argparse.Namespace, base_meta: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    engines = []
    preferred = (args.asr_engine or "auto").lower()
    if preferred == "hyperframes":
        engines = [asr_hyperframes]
    elif preferred == "faster-whisper":
        engines = [asr_faster_whisper]
    elif preferred == "openai":
        engines = [asr_openai]
    else:
        engines = [asr_hyperframes, asr_faster_whisper, asr_openai]

    lang = None if args.lang == "auto" else args.lang
    last_err = None
    for engine in engines:
        try:
            if engine is asr_hyperframes:
                result = engine(media, out_dir, lang, args.whisper_model)
            elif engine is asr_faster_whisper:
                result = engine(media, lang, args.whisper_model)
            else:
                result = engine(media, lang)
        except Exception as exc:  # noqa: BLE001 — try next engine
            last_err = exc
            print(f"[asr] engine failed: {exc}", file=sys.stderr)
            result = None
        if result:
            segments, meta = result
            if segments:
                return segments, {**base_meta, **meta}
    hint = (
        "ASR failed. Install one of:\n"
        "  - Node + hyperframes (npx hyperframes)  [recommended]\n"
        "  - pip install faster-whisper\n"
        "  - set OPENAI_API_KEY and pip install openai"
    )
    if last_err:
        die(f"{hint}\nLast error: {last_err}")
    die(hint)


def process_url(url: str, out_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    soft_err: Exception | None = None
    if args.prefer != "asr":
        try:
            soft = extract_url_soft_subs(url, out_dir, args)
            if soft:
                segments, meta = soft
                stem = slugify(meta.get("title") or meta.get("video_id") or "subtitle")
                files = write_outputs(out_dir, stem, segments, meta)
                return {**meta, "files": files, "segment_count": len(segments)}
        except Exception as exc:  # noqa: BLE001
            soft_err = exc
            print(f"[soft-sub] failed, falling back to ASR: {exc}", file=sys.stderr)

    try:
        audio_path, base_meta = download_audio(url, out_dir, args)
    except Exception as exc:  # noqa: BLE001
        hints = [
            "Could not download media for ASR.",
            "Try: --cookies-from-browser chrome  |  --cookies cookies.txt  |  --proxy URL",
            "Or download the video manually and pass the local file path.",
        ]
        if soft_err:
            hints.insert(0, f"Soft-sub error: {soft_err}")
        die("\n".join(hints) + f"\nDownload error: {exc}")

    segments, meta = run_asr(audio_path, out_dir, args, base_meta)
    stem = slugify(meta.get("title") or meta.get("video_id") or "subtitle")
    files = write_outputs(out_dir, stem, segments, meta)
    return {**meta, "files": files, "segment_count": len(segments)}


def process_local(path: Path, out_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    if not path.exists():
        die(f"File not found: {path}")
    if args.prefer != "asr":
        embedded = extract_embedded_subs(path, out_dir, None if args.lang == "auto" else args.lang)
        if embedded:
            segments, meta = embedded
            stem = slugify(path.stem)
            files = write_outputs(out_dir, stem, segments, meta)
            return {**meta, "files": files, "segment_count": len(segments)}
    base_meta = {
        "source": str(path.resolve()),
        "platform": "local",
        "title": path.stem,
    }
    segments, meta = run_asr(path, out_dir, args, base_meta)
    stem = slugify(path.stem)
    files = write_outputs(out_dir, stem, segments, meta)
    return {**meta, "files": files, "segment_count": len(segments)}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Extract subtitles from YouTube / Bilibili / Douyin / local media."
    )
    p.add_argument("source", help="Video URL or local file path")
    p.add_argument(
        "-o",
        "--out-dir",
        default="outputs/subtitles",
        help="Output directory (default: outputs/subtitles)",
    )
    p.add_argument(
        "--lang",
        default="auto",
        help="Preferred language code (auto|zh|zh-Hans|en|...). Default: auto",
    )
    p.add_argument(
        "--prefer",
        choices=["soft", "asr"],
        default="soft",
        help="Prefer soft/embedded captions, or force ASR",
    )
    p.add_argument(
        "--asr-engine",
        choices=["auto", "hyperframes", "faster-whisper", "openai"],
        default="auto",
        help="ASR backend when soft captions are unavailable",
    )
    p.add_argument(
        "--whisper-model",
        default="small",
        help="Whisper model size for local ASR (default: small). Do not use *.en for Chinese.",
    )
    p.add_argument("--cookies", help="Netscape cookies.txt path for yt-dlp")
    p.add_argument(
        "--cookies-from-browser",
        help="Browser name for yt-dlp cookies (chrome|edge|firefox|brave)",
    )
    p.add_argument("--proxy", help="Proxy URL for yt-dlp")
    p.add_argument(
        "--print-json",
        action="store_true",
        help="Print full result JSON to stdout",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = args.source.strip().strip('"').strip("'")
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if is_url(source):
        result = process_url(source, out_dir, args)
    else:
        result = process_local(Path(source).expanduser(), out_dir, args)

    summary = {
        "ok": True,
        "source": result.get("source"),
        "platform": result.get("platform"),
        "title": result.get("title"),
        "method": result.get("method"),
        "language": result.get("language"),
        "segment_count": result.get("segment_count"),
        "files": result.get("files"),
    }
    if args.print_json:
        print(json.dumps({**summary, "segments": result.get("segments")}, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        die("Interrupted", 130)
