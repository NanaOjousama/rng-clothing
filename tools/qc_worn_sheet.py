"""A worn contact sheet framed on the HEAD, built from existing captures.

The bridge's own `*_head.png` crop is framed on the farmer's world position, so
it lands low: mostly floor, with the top of the hat cut off.  This rebuilds the
sheet from the isolated `*_worn.png` frames instead, using a FIXED window
measured from the captures themselves — fixed so that two hats of different
heights stay comparable, which a per-hat crop destroys.

Window (measured over this session's 80 frames, in the 256x256 isolated frame):
farmer x 96-159, y 56-175; hat y 56-91.  So the head, the whole hat and a few
rows of shoulder live in x 92-163, y 50-128.

    python3 tools/qc_worn_sheet.py <session-dir> [--scale 3] [--which worn]
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5.pngio import (blank_image, blit, draw_text, nearest_scale,
                      read_rgba_png, write_rgba_png)

DIRS = ("front", "right", "left", "back")
WINDOW = (92, 163, 50, 128)          # x0, x1, y0, y1 inclusive
BG = (46, 46, 54, 255)
TILE_BG = (120, 120, 128, 255)


def crop(im, window=WINDOW):
    x0, x1, y0, y1 = window
    h, w = len(im), len(im[0])
    return [[im[y][x] if 0 <= y < h and 0 <= x < w else (0, 0, 0, 0)
             for x in range(x0, x1 + 1)] for y in range(y0, y1 + 1)]


def flatten(tile, bg=TILE_BG):
    """Composite onto a flat ground: an isolated frame is transparent, and a
    transparent tile on a dark sheet hides exactly the dark hats we care about."""
    out = []
    for row in tile:
        line = []
        for px in row:
            if px[3] == 0:
                line.append(bg)
            elif px[3] == 255:
                line.append(px)
            else:
                a = px[3] / 255
                line.append(tuple(round(px[i] * a + bg[i] * (1 - a)) for i in range(3)) + (255,))
        out.append(line)
    return out


def build(session: str, scale: int = 3, which: str = "worn") -> str:
    folders = [f for f in sorted(os.listdir(session))
               if os.path.isdir(os.path.join(session, f))]
    rows = []
    # a bare-headed reference row first, so seating can be judged against it
    ref = os.path.join(session, folders[0])
    bare = [nearest_scale(flatten(crop(read_rgba_png(
        os.path.join(ref, f"{d}_nohat.png")))), scale) for d in DIRS
        if os.path.exists(os.path.join(ref, f"{d}_nohat.png"))]
    if bare:
        rows.append(("(no hat)", bare))
    for f in folders:
        d = os.path.join(session, f)
        tiles = []
        for direction in DIRS:
            p = os.path.join(d, f"{direction}_{which}.png")
            if os.path.exists(p):
                tiles.append(nearest_scale(flatten(crop(read_rgba_png(p))), scale))
        if tiles:
            rows.append((f, tiles))

    th, tw = len(rows[0][1][0]), len(rows[0][1][0][0])
    pad, label = 8, 168
    img = blank_image(label + len(DIRS) * (tw + pad) + pad,
                      26 + len(rows) * (th + pad), BG)
    draw_text(img, f"WORN IN GAME — {os.path.basename(session)} — "
                   f"front / right / left / back", 8, 6, color=(238, 238, 242, 255))
    y = 24
    for name, tiles in rows:
        draw_text(img, name[:24], 6, y + th // 2 - 4, color=(224, 224, 230, 255))
        x = label
        for t in tiles:
            blit(img, t, x, y)
            x += tw + pad
        y += th + pad
    out = os.path.join(session, f"worn_sheet_{which}.png")
    write_rgba_png(out, img)
    return out


def grid(session: str, direction: str = "front", scale: int = 3,
         which: str = "worn", cols: int = 5) -> str:
    """One direction, every hat, on a single screen — for judging at a glance.

    The four-direction sheet is 5000px tall by necessity; this is the same
    frames laid out so the whole batch can be compared side by side.
    """
    folders = [f for f in sorted(os.listdir(session))
               if os.path.isdir(os.path.join(session, f))]
    tiles = []
    for f in folders:
        p = os.path.join(session, f, f"{direction}_{which}.png")
        if os.path.exists(p):
            tiles.append((f, nearest_scale(flatten(crop(read_rgba_png(p))), scale)))
    th, tw = len(tiles[0][1]), len(tiles[0][1][0])
    pad, label = 10, 12
    rows = (len(tiles) + cols - 1) // cols
    img = blank_image(cols * (tw + pad) + pad, 24 + rows * (th + label + pad), BG)
    draw_text(img, f"WORN IN GAME — {direction.upper()} — "
                   f"{os.path.basename(session)}", 8, 6, color=(238, 238, 242, 255))
    for i, (name, t) in enumerate(tiles):
        x = pad + (i % cols) * (tw + pad)
        y = 24 + (i // cols) * (th + label + pad)
        blit(img, t, x, y)
        draw_text(img, name[:20], x, y + th + 2, color=(224, 224, 230, 255))
    out = os.path.join(session, f"worn_grid_{direction}.png")
    write_rgba_png(out, img)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("session")
    ap.add_argument("--scale", type=int, default=3)
    ap.add_argument("--which", default="worn",
                    choices=("worn", "screen", "head", "hatonly"))
    ap.add_argument("--grid", metavar="DIRECTION",
                    help="one-direction grid instead of the four-direction sheet")
    a = ap.parse_args()
    if a.grid:
        print("wrote", grid(a.session, a.grid, a.scale, a.which))
    else:
        print("wrote", build(a.session, a.scale, a.which))
