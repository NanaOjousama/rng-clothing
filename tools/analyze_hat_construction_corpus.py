"""Construction analysis over BOTH hat corpora: vanilla and the mod-author sheet.

Reads 20x20 four-direction frames, measures the geometry the generator already
speaks (crown/brim split, overhang, symmetry) AND the interior rendering that
`hat_templates` needs to author (planes, band, highlight, contact, outline),
then clusters the result into structural families.

Run:  python3 tools/analyze_hat_construction_corpus.py
"""
from __future__ import annotations

import colorsys
import json
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5.grammar import (HAT_ENVELOPE, HEAD_BOX, brim_line, crown_metrics,
                        enclosed_holes, luminance, mirror_symmetry,
                        occupied_bbox, outline_delta, overhang, row_widths)
from v5.pngio import read_rgba_png

VANILLA = ("/run/media/deck/USD00/steamapps/common/Stardew Valley/"
           "Content (unpacked)/Characters/Farmer/hats.png")
MOD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "female.png")
DIRS = ("front", "right", "left", "back")


def frames(path):
    """[{direction: {cell: rgba}}] for every 20x20x4 block in a sheet."""
    im = read_rgba_png(path)
    w, h = len(im[0]), len(im)
    out, idx = [], 0
    while True:
        x0, y0 = (idx * 20) % w, (idx * 20 // w) * 80
        if y0 + 80 > h:
            break
        blk = {}
        for di, d in enumerate(DIRS):
            blk[d] = {(x, y): tuple(im[y0 + di * 20 + y][x0 + x])
                      for y in range(20) for x in range(20)
                      if im[y0 + di * 20 + y][x0 + x][3] > 0}
        if len(blk["front"]) >= 12:
            out.append(blk)
        idx += 1
    return out


def hsv(c):
    return colorsys.rgb_to_hsv(c[0] / 255, c[1] / 255, c[2] / 255)


def body_hue(px):
    from collections import Counter
    for col, _ in Counter(px.values()).most_common():
        h, s, _ = hsv(col)
        if s > 0.12:
            return h
    return None


def hue_gap(a, b):
    d = abs(a - b)
    return min(d, 1 - d) * 360


def bands(px, cells, crown_rows):
    """Rows inside the crown whose colour differs from the crown body.

    A band in this corpus is a HORIZONTAL run that covers most of its row and
    reads differently from the rows above it — by hue, or by value, or by both.
    Returns (row, coverage, hue_gap, value_delta) for each.
    """
    from collections import Counter
    rows = {}
    for (x, y), c in px.items():
        rows.setdefault(y, []).append(c)
    body = Counter(px.values()).most_common(1)[0][0]
    bh = body_hue(px)
    out = []
    for y in sorted(crown_rows):
        row = rows.get(y, [])
        if len(row) < 3:
            continue
        col, n = Counter(row).most_common(1)[0]
        if col == body or n / len(row) < 0.6:
            continue
        h, s, _ = hsv(col)
        gap = hue_gap(h, bh) if (bh is not None and s > 0.12) else 0.0
        dv = luminance(col) - luminance(body)
        if gap > 25 or abs(dv) > 25:
            out.append({"row": y, "coverage": round(n / len(row), 2),
                        "hue_gap": round(gap), "value_delta": round(dv)})
    return out


def measure(blk) -> dict:
    px = blk["front"]
    cells = set(px)
    L = {c: luminance(px[c]) for c in cells}
    x0, x1, y0, y1 = occupied_bbox(cells)
    cm = crown_metrics(cells)
    bl = cm["brim_line"]
    widths = row_widths(cells)
    crown_rows = [y for y in sorted(widths) if y < bl]
    peak = max(L.values())
    hi = [c for c, v in L.items() if v >= peak - 12]
    body = st.median(list(L.values()))
    rows_lum = {}
    for (x, y), v in L.items():
        rows_lum.setdefault(y, []).append(v)

    # protrusions: cells outside the widest contiguous run of their row
    splits = 0
    for y, xs in ((y, sorted(x for (x, yy) in cells if yy == y)) for y in widths):
        runs, run = [], [xs[0]]
        for a, b in zip(xs, xs[1:]):
            if b == a + 1:
                run.append(b)
            else:
                runs.append(run)
                run = [b]
        runs.append(run)
        if len(runs) > 1:
            splits += 1

    bnd = bands(px, cells, crown_rows)
    side = set(blk["right"])
    back = set(blk["back"])
    return {
        "cells": len(cells),
        "bbox_w": x1 - x0 + 1, "bbox_h": y1 - y0 + 1,
        "top": y0, "bottom": y1,
        "brim_line": bl,
        "brim_ratio": round(cm["brim_ratio"], 2),
        "crown_h": cm["crown_height"], "crown_w": cm["crown_width"],
        "overhang": max(overhang(cells, HEAD_BOX)),
        "symmetry": round(mirror_symmetry(cells, HAT_ENVELOPE), 2),
        "holes": len(enclosed_holes(cells, HAT_ENVELOPE)),
        "split_rows": splits,
        "colors": len(set(px.values())),
        "span": round(peak - min(L.values())),
        "darkest": round(min(L.values())),
        "highlight_share": round(100 * len(hi) / len(cells), 1),
        "highlight_depth": round((st.mean([y for _, y in hi]) - y0) / max(1, y1 - y0), 2),
        "highlight_x": round((st.mean([x for x, _ in hi]) - x0) / max(1, x1 - x0), 2),
        "outline": round(outline_delta(px), 1),
        "contact": round(st.mean(rows_lum[y1 - 1]) - body) if (y1 - 1) in rows_lum else None,
        "bands": bnd,
        "band_row_from_brim": (bl - bnd[0]["row"]) if bnd else None,
        "side_cells": len(side), "back_cells": len(back),
        "side_vs_front": round(len(side) / max(1, len(cells)), 2),
        "back_vs_front": round(len(back) / max(1, len(cells)), 2),
    }


def family(m) -> str:
    """Structural family, from geometry alone.

    Ordered so the rarer, load-bearing structures claim their members first:
    a hat with a detached mass is an EARED hat whatever its brim does, and a
    very tall crown is a TALL_CROWN whether or not it also has a wide brim.
    """
    if m["holes"] > 0 or m["split_rows"] >= 4:
        return "EARED_OR_SPLIT"
    if m["crown_h"] >= 8:
        return "TALL_CROWN"
    if m["brim_ratio"] > 1.15:
        if m["bbox_w"] >= 16 or m["overhang"] >= 3:
            return "WIDE_BRIM"
        return "BRIMMED_FELT"
    if m["crown_h"] <= 4:
        return "SOFT_CAP"
    return "CLOSE_FIT"


def summarize(name, ms, keys):
    print(f"\n=== {name}  n={len(ms)}")
    for k in keys:
        vals = sorted(m[k] for m in ms if m.get(k) is not None)
        if not vals:
            continue
        print(f"  {k:18s} p10 {vals[int(.1*(len(vals)-1))]:7.1f}  median "
              f"{st.median(vals):7.1f}  p90 {vals[int(.9*(len(vals)-1))]:7.1f}")


KEYS = ["cells", "bbox_w", "bbox_h", "top", "brim_line", "brim_ratio", "crown_h",
        "crown_w", "overhang", "symmetry", "split_rows", "colors", "span",
        "darkest", "highlight_share", "highlight_depth", "outline", "contact",
        "side_vs_front", "back_vs_front"]

if __name__ == "__main__":
    out = {}
    for label, path in (("vanilla", VANILLA), ("mod", MOD)):
        if not os.path.exists(path):
            print(f"skip {label}: {path} not found")
            continue
        ms = [measure(b) for b in frames(path)]
        for m in ms:
            m["family"] = family(m)
        out[label] = ms
        summarize(label, ms, KEYS)
        fams = {}
        for m in ms:
            fams.setdefault(m["family"], []).append(m)
        print(f"  families: " + ", ".join(f"{k} {len(v)}" for k, v in sorted(fams.items())))
        withband = [m for m in ms if m["bands"]]
        print(f"  hats with a band: {len(withband)}/{len(ms)}")
        if withband:
            print(f"    rows above the brim line: "
                  f"{sorted(m['band_row_from_brim'] for m in withband)[:20]}")
            print(f"    median hue gap {st.median([m['bands'][0]['hue_gap'] for m in withband]):.0f}deg,"
                  f" median value delta {st.median([m['bands'][0]['value_delta'] for m in withband]):.0f}")
    # --- per-family interior tables: what a template for each would author ---
    fam_keys = ["cells", "crown_h", "crown_w", "brim_ratio", "bbox_w", "top",
                "colors", "span", "darkest", "highlight_share", "highlight_depth",
                "highlight_x", "outline", "contact", "split_rows",
                "side_vs_front", "back_vs_front"]
    allms = [(lab, m) for lab, ms in out.items() for m in ms]
    fams = {}
    for lab, m in allms:
        fams.setdefault(m["family"], []).append((lab, m))
    print("\n\n########## PER-FAMILY INTERIOR (both corpora) ##########")
    for fam, entries in sorted(fams.items(), key=lambda kv: -len(kv[1])):
        v = sum(1 for lab, _ in entries if lab == "vanilla")
        print(f"\n--- {fam}  n={len(entries)}  (vanilla {v}, mod {len(entries)-v})")
        for k in fam_keys:
            vals = sorted(m[k] for _, m in entries if m.get(k) is not None)
            if not vals:
                continue
            print(f"    {k:16s} p25 {vals[len(vals)//4]:7.2f}  median "
                  f"{st.median(vals):7.2f}  p75 {vals[3*len(vals)//4]:7.2f}")
        wb = [m for _, m in entries if m["bands"]]
        print(f"    band: {len(wb)}/{len(entries)}", end="")
        if wb:
            print(f"  rows above brim median {st.median([m['band_row_from_brim'] for m in wb]):.0f}"
                  f"  hue gap {st.median([m['bands'][0]['hue_gap'] for m in wb]):.0f}deg"
                  f"  value {st.median([m['bands'][0]['value_delta'] for m in wb]):.0f}"
                  f"  coverage {st.median([m['bands'][0]['coverage'] for m in wb]):.2f}")
        else:
            print()

    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "output", "hat_corpus_construction.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"\nwrote {path}")
