# Store metadata

Working spec for the App Store and Google Play listings. Requirements checked
against Apple and Google developer documentation, September 2026.

## Text fields and limits

| Field | App Store | Google Play | Indexed for search? |
|---|---|---|---|
| App name / title | 30 | 30 | **Yes — heaviest weight on both** |
| Subtitle | 30 | — | **Yes (Apple)** |
| Short description | — | 80 | **Yes (Google)** |
| Keywords | 100, comma-separated | — | **Yes (Apple), not shown to users** |
| Full description | 4000 | 4000 | **Google yes, Apple NO** |
| Promotional text | 170 | — | No; editable without a release |

### The one thing that changes how we write these

**Apple does not index the description. Google does.** So the same copy cannot
serve both:

- **Apple**: ranking terms have to live in the name, subtitle and the 100-char
  keywords field. The description is pure persuasion — it wins the download,
  not the ranking.
- **Google**: the full description *is* the ranking surface. Terms need to
  appear naturally in the body copy, at a sane density.

Apple's keyword rules: no plurals of words already present, no category names,
no the word "app", no duplicates across name/subtitle/keywords (they are
already combined when indexing), comma-separated with no spaces.

## Graphics

| Asset | App Store | Google Play |
|---|---|---|
| Icon | 1024 × 1024, no alpha | 512 × 512, 32-bit PNG, < 1024 KB |
| Feature graphic | — | **1024 × 500, required**, no transparency |
| Phone screenshots | 1–10 per size | 2–8 (min 2, 8 max) |
| Tablet screenshots | Required if the app runs on iPad | Optional unless tablet-optimised |

### Screenshot sizes

**App Store — iPhone 6.9" is the one to make: 1320 × 2868 px.** Everything
smaller is auto-scaled from it. 6.5" (1284 × 2778) is only needed if 6.9" is
absent. iPad 13" (2064 × 2752) is required only if the app ships for iPad.

**Google Play** is flexible: any side ≥ 320 px, no side > 3840 px, ratio within
2:1. The 1320 × 2868 iPhone frames can be reused directly.

Both stores: JPEG or 24-bit PNG, **no alpha channel**.

From March 31 2026 Google Play renders icons with a 30% corner radius
automatically — the source icon should be a full square with no baked-in
rounding.

## Screenshot set

Five frames, matching the FormuLap set:

| # | Screen | Carries |
|---|---|---|
| 1 | Races | the calendar and circuit maps |
| 2 | Riders | rider list and photos |
| 3 | Teams | team standings and logos |
| 4 | News | news feed |
| 5 | H2H | head-to-head comparison |

Frame 1 does most of the work — it is what shows in search results.

### The FormuLap frame, as observed

Each frame is one composition on a 1320 × 2868 canvas:

| Element | Treatment |
|---|---|
| Canvas | near-black, sampled ≈ `#0E0F12` |
| Headline | white, heavy **italic uppercase**, centred, in the top eighth |
| Device | iPhone mockup with a **red** frame rather than the usual silver or black — this is what makes the set recognisable |
| Screen | the real app UI, dark theme, status bar reading 9:41 |
| Highlight | a rounded **red pill** floating over one row and breaking past the phone's left edge, pulling the eye to a single fact |
| Variant | the Drivers frame swaps the red pill for a dark card holding two rows |

Accent red sampled from the pills ≈ `#AE2318`, but that is measured off a
screenshot of the store page, so it has been through a scrim and JPEG. The
exact brand red should come from the design file rather than from this.

FormuLap runs seven frames (Races, Chat, Drivers, Teams, News, Polls, H2H).
MotoLap takes the five above.

## Languages

Eleven, matching the in-app language list. Store locale codes differ between
the two consoles:

