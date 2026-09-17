"""Build neutral Source-Backed V2 proofs for the approved cap source candidates.

These are deliberately neutral: no palette, material, decal, fitting override or
legacy six-step repaint. The output must therefore be the original source art,
with Fashion Sense's flipped Left view materialised as an explicit frame.

    python3 tools/build_cap_source_backed_pack.py
    python3 tools/build_cap_source_backed_pack.py --install
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from v5 import source_backed as sbm  # noqa: E402
from v5.pngio import write_rgba_png  # noqa: E402

PACK = ROOT / "test-packs/fashionsense/RNG-Cap-SourceBacked-V2"
UNIQUE_ID = "RNGClothing.FashionSense.CapSourceBackedV2"
MODS = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods")
ITEMS = (
    ("SB2CapBaseballNeutral", "cap_baseball"),
    ("SB2CapSnapbackNeutral", "cap_snapback"),
)


def main():
    if (PACK / "Hats").exists():
        shutil.rmtree(PACK / "Hats")
    (PACK / "Hats").mkdir(parents=True, exist_ok=True)
    (PACK / "manifest.json").write_text(json.dumps({
        "Name": "RNG Clothing - Cap Source-Backed V2",
        "Author": "RNG Clothing",
        "Version": "0.1.0",
        "Description": "Neutral source-backed proofs for Baseball and Snapback construction masters.",
        "UniqueID": UNIQUE_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"},
    }, indent=2) + "\n")
    trace = []
    for appearance, name in ITEMS:
        b = sbm.load_one(name)
        r = sbm.render(b)
        d = PACK / "Hats" / appearance
        d.mkdir(parents=True, exist_ok=True)
        write_rgba_png(d / "hat.png", sbm.sheet(r))
        (d / "hat.json").write_text(json.dumps(sbm.hat_json(
            r, appearance,
            ["RNG Clothing", "Source-Backed V2", "Cap", name,
             "neutral", f"{b.classification}-ONLY source"]), indent=2) + "\n")
        trace.append({
            "appearance": appearance,
            "base": name,
            "source": b.source_png,
            "source_md5": b.source_md5,
            "baked": r.baked,
            "placement": {v: b.placement(v) for v in sbm.MODEL_OF},
            "mirrored": b.mirrored,
            "dropped": list(r.dropped),
        })
        print(f"{appearance}: {name} md5={b.source_md5} placement={b.placement('front')} dropped={r.dropped}")
    (PACK / "TRACEABILITY.json").write_text(json.dumps(trace, indent=2) + "\n")
    if "--install" in sys.argv:
        dest = MODS / PACK.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(PACK, dest)
        print("installed ->", dest)
    print("wrote", PACK)


if __name__ == "__main__":
    main()
