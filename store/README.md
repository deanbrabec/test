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
| 2 | Drivers | rider list and photos |
| 3 | Teams | team standings and logos |
| 4 | News | news feed |
| 5 | H2H | head-to-head comparison |

Frame 1 does most of the work — it is what shows in search results.

## Naming constraint

The app name must not contain "MotoGP". See the trademark note below for what
that means for the subtitle and description.

## Still needed

- [ ] FormuLap screenshots as the reference, and the MotoLap equivalents
- [ ] The list of languages to localise into
- [ ] Final app name
- [ ] Category, age rating, support URL, privacy policy URL
