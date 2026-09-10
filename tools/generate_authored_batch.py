"""Batch + contact sheet for the pre-authored path."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import authored
from v5.pngio import blank_image, blit, draw_text, nearest_scale, write_rgba_png

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "output", "v5_authored")
S = 4


def sheet(garments, cols=6, title=""):
    w, h = garments[0].base.size
    tw, th = (w * S) * 4 + 12, h * S
    rows = (len(garments) + cols - 1) // cols
    img = blank_image(cols * (tw + 10) + 10, rows * (th + 26) + 20, (58, 58, 64, 255))
    draw_text(img, title, 8, 4, color=(238, 238, 238, 255))
    for i, g in enumerate(garments):
        x = 10 + (i % cols) * (tw + 10)
        y = 18 + (i // cols) * (th + 26)
        tile = blank_image(tw, th, (112, 112, 120, 255))
        for j, d in enumerate(authored.ATLAS_ORDER):
            blit(tile, nearest_scale(g.directions[d], S), j * (w * S + 4), 0)
        blit(img, tile, x, y)
        draw_text(img, f"{g.style} {g.palette.id[:18]}", x, y + th + 2,
                  color=(206, 206, 210, 255))
    return img


def main(count=12):
    lib = authored.load()
    os.makedirs(OUT, exist_ok=True)
    report = []
    for slot, label in (("HEAD", "felt_hat"), ("TOP", "work_shirt")):
        gs = [authored.compose(s, slot, lib) for s in range(count)]
        write_rgba_png(os.path.join(OUT, f"{label}_sheet.png"),
                       sheet(gs, title=f"{label.upper()}  front / right / left / back"))
        for g in gs:
            authored.write(g, os.path.join(OUT, "pack"))
            report.append({"seed": g.seed, "slot": slot, "base": g.base.name,
                           "style": g.style, "palette": g.palette.id,
                           "decals": [d.name for d in g.decals],
                           "dropped": [list(d) for d in g.dropped]})
    with open(os.path.join(OUT, "report.json"), "w") as fh:
        json.dump(report, fh, indent=2)
    drops = sum(len(r["dropped"]) for r in report)
    print(f"{len(report)} garments, {drops} dropped decal cells -> {OUT}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 12)
