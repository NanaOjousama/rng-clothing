"""Build the isolated four-tier Beret validation pack.

The point of this pack is NOT four nice hats. It is one controlled experiment:
family, shape and palette are held FIXED across all four appearances and only
`quality_tier` moves. If quality were secretly another shape or preset selector,
the base or the palette would change underneath and the pack would show it.

Four appearances, one per tier, plus a TRACEABILITY.json recording exactly what
was held and what varied.

    python3 tools/build_beret_tier_pack.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import authored
from v5.pngio import blank_image, blit, write_rgba_png

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "test-packs", "fashionsense", "RNG-Beret-Family-M1")

# --- the controlled experiment -----------------------------------------------
FAMILY = "beret"
SHAPE = "beret_01"                 # held fixed
PALETTE = "AUTUMN_OCHRE_PLUM"      # held fixed
STYLE = "cottagecore"              # held fixed
SEED = 8                           # held fixed
# ...only this varies:
TIERS = ["Common", "Uncommon", "Rare", "RarePlus"]

HEAD_Y = -2                        # matches the authored-hat checkpoint packs


def sheet_of(g):
    """20x80 four-frame sheet in Fashion Sense stacking order."""
    img = blank_image(20, 80)
    for i, view in enumerate(authored.ATLAS_ORDER):
        blit(img, g.directions[view], 0, i * 20)
    return img


def hat_json(name, g):
    def block(y):
        return {
            "DisableGrayscale": True,
            "HideHair": False,
            "HatSize": {"Width": 20, "Length": 20},
            "StartingPosition": {"X": 0, "Y": y},
            "HeadPosition": {"X": 0, "Y": HEAD_Y},
        }
    return {
        "Name": name,
        "Tags": ["RNG Clothing", "Beret Family M1", FAMILY, g.shape_variant,
                 g.quality_tier, g.material, g.palette.id, g.style,
                 "REFERENCE-ONLY source"],
        "FrontHat": block(0),
        "RightHat": block(20),
        "LeftHat": block(40),
        "BackHat": block(60),
    }


def main():
    lib = authored.load()
    base = next(b for b in lib.family_bases(FAMILY) if b.shape_variant == SHAPE)
    os.makedirs(os.path.join(PACK, "Hats"), exist_ok=True)

    with open(os.path.join(PACK, "manifest.json"), "w") as fh:
        json.dump({
            "Name": "RNG Beret Family M1",
            "Author": "RNG Clothing Experiment",
            "Version": "1.0.0",
            "Description": "Milestone 1: the Beret family shape axis. Four quality "
                           "tiers over ONE fixed shape and palette, to show quality "
                           "varies independently of shape.",
            "UniqueID": "RNGClothing.FashionSense.BeretFamilyM1",
            "UpdateKeys": [],
            "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                               "MinimumVersion": "7.5.0"},
        }, fh, indent=2)
        fh.write("\n")

    rows = []
    for tier in TIERS:
        g = authored.build_tier(FAMILY, SHAPE, PALETTE, tier,
                                seed=SEED, lib=lib, style=STYLE)
        app = f"Beret{tier}"
        d = os.path.join(PACK, "Hats", app)
        os.makedirs(d, exist_ok=True)
        write_rgba_png(os.path.join(d, "hat.png"), sheet_of(g))
        with open(os.path.join(d, "hat.json"), "w") as fh:
            json.dump(hat_json(f"Beret — {tier}", g), fh, indent=2)
            fh.write("\n")
        cells = sum(max(len(x.view_cells(v)) for v in x.views) for x in g.decals)
        rows.append({
            "appearance": app, "quality_tier": tier,
            "family": g.family, "shape_variant": g.shape_variant,
            "palette": g.palette.id, "material": g.material, "style": g.style,
            "decals": [x.name for x in g.decals],
            "motif_classes": sorted({x.motif_class for x in g.decals}),
            "decor_cells": cells,
            "budget": lib.tier(tier)["max_decor_cells"],
            "dropped": [list(x) for x in g.dropped],
        })

    held = {"family": {r["family"] for r in rows},
            "shape_variant": {r["shape_variant"] for r in rows},
            "palette": {r["palette"] for r in rows},
            "style": {r["style"] for r in rows}}
    with open(os.path.join(PACK, "TRACEABILITY.json"), "w") as fh:
        json.dump({
            "purpose": "Axis independence: quality_tier is the ONLY input that "
                       "differs between these four appearances.",
            "held_fixed": {k: sorted(v) for k, v in held.items()},
            "held_fixed_is_actually_fixed": {k: len(v) == 1 for k, v in held.items()},
            "seed": SEED,
            "varied": "quality_tier",
            "source_classification": "REFERENCE — beret_01 derives from "
                                     "hyoung_hats_24, provenance unestablished. "
                                     "Not a shippable production asset.",
            "base_provenance": base.provenance,
            "appearances": rows,
        }, fh, indent=2)
        fh.write("\n")

    print(f"pack  {os.path.relpath(PACK, ROOT)}")
    print(f"held  family={SHAPE and FAMILY}  shape={SHAPE}  palette={PALETTE}  "
          f"style={STYLE}  seed={SEED}")
    print()
    print(f"{'tier':10} {'decor':>6} {'budget':>7}  decals")
    for r in rows:
        print(f"{r['quality_tier']:10} {r['decor_cells']:6} {r['budget']:7}  "
              f"{'+'.join(r['decals']) or '(plain)'}"
              + ("   DROPPED " + str(r["dropped"]) if r["dropped"] else ""))
    assert all(len(v) == 1 for v in held.values()), "the experiment is not controlled"
    print("\ncontrolled: family, shape, palette and style are identical across all four")


if __name__ == "__main__":
    main()
