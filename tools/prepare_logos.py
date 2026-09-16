#!/usr/bin/env python3
"""Fit team logos into the app's tile, matching the F1 standings list.

The tile is the same 36x25 pt as the rider thumbnails, but a logo is fitted
inside it rather than cropped to fill: scaled to sit within a safe area and
centred on white, which is how the F1 team logos are laid out.

Usage:
    python3 tools/prepare_logos.py --manifest tools/team_logos.json \\
        --source presentations=<graphic.webp> \\
        --source launch2026=<graphic.jpg> -o photos/motogp/teams
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

# Soft-key thresholds: below KEY_LO from the backdrop a pixel is background and
# goes fully white, above KEY_HI it is ink and is kept, between the two it fades.
KEY_LO, KEY_HI = 10, 48


def key_out_panel(sheet: np.ndarray, box, inset: int = 0, tol: int = 22) -> Image.Image:
    """Crop `box` out of `sheet`, clearing panel background to white.

    Badges that are rounded or slanted leave some of the presentation graphic's
    background inside their bounding box. Flood-fill each corner, but only when
    that corner matches the panel colour sampled just outside the badge —
    otherwise a badge whose own corner is a pale block (Gresini's title bar)
    would be eaten too.

    The fill gives a hard region; painting it flat white would leave the ragged
    staircase edge of a binary mask, and would strip the antialiased fringe that
    makes small artwork read cleanly. So inside that region each pixel is faded
    towards white by how close it is to the background colour: compression
    mottling in the flat background disappears, while a pixel that is partly
    logo ink keeps that much of its ink.
    """
    x0, y0, x1, y1 = box
    x0, y0, x1, y1 = x0 + inset, y0 + inset, x1 - inset, y1 - inset
    crop = sheet[y0:y1, x0:x1].astype(np.int16)
    h, w = crop.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    probe = 6
    for (cx, cy), (px, py) in (((0, 0), (x0 - probe, y0 - probe)),
                               ((w - 1, 0), (x1 + probe, y0 - probe)),
                               ((0, h - 1), (x0 - probe, y1 + probe)),
                               ((w - 1, h - 1), (x1 + probe, y1 + probe))):
        py = min(max(py, 0), sheet.shape[0] - 1)
        px = min(max(px, 0), sheet.shape[1] - 1)
        if np.abs(crop[cy, cx] - sheet[py, px].astype(np.int16)).max() > tol:
            continue
        cv2.floodFill(crop.astype(np.uint8), mask, (cx, cy), 0, (12,) * 3, (12,) * 3,
                      4 | cv2.FLOODFILL_MASK_ONLY | (255 << 8))

    region = mask[1:-1, 1:-1] > 0
    if not region.any():
        return Image.fromarray(crop.astype(np.uint8)).convert("RGBA")

    # Grow the region by a pixel so the antialiased fringe is faded too.
    region = cv2.dilate(region.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0

    backdrop = np.median(crop[mask[1:-1, 1:-1] > 0], axis=0)
    dist = np.abs(crop - backdrop).max(axis=2)
    keep = np.clip((dist - KEY_LO) / (KEY_HI - KEY_LO), 0, 1)[..., None]
    faded = crop * keep + 255 * (1 - keep)
    out = np.where(region[..., None], faded, crop).astype(np.uint8)
    return trim(Image.fromarray(out).convert("RGBA"))


def hull_out_panel(sheet: np.ndarray, box, thr: int, inset: int = 0) -> Image.Image:
    """Isolate a badge by its convex hull, for badges the flood fill cannot key.

    Where a badge is slanted and the panel behind it is both out of focus and
    the same hue as the badge itself (Honda's red parallelogram on red), there
    is no edge for a flood fill to stop at: a tolerance low enough to spare the
    badge leaves a soft halo, and one high enough to clear it bleeds inside.
    The badge is convex, so take everything far enough from the panel colour,
    hull it, and whiten the outside. The polygon is rasterised at 4x and boxed
    down so its edge lands antialiased rather than as a staircase.
    """
    x0, y0, x1, y1 = box
    crop = sheet[y0 + inset:y1 - inset, x0 + inset:x1 - inset].astype(np.int16)
    h, w = crop.shape[:2]
    corners = np.concatenate([crop[:5, :5].reshape(-1, 3), crop[:5, -5:].reshape(-1, 3),
                              crop[-5:, :5].reshape(-1, 3), crop[-5:, -5:].reshape(-1, 3)])
    panel = np.median(corners, axis=0)
    m = (np.abs(crop - panel).max(axis=2) > thr).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    if count < 2:
        return trim(Image.fromarray(crop.astype(np.uint8)).convert("RGBA"))
    biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    hull = cv2.convexHull(np.column_stack(np.where(labels == biggest))[:, ::-1])

    super_sample = 4
    big = np.zeros((h * super_sample, w * super_sample), np.uint8)
    cv2.fillConvexPoly(big, (hull * super_sample).astype(np.int32), 255)
    alpha = (cv2.resize(big, (w, h), interpolation=cv2.INTER_AREA)
             .astype(float) / 255)[..., None]
    out = crop * alpha + 255 * (1 - alpha)
    return trim(Image.fromarray(out.astype(np.uint8)).convert("RGBA"))


def trim(logo: Image.Image, white: int = 247) -> Image.Image:
    """Drop whitened border so the fit is driven by the artwork, not the crop."""
    a = np.asarray(logo.convert("RGB"))
    ink = a.min(axis=2) < white
    if not ink.any():
        return logo
    rows, cols = np.where(ink.any(axis=1))[0], np.where(ink.any(axis=0))[0]
    return logo.crop((cols.min(), rows.min(), cols.max() + 1, rows.max() + 1))


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
    p.add_argument("--manifest", type=Path, help="JSON of crop boxes into the sources")
    p.add_argument("--source", action="append", default=[], metavar="NAME=PATH",
                   help="a source image the manifest refers to; repeatable")
    p.add_argument("-o", "--out-dir", type=Path, default=Path("photos/motogp/teams"))
    p.add_argument("--pt-width", type=int, default=36)
    p.add_argument("--pt-height", type=int, default=25)
    p.add_argument("--scales", type=int, nargs="+", default=[2, 3])
    p.add_argument("--name", help="output name for a single standalone input")
    args = p.parse_args(argv)

    if args.manifest and not args.source:
        p.error("--manifest needs at least one --source")
    sources = {}
    for spec in args.source:
        name, _, path = spec.partition("=")
        sources[name if path else "main"] = np.asarray(
            Image.open(path or name).convert("RGB"))
    if args.name and len(args.inputs) != 1:
        p.error("--name takes exactly one input file")

    jobs = []
    if args.manifest:
        for entry in json.loads(args.manifest.read_text())["logos"]:
            sheet = sources[entry.get("source", "main")]
            x0, y0, x1, y1 = entry["box"]
            inset = entry.get("inset", 0)
            if entry.get("hull"):
                logo = hull_out_panel(sheet, entry["box"], entry["hull"], inset)
            elif entry.get("key", True):
                logo = key_out_panel(sheet, entry["box"], inset)
            else:
                # The badge IS a coloured block; keying would strip it away.
                logo = Image.fromarray(
                    sheet[y0 + inset:y1 - inset, x0 + inset:x1 - inset]).convert("RGBA")
            jobs.append((entry["name"], logo))
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
