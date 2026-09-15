"""Extract an AUTHORED material mask from a reference sheet, exactly as drawn.

Nothing is reinterpreted: the mask is the reference's own line cells, and this
reports their topology -- thickness, spacing, continuity, intersections -- so a
later application can be held to it. Lines are found as cells darker than both
flanks on one axis (tools/validate_material_mask.py), then checked 1px thick.

`--against <source-backed base>` answers one question: do those exact cells lie
on that shape? If not, the answer is "incompatible -- author a mask for this
shape", never a re-fitted pattern.

A mask taken from a REFERENCE-ONLY sheet is evidence, not library content; it is
written under experiments/, never under authored/.

    python3 tools/extract_material_mask.py
    python3 tools/extract_material_mask.py --reference PATH --treatment plaid --against beret_02
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from validate_material_mask import (REFERENCE, Sheet, extract_dark_lines, lstar,  # noqa: E402
                                    view_of, violations)
from v5 import source_backed as sbm  # noqa: E402
from v5.authored import ATLAS_ORDER  # noqa: E402
from v5.pngio import read_rgba_png  # noqa: E402


def _lin(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def topology(s: Sheet, cells: set, frame: int):
    """Thickness, runs, spacing, intersections and components of one view's mask."""
    y0 = frame * s.fh
    own = {(x, y - y0) for x, y in cells if y0 <= y < y0 + s.fh}
    rows, cols = {}, {}
    for x, y in own:
        rows.setdefault(y, []).append(x)
        cols.setdefault(x, []).append(y)

    def runs(d):
        out = {}
        for k, vs in d.items():
            vs, cur, rr = sorted(vs), [], []
            for v in vs:
                if cur and v != cur[-1] + 1:
                    rr.append(cur)
                    cur = []
                cur.append(v)
            rr.append(cur)
            out[k] = [len(r) for r in rr]
        return out

    hr, vr = runs(rows), runs(cols)
    h_lines = sorted(k for k, r in hr.items() if max(r) >= 3)
    v_lines = sorted(k for k, r in vr.items() if max(r) >= 3)
    cross = sum(1 for x, y in own
                if ((x - 1, y) in own or (x + 1, y) in own) and ((x, y - 1) in own or (x, y + 1) in own))
    seen, comps = set(), 0
    for c in own:
        if c in seen:
            continue
        comps += 1
        stack = [c]
        while stack:
            x, y = stack.pop()
            if (x, y) in seen or (x, y) not in own:
                continue
            seen.add((x, y))
            stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return {"cells": len(own), "h_lines_at_y": h_lines, "v_lines_at_x": v_lines,
            "h_spacing": [b - a for a, b in zip(h_lines, h_lines[1:])],
            "v_spacing": [b - a for a, b in zip(v_lines, v_lines[1:])],
            "row_runs": {str(k): v for k, v in sorted(hr.items())},
            "col_runs": {str(k): v for k, v in sorted(vr.items())},
            "intersections": cross, "components": comps}


def extract(path, treatment):
    s = Sheet(read_rgba_png(path))
    cells, pol, axis = extract_dark_lines(s)
    viol = violations(s, cells, pol, across_hint=axis)
    # value relationship actually drawn: line / mean of its two lighter flanks
    ratios = []
    for p in cells:
        flanks = [s.at(p, d) for d in (((-1, 0), (1, 0)) if "h" in axis[p] else ((0, -1), (0, 1)))]
        if all(flanks):
            ratios.append(_lin(s.px[p[1]][p[0]]) / (sum(_lin(s.px[q[1]][q[0]]) for q in flanks) / 2))
    ratios.sort()
    views = {v: sorted([x, y - i * s.fh] for x, y in cells if i * s.fh <= y < (i + 1) * s.fh)
             for i, v in enumerate(ATLAS_ORDER)}
    return s, {
        "treatment": treatment,
        "authored_for": "REFERENCE:" + os.path.relpath(path, ROOT),
        "factor": round(ratios[len(ratios) // 2], 3) if ratios else 1.0,
        "factor_range": [round(ratios[0], 3), round(ratios[-1], 3)] if ratios else None,
        "provenance": "extracted cell-for-cell from a REFERENCE-ONLY sheet; evidence, not library",
        "thickness_violations": [[k, list(p), view_of(s, p)] for k, p, _ in viol],
        "topology": {v: topology(s, cells, i) for i, v in enumerate(ATLAS_ORDER)},
        "views": views,
    }


def compatibility(mask, base: "sbm.SourceBackedBase"):
    """Per view: which exact mask cells fall off the base or onto its outline."""
    out = {}
    for v in ATLAS_ORDER:
        src_v = v if v in base.views else base.mirrored.get(v)
        cells = set(base.semantic.view(src_v)) if src_v else set()
        if v in base.mirrored:
            w = base.size[0]
            cells = {(w - 1 - x, y) for x, y in cells}
        want = {tuple(c) for c in mask["views"].get(v, [])}
        off = sorted(c for c in want if c not in cells)
        edge = sorted(c for c in want if c in cells and any(
            (c[0] + dx, c[1] + dy) not in cells for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))))
        out[v] = {"mask_cells": len(want), "off_silhouette": len(off), "on_outline": len(edge),
                  "fits_exactly": not off and not edge}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reference", default=REFERENCE)
    ap.add_argument("--treatment", default="plaid")
    ap.add_argument("--against", nargs="*", default=["beret_02", "beret_01"])
    ap.add_argument("--out", default=os.path.join(ROOT, "experiments", "material_masks"))
    args = ap.parse_args()
    s, mask = extract(args.reference, args.treatment)
    print(f"{args.reference}: {sum(len(c) for c in mask['views'].values())} cells, "
          f"factor {mask['factor']} (range {mask['factor_range']}), "
          f"thickness violations {len(mask['thickness_violations'])}")
    for v, t in mask["topology"].items():
        print(f"  {v:5} cells {t['cells']:3}  h-lines y{t['h_lines_at_y']} spacing {t['h_spacing']}  "
              f"v-lines x{t['v_lines_at_x']} spacing {t['v_spacing']}  crossings {t['intersections']}  "
              f"components {t['components']}")
    verdicts = {}
    for name in args.against:
        c = compatibility(mask, sbm.load_one(name))
        verdicts[name] = c
        ok = all(x["fits_exactly"] for x in c.values())
        print(f"  against {name}: {'COMPATIBLE' if ok else 'INCOMPATIBLE -- author a mask for this shape'}  "
              + "  ".join(f"{v}: {x['off_silhouette']} off, {x['on_outline']} on outline" for v, x in c.items()))
    mask["compatibility"] = verdicts
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, f"reference_hat_8_{args.treatment}.json")
    with open(path, "w") as fh:
        json.dump(mask, fh, indent=1)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
