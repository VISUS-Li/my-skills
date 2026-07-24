#!/usr/bin/env python3
"""按确定性摆放与可见性交接合成 RGBA 片段。"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

from PIL import Image


def resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def frame_files(folder: Path) -> list[Path]:
    files = sorted(folder.glob("frame_*.png"))
    if not files:
        raise FileNotFoundError(f"no frame_*.png in {folder}")
    return files


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def interpolate_transform(state: dict, progress: float) -> dict:
    fixed = state.get("transform") or {}
    start = {**fixed, **(state.get("transform_from") or {})}
    end = {**start, **(state.get("transform_to") or {})}
    return {
        key: lerp(float(start.get(key, default)), float(end.get(key, start.get(key, default))), progress)
        for key, default in (("x", 0.5), ("y", 0.85), ("height", 0.5), ("opacity", 1.0))
    }


def visibility_opacity(state: dict, local_time: float) -> float:
    """Return a deterministic state-entry/state-exit fade multiplier."""
    visibility = state.get("visibility") or {}
    start = float(state["start_sec"])
    end = float(state["end_sec"])
    elapsed = max(0.0, local_time - start)
    remaining = max(0.0, end - local_time)
    opacity = 1.0
    fade_in = float(visibility.get("fade_in_sec", 0.0))
    fade_out = float(visibility.get("fade_out_sec", 0.0))
    if fade_in > 0:
        opacity = min(opacity, elapsed / fade_in)
    if fade_out > 0:
        opacity = min(opacity, remaining / fade_out)
    return max(0.0, min(1.0, opacity))


def choose_index(state: dict, local_time: float, count: int, fps: int) -> int:
    start = float(state["start_sec"])
    end = float(state["end_sec"])
    elapsed = max(0.0, local_time - start)
    playback = state.get("playback", "stretch")
    source_fps = float(state.get("source_fps", fps))
    if playback == "loop":
        return int(elapsed * source_fps) % count
    if playback in ("once", "hold"):
        return min(count - 1, int(elapsed * source_fps))
    progress = min(1.0, elapsed / max(end - start, 1e-6))
    return min(count - 1, int(round(progress * (count - 1))))


@lru_cache(maxsize=256)
def load_rgba(path: str) -> Image.Image:
    return Image.open(path).convert("RGBA")


def place(
    canvas: Image.Image,
    asset: Image.Image,
    transform: dict,
    anchor: str,
    sampling: str,
) -> None:
    target_h = max(1, round(canvas.height * transform["height"]))
    target_w = max(1, round(asset.width * target_h / max(asset.height, 1)))
    resample = Image.Resampling.NEAREST if sampling == "nearest" else Image.Resampling.LANCZOS
    resized = asset.resize((target_w, target_h), resample)
    opacity = max(0.0, min(1.0, transform["opacity"]))
    if opacity < 1.0:
        alpha = resized.getchannel("A").point(lambda value: round(value * opacity))
        resized.putalpha(alpha)
    px = round(canvas.width * transform["x"])
    py = round(canvas.height * transform["y"])
    if anchor == "center":
        x, y = px - target_w // 2, py - target_h // 2
    elif anchor == "top-left":
        x, y = px, py
    else:
        x, y = px - target_w // 2, py - target_h
    canvas.alpha_composite(resized, (x, y))


def active_state(element: dict, local_time: float) -> dict | None:
    for state in element.get("states") or []:
        if float(state["start_sec"]) <= local_time < float(state["end_sec"]):
            return state
    # Include final endpoint on the last frame.
    states = element.get("states") or []
    if states and math.isclose(local_time, float(states[-1]["end_sec"]), abs_tol=1e-6):
        return states[-1]
    return None


def state_asset(root: Path, state: dict, local_time: float, fps: int) -> Image.Image:
    if state.get("mode") == "static":
        path = resolve(root, state.get("image") or state["start_image"])
        return load_rgba(str(path.resolve())).copy()
    folder = resolve(root, state["rgba_dir"])
    files = frame_files(folder)
    index = choose_index(state, local_time, len(files), fps)
    return load_rgba(str(files[index].resolve())).copy()


def shot_at(shots: list[dict], time_sec: float) -> dict | None:
    for shot in shots:
        if float(shot["start_sec"]) <= time_sec < float(shot["end_sec"]):
            return shot
    if shots and math.isclose(time_sec, float(shots[-1]["end_sec"]), abs_tol=1e-6):
        return shots[-1]
    return None


def render_frame(plan: dict, root: Path, time_sec: float) -> Image.Image:
    project = plan["project"]
    width, height = [int(v) for v in project.get("canvas", [960, 540])]
    shot = shot_at(plan.get("shots") or [], time_sec)
    if shot is None:
        return Image.new("RGBA", (width, height), (0, 0, 0, 255))
    local_time = time_sec - float(shot["start_sec"])
    background = shot.get("background") or {}
    if background.get("image"):
        bg = load_rgba(str(resolve(root, background["image"]).resolve())).copy()
        canvas = bg.resize((width, height), Image.Resampling.LANCZOS)
    else:
        color = background.get("color", "#000000")
        canvas = Image.new("RGBA", (width, height), color)

    active: list[tuple[int, dict, dict]] = []
    for element in shot.get("elements") or []:
        state = active_state(element, local_time)
        if state is not None:
            active.append((int(state.get("z", element.get("z", 0))), element, state))
    active.sort(key=lambda item: item[0])
    fps = int(project.get("fps", 16))
    for _, element, state in active:
        duration = float(state["end_sec"]) - float(state["start_sec"])
        progress = min(1.0, max(0.0, (local_time - float(state["start_sec"])) / max(duration, 1e-6)))
        transform = interpolate_transform(state, progress)
        transform["opacity"] *= visibility_opacity(state, local_time)
        asset = state_asset(root, state, local_time, fps)
        default_sampling = "nearest" if project.get("style_id") == "pixel-8bit" else "smooth"
        sampling = state.get("sampling", element.get("sampling", default_sampling))
        place(
            canvas,
            asset,
            transform,
            state.get("anchor", element.get("anchor", "bottom-center")),
            sampling,
        )
    return canvas.convert("RGB")


def main() -> None:
    ap = argparse.ArgumentParser(description="Compose compiled_scene_plan.json")
    ap.add_argument("plan", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=None)
    ap.add_argument("--frames-dir", type=Path, default=None)
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--ffmpeg", default="ffmpeg")
    args = ap.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    root = args.plan.parent.resolve()
    project = plan["project"]
    fps = int(project.get("fps", 16))
    duration = float(project.get("duration_sec") or max(float(s["end_sec"]) for s in plan["shots"]))
    frame_count = max(1, math.ceil(duration * fps))
    frames_dir = args.frames_dir or (root / "renders" / "composite_frames")
    frames_dir.mkdir(parents=True, exist_ok=True)
    for old in frames_dir.glob("frame_*.png"):
        old.unlink()
    digits = max(5, len(str(frame_count)))
    for index in range(frame_count):
        image = render_frame(plan, root, index / fps)
        image.save(frames_dir / f"frame_{index + 1:0{digits}d}.png")
        if index == 0 or (index + 1) % max(fps, 1) == 0 or index + 1 == frame_count:
            print(f"rendered {index + 1}/{frame_count}")

    output = args.out or (root / "renders" / "final.mp4")
    if not args.no_video:
        if not shutil.which(args.ffmpeg):
            raise SystemExit(f"ffmpeg not found: {args.ffmpeg}")
        output.parent.mkdir(parents=True, exist_ok=True)
        command = [
            args.ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-framerate",
            str(fps),
            "-i",
            str(frames_dir / f"frame_%0{digits}d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output),
        ]
        subprocess.run(command, check=True)
        print(f"video → {output.resolve()}")
    print(f"OK {frame_count} frames @ {fps}fps → {frames_dir.resolve()}")


if __name__ == "__main__":
    main()
