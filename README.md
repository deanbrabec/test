# MotoGP assets

Rider photos, team logos and circuit maps for the app, sized to match the
existing Formula 1 lists.

## Where things are

| Path | What | Count |
|---|---|---|
| `photos/motogp/drivers/` | Rider thumbnails, PNG | 22 riders × `@2x` + `@3x` |
| `photos/motogp/teams/` | Team logo tiles, PNG | 12 teams × `@2x` + `@3x` |
| `maps/motogp/circuits/` | Circuit outlines, SVG | 22 |
| `maps/motogp/circuits.json` | Circuit name, country, length, direction | 22 entries |
| `tools/` | Scripts that produced all of the above | — |

Each folder has its own README with the full specification:
[`photos/README.md`](photos/README.md) and [`maps/README.md`](maps/README.md).

## Using the assets

**Filenames are the lookup key.** Riders and teams are `name_surname`,
lowercase, ASCII, underscore separated, with the scale suffix:

```
photos/motogp/drivers/marc_marquez@2x.png      72 × 50 px
photos/motogp/drivers/marc_marquez@3x.png     108 × 75 px
photos/motogp/teams/ducati_lenovo@2x.png       72 × 50 px
maps/motogp/circuits/thailand.svg              viewBox 0 0 1000 1000
```

Accents are transliterated, so `Marc Márquez` is `marc_marquez` and
`Toprak Razgatlıoğlu` is `toprak_razgatlioglu`.

**Photos and logos** are 36 × 25 pt at two scales, on a white background,
matching the F1 driver and standings lists. Rider photos are cropped to fill;
team logos are fitted inside with a margin.

**Circuit maps** are a single `<path>` with `fill="none"`, `stroke="#fff"` and
a fixed `stroke-width`, normalised to a 1000 × 1000 viewBox with aspect ratio
kept. The same file works in the small card on the home screen and full width
on race detail. Recolour with `stroke`, or drop the attribute and set it in CSS.

**Circuit data** joins to the maps by `id`, which is also the SVG filename:

```json
{
  "id": "thailand",
  "round": 1,
  "grand_prix": "Thailand",
  "circuit": "Chang International Circuit",
  "country": "Thailand",
  "country_code": "TH",
  "length_km": 4.554,
  "direction": "Clockwise",
  "map": "maps/motogp/circuits/thailand.svg"
}
```

Note that `grand_prix` is the event name and is not always the circuit's
country — the San Marino GP runs at Misano in Italy, and the Catalunya, Aragon
and Valencia GPs all run in Spain. Use `country` / `country_code` for where the
circuit is, `grand_prix` for the label and flag the calendar uses.

## Regenerating or adding assets

The scripts are reproducible: each reads a manifest of crop boxes and rewrites
its outputs, so re-running after editing a manifest is safe.

```bash
pip install Pillow numpy "opencv-python-headless<5" scikit-image

# rider photos - one file per rider, name taken from --name or the filename
python3 tools/prepare_photos.py <rider-images...> -o photos/motogp/drivers

# team logos - crops defined in tools/team_logos.json
python3 tools/prepare_logos.py --manifest tools/team_logos.json \
    --source presentations=<graphic> -o photos/motogp/teams

# circuit maps - cells defined in tools/circuits.json
python3 tools/trace_circuits.py --manifest tools/circuits.json \
    --source <calendar-poster> -o maps/motogp/circuits
```

Both image scripts take `--scales 2 3`, so adding `@1x` or `@4x` is a flag
change rather than a rework. They warn on stderr if a requested scale would
upscale the source.

## Known gaps

- **`lcr_honda` ships as two identical files.** The rider list carries LCR
  twice under different sponsor branding (`castrol_honda_lcr`, `pro_honda_lcr`)
  but every source graphic has only the one LCR mark. Drop a distinct logo in
  for either and it overrides.
- **`castrol_honda_lcr`, `pro_honda_lcr` and `trackhouse` are soft.** They are
  upscaled 1.10× and 1.24× from small tiles in the launch-dates graphic, the
  only source that carries them, and they keep that graphic's background rather
  than a team colour. Press-kit files would fix both.
- **Circuit maps carry the outline only.** No start/finish marker and no sector
  colouring; neither is present in the source poster.
- **No circuit-type field.** Every 2026 MotoGP round is a permanent circuit, so
  it carried no information. It would need to come back if F1 circuits join the
  same schema, since those do vary.
