#!/usr/bin/env python3
"""Split transparent sticker sheets into individual part_XX.png files."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

try:
    from scipy import ndimage
except Exception:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "scipy", "-q"])
    from scipy import ndimage


def split_sheet(path: Path, out_parent: Path | None = None, min_area: int = 1200, pad: int = 6) -> Path:
    img = Image.open(path).convert("RGBA")
    arr = np.asarray(img)
    alpha = arr[..., 3] > 20
    labeled, n = ndimage.label(alpha)
    parts_dir = (out_parent or path.parent) / f"{path.stem}_parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    for old in parts_dir.glob("*.png"):
        old.unlink()
    saved = 0
    for i in range(1, n + 1):
        ys, xs = np.where(labeled == i)
        if ys.size < min_area:
            continue
        y0, y1 = int(ys.min()), int(ys.max())
        x0, x1 = int(xs.min()), int(xs.max())
        if (x1 - x0) > img.width * 0.92 and (y1 - y0) > img.height * 0.92:
            continue
        y0 = max(0, y0 - pad)
        x0 = max(0, x0 - pad)
        y1 = min(img.height - 1, y1 + pad)
        x1 = min(img.width - 1, x1 + pad)
        crop = arr[y0 : y1 + 1, x0 : x1 + 1].copy()
        mask = labeled[y0 : y1 + 1, x0 : x1 + 1] == i
        crop_alpha = crop[..., 3].copy()
        crop_alpha[~mask] = 0
        crop[..., 3] = crop_alpha
        out = Image.fromarray(crop, "RGBA")
        bb = out.split()[-1].getbbox()
        if bb is None:
            continue
        out = out.crop(bb)
        if out.width * out.height < min_area:
            continue
        saved += 1
        out.save(parts_dir / f"part_{saved:02d}.png")
    print(f"{path.name}: {n} components -> {saved} parts in {parts_dir}")
    return parts_dir


def main() -> None:
    ap = argparse.ArgumentParser(description="Split transparent PNG sticker sheets into parts")
    ap.add_argument("inputs", nargs="+", type=Path, help="Transparent PNG sheets (globs ok via shell)")
    ap.add_argument(
        "-o",
        "--out",
        type=Path,
        default=None,
        help="Parent dir for *_parts folders (default: beside each input)",
    )
    ap.add_argument("--min-area", type=int, default=1200)
    args = ap.parse_args()

    # Expand simple globs if shell did not
    paths: list[Path] = []
    for p in args.inputs:
        if any(ch in str(p) for ch in "*?[]"):
            paths.extend(sorted(Path().glob(str(p))))
            parent = p.parent if p.parent != Path("") else Path(".")
            paths.extend(sorted(parent.glob(p.name)))
        else:
            paths.append(p)
    # de-dupe
    seen = set()
    uniq = []
    for p in paths:
        rp = p.resolve()
        if rp in seen or not p.exists() or p.suffix.lower() != ".png":
            continue
        if "_parts" in p.parts:
            continue
        seen.add(rp)
        uniq.append(p)

    if not uniq:
        print("no PNG inputs found")
        sys.exit(1)

    for p in uniq:
        split_sheet(p, out_parent=args.out, min_area=args.min_area)


if __name__ == "__main__":
    main()
