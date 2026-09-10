"""Repair farm buildings whose type came from an uninstalled mod.

A building whose `buildingType` has no definition gets no interior map, and the
save then holds a location with a null map -- which is what breaks travel:

    Can't read map property 'DayTiles' for location 'Coop<guid>'
      because the map is null.

The fix is to point the building at the vanilla type with the SAME capacity, so
the interior map resolves and every animal inside stays where it is. Three
fields carry the type per building, and all three must agree:

    <buildingType>   the Data/Buildings key
    <upgradeName>    upgrade tracking
    <name>           on the INDOORS location -- this is the map lookup, and it
                     is a DIFFERENT <name> from the nickname the player gave the
                     building, which appears earlier in the same block

Inert references are deliberately left alone: `firstVisit_*` and
`structureBuilt_*` stat keys and the `constructed` type list are just strings
the game carries around, and rewriting them would edit history rather than
repair it.

Dry run by default. Nothing is written without --apply, and --apply always
writes a timestamped backup first.
"""
from __future__ import annotations

import argparse
import datetime
import os
import re
import shutil
import sys

# vanilla replacements, matched on capacity so no animal is evicted
REPLACEMENTS = {
    "BigPokeCoop": ("Big Coop", 8),
    "BigPokeBarn": ("Big Barn", 8),
}


def find_block(x: str, bt: str):
    i = x.find(f"<buildingType>{bt}</buildingType>")
    if i < 0:
        return None
    s = x.rfind("<Building", 0, i)
    e = x.find("</Building>", i)
    return (s, e) if s >= 0 and e > s else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("save")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    if not os.path.isfile(a.save):
        print(f"no such save: {a.save}")
        return 2
    x = open(a.save, encoding="utf-8", errors="strict").read()
    original = x
    total = 0

    for bad, (good, capacity) in REPLACEMENTS.items():
        span = find_block(x, bad)
        if span is None:
            print(f"{bad:14s} not present — nothing to do")
            continue
        s, e = span
        blk = x[s:e]

        occ = re.search(r"<maxOccupants>(\d+)</maxOccupants>", blk)
        animals = len(re.findall("<FarmAnimal", blk))
        if occ and int(occ.group(1)) != capacity:
            print(f"{bad:14s} REFUSED: capacity is {occ.group(1)}, "
                  f"but {good} holds {capacity}; an animal could be evicted")
            return 3

        changes = []
        new = blk
        for tag in ("buildingType", "upgradeName"):
            pat = f"<{tag}>{bad}</{tag}>"
            if pat in new:
                n = new.count(pat)
                new = new.replace(pat, f"<{tag}>{good}</{tag}>")
                changes.append(f"{tag} x{n}")

        # the indoors location's own name, anchored to uniqueName so the
        # player's nickname for the building is never touched
        pat = re.compile(r"(</uniqueName>\s*<name>)" + re.escape(bad) + r"(</name>)")
        new, n = pat.subn(rf"\1{good}\2", new)
        if n:
            changes.append(f"indoors name x{n}")

        print(f"{bad:14s} -> {good:10s}  capacity {capacity}  "
              f"animals inside {animals:2d}   [{', '.join(changes)}]")
        x = x[:s] + new + x[e:]
        total += len(changes)

    left = {b: x.count(f"<buildingType>{b}</buildingType>") for b in REPLACEMENTS}
    print(f"\nremaining broken buildingType entries: {left}")
    inert = len(re.findall(r"firstVisit_BigPoke|structureBuilt_BigPoke", x))
    print(f"inert stat/mail strings left untouched: {inert}")

    if not a.apply:
        print("\nDRY RUN — nothing written. Re-run with --apply to write.")
        return 0
    if x == original:
        print("\nno change needed")
        return 0

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"{a.save}.backup-{stamp}"
    shutil.copy2(a.save, backup)
    print(f"\nbackup: {backup}")
    tmp = a.save + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(x)
    os.replace(tmp, a.save)
    print(f"written: {a.save}  ({total} field group(s) changed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
