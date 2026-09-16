#!/usr/bin/env python3
"""Vectorise circuit outlines from a calendar poster into stroked SVG paths.

The poster draws each circuit as a thin white stroke on black. Tracing that
stroke's outline would give a closed ribbon whose apparent line weight grows
with the display size; instead this reduces the stroke to its centreline and
emits a single open/closed path stroked with a fixed width, so the circuit
stays a crisp constant-weight line at any size.

Usage:
    python3 tools/trace_circuits.py --manifest tools/circuits.json \\
        --source <poster.jpg> -o maps/motogp/circuits
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from skimage.morphology import skeletonize

sys.path.insert(0, str(Path(__file__).parent))
from prepare_photos import slugify

UPSCALE = 6          # work above source resolution so the centreline lands sub-pixel
INK = 170            # poster watermarks are mid-grey; the circuit stroke is near-white
VIEW = 1000          # SVG viewBox is normalised to this box
STROKE = 14          # stroke width in viewBox units


def circuit_mask(gray: np.ndarray) -> np.ndarray:
    up = cv2.resize(gray, (gray.shape[1] * UPSCALE, gray.shape[0] * UPSCALE),
                    interpolation=cv2.INTER_CUBIC)
    m = (up > INK).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    if count < 2:
        raise ValueError("no circuit found in cell")
    biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return (labels == biggest).astype(np.uint8)


def order_loop(skel: np.ndarray) -> np.ndarray:
    """Walk the 1px skeleton into an ordered sequence of points."""
    pts = {(int(y), int(x)) for y, x in zip(*np.where(skel))}
    if not pts:
        raise ValueError("empty skeleton")
    neigh = lambda p: [(p[0] + dy, p[1] + dx)
                       for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                       if (dy or dx) and (p[0] + dy, p[1] + dx) in pts]
    # Start at an endpoint if the skeleton is open, else anywhere on the loop.
    ends = [p for p in pts if len(neigh(p)) == 1]
    start = ends[0] if ends else next(iter(pts))
    order, seen, cur = [start], {start}, start
    while True:
        nxt = [q for q in neigh(cur) if q not in seen]
        if not nxt:
            break
        # Prefer the straightest continuation so junctions do not derail the walk.
        if len(order) > 1 and len(nxt) > 1:
            dy, dx = order[-1][0] - order[-2][0], order[-1][1] - order[-2][1]
            nxt.sort(key=lambda q: -((q[0] - cur[0]) * dy + (q[1] - cur[1]) * dx))
        cur = nxt[0]
        order.append(cur)
        seen.add(cur)
    return np.array(order, float)[:, ::-1]      # to (x, y)


def smooth(points: np.ndarray, closed: bool, window: int = 9) -> np.ndarray:
    """Moving average along the path, wrapping when the path is a loop."""
    if len(points) < window * 2:
        return points
    mode = "wrap" if closed else "edge"
    pad = window // 2
    padded = np.pad(points, ((pad, pad), (0, 0)), mode=mode)
    kern = np.ones(window) / window
    return np.stack([np.convolve(padded[:, i], kern, "valid") for i in range(2)], axis=1)


def resample(points: np.ndarray, n: int) -> np.ndarray:
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    if d[-1] == 0:
        return points
    return np.stack([np.interp(np.linspace(0, d[-1], n), d, points[:, i])
                     for i in range(2)], axis=1)


def to_bezier(p: np.ndarray, closed: bool) -> str:
    """Catmull-Rom through the points, written as cubic Beziers."""
    n = len(p)
    idx = lambda i: p[i % n] if closed else p[min(max(i, 0), n - 1)]
    out = [f"M {p[0][0]:.2f} {p[0][1]:.2f}"]
    for i in range(n - (0 if closed else 1)):
        p0, p1, p2, p3 = idx(i - 1), idx(i), idx(i + 1), idx(i + 2)
        c1, c2 = p1 + (p2 - p0) / 6, p2 - (p3 - p1) / 6
        out.append(f"C {c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {p2[0]:.2f} {p2[1]:.2f}")
    if closed:
        out.append("Z")
    return " ".join(out)


def trace(gray: np.ndarray, points: int = 150):
    mask = circuit_mask(gray)
    skel = skeletonize(mask > 0)
    pts = order_loop(skel)
    closed = np.linalg.norm(pts[0] - pts[-1]) < 6 * UPSCALE
    pts = smooth(pts, closed)
    pts = resample(pts, points)
    pts = smooth(pts, closed, 5)

    lo, hi = pts.min(axis=0), pts.max(axis=0)
    scale = (VIEW - 2 * STROKE) / max(hi - lo)
    pts = (pts - (lo + hi) / 2) * scale + VIEW / 2
    return to_bezier(pts, closed), closed


def svg(path: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEW} {VIEW}" '
            f'fill="none">\n  <path d="{path}" stroke="#fff" stroke-width="{STROKE}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>\n</svg>\n')


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("-o", "--out-dir", type=Path, default=Path("maps/motogp/circuits"))
    args = p.parse_args(argv)

    gray = np.asarray(Image.open(args.source).convert("L"))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    failed = 0
    for entry in json.loads(args.manifest.read_text())["circuits"]:
        x0, y0, x1, y1 = entry["box"]
        try:
            d, closed = trace(gray[y0:y1, x0:x1])
        except ValueError as exc:
            print(f"skip {entry['name']}: {exc}", file=sys.stderr)
            failed += 1
            continue
        dst = args.out_dir / f"{slugify(entry['name'])}.svg"
        dst.write_text(svg(d))
        print(f"{slugify(entry['name']):18s} -> {dst.name}  "
              f"{'closed loop' if closed else 'OPEN PATH'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
