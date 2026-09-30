#!/usr/bin/env python3
"""Render the Google Play feature graphic, 1024 x 500.

Play requires this asset and has no App Store equivalent. It is shown at
several sizes and can be cropped at the edges on some surfaces, so everything
that has to be read sits inside the middle 80%.

    python3 tools/build_feature_graphic.py -o store/feature_graphic.png
"""
import argparse
import io
from pathlib import Path

import cairosvg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 500
RED = (200, 16, 46)
TOP, BOTTOM = (18, 20, 27), (7, 8, 11)
SAFE = 0.10                    # keep copy out of this fraction of each edge


def background() -> Image.Image:
    """Same 'rise' treatment as the screenshots, so the set reads as one."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    ny, nx = y / (H - 1), x / (W - 1)
    base = np.zeros((H, W, 3), np.float32)
    for c, (a, b) in enumerate(zip(TOP, BOTTOM)):
        base[..., c] = a + (b - a) * ny
    glow = np.clip((ny - 0.35) / 0.65, 0, 1) ** 1.6
    side = np.clip(1 - np.abs(nx - 0.5) * 1.25, 0, 1)
    out = base + (glow * side)[..., None] * np.array(RED, np.float32) * 0.62
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert("RGBA")


def circuit(path: Path, height: int, opacity: int) -> Image.Image:
    """A circuit outline as a watermark, drawn from the repo's own maps."""
    png = cairosvg.svg2png(url=str(path), output_width=height, output_height=height)
    img = Image.open(io.BytesIO(png)).convert("RGBA")
    a = img.split()[-1].point(lambda v: v * opacity // 255)
    img.putalpha(a)
    return img


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-o", "--out", type=Path, default=Path("store/feature_graphic.png"))
    p.add_argument("--wordmark", default="MotoLap")
    p.add_argument("--tagline", default="Every rider. Every race. Every result.")
    p.add_argument("--map", type=Path, default=Path("maps/motogp/circuits/italy.svg"))
    p.add_argument("--font", type=Path, default=Path("store/fonts/Poppins.ttf"))
    p.add_argument("--font-ui", type=Path, default=Path("store/fonts/Poppins-SemiBold.ttf"))
    p.add_argument("--map-size", type=int, default=470)
    p.add_argument("--map-x", type=int, default=600)
    p.add_argument("--map-y", type=int, default=0)
    p.add_argument("--map-alpha", type=int, default=52)
    p.add_argument("--tagline-size", type=int, default=36)
    args = p.parse_args(argv)

    canvas = background()
    cw = args.map_size
    canvas.alpha_composite(circuit(args.map, cw, args.map_alpha),
                           (args.map_x, (H - cw) // 2 + args.map_y))

    d = ImageDraw.Draw(canvas)
    pad = round(W * SAFE)

    wf = ImageFont.truetype(str(args.font), 104)
    tf = ImageFont.truetype(str(args.font_ui), args.tagline_size)
    wb, tb = wf.getbbox(args.wordmark), tf.getbbox(args.tagline)
    block = (wb[3] - wb[1]) + 26 + (tb[3] - tb[1])
    top = (H - block) // 2

    # red slash, echoing the bar in the app's "m" mark
    sx = pad + 4
    d.polygon([(sx + 26, top - 6), (sx + 56, top - 6),
               (sx + 30, top + block + 6), (sx, top + block + 6)], fill=RED)

    tx = sx + 92
    d.text((tx, top - wb[1]), args.wordmark, font=wf, fill=(255, 255, 255))
    d.text((tx + 4, top + (wb[3] - wb[1]) + 26 - tb[1]), args.tagline,
           font=tf, fill=(255, 255, 255, 216))

    out = canvas.convert("RGB")        # Play rejects transparency
    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.save(args.out)
    print(f"{args.out}  {out.width}x{out.height}  mode={out.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
