# Circuit maps

Track outlines for the race detail screen, as SVG.

```
maps/
  motogp/
    circuits/     # 22 circuits of the 2026 calendar
```

## Format

| | |
|---|---|
| Format | SVG, `viewBox="0 0 1000 1000"` |
| Geometry | one `<path>`, `fill="none"`, `stroke="#fff"`, `stroke-width="14"` |
| Background | none — the path is drawn on whatever is behind it |
| Filename | `country.svg`, lowercase ASCII, underscore separated |

Each circuit is scaled to fit the viewBox with its aspect ratio kept, and
centred, so the same file works in the small card on the home screen and full
width on race detail. Recolour with `stroke`, or drop the attribute and set
`stroke` in CSS. Average file is 6.6 KB, 145 KB for all 22.

## How they are traced

```bash
python3 tools/trace_circuits.py --manifest tools/circuits.json \
    --source <2026-calendar-poster.jpg> -o maps/motogp/circuits
```

The poster draws each circuit as a thin white stroke on black.
`tools/circuits.json` holds one cell box per circuit.

Tracing that stroke's *outline* would give a closed ribbon — two lines, whose
apparent weight would grow with display size. Instead the stroke is reduced to
its **centreline** and emitted as a single path with a fixed stroke width, so
the circuit stays a constant-weight line at any size.

1. Threshold at 170. The poster's watermarks are mid-grey (48–140) and the
   circuit stroke is near-white, so this drops them cleanly.
2. Upscale 6× before thresholding, so the centreline lands sub-pixel rather
   than snapping to the source grid.
3. Keep the largest connected component — this is what rejects the date text
   bleeding in from the neighbouring row's banner.
4. Skeletonise to a 1px centreline, walk it into an ordered path (preferring
   the straightest continuation, so a self-crossing circuit like Malaysia does
   not derail the walk), smooth, resample to 150 points, smooth again.
5. Emit as Catmull-Rom through those points, written as cubic Béziers.

## Fidelity

Measured centreline-to-centreline against the source, as a percentage of each
circuit's bounding box:

| | mean deviation | 99th percentile |
|---|---|---|
| best (`brazil`) | 0.28% | 1.37% |
| worst (`hungary`, `malaysia`) | 0.81% | 3.00% |

All 22 sit under 1% mean. The peaks are at tight hairpins, where the smoothing
rounds the corner slightly — the poster is 750 × 1000, so a circuit is only
about 130 × 80 px before upscaling, and a hairpin there is a handful of pixels.
A higher-resolution source, or official circuit vectors, would sharpen those
corners; nothing else about the shapes would change.

The traces carry the outline only. The start/finish marker and the sector
colouring visible in the app's F1 maps are not in this source.

## Circuit data

`maps/motogp/circuits.json` carries what the race detail screen shows — length
and direction — plus the circuit name, country and the path to its SVG. One
entry per circuit, `id` matching the SVG filename:

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

Three things worth knowing about the data:

- **`length_km` is the layout MotoGP races**, which is not always the venue's
  headline figure. Lusail is 5.419 km on the current layout, not the 5.380 km
  of the 2004–2022 one; Balaton Park's motorcycle layout is 4.075 km, not the
  4.115 km full circuit.
- **There is no circuit-type field.** No 2026 MotoGP round is a street circuit,
  so the value was `Permanent` for all 22 and carried no information. If F1
  circuits are ever added to this schema it needs to come back for those —
  the app shows Madring as a street circuit.
- **`grand_prix` is the event name, not always the circuit's country.** The San
  Marino GP runs at Misano in Italy, and the Catalunya, Aragon and Valencia GPs
  all run in Spain. `country` / `country_code` give where the circuit actually
  is; use `grand_prix` for the label and flag the calendar uses.
