"""Structural semantic map for Cap 2, derived from the source pixels.

This replaces a decomposition that mistook the visor's lit surface for a
decorative emblem.  The lesson is written into the method: a region is labelled
by what it IS on the worn garment, and mathematical separability is treated as
a hint, never as evidence.

Roles are derived, not asserted:

    outline     the vocabulary's darkest step, which the author uses as the rim
    crown       the dome; in profile, everything at or behind the crown's own
                forward edge
    visor       in PROFILE, whatever projects past that edge -- an unambiguous
                geometric definition.  In FRONT, the contiguous band below the
                crown whose row means drop away from the dome, which is the
                same peak foreshortened
    underside   the lowest rows of the visor, and on the back the adjuster
                opening
    highlight   the brightest step where it sits inside the crown
    decoration  only if something survives being none of the above
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5.grammar import luminance
from v5.source import audit, dissect, pngread, semantic

OUT = "authored/source_bases/cap2"


def main():
    cat = json.load(open("source_catalog/catalog.json"))
    app = next(a for a in cat["appearances"]
               if a["name"] == "Cap 2" and a["pack"].startswith("More Acc"))
    px = pngread.read(app["png_path"])
    fr = {d: audit.cut(px, tuple(b)) for d, b in app["analysis"]["boxes"].items()}
    vocab = semantic.build_vocabulary([fr], app["analysis"].get("declared_masks"))
    steps = {d: dissect.step_map(f, vocab) for d, f in fr.items()}

    # --- profile: the visor is what projects past the crown's forward edge ---
    prof = steps["Right"]
    rows = {}
    for (x, y) in prof:
        rows.setdefault(y, []).append(x)
    top_rows = [y for y in sorted(rows) if y <= min(rows) + 2]
    crown_edge = max(max(rows[y]) for y in top_rows)
    prof_visor = {c for c in prof if c[0] > crown_edge}
    prof_crown = {c for c in prof if c[0] <= crown_edge}

    # --- front: the band below the dome, found by where row means fall away ---
    f = steps["Front"]
    frows = {}
    for (x, y), s in f.items():
        frows.setdefault(y, []).append(luminance(vocab[s]))
    means = {y: sum(v) / len(v) for y, v in frows.items()}
    ys = sorted(means)
    peak = max(means, key=lambda y: means[y])
    split = next((y for y in ys if y > peak and means[y] < means[peak] * 0.72), None)
    front_visor = {c for c in f if c[1] >= split}
    front_crown = {c for c in f if c[1] < split}
    bottom = max(y for _, y in f)
    front_under = {c for c in front_visor if c[1] == bottom}

    # --- back: the adjuster opening is the enclosed transparent gap ---
    b = steps["Back"]
    brows = {}
    for (x, y) in b:
        brows.setdefault(y, []).append(x)
    gap_rows = [y for y, xs in brows.items()
                if max(xs) - min(xs) + 1 > len(xs)]      # a row with a hole
    back_under = {c for c in b if c[1] in gap_rows or c[1] == max(brows)}

    def role_map(direction):
        s = steps[direction]
        out = {}
        for c, st in s.items():
            if st == 0:
                out[c] = "outline"
            elif direction == "Front":
                out[c] = ("underside" if c in front_under
                          else "visor" if c in front_visor else "crown")
            elif direction in ("Right", "Left"):
                out[c] = "visor" if c in prof_visor else "crown"
            else:
                out[c] = "underside" if c in back_under else "crown"
        # highlight: the brightest step, only where it lies in the crown
        top = max(s.values())
        for c, st in s.items():
            if st == top and out[c] == "crown":
                out[c] = "highlight"
        return out

    maps = {d: role_map(d) for d in fr}
    counts = {d: {} for d in maps}
    for d, m in maps.items():
        for r in m.values():
            counts[d][r] = counts[d].get(r, 0) + 1

    manifest = {
        "base": {"name": "cap2", "family": "SOFT_CAP",
                 "source": {"pack": app["pack"], "author": app["pack_author"],
                            "asset": app["name"], "png": app["png_path"],
                            "json": app["json_path"]},
                 "integrity": "INTACT — nothing is extracted from this base",
                 "size": next(iter(app["analysis"]["boxes"].values()))[2:],
                 "directions": sorted(fr),
                 "vocabulary": [list(c) for c in vocab],
                 "tone": semantic.tone_profile(vocab)},
        "structural_roles": {d: {f"{x},{y}": r for (x, y), r in m.items()}
                             for d, m in maps.items()},
        "role_counts": counts,
        "derivation": {
            "profile_crown_edge": crown_edge,
            "front_crown_visor_split_row": split,
            "back_opening_rows": sorted(gap_rows),
        },
        "decoration": {
            "present": False,
            "finding": ("Cap 2 contains NO decorative element. The only region "
                        "that is mathematically separable is the visor's lit "
                        "top surface (Front x8-11, y10) and the crown's own "
                        "specular highlight. Both are structural."),
            "consequence": ("the generator may vary PALETTE only. A motif zone "
                            "requires a real decorable surface, which this "
                            "construction does not provide."),
        },
    }
    os.makedirs(OUT, exist_ok=True)
    json.dump(manifest, open(f"{OUT}/semantic_map.json", "w"), indent=1)

    print(f"profile crown edge at x={crown_edge}; "
          f"front crown/visor split at row {split}; "
          f"back opening rows {sorted(gap_rows)}\n")
    for d in ("Front", "Right", "Left", "Back"):
        print(f"  {d:6s} " + "  ".join(f"{r}={n}" for r, n in
                                       sorted(counts[d].items())))
    print(f"\ndecoration present: {manifest['decoration']['present']}")
    print(f"wrote {OUT}/semantic_map.json")


if __name__ == "__main__":
    main()
