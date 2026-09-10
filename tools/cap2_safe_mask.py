"""CAP2_FRONT_MOTIF_SAFE_MASK — per-pixel legality for front-crown marks.

A rectangle is too permissive. The crown is a dome: its top corners are
silhouette, so a 4x3 box centred on the crown necessarily includes cells that
make the outer shape read. Overwriting those makes a mark look like it changed
the hat, which is exactly what the worn sheet showed.

So legality is per pixel. A cell is SAFE only if it is:

    drawn, and semantically crown or highlight
    not an outline cell
    not on the rim under EIGHT-connectivity -- four-connectivity is too weak,
      because a cell touching transparency only diagonally still reads as part
      of the outer edge at gameplay scale
    not orthogonally adjacent to the visor, so the crown/visor seam survives

The rectangle survives only as a coarse bounding box. The mask is authoritative.
"""
from __future__ import annotations

import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v5.source import audit, pngread

BASE = "authored/source_bases/cap2"
N8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def build():
    sm = json.load(open(f"{BASE}/semantic_map.json"))
    roles = {tuple(int(v) for v in k.split(",")): r
             for k, r in sm["structural_roles"]["Front"].items()}
    cat = json.load(open("source_catalog/catalog.json"))
    app = next(a for a in cat["appearances"]
               if a["name"] == "Cap 2" and a["pack"].startswith("More Acc"))
    f = audit.cut(pngread.read(app["png_path"]), (0, 0, 20, 20))
    drawn = {(x, y) for y in range(20) for x in range(20) if f[y][x][3]}
    visor = {c for c, r in roles.items() if r in ("visor", "underside")}
    outline = {c for c, r in roles.items() if r == "outline"}
    crown = {c for c, r in roles.items() if r in ("crown", "highlight")}
    rim = {c for c in drawn
           if any((c[0] + dx, c[1] + dy) not in drawn for dx, dy in N8)}
    seam = {c for c in drawn
            if any((c[0] + dx, c[1] + dy) in visor for dx, dy in N4)}
    safe = crown - outline - rim - seam
    return safe, {"drawn": len(drawn), "crown": len(crown),
                  "outline": len(outline), "rim_8conn": len(rim),
                  "visor_adjacent": len(seam), "safe": len(safe)}


def legal(cells, safe):
    bad = [c for c in cells if c not in safe]
    return (not bad), bad


def main():
    safe, stats = build()
    rows = {}
    for (x, y) in sorted(safe, key=lambda c: (c[1], c[0])):
        rows.setdefault(y, []).append(x)
    doc = {
        "id": "CAP2_FRONT_MOTIF_SAFE_MASK",
        "authoritative": True,
        "provenance": "generator-authored constraint over the intact source base",
        "derivation": {
            "included": "cells whose semantic role is crown or highlight",
            "excluded": [
                "transparent / background",
                "outline cells (vocabulary step 0)",
                "rim cells under 8-connectivity — a cell touching transparency "
                "even diagonally still reads as the outer edge",
                "cells orthogonally adjacent to the visor, preserving the seam",
            ],
            "counts": stats,
        },
        "safe_cells_by_row": {str(k): v for k, v in sorted(rows.items())},
        "safe_cells": [list(c) for c in sorted(safe, key=lambda c: (c[1], c[0]))],
        "coarse_bounding_box": {"x0": min(x for x, _ in safe),
                                "x1": max(x for x, _ in safe),
                                "y0": min(y for _, y in safe),
                                "y1": max(y for _, y in safe),
                                "note": "informational only; the cell list decides"},
        "rule": "a motif pixel is legal ONLY if that exact cell is in safe_cells",
    }
    json.dump(doc, open(f"{BASE}/motif_safe_mask.json", "w"), indent=1)
    print(f"SAFE MASK: {stats['safe']} cells of {stats['crown']} crown cells")
    for k, v in sorted(rows.items()):
        print(f"   row {k}: {v}")
    print(f"wrote {BASE}/motif_safe_mask.json")


if __name__ == "__main__":
    main()
