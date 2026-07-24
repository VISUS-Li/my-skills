#!/usr/bin/env python3
"""从 take_a / take_b 文件夹选出跳跃更小的 take 序列。"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def list_frames(folder: Path) -> list[Path]:
    files = sorted(folder.glob("frame_*.png"))
    return files


def alpha_mask(path: Path, thresh: int = 16) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"))[..., 3] > thresh


def pair_diff(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        bi = Image.fromarray(b.astype(np.uint8) * 255).resize(
            (a.shape[1], a.shape[0]), Image.Resampling.NEAREST
        )
        b = np.asarray(bi) > 127
    union = np.logical_or(a, b).sum()
    if union == 0:
        return 1.0
    return float(1.0 - np.logical_and(a, b).sum() / union)


def ghost_score(path: Path) -> float:
    a = np.asarray(Image.open(path).convert("RGBA"))[..., 3].astype(np.int16)
    nz = a > 8
    if not np.any(nz):
        return 1.0
    soft = (a > 8) & (a < 200)
    return float(soft.sum() / nz.sum())


def score_take(files: list[Path]) -> dict:
    if len(files) < 2:
        return {"mean_pair_diff": 1.0, "mean_ghost": 1.0, "n": len(files)}
    masks = [alpha_mask(f) for f in files]
    diffs = [pair_diff(masks[i], masks[i + 1]) for i in range(len(masks) - 1)]
    ghosts = [ghost_score(f) for f in files]
    return {
        "mean_pair_diff": float(np.mean(diffs)),
        "max_pair_diff": float(np.max(diffs)),
        "mean_ghost": float(np.mean(ghosts)),
        "n": len(files),
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Choose take_a or take_b by lower mean consecutive silhouette jump"
    )
    ap.add_argument(
        "takes_dir",
        type=Path,
        help="Folder containing take_a/ and take_b/ (each with frame_*.png)",
    )
    ap.add_argument("-o", "--out", type=Path, required=True, help="Output ordered/ folder")
    ap.add_argument(
        "--prefer",
        choices=["auto", "take_a", "take_b"],
        default="auto",
        help="Force a take, or auto-pick by score",
    )
    args = ap.parse_args()

    takes = {}
    for name in ("take_a", "take_b"):
        p = args.takes_dir / name
        if p.is_dir():
            frames = list_frames(p)
            if frames:
                takes[name] = frames

    if not takes:
        print(f"no take_a/take_b frames under {args.takes_dir}", file=sys.stderr)
        sys.exit(2)

    scores = {k: score_take(v) for k, v in takes.items()}
    if args.prefer != "auto" and args.prefer in takes:
        winner = args.prefer
    else:
        # lower mean_pair_diff wins; tie-break lower ghost
        winner = min(
            scores.keys(),
            key=lambda k: (scores[k]["mean_pair_diff"], scores[k]["mean_ghost"]),
        )

    args.out.mkdir(parents=True, exist_ok=True)
    for i, src in enumerate(takes[winner], start=1):
        dst = args.out / f"frame_{i:02d}.png"
        shutil.copy2(src, dst)

    report = {"winner": winner, "scores": scores, "copied": len(takes[winner])}
    (args.out / "pick_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"OK {winner} → {args.out} ({len(takes[winner])} frames)")


if __name__ == "__main__":
    main()
