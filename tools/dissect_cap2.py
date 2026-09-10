"""Controlled dissection of Cap 2, with a compatibility grammar.

Findings, from structural analysis rather than judgement:

  front_emblem     x8-11 y10, front only, a 4-cell bright bar on a flat field.
                   FAMILY-SPECIFIC: the author draws the SAME element at the
                   SAME cells on Cap 1, a different construction. Two
                   independent uses by the author is the positive evidence
                   that promotes it above base-specific.

  crown_highlight  x9-11 y6-7, front only. Enclosed, so separable in pixels --
                   but it is the specular highlight of THIS dome, and Cap 1's
                   crown is shaded entirely differently. Classified
                   BASE-SPECIFIC and deliberately LEFT EMBEDDED; extracting
                   lighting as a movable part would be forcing a split.

  everything else  crown, visor, adjuster gap, all side and back structure:
                   REFERENCE-ONLY. None of it is enclosed; every candidate
                   either touches transparency or borders two or more values,
                   so removing it would leave a hole with no authored filler.

Of 68 candidate regions across four directions, exactly 2 were enclosed and
exactly 1 is extracted. That ratio is the point: the source is mostly
inseparable, and saying so is the correct result.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5.source import dissect, roundtrip, semantic

OUT = "authored/source_bases/cap2"
SUBJECT = ("Cap 2", "More Accessories")

# The one component we extract, and the one we deliberately do not.
EXTRACT = {"front_emblem": {"direction": "Front", "bbox": (8, 11, 10, 10)}}
EMBED = {"crown_highlight": {"direction": "Front", "bbox": (9, 11, 6, 7),
                             "why": "specular highlight of this dome; Cap 1's "
                                    "crown is shaded differently, so it does "
                                    "not travel"}}


def main():
    cat = json.load(open("source_catalog/catalog.json"))
    app = next(a for a in cat["appearances"]
               if a["name"] == SUBJECT[0] and a["pack"].startswith(SUBJECT[1]))
    comps, _, vocab, diags, frames = dissect.find_components(app)

    chosen = None
    for d, blob, val, fill, frame, kind in comps:
        xs = [x for x, _ in blob]; ys = [y for _, y in blob]
        if (d, min(xs), max(xs), min(ys), max(ys)) == (
                "Front", *EXTRACT["front_emblem"]["bbox"]):
            chosen = (d, blob, fill, frame)
    if chosen is None:
        raise SystemExit("front_emblem not found; dissection changed")
    d, blob, fill, frame = chosen

    # the base with the emblem removed, filled with the single authored value
    # that already surrounds it -- so the hole is the author's own pixel
    fill_rgba = tuple(vocab[fill]) + (255,)
    base = {k: [list(r) for r in f] for k, f in frames.items()}
    emblem = {}
    for (x, y) in sorted(blob):
        emblem[(x, y)] = tuple(frame[y][x])
        base[d][y][x] = fill_rgba

    # MANDATORY: base + component must rebuild the source byte-for-byte
    rebuilt = {k: [list(r) for r in f] for k, f in base.items()}
    for (x, y), px in emblem.items():
        rebuilt[d][y][x] = px
    diff = 0
    for k, f in frames.items():
        for y in range(len(f)):
            for x in range(len(f[0])):
                if tuple(rebuilt[k][y][x]) != tuple(f[y][x]):
                    diff += 1

    os.makedirs(OUT, exist_ok=True)
    manifest = {
        "base": {"name": "cap2", "source": {
            "pack": app["pack"], "author": app["pack_author"],
            "asset": app["name"], "png": app["png_path"],
            "json": app["json_path"]},
            "family": "SOFT_CAP",
            "size": next(iter(app["analysis"]["boxes"].values()))[2:],
            "directions": sorted(frames),
            "vocabulary": [list(c) for c in vocab],
            "roles": semantic.roles_for(vocab),
            "tone": semantic.tone_profile(vocab),
            "wear_properties": roundtrip.source_blocks(app),
        },
        "components": {
            "front_emblem": {
                "classification": dissect.FAMILY_SPECIFIC,
                "kind": "surface motif",
                "zone": "visor_face",
                "directions": ["Front"],
                "cells": {f"{x},{y}": list(v) for (x, y), v in emblem.items()},
                "fill_value": list(fill_rgba),
                "evidence": ("the same element at the same cells (x8-11, y10) "
                             "on Cap 1, a different construction by the same "
                             "author"),
            }
        },
        "embedded": EMBED,
        "not_separable": {
            "count": sum(1 for x in diags if not x["enclosed"]),
            "classification": dissect.REFERENCE_ONLY,
            "why": ("not enclosed: each candidate touches transparency or "
                    "borders two or more authored values, so no single "
                    "authored fill exists"),
        },
        "reconstruction": {"differing_pixels": diff, "exact": diff == 0},
    }
    json.dump(manifest, open(f"{OUT}/manifest.json", "w"), indent=1)
    print(f"base cap2 + 1 component; reconstruction diff = {diff} px "
          f"({'EXACT' if diff == 0 else 'FAILED'})")
    print(f"  extracted : front_emblem ({len(emblem)} cells) "
          f"{dissect.FAMILY_SPECIFIC}")
    print(f"  embedded  : crown_highlight  {dissect.BASE_SPECIFIC}")
    print(f"  rejected  : {manifest['not_separable']['count']} regions "
          f"{dissect.REFERENCE_ONLY}")
    print(f"wrote {OUT}/manifest.json")


if __name__ == "__main__":
    main()
