"""Pixel-level audit of the ingested source library.

Phase 1 recorded what the packs declare.  This reads what they actually draw:
every appearance's per-direction frames are cut out of its PNG using its own
StartingPosition/Size, and each frame is measured.

Two properties matter most for the pivot:

  recolour-readiness   Fashion Sense recolours by keying on declared
                       ColorMasks — greyscale ramp values the game tints at
                       draw time.  An appearance that declares masks (or is
                       simply drawn greyscale) can be recoloured without any
                       reinterpretation by us.  One that is drawn in fixed
                       colour cannot, and must be treated as fixed-palette.

  variant siblings     folders like Beret / BeretRibbon / BeretLeaf are the
                       same authored construction plus a decoration.  Their
                       pixel difference IS the decoration, exactly, with no
                       segmentation guesswork — which is what makes a later
                       reconstruction test pass by construction rather than by
                       approximation.
"""
from __future__ import annotations

import os
import re
from collections import Counter

import sys
sys.path.insert(0, "/run/media/deck/USD00/RNG_clothing")
from v5.source.pngread import read as read_rgba_png

SIZE_KEYS = ("HatSize", "ShirtSize", "PantsSize", "SleeveSize",
             "AccessorySize", "ShoesSize")


def frame_boxes(app: dict) -> dict:
    """{direction: (x, y, w, h)} from the appearance's own declarations."""
    out = {}
    for d, blk in (app.get("directions") or {}).items():
        size = next((blk[k] for k in SIZE_KEYS if blk.get(k)), None)
        pos = blk.get("StartingPosition") or {"X": 0, "Y": 0}
        if not size:
            continue
        out[d] = (int(pos.get("X", 0)), int(pos.get("Y", 0)),
                  int(size.get("Width", 0)), int(size.get("Length", 0)))
    return out


def cut(pixels, box):
    x0, y0, w, h = box
    return [[pixels[y][x] if 0 <= y < len(pixels) and 0 <= x < len(pixels[0])
             else (0, 0, 0, 0)
             for x in range(x0, x0 + w)] for y in range(y0, y0 + h)]


def is_grey(c):
    return c[0] == c[1] == c[2]


def measure(frame) -> dict:
    cells = [(x, y, tuple(p)) for y, r in enumerate(frame)
             for x, p in enumerate(r) if p[3] > 0]
    if not cells:
        return {"empty": True}
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    cols = Counter(c[2] for c in cells)
    greys = sum(n for c, n in cols.items() if is_grey(c))
    return {
        "empty": False,
        "cells": len(cells),
        "bbox": [min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1],
        "colours": len(cols),
        "grey_share": round(greys / len(cells), 3),
        "palette": [list(c) + [n] for c, n in cols.most_common(12)],
    }


def analyse(app: dict) -> dict:
    if not app.get("png_path") or not os.path.isfile(app["png_path"]):
        return {"error": "no png"}
    px = read_rgba_png(app["png_path"])
    boxes = frame_boxes(app)
    if not boxes:
        # undeclared layout: treat the whole sheet as one frame
        boxes = {"sheet": (0, 0, len(px[0]), len(px))}
    frames = {d: measure(cut(px, b)) for d, b in boxes.items()}
    drawn = [f for f in frames.values() if not f.get("empty")]
    allcols = Counter()
    for d, b in boxes.items():
        for row in cut(px, b):
            for p in row:
                if p[3] > 0:
                    allcols[tuple(p)] += 1
    grey = sum(n for c, n in allcols.items() if is_grey(c))
    masks = []
    for m in app.get("color_masks") or []:
        for _, v in m.items():
            for entry in (v or []):
                if isinstance(entry, list) and len(entry) >= 3:
                    masks.append(tuple(entry[:3]))
    return {
        "boxes": boxes,
        "frames": frames,
        "directions_drawn": sorted(d for d, f in frames.items()
                                   if not f.get("empty")),
        "total_cells": sum(f.get("cells", 0) for f in drawn),
        "total_colours": len(allcols),
        "grey_share": round(grey / sum(allcols.values()), 3) if allcols else 0.0,
        "declared_masks": sorted(set(masks)),
        "recolourable": bool(masks) or (
            sum(allcols.values()) and grey / sum(allcols.values()) > 0.85),
    }


def stem_of(name: str) -> str:
    """The authored construction name, with variant qualifiers removed.

    These packs use a display convention the folder names do not: the base
    construction, then its variant in parentheses -- "Blouse (Frill Trim)",
    "Beret (White Ribbon)", "Sun Hat (Flowers)".  Reading that convention
    groups families correctly; an earlier CamelCase splitter missed the whole
    Blouse family because the qualifier lives outside the parentheses only in
    the folder name, not the declared Name.
    """
    base = name.split("(")[0].strip()
    return re.sub(r"[^A-Za-z0-9]", "", base) or name


def qualifier_of(name: str) -> str:
    """What a variant adds, as the author named it: "" for the plain base."""
    m = re.search(r"\(([^)]*)\)", name)
    return m.group(1).strip() if m else ""
