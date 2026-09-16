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
| Background | White, matching the F1 studio shots |

### Framing rule

Measured off the F1 reference and applied by the script, as fractions of the
output height:

| | F1 reference | |
|---|---|---|
| Top of head (hair or cap) | 0.022 | `HEAD_TOP` |
| Chin | 0.674 | `CHIN` |
| Face centre | 0.48 of width | centred |

Shoulders run off the bottom edge; white backdrop fills the sides.

Filenames are transliterated to ASCII: `Marc Márquez` → `marc_marquez.png`,
`Pedro Acosta` → `pedro_acosta.png`.

## Adding photos

Drop the source images anywhere and run:

```bash
python3 tools/prepare_photos.py <source-images...> -o photos/motogp/drivers
```

The script locates the face, sizes the crop so the head lands on the framing
rule above, centres it horizontally, resizes with Lanczos and writes an
optimized PNG. Because the sources are studio shots on white, a crop box that
runs past the source edge is padded with white rather than clamped, so the
framing stays exact.

Override the derived name for a single file with `--name "Marc Marquez"`.

Requires `pip install Pillow numpy "opencv-python-headless<5"`.

## Current riders

| File | Rider | Team |
|---|---|---|
| `marc_marquez.png` | Marc Márquez | Ducati Lenovo |
| `francesco_bagnaia.png` | Francesco Bagnaia | Ducati Lenovo |
| `jorge_martin.png` | Jorge Martín | Aprilia Racing |
| `marco_bezzecchi.png` | Marco Bezzecchi | Aprilia Racing |
| `alex_marquez.png` | Álex Márquez | BK8 Gresini Racing |
