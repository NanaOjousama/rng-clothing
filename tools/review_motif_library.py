"""Score every motif for readability and group the library KEEP / REWORK / REJECT.

A motif earns its place by CHANGING the hat legibly.  Three numbers, measured
against the same base and palette without it:

    changed   how many rendered cells differ from the plain hat
    mean dL   how far they differ in luminance
    fragments how many disconnected pieces those cells form

Fragmentation is the one that catches noise: a motif that reads as three
scattered specks is the failure mode the in-game pass found for side_pin, and
it is invisible to a size-or-contrast check alone.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import authored                                              # noqa: E402
from v5.grammar import luminance                                     # noqa: E402
from v5.pngio import (blank_image, blit, draw_text, nearest_scale,    # noqa: E402
                      write_rgba_png)

S = 7
OUT = "output/v5_authored/motif_library_review.png"

KEEP_CHANGED, KEEP_DL, KEEP_FRAG = 6, 32.0, 2
REJECT_CHANGED, REJECT_DL, REJECT_FRAG = 4, 22.0, 3


def fragments(cells):
    seen, groups = set(), 0
    for c in cells:
        if c in seen:
            continue
        groups += 1
        stack = [c]
        while stack:
            x, y = stack.pop()
            if (x, y) in seen:
                continue
            seen.add((x, y))
            stack += [(x + dx, y + dy)
                      for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                      if (x + dx, y + dy) in cells and (x + dx, y + dy) not in seen]
    return groups


def score(lib, base, palette, style, motif):
    plain = authored.build(base.name, palette, [], lib, style=style)
    dressed = authored.build(base.name, palette, [motif.name], lib, style=style)
    best = None
    for view in ("front", "left"):
        a, b = plain.directions[view], dressed.directions[view]
        changed = {(x, y) for y in range(len(a)) for x in range(len(a[0]))
                   if tuple(a[y][x]) != tuple(b[y][x])}
        if not changed:
            continue
        dl = [abs(luminance(a[y][x]) - luminance(b[y][x])) if a[y][x][3] and b[y][x][3]
              else 255.0 for (x, y) in changed]
        row = (len(changed), sum(dl) / len(dl), fragments(changed), view)
        if best is None or row[0] > best[0]:
            best = row
    return best


# A deliberate POINT ACCENT is one cell by design — a button, a rivet.  The
# in-game pass read crown_button clearly on both caps, so a size threshold
# alone would throw away a motif the game says works.  It still has to be
# loud: one cell earns its place only at high contrast.
POINT_ACCENT_DL = 120.0


def verdict(row):
    if row is None:
        return "REJECT"
    n, dl, frag, _ = row
    if n <= 2 and dl >= POINT_ACCENT_DL and frag == 1:
        return "KEEP"
    if n < REJECT_CHANGED or dl < REJECT_DL or frag >= REJECT_FRAG:
        return "REJECT"
    if n >= KEEP_CHANGED and dl >= KEEP_DL and frag <= KEEP_FRAG:
        return "KEEP"
    return "REWORK"


def main():
    lib = authored.load()
    pal = {p.id: p for p in lib.palettes}
    rows = []
    for d in sorted(lib.decals, key=lambda d: d.name):
        if d.slot != "HEAD":
            continue
        base = next((b for b in lib.bases if b.slot == "HEAD" and d.fits_base(b)
                     and set(b.style) & set(d.style)
                     and any(authored._placement(b, d, v) for v in d.views)), None)
        if base is None:
            rows.append((d, None, None, None, "REJECT", "no legal base"))
            continue
        style = sorted(set(base.style) & set(d.style))[0]
        palette = next((p.id for p in lib.palettes if style in p.style), None)
        row = score(lib, base, palette, style, d)
        g = authored.build(base.name, palette, [d.name], lib, style=style)
        rows.append((d, base, palette, style, verdict(row), row, g))

    order = {"KEEP": 0, "REWORK": 1, "REJECT": 2}
    rows.sort(key=lambda r: (order[r[4]], r[0].name))

    # A grid, not a list: thirty motifs stacked one per line is 4000px tall and
    # nobody compares the top of that against the bottom.
    COLS, LABEL = 5, 26
    tile_w, tile_h = 20 * S * 2 + 6, 20 * S
    groups = {}
    for entry in rows:
        groups.setdefault(entry[4], []).append(entry)
    height = 34
    for v, items in groups.items():
        height += 22 + ((len(items) + COLS - 1) // COLS) * (tile_h + LABEL + 8)
    img = blank_image(COLS * (tile_w + 10) + 10, height, (46, 46, 54, 255))
    draw_text(img, "MOTIF LIBRARY REVIEW — front / left per tile — "
                   "changed cells, mean dL, fragments", 8, 6, color=(240, 240, 244, 255))
    colour = {"KEEP": (170, 235, 190, 255), "REWORK": (245, 220, 150, 255),
              "REJECT": (245, 160, 160, 255)}
    print(f"{'motif':17s} {'verdict':8s} {'kind':11s} {'zone':11s} "
          f"{'chg':>4s} {'dL':>6s} {'frg':>4s}  base")
    y = 26
    for v in ("KEEP", "REWORK", "REJECT"):
        items = groups.get(v, [])
        if not items:
            continue
        draw_text(img, f"{v}  ({len(items)})", 8, y, color=colour[v])
        y += 20
        for i, entry in enumerate(items):
            d, base, palette, style, verd, row = entry[:6]
            g = entry[6] if len(entry) > 6 else None
            n, dl, frag = (row[0], row[1], row[2]) if row else (0, 0, 0)
            print(f"{d.name:17s} {verd:8s} {d.kind:11s} {str(d.zone):11s} "
                  f"{n:4d} {dl:6.0f} {frag:4d}  {base.name if base else '-'}")
            cx = 10 + (i % COLS) * (tile_w + 10)
            cy = y + (i // COLS) * (tile_h + LABEL + 8)
            if g:
                x = cx
                for view in ("front", "left"):
                    tile = [[p if p[3] else (112, 112, 120, 255) for p in r]
                            for r in g.directions[view]]
                    blit(img, nearest_scale(tile, S), x, cy)
                    x += 20 * S + 6
            draw_text(img, d.name[:24], cx, cy + tile_h + 3, color=colour[v])
            draw_text(img, f"{d.kind[:4]}/{d.zone}  {n}c dL{dl:.0f} f{frag}",
                      cx, cy + tile_h + 14, color=(186, 186, 196, 255))
        y += ((len(items) + COLS - 1) // COLS) * (tile_h + LABEL + 8) + 6
    write_rgba_png(OUT, img)
    print(f"\n{len(rows)} motifs -> {OUT}")


if __name__ == "__main__":
    main()
