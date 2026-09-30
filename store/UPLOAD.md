# Uploading to the stores

Everything in this folder is final and needs no editing. This is the order to
work through and which file goes in which field.

## What is here

```
store/
  listing/paste/<locale>.md    ← work from these; every field ready to copy
  listing/<locale>.json        source of truth behind the paste sheets
  screenshots/appstore/<locale>/      5 frames, 1320 × 2868   iPhone 6.9"
  screenshots/ipad/<locale>/          5 frames, 2064 × 2752   iPad 13"
  screenshots/play/<locale>/          5 frames, 1320 × 2620   Play phone
  screenshots/play-tablet/<locale>/   5 frames, 1600 × 2560   Play tablet
  feature_graphic.png          1024 × 500, Google Play only
```

Eleven locales, identical in both places:

`cs` `de` `en-US` `es` `fr` `hu` `it` `nl` `pl` `pt-BR` `tr`

Open `store/listing/paste/cs.md` and it holds every Czech field in its own
block, with the character count against that field's limit, then the Czech
screenshot filenames in upload order. Nothing needs editing or unescaping.

## App Store Connect

Per locale, under **App Store → [version] → [language]**:

| Console field | From the paste sheet |
|---|---|
| Name | **Name** |
| Subtitle | **Subtitle** |
| Promotional Text | **Promotional Text** |
| Description | **Description** |
| Keywords | **Keywords** |
| App Previews and Screenshots → iPhone 6.9" | `screenshots/appstore/<locale>/`, 5 files in order |

**Only upload the 6.9" iPhone size.** Apple scales every smaller iPhone from
it, so 6.5", 6.3" and the rest need nothing.

### iPad is mandatory if the app runs on iPad

Apple's wording is *"Required if app runs on iPad."* FormuLap ships for iPad —
its store page lists "iPhone, iPad" — so if MotoLap does the same, the version
cannot be submitted without this set.

| Console field | From |
|---|---|
| App Previews and Screenshots → iPad 13" | `screenshots/ipad/<locale>/`, 5 files in order |

**2064 × 2752**, which is what Apple requires; it scales the smaller iPad sizes
from it.

**Read this before uploading them.** There were no iPad captures of the app, so
these frames put the *phone* UI on an iPad-shaped canvas. That is accurate only
if the app is iPhone-only and runs on iPad in compatibility mode — which is
exactly what an iPad user would see. **If the app has a native iPad layout,
these are misleading and Apple can reject them under 2.3.3**, which requires
screenshots to show the app in use. In that case the set needs re-rendering
from real iPad captures; the command is the same, only `store/raw/` changes.

Locale codes in App Store Connect are `cs`, `de-DE`, `en-US`, `es-ES`, `fr-FR`,
`hu`, `it`, `nl-NL`, `pl`, `pt-BR`, `tr` — Apple drops the region on some of
them, Google does not. The filenames here use the shorter form.

### Worth doing while you are in there

`en-GB`, `en-AU` and `en-CA` are separate **metadata** localisations. Adding
them needs no app change and no new translation — paste the `en-US` sheet into
each — and buys a distinct keyword set in those storefronts. The app stays
English either way.

## Google Play Console

Per locale, under **Grow → Store presence → Main store listing**:

| Console field | From the paste sheet |
|---|---|
| App name | **App name** |
| Short description | **Short description** |
| Full description | **Full description** |
| Phone screenshots | `screenshots/play/<locale>/`, 5 files in order |
| Feature graphic | `store/feature_graphic.png` |

**Use the `play/` set, not the `appstore/` one.** Play refuses any image whose
long side is more than twice its short side, and the App Store 6.9" frame is
2.17:1 — it would be rejected. The `play/` frames are the same composition on a
1320 × 2620 canvas, which is 1.98:1.

Play has no keywords field — the full description is what it indexes, which is
why the Play and App Store descriptions here are written differently rather
than being the same text twice.

### Tablet screenshots on Play

| Console field | From |
|---|---|
| 7-inch tablet screenshots | `screenshots/play-tablet/<locale>/`, 5 files |
| 10-inch tablet screenshots | the same 5 files |

Not compulsory, but without them an app can be filtered out of the large-screen
experience, and large-screen quality feeds ranking and featuring for tablet and
Chromebook users. One 1600 × 2560 set satisfies both slots.

These carry the same caveat as the iPad set: the phone UI on a tablet canvas,
because no tablet captures existed.

Locale codes are `cs-CZ`, `de-DE`, `en-US`, `es-ES`, `fr-FR`, `hu-HU`, `it-IT`,
`nl-NL`, `pl-PL`, `pt-BR`, `tr-TR`.

## Two things that will fail review if changed

**Keep the disclaimer.** Both descriptions end with the unofficial-app notice
attributing the marks to Dorna Sports, S.L. It is what makes a descriptive use
of the trademark defensible rather than a claim of affiliation, and reviewers
look for it. The app carries the same line in Settings.

**Do not put MotoGP in the app name.** It sits in the subtitle, keywords and
both descriptions, which was a deliberate decision. The name field is the one
place it must not appear.

## Not in this repo

These have to be filled in from the console, there is nothing here to paste:

- Category and age rating
- Support URL and privacy policy URL
- The app icon — 1024 × 1024 for Apple, 512 × 512 for Play

## Changing anything

The screenshots and the paste sheets are generated, so edit the source and
re-run rather than touching the output:

```bash
# text: edit store/listing/<locale>.json, then
python3 tools/check_listing.py store/listing/*.json
python3 tools/export_listing.py store/listing/*.json -o store/listing/paste

# screenshot copy: edit store/strings/<locale>.json, then
python3 tools/build_screenshots.py --manifest store/frames.json \
    --shots store/raw -o store/screenshots --lang cs --bg rise \
    --strings store/strings/cs.json
```

`check_listing.py` enforces every field limit and the App Store keyword rules.
Run it before uploading — it has already caught over-length keyword lists in
ten locales once.
