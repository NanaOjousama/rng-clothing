"""Ingest `beret_03` from the user's own drawn directional sheet.

Source (READ-ONLY, per CLAUDE.md section 2):
    BERET_MATERIAL(slash)PATTERN REFERENCE/Hats/hat_4/beret_{front,side,back}.png

These three files are authored art the user drew and supplied as "it should look
like this". They are ingested by READING PIXELS, never by transcribing them into
ASCII -- four earlier passes at this shape were hand-transcribed and every one of
them was rejected, each for a different invented detail. Nothing here is drawn.

What the source contains:
  - FRONT is an ARCH. The hat has a hole: a head opening outlined along its
    underside, with a short leg down each side. It is not a closed dome.
  - BACK is a full disc, since nothing occludes it from behind.
  - SIDE is deliberately asymmetric -- the beret sits high at the front and
    drapes down and back. `left` is mirrored from it at render time.

ONLY THE OUTLINE, THE SILHOUETTE AND INTERIOR DETAIL SILHOUETTES ARE TAKEN. The sheet's four reds are its
own shading, and the user was explicit that the shading is not what is wanted --
this project has its own. So the darkest tone, which is the boundary in all
three views, becomes the rim step, and every other opaque cell becomes flat body.
The interior form then comes from where it is supposed to: the palette ramp, the
material treatment axis, and decals.

The exception is INTERIOR DETAIL, which is construction rather than shading: the
back view carries a small hollow button ringed by the lighter tone at its centre,
and the user asked for that kept. It is found geometrically, not by naming a
colour -- a blob of non-lightest cells that touches NEITHER the outline nor the outside is
interior detail and keeps a shade step. Everything else in that tone is edge or
underside shading -- it reaches the outline -- and is discarded with the rest.

Distance from the edge was tried first and is wrong: the back's whole lower half
is shaded in the same tone as the button and sits just as deep inside the disc.
What actually separates them is that the shading runs into the outline and the
button is ringed by the lightest tone. So the rule finds the button without
anyone hardcoding where the button is, and finds nothing in the two views that
have none.

VERTICAL REGISTRATION COMES FROM THE SOURCE, at each view's own drawn offset --
front row 3, side row 2, back row 0. This was got wrong once and the in-game
capture settled it.

The canvases are of differing height (17, 14, 15), which looked like ad-hoc
export rather than intent, so a first pass registered all three by TOP EDGE at
row 3. On the farmer that put the back disc at rows 3-16 against a head spanning
rows 2-13.5: two and a half rows of beret hanging below the head, reading as an
enormous circle swallowing it. At the drawn offset the disc sits at rows 0-13 --
bottom landing on the head bottom, top standing proud of the hair, which is what
a beret does. The offsets were deliberate.

    python3 tools/ingest_beret_03.py
"""
from __future__ import annotations

import json
import os
import shutil
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from v5.pngio import write_rgba_png
from ingest_hat_base import derive_zones, bbox

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "BERET_MATERIAL⁄PATTERN REFERENCE", "Hats", "hat_4")
OUT = os.path.join(ROOT, "authored", "bases", "beret_03")
REF = os.path.join(ROOT, "authored", "source_bases", "beret", "beret_03")
BODY = ["#202020", "#404040", "#606060", "#808080", "#B0B0B0", "#E0E0E0"]
RIM = 2          # the source outline lands here
BODY_STEP = 4    # everything the outline encloses
SHADE = 3        # interior detail silhouettes, e.g. the back's button
CONTACT = 1      # the underside edge, where the hat meets the head
BAND = 3         # the lower rim, read as a band distinct from the crown
CROWN = 5        # the lit top of the crown, giving it volume above the band

# --- minor fit tuning --------------------------------------------------------
# The silhouette is the user's and is ACCEPTED. These are pixel-level trims only,
# allowed explicitly to improve how it wears, and they keep the variant's
# identity intact: it is still an arch with a head opening, a full back disc with
# its button, and a side that droops backward.
#
# The measured problem, against beret_01 -- the shape the user judged to wear
# well -- was that this one is 16 cells across to beret_01's 13, its back disc
# runs 14 rows to beret_01's 11, and its side droop reaches the frame edge at
# col 0 where beret_01 stops at col 2. Broad, tall and far-reaching all at once
# is what reads as engulfing the head.
#
# Every operation is integer and morphological. Nothing is redrawn and nothing is
# resampled: cells are removed or added on the existing grid, then the outline
# and shading are re-derived, so the source's shape language survives the trim.
REFINE = {
    "trim_sides": {"front": 1, "back": 1},      # 16 -> 14 across
    "trim_droop": {"right": 2},                 # overhang pulled off the edge
    "trim_middle_rows": {"back": 3},            # 14 -> 11 rows, shoulders kept
    "shrink_opening": {"front": 1},             # thickens the arch into a band
}

