"""Original approved soft_cap vs the minimally enlarged one.

The ORIGINAL art here is not a guess: it was recovered pixel-exactly from the
in-game capture of the plain cap (session 20260907-022706, Dec11CapPlain) by
inverting the 4x screen scale and mapping each colour back through the
vanilla_016 tone levels.  It cross-checks against a copy in the session log,
and its right view is the exact mirror of its left, which a lossy recovery
would not produce.  That is the baseline every comparison below is measured
against, so "preserved" means preserved against the thing that shipped.

The only authorised change is ONE cell of crown width per side.  Nothing else
moves: the visor keeps its row count, its split stub row, its value pattern
and its position relative to the crown; the peak keeps its absolute forward
extent; the envelope keeps its top and bottom rows.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import authored, grammar, pngio

OUT = "output/softcap_enlargement"
BG = (28, 30, 34, 255)
INK = (232, 232, 228, 255)
DIM = (122, 126, 132, 255)
MARK = (226, 122, 84, 255)
GOOD = (120, 196, 140, 255)
PAL = "EVERYDAY_STONE_BLUE"
VIEWS = ("front", "right", "left", "back")

# --- the shipped cap, recovered from qc_bridge/captures/20260907-022706 ------
ORIG = {
    "front": [
        "", "", "", "",
        ".........33.........",
        ".......224422.......",
        "......24566652......",
        ".....2455566652.....",
        ".....2443333562.....",
        ".....2434554352.....",
        ".....2343333432.....",
        ".....22.....222.....",
    ],
    "left": [
        "", "", "", "",
        ".........33.........",
        ".......334432.......",
        "......35555432......",
        "..3333566554432.....",
        ".35443665545442.....",
        ".34554555454432.....",
        "..3224433222222.....",
    ],
    "back": [
        "", "", "", "", "",
        ".......333333.......",
        "......34455543......",
        ".....3445456543.....",
        ".....3444545553.....",
        ".....1444454541.....",
        ".....1344444431.....",
        ".....1331111331.....",
        ".....131....131.....",
        "......11111111......",
    ],
}


def orig_cells():
    """The recovered art as {view: {cell: (role, step)}}, right mirrored."""
    out = {}
    for view, art in ORIG.items():
        cells = {}
        for y, line in enumerate(art):
            for x, ch in enumerate(line):
                if ch != ".":
                    cells[(x, y)] = ("body", int(ch) - 1)
        out[view] = cells
    out["right"] = {(19 - x, y): v for (x, y), v in out["left"].items()}
    return out


def paint(cells, palette, tone):
    """Same path the runtime uses: the tone profile re-levels the PALETTE."""
    pal = tone.apply(palette) if tone else palette
    rows = [[(0, 0, 0, 0) for _ in range(20)] for _ in range(20)]
    for (x, y), (role, step) in cells.items():
        rows[y][x] = pal.color(role, step)
    return rows


def frames(garment):
    px = authored.atlas(garment, 1)
    h = len(px) // 4
    return {v: [r[:] for r in px[i * h:(i + 1) * h]]
            for i, v in enumerate(VIEWS)}


def geom(cells):
    c = set(cells)
    xs = [x for x, _ in c]
    ys = [y for _, y in c]
    m = grammar.crown_metrics(c)
    return {"w": max(xs) - min(xs) + 1, "h": max(ys) - min(ys) + 1,
            "rows": (min(ys), max(ys)), "crown_w": m["crown_width"],
            "ratio": m["brim_ratio"], "cells": len(c)}


def panel(px, scale, label, sub="", box=None):
    art = pngio.nearest_scale(px, scale)
    if box:
        x0, y0, x1, y1 = box
        for x in range(x0 * scale, (x1 + 1) * scale):
            art[y0 * scale][x] = MARK
            art[(y1 + 1) * scale - 1][x] = MARK
        for y in range(y0 * scale, (y1 + 1) * scale):
            art[y][x0 * scale] = MARK
            art[y][(x1 + 1) * scale - 1] = MARK
    w = max(len(art[0]), 110)
    img = pngio.blank_image(w, len(art) + 24, BG)
    pngio.blit(img, art, (w - len(art[0])) // 2, 0)
    pngio.draw_text(img, label, 2, len(art) + 4, color=INK)
    if sub:
        pngio.draw_text(img, sub, 2, len(art) + 14, color=DIM)
    return img


def row(panels, gap=12):
    h = max(len(p) for p in panels)
    w = sum(len(p[0]) for p in panels) + gap * (len(panels) - 1)
    img = pngio.blank_image(w, h, BG)
    x = 0
    for p in panels:
        pngio.blit(img, p, x, 0)
        x += len(p[0]) + gap
    return img


def stack(rows, gap=14, pad=12):
    w = max(len(r[0]) for r in rows) + pad * 2
    h = sum(len(r) for r in rows) + gap * (len(rows) - 1) + pad * 2
    img = pngio.blank_image(w, h, BG)
    y = pad
    for r in rows:
        pngio.blit(img, r, pad, y)
        y += len(r) + gap
    return img


def title(text, w=820, color=INK):
    img = pngio.blank_image(w, 12, BG)
    pngio.draw_text(img, text, 0, 1, color=color)
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    lib = authored.load()
    cap = next(b for b in lib.bases if b.name == "soft_cap")
    pal = next(p for p in lib.palettes if p.id == PAL)
    tone = lib.tone_for(cap)

    oc = orig_cells()
    o_px = {v: paint(oc[v], pal, tone) for v in VIEWS}
    n_px = frames(authored.build("soft_cap", PAL))

    rows = []
    # 1 + 2: the two bases, four directions each, blown up
    for label, px, tag in (("1  ORIGINAL (approved, recovered from capture)", o_px, "orig"),
                           ("2  MINIMALLY ENLARGED (+1 cell per side)", n_px, "new")):
        rows.append(title(label))
        rows.append(row([panel(px[v], 9, v,
                               f"{geom(cells_of(px[v]))['w']}x{geom(cells_of(px[v]))['h']}"
                               f" crown{geom(cells_of(px[v]))['crown_w']}")
                         for v in VIEWS]))

    # 3: gameplay scale, alternating, so the size change is judged at 4x
    rows.append(title("3  SIDE BY SIDE AT GAMEPLAY SCALE (4x) — orig / enlarged"))
    cells = []
    for v in VIEWS:
        cells.append(panel(o_px[v], 4, f"{v} orig"))
        cells.append(panel(n_px[v], 4, f"{v} NEW"))
    rows.append(row(cells, gap=6))

    # 4: the front panel, which is the whole point of the change
    rows.append(title("4  FRONT-PANEL USABLE AREA (orange box = legal emblem zone)"))
    o_zone = cap_front_zone(oc["front"])
    n_zone = cap.zones["front"]["front_panel"]
    ow = o_zone[2] - o_zone[0] + 1
    oh = o_zone[3] - o_zone[1] + 1
    nw = n_zone[2] - n_zone[0] + 1
    nh = n_zone[3] - n_zone[1] + 1
    rows.append(row([
        panel(o_px["front"], 12, "original panel", f"{ow}x{oh} = {ow*oh} cells", o_zone),
        panel(n_px["front"], 12, "enlarged panel", f"{nw}x{nh} = {nw*nh} cells", n_zone),
    ]))
    sheet = stack(rows)
    pngio.write_rgba_png(os.path.join(OUT, "enlargement.png"), sheet)
    print("wrote", os.path.join(OUT, "enlargement.png"))

    print(f"\n{'view':7s} {'original':>26s}   {'enlarged':>26s}")
    for v in VIEWS:
        a, b = geom(cells_of(o_px[v])), geom(cells_of(n_px[v]))
        print(f"{v:7s} {a['w']:2d}x{a['h']:<2d} rows{a['rows']} crown{a['crown_w']:2d} "
              f"ratio{a['ratio']:.2f}   {b['w']:2d}x{b['h']:<2d} rows{b['rows']} "
              f"crown{b['crown_w']:2d} ratio{b['ratio']:.2f}")
    print(f"\nfront panel  {ow}x{oh} = {ow*oh} cells  ->  {nw}x{nh} = {nw*nh} cells "
          f"({(nw*nh)/(ow*oh):.2f}x)")


def cells_of(px):
    return {(x, y) for y, r in enumerate(px)
            for x, p in enumerate(r) if p[3] > 0}


def cap_front_zone(cells):
    """Run the live zone derivation over the recovered original."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
    from author_base_assets import cap_zones
    return cap_zones({"front": set(cells)})["front"]["front_panel"]


if __name__ == "__main__":
    main()