| Language | App Store | Google Play |
|---|---|---|
| Czech | `cs` | `cs-CZ` |
| English | `en-US` | `en-US` |
| Portuguese (Brazil) | `pt-BR` | `pt-BR` |
| German | `de-DE` | `de-DE` |
| Dutch | `nl-NL` | `nl-NL` |
| French | `fr-FR` | `fr-FR` |
| Italian | `it` | `it-IT` |
| Spanish | `es-ES` | `es-ES` |
| Polish | `pl` | `pl-PL` |
| Hungarian | `hu` | `hu-HU` |
| Turkish | `tr` | `tr-TR` |

### What this costs, and what it buys

**Cost:** screenshots carry a headline, so the set is localised too —
5 frames × 11 languages = **55 exports** per store size.

**Buys:** on the App Store every localisation has its own name, subtitle and
keywords, so eleven locales is 11 × (30 + 30 + 100) characters of indexed
metadata rather than one set.

**Free extra:** App Store English variants (`en-GB`, `en-AU`, `en-CA`) are
separate *metadata* localisations — adding them needs no app change and no new
in-app translation, but gives a distinct keyword set in the UK, Australian and
Canadian storefronts. The app stays English in all of them. Worth taking.

## Naming constraint

The app name must not contain "MotoGP".

### Disclaimer

FormuLap carries an unofficial-app disclaimer in Settings, naming the marks and
their owner. MotoLap needs the same, in-app and repeated at the foot of both
store descriptions — reviewers look for it, and it is the thing that makes a
descriptive use of the mark defensible rather than a claim of affiliation.

FormuLap's wording, for reference:

> This app is unofficial and is not associated in any way with the Formula One
> group of companies. F1, FORMULA ONE, FORMULA 1, FIA FORMULA ONE WORLD
> CHAMPIONSHIP, GRAND PRIX, FORMULA ONE PADDOCK CLUB, PADDOCK CLUB and related
> marks are trademarks of Formula One Licensing B.V.

The MotoGP equivalent has a wrinkle: the marks (MOTOGP, MOTO2, MOTO3) are
registered to **Dorna Sports, S.L.**, but Dorna rebranded during 2026, after
the ownership change, to trade as **MotoGP Sports Entertainment Group**. The
registrations still name Dorna Sports, S.L., so that is the entity to attribute
to — but this is worth a lawyer's eye before it ships, not mine.

## Building the screenshots

```bash
python3 tools/build_screenshots.py --manifest store/frames.json \
    --shots store/raw -o store/screenshots --lang en
```

`store/raw/` holds the untouched app captures, `store/frames.json` says which
screen each frame uses, its headline and its pill copy. Output is
`store/screenshots/<lang>/`.

`--bg` picks the canvas behind the phone:

| Value | Look | Notes |
|---|---|---|
| `flat` | vertical dark gradient | clean, but reads as empty at thumbnail size |
| `glow` | brand-red halo behind the phone | premium, subtle — almost indistinguishable from `flat` when small |
| **`rise`** | **red climbing from the bottom edge** | **current default.** Warm, the phone sits in light |
| `sweep` | diagonal red band | the most distinctive at thumbnail size |
| `vignette` | centre lifted, corners dropped | subtle depth only |

The first one to three frames appear in App Store search results at a fraction
of full size, so the background is doing ASO work, not only decoration —
`flat` and `glow` become indistinguishable at that scale. Switching is one
flag; nothing else in the build depends on it.

The builder repaints the status bar on every frame. The raw captures were taken
on a real phone, so one carried a music player expanded in the Dynamic Island
reading "SHE DOESN'T MIND", the H2H one was on wifi with a different island
shape, and the signal and battery glyphs are near-black against the dark UI, so
they read as smudges. Each frame gets a clean 9:41, a centred island, full
signal and a full battery instead.

Headline font is Poppins ExtraBold Italic, chosen to match the FormuLap
lettering. If FormuLap uses something else, swap the file in `store/fonts/`.

## Still needed

- [ ] The list of languages to localise into
- [ ] Final app name
- [ ] Category, age rating, support URL, privacy policy URL
