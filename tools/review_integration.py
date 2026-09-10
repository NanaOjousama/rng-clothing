"""Natural-integration review: source motif vs the motif seated on the hat.

Judged at gameplay scale, on the base it is meant for, in every view it
declares.  A motif passes only if it reads as part of the hat: visible, one
shape, taking its light from the surface, and off the hat's own outline unless
it is an edge treatment.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import authored                                              # noqa: E402
from v5.grammar import luminance                                     # noqa: E402
from v5.integration import rim_cells                                 # noqa: E402
from v5.pngio import (blank_image, blit, draw_text, nearest_scale,    # noqa: E402
                      write_rgba_png)

S = 7
BASE = "soft_cap"
OUT = "output/v5_authored/softcap_integration_review.png"
CANON = {"casual": "EVERYDAY_STONE_BLUE", "work": "FIELD_CANVAS_MOSS",
         "cottagecore": "SPRING_SAGE_PETAL", "smart": "WINTER_FROST_INK"}
DIRS = ("front", "right", "left", "back")


def fragments(cells):
    seen, n = set(), 0
    for c in cells:
        if c in seen:
            continue
        n += 1
        stack = [c]
        while stack:
            x, y = stack.pop()
            if (x, y) in seen:
                continue
            seen.add((x, y))
            stack += [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                      if (x + dx, y + dy) in cells and (x + dx, y + dy) not in seen]
    return n


def measure(lib, base, palette, style, motif):
    plain = authored.build(base.name, palette, [], lib, style=style)
    worn = authored.build(base.name, palette, [motif.name], lib, style=style)
    per = {}
    for view in DIRS:
        if view not in motif.views:
            per[view] = None
            continue
        a, b = plain.directions[view], worn.directions[view]
        changed = {(x, y) for y in range(len(a)) for x in range(len(a[0]))
                   if tuple(a[y][x]) != tuple(b[y][x])}
        if not changed:
            per[view] = (0, 0.0, 0, 0)
            continue
        dl = [abs(luminance(a[y][x]) - luminance(b[y][x])) if a[y][x][3] and b[y][x][3]
              else 255.0 for (x, y) in changed]
        rim = rim_cells(set(base.cells[view]))
        per[view] = (len(changed), sum(dl) / len(dl), fragments(changed),
                     len(changed & rim))
    return plain, worn, per


def verdict(motif, per):
    """KEEP / REWORK / REJECT, with the reason that decided it."""
    seen = [v for v in per.values() if v]
    live = [v for v in seen if v[0] > 0]
    if not live:
        return "REJECT", "renders nothing on this base"
    frag = max(v[2] for v in live)
    dls = [v[1] for v in live]
    onrim = max(v[3] for v in live)
    blind = [d for d, v in per.items() if v and v[0] == 0]
    if frag >= 3:
        return "REWORK", f"breaks into {frag} pieces — reads as speckle, not a motif"
    if max(v[0] for v in live) < 4:
        return "REJECT", "too few cells change to read as anything at gameplay scale"
    # Surface motifs must stay off the outline: covering it is what makes
    # embroidery look pasted on.  An ATTACHMENT has to touch the rim — that is
    # how it is anchored — so the question there is whether it merely lands on
    # the edge (fine) or lies ALONG it (a stuck-on object, not a projecting one).
    ANCHOR_FOOT = 2
    if not motif.edge:
        if motif.kind == "surface" and onrim:
            return "REWORK", (f"covers the hat's own outline in {onrim} cells — "
                              f"embroidery must sit inside the panel")
        if motif.kind == "attachment" and onrim > ANCHOR_FOOT:
            return "REWORK", (f"lies along the outline for {onrim} cells rather "
                              f"than projecting from it")
    if max(dls) > 150 and motif.kind == "surface":
        return "REWORK", (f"still swings dL {max(dls):.0f} against the cloth — "
                          f"embroidery should sit in the surface, not on it")
    if blind:
        return "KEEP", (f"seated cleanly; absent in {'/'.join(blind)} because the "
                        f"cap has no zone for it there")
    return "KEEP", (f"one shape in every view, dL {min(dls):.0f}-{max(dls):.0f}, "
                    f"taking its light from the panel underneath")


def main():
    lib = authored.load()
    base = next(b for b in lib.bases if b.name == BASE)
    motifs = [d for d in lib.decals
              if d.slot == "HEAD" and d.fits_base(base) and d.pending
              and set(base.style) & set(d.style)]
    rows = []
    for d in sorted(motifs, key=lambda d: d.name):
        style = sorted(set(base.style) & set(d.style))[0]
        palette = CANON[style]
        plain, worn, per = measure(lib, base, palette, style, d)
        v, why = verdict(d, per)
        rows.append((d, style, palette, worn, per, v, why))

    order = {"KEEP": 0, "REWORK": 1, "REJECT": 2}
    rows.sort(key=lambda r: (order[r[5]], r[0].name))

    tile = 20 * S
    src_w = 6 * S
    width = 300 + src_w + 10 + len(DIRS) * (tile + 6) + 16
    img = blank_image(width, 40 + len(rows) * (tile + 26), (46, 46, 54, 255))
    draw_text(img, "SOFT_CAP NATURAL INTEGRATION REVIEW — source | front / right / left / back",
              8, 6, color=(240, 240, 244, 255))
    colour = {"KEEP": (170, 235, 190, 255), "REWORK": (245, 220, 150, 255),
              "REJECT": (245, 160, 160, 255)}
    y = 26
    print(f"{'motif':18s} {'verdict':8s} why")
    for d, style, palette, worn, per, v, why in rows:
        draw_text(img, d.name[:26], 6, y + 2, color=colour[v])
        draw_text(img, f"{v} — {d.kind}", 6, y + 14, color=colour[v])
        draw_text(img, why[:44], 6, y + 26, color=(190, 190, 198, 255))
        nums = "  ".join(f"{k[:1]}{v2[0]}/{v2[1]:.0f}/{v2[2]}"
                         for k, v2 in per.items() if v2)
        draw_text(img, nums[:44], 6, y + 38, color=(150, 150, 160, 255))
        # the source motif, on its own, at the same scale
        pal = next(p for p in lib.palettes if p.id == palette)
        src = blank_image(6, 6, (70, 70, 78, 255))
        for (x, cy), (role, step) in d.view_cells(d.views[0]).items():
            if 0 <= x < 6 and 0 <= cy < 6:
                src[cy][x] = pal.color(role, step)
        blit(img, nearest_scale(src, S), 300, y)
        x = 300 + src_w + 10
        for view in DIRS:
            tilemap = [[p if p[3] else (112, 112, 120, 255) for p in r]
                       for r in worn.directions[view]]
            blit(img, nearest_scale(tilemap, S), x, y)
            x += tile + 6
        y += tile + 26
        print(f"{d.name:18s} {v:8s} {why}")
    write_rgba_png(OUT, img)
    print(f"\n{len(rows)} pending motifs -> {OUT}")


if __name__ == "__main__":
    main()
