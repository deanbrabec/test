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

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1320, 2868
RED = (200, 16, 46)            # sampled from the app's own accent
TOP, BOTTOM = (18, 20, 27), (7, 8, 11)

PHONE_W = 900                  # phone body width on the canvas
PHONE_TOP = 640
PILL_X, PILL_W, PILL_H = 46, 1228, 212
GOLD = (198, 158, 42)
BEZEL = 9                      # red frame thickness
RADIUS = 78


BACKGROUNDS = ("flat", "glow", "rise", "sweep", "vignette")


def background(kind: str) -> Image.Image:
    """Canvas behind the phone. All start from the app's own near-black."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    ny, nx = y / (H - 1), x / (W - 1)

    base = np.zeros((H, W, 3), np.float32)
    for c, (a, b) in enumerate(zip(TOP, BOTTOM)):
        base[..., c] = a + (b - a) * ny

    if kind == "flat":
        out = base
    elif kind == "glow":
        # brand-coloured halo centred behind the phone
        d = np.sqrt(((nx - 0.5) * 1.35) ** 2 + ((ny - 0.46) * 0.95) ** 2)
        g = np.clip(1 - d / 0.62, 0, 1) ** 2.1
        out = base + g[..., None] * np.array(RED, np.float32) * 0.46
    elif kind == "rise":
        # glow climbing from the bottom edge, so the phone sits in light
        g = np.clip((ny - 0.42) / 0.58, 0, 1) ** 1.7
        side = np.clip(1 - np.abs(nx - 0.5) * 1.5, 0, 1)
        out = base + (g * side)[..., None] * np.array(RED, np.float32) * 0.55
    elif kind == "sweep":
        # diagonal band, echoing the livery stripes in the app icon
        dgn = np.clip(1 - np.abs((nx * 0.75 + ny * 0.55) - 0.62) / 0.42, 0, 1) ** 1.6
        out = base + dgn[..., None] * np.array(RED, np.float32) * 0.34
    elif kind == "vignette":
        d = np.sqrt(((nx - 0.5) * 1.1) ** 2 + ((ny - 0.44) * 0.8) ** 2)
        lift = np.clip(1 - d / 0.78, 0, 1) ** 1.5
        out = base * (0.58 + 0.75 * lift[..., None])
        out += lift[..., None] * np.array(RED, np.float32) * 0.12
    else:
        raise ValueError(f"unknown background {kind!r}; pick from {BACKGROUNDS}")

    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


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


def photo_tile(path, h):
    """Rider photo at the 36:25 the app uses, rounded like the app's tiles."""
    img = Image.open(path).convert("RGB")
    w = round(h * img.width / img.height)
    img = img.resize((w, h), Image.LANCZOS).convert("RGBA")
    img.putalpha(rounded((w, h), 18, (255, 255, 255, 255)).split()[-1])
    return img


