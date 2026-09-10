"""Foundation review for the reworked soft_cap: geometry, then emblem seating.

Two sheets, answering the two complaints in the order they have to be fixed:

  base_sheet     the cap alone, four directions, at gameplay scale and blown
                 up, with its head-coverage footprint drawn against the
                 felt_hat control that already reads as worn.
  placement      a handful of front emblems in the redefined front-panel zone,
                 with the visor row and the plain-cloth margin marked, so the
                 question "is that on the crown or on the brim" is answerable
                 by looking rather than by trusting a number.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import authored, grammar, pngio

OUT = "output/softcap_foundation"
BG = (28, 30, 34, 255)
INK = (232, 232, 228, 255)
DIM = (120, 124, 130, 255)
MARK = (226, 122, 84, 255)
GOOD = (120, 196, 140, 255)
VIEWS = ("front", "right", "left", "back")
PAL = "EVERYDAY_STONE_BLUE"


def frames(garment):
    """The four FS frames as pixel grids, right mirrored from left."""
    px = authored.atlas(garment, 1)
    h = len(px) // 4
    order = ("front", "right", "left", "back")
    return {v: [row[:] for row in px[i * h:(i + 1) * h]]
            for i, v in enumerate(order)}


def cells_of(px):
    return {(x, y) for y, r in enumerate(px)
            for x, p in enumerate(r) if p[3] > 0}


def coverage(px):
    """What the sprite spans — the numbers the 'too small' complaint was about."""
    c = cells_of(px)
    if not c:
        return None
    xs = [x for x, _ in c]
    ys = [y for _, y in c]
    m = grammar.crown_metrics(c)
    return {"w": max(xs) - min(xs) + 1, "h": max(ys) - min(ys) + 1,
            "top": min(ys), "cells": len(c), "ratio": m["brim_ratio"],
            "crown_w": m["crown_width"], "crown_h": m["crown_height"]}


def panel(px, scale, label, sub=""):
    art = pngio.nearest_scale(px, scale)
    w = max(len(art[0]), 90)
    img = pngio.blank_image(w, len(art) + 22, BG)
    pngio.blit(img, art, (w - len(art[0])) // 2, 0)
    pngio.draw_text(img, label, 2, len(art) + 3, scale=1, color=INK)
    if sub:
        pngio.draw_text(img, sub, 2, len(art) + 12, scale=1, color=DIM)
    return img


def row(panels, gap=10):
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


def title(text, w, color=INK):
    img = pngio.blank_image(w, 12, BG)
    pngio.draw_text(img, text, 0, 1, scale=1, color=color)
    return img


def base_sheet():
    cap = frames(authored.build("soft_cap", PAL))
    felt = frames(authored.build("felt_hat", PAL))
    rows = [title("SOFT_CAP BASE — reworked geometry, four directions", 700)]
    for scale, note in ((4, "4x"), (10, "10x")):
        cells = []
        for v in VIEWS:
            m = coverage(cap[v])
            cells.append(panel(cap[v], scale, f"{v} {note}",
                               f"{m['w']}x{m['h']} top{m['top']} "
                               f"ratio{m['ratio']:.2f}"))
        rows.append(row(cells))
    rows.append(title("FELT_HAT control — the hat that already reads as worn",
                      700, DIM))
    rows.append(row([panel(felt[v], 4, f"{v} 4x",
                           f"{coverage(felt[v])['w']}x{coverage(felt[v])['h']} "
                           f"top{coverage(felt[v])['top']}") for v in VIEWS]))
    return stack(rows)


def zone_overlay(px, box, visor, scale):
    """The cap with the legal emblem area and the visor row called out."""
    art = pngio.nearest_scale(px, scale)
    x0, y0, x1, y1 = box
    for x in range(x0, x1 + 1):
        for y in (y0, y1):
            for dx in range(scale):
                art[y * scale][x * scale + dx] = MARK if y == y0 else MARK
                art[(y + 1) * scale - 1][x * scale + dx] = MARK
    for y in range(y0, y1 + 1):
        for dy in range(scale):
            art[y * scale + dy][x0 * scale] = MARK
            art[y * scale + dy][(x1 + 1) * scale - 1] = MARK
    if visor:
        vx0, vy0, vx1, vy1 = visor
        for x in range(vx0, vx1 + 1):
            for y in range(vy0, vy1 + 1):
                for dy in range(scale):
                    art[y * scale + dy][x * scale] = GOOD
    return art


def placement_sheet():
    lib = authored.load()
    cap = next(b for b in lib.bases if b.name == "soft_cap")
    plain = frames(authored.build("soft_cap", PAL))
    zf = cap.zones["front"]
    rows = [title("FRONT EMBLEM SEATING — orange = legal front-panel zone, "
                  "green = visor", 780)]
    over = zone_overlay(plain["front"], zf["front_panel"], zf.get("visor"), 10)
    img = pngio.blank_image(max(len(over[0]), 300), len(over) + 34, BG)
    pngio.blit(img, over, 0, 0)
    gap = zf["visor"][1] - zf["front_panel"][3] - 1 if zf.get("visor") else 0
    pngio.draw_text(img, f"panel rows {zf['front_panel'][1]}-{zf['front_panel'][3]}"
                         f"  visor row {zf['visor'][1]}", 2, len(over) + 4,
                    color=INK)
    pngio.draw_text(img, f"{gap} row(s) of plain cloth between them",
                    2, len(over) + 14, color=GOOD if gap >= 1 else MARK)
    rows.append(img)

    # gem_drop is excluded by the locked cap policy: jewellery is reserved for
    # a future fantasy/festival tag, not a general-purpose cap emblem.
    emblems = [d for d in lib.decals
               if d.zone == "front_panel" and "soft_cap" in (d.fits or ())
               and d.name != "gem_drop"]
    rows.append(title("front view — one emblem each, no combinations", 780, DIM))
    for chunk in (emblems[:4], emblems[4:]):
        if not chunk:
            continue
        cells = []
        for d in chunk:
            f = frames(authored.build("soft_cap", PAL, (d.name,),
                                      style=d.style[0]))
            cells.append(panel(f["front"], 10, d.name))
        rows.append(row(cells))
    rows.append(title("direction rules — front full / profile compressed / "
                      "back none", 780, DIM))
    demo = emblems[0] if emblems else None
    if demo:
        f = frames(authored.build("soft_cap", PAL, (demo.name,),
                                  style=demo.style[0]))
        rows.append(row([panel(f[v], 8, f"{v}  {demo.name}") for v in VIEWS]))
    return stack(rows)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, img in (("base_sheet.png", base_sheet()),
                      ("placement_sheet.png", placement_sheet())):
        pngio.write_rgba_png(os.path.join(OUT, name), img)
        print("wrote", os.path.join(OUT, name))
    cap = frames(authored.build("soft_cap", PAL))
    felt = frames(authored.build("felt_hat", PAL))
    print(f"{'view':6s} {'cap':>22s}   {'felt (control)':>22s}")
    for v in VIEWS:
        c, f = coverage(cap[v]), coverage(felt[v])
        print(f"{v:6s} {c['w']:2d}x{c['h']:<2d} top{c['top']} "
              f"ratio{c['ratio']:.2f} cells{c['cells']:3d}   "
              f"{f['w']:2d}x{f['h']:<2d} top{f['top']} "
              f"ratio{f['ratio']:.2f} cells{f['cells']:3d}")


if __name__ == "__main__":
    main()
