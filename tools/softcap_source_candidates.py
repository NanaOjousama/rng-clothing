"""Convert the soft-cap source sheet into candidates for the cap's four zones.

The locked policy decides the method, not taste:

    target at least 3x3      nearest-neighbour resize
    smaller, or one cell thin  native remake
    always                   the integration pass
    reject                   anything still pasted, speckled or foreign

Zones come from the cap's own geometry and are not widened here: front_panel
takes one emblem, top a button, side_panel a small tag, visor an edge accent.
Jewel and gemstone motifs are deliberately absent — those are held for a future
fantasy/festival tag rather than shipped as general-purpose cap emblems.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import authored                                              # noqa: E402
from v5.grammar import luminance                                     # noqa: E402
from v5.pngio import (blank_image, blit, draw_text, nearest_scale,    # noqa: E402
                      read_rgba_png, write_rgba_png)

SHEET = "motif/softcap_motif.png"
IM = read_rgba_png(SHEET)
S = 7
OUT = "output/v5_authored/softcap_source_candidates.png"
DIRS = ("front", "right", "left", "back")
CANON = {"casual": "EVERYDAY_STONE_BLUE", "work": "FIELD_CANVAS_MOSS",
         "smart": "WINTER_FROST_INK", "cottagecore": "SPRING_SAGE_PETAL"}


def ink(px):
    r, g, b = px[:3]
    if max(r, g, b) - min(r, g, b) > 6:
        return True
    return (r + g + b) // 3 < 190


# name, crop, zone, target size, role, class, method
CANDIDATES = [
    ("mountain",   (30, 30, 110, 100),   "front_panel", (4, 4), "accent", "emblem"),
    ("pine",       (125, 25, 205, 100),  "front_panel", (4, 4), "accent", "emblem"),
    ("bolt",       (230, 25, 295, 100),  "front_panel", (3, 4), "accent", "emblem"),
    ("anchor",     (320, 25, 400, 100),  "front_panel", (4, 4), "accent", "emblem"),
    ("star",       (550, 30, 625, 100),  "front_panel", (4, 4), "accent", "star"),
    ("heart",      (785, 125, 865, 195), "front_panel", (4, 4), "accent", "heart"),
    ("bear",       (25, 125, 110, 200),  "front_panel", (4, 4), "accent", "emblem"),
    ("cat",        (240, 125, 320, 200), "front_panel", (4, 4), "accent", "emblem"),
    ("circle_patch", (530, 250, 615, 335), "front_panel", (4, 4), "trim", "patch"),
    ("shield_patch", (895, 250, 980, 335), "front_panel", (4, 4), "trim", "patch"),
    ("letter_patch", (1010, 250, 1095, 335), "front_panel", (4, 4), "trim", "logo"),
]
# below 3x3, or one cell thin: redrawn at target size per the policy
REMAKES = [
    ("tag_small",  "side_panel", (3, 2), "trim", "tag", ["ddc", "cdc"]),
    ("pin_dot",    "side_panel", (2, 2), "hardware", "pin", ["DF", "CD"]),
    ("crown_btn",  "top", (2, 2), "hardware", "button", ["DF", "AC"]),
]
# The visor is 10 cells wide head-on and a 3-cell peak in profile, so an edge
# accent needs a per-view variant — the policy's "view-specific variants when
# needed", decided by the geometry rather than by preference.
VISOR = [
    ("visor_stitch", "stitch_accent", {"front": ["tttttttt"], "left": ["ttt"]}),
    ("visor_stripe", "stitch_accent", {"front": ["dddddddd"], "left": ["ddd"]}),
]
CHARS = {"body": "123456", "trim": "abcdef", "accent": "pqrstu", "hardware": "ABCDEF"}


def resize_nn(crop, w, h, role):
    x0, y0, x1, y1 = crop
    sw, sh = (x1 - x0) / w, (y1 - y0) / h
    picked = {}
    for cy in range(h):
        for cx in range(w):
            # sample a small neighbourhood's darkest inked pixel: pure point
            # sampling on line art misses strokes thinner than the step
            best = None
            for oy in (0.35, 0.5, 0.65):
                for ox in (0.35, 0.5, 0.65):
                    sx, sy = int(x0 + (cx + ox) * sw), int(y0 + (cy + oy) * sh)
                    px = IM[min(sy, len(IM) - 1)][min(sx, len(IM[0]) - 1)]
                    if ink(px) and (best is None or luminance(px) < luminance(best)):
                        best = px
            if best is not None:
                picked[(cx, cy)] = luminance(best)
    if not picked:
        return {}
    lo, hi = min(picked.values()), max(picked.values())
    span = max(1.0, hi - lo)
    return {c: (role, max(0, min(5, round((v - lo) / span * 5))))
            for c, v in picked.items()}


def art_cells(rows):
    out = {}
    for y, line in enumerate(rows):
        for x, ch in enumerate(line):
            if ch != ".":
                for role, cs in CHARS.items():
                    if ch in cs:
                        out[(x, y)] = (role, cs.index(ch))
    return out


def decal(name, cells, size, zone, kind, cls):
    return authored.Decal(name=name, slot="HEAD", attach="", z=3,
                          style=("casual", "work", "smart", "cottagecore"),
                          views=(("front",) if zone == "front_panel" else
                                 ("front", "left") if zone == "visor" else
                                 ("front", "left", "back")),
                          size=size, cells=cells, zone=zone, kind=kind,
                          motif_class=cls, edge=(zone == "visor"), pending=True,
                          max_extent=0, per_view=False, anchor_cell=(0, 0),
                          anchor_point="top_centre", fits=("soft_cap",))


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
    base = next(b for b in lib.bases if b.name == "soft_cap")
    tone = lib.tone_for(base)
    pal = next(p for p in lib.palettes if p.id == CANON["casual"])
    plain, _ = authored._render(base, [], pal, tone)

    rows = []
    for name, crop, zone, size, role, cls in CANDIDATES:
        cells = resize_nn(crop, size[0], size[1], role)
        d = decal(name, cells, size, zone, "surface", cls)
        dirs, dropped = authored._render(base, [d], pal, tone)
        rows.append((name, "resize", zone, cells, size, dirs, dropped))
    for name, zone, size, role, cls, art in REMAKES:
        cells = art_cells(art)
        d = decal(name, cells, size, zone, "surface", cls)
        dirs, dropped = authored._render(base, [d], pal, tone)
        rows.append((name, "remake", zone, cells, size, dirs, dropped))
    for name, cls, per_view in VISOR:
        cells = {v: art_cells(a) for v, a in per_view.items()}
        d = authored.Decal(name=name, slot="HEAD", attach="", z=3,
                           style=("casual", "work", "smart", "cottagecore"),
                           views=tuple(per_view), size=(8, 1), cells=cells,
                           zone="visor", kind="surface", motif_class=cls,
                           edge=True, pending=True, max_extent=0, per_view=True,
                           anchor_cell=(0, 0), anchor_point="top_centre",
                           fits=("soft_cap",))
        dirs, dropped = authored._render(base, [d], pal, tone)
        rows.append((name, "remake", "visor", cells["front"], (8, 1), dirs, dropped))

    scored = []
    for name, method, zone, cells, size, dirs, dropped in rows:
        per = {}
        for v in DIRS:
            a, b = plain[v], dirs[v]
            ch = {(x, y) for y in range(len(a)) for x in range(len(a[0]))
                  if tuple(a[y][x]) != tuple(b[y][x])}
            if not ch:
                per[v] = None
                continue
            dl = [abs(luminance(a[y][x]) - luminance(b[y][x]))
                  if a[y][x][3] and b[y][x][3] else 255.0 for (x, y) in ch]
            per[v] = (len(ch), sum(dl) / len(dl), fragments(ch))
        live = [p for p in per.values() if p]
        if dropped or not live:
            v, why = "REJECT", (dropped[0][2] if dropped else "renders nothing")
        elif max(p[2] for p in live) >= 3:
            v, why = "REJECT", f"{max(p[2] for p in live)} fragments — speckle"
        elif max(p[0] for p in live) < 4:
            v, why = "REJECT", f"only {max(p[0] for p in live)} cells read"
        else:
            v, why = "CANDIDATE", (f"{min(p[0] for p in live)}-{max(p[0] for p in live)} "
                                   f"cells, dL {min(p[1] for p in live):.0f}-"
                                   f"{max(p[1] for p in live):.0f}")
        scored.append((name, method, zone, cells, size, dirs, per, v, why))

    zorder = {"front_panel": 0, "side_panel": 1, "top": 2, "visor": 3}
    scored.sort(key=lambda r: (zorder[r[2]], r[7] != "CANDIDATE", r[0]))

    tile = 20 * S
    iso = 5 * S
    img = blank_image(300 + iso + 12 + len(DIRS) * (tile + 6) + 16,
                      46 + len(scored) * (tile + 14) + 4 * 22, (46, 46, 54, 255))
    draw_text(img, "SOFT_CAP CANDIDATES from the cap source sheet — by zone — "
                   "isolated | front / right / left / back", 8, 6,
              color=(240, 240, 244, 255))
    colour = {"CANDIDATE": (170, 235, 190, 255), "REJECT": (245, 160, 160, 255)}
    y = 26
    last_zone = None
    print(f"{'motif':14s} {'method':7s} {'zone':12s} {'verdict':10s} why")
    for name, method, zone, cells, size, dirs, per, v, why in scored:
        if zone != last_zone:
            draw_text(img, zone.upper().replace("_", " "), 8, y,
                      color=(255, 232, 170, 255))
            y += 20
            last_zone = zone
        draw_text(img, f"{name}", 8, y + 2, color=colour[v])
        draw_text(img, f"{v} · {method}", 8, y + 14, color=colour[v])
        draw_text(img, why[:40], 8, y + 26, color=(190, 190, 198, 255))
        sprite = blank_image(5, 5, (70, 70, 78, 255))
        for (x, cy), (role, step) in cells.items():
            if 0 <= x < 5 and 0 <= cy < 5:
                sprite[cy][x] = pal.color(role, step)
        blit(img, nearest_scale(sprite, S), 300, y)
        x = 300 + iso + 12
        for view in DIRS:
            t = [[p if p[3] else (112, 112, 120, 255) for p in r]
                 for r in dirs[view]]
            blit(img, nearest_scale(t, S), x, y)
            x += tile + 6
        y += tile + 14
        print(f"{name:14s} {method:7s} {zone:12s} {v:10s} {why}")
    write_rgba_png(OUT, img)
    print(f"\n{len(scored)} candidates -> {OUT}")


if __name__ == "__main__":
    main()
