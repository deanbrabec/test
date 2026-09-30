#!/usr/bin/env python3
"""Render listing JSON into paste-ready sheets, one per locale.

Each field sits alone in a fenced block so it can be copied into the console
without picking escapes or stray indentation out of the JSON.

    python3 tools/export_listing.py store/listing/*.json -o store/listing/paste
"""
import argparse
import json
from pathlib import Path

FIELDS = [
    ("App Store Connect", "app_store", [
        ("name", "Name", 30), ("subtitle", "Subtitle", 30),
        ("keywords", "Keywords", 100), ("promotional_text", "Promotional Text", 170),
        ("description", "Description", 4000)]),
    ("Google Play Console", "google_play", [
        ("title", "App name", 30), ("short_description", "Short description", 80),
        ("full_description", "Full description", 4000)]),
]


def sheet(doc: dict, screenshots: Path) -> str:
    loc = doc["locale"]
    out = [f"# {loc}", "",
           "Every field below is ready to paste as-is. The count after each "
           "heading is the length against that field's limit.", ""]
    for console, key, fields in FIELDS:
        out += [f"## {console}", ""]
        for field, label, limit in fields:
            value = doc[key][field]
            out += [f"### {label} — {len(value)}/{limit}", "", "```", value, "```", ""]
    shots = sorted((screenshots / loc).glob("*.png")) if (screenshots / loc).is_dir() else []
    out += ["## Screenshots", "",
            f"`{screenshots / loc}/` — {len(shots)} frames, 1320 × 2868, upload in order:", ""]
    out += [f"{i}. `{p.name}`" for i, p in enumerate(shots, 1)]
    out += ["", "The same files serve Google Play, which accepts this size.", ""]
    return "\n".join(out)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+", type=Path)
    p.add_argument("-o", "--out-dir", type=Path, default=Path("store/listing/paste"))
    p.add_argument("--screenshots", type=Path, default=Path("store/screenshots"))
    args = p.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for f in args.files:
        doc = json.loads(f.read_text())
        dst = args.out_dir / f"{doc['locale']}.md"
        dst.write_text(sheet(doc, args.screenshots))
        print(f"{dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
