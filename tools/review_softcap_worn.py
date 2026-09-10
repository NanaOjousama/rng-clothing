"""In-game comparison: the approved cap vs the +1-cell-per-side candidate.

Both were captured in ONE session with one palette, one hairstyle, one pose and
one offset, so the only variable between the first two rows is the two cells of
width.  The felt hat is the seating control every earlier session used.

Head coverage is the number the "too small / sitting on the forehead" complaint
was really about: the farmer's head is 56 screen px wide, and a hat that spans
40 of them reads as perched no matter where it is positioned.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import pngio

SESSION = "qc_bridge/captures/20260908-205617"
OUT = "output/softcap_worn"
BG = (28, 30, 34, 255)
INK = (232, 232, 228, 255)
DIM = (122, 126, 132, 255)
MARK = (226, 122, 84, 255)
VIEWS = ("front", "right", "left", "back")
HATS = [("Cap01Orig", "ORIGINAL 10-wide"),
        ("Cap02Wide", "ENLARGED 12-wide  <- candidate"),
        ("Cap03Felt", "felt control")]
SCALE = 3
# the farmer's head, in the capture's own coordinates
HEAD = (96, 60, 160, 108)


def cells(im):
    return [(x, y) for y, r in enumerate(im) for x, p in enumerate(r) if p[3] > 0]


def crop(im, box, bg=(46, 49, 54, 255)):
    x0, y0, x1, y1 = box
    out = []
    for y in range(y0, y1):
        row = []
        for x in range(x0, x1):
            p = im[y][x] if 0 <= y < len(im) and 0 <= x < len(im[0]) else bg
            row.append(p if p[3] else bg)
        out.append(row)
    return out


def tile(path, box, scale=SCALE, mark_head=False):
    im = pngio.read_rgba_png(path)
    art = pngio.nearest_scale(crop(im, box), scale)
    if mark_head:
        for x in range(len(art[0])):
            art[0][x] = MARK
    return art


def row_of(tiles, labels, gap=10, sub=None):
    h = max(len(t) for t in tiles)
    w = sum(len(t[0]) for t in tiles) + gap * (len(tiles) - 1)
    img = pngio.blank_image(w, h + 24, BG)
    x = 0
    for i, t in enumerate(tiles):
        pngio.blit(img, t, x, 0)
        pngio.draw_text(img, labels[i], x + 2, h + 4, color=INK)
        if sub:
            pngio.draw_text(img, sub[i], x + 2, h + 14, color=DIM)
        x += len(t[0]) + gap
    return img


def stack(rows, gap=16, pad=12):
    w = max(len(r[0]) for r in rows) + pad * 2
    h = sum(len(r) for r in rows) + gap * (len(rows) - 1) + pad * 2
    img = pngio.blank_image(w, h, BG)
    y = pad
    for r in rows:
        pngio.blit(img, r, pad, y)
        y += len(r) + gap
    return img


def title(text, w=760, color=INK):
    img = pngio.blank_image(w, 12, BG)
    pngio.draw_text(img, text, 0, 1, color=color)
    return img


def coverage(folder, view):
    """Hat footprint against the head's own footprint, in screen px."""
    hat = cells(pngio.read_rgba_png(f"{SESSION}/{folder}/{view}_hatonly.png"))
    worn = pngio.read_rgba_png(f"{SESSION}/{folder}/{view}_worn.png")
    nohat = pngio.read_rgba_png(f"{SESSION}/{folder}/{view}_nohat.png")
    head = [(x, y) for y, r in enumerate(nohat) for x, p in enumerate(r)
            if p[3] and HEAD[1] <= y < HEAD[3]]
    hx = {x for x, _ in hat}
    headx = {x for x, _ in head}
    top = min(y for _, y in hat)
    head_top = min(y for _, y in head)
    return {"w": max(hx) - min(hx) + 1, "cover": len(hx & headx),
            "head_w": len(headx), "top_delta": top - head_top}


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = [title("IN-GAME  session 20260908-205617  one palette, one pose, "
                  "one offset (+0,-2)")]
    for folder, label in HATS:
        m = {v: coverage(folder, v) for v in VIEWS}
        rows.append(title(
            f"{label}   head coverage {m['front']['cover']}/{m['front']['head_w']} px"
            f"   hat top {m['front']['top_delta']:+d} px from head top",
            color=INK if folder != "Cap03Felt" else DIM))
        rows.append(row_of(
            [tile(f"{SESSION}/{folder}/{v}_worn.png", HEAD) for v in VIEWS],
            list(VIEWS),
            sub=[f"{m[v]['w']}px wide" for v in VIEWS]))
    sheet = stack(rows)
    pngio.write_rgba_png(f"{OUT}/worn_comparison.png", sheet)
    print("wrote", f"{OUT}/worn_comparison.png")

    print(f"\n{'hat':22s} {'view':6s} {'hat w':>6s} {'covers':>8s} {'top':>5s}")
    for folder, label in HATS:
        for v in VIEWS:
            m = coverage(folder, v)
            print(f"{label[:22]:22s} {v:6s} {m['w']:>5d}px "
                  f"{m['cover']:>4d}/{m['head_w']:<3d} {m['top_delta']:>+4d}px")


if __name__ == "__main__":
    main()
