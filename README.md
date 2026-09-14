# test

## Driver image import

`scripts/import_driver_images.py` imports MotoGP rider photos from the
motorsport.com standings page and normalises them into a single asset spec.

### What it does

1. Reads <https://www.motorsport.com/motogp/standings/2026/> and collects every
   rider's detail-page link, in standings order.
2. Opens each rider detail page and resolves the rider photo — trying `og:image`
   first, then JSON-LD, then a heuristic `<img>` match as a last resort.
3. Flattens the photo onto a solid white background (transparency becomes white).
4. Resizes to **36 x 26 at @3x = 108 x 78 px**.
5. Saves it to `drivers/` as `firstname_lastname.png` — lowercase, accents
   stripped (`Marc Márquez` -> `marc_marquez.png`).

### Usage

    pip install pillow
    python3 scripts/import_driver_images.py

Options:

| Flag | Purpose |
|------|---------|
| `--out DIR`      | output folder (default `drivers`) |
| `--scale N`      | density multiplier (default `3`, so 108x78) |
| `--fit contain`  | keep the whole photo, letterboxed on white (default) |
| `--fit cover`    | fill the frame, cropping the overflowing axis |
| `--list FILE`    | offline mode: CSV of `Name,image_url` rows, skips scraping |
| `--dry-run`      | resolve photo URLs and print them, write nothing |
| `--limit N`      | only process the first N riders |

The script retries each request 4 times with exponential backoff and throttles
between requests; one rider failing does not abort the run, and every failure is
listed in the summary at the end.

### Network requirement

The import needs outbound HTTPS to `motorsport.com` and its image CDN. In a
sandbox where egress is restricted, run it locally instead, or pass the photo
URLs in directly with `--list`.
