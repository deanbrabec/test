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

The script locates the face, sizes the crop so the head lands on the framing
rule above, centres it horizontally, resizes with Lanczos and writes an
optimized PNG. Because the sources are studio shots on white, a crop box that
runs past the source edge is padded with white rather than clamped, so the
framing stays exact.

Override the derived name for a single file with `--name "Marc Marquez"`.

Requires `pip install Pillow numpy "opencv-python-headless<5"`.

## Riders

All 22 from the official MotoGP entry list, source photos from motogp.com.

| File | # | Rider | Country | Team |
|---|---|---|---|---|
| `johann_zarco.png` | 5 | Johann Zarco | France | CASTROL Honda LCR |
| `toprak_razgatlioglu.png` | 7 | Toprak Razgatlıoğlu | Türkiye | Prima Pramac Yamaha MotoGP |
| `luca_marini.png` | 10 | Luca Marini | Italy | Honda HRC Castrol |
| `diogo_moreira.png` | 11 | Diogo Moreira | Brazil | Pro Honda LCR |
| `maverick_vinales.png` | 12 | Maverick Viñales | Spain | Red Bull KTM Tech3 |
| `fabio_quartararo.png` | 20 | Fabio Quartararo | France | Monster Energy Yamaha MotoGP |
| `franco_morbidelli.png` | 21 | Franco Morbidelli | Italy | Pertamina Enduro VR46 Racing Team |
| `enea_bastianini.png` | 23 | Enea Bastianini | Italy | Red Bull KTM Tech3 |
| `raul_fernandez.png` | 25 | Raúl Fernández | Spain | SuperFile Trackhouse MotoGP Team |
| `brad_binder.png` | 33 | Brad Binder | South Africa | Red Bull KTM Factory Racing |
| `joan_mir.png` | 36 | Joan Mir | Spain | Honda HRC Castrol |
| `pedro_acosta.png` | 37 | Pedro Acosta | Spain | Red Bull KTM Factory Racing |
| `alex_rins.png` | 42 | Álex Rins | Spain | Monster Energy Yamaha MotoGP |
| `jack_miller.png` | 43 | Jack Miller | Australia | Prima Pramac Yamaha MotoGP |
| `fabio_di_giannantonio.png` | 49 | Fabio Di Giannantonio | Italy | Pertamina Enduro VR46 Racing Team |
| `fermin_aldeguer.png` | 54 | Fermín Aldeguer | Spain | BK8 Gresini Racing MotoGP |
| `francesco_bagnaia.png` | 63 | Francesco Bagnaia | Italy | Ducati Lenovo Team |
| `marco_bezzecchi.png` | 72 | Marco Bezzecchi | Italy | Aprilia Racing |
| `alex_marquez.png` | 73 | Álex Márquez | Spain | BK8 Gresini Racing MotoGP |
| `ai_ogura.png` | 79 | Ai Ogura | Japan | SuperFile Trackhouse MotoGP Team |
| `jorge_martin.png` | 89 | Jorge Martín | Spain | Aprilia Racing |
| `marc_marquez.png` | 93 | Marc Márquez | Spain | Ducati Lenovo Team |
