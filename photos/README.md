# Photos

Assets for the app's driver/rider pickers (e.g. the H2H **Select driver** list).

## Layout

```
photos/
  motogp/
    drivers/      # MotoGP rider thumbnails
```

Formula 1 lives alongside this once its assets land (`photos/f1/drivers/`).

## Thumbnail spec

| | |
|---|---|
| Display size | 36 × 25 pt |
| File size | **72 × 50 px** (@2x) |
| Format | PNG |
| Filename | `name_surname.png` — lowercase, ASCII, underscore separated |
| Framing | Head-and-shoulders, same crop style as the F1 list |

Filenames are transliterated to ASCII: `Marc Márquez` → `marc_marquez.png`,
`Pedro Acosta` → `pedro_acosta.png`.

## Adding photos

Drop the source images anywhere and run:

```bash
python3 tools/prepare_photos.py <source-images...> -o photos/motogp/drivers
```

The script center-crops to 36:25, anchors the vertical crop toward the top so
faces stay in frame, resizes with Lanczos and writes an optimized PNG. Override
the derived name for a single file with `--name "Marc Marquez"`, and nudge the
crop with `--focus` (`0` = top, `1` = bottom, default `0.3`).

Requires Pillow: `pip install Pillow`.
