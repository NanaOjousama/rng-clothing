"""Check every motif against a base's locked compatibility policy.

Four ways a motif can fail, and they are different failures:

    BANNED        its CLASS is banned on this base (a hat band on a cap)
    NO ZONE       the base has no such region at all — banned by geometry
    WRONG ZONE    the region exists but does not carry this class of thing
    REWORK        legal, but does not read at gameplay scale once integrated

Anything left is LEGAL.  The point of separating them is that only the last is
an art problem; the others are policy, and policy is cheaper to fix.
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

BASE = "soft_cap"
S = 7
OUT = "output/v5_authored/softcap_compatibility.png"
DIRS = ("front", "right", "left", "back")
CANON = {"casual": "EVERYDAY_STONE_BLUE", "work": "FIELD_CANVAS_MOSS",
         "cottagecore": "SPRING_SAGE_PETAL", "smart": "WINTER_FROST_INK"}


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


def main():
    lib = authored.load()
    base = next(b for b in lib.bases if b.name == BASE)
    policy = json.load(open("authored/policy.json"))["bases"][BASE]
    zones = policy["zones"]
    banned = set(policy["banned_classes"])
    have = {z for v in base.zones.values() for z in v}

    rows = []
    for d in sorted(lib.decals, key=lambda x: x.name):
        if d.slot != "HEAD":
            continue
        cls = getattr(d, "motif_class", None) or "?"
        if cls in banned:
            rows.append((d, cls, "BANNED", f"class '{cls}' is banned on this base", None))
            continue
        if d.zone not in have:
            rows.append((d, cls, "NO ZONE",
                         f"a cap has no '{d.zone}' region", None))
            continue
        allowed = zones.get(d.zone, {}).get("classes", [])
        if cls not in allowed:
            rows.append((d, cls, "WRONG ZONE",
                         f"'{d.zone}' carries {'/'.join(allowed[:3])}…, not '{cls}'", None))
            continue
        shared = sorted(set(base.style) & set(d.style))
        if not shared or not any(authored._placement(base, d, v) for v in d.views):
            rows.append((d, cls, "NO ZONE", "no legal placement or style on this base", None))
            continue
        style = shared[0]
        pal = CANON[style]
        plain = authored.build(BASE, pal, [], lib, style=style)
        worn = authored.build(BASE, pal, [d.name], lib, style=style)
        per = {}
        for v in DIRS:
            a, b = plain.directions[v], worn.directions[v]
            ch = {(x, y) for y in range(len(a)) for x in range(len(a[0]))
                  if tuple(a[y][x]) != tuple(b[y][x])}
            if not ch:
                per[v] = None
                continue
            dl = [abs(luminance(a[y][x]) - luminance(b[y][x]))
                  if a[y][x][3] and b[y][x][3] else 255.0 for (x, y) in ch]
            per[v] = (len(ch), sum(dl) / len(dl), fragments(ch))
        live = [p for p in per.values() if p]
        rim = rim_cells(set(base.cells["front"]))
        if not live:
            rows.append((d, cls, "REWORK", "renders nothing", (worn, per)))
        elif max(p[2] for p in live) >= 3:
            rows.append((d, cls, "REWORK",
                         f"{max(p[2] for p in live)} fragments", (worn, per)))
        elif max(p[0] for p in live) < 4:
            rows.append((d, cls, "REWORK",
                         f"only {max(p[0] for p in live)} cells read", (worn, per)))
        else:
            rows.append((d, cls, "LEGAL",
                         f"{min(p[0] for p in live)}-{max(p[0] for p in live)} cells, "
                         f"dL {min(p[1] for p in live):.0f}-{max(p[1] for p in live):.0f}",
                         (worn, per)))

    order = {"LEGAL": 0, "REWORK": 1, "WRONG ZONE": 2, "NO ZONE": 3, "BANNED": 4}
    rows.sort(key=lambda r: (order[r[2]], r[0].zone or "", r[0].name))

    print(f"{'motif':18s} {'class':15s} {'zone':12s} {'verdict':11s} why")
    for d, cls, v, why, _ in rows:
        print(f"{d.name:18s} {cls:15s} {str(d.zone):12s} {v:11s} {why}")

    shown = [r for r in rows if r[4]]
    tile = 20 * S
    img = blank_image(330 + len(DIRS) * (tile + 6) + 20,
                      44 + len(shown) * (tile + 16) + 30 * (len(rows) - len(shown)) + 40,
                      (46, 46, 54, 255))
    draw_text(img, f"SOFT_CAP COMPATIBILITY — policy-checked — front / right / left / back",
              8, 6, color=(240, 240, 244, 255))
    colour = {"LEGAL": (170, 235, 190, 255), "REWORK": (245, 220, 150, 255),
              "WRONG ZONE": (220, 180, 240, 255), "NO ZONE": (170, 180, 200, 255),
              "BANNED": (245, 160, 160, 255)}
    y = 28
    for d, cls, v, why, shown_data in rows:
        if shown_data:
            worn, per = shown_data
            draw_text(img, d.name[:24], 6, y + 2, color=colour[v])
            draw_text(img, f"{v} · {cls} · {d.zone}", 6, y + 14, color=colour[v])
            draw_text(img, why[:40], 6, y + 26, color=(190, 190, 198, 255))
            nums = " ".join(f"{k[:1]}{p[0]}/{p[1]:.0f}/{p[2]}"
                            for k, p in per.items() if p)
            draw_text(img, nums[:40], 6, y + 38, color=(150, 150, 160, 255))
            x = 330
            for view in DIRS:
                t = [[p if p[3] else (112, 112, 120, 255) for p in r]
                     for r in worn.directions[view]]
                blit(img, nearest_scale(t, S), x, y)
                x += tile + 6
            y += tile + 16
        else:
            draw_text(img, f"{d.name}", 6, y, color=colour[v])
            draw_text(img, f"{v} — {why}"[:70], 190, y, color=(160, 160, 172, 255))
            y += 22
    write_rgba_png(OUT, img)
    print(f"\n{len(rows)} motifs checked -> {OUT}")


if __name__ == "__main__":
    main()
