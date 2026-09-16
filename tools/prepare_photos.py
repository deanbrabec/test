#!/usr/bin/env python3
"""Crop and resize driver photos to the app's thumbnail spec.

Default output: 72x50 px PNG (36x25 pt @2x), named name_surname.png.

Usage:
    python3 tools/prepare_photos.py <input...> -o photos/motogp/drivers
    python3 tools/prepare_photos.py /root/.claude/uploads/*.jpg -o photos/motogp/drivers

Each input file is center-cropped to the target aspect ratio (vertical anchor
biased toward the top so faces stay in frame), resized with Lanczos, and saved
as PNG. The output name is derived from the input filename unless --name is
given for a single file.
"""
import argparse
import re
import sys
import unicodedata
from pathlib import Path

from PIL import Image


def slugify(value: str) -> str:
    """'Marc Márquez' / 'Marc-Marquez.JPG' -> 'marc_marquez'."""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def crop_resize(img: Image.Image, width: int, height: int, focus: float) -> Image.Image:
    img = img.convert("RGBA")
    target = width / height
    src = img.width / img.height

    if src > target:  # too wide -> trim sides, keep the centre
        new_w = round(img.height * target)
        left = (img.width - new_w) // 2
        box = (left, 0, left + new_w, img.height)
    else:  # too tall -> trim top/bottom, anchored by `focus`
        new_h = round(img.width / target)
        top = round((img.height - new_h) * focus)
        top = max(0, min(top, img.height - new_h))
        box = (0, top, img.width, top + new_h)

    return img.crop(box).resize((width, height), Image.LANCZOS)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("inputs", nargs="+", type=Path, help="source image files")
    p.add_argument("-o", "--out-dir", type=Path, default=Path("photos/motogp/drivers"))
    p.add_argument("--width", type=int, default=72, help="output width in px (default 72 = 36pt @2x)")
    p.add_argument("--height", type=int, default=50, help="output height in px (default 50 = 25pt @2x)")
    p.add_argument("--focus", type=float, default=0.3,
                   help="vertical crop anchor, 0=top 1=bottom (default 0.3, keeps faces in frame)")
    p.add_argument("--name", help="output name for a single input, e.g. 'Marc Marquez'")
    args = p.parse_args(argv)

    if args.name and len(args.inputs) > 1:
        p.error("--name only works with a single input file")

    args.out_dir.mkdir(parents=True, exist_ok=True)

    for src in args.inputs:
        if not src.is_file():
            print(f"skip (not a file): {src}", file=sys.stderr)
            continue
        name = slugify(args.name or src.stem)
        if not name:
            print(f"skip (cannot derive a name): {src}", file=sys.stderr)
            continue
        dst = args.out_dir / f"{name}.png"
        with Image.open(src) as img:
            crop_resize(img, args.width, args.height, args.focus).save(dst, "PNG", optimize=True)
        print(f"{src} -> {dst} ({args.width}x{args.height})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
