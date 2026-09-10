"""A/B: nearest-neighbour RESIZE of the source motif vs a NATIVE REMAKE.

Same five source motifs, same base, same zones, same integration pass — the
only variable is how the art got to 20x20 scale:

    A  RESIZED   the source sprite sampled down with nearest-neighbour only.
                 No averaging, no blur: one source pixel per target cell.
                 Background is dropped, then colours are ranked into the
                 semantic ramp so it can be recoloured like anything else.
    B  REMAKE    redrawn at target size, keeping only silhouette and identity.

Neither is written to the library: both are built in memory, so this compares
the two methods without committing to either.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import authored                                              # noqa: E402
from v5.grammar import luminance                                     # noqa: E402
from v5.integration import rim_cells                                 # noqa: E402
from v5.pngio import (blank_image, blit, draw_text, nearest_scale,    # noqa: E402
                      read_rgba_png, write_rgba_png)

SHEET = "motif/SOFTCAP_MOTIF.png"          # the PNG source, no JPEG artefacts
BG = (194, 202, 214)
S = 7
OUT = "output/v5_authored/ab_resize_vs_remake.png"
BASE = "soft_cap"
DIRS = ("front", "right", "left", "back")

IM = read_rgba_png(SHEET)
H, W = len(IM), len(IM[0])


def ink(px):
    return sum(abs(px[i] - BG[i]) for i in range(3)) > 60


def rows_of_sheet():
    rows = [sum(1 for x in range(W) if ink(IM[y][x])) for y in range(H)]
    out, start = [], None
    for y, n in enumerate(rows):
        if n > 3 and start is None:
            start = y
        elif n <= 3 and start is not None:
            if y - start > 10:
                out.append((start, y - 1))
            start = None
    if start is not None:
        out.append((start, H - 1))
    return out


def cols_of(y0, y1):
    c = [sum(1 for y in range(y0, y1 + 1) if ink(IM[y][x])) for x in range(W)]
    out, s = [], None
    for x, n in enumerate(c):
        if n > 0 and s is None:
            s = x
        elif n == 0 and s is not None:
            if x - s > 4:
                out.append((s, x - 1))
            s = None
    if s is not None:
        out.append((s, W - 1))
    return out


ROWS = rows_of_sheet()
GRID = {i: cols_of(*r) for i, r in enumerate(ROWS)}


def resize_nn(row, idx, w, h, role):
    """Nearest-neighbour ONLY: one source pixel decides each target cell."""
    y0, y1 = ROWS[row]
    x0, x1 = GRID[row][idx]
    sw, sh = (x1 - x0 + 1) / w, (y1 - y0 + 1) / h
    picked = {}
    for cy in range(h):
        for cx in range(w):
            sx = int(x0 + (cx + 0.5) * sw)
            sy = int(y0 + (cy + 0.5) * sh)
            px = IM[min(sy, H - 1)][min(sx, W - 1)]
            if ink(px):
                picked[(cx, cy)] = luminance(px)
    if not picked:
        return {}
    vals = sorted(set(picked.values()))
    lo, hi = vals[0], vals[-1]
    span = max(1.0, hi - lo)
    return {c: (role, max(0, min(5, round((v - lo) / span * 5))))
            for c, v in picked.items()}


def art_to_cells(rows, chars):
    out = {}
    for y, line in enumerate(rows):
        for x, ch in enumerate(line):
            if ch != ".":
                for role, cs in chars.items():
                    if ch in cs:
                        out[(x, y)] = (role, cs.index(ch))
    return out


CHARS = {"body": "123456", "trim": "abcdef", "accent": "pqrstu",
         "hardware": "ABCDEF"}

# (label, source row/idx, size, role, kind, zone, anchor_cell, anchor_pt,
#  remake art, views)
CASES = [
    ("patch / badge", (0, 1), (4, 2), "trim", "surface", "crown_face",
     (0, 0), "top_centre", ["bddb", "bffb"], ("front", "back")),
    ("heart emblem", (0, 5), (3, 3), "accent", "attachment", "side",
     (1, 2), "top_right", ["t.t", "tut", ".t."], ("front", "left", "back")),
    ("leaf", (0, 3), (3, 3), "accent", "attachment", "side",
     (0, 2), "top_right", [".tu", "tut", "s.."], ("front", "left")),
    ("gem / pin", (3, 8), (2, 3), "accent", "attachment", "side",
     (0, 2), "top_right", ["tu", "uu", "qq"], ("front", "left")),
    ("ribbon tag", (5, 12), (2, 4), "trim", "attachment", "side",
     (0, 0), "top_right", ["dd", "cd", "cc", ".c"], ("front", "left")),
]


def make_decal(name, cells, size, role, kind, zone, anchor, apt, views):
    return authored.Decal(name=name, slot="HEAD", attach="", z=3,
                          style=("casual", "work", "cottagecore", "smart"),
                          views=tuple(views), size=size, cells=cells, zone=zone,
                          kind=kind, edge=False, pending=True,
                          max_extent=9, per_view=False,
                          anchor_cell=anchor, anchor_point=apt, fits=(BASE,))


def fragments(cells):
    seen, n = set(), 0
    for c in cells:
        if c in seen:
            continue
        n += 1
        st = [c]
        while st:
            x, y = st.pop()
            if (x, y) in seen:
                continue
            seen.add((x, y))
            st += [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                   if (x + dx, y + dy) in cells and (x + dx, y + dy) not in seen]
    return n


def wear(lib, base, palette, tone, decal):
    dirs, dropped = authored._render(base, [decal], palette, tone)
    return dirs, dropped


def measure(plain, worn, base, views):
    per = {}
    for v in DIRS:
        if v not in views:
            per[v] = None
            continue
        a, b = plain[v], worn[v]
        changed = {(x, y) for y in range(len(a)) for x in range(len(a[0]))
                   if tuple(a[y][x]) != tuple(b[y][x])}
        if not changed:
            per[v] = (0, 0.0, 0)
            continue
        dl = [abs(luminance(a[y][x]) - luminance(b[y][x]))
              if a[y][x][3] and b[y][x][3] else 255.0 for (x, y) in changed]
        per[v] = (len(changed), sum(dl) / len(dl), fragments(changed))
    return per


def judge(a, b):
    """RESIZE BETTER / REMAKE BETTER / BOTH USABLE / NEITHER USABLE."""
    def ok(per):
        live = [v for v in per.values() if v and v[0] > 0]
        if not live:
            return False, "renders nothing"
        if max(v[2] for v in live) >= 3:
            return False, f"{max(v[2] for v in live)} fragments"
        if max(v[0] for v in live) < 4:
            return False, f"only {max(v[0] for v in live)} cells"
        return True, f"{min(v[0] for v in live)}-{max(v[0] for v in live)} cells"

    a_ok, a_why = ok(a)
    b_ok, b_why = ok(b)
    if a_ok and b_ok:
        # both read: prefer the one that is one shape and larger-reading
        a_cells = max(v[0] for v in a.values() if v)
        b_cells = max(v[0] for v in b.values() if v)
        if abs(a_cells - b_cells) <= 1:
            return "BOTH USABLE", f"resize {a_why}, remake {b_why}"
        return ("RESIZE BETTER" if a_cells > b_cells else "REMAKE BETTER",
                f"resize {a_why}, remake {b_why}")
    if a_ok:
        return "RESIZE BETTER", f"remake fails: {b_why}"
    if b_ok:
        return "REMAKE BETTER", f"resize fails: {a_why}"
    return "NEITHER USABLE", f"resize {a_why}; remake {b_why}"


def main():
    lib = authored.load()
    base = next(b for b in lib.bases if b.name == BASE)
    tone = lib.tone_for(base)
    palette = next(p for p in lib.palettes if p.id == "EVERYDAY_STONE_BLUE")
    plain, _ = authored._render(base, [], palette, tone)

    rows = []
    for label, (r, i), size, role, kind, zone, anchor, apt, remake, views in CASES:
        rz_cells = resize_nn(r, i, size[0], size[1], role)
        rz = make_decal(f"{label}-resize", rz_cells, size, role, kind, zone,
                        anchor, apt, views)
        rm_cells = art_to_cells(remake, CHARS)
        rm = make_decal(f"{label}-remake", rm_cells, size, role, kind, zone,
                        anchor, apt, views)
        a_dirs, a_drop = wear(lib, base, palette, tone, rz)
        b_dirs, b_drop = wear(lib, base, palette, tone, rm)
        a_per = measure(plain, a_dirs, base, views)
        b_per = measure(plain, b_dirs, base, views)
        v, why = judge(a_per, b_per)
        rows.append((label, rz_cells, rm_cells, size, a_dirs, b_dirs,
                     a_per, b_per, v, why, views, palette))
        print(f"{label:14s} {v:15s} {why}")

    tile = 20 * S
    iso = 6 * S
    width = 300 + iso * 2 + 20 + len(DIRS) * (tile + 6) + 20
    img = blank_image(width, 40 + len(rows) * 2 * (tile + 18) + 24,
                      (46, 46, 54, 255))
    draw_text(img, "A/B — nearest-neighbour RESIZE vs NATIVE REMAKE — "
                   "isolated | front / right / left / back", 8, 6,
              color=(240, 240, 244, 255))
    colour = {"RESIZE BETTER": (180, 215, 245, 255),
              "REMAKE BETTER": (170, 235, 190, 255),
              "BOTH USABLE": (235, 230, 170, 255),
              "NEITHER USABLE": (245, 160, 160, 255)}
    y = 26
    for (label, rzc, rmc, size, a_dirs, b_dirs, a_per, b_per, v, why,
         views, pal) in rows:
        draw_text(img, label.upper(), 6, y, color=colour[v])
        draw_text(img, v, 6, y + 12, color=colour[v])
        draw_text(img, why[:40], 6, y + 24, color=(190, 190, 198, 255))
        for k, (tag, cells, dirs, per) in enumerate(
                [("A resize", rzc, a_dirs, a_per), ("B remake", rmc, b_dirs, b_per)]):
            ry = y + k * (tile + 18)
            draw_text(img, tag, 6, ry + 38, color=(210, 210, 216, 255))
            nums = " ".join(f"{d[:1]}{p[0]}/{p[1]:.0f}/{p[2]}"
                            for d, p in per.items() if p)
            draw_text(img, nums[:40], 6, ry + 50, color=(150, 150, 160, 255))
            sprite = blank_image(6, 6, (70, 70, 78, 255))
            for (x, cy), (role, step) in cells.items():
                if 0 <= x < 6 and 0 <= cy < 6:
                    sprite[cy][x] = pal.color(role, step)
            blit(img, nearest_scale(sprite, S), 300 + k * (iso + 8), ry)
            x = 300 + iso * 2 + 20
            for view in DIRS:
                t = [[p if p[3] else (112, 112, 120, 255) for p in r]
                     for r in dirs[view]]
                blit(img, nearest_scale(t, S), x, ry)
                x += tile + 6
        y += 2 * (tile + 18) + 12
    write_rgba_png(OUT, img)
    print(f"\n{len(rows)} pairs -> {OUT}")


if __name__ == "__main__":
    main()
