"""Diff what Fashion Sense supports against what our exporters actually emit.

The property matrix comes from the official wiki; the emitted sets are read
out of our own builders.  The point is to find conventions we inferred wrongly
or never knew about, rather than to trust that exporting without an error means
exporting correctly.
"""
from __future__ import annotations

import json
import os
import re
import sys

MATRIX = "references/fashion-sense-official/property_matrix.json"
BUILDERS = {
    "Hats": ["tools/build_authored_fs_pack.py", "tools/build_softcap_size_pack.py",
             "tools/build_source_poc_pack.py"],
    "Shirts": ["tools/build_source_poc_pack.py"],
}
# properties whose absence is a real risk rather than a stylistic choice
CRITICAL = {
    "Scale": "wrong size if the sprite is not authored at 4x the game grid",
    "Flipped": "right/left must be authored separately without it",
    "DrawOrderOverride": "cannot layer against hair/player when needed",
    "HideHair": "hat sits under the hairstyle",
    "UseBaldHead": "hat sits under the hairstyle",
    "HidePlayerBase": "full-body appearances show the farmer underneath",
    "HideWhileSwimming": "appearance persists while swimming",
    "HideWhileWearingBathingSuit": "appearance persists in a bathing suit",
    "ColorMasks": "recolour targets the whole sprite",
    "ColorMaskLayers": "only one colourable section is possible",
    "SkinToneMasks": "skin areas do not follow the player's skin tone",
    "IsPrismatic": "no prismatic option",
    "IdleAnimation": "no idle animation",
    "MovementAnimation": "no movement animation",
    "UniformAnimation": "no always-on animation",
    "RequireAnimationToFinish": "movement animation can cut off early",
    "Item": "appearance cannot also be a wearable in-game item",
    "Tags": "not searchable in the Hand Mirror",
}


def emitted(paths):
    keys = set()
    for p in paths:
        if not os.path.isfile(p):
            continue
        src = open(p).read()
        keys |= set(re.findall(r'"([A-Z][A-Za-z]+)":', src))
    return keys


def main():
    m = json.load(open(MATRIX))
    print(f"{'property':34s} {'FS default':12s} status")
    print("-" * 96)
    rows = []
    for cat, builders in BUILDERS.items():
        props = m["by_type"][cat]
        ours = emitted(builders)
        missing_req = [k for k, v in props.items() if v["required"] and k not in ours]
        missing_crit = [k for k in props if k not in ours and k in CRITICAL]
        unknown = [k for k in ours if k not in props and k not in
                   ("Name", "Format", "Author", "Version", "Description",
                    "UniqueID", "UpdateKeys", "ContentPackFor", "MinimumVersion",
                    "X", "Y", "Width", "Length", "Frame", "Duration")]
        print(f"\n=== {cat}   emitted {len(ours & set(props))}/{len(props)} "
              f"documented properties")
        if missing_req:
            print(f"  MISSING REQUIRED: {missing_req}")
        for k in sorted(missing_crit):
            print(f"  {k:32s} {props[k]['default']:12s} not emitted -> "
                  f"{CRITICAL[k]}")
        if unknown:
            print(f"  emitted but not in the wiki table: {sorted(unknown)}")
        rows.append({"category": cat, "emitted": sorted(ours & set(props)),
                     "missing_required": missing_req,
                     "missing_critical": sorted(missing_crit)})
    json.dump(rows, open("references/fashion-sense-official/exporter_gap.json",
                         "w"), indent=1)
    print("\nwrote references/fashion-sense-official/exporter_gap.json")


if __name__ == "__main__":
    main()
