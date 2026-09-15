"""Build the bare-geometry test pack for the `beret_03` base.

The geometry is now ACCEPTED and this pack tests WEAR READABILITY: whether the
derived contact edge, band and crown shading make the hat read as sitting on the
head rather than pasted over it, and whether the five materials express that
differently without touching the silhouette.

Still no decoration -- quality_tier stays pinned to Common, so nothing in the
frame competes with the shading being judged. Palette and material are the two
axes that move, crossed so each material is seen on more than one colour.

    python3 tools/build_beret03_base_pack.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import authored
from v5.pngio import blank_image, blit, write_rgba_png

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "test-packs", "fashionsense", "RNG-Beret03-Base")

FAMILY = "beret"
SHAPE = "beret_03"
TIER = "Common"          # zero decor budget: geometry only
STYLE = "cute"
SEED = 3

# One near-neutral first so the silhouette reads without colour noise, then a
# spread across the ramp -- pale, mid and dark -- since a rim step that works on
# cream can vanish on chocolate.
PALETTES = ["CUTE_IVORY_BLOSSOM", "CUTE_ROSE_CREAM",
            "CUTE_PERIWINKLE_HEART", "CUTE_COCOA_GOLD"]
# Every material, crossed against the palettes. A material that only ever
# appears on cream proves nothing about whether its texture survives a dark ramp.
MATERIALS = ["felt", "wool", "knit", "plaid", "stitched"]
PROFILE = "cute_beret"

HEAD_Y = -2              # unchanged from the verified authored-hat packs


def sheet_of(g):
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
        "Tags": ["RNG Clothing", "Beret03 Base", FAMILY, g.shape_variant,
                 g.quality_tier, g.palette.id, g.material, "wear readability",
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
            "Name": "RNG Beret03 Base",
            "Author": "RNG Clothing Experiment",
            "Version": "1.0.0",
            "Description": "Bare geometry check for the beret_03 base, ingested "
                           "from the user's drawn directional sheet. No "
                           "decoration: palette varies, nothing else.",
            "UniqueID": "RNGClothing.FashionSense.Beret03Base",
            "UpdateKeys": [],
            "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                               "MinimumVersion": "7.5.0"},
        }, fh, indent=2)
        fh.write("\n")

    rows = []
    for i, mat in enumerate(MATERIALS):
        pal = PALETTES[i % len(PALETTES)]
        g = authored.build_profile(FAMILY, PROFILE, SHAPE, pal, TIER,
                                   treatment=mat, seed=SEED, lib=lib)
        assert not g.decals, f"{mat}: expected bare geometry, got {g.decals}"
        short = pal.replace('CUTE_', '').title().replace('_', '')
        app = f"Beret03{mat.title()}{short}"
        d = os.path.join(PACK, "Hats", app)
        os.makedirs(d, exist_ok=True)
        write_rgba_png(os.path.join(d, "hat.png"), sheet_of(g))
        with open(os.path.join(d, "hat.json"), "w") as fh:
            json.dump(hat_json(f"Beret03 — {mat} — {pal}", g), fh, indent=2)
            fh.write("\n")
        rows.append({"appearance": app, "palette": pal, "material": mat,
                     "shape_variant": g.shape_variant, "decals": []})

    with open(os.path.join(PACK, "TRACEABILITY.json"), "w") as fh:
        json.dump({
            "purpose": "Bare geometry check for beret_03 on the farmer. No "
                       "decoration; palette is the only axis that moves.",
            "what_to_look_for": [
                "the dark contact edge reads as the hat meeting the head, and "
                "keeps the forehead separate from the crown",
                "the lower band is distinguishable from the crown above it",
                "the crown reads as volume sitting above the band",
                "each material differs visibly WITHOUT the silhouette moving",
                "the front arch sits ON the head, with the head opening around "
                "the hair rather than a slab across the forehead",
                "no clipping into the face; no floating above the hair",
                "horizontal centring in all four directions",
                "the authored side view appears on the RIGHT, mirrored on the LEFT",
                "the back reads as a full disc and its button is legible at scale",
                f"HeadPosition Y={HEAD_Y} is inherited, not re-verified for this "
                "base -- the arch is a different height from beret_01/02",
                "the three source canvases were registered by top edge at row 3; "
                "if the back sits high or low relative to the front, that is the "
                "line to change (tools/ingest_beret_03.py, TOP)",
            ],
            "held_fixed": {"family": FAMILY, "shape_variant": SHAPE,
                           "quality_tier": TIER, "style": STYLE, "seed": SEED},
            "varied": "material x palette",
            "source_classification": "REFERENCE — drawn by the user and ingested; "
                                     "held with the rest of the beret family.",
            "base_provenance": base.provenance,
            "appearances": rows,
        }, fh, indent=2)
        fh.write("\n")

    print(f"pack  {os.path.relpath(PACK, ROOT)}")
    for r in rows:
        print(f"  {r['appearance']:34} {r['material']:9} {r['palette']}")
    print(f"\n{len(rows)} appearances, all bare geometry, HeadPosition Y={HEAD_Y}")


if __name__ == "__main__":
    main()
