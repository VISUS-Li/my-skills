#!/usr/bin/env python3
"""Continuity gates: empty frames, scale jitter, consecutive silhouette jump."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def alpha_mask(path: Path, thresh: int = 16) -> np.ndarray:
    a = np.asarray(Image.open(path).convert("RGBA"))[..., 3] > thresh
    return a


def silhouette_height(mask: np.ndarray) -> float:
    ys, xs = np.where(mask)
    if ys.size == 0:
        return 0.0
    return float(ys.max() - ys.min() + 1)


def pair_diff(a: np.ndarray, b: np.ndarray) -> float:
    """Fraction of differing alpha pixels over union bbox (0..1)."""
    if a.shape != b.shape:
        # resize b to a
        bi = Image.fromarray(b.astype(np.uint8) * 255).resize((a.shape[1], a.shape[0]), Image.Resampling.NEAREST)
        b = np.asarray(bi) > 127
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    if union == 0:
        return 1.0
    return float(1.0 - inter / union)


def ghost_score(path: Path) -> float:
    """
    Heuristic: share of 'soft' alpha pixels among all non-zero alpha.
    Blend/afterimage frames tend to have many mid-alpha pixels.
    """
    a = np.asarray(Image.open(path).convert("RGBA"))[..., 3].astype(np.int16)
    nz = a > 8
    if not np.any(nz):
        return 1.0
    soft = (a > 8) & (a < 200)
    return float(soft.sum() / nz.sum())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", type=Path)
    ap.add_argument("--max-scale-jitter", type=float, default=0.25)
    ap.add_argument(
        "--max-pair-diff",
        type=float,
        default=None,
        help="Max silhouette XOR ratio between consecutive frames (e.g. 0.22)",
    )
    ap.add_argument(
        "--max-ghost",
        type=float,
        default=None,
        help="Max soft-alpha ratio (e.g. 0.35); flags blend/afterimage frames",
    )
    ap.add_argument("--write-report", type=Path, default=None)
    args = ap.parse_args()

    files = sorted(args.folder.glob("frame_*.png"))
    if not files:
        files = sorted(args.folder.glob("part_*.png"))
    if len(files) < 2:
        print(f"need ≥2 frames in {args.folder}", file=sys.stderr)
        sys.exit(2)

    masks = [alpha_mask(f) for f in files]
    heights = [(f.name, silhouette_height(m)) for f, m in zip(files, masks)]
    nonzero = [h for _, h in heights if h > 0]
    if not nonzero:
        print("all frames empty", file=sys.stderr)
        sys.exit(2)
    med = float(np.median(nonzero))
    report: dict = {"median_height": med, "frames": [], "pairs": [], "failures": []}

    for f, (name, h) in zip(files, heights):
        if h <= 0:
            report["failures"].append({"file": name, "reason": "empty"})
            continue
        jitter = abs(h / med - 1.0)
        g = ghost_score(f) if args.max_ghost is not None else None
        row = {"file": name, "height": h, "jitter": round(jitter, 4)}
        if g is not None:
            row["ghost"] = round(g, 4)
        report["frames"].append(row)
        if jitter > args.max_scale_jitter:
            report["failures"].append({"file": name, "reason": "scale_jitter", "jitter": jitter})
        if args.max_ghost is not None and g is not None and g > args.max_ghost:
            report["failures"].append(
                {
                    "file": name,
                    "reason": "ghosting",
                    "ghost": g,
                    "hint": "discard; regenerate single crisp pose — do not blend frames",
                }
            )

    if args.max_pair_diff is not None:
        for i in range(len(files) - 1):
            d = pair_diff(masks[i], masks[i + 1])
            row = {
                "a": files[i].name,
                "b": files[i + 1].name,
                "diff": round(d, 4),
            }
            report["pairs"].append(row)
            if d > args.max_pair_diff:
                report["failures"].append(
                    {
                        "file": f"{files[i].name}->{files[i+1].name}",
                        "reason": "pose_jump",
                        "diff": d,
                        "hint": "generate 1–3 bridge frames; do not interpolate across this pair",
                    }
                )

    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.write_report:
        args.write_report.write_text(text, encoding="utf-8")
    print(text)
    if report["failures"]:
        print(f"QA FAIL: {len(report['failures'])} issues", file=sys.stderr)
        sys.exit(1)
    print(f"QA OK: {len(files)} frames, median_h={med:.1f}")


if __name__ == "__main__":
    main()