def render_pill(pill, fonts):
    """Pills carry the same furniture as the rows they lift: photo, two text
    levels, result chips, a split bar. A flat line of text reads as a caption;
    these read as a piece of the product."""
    kind = pill.get("type", "text")
    card = rounded((PILL_W, PILL_H), PILL_H // 2, RED + (255,))
    d = ImageDraw.Draw(card)
    mid = PILL_H // 2
    x = 80

    if kind == "stat":
        f = ImageFont.truetype(fonts["head"], 60)
        lab = pill["label"].upper()
        lw = d.textlength(lab, font=f)
        d.text(((PILL_W - lw) / 2, mid - 74), lab, font=f, fill=(255, 255, 255))
        nf = ImageFont.truetype(fonts["head"], 76)
        d.text((88, mid - 44), pill["left"], font=nf, fill=(255, 255, 255))
        rw = d.textlength(pill["right"], font=nf)
        d.text((PILL_W - 88 - rw, mid - 44), pill["right"], font=nf, fill=(255, 255, 255))
        bx0, bx1, by = 250, PILL_W - 250, mid + 54
        d.rounded_rectangle([bx0, by, bx1, by + 20], radius=10, fill=(255, 255, 255, 70))
        split = bx0 + round((bx1 - bx0) * pill.get("ratio", 0.5))
        d.rounded_rectangle([bx0, by, split, by + 20], radius=10, fill=(255, 255, 255))
        return card

    if pill.get("badge"):
        bf = ImageFont.truetype(fonts["head"], 64)
        d.text((x, mid - 40), pill["badge"], font=bf, fill=(255, 255, 255))
        x += 96

    if pill.get("photo"):
        tile = photo_tile(pill["photo"], 116)
        card.alpha_composite(tile, (x, mid - 58))
        x += tile.width + 34
    elif pill.get("thumb"):
        src = Image.open(pill["thumb"]).convert("RGB").crop(tuple(pill["thumb_box"]))
        th = 132
        tw = round(th * src.width / src.height)
        src = src.resize((tw, th), Image.LANCZOS).convert("RGBA")
        src.putalpha(rounded((tw, th), 18, (255, 255, 255, 255)).split()[-1])
        card.alpha_composite(src, (x, mid - th // 2))
        x += tw + 34

    right_w = 0
    if pill.get("value"):
        vf = ImageFont.truetype(fonts["head"], 60)
        right_w = d.textlength(pill["value"], font=vf) + 80
        d.text((PILL_W - 80 - (right_w - 80), mid - 38), pill["value"], font=vf, fill=(255, 255, 255))
    elif pill.get("chips"):
        cw, gap = 74, 12
        chips = pill["chips"]
        right_w = len(chips) * (cw + gap) + 80
        cx = PILL_W - 80 - len(chips) * (cw + gap) + gap
        cf = ImageFont.truetype(fonts["ui"], 40)
        for c in chips:
            fill = GOLD if c.strip(". ") == "1" else (255, 255, 255, 64)
            d.rounded_rectangle([cx, mid - 37, cx + cw, mid + 37], radius=16, fill=fill)
            tw2 = d.textlength(c, font=cf)
            d.text((cx + (cw - tw2) / 2, mid - 23), c, font=cf, fill=(255, 255, 255))
            cx += cw + gap

    avail = PILL_W - x - right_w - 40
    tf = fit_text(d, pill["title"], fonts["head"], avail, 62, 34)
    sub = pill.get("subtitle")
    if sub:
        # the subtitle has to respect the same column as the title, or it runs
        # under the chips on the right
        sf = fit_text(d, sub, fonts["ui"], avail, 40, 26)
        d.text((x, mid - 62), pill["title"], font=tf, fill=(255, 255, 255))
        d.text((x, mid + 6), sub, font=sf, fill=(255, 255, 255, 205))
    else:
        d.text((x, mid - 34), pill["title"], font=tf, fill=(255, 255, 255))
    return card


def build(entry, fonts, shots_dir, bg="flat") -> Image.Image:
    canvas = background(bg).convert("RGBA")
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
        p = render_pill(pill, fonts)
        py = PHONE_TOP + round(inner_h * pill["at"])
        canvas.alpha_composite(shadow(p, 32, 175), (PILL_X, py + 18))
        canvas.alpha_composite(p, (PILL_X, py))

    return canvas.convert("RGB")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--shots", type=Path, default=Path("store/raw"))
    p.add_argument("-o", "--out-dir", type=Path, default=Path("store/screenshots"))
    p.add_argument("--lang", default="en")
    p.add_argument("--bg", default="flat", choices=BACKGROUNDS)
    p.add_argument("--strings", type=Path,
                   help="locale overrides for headline and pill copy; "
                        "the manifest itself carries the layout and the English text")
    args = p.parse_args(argv)

    spec = json.loads(args.manifest.read_text())
    if args.strings:
        over = json.loads(args.strings.read_text())
        for frame in spec["frames"]:
            key = frame["headline"].lower()
            frame["headline"] = over.get("headlines", {}).get(key, frame["headline"])
            for field, value in over.get("pills", {}).get(key, {}).items():
                frame["pill"][field] = value
    fonts = {k: str(Path(v)) for k, v in spec["fonts"].items()}
    out = args.out_dir / args.lang
    out.mkdir(parents=True, exist_ok=True)

    for i, entry in enumerate(spec["frames"], 1):
        img = build(entry, fonts, args.shots, args.bg)
        dst = out / f"{i:02d}_{entry['headline'].lower()}.png"
        img.save(dst)
        print(f"{dst}  {img.width}x{img.height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
