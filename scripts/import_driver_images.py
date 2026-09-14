#!/usr/bin/env python3
"""Import MotoGP rider photos from motorsport.com standings and normalise them.

Pipeline
--------
1. Read the standings page and collect every rider's detail-page URL.
2. Open each rider detail page and locate the rider photo.
3. Flatten the photo onto a solid white background.
4. Resize to 36x26 at 3x device scale -> 108x78 px.
5. Save as PNG named ``firstname_lastname.png``.

Only dependency beyond the standard library is Pillow::

    pip install pillow

Usage::

    python3 scripts/import_driver_images.py
    python3 scripts/import_driver_images.py --out drivers --scale 3
    python3 scripts/import_driver_images.py --list riders.csv   # offline: "Name,image_url" per line
    python3 scripts/import_driver_images.py --dry-run           # scrape only, download nothing
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image

STANDINGS_URL = "https://www.motorsport.com/motogp/standings/2026/"

# Logical size requested by the design, and the pixel density multiplier.
TARGET_W = 36
TARGET_H = 26
DEFAULT_SCALE = 3

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)
REQUEST_TIMEOUT = 30
RETRIES = 4
THROTTLE_SECONDS = 0.5


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
def fetch(url: str, *, binary: bool = False):
    """GET a URL with retries and exponential backoff."""
    last_error: Exception | None = None
    for attempt in range(RETRIES):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": STANDINGS_URL,
                },
            )
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                payload = response.read()
            return payload if binary else payload.decode("utf-8", "replace")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as error:
            last_error = error
            if attempt == RETRIES - 1:
                break
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}: {last_error}")


# --------------------------------------------------------------------------- #
# Scraping
# --------------------------------------------------------------------------- #
@dataclass
class Rider:
    name: str
    detail_url: str
    image_url: str | None = None


DRIVER_LINK_RE = re.compile(
    r'<a[^>]+href="(?P<href>[^"]*?/(?:driver|rider)/[^"?#]+/?)"[^>]*>(?P<label>.*?)</a>',
    re.I | re.S,
)
TAG_RE = re.compile(r"<[^>]+>")


def clean_text(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", fragment))).strip()


def slug_to_name(href: str) -> str:
    slug = href.rstrip("/").rsplit("/", 1)[-1]
    return " ".join(part.capitalize() for part in slug.split("-") if part)


def parse_standings(page: str, base_url: str) -> list[Rider]:
    """Collect rider detail links, preserving standings order and skipping dupes."""
    riders: list[Rider] = []
    seen: set[str] = set()
    for match in DRIVER_LINK_RE.finditer(page):
        href = urllib.parse.urljoin(base_url, html.unescape(match.group("href")))
        if href in seen:
            continue
        label = clean_text(match.group("label"))
        # Link labels are sometimes just a flag or a number; fall back to the slug.
        if len(label) < 3 or not re.search(r"[A-Za-z]{2}", label):
            label = slug_to_name(href)
        seen.add(href)
        riders.append(Rider(name=label, detail_url=href))
    return riders


OG_IMAGE_RE = re.compile(
    r'<meta[^>]+(?:property|name)="og:image"[^>]+content="([^"]+)"', re.I
)
OG_IMAGE_REVERSED_RE = re.compile(
    r'<meta[^>]+content="([^"]+)"[^>]+(?:property|name)="og:image"', re.I
)
JSONLD_RE = re.compile(
    r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', re.I | re.S
)
IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.I)
ATTR_RE = re.compile(r'(\w[\w:-]*)\s*=\s*"([^"]*)"')


def _walk_jsonld(node) -> str | None:
    """Depth-first search for an ``image`` value in a JSON-LD blob."""
    if isinstance(node, dict):
        image = node.get("image")
        if isinstance(image, str):
            return image
        if isinstance(image, dict) and isinstance(image.get("url"), str):
            return image["url"]
        if isinstance(image, list) and image:
            first = image[0]
            if isinstance(first, str):
                return first
            if isinstance(first, dict) and isinstance(first.get("url"), str):
                return first["url"]
        for value in node.values():
            found = _walk_jsonld(value)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _walk_jsonld(value)
            if found:
                return found
    return None


def _best_from_srcset(srcset: str) -> str | None:
    """Pick the highest-width candidate out of a srcset attribute."""
    best_url, best_width = None, -1
    for candidate in srcset.split(","):
        parts = candidate.split()
        if not parts:
            continue
        url = parts[0]
        width = 0
        if len(parts) > 1 and parts[1].endswith("w"):
            try:
                width = int(parts[1][:-1])
            except ValueError:
                width = 0
        if width >= best_width:
            best_url, best_width = url, width
    return best_url


def find_image_url(page: str, base_url: str) -> str | None:
    """Locate the rider photo, trying the most reliable sources first."""
    for pattern in (OG_IMAGE_RE, OG_IMAGE_REVERSED_RE):
        match = pattern.search(page)
        if match:
            return urllib.parse.urljoin(base_url, html.unescape(match.group(1)))

    for block in JSONLD_RE.findall(page):
        try:
            data = json.loads(block.strip())
        except json.JSONDecodeError:
            continue
        image = _walk_jsonld(data)
        if image:
            return urllib.parse.urljoin(base_url, image)

    # Last resort: the first <img> that looks like a portrait/profile asset.
    for tag in IMG_TAG_RE.findall(page):
        attrs = {key.lower(): value for key, value in ATTR_RE.findall(tag)}
        haystack = " ".join(
            attrs.get(key, "") for key in ("class", "alt", "id", "src", "data-src")
        ).lower()
        if not any(
            hint in haystack
            for hint in ("driver", "rider", "profile", "portrait", "photo", "avatar", "hero")
        ):
            continue
        source = (
            _best_from_srcset(attrs["srcset"])
            if attrs.get("srcset")
            else attrs.get("src") or attrs.get("data-src")
        )
        if source and not source.startswith("data:"):
            return urllib.parse.urljoin(base_url, html.unescape(source))
    return None


# --------------------------------------------------------------------------- #
# Naming
# --------------------------------------------------------------------------- #
def to_filename(name: str) -> str:
    """'Marc Márquez' -> 'marc_marquez'. Accents stripped, tokens underscored."""
    decomposed = unicodedata.normalize("NFKD", name)
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")
    tokens = re.findall(r"[A-Za-z0-9]+", ascii_only)
    return "_".join(token.lower() for token in tokens) or "unknown"


# --------------------------------------------------------------------------- #
# Image processing
# --------------------------------------------------------------------------- #
def normalise(payload: bytes, width: int, height: int, mode: str) -> Image.Image:
    """Flatten onto white and fit into an exact width x height canvas."""
    source = Image.open(BytesIO(payload))
    source = source.convert("RGBA")

    canvas = Image.new("RGB", (width, height), (255, 255, 255))

    source_ratio = source.width / source.height
    target_ratio = width / height

    if mode == "cover":
        # Fill the canvas, cropping the overflowing axis.
        if source_ratio > target_ratio:
            new_height = height
            new_width = max(1, round(height * source_ratio))
        else:
            new_width = width
            new_height = max(1, round(width / source_ratio))
    else:  # contain - keep the whole photo, letterbox with white
        if source_ratio > target_ratio:
            new_width = width
            new_height = max(1, round(width / source_ratio))
        else:
            new_height = height
            new_width = max(1, round(height * source_ratio))

    resized = source.resize((new_width, new_height), Image.LANCZOS)
    offset = ((width - new_width) // 2, (height - new_height) // 2)
    # Paste with the alpha channel as mask so transparency becomes white.
    canvas.paste(resized.convert("RGB"), offset, resized.split()[3])
    return canvas


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def load_riders(args) -> list[Rider]:
    if args.list:
        riders = []
        with open(args.list, newline="", encoding="utf-8") as handle:
            for row in csv.reader(handle):
                if len(row) >= 2 and row[0].strip() and not row[0].lstrip().startswith("#"):
                    riders.append(
                        Rider(name=row[0].strip(), detail_url="", image_url=row[1].strip())
                    )
        return riders

    print(f"Reading standings: {args.standings}")
    riders = parse_standings(fetch(args.standings), args.standings)
    if not riders:
        raise SystemExit(
            "No rider detail links found on the standings page.\n"
            "The page markup has probably changed - adjust DRIVER_LINK_RE, or feed "
            "the riders in manually with --list."
        )
    print(f"Found {len(riders)} riders")
    return riders


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--standings", default=STANDINGS_URL, help="standings page URL")
    parser.add_argument("--out", default="drivers", help="output folder (default: drivers)")
    parser.add_argument("--scale", type=int, default=DEFAULT_SCALE, help="pixel density (default: 3)")
    parser.add_argument(
        "--fit",
        choices=("contain", "cover"),
        default="contain",
        help="contain keeps the whole photo on white; cover fills and crops",
    )
    parser.add_argument("--list", help="CSV of 'Name,image_url' to use instead of scraping")
    parser.add_argument("--dry-run", action="store_true", help="resolve URLs but write nothing")
    parser.add_argument("--limit", type=int, help="only process the first N riders")
    args = parser.parse_args()

    width = TARGET_W * args.scale
    height = TARGET_H * args.scale
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    riders = load_riders(args)
    if args.limit:
        riders = riders[: args.limit]

    print(f"Output: {out_dir}/  ({TARGET_W}x{TARGET_H} @{args.scale}x = {width}x{height} px, white background)\n")

    written, failed = 0, []
    for index, rider in enumerate(riders, start=1):
        filename = to_filename(rider.name)
        label = f"[{index}/{len(riders)}] {rider.name} -> {filename}.png"
        try:
            if rider.image_url is None:
                detail = fetch(rider.detail_url)
                rider.image_url = find_image_url(detail, rider.detail_url)
                time.sleep(THROTTLE_SECONDS)
            if not rider.image_url:
                raise RuntimeError("no photo found on the detail page")

            if args.dry_run:
                print(f"{label}  [dry-run] {rider.image_url}")
                continue

            image = normalise(fetch(rider.image_url, binary=True), width, height, args.fit)
            destination = out_dir / f"{filename}.png"
            image.save(destination, "PNG", optimize=True)
            written += 1
            print(f"{label}  OK ({destination.stat().st_size} B)")
            time.sleep(THROTTLE_SECONDS)
        except Exception as error:  # keep going; report at the end
            failed.append((rider.name, str(error)))
            print(f"{label}  FAILED: {error}", file=sys.stderr)

    print(f"\nDone: {written} written, {len(failed)} failed")
    for name, error in failed:
        print(f"  - {name}: {error}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
