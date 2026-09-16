#!/usr/bin/env python3
"""Fit team logos into the app's tile, matching the F1 standings list.

The tile is the same 36x25 pt as the rider thumbnails, but a logo is fitted
inside it rather than cropped to fill: scaled to sit within a safe area and
centred on white, which is how the F1 team logos are laid out.

Usage:
    python3 tools/prepare_logos.py --manifest tools/team_logos.json \\
        --source <graphic.webp> -o photos/motogp/teams
    python3 tools/prepare_logos.py logo.png --name "Ducati Lenovo"
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from prepare_photos import slugify

# Safe area as a fraction of the tile, measured off the F1 standings tiles
# (widest logo filled 0.97 of the width, tallest 0.86 of the height).
SAFE_W, SAFE_H = 0.94, 0.86


def key_out_panel(sheet: np.ndarray, box, tol: int = 22) -> Image.Image:
    """Crop `box` out of `sheet`, dropping panel gradient left in the corners.

    Badges that are rounded or slanted leave some of the presentation graphic's
    background inside their bounding box. Flood-fill each corner, but only when
    that corner matches the panel colour sampled just outside the badge —
    otherwise a badge whose own corner is a pale block (Gresini's title bar)
    would be eaten too.
    """
    x0, y0, x1, y1 = box
    crop = sheet[y0:y1, x0:x1]
    h, w = crop.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    probe = 6
    for (cx, cy), (px, py) in (((0, 0), (x0 - probe, y0 - probe)),
                               ((w - 1, 0), (x1 + probe, y0 - probe)),
                               ((0, h - 1), (x0 - probe, y1 + probe)),
                               ((w - 1, h - 1), (x1 + probe, y1 + probe))):
        py = min(max(py, 0), sheet.shape[0] - 1)
        px = min(max(px, 0), sheet.shape[1] - 1)
        outside = sheet[py, px].astype(int)
        if np.abs(crop[cy, cx].astype(int) - outside).max() > tol:
            continue
        cv2.floodFill(crop.copy(), mask, (cx, cy), 0, (12,) * 3, (12,) * 3,
                      4 | cv2.FLOODFILL_MASK_ONLY | (255 << 8))

    rgba = np.dstack([crop, np.full((h, w), 255, np.uint8)])
    rgba[..., 3][mask[1:-1, 1:-1] > 0] = 0
    img = Image.fromarray(rgba, "RGBA")
    return img.crop(img.getbbox()) if img.getbbox() else img


def fit(logo: Image.Image, width: int, height: int) -> Image.Image:
    """Scale `logo` to fit the safe area and centre it on a white tile."""
    box_w, box_h = width * SAFE_W, height * SAFE_H
    scale = min(box_w / logo.width, box_h / logo.height)
    w, h = max(1, round(logo.width * scale)), max(1, round(logo.height * scale))

    resized = logo.convert("RGBA").resize((w, h), Image.LANCZOS)
    tile = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    tile.alpha_composite(resized, ((width - w) // 2, (height - h) // 2))
    return tile.convert("RGB")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("inputs", nargs="*", type=Path, help="standalone logo files")
    p.add_argument("--manifest", type=Path, help="JSON of crop boxes into --source")
    p.add_argument("--source", type=Path, help="image the manifest boxes refer to")
    p.add_argument("-o", "--out-dir", type=Path, default=Path("photos/motogp/teams"))
    p.add_argument("--pt-width", type=int, default=36)
    p.add_argument("--pt-height", type=int, default=25)
    p.add_argument("--scales", type=int, nargs="+", default=[2, 3])
    p.add_argument("--name", help="output name for a single standalone input")
    args = p.parse_args(argv)

    if args.manifest and not args.source:
        p.error("--manifest needs --source")
    if args.name and len(args.inputs) != 1:
        p.error("--name takes exactly one input file")

    jobs = []
    if args.manifest:
        sheet = np.asarray(Image.open(args.source).convert("RGB"))
        for entry in json.loads(args.manifest.read_text())["logos"]:
            jobs.append((entry["name"], key_out_panel(sheet, entry["box"])))
    for src in args.inputs:
        jobs.append((args.name or src.stem, Image.open(src)))

    if not jobs:
        p.error("nothing to do: pass image files or --manifest/--source")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for name, logo in jobs:
        slug = slugify(name)
        sizes = []
        for scale in args.scales:
            w, h = args.pt_width * scale, args.pt_height * scale
            need = min(w * SAFE_W / logo.width, h * SAFE_H / logo.height)
            if need > 1:
                print(f"warning: {slug}@{scale}x upscales source by "
                      f"{need:.2f}x", file=sys.stderr)
            fit(logo, w, h).save(args.out_dir / f"{slug}@{scale}x.png", "PNG", optimize=True)
            sizes.append(f"@{scale}x {w}x{h}")
        print(f"{slug}  (source {logo.width}x{logo.height})  " + ", ".join(sizes))
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    raise SystemExit(main())
