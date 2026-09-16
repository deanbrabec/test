#!/usr/bin/env python3
"""Crop and resize rider/driver photos to the app's thumbnail spec.

Output: 36x25 pt PNGs at each requested scale, named name_surname@2x.png,
name_surname@3x.png and so on.

The crop reproduces the framing used by the existing F1 "Select driver" list:
the head sits centred in a wide white box, top of the head ~6% down from the
top edge, chin at ~40%, shoulders running off the bottom edge. Sources may be
either transparent cut-outs (the official MotoGP press shots) or studio photos
on a white backdrop; both are flattened onto white, which lets the crop box
extend past the image edge and be padded seamlessly rather than clamped.

Usage:
    python3 tools/prepare_photos.py <image>... -o photos/motogp/drivers
    python3 tools/prepare_photos.py rider.webp --name "Marc Marquez"
    python3 tools/prepare_photos.py rider.webp --scales 1 2 3
"""
import argparse
import re
import sys
import unicodedata
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

# Framing constants, measured off the F1 reference screenshot.
HEAD_TOP = 0.03   # top of head, as a fraction of output height
CHIN = 0.68       # chin, as a fraction of output height
WHITE_CUTOFF = 235  # below this on any channel counts as subject, not backdrop


def slugify(value: str) -> str:
    """'Marc Márquez' / 'Marc-Marquez.WEBP' -> 'marc_marquez'."""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def load(path) -> tuple:
    """Return (RGB-on-white array, subject mask).

    Transparent cut-outs carry an exact silhouette in the alpha channel; for
    opaque sources fall back to "anything darker than the backdrop".
    """
    img = Image.open(path)
    if img.mode in ("RGBA", "LA") or "transparency" in img.info:
        img = img.convert("RGBA")
        alpha = np.array(img)[..., 3]
        if (alpha < 128).any():
            flat = Image.alpha_composite(
                Image.new("RGBA", img.size, (255, 255, 255, 255)), img)
            return np.array(flat.convert("RGB")), alpha > 128
    rgb = np.array(img.convert("RGB"))
    return rgb, rgb.min(axis=2) < WHITE_CUTOFF


def find_head(rgb: np.ndarray, subject: np.ndarray):
    """Return (head_top_y, chin_y, face_centre_x) in source pixels."""
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = cascade.detectMultiScale(gray, 1.05, 6, minSize=(40, 40))
    if len(faces) == 0:
        raise ValueError("no face detected")
    # Studio portraits put the head at the top; logos on leathers can also
    # trip the detector, so take the highest box.
    fx, fy, fw, fh = min(faces, key=lambda b: b[1])
    cx, chin = fx + fw / 2, fy + fh

    # Top of the head (hair or cap) from the subject silhouette, limited to a
    # column around the face so a raised elbow or shoulder can't win.
    lo, hi = int(max(0, cx - fw * 0.7)), int(min(rgb.shape[1], cx + fw * 0.7))
    rows = np.where(subject[:, lo:hi].any(axis=1))[0]
    head_top = float(rows.min()) if len(rows) else float(fy)
    return head_top, float(chin), float(cx)


def crop(rgb: np.ndarray, subject: np.ndarray, aspect: float) -> Image.Image:
    """Crop to `aspect` (w/h) with the head on the reference framing."""
    head_top, chin, cx = find_head(rgb, subject)

    crop_h = (chin - head_top) / (CHIN - HEAD_TOP)
    crop_w = crop_h * aspect
    top = head_top - HEAD_TOP * crop_h
    left = cx - crop_w / 2

    # Paste onto a white canvas so a crop box running off the source edge is
    # padded with backdrop instead of shifting the framing.
    canvas = Image.new("RGB", (round(crop_w), round(crop_h)), "white")
    canvas.paste(Image.fromarray(rgb), (round(-left), round(-top)))
    return canvas


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("inputs", nargs="+", type=Path, help="source image files")
    p.add_argument("-o", "--out-dir", type=Path, default=Path("photos/motogp/drivers"))
    p.add_argument("--pt-width", type=int, default=36, help="display width in pt (default 36)")
    p.add_argument("--pt-height", type=int, default=25, help="display height in pt (default 25)")
    p.add_argument("--scales", type=int, nargs="+", default=[2, 3],
                   help="pixel scales to emit (default: 2 3)")
    p.add_argument("--name", help="output name for a single input, e.g. 'Marc Marquez'")
    args = p.parse_args(argv)

    if args.name and len(args.inputs) > 1:
        p.error("--name only works with a single input file")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    aspect = args.pt_width / args.pt_height

    failed = 0
    for src in args.inputs:
        name = slugify(args.name or src.stem)
        if not src.is_file() or not name:
            print(f"skip: {src}", file=sys.stderr)
            failed += 1
            continue
        rgb, subject = load(src)
        try:
            box = crop(rgb, subject, aspect)
        except ValueError as exc:
            print(f"skip {src}: {exc}", file=sys.stderr)
            failed += 1
            continue
        sizes = []
        for scale in args.scales:
            w, h = args.pt_width * scale, args.pt_height * scale
            if box.width < w:
                print(f"warning: {name}@{scale}x upscales "
                      f"({box.width}px crop -> {w}px)", file=sys.stderr)
            box.resize((w, h), Image.LANCZOS).save(
                args.out_dir / f"{name}@{scale}x.png", "PNG", optimize=True)
            sizes.append(f"@{scale}x {w}x{h}")
        print(f"{src.name} -> {name}  " + ", ".join(sizes))

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
