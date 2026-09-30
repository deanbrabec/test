# Uploading to the stores

Everything in this folder is final and needs no editing. This is the order to
work through and which file goes in which field.

## What is here

```
store/
  listing/paste/<locale>.md    ← work from these; every field ready to copy
  listing/<locale>.json        source of truth behind the paste sheets
  screenshots/appstore/<locale>/   5 frames, 1320 × 2868
  screenshots/play/<locale>/       5 frames, 1320 × 2620
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

Apple's wording is *"Required if app runs on iPad."* If MotoLap ships for iPad
— FormuLap does, its store page lists "iPhone, iPad" — then the 13" size is
compulsory and the version cannot be submitted without it:

**2064 × 2752** portrait (2048 × 2732 is also accepted). Apple scales the
smaller iPad sizes from it.

**This set is not in the repo**, because building it needs iPad captures of
the app. If the app has a native iPad layout, those frames have to show it;
screenshots of a phone layout would not represent what an iPad user gets. If
the app is iPhone-only and merely runs on iPad in compatibility mode, the phone
composition is representative and can be re-rendered at the iPad canvas with
`--size 2064x2752`.

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

Not compulsory, but consequential: without them an app can be filtered out of
the large-screen experience, and large-screen quality feeds ranking and
featuring for tablet and Chromebook users. Play asks for at least four, at
1200 × 1920 (7") or 1600 × 2560 (10"). Same dependency as iPad — it needs
tablet captures of the app.

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
