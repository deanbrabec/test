# Photos

Assets for the app's driver/rider pickers (e.g. the H2H **Select driver** list).

## Layout

```
photos/
  motogp/
    drivers/      # MotoGP rider thumbnails
    teams/        # MotoGP team logos
```

Formula 1 lives alongside this once its assets land (`photos/f1/drivers/`).

## Thumbnail spec

| | |
|---|---|
| Display size | 36 × 25 pt |
| File sizes | **72 × 50 px** (@2x) and **108 × 75 px** (@3x) |
| Format | PNG |
| Filename | `name_surname@2x.png` / `name_surname@3x.png` — lowercase, ASCII, underscore separated |
| Framing | Head-and-shoulders, same crop style as the F1 list |
| Background | White; transparent sources are flattened onto it |

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

Both scales are written from a single crop box, so @2x and @3x are the same
framing at different resolutions. Add or change scales with `--scales 1 2 3`;
the script warns if a requested scale would upscale the source. The official
press shots are 1000 × 700, which leaves the tightest crop a 3.3× downscale at
@3x — no upscaling anywhere in the current set.

The script locates the face, sizes the crop so the head lands on the framing
rule above, centres it horizontally, resizes with Lanczos and writes an
optimized PNG. Because the sources are studio shots on white, a crop box that
runs past the source edge is padded with white rather than clamped, so the
framing stays exact.

Override the derived name for a single file with `--name "Marc Marquez"`.

Requires `pip install Pillow numpy "opencv-python-headless<5"`.

## Riders

All 22 from the official MotoGP entry list, source photos from motogp.com.

| File (`@2x` / `@3x`) | # | Rider | Country | Team |
|---|---|---|---|---|
| `johann_zarco` | 5 | Johann Zarco | France | CASTROL Honda LCR |
| `toprak_razgatlioglu` | 7 | Toprak Razgatlıoğlu | Türkiye | Prima Pramac Yamaha MotoGP |
| `luca_marini` | 10 | Luca Marini | Italy | Honda HRC Castrol |
| `diogo_moreira` | 11 | Diogo Moreira | Brazil | Pro Honda LCR |
| `maverick_vinales` | 12 | Maverick Viñales | Spain | Red Bull KTM Tech3 |
| `fabio_quartararo` | 20 | Fabio Quartararo | France | Monster Energy Yamaha MotoGP |
| `franco_morbidelli` | 21 | Franco Morbidelli | Italy | Pertamina Enduro VR46 Racing Team |
| `enea_bastianini` | 23 | Enea Bastianini | Italy | Red Bull KTM Tech3 |
| `raul_fernandez` | 25 | Raúl Fernández | Spain | SuperFile Trackhouse MotoGP Team |
| `brad_binder` | 33 | Brad Binder | South Africa | Red Bull KTM Factory Racing |
| `joan_mir` | 36 | Joan Mir | Spain | Honda HRC Castrol |
| `pedro_acosta` | 37 | Pedro Acosta | Spain | Red Bull KTM Factory Racing |
| `alex_rins` | 42 | Álex Rins | Spain | Monster Energy Yamaha MotoGP |
| `jack_miller` | 43 | Jack Miller | Australia | Prima Pramac Yamaha MotoGP |
| `fabio_di_giannantonio` | 49 | Fabio Di Giannantonio | Italy | Pertamina Enduro VR46 Racing Team |
| `fermin_aldeguer` | 54 | Fermín Aldeguer | Spain | BK8 Gresini Racing MotoGP |
| `francesco_bagnaia` | 63 | Francesco Bagnaia | Italy | Ducati Lenovo Team |
| `marco_bezzecchi` | 72 | Marco Bezzecchi | Italy | Aprilia Racing |
| `alex_marquez` | 73 | Álex Márquez | Spain | BK8 Gresini Racing MotoGP |
| `ai_ogura` | 79 | Ai Ogura | Japan | SuperFile Trackhouse MotoGP Team |
| `jorge_martin` | 89 | Jorge Martín | Spain | Aprilia Racing |
| `marc_marquez` | 93 | Marc Márquez | Spain | Ducati Lenovo Team |


