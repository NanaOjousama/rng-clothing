"""Milestone 2 batch: Shape x Palette x Decoration x Quality Tier.

A deterministic matrix, so the four axes can be read against each other rather
than sampled. Every (shape, palette) pair is run through all four tiers with the
style pinned, which is what makes "does quality actually increase richness?" a
question with an answer per row rather than an average over noise.

    python3 tools/build_beret_batch.py
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
PACK = os.path.join(ROOT, "test-packs", "fashionsense", "RNG-Beret-Batch-M2")

FAMILY = "beret"
SHAPES = ["beret_01", "beret_02"]
# Four palettes covering all four materials across two style stories, so the
# batch exercises the parts of the decal pool that only one story can reach.
PALETTES = [("FIELD_CANVAS_MOSS", "cottagecore"),
            ("AUTUMN_OCHRE_PLUM", "cottagecore"),
            ("FORMAL_PEARL_MIDNIGHT", "formal"),
            ("LUXURY_JADE_BRONZE", "formal"),
            # A smart story as well: it is the only one that reaches the button
            # class, and so the only one where beret_02's nub-only restriction
            # shows up as a difference in the output rather than as a rule.
            ("EVERYDAY_STONE_BLUE", "smart"),
            ("SAILOR_COBALT_CREAM", "smart")]
SEED = 8
HEAD_Y = -2


def sheet_of(g):
    img = blank_image(20, 80)
    for i, view in enumerate(authored.ATLAS_ORDER):
        blit(img, g.directions[view], 0, i * 20)
    return img


def hat_json(name, g):
    def block(y):
        return {"DisableGrayscale": True, "HideHair": False,
                "HatSize": {"Width": 20, "Length": 20},
                "StartingPosition": {"X": 0, "Y": y},
                "HeadPosition": {"X": 0, "Y": HEAD_Y}}
    return {"Name": name,
            "Tags": ["RNG Clothing", "Beret Batch M2", FAMILY, g.shape_variant,
                     g.quality_tier, g.material, g.palette.id, g.style,
                     "REFERENCE-ONLY source"],
            "FrontHat": block(0), "RightHat": block(20),
            "LeftHat": block(40), "BackHat": block(60)}


def main():
    lib = authored.load()
    os.makedirs(os.path.join(PACK, "Hats"), exist_ok=True)
    with open(os.path.join(PACK, "manifest.json"), "w") as fh:
        json.dump({"Name": "RNG Beret Batch M2", "Author": "RNG Clothing Experiment",
                   "Version": "1.0.0",
                   "Description": "Milestone 2: two beret shapes x four palettes x "
                                  "four quality tiers, to show the axes are independent.",
                   "UniqueID": "RNGClothing.FashionSense.BeretBatchM2",
                   "UpdateKeys": [],
                   "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                                      "MinimumVersion": "7.5.0"}}, fh, indent=2)
        fh.write("\n")

    rows, drops, renders = [], [], {}
    for shape in SHAPES:
        for pid, story in PALETTES:
            for tier in lib.tier_order():
                g = authored.build_tier(FAMILY, shape, pid, tier, SEED, lib, style=story)
                app = f"{shape.replace('_', '')}{pid.split('_')[0].title()}{tier}"
                d = os.path.join(PACK, "Hats", app)
                os.makedirs(d, exist_ok=True)
                sheet = sheet_of(g)
                write_rgba_png(os.path.join(d, "hat.png"), sheet)
                with open(os.path.join(d, "hat.json"), "w") as fh:
                    json.dump(hat_json(f"{shape} {tier} {pid}", g), fh, indent=2)
                    fh.write("\n")
                cells = sum(max(len(x.view_cells(v)) for v in x.views) for x in g.decals)
                key = tuple(tuple(tuple(px) for px in row) for row in sheet)
                # Two appearances built from the same shape, palette and decal
                # set SHOULD render identically -- Common and a plain Uncommon
                # are the same hat, and that is the design, not a collision. The
                # defect is identical pixels from different inputs.
                renders.setdefault(key, []).append(
                    (app, (shape, pid, tuple(sorted(x.name for x in g.decals)))))
                rows.append({"appearance": app, "shape_variant": shape,
                             "palette": pid, "style": story, "quality_tier": tier,
                             "material": g.material,
                             "decals": [x.name for x in g.decals],
                             "classes": sorted({x.motif_class for x in g.decals}),
                             "decor_cells": cells,
                             "budget": lib.tier(tier)["max_decor_cells"],
                             "dropped": [list(x) for x in g.dropped]})
                drops += [list(x) for x in g.dropped]

    # Where a tier has no legal piece of a kind at all, its floor cannot be met
    # and richness can dip. That is a library gap, not a logic fault, so name it
    # precisely instead of averaging it away.
    coverage, gaps = {}, []
    for shape in SHAPES:
        base = next(b for b in lib.family_bases(FAMILY) if b.shape_variant == shape)
        for pid, story in PALETTES:
            for tier in lib.tier_order():
                pools = lib.family(FAMILY)["pools"]
                got = {"attachment": [], "surface": []}
                for d in lib.decals:
                    if d.slot != base.slot or d.pending or story not in d.style:
                        continue
                    if not d.fits_base(base):
                        continue
                    allowed = pools["attachment" if d.kind == "attachment"
                                    else "surface_motif"].get(tier, [])
                    if d.motif_class not in allowed:
                        continue
                    if authored.can_place(base, d):
                        got[d.kind].append(d.name)
                key = f"{shape}|{story}|{tier}"
                coverage[key] = {k: sorted(v) for k, v in got.items()}
                need = lib.tier(tier).get("min_decor_pieces", 0)
                if need < 2:
                    continue
                legal = [d for d in lib.decals
                         if d.name in got["attachment"] + got["surface"]]
                regions = {authored.region_of(d) for d in legal}
                caps = (lib.tier(tier)["max_attachments"]
                        + lib.tier(tier)["max_motifs"])
                # Regions are exclusive on purpose -- two motifs in one region
                # read as speckle -- so the reachable maximum is bounded by the
                # number of DISTINCT regions available, not by the piece count.
                reachable = min(caps, len(regions))
                if reachable >= need:
                    continue
                if not got["surface"]:
                    why, missing = ("no piece of an allowed class fits this shape "
                                    "in this style"), "surface_motif"
                else:
                    why, missing = (f"every legal piece sits in the same region "
                                    f"{sorted(regions)}, and regions are "
                                    f"exclusive"), "a second region"
                gaps.append({"where": key, "missing": missing,
                             "reachable_pieces": reachable, "floor": need,
                             "legal": sorted(got["attachment"] + got["surface"]),
                             "classes_allowed": {
                                 "surface": pools["surface_motif"][tier],
                                 "attachment": pools["attachment"][tier]},
                             "why": why})
    # One gap can show up under several stories; fold them together so the
    # report says "beret_02 has no premium surface motif at all" rather than
    # naming whichever story happened to sort first.
    folded = {}
    for g in gaps:
        shape, story, tier = g["where"].split("|")
        k = (shape, tier, g["missing"])
        rec = folded.setdefault(k, {**g, "shape": shape, "tier": tier,
                                    "stories": []})
        rec["stories"].append(story)
        rec.pop("where", None)
    uniq = [dict(v, stories=sorted(set(v["stories"]))) for v in folded.values()]

    dupes = {v[0][0]: [a for a, _ in v[1:]]
             for v in renders.values()
             if len({inputs for _, inputs in v}) > 1}
    expected_same = sum(1 for v in renders.values()
                        if len(v) > 1 and len({i for _, i in v}) == 1)
    monotonic = {}
    for shape in SHAPES:
        for pid, _ in PALETTES:
            sel = [r for r in rows
                   if r["shape_variant"] == shape and r["palette"] == pid]
            # Richness is PIECES, not cells. A 6-cell flower is not a poorer
            # decoration than a 7-cell leaf sprig; cells are the budget guard.
            pieces = [len(r["decals"]) for r in sel]
            monotonic[f"{shape}|{pid}"] = {
                "pieces": pieces, "cells": [r["decor_cells"] for r in sel],
                "non_decreasing": all(a <= b for a, b in zip(pieces, pieces[1:]))}

    stats = {
        "batch_size": len(rows),
        "axes": {"shape": SHAPES, "palette": [p for p, _ in PALETTES],
                 "quality_tier": lib.tier_order()},
        "placement_drops": len(drops),
        "drop_detail": drops,
        "identical_renders_that_should_differ": dupes,
        "identical_renders_expected": expected_same,
        "pool_coverage": coverage,
        "pool_gaps": uniq,
        "tier_monotonicity": monotonic,
        "decals_used": dict(Counter(n for r in rows for n in r["decals"]).most_common()),
        "cells_by_tier": {t: sorted({r["decor_cells"] for r in rows
                                     if r["quality_tier"] == t})
                          for t in lib.tier_order()},
        "decals_by_shape": {s: dict(Counter(n for r in rows
                                            if r["shape_variant"] == s
                                            for n in r["decals"]).most_common())
                            for s in SHAPES},
        "appearances": rows,
    }
    with open(os.path.join(PACK, "TRACEABILITY.json"), "w") as fh:
        json.dump(stats, fh, indent=2)
        fh.write("\n")

    print(f"pack {os.path.relpath(PACK, ROOT)}   {len(rows)} appearances "
          f"({len(SHAPES)} shapes x {len(PALETTES)} palettes x {len(lib.tier_order())} tiers)")
    print(f"placement drops: {len(drops)}   "
          f"unexpected identical renders: {len(dupes)}   "
          f"(expected identical, same inputs: {expected_same})")
    print()
    hdr = f"{'shape':10} {'palette':22} {'tier':10} {'cells':>5}  decals"
    print(hdr); print("-" * 92)
    for r in rows:
        print(f"{r['shape_variant']:10} {r['palette']:22} {r['quality_tier']:10} "
              f"{r['decor_cells']:5}  {'+'.join(r['decals']) or '—'}")
    print()
    for k, v in monotonic.items():
        flag = "" if v["non_decreasing"] else "   NOT MONOTONIC"
        print(f"  {k:34} pieces {v['pieces']}  cells {v['cells']}{flag}")
    print()
    if uniq:
        print("pool gaps (a tier whose floor cannot be met for lack of a legal piece):")
        for g in uniq:
            print(f"  {g['shape']}/{g['tier']}: floor {g['floor']}, reachable "
                  f"{g['reachable_pieces']} in {len(g['stories'])} of "
                  f"{len({s2 for _, s2 in PALETTES})} stories "
                  f"({', '.join(g['stories'])})")
            print(f"     missing {g['missing']} -- {g['why']}")
            print(f"     allowed classes {g['classes_allowed']['surface']}")
        print()
    print("decals by shape:")
    for s, c in stats["decals_by_shape"].items():
        print(f"  {s}: {c}")


if __name__ == "__main__":
    main()
