#!/usr/bin/env python3
"""Reference audio helpers: validate uploads and normalize to WAV for IndexTTS."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REF_EXTENSIONS = {".wav", ".mp3"}


def is_wav(data: bytes) -> bool:
    return len(data) >= 4 and data[:4] == b"RIFF"


def is_mp3(data: bytes) -> bool:
    if len(data) < 3:
        return False
    if data[:3] == b"ID3":
        return True
    return data[0] == 0xFF and (data[1] & 0xE0) == 0xE0


def is_supported_ref(data: bytes, filename: str) -> bool:
    """Loose pre-check; final validation is done by ffmpeg when needed."""
    ext = Path(filename).suffix.lower()
    if ext not in REF_EXTENSIONS:
        return False
    if len(data) < 16:
        return False
    if ext == ".wav" and is_wav(data):
        return True
    if ext == ".mp3" and is_mp3(data):
        return True
    # Accept by extension — ffmpeg will validate/normalize on save.
    return ffmpeg_available() or is_wav(data) or is_mp3(data)


def normalize_ref_audio(src: Path, dest: Path) -> None:
    """Ensure IndexTTS-ready mono 44.1kHz WAV."""
    if src.suffix.lower() == ".wav" and src.resolve() == dest.resolve() and is_riff_file(src):
        return
    if src.suffix.lower() == ".wav" and src.resolve() != dest.resolve() and is_riff_file(src):
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return
    convert_to_wav(src, dest)


def is_riff_file(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 44:
        return False
    return path.read_bytes()[:4] == b"RIFF"


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def convert_to_wav(src: Path, dest: Path) -> None:
    if not ffmpeg_available():
        raise RuntimeError("ffmpeg is required to convert or normalize reference audio")
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-ac", "1", "-ar", "44100", str(dest)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"ffmpeg failed (exit {proc.returncode})")


def wav_path_for_ref(root: Path, rel_path: str) -> Path:
    """Return WAV path used by IndexTTS; convert MP3 sibling if needed."""
    normalized = rel_path.replace("\\", "/")
    src = root / normalized
    if not src.exists():
        raise FileNotFoundError(normalized)
    if src.suffix.lower() == ".wav" and is_riff_file(src):
        return src
    if src.suffix.lower() == ".mp3":
        dest = src.with_suffix(".wav")
        if not is_riff_file(dest):
            convert_to_wav(src, dest)
        return dest
    if is_riff_file(src):
        return src
    dest = src.with_suffix(".wav")
    if not is_riff_file(dest):
        convert_to_wav(src, dest)
    return dest


def tts_ref_rel_path(root: Path, rel_path: str) -> str:
    return wav_path_for_ref(root, rel_path).relative_to(root).as_posix()
