"""soft_cap under each Fashion Sense hair policy, plus the felt control.

The question this answers is one the framework can settle directly and that we
spent four capture sessions attacking as a silhouette problem: does the cap
stop reading as buried under the hairstyle when the hairstyle is hidden, or
when the head itself is drawn bald?

Geometry is IDENTICAL across the three cap entries. Only HideHair /
UseBaldHead differ, so the comparison isolates the policy.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import authored, hairpolicy, pngio
from build_authored_fs_pack import fit_for, MODS

PACK = Path("test-packs/fashionsense/RNG-HairPolicy")
UNIQUE_ID = "RNGClothing.FashionSense.HairPolicy"
PAL = "EVERYDAY_STONE_BLUE"
ORDER = ["front", "right", "left", "back"]
KEYS = {"front": "FrontHat", "right": "RightHat",
        "left": "LeftHat", "back": "BackHat"}


# The four states under test.  Flags are written out explicitly rather than
# going through hairpolicy.flags(), because this experiment exists to test an
# assumption baked into that helper: it treats BALD as implying HideHair, on
# the reasoning that the hairstyle would otherwise still draw over the bald
# head.  That has never been verified, so C isolates UseBaldHead on its own.
STATES = {
    "KEEP": {"HideHair": False},
    "HIDE": {"HideHair": True, "UseBaldHead": False},
    "BALD": {"HideHair": False, "UseBaldHead": True},
}


def hat_json(g, name, state):
    w, h = g.base.size
    dx, dy = fit_for(g.base.name)
    out = {"Name": name, "Format": "7.5.0",
           "Tags": ["RNG Clothing", "Hair Policy", g.base.name, state]}
    for i, d in enumerate(authored.ATLAS_ORDER):
        out[KEYS[d]] = {
            "DisableGrayscale": True,
            **STATES[state],
            "HatSize": {"Width": w, "Length": h},
            "StartingPosition": {"X": 0, "Y": i * h},
            "HeadPosition": {"X": int(dx), "Y": int(dy)},
        }
    return out


def main():
    install = "--install" in sys.argv
    if PACK.exists():
        shutil.rmtree(PACK)
    (PACK / "Hats").mkdir(parents=True, exist_ok=True)
    (PACK / "manifest.json").write_text(json.dumps({
        "Name": "RNG Hair Policy Check",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "soft_cap under KEEP / HIDE / BALD, with felt_hat as control.",
        "UniqueID": UNIQUE_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                           "MinimumVersion": "7.5.0"},
    }, indent=2))

    cap = authored.build("soft_cap", PAL)
    felt = authored.build("felt_hat", PAL)
    entries = [("HairACapKeep", "A KEEP (hair normal)", cap, "KEEP"),
               ("HairBCapHide", "B HIDE (HideHair only)", cap, "HIDE"),
               ("HairCCapBald", "C BALD (UseBaldHead only)", cap, "BALD"),
               ("HairDFelt", "D felt control (unchanged)", felt, "KEEP")]
    trace = []
    for folder, label, g, policy in entries:
        d = PACK / "Hats" / folder
        d.mkdir(parents=True, exist_ok=True)
        pngio.write_rgba_png(d / "hat.png", authored.atlas(g))
        (d / "hat.json").write_text(json.dumps(hat_json(g, label, policy), indent=2))
        trace.append({"folder": folder, "label": label, "base": g.base.name,
                      "state": policy, "flags": STATES[policy]})
        print(f"  {folder:16s} {label:32s} {STATES[policy]}")
    (PACK / "trace.json").write_text(json.dumps(trace, indent=2))
    if install:
        dest = MODS / PACK.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(PACK, dest)
        print("installed ->", dest)


if __name__ == "__main__":
    main()
