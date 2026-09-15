"""Build the Source-Backed V2 comparison pack: NEUTRAL renders only.

The point is the in-game comparison against the untouched source packs, so each
item here must be the source's own pixels AND its own rendering semantics:
source HeadPosition, grayscale/tint left exactly as the source declares it, no
palette, no material, no decals. Layout is the only change (four stacked
frames; a Flipped view materialised as a mirrored frame).

    python3 tools/build_source_backed_pack.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from v5 import source_backed as sbm  # noqa: E402
from v5.pngio import write_rgba_png  # noqa: E402

PACK = os.path.join(ROOT, "test-packs", "fashionsense", "RNG-SourceBacked-V2")
UNIQUE_ID = "RNGClothing.FashionSense.SourceBackedV2"
ITEMS = [("beret_02", "SB2Beret02Neutral"), ("beret_01", "SB2Beret01Neutral")]


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
    trace = []
    for name, app in ITEMS:
        b = sbm.load_one(name)
        r = sbm.render(b)
        d = os.path.join(PACK, "Hats", app)
        os.makedirs(d, exist_ok=True)
        write_rgba_png(os.path.join(d, "hat.png"), sbm.sheet(r))
        with open(os.path.join(d, "hat.json"), "w") as fh:
            json.dump(sbm.hat_json(r, app, ["RNG Clothing", "Source-Backed V2", name, "neutral",
                                            f"{b.classification}-ONLY source"]), fh, indent=2)
            fh.write("\n")
        trace.append({"appearance": app, "base": name, "source": b.source_png, "source_md5": b.source_md5,
                      "baked": r.baked, "placement": {v: b.placement(v) for v in sbm.MODEL_OF},
                      "placement_origin": "override" if b.placement_override else "source hat.json"})
        print(f"  {app:20} {name}  baked={r.baked}  HeadPosition {b.placement('front')}")
    with open(os.path.join(PACK, "TRACEABILITY.json"), "w") as fh:
        json.dump(trace, fh, indent=2)
        fh.write("\n")
    print(f"wrote {PACK}")


if __name__ == "__main__":
    main()
