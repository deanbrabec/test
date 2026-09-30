#!/usr/bin/env python3
"""Compose App Store / Google Play screenshots from raw app screens.

Each frame is a 1320 x 2868 canvas in the FormuLap house style: a heavy italic
uppercase headline, the app screen inside a red-framed phone, and a red pill
floating over one row that breaks past the phone's left edge.

    python3 tools/build_screenshots.py --manifest store/frames.json \\
        -o store/screenshots
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1320, 2868
RED = (200, 16, 46)            # sampled from the app's own accent
TOP, BOTTOM = (18, 20, 27), (7, 8, 11)

PHONE_W = 900                  # phone body width on the canvas
PHONE_TOP = 640
BEZEL = 9                      # red frame thickness
RADIUS = 78


def gradient() -> Image.Image:
    g = Image.new("RGB", (1, H))
    for y in range(H):
        t = y / (H - 1)
        g.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(TOP, BOTTOM)))
    return g.resize((W, H))


def rounded(size, radius, fill) -> Image.Image:
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1],
                                          radius=radius, fill=fill)
    return img


def shadow(img: Image.Image, blur: int, alpha: int) -> Image.Image:
    a = img.split()[-1].point(lambda v: min(alpha, v))
    s = Image.new("RGBA", img.size, (0, 0, 0, 0))
    s.putalpha(a)
    return s.filter(ImageFilter.GaussianBlur(blur))


def fit_text(draw, text, font_path, box_w, start, min_size=28):
    """Largest size at which `text` fits `box_w`."""
    size = start
    while size > min_size:
        f = ImageFont.truetype(font_path, size)
        if draw.textlength(text, font=f) <= box_w:
            return f
        size -= 2
    return ImageFont.truetype(font_path, min_size)


def clean_status_bar(shot: Image.Image, font_path: str) -> Image.Image:
    """Repaint the captured status bar.

    Raw captures carry whatever the phone was doing — one had a music player
    expanded in the Dynamic Island reading "SHE DOESN'T MIND", and the H2H
    capture was taken on wifi with a different island shape. The signal and
    battery glyphs are also near-black against the dark background, so they
    read as smudges rather than icons. Repaint the whole strip and draw a
    clean one: 9:41, a centred island, full signal and a full battery.
    """
    shot = shot.copy()
    d = ImageDraw.Draw(shot)
    bg = shot.getpixel((170, 30))
    white = (255, 255, 255)

    d.rectangle([0, 0, shot.width, 176], fill=bg)
    d.rounded_rectangle([470, 42, 850, 152], radius=55, fill=(0, 0, 0))
    d.text((96, 60), "9:41", font=ImageFont.truetype(font_path, 58), fill=white)

    x, base = 1044, 116                                   # signal bars
    for i, h in enumerate((18, 27, 36, 45)):
        left = x + i * 24
        d.rounded_rectangle([left, base - h, left + 15, base], radius=5, fill=white)

    bx, by, bw, bh = 1160, 70, 92, 46                     # battery
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=15, outline=white, width=5)
    d.rounded_rectangle([bx + 9, by + 9, bx + bw - 9, by + bh - 9], radius=8, fill=white)
    d.rounded_rectangle([bx + bw + 5, by + 15, bx + bw + 12, by + bh - 15], radius=4, fill=white)
    return shot


def build(entry, fonts, shots_dir) -> Image.Image:
    canvas = gradient().convert("RGBA")
    d = ImageDraw.Draw(canvas)

    # headline
    head = entry["headline"].upper()
    f = fit_text(d, head, fonts["head"], W - 200, 190)
    tw = d.textlength(head, font=f)
    box = f.getbbox(head)
    d.text(((W - tw) / 2, 300 - box[1]), head, font=f, fill=(255, 255, 255))

    # phone
    shot = Image.open(shots_dir / entry["screen"]).convert("RGB")
    shot = clean_status_bar(shot, fonts["ui"])
    inner_w = PHONE_W - 2 * BEZEL
    inner_h = round(inner_w * shot.height / shot.width)
    screen = shot.resize((inner_w, inner_h), Image.LANCZOS)
    mask = rounded((inner_w, inner_h), RADIUS - BEZEL, (255, 255, 255, 255))
    screen.putalpha(mask.split()[-1])

    body = rounded((PHONE_W, inner_h + 2 * BEZEL), RADIUS, RED + (255,))
    body.alpha_composite(screen, (BEZEL, BEZEL))

    px = (W - PHONE_W) // 2
    canvas.alpha_composite(shadow(body, 42, 150), (px, PHONE_TOP + 22))
    canvas.alpha_composite(body, (px, PHONE_TOP))

    # highlight pill, breaking past the phone's left edge
    pill = entry.get("pill")
    if pill:
        pw, ph = W - 2 * 46, 156
        p = rounded((pw, ph), ph // 2, RED + (255,))
        pd = ImageDraw.Draw(p)
        left = pill["left"]
        lf = fit_text(pd, left, fonts["pill"], pw - 380, 62)
        lb = lf.getbbox(left)
        pd.text((72, (ph - (lb[3] - lb[1])) / 2 - lb[1]), left, font=lf, fill=(255, 255, 255))
        if pill.get("right"):
            rf = ImageFont.truetype(fonts["pill"], 62)
            rb = rf.getbbox(pill["right"])
            rw = pd.textlength(pill["right"], font=rf)
            pd.text((pw - 72 - rw, (ph - (rb[3] - rb[1])) / 2 - rb[1]),
                    pill["right"], font=rf, fill=(255, 255, 255))
        py = PHONE_TOP + round(inner_h * pill["at"])
        canvas.alpha_composite(shadow(p, 30, 170), (46, py + 16))
        canvas.alpha_composite(p, (46, py))

    return canvas.convert("RGB")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--shots", type=Path, default=Path("store/raw"))
    p.add_argument("-o", "--out-dir", type=Path, default=Path("store/screenshots"))
    p.add_argument("--lang", default="en")
    args = p.parse_args(argv)

    spec = json.loads(args.manifest.read_text())
    fonts = {k: str(Path(v)) for k, v in spec["fonts"].items()}
    out = args.out_dir / args.lang
    out.mkdir(parents=True, exist_ok=True)

    for i, entry in enumerate(spec["frames"], 1):
        img = build(entry, fonts, args.shots)
        dst = out / f"{i:02d}_{entry['headline'].lower()}.png"
        img.save(dst)
        print(f"{dst}  {img.width}x{img.height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