## Team logos

Twelve tiles for twelve entries in the rider list. Same 36 × 25 pt tile as the
riders, at @2x and @3x, on white.

LCR appears twice under different sponsor branding — `CASTROL Honda LCR` for
Zarco and `Pro Honda LCR` for Moreira — so it gets two tiles. Every source
graphic carries only the one LCR mark, so the two files are currently identical
artwork under the two names; drop a distinct logo in for either and it will
override. A logo is
**fitted** inside the tile rather than cropped to fill it: scaled to sit within
a safe area of 0.94 × 0.86 of the tile and centred, which is how the F1
standings list lays its team logos out (its widest logo fills 0.97 of the
width, its tallest 0.86 of the height).

```bash
python3 tools/prepare_logos.py --manifest tools/team_logos.json \
    --source presentations=<2026-team-presentations.webp> \
    --source launches2025=<2025-team-launches.jpg> \
    --source launch2026=<2026-launch-dates.jpg> \
    -o photos/motogp/teams
```

`tools/team_logos.json` holds one crop box per badge, each naming the source
graphic it came from. Badges that are rounded or slanted keep some of the
graphic's panel gradient inside their bounding box, so each corner is
flood-filled to white — but only when that corner matches the panel colour just
outside the badge, otherwise a badge with a pale block in its own corner
(Gresini's title bar) would be eaten too. Entries with `"key": false` skip that
step because the badge itself is a coloured block.

| File (`@2x` / `@3x`) | Team | Riders |
|---|---|---|
| `ducati_lenovo` | Ducati Lenovo Team | 63, 93 |
| `aprilia_racing` | Aprilia Racing | 72, 89 |
| `red_bull_ktm_factory_racing` | Red Bull KTM Factory Racing | 33, 37 |
| `red_bull_ktm_tech3` | Red Bull KTM Tech3 | 12, 23 |
| `monster_energy_yamaha` | Monster Energy Yamaha MotoGP | 20, 42 |
| `prima_pramac_yamaha` | Prima Pramac Yamaha MotoGP | 7, 43 |
| `pertamina_enduro_vr46` | Pertamina Enduro VR46 Racing Team | 21, 49 |
| `bk8_gresini_racing` | BK8 Gresini Racing MotoGP | 54, 73 |
| `honda_hrc_castrol` | Honda HRC Castrol | 10, 36 |
| `castrol_honda_lcr` | CASTROL Honda LCR | 5 |
| `pro_honda_lcr` | Pro Honda LCR | 11 |
| `trackhouse` | SuperFile Trackhouse MotoGP Team | 25, 79 |

### Source quality

Nine of the eleven are downscaled from a source larger than the tile. Two are
not, and are visibly soft:

| File | Source | @3x scale |
|---|---|---|
| `castrol_honda_lcr` | 2026 launch-dates graphic | 1.10× upscale |
| `pro_honda_lcr` | 2026 launch-dates graphic | 1.10× upscale |
| `trackhouse` | 2026 launch-dates graphic | 1.24× upscale |

Both come from small tiles in the launch-dates graphic, which is the only
source here that carries them at all — the team-presentations graphic sets
Aprilia, LCR and Trackhouse as white wordmarks over a photographed fairing,
with no badge to crop and lettering that would vanish on a white tile. Aprilia
was recovered from the 2025 launches graphic, where it is set in black on a
light background, and needs no upscaling.

The LCR tiles and `trackhouse` also keep their launch-graphic backgrounds (silver
and blue), which are that graphic's styling rather than team colours. Press-kit
files for those two would improve both problems at once:

```bash
python3 tools/prepare_logos.py trackhouse.png --name "Trackhouse"
```
