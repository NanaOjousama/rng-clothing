"""Validation batch for the `cute_beret` style profile.

The success test is a side-by-side one: does a generated batch read as the same
collection as the user's reference sheet, rather than merely as more berets? So
this rolls the profile the way the generator actually would -- weighted, not a
hand-picked matrix -- and prints what each roll used, so the variation can be
checked against the four axes it is supposed to come from.

    python3 tools/build_cute_beret_batch.py [n]
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import authored
from v5.pngio import blank_image, blit, write_rgba_png

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "test-packs", "fashionsense", "RNG-Beret-Cute-M3")
FAMILY, PROFILE = "beret", "cute_beret"
HEAD_Y = -2


def sheet_of(g):
    img = blank_image(20, 80)
    for i, v in enumerate(authored.ATLAS_ORDER):
        blit(img, g.directions[v], 0, i * 20)
    return img


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    lib = authored.load()
    tiers = lib.tier_order()
    # Rebuild the Hats tree from scratch: a shorter run after a longer one used
    # to leave the extra appearances behind, and Fashion Sense would happily load
    # a pack half of whose contents were from a batch that no longer exists.
    import shutil
    shutil.rmtree(os.path.join(PACK, "Hats"), ignore_errors=True)
    os.makedirs(os.path.join(PACK, "Hats"), exist_ok=True)
    with open(os.path.join(PACK, "manifest.json"), "w") as fh:
        json.dump({"Name": "RNG Beret Cute M3", "Author": "RNG Clothing Experiment",
                   "Version": "1.0.0",
                   "Description": "Milestone 3: the cute_beret style profile, "
                                  "rolled the way the generator would.",
                   "UniqueID": "RNGClothing.FashionSense.BeretCuteM3",
                   "UpdateKeys": [],
                   "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                                      "MinimumVersion": "7.5.0"}}, fh, indent=2)
        fh.write("\n")

    rows, renders, drops = [], {}, []
    for i in range(n):
        tier = tiers[i % len(tiers)] if i < len(tiers) else \
            authored.StreamBank(1000 + i)("tier").weighted(
                # The reference sheet is mostly decorated, so the validation
                # batch leans the same way; the ladder itself is unchanged.
                {"Common": 2, "Uncommon": 3, "Rare": 3, "RarePlus": 3})
        g = authored.compose(1000 + i, family=FAMILY, profile=PROFILE,
                             quality_tier=tier, lib=lib)
        app = f"Cute{i:02d}"
        d = os.path.join(PACK, "Hats", app)
        os.makedirs(d, exist_ok=True)
        sh = sheet_of(g)
        write_rgba_png(os.path.join(d, "hat.png"), sh)

        def block(y):
            return {"DisableGrayscale": True, "HideHair": False,
                    "HatSize": {"Width": 20, "Length": 20},
                    "StartingPosition": {"X": 0, "Y": y},
                    "HeadPosition": {"X": 0, "Y": HEAD_Y}}
        with open(os.path.join(d, "hat.json"), "w") as fh:
            json.dump({"Name": f"Cute Beret {i:02d}",
                       "Tags": ["RNG Clothing", "Cute Beret M3", g.shape_variant,
                                g.treatment, g.quality_tier, g.palette.id],
                       "FrontHat": block(0), "RightHat": block(20),
                       "LeftHat": block(40), "BackHat": block(60)}, fh, indent=2)
            fh.write("\n")

        key = tuple(tuple(tuple(p) for p in r) for r in sh)
        sig = (g.shape_variant, g.treatment, g.palette.id,
               tuple(sorted(x.name for x in g.decals)))
        renders.setdefault(key, []).append((app, sig))
        drops += [list(x) for x in g.dropped]
        rows.append({"appearance": app, "shape_variant": g.shape_variant,
                     "treatment": g.treatment, "palette": g.palette.id,
                     "quality_tier": g.quality_tier,
                     "decals": [x.name for x in g.decals],
                     "classes": sorted({x.motif_class for x in g.decals}),
                     "dropped": [list(x) for x in g.dropped]})

    dupes = {v[0][0]: [a for a, _ in v[1:]] for v in renders.values()
             if len({s for _, s in v}) > 1}
    ax = {k: Counter(r[k] for r in rows)
          for k in ("shape_variant", "treatment", "palette", "quality_tier")}
    combos = len({(r["shape_variant"], r["treatment"], r["palette"],
                   tuple(r["decals"])) for r in rows})
    stats = {"batch_size": len(rows), "profile": PROFILE,
             "reference": lib.profile(FAMILY, PROFILE)["reference"],
             "placement_drops": len(drops), "drop_detail": drops,
             "identical_renders_that_should_differ": dupes,
             "distinct_combinations": combos,
             "axis_spread": {k: dict(v) for k, v in ax.items()},
             "decals_used": dict(Counter(x for r in rows for x in r["decals"]).most_common()),
             "appearances": rows}
    with open(os.path.join(PACK, "TRACEABILITY.json"), "w") as fh:
        json.dump(stats, fh, indent=2)
        fh.write("\n")

    print(f"{len(rows)} rolls   drops {len(drops)}   "
          f"unexpected identical {len(dupes)}   distinct combos {combos}/{len(rows)}")
    print()
    print(f"{'':6} {'shape':9} {'material':9} {'tier':9} {'palette':22} decoration")
    for r in rows:
        print(f"{r['appearance']:6} {r['shape_variant']:9} {r['treatment']:9} "
              f"{r['quality_tier']:9} {r['palette']:22} "
              f"{'+'.join(r['decals']) or '—'}")
    print()
    for k, v in ax.items():
        print(f"  {k:14} {dict(v)}")


if __name__ == "__main__":
    main()