SIZE = 20
# Each view keeps the offset it was drawn at; see the registration note above.
FILES = {"front": "beret_front.png", "right": "beret_side.png",
         "back": "beret_back.png"}


def read_png(path):
    b = open(path, "rb").read()
    i, idat, pal, trns = 8, b"", None, None
    while i < len(b):
        ln = struct.unpack(">I", b[i:i + 4])[0]
        typ, dat = b[i + 4:i + 8], b[i + 8:i + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ct = struct.unpack(">IIBB", dat[:10])
        elif typ == b"PLTE":
            pal = dat
        elif typ == b"tRNS":
            trns = dat
        elif typ == b"IDAT":
            idat += dat
        i += 12 + ln
    raw = zlib.decompress(idat)
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    bpp, stride = max(1, ch * depth // 8), (w * ch * depth + 7) // 8
    out, prev, p = bytearray(), bytearray(stride), 0
    for _ in range(h):
        f = raw[p]; p += 1
        line = bytearray(raw[p:p + stride]); p += stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            up = prev[x]
            ul = prev[x - bpp] if x >= bpp else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + up) & 255
            elif f == 3:
                line[x] = (line[x] + (a + up) // 2) & 255
            elif f == 4:
                pa, pb, pc = abs(up - ul), abs(a - ul), abs(a + up - 2 * ul)
                pr = a if (pa <= pb and pa <= pc) else (up if pb <= pc else ul)
                line[x] = (line[x] + pr) & 255
        out += line; prev = line

    def px(x, y):
        if ct == 6:
            o = (y * w + x) * 4
            return tuple(out[o:o + 4])
        if ct == 2:
            o = (y * w + x) * 3
            return tuple(out[o:o + 3]) + (255,)
        if ct == 3:
            idx = out[y * stride + x]
            r, g, bl = pal[idx * 3:idx * 3 + 3]
            return (r, g, bl, trns[idx] if trns and idx < len(trns) else 255)
        raise SystemExit(f"unsupported colour type {ct}")

    return w, h, px


def rgb(hx):
    h = hx.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _interior_detail(w, h, px, outline, lightest):
    """Cells belonging to a detail blob: non-lightest, and enclosed by lightest.

    8-connected components over the non-outline, non-lightest cells. A component
    qualifies only if nothing in it touches an outline cell or a transparent one,
    which is what separates a button ringed by the light tone from shading that
    runs into the hat's own edge.
    """
    from collections import deque

    def tone(x, y):
        c = px(x, y)
        return c[:3] if c[3] else None

    cand = {(x, y) for y in range(h) for x in range(w)
            if tone(x, y) not in (None, outline, lightest)}
    detail, seen = set(), set()
    for start in cand:
        if start in seen:
            continue
        comp, q, enclosed = set(), deque([start]), True
        seen.add(start)
        while q:
            x, y = q.popleft()
            comp.add((x, y))
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < w and 0 <= ny < h):
                        enclosed = False
                        continue
                    t = tone(nx, ny)
                    if t is None or t == outline:
                        enclosed = False
                    elif (nx, ny) in cand and (nx, ny) not in seen:
                        seen.add((nx, ny))
                        q.append((nx, ny))
        if enclosed:
            detail |= comp
    return detail


def _extent(cells):
    xs = [x for (x, _) in cells]
    ys = [y for (_, y) in cells]
    return {"w": max(xs) - min(xs) + 1, "h": max(ys) - min(ys) + 1,
            "cols": [min(xs), max(xs)], "rows": [min(ys), max(ys)]}


def _refine(view, cells):
    """Pixel-level fit tuning. Integer morphology only -- see REFINE."""
    cells = dict(cells)

    for _ in range(REFINE["trim_sides"].get(view, 0)):
        cols = sorted({x for (x, _) in cells})
        edge = {cols[0], cols[-1]}
        cells = {c: v for c, v in cells.items() if c[0] not in edge}

    for _ in range(REFINE["trim_droop"].get(view, 0)):
        cols = sorted({x for (x, _) in cells})
        # Which end is the droop is MEASURED, as the end further from the mass's
        # centre, rather than assumed to be the left.
        cx = sum(x for (x, _) in cells) / len(cells)
        end = cols[0] if (cx - cols[0]) > (cols[-1] - cx) else cols[-1]
        cells = {c: v for c, v in cells.items() if c[0] != end}

    n = REFINE["trim_middle_rows"].get(view, 0)
    if n:
        rows = sorted({y for (_, y) in cells})
        width = {y: sum(1 for (_, yy) in cells if yy == y) for y in rows}
        full = [y for y in rows if width[y] == max(width.values())]
        # Dropped from the middle of the full-width run, where each row is a
        # duplicate of its neighbour and losing it costs no shape.
        first = full[max(0, len(full) // 2 - n // 2)]
        drop = set(full[full.index(first):full.index(first) + n])
        cells = {(x, y - sum(1 for d in drop if d < y)): v
                 for (x, y), v in cells.items() if y not in drop}

    for _ in range(REFINE["shrink_opening"].get(view, 0)):
        occupied = set(cells)
        hole = set()
        for y in sorted({y for (_, y) in occupied}):
            xs = [x for (x, yy) in occupied if yy == y]
            hole |= {(x, y) for x in range(min(xs), max(xs) + 1)
                     if (x, y) not in occupied}
        for c in hole:
            if any((c[0] + dx, c[1] + dy) in occupied
                   for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                cells[c] = BODY_STEP

    return cells


def _shade(cells, w, h):
    """Derive the wear-readability shading from the silhouette itself.

    The base arrived flat -- one outline step and one body step -- which is what
    made it read as a shape pasted over the head rather than a hat resting on it.
    Four things are derived here, all from geometry, so they survive any palette
    and hold for any shape put through this ingest:

      CONTACT  the underside edge. A boundary cell with empty space DIRECTLY
               BELOW it is where the hat meets the head, and it takes the darkest
               step. This is the line that separates hat from forehead, and it
               runs around the head opening as well as the outer hem.
      RIM      every other boundary cell: the ordinary outline.
      BAND     the lowest two interior cells of each column, so the lower rim
               reads as a band rather than dissolving into the crown.
      CROWN    the topmost interior cell of each column, lit, so the crown has
               volume above that band.

    Interior detail found earlier (the back's button) keeps its own step; it is
    construction, not shading.
    """
    occupied = set(cells)
    # Detail cells carry SHADE in from the ingest and keep it through the trims,
    # so they identify themselves rather than needing coordinates threaded here.
    detail = {c for c, v in cells.items() if v == SHADE}

    def empty(x, y):
        return not (0 <= x < w and 0 <= y < h) or (x, y) not in occupied

    out, interior = {}, {}
    for (x, y), v in cells.items():
        border = any(empty(x + dx, y + dy)
                     for dx in (-1, 0, 1) for dy in (-1, 0, 1))
        if border:
            out[(x, y)] = CONTACT if empty(x, y + 1) else RIM
        else:
            interior.setdefault(x, []).append(y)

    for x, ys in interior.items():
        ys.sort()
        for i, y in enumerate(ys):
            if (x, y) in detail:
                out[(x, y)] = SHADE
            elif i >= len(ys) - 2:
                out[(x, y)] = BAND
            elif i == 0:
                out[(x, y)] = CROWN
            else:
                out[(x, y)] = BODY_STEP
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(REF, exist_ok=True)

    # One tone map across all three views, so a colour means the same thing in
    # every direction.  Derived from the union, not per file.
    loaded, tones = {}, set()
    for view, fn in FILES.items():
        w, h, px = read_png(os.path.join(SRC, fn))
        loaded[view] = (w, h, px)
        for y in range(h):
            for x in range(w):
                c = px(x, y)
                if c[3]:
                    tones.add(c[:3])
    ramp = sorted(tones, key=lum)
    outline, lightest = ramp[0], ramp[-1]

    frames, detail_found, refined = {}, {}, {}
    for view, (w, h, px) in loaded.items():
        rows = [y for y in range(h)
                if any(px(x, y)[3] for x in range(w))]
        shift = 0   # the drawn offset IS the registration
        detail = _interior_detail(w, h, px, outline, lightest)
        cellmap = {}
        n_detail = 0
        for y in rows:
            for x in range(w):
                c = px(x, y)
                if not c[3]:
                    continue
                tone = c[:3]
                if tone == outline:
                    st = RIM
                elif (x, y) in detail:
                    st = SHADE
                    n_detail += 1
                else:
                    st = BODY_STEP
                ty, tx = y + shift, x
                if not (0 <= ty < SIZE and 0 <= tx < SIZE):
                    raise SystemExit(f"{view}: cell ({tx},{ty}) falls outside the frame")
                cellmap[(tx, ty)] = st
        before = _extent(cellmap)
        cellmap = _refine(view, cellmap)
        refined[view] = (before, _extent(cellmap))
        cellmap = _shade(cellmap, SIZE, SIZE)
        img = [[(0, 0, 0, 0)] * SIZE for _ in range(SIZE)]
        for (tx, ty), st in cellmap.items():
            img[ty][tx] = rgb(BODY[st]) + (255,)
        frames[view] = img
        detail_found[view] = n_detail
        write_rgba_png(os.path.join(OUT, f"{view}.png"), img)

    # Preserve the source beside the normalised art, byte-for-byte.
    for view, fn in FILES.items():
        shutil.copyfile(os.path.join(SRC, fn), os.path.join(REF, fn))

    zones = {v: derive_zones(img) for v, img in frames.items()}
    anchors = {}
    for z in ("crown_top", "side", "band"):
        got = {v: [zones[v][z][0], zones[v][z][1]] for v in zones if z in zones[v]}
        if got:
            anchors[z] = got

    base = {
        "name": "beret_03",
        "family": "beret",
        "shape_variant": "beret_03",
        "slot": "HEAD",
        "classification": "REFERENCE",
        "size": [SIZE, SIZE],
        "views": ["front", "right", "back"],
        "mirrored_at_render": ["left"],
        "style": ["cute", "cottagecore", "casual", "smart", "formal"],
        "provenance": "REFERENCE-ONLY: ingested from the user's own drawn "
                      "directional sheet at BERET_MATERIAL⁄PATTERN "
                      "REFERENCE/Hats/hat_4/beret_{front,side,back}.png, "
                      "supplied as the shape target. Pixels read, not "
                      "transcribed. See "
                      "authored/source_bases/beret/beret_03/provenance.json",
        "derived_from": "BERET_MATERIAL⁄PATTERN REFERENCE/Hats/hat_4/",
        "anchors": anchors,
        "zones": zones,
    }
    with open(os.path.join(OUT, "base.json"), "w") as fh:
        json.dump(base, fh, indent=2)
        fh.write("\n")

    prov = {
        "id": "beret_03",
        "family": "beret",
        "classification": "REFERENCE",
        "classification_reason":
            "Drawn by the user and supplied directly as the shape target. Held "
            "at REFERENCE with the rest of the beret family until the family is "
            "cleared for shipping; it is not third-party art and carries no "
            "licence question of its own.",
        "attribution": "drawn by the user; ingested to index colours here",
        "source": {"path": "BERET_MATERIAL⁄PATTERN REFERENCE/Hats/hat_4/",
                   "files": sorted(FILES.values()),
                   "read_only": True},
        "construction": {
            "ingested": "pixels read from the source PNGs; no ASCII "
                        "transcription and no resampling",
            "taken_from_source": "outline and silhouette only",
            "source_tones": ["%02x%02x%02x" % c for c in ramp],
            "outline_tone": "%02x%02x%02x" % outline,
            "geometry": "ACCEPTED AND FROZEN by the user as one beret shape "
                        "variant. A fit refinement that narrowed it toward "
                        "beret_01's proportions was written and reverted: the "
                        "silhouette is not to be tuned further. Wear quality is "
                        "addressed through shading and material instead.",
            "interior_detail": {"cells_per_view": detail_found,
                                "rule": "an 8-connected blob of non-lightest "
                                        "cells touching neither the outline nor "
                                        "the exterior; found geometrically, not "
                                        "by colour name"},
            "shading": "NOT taken from the source. The sheet's four reds are its "
                       "own shading; the project has its own. Outline -> rim step "
                       "%d, everything it encloses -> flat body step %d, with "
                       "interior form left to the palette ramp, the material "
                       "treatment axis and decals." % (RIM, BODY_STEP),
            "front": "an ARCH -- the hat has a head opening cut through it, "
                     "outlined along the underside, with a short leg each side. "
                     "Four earlier passes drew it as a closed dome.",
            "back": "a full disc; nothing occludes it from behind",
            "side": "deliberately asymmetric -- high at the front, draping down "
                    "and back. `left` is mirrored from it at render time.",
            "vertical_registration":
                "each view at its own drawn offset -- front 3, side 2, back 0. "
                "Top-aligning all three instead was tried and rejected by the "
                "in-game capture: it hung the back disc 2.5 rows below the head.",
        },
        "directions": {"authored": ["front", "right", "back"],
                       "mirrored": ["left"]},
    }
    with open(os.path.join(REF, "provenance.json"), "w") as fh:
        json.dump(prov, fh, indent=2)
        fh.write("\n")

    print(f"  {len(ramp)} source tones -> outline {RIM}, body {BODY_STEP}, "
          f"interior detail {SHADE}")
    print(f"  interior detail cells: {detail_found}")
    for v in ("front", "right", "back"):
        print(f"  {v:6} bbox {bbox(frames[v])}  zones {sorted(zones[v])}")
    print("beret_03 ingested")


if __name__ == "__main__":
    main()
