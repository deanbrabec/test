#!/usr/bin/env python3
"""Check store listing copy against each field's hard limit.

Both consoles silently truncate or reject over-length fields, and the App
Store's keyword rules are easy to break by accident, so this runs the checks
that a console only tells you about at upload time.

    python3 tools/check_listing.py store/listing/*.json
"""
import argparse
import json
import re
import sys
from pathlib import Path

LIMITS = {
    "app_store": {"name": 30, "subtitle": 30, "keywords": 100,
                  "promotional_text": 170, "description": 4000},
    "google_play": {"title": 30, "short_description": 80, "full_description": 4000},
}


def check(path: Path) -> list:
    doc = json.loads(path.read_text())
    problems = []
    print(f"\n{path}  ({doc.get('locale', '?')})")
    for store, fields in LIMITS.items():
        for field, limit in fields.items():
            value = doc.get(store, {}).get(field)
            if value is None:
                problems.append(f"{path.name}: {store}.{field} missing")
                print(f"  {store+'.'+field:32s} MISSING")
                continue
            n = len(value)
            bad = n > limit
            problems += [f"{path.name}: {store}.{field} is {n}, limit {limit}"] * bad
            print(f"  {store+'.'+field:32s} {n:5d} / {limit:<5d} {'OVER' if bad else ''}")

    kw = doc.get("app_store", {}).get("keywords", "")
    if kw:
        terms = [t.strip() for t in kw.split(",")]
        if " , " in kw or ", " in kw:
            problems.append(f"{path.name}: keywords use ', ' — the space is a wasted character")
            print("  keywords: remove the space after each comma")
        # Apple indexes name + subtitle + keywords together, so a word repeated
        # across them buys nothing and costs characters. Compare whole tokens,
        # not substrings: "gp" is not a repeat of "MotoGP", and "race" is not a
        # repeat of "racing".
        blob = (doc["app_store"]["name"] + " " + doc["app_store"]["subtitle"]).lower()
        words = set(re.findall(r"[a-z0-9]+", blob))
        dupes = sorted({t for t in terms
                        if t and set(re.findall(r"[a-z0-9]+", t.lower())) <= words})
        if dupes:
            problems.append(f"{path.name}: keywords repeat name/subtitle terms: {dupes}")
            print(f"  keywords repeat the name or subtitle: {', '.join(dupes)}")
    return problems


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+", type=Path)
    args = p.parse_args(argv)
    problems = [pr for f in args.files for pr in check(f)]
    print("\n" + ("\n".join("FAIL: " + p for p in problems) if problems
                  else "all fields within limits"))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
