"""Offline comparison: one base, several legal decoration combinations.

The point is to see whether decoration changes a hat's PERSONALITY without
costing readability, so each row is the same base and palette with a different
legal combination, and each block is the same combinations under a different
palette.  Anything illegal — wrong base, wrong style, wrong zone — cannot
appear here, because the combinations are built through the same rules the
combinator uses.
"""
from __future__ import annotations

import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import authored                                              # noqa: E402
from v5.pngio import (blank_image, blit, draw_text, nearest_scale,    # noqa: E402
                      write_rgba_png)

S = 6
OUT = "output/v5_authored/decoration_matrix.png"
PLAN = [
    ("felt_hat", ["WORKWEAR_DENIM_RUST", "GOTHIC_WINE_ASH"]),
    ("wide_brim_hat", ["FIELD_CANVAS_MOSS", "AUTUMN_OCHRE_PLUM"]),
    ("soft_cap", ["EVERYDAY_STONE_BLUE", "SPRING_SAGE_PETAL"]),
    ("knit_cap", ["COASTAL_SEAFOAM_CORAL", "AUTUMN_OCHRE_PLUM"]),
]


def flat(rows, bg=(112, 112, 120, 255)):
    return [[p if p[3] else bg for p in r] for r in rows]


def legal_combos(lib, base, style, limit=5):
    """Up to `limit` legal decoration sets: none, each single, then pairs."""
    usable = [d for d in lib.decals
              if d.slot == base.slot and d.fits_base(base) and style in d.style
              and any(authored._placement(base, d, v) for v in d.views)]
    usable.sort(key=lambda d: d.name)
    combos = [()]
    combos += [(d,) for d in usable]
    for a, b in itertools.combinations(usable, 2):
        if (a.zone or a.attach) != (b.zone or b.attach):
            combos.append((a, b))
    return combos[:limit]


def main():
    lib = authored.load()
    pal = {p.id: p for p in lib.palettes}
    rows = []
    for base_name, palettes in PLAN:
        base = next(b for b in lib.bases if b.name == base_name)
        for pid in palettes:
            style = next((s for s in base.style if s in pal[pid].style), None)
            if style is None:
                continue
            for combo in legal_combos(lib, base, style):
                g = authored.build(base_name, pid, [d.name for d in combo], lib,
                                   style=style)
                label = " + ".join(d.name for d in combo) or "(plain base)"
                rows.append((f"{base_name} · {pid[:14]}", label,
                             [flat(g.directions[d]) for d in
                              ("front", "right", "left", "back")],
                             bool(g.dropped)))
    tw, th = 20 * S * 4 + 18, 20 * S
    img = blank_image(330 + tw + 16, 26 + len(rows) * (th + 8), (46, 46, 54, 255))
    draw_text(img, "DECORATION MATRIX — legal combinations only — front / right / left / back",
              8, 6, color=(240, 240, 244, 255))
    y = 24
    last = None
    for group, label, tiles, bad in rows:
        if group != last:
            draw_text(img, group[:40], 6, y + 2, color=(255, 232, 170, 255))
            last = group
        draw_text(img, label[:38], 14, y + th // 2 + 2,
                  color=(255, 150, 150, 255) if bad else (222, 222, 228, 255))
        x = 330
        for t in tiles:
            blit(img, nearest_scale(t, S), x, y)
            x += 20 * S + 6
        y += th + 8
    write_rgba_png(OUT, img)
    print(f"{len(rows)} combinations -> {OUT}")


if __name__ == "__main__":
    main()
