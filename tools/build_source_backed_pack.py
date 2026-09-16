"""Build the Source-Backed V2 validation pack.

Neutral items are the source's own pixels AND rendering semantics: source
HeadPosition, grayscale/tint exactly as the source declares it, no palette, no
material, no decals. They are the in-game comparison against the untouched
source packs and must not change.

Plaid and knit items exercise authored materials on beret_02. The final three
appearances exercise the player-facing Decorated Beret bucket (ribbon, leaf,
dotted) on the source-backed shape. Neutral items remain untouched comparison
anchors.

    python3 tools/build_source_backed_pack.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from v5 import authored  # noqa: E402
from v5 import source_backed as sbm  # noqa: E402
from v5.pngio import write_rgba_png  # noqa: E402

PACK = os.path.join(ROOT, "test-packs", "fashionsense", "RNG-SourceBacked-V2")
UNIQUE_ID = "RNGClothing.FashionSense.SourceBackedV2"
# (appearance, base, palette id or None, material or None, decal names)
ITEMS = [("SB2Beret02Neutral", "beret_02", None, None, ()),
         ("SB2Beret01Neutral", "beret_01", None, None, ()),
         ("SB2Beret02Plaid", "beret_02", None, "plaid", ()),
         ("SB2Beret02PlaidStoneBlue", "beret_02", "EVERYDAY_STONE_BLUE", "plaid", ()),
         ("SB2Beret02PlaidCocoaGold", "beret_02", "CUTE_COCOA_GOLD", "plaid", ()),
         ("SB2Beret02PlaidRoseCream", "beret_02", "CUTE_ROSE_CREAM", "plaid", ()),
         ("SB2Beret02Knit", "beret_02", None, "knit", ()),
         ("SB2Beret02KnitStoneBlue", "beret_02", "EVERYDAY_STONE_BLUE", "knit", ()),
         ("SB2Beret02KnitCocoaGold", "beret_02", "CUTE_COCOA_GOLD", "knit", ()),
         ("SB2Beret02KnitRoseCream", "beret_02", "CUTE_ROSE_CREAM", "knit", ()),
         ("SB2Beret02DecorRibbon", "beret_02", "CUTE_ROSE_CREAM", None, ("bow_knot",)),
         ("SB2Beret02DecorLeaf", "beret_02", "CUTE_ROSE_CREAM", None, ("leaf_sprig",)),
         ("SB2Beret02DecorDotted", "beret_02", "CUTE_ROSE_CREAM", None, ("beret_dots_small",))]


def main():
    if os.path.isdir(os.path.join(PACK, "Hats")):
        shutil.rmtree(os.path.join(PACK, "Hats"))
    os.makedirs(PACK, exist_ok=True)
    with open(os.path.join(PACK, "manifest.json"), "w") as fh:
        json.dump({"Name": "RNG Clothing - Source-Backed V2 (neutral)",
                   "Author": "RNG Clothing", "Version": "0.1.0",
                   "Description": "Source-backed V2 neutral renders: source pixels, source placement, "
                                  "source tint semantics. For in-game comparison with the source packs.",
                   "UniqueID": UNIQUE_ID, "UpdateKeys": [],
                   "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"}},
                  fh, indent=2)
        fh.write("\n")
    lib = authored.load()
    trace = []
    for app, name, pid, material, decal_names in ITEMS:
        b = sbm.load_one(name)
        pal = next(p for p in lib.palettes if p.id == pid) if pid else None
        decals = tuple(next(d for d in lib.decals if d.name == n) for n in decal_names)
        r = sbm.render(b, pal, material, decals)
        d = os.path.join(PACK, "Hats", app)
        os.makedirs(d, exist_ok=True)
        write_rgba_png(os.path.join(d, "hat.png"), sbm.sheet(r))
        tags = ["RNG Clothing", "Source-Backed V2", name, pid or "unbaked", material or "no material",
                "+".join(decal_names) if decal_names else "plain", f"{b.classification}-ONLY source"]
        with open(os.path.join(d, "hat.json"), "w") as fh:
            json.dump(sbm.hat_json(r, app, tags), fh, indent=2)
            fh.write("\n")
        trace.append({"appearance": app, "base": name, "palette": pid, "material": material,
                      "decals": list(decal_names), "dropped": list(r.dropped),
                      "source": b.source_png, "source_md5": b.source_md5, "baked": r.baked,
                      "material_cells": sum(len(r.changes[v]["material"]) for v in r.changes),
                      "placement": {v: b.placement(v) for v in sbm.MODEL_OF},
                      "placement_origin": "override" if b.placement_override else "source hat.json"})
        print(f"  {app:26} {name}  palette={pid}  material={material}  decals={decal_names}  baked={r.baked}  "
              f"HeadPosition {b.placement('front')}")
    with open(os.path.join(PACK, "TRACEABILITY.json"), "w") as fh:
        json.dump(trace, fh, indent=2)
        fh.write("\n")
    print(f"wrote {PACK}")


if __name__ == "__main__":
    main()
