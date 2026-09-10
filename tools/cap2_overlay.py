"""Render CAP2_FRONT_OVERLAY test marks on the intact Cap 2 base.

The base is never edited: a mark writes only into the bounded overlay cells,
and every other source pixel is passed through untouched. That is asserted
after rendering, not assumed.
"""
from __future__ import annotations

import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v5 import pngio
from v5.source import audit, pngread

BASE = "authored/source_bases/cap2"
DIRS = ["Front", "Right", "Left", "Back"]


def load():
    cat = json.load(open("source_catalog/catalog.json"))
    app = next(a for a in cat["appearances"]
               if a["name"] == "Cap 2" and a["pack"].startswith("More Acc"))
    px = pngread.read(app["png_path"])
    fr = {d: audit.cut(px, tuple(b)) for d, b in app["analysis"]["boxes"].items()}
    ov = json.load(open(f"{BASE}/front_overlay.json"))
    marks = json.load(open(f"{BASE}/overlay_marks.json"))["marks"]
    vocab = [tuple(c) for c in
             json.load(open(f"{BASE}/semantic_map.json"))["base"]["vocabulary"]]
    return app, fr, ov, marks, vocab


def apply_mark(fr, ov, marks, vocab, name, safe=None, step=1):
    """Draw a mark as EXPLICIT CELLS, refusing any cell outside the safe mask.

    The mask is authoritative: a rectangle cannot express that the crown's top
    corners are silhouette, which is how earlier marks ended up touching the
    outer edge.
    """
    out = {d: [list(r) for r in f] for d, f in fr.items()}
    touched = []
    if name:
        for c in marks[name]["cells"]:
            x, y = int(c[0]), int(c[1])
            if safe is not None and (x, y) not in safe:
                raise ValueError(f"{name}: cell {x},{y} is outside the safe mask")
            if fr["Front"][y][x][3] == 0:
                raise ValueError(f"{name}: cell {x},{y} is off the garment")
            out["Front"][y][x] = (*vocab[step], 255)
            touched.append((x, y))
    # nothing outside the overlay cells may change, in any direction
    for d, f in fr.items():
        for y in range(len(f)):
            for x in range(len(f[0])):
                if (d, x, y) != ("Front", x, y) or (x, y) not in touched:
                    if d != "Front" or (x, y) not in touched:
                        assert tuple(out[d][y][x]) == tuple(f[y][x]), \
                            f"{name}: altered {d} {x},{y} outside the overlay"
    return out, touched
