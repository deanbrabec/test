#!/usr/bin/env python3
"""Check every store asset against the rules each console enforces.

Both stores reject on upload rather than at review, so this catches the things
that would send you back round the loop: wrong size for the slot, an alpha
channel, or — the one that is easy to miss — an aspect ratio Google Play will
not take, which the App Store's own 6.9" frame exceeds.

    python3 tools/check_assets.py
"""
import argparse
import sys
from pathlib import Path

from PIL import Image

# slot -> (exact size or None, store)
SLOTS = {
    "screenshots/appstore":    ((1320, 2868), "apple"),
    "screenshots/ipad":        ((2064, 2752), "apple"),
    "screenshots/play":        (None,         "play"),
    "screenshots/play-tablet": (None,         "play"),
}
PLAY_MIN, PLAY_MAX, PLAY_RATIO = 320, 3840, 2.0
# Play documents 8MB per screenshot. Apple's own specification page states no
# file-size limit at all, and third-party guides disagree with each other
# (8, 10 and 30MB are all in circulation), so hold both stores to the smallest
# published figure rather than trusting the generous ones.
MAX_BYTES = 8 * 1024 * 1024


def check(root: Path) -> list:
    problems = []
    for slot, (exact, store) in SLOTS.items():
        files = sorted((root / slot).rglob("*.png"))
        if not files:
            problems.append(f"{slot}: no files")
            continue
        sizes, modes = {f.size for f in map(Image.open, files)}, set()
        for f in files:
            im = Image.open(f)
            modes.add(im.mode)
            w, h = im.size
            if im.mode not in ("RGB", "L"):
                problems.append(f"{f}: mode {im.mode} — both stores reject alpha")
            if exact and im.size != exact:
                problems.append(f"{f}: {w}x{h}, slot needs {exact[0]}x{exact[1]}")
            if f.stat().st_size > MAX_BYTES:
                problems.append(f"{f}: {f.stat().st_size//1024}KB over the 8MB cap")
            if store == "play":
                if min(w, h) < PLAY_MIN or max(w, h) > PLAY_MAX:
                    problems.append(f"{f}: {w}x{h} outside Play's {PLAY_MIN}–{PLAY_MAX}px")
                if max(w, h) / min(w, h) > PLAY_RATIO:
                    problems.append(f"{f}: {max(w,h)/min(w,h):.2f}:1 — Play caps at 2:1")
        ratio = max(max(s) / min(s) for s in sizes)
        locales = {p.parent.name for p in files}
        biggest = max(f.stat().st_size for f in files)
        print(f"{slot:26s} {len(files):4d} files  {len(locales):2d} locales  "
              f"{sizes}  {ratio:.2f}:1  {modes}  max {biggest//1024}KB "
              f"({100*biggest/MAX_BYTES:.0f}% of cap)")

    fg = root / "feature_graphic.png"
    if fg.is_file():
        im = Image.open(fg)
        ok = im.size == (1024, 500) and im.mode == "RGB"
        print(f"{'feature_graphic.png':26s}    1 file            {im.size}  {im.mode}  "
              f"max {fg.stat().st_size//1024}KB")
        if not ok:
            problems.append(f"{fg}: must be exactly 1024x500 RGB")
    else:
        problems.append("feature_graphic.png missing — Google Play requires it")
    return problems


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", type=Path, default=Path("store"))
    args = p.parse_args(argv)
    problems = check(args.root)
    print()
    if problems:
        for pr in problems[:20]:
            print("FAIL:", pr)
        if len(problems) > 20:
            print(f"... and {len(problems)-20} more")
        return 1
    print("every asset passes both stores' upload rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
