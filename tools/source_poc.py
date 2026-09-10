"""PROOF OF CONCEPT for the authored-source pivot.

One hat construction and one top construction, taken from the source library
and carried through the whole path: dissect -> reconstruct -> prove -> recolour
-> remix -> export.  Nothing is promoted to production from here; the point is
to show whether dissection and clean reassembly actually work on real assets.

Chosen on evidence rather than preference:
  Beret   (Cottagecore Set, plurffle) -- 5 siblings, 4 directions, greyscale,
          and the only hat family whose decoration survives as REUSABLE.
  Blouse  (Cottagecore Set, plurffle) -- 5 siblings, 4 directions, and the
          pack declares its five ColorMasks, so its semantic vocabulary is the
          author's own rather than one we inferred.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import authored, pngio
from v5.source import decompose, library, render

OUT = "output/source_poc"
BG = (26, 28, 32, 255)
INK = (233, 233, 228, 255)
DIM = (124, 128, 134, 255)
OK = (110, 200, 135, 255)
BAD = (228, 84, 74, 255)
CHECK = (48, 52, 58, 255)

FS_ORDER = {"Hats": ["Front", "Right", "Left", "Back"],
            "Shirts": ["Front", "Right", "Left", "Back"]}


def checker(w, h, s=4):
    return [[(CHECK if ((x // s + y // s) % 2) else (38, 41, 46, 255))
             for x in range(w)] for y in range(h)]


def tile(frame, scale, label, sub=""):
    h, w = len(frame), len(frame[0])
    bg = checker(w, h)
    comp = [[frame[y][x] if frame[y][x][3] else bg[y][x] for x in range(w)]
            for y in range(h)]
    art = pngio.nearest_scale(comp, scale)
    img = pngio.blank_image(max(len(art[0]), 92), len(art) + 22, BG)
    pngio.blit(img, art, 0, 0)
    pngio.draw_text(img, label, 1, len(art) + 3, color=INK)
    if sub:
        pngio.draw_text(img, sub, 1, len(art) + 13, color=DIM)
    return img


def row(tiles, gap=8):
    h = max(len(t) for t in tiles)
    w = sum(len(t[0]) for t in tiles) + gap * (len(tiles) - 1)
    img = pngio.blank_image(w, h, BG)
    x = 0
    for t in tiles:
        pngio.blit(img, t, x, 0)
        x += len(t[0]) + gap
    return img


def title(t, w=980, c=INK):
    img = pngio.blank_image(w, 12, BG)
    pngio.draw_text(img, t, 0, 1, color=c)
    return img


def stack(rows, gap=12, pad=12):
    w = max(len(r[0]) for r in rows) + pad * 2
    h = sum(len(r) for r in rows) + gap * (len(rows) - 1) + pad * 2
    img = pngio.blank_image(w, h, BG)
    y = pad
    for r in rows:
        pngio.blit(img, r, pad, y)
        y += len(r) + gap
    return img


def diff_frame(a, b):
    """Red where two frames differ — the reconstruction proof, drawn."""
    h, w = len(a), len(a[0])
    out = [[(40, 43, 48, 255)] * w for _ in range(h)]
    n = 0
    for y in range(h):
        for x in range(w):
            if tuple(a[y][x]) != tuple(b[y][x]):
                out[y][x] = BAD
                n += 1
            elif a[y][x][3]:
                out[y][x] = (70, 74, 80, 255)
    return out, n


def component_frame(comp, direction, size):
    """The extracted delta alone, on transparency."""
    w, h = size
    rows = [[(0, 0, 0, 0)] * w for _ in range(h)]
    for (x, y), px in comp.cells.get(direction, {}).items():
        if px and y < h and x < w:
            rows[y][x] = tuple(px)
    return rows


def build(family_name, category, role_hint, palettes, comps_wanted):
    cat = json.load(open("source_catalog/catalog.json"))
    group = [a for a in cat["appearances"]
             if a["stem"] == family_name and a["category"] == category
             and not a["analysis"].get("error")]
    fam = decompose.build_family(group)
    rep = decompose.reconstruct_report(fam)
    bases, comps = library.load()
    base = next(b for b in bases if b.name == fam.base_app["name"]
                and b.family == family_name)
    mine = [c for c in comps if c.family == family_name]
    dirs = FS_ORDER[category]
    lib = authored.load()

    rows = [title(f"{family_name.upper()}  —  {fam.pack} by {fam.author}"
                  f"   [READ-ONLY SOURCE]")]

    # 1 — the original source, as the author drew it
    rows.append(title("1  ORIGINAL SOURCE ASSETS", c=DIM))
    for app in group:
        f = decompose.frames_of(app)
        rows.append(row([tile(f[d], 7, f"{app['name'][:22]} {d}") for d in dirs
                         if d in f]))

    # 2 — base and extracted components
    rows.append(title("2  EXTRACTED BASE + COMPONENTS", c=DIM))
    rows.append(row([tile(base.frames[d], 7, f"BASE {d}") for d in dirs
                     if d in base.frames]))
    for c in mine:
        rows.append(row([tile(component_frame(c, d, base.size), 7,
                              f"{c.qualifier or c.name} {d}",
                              c.classification) for d in dirs
                         if d in c.cells]))

    # 3 — reconstruction proof
    rows.append(title("3  RECONSTRUCTION  (base + delta vs original; "
                      "red = any differing pixel)", c=DIM))
    total_diff = 0
    for d in fam.deltas:
        if d.classification == decompose.REFERENCE_ONLY:
            continue
        rebuilt = decompose.apply_delta(fam.base_frames, d)
        orig = decompose.frames_of(d.app)
        tiles, n = [], 0
        for dd in dirs:
            if dd not in rebuilt:
                continue
            df, k = diff_frame(rebuilt[dd], orig[dd])
            n += k
            tiles.append(tile(df, 7, f"{dd} diff", f"{k} px"))
        total_diff += n
        rows.append(row([tile(rebuilt[dirs[0]], 7, d.name[:22], "rebuilt")]
                        + tiles))

    # 4 — remixes: authored geometry, new palettes
    rows.append(title("4  REMIX VARIANTS  (authored silhouette, "
                      "palette + component only)", c=DIM))
    variants = []
    for pal_id in palettes:
        pal = next(p for p in lib.palettes if p.id == pal_id)
        for want in comps_wanted:
            use = [c for c in mine if c.qualifier == want] if want else []
            frames = render.render(base, pal, use, role_hint)
            label = f"{pal_id.split('_')[0].title()}{'+' + want if want else ''}"
            variants.append((label, frames, pal, use))
    for label, frames, pal, use in variants:
        rows.append(row([tile(frames[d], 7, f"{label[:20]} {d}") for d in dirs
                         if d in frames]))

    return fam, rep, base, mine, variants, rows, total_diff


def main():
    os.makedirs(OUT, exist_ok=True)
    report = {}
    for family, category, role, pals, comps in (
            ("Beret", "Hats", "body",
             ["EVERYDAY_STONE_BLUE", "AUTUMN_OCHRE_PLUM", "SPRING_SAGE_PETAL"],
             ["", "Leaf", "Dotted"]),
            ("Blouse", "Shirts", "body",
             ["COASTAL_SEAFOAM_CORAL", "FORMAL_PEARL_MIDNIGHT"],
             [""])):
        fam, rep, base, mine, variants, rows, diff = build(
            family, category, role, pals, comps)
        pngio.write_rgba_png(f"{OUT}/{family.lower()}_poc.png", stack(rows))
        report[family] = {
            "pack": fam.pack, "author": fam.author,
            "base": base.name, "base_cells": base.cells,
            "vocabulary": [list(c) for c in base.vocab],
            "tone": base.tone, "roles": base.roles,
            "components": [{"name": c.name, "class": c.classification,
                            "reason": c.reason} for c in mine],
            "promoted_to_own_base": [p["name"]
                                     for p in rep["promote_to_own_base"]],
            "reconstruction_exact": rep["all_exact"],
            "reconstruction_diff_pixels": diff,
            "modelled_variants": rep["modelled_count"],
            "variants_generated": [v[0] for v in variants],
            "credit": render.credits_for(base, mine),
        }
        print(f"{family}: base {base.name!r} {base.cells} cells, "
              f"{len(mine)} components, reconstruction diff = {diff} px, "
              f"{len(variants)} remixes -> {OUT}/{family.lower()}_poc.png")
    json.dump(report, open(f"{OUT}/report.json", "w"), indent=1)
    print("wrote", f"{OUT}/report.json")


if __name__ == "__main__":
    main()
