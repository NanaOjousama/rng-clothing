"""Ingest a Fashion Sense hat sheet as an authored base in a garment family.

Generic: every shape is a row in SPECS below and goes through one code path.
Nothing here knows what a beret is.

Two things happen to a source sheet and exactly two:

  1. its AUTHORED direction views are carried through unchanged -- no mirroring,
     no synthesis. A sheet that authors only one profile view says so, and the
     engine mirrors the other at render time, which is the Fashion Sense
     `Flipped` convention rather than an invention.
  2. its grey ramp is normalised onto the authoring index's six semantic `body`
     steps, because the engine requires every pixel to decode to a (role, step)
     pair. Two policies, chosen per source:
       equal_width  -- for a noisy ramp that is conversion artefact, not design
       rank         -- for a small clean ramp an artist actually chose, where
                       equal-width bucketing would collide two levels into one

The normalisation changes SHADING only: alpha, silhouette, bounding boxes and
the per-direction layout are asserted identical to the source before anything is
written.

Nothing is destructive. Sources are opened read-only and a byte-identical copy of
each is preserved beside its provenance record, so normalised art never becomes
the only surviving version.

    python3 tools/ingest_hat_base.py            # every shape
    python3 tools/ingest_hat_base.py beret_02   # one shape
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5.pngio import read_rgba_png, write_rgba_png

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BODY = ["#202020", "#404040", "#606060", "#808080", "#B0B0B0", "#E0E0E0"]
STEPS = 6
# Two greys this close apart are the same level; see `stepper`.
NEAR = 2

# Fashion Sense stacking; a sheet declares only the frames it actually authors.
FOUR = [("front", 0), ("right", 20), ("left", 40), ("back", 60)]
THREE = [("front", 0), ("right", 20), ("back", 40)]

SPECS = {
    "beret_01": {
        "family": "beret",
        "source": "beret_variant1/hat.png",
        "source_json": "beret_variant1/hat.json",
        "internal_name": "hyoung_hats_24",
        "layout": FOUR,
        "mirrored": [],
        "normalise": "equal_width",
        "style": ["casual", "cottagecore", "smart", "formal"],
        "classification": "REFERENCE",
        "classification_reason":
            "Byte-identical to hyoung_hats_24 in the third-party pack "
            "'[FS] h young's hats' (author: h young, FS code by Mychocolate, "
            "v1.0.0), which declares no licence. Usable for architecture, "
            "conversion and testing; not a shippable production asset.",
        "attribution": "h young — [FS] h young's hats (hyoung_hats.fs), hat 24",
    },
    "beret_02": {
        "family": "beret",
        "source": "generator content/[FS] Cottagecore Set/Hats/Beret/hat.png",
        "source_json": "generator content/[FS] Cottagecore Set/Hats/Beret/hat.json",
        "internal_name": "Cottagecore Set / Beret",
        "layout": THREE,
        # The source's LeftHat reuses the Right StartingPosition with
        # "Flipped": true, so there is no authored left frame to carry through.
        "mirrored": ["left"],
        "normalise": "rank",
        "style": ["cottagecore", "casual", "smart", "formal"],
        "classification": "REFERENCE",
        "classification_reason":
            "Approved source pack (Cottagecore Set, plurffle, "
            "SmolHooman.CottagecoreSet) and composable per tools/catalog.py, so "
            "its standing is materially better than beret_01's. Held at "
            "REFERENCE only until the family as a whole is cleared for shipping.",
        "attribution": "plurffle — [FS] Cottagecore Set (SmolHooman.CottagecoreSet), Beret",
    },
}


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def rgb(hx):
    h = hx.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def frames(sheet, layout, frame_height=20):
    return {name: [row[:] for row in sheet[y:y + frame_height]] for name, y in layout}


def bbox(f):
    height = len(f)
    width = len(f[0]) if height else 0
    xs = [x for y in range(height) for x in range(width) if f[y][x][3]]
    ys = [y for y in range(height) for x in range(width) if f[y][x][3]]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def solid_rect(f, ya, yb):
    """Largest all-opaque rectangle inside rows ya..yb.

    A zone derived as a bounding box is wrong on this art: the beret's lower
    rows are sparse, so the box spans holes and a motif centred in it lands off
    the hat.  Requiring the rectangle to be solid means anything that fits its
    zone is guaranteed to sit on the base.
    """
    best = None
    width = len(f[0]) if f else 0
    heights = [0] * width
    for y in range(ya, yb + 1):
        for x in range(width):
            heights[x] = heights[x] + 1 if f[y][x][3] else 0
        stack = []
        for x in range(width + 1):
            h = heights[x] if x < width else 0
            start = x
            while stack and stack[-1][1] >= h:
                sx, sh = stack.pop()
                area = sh * (x - sx)
                if sh and (best is None or area > best[0]):
                    best = (area, sx, y - sh + 1, x - 1, y)
                start = sx
            stack.append((start, h))
    return list(best[1:]) if best else None


def derive_zones(f):
    """Legal decoration boxes, measured off this view's own silhouette.

    A zone is where a piece MAY go; the placement rules still decide whether a
    given piece fits.  Deriving them from the art rather than typing them in by
    eye is what keeps them true when a second beret shape is ingested.

    Surface zones (crown_top, crown_face, band) are solid rectangles, so a motif
    that fits its zone cannot fall off the hat.  `side` is different on purpose:
    it is where an attachment hangs off the edge, so it is taken from the crown's
    outer boundary and is allowed to extend past the silhouette.
    """
    box = bbox(f)
    if box is None:
        return {}
    x0, y0, x1, y1 = box
    h = y1 - y0 + 1
    crown_end = y0 + max(1, round(h * 0.5)) - 1
    zones = {}
    top = solid_rect(f, y0, min(y0 + 1, y1))
    if top:
        zones["crown_top"] = top
    face = solid_rect(f, y0, crown_end)
    if face:
        zones["crown_face"] = face
    if crown_end < y1:
        band = solid_rect(f, crown_end + 1, y1)
        if band:
            zones["band"] = band
    width = len(f[0]) if f else 0
    rows = {y: [x for x in range(width) if f[y][x][3]] for y in range(y0, y1 + 1)}
    wide = max(range(y0, crown_end + 1), key=lambda y: len(rows.get(y, [])))
    wx = rows.get(wide, [])
    if wx:
        zones["side"] = [max(wx) - 3, y0 + 1, max(wx), min(crown_end + 1, y1)]
    return zones


def stepper(shades, policy):
    """Map each source grey to one of the index's six body steps.

    `equal_width` buckets the observed luminance range: right for a noisy ramp
    where the levels carry no authorial intent. `rank` spreads the distinct
    levels evenly across the six steps in order: right for a small clean ramp,
    where nearest-luminance matching would collapse two of an artist's chosen
    levels onto one step and flatten the shading.
    """
    raw = sorted({c[0] for c in shades})
    # Collapse near-duplicates first. A one-pixel #a4a4a4 sitting beside 67 px of
    # #a5a5a5 is a stray, not a level the artist chose, and ranking it as its own
    # level shifts every step above it.
    lums, groups = [], []
    for v in raw:
        if groups and v - groups[-1][-1] <= NEAR:
            groups[-1].append(v)
        else:
            groups.append([v])
    for g in groups:
        lums.append(g)
    if policy == "equal_width":
        flat = [v for g in lums for v in g]
        lo, hi = flat[0], flat[-1]
        return {v: min(STEPS - 1, int((v - lo) / (hi - lo) * STEPS)) for v in flat}
    if policy == "rank":
        n = len(lums)
        if n == 1:
            return {v: STEPS // 2 for v in lums[0]}
        # int(x + 0.5), not round(): round() is banker's and would send an exact
        # .5 to the even step, which is a surprising rule to debug later.
        return {v: int(i * (STEPS - 1) / (n - 1) + 0.5)
                for i, g in enumerate(lums) for v in g}
    raise ValueError(f"unknown normalisation policy {policy!r}")




def ingest(name, spec):
    src_png = os.path.join(ROOT, spec["source"])
    src_json = os.path.join(ROOT, spec["source_json"])
    ref = os.path.join(ROOT, "authored", "source_bases", spec["family"], name)
    out_dir = os.path.join(ROOT, "authored", "bases", name)
    layout = spec["layout"]

    sheet = read_rgba_png(src_png)
    assert len(sheet[0]) == 20, f"{name}: source is not 20 wide"
    assert len(sheet) >= 20 * len(layout), f"{name}: sheet too short for its layout"
    src = frames(sheet, layout)

    shades = sorted({px[:3] for row in sheet for px in row if px[3]})
    smap = stepper(shades, spec["normalise"])
    ramp = [rgb(c) for c in BODY]

    out, mapping, counts = {}, {}, {}
    for vname, f in src.items():
        g = [[(0, 0, 0, 0)] * 20 for _ in range(20)]
        for y in range(20):
            for x in range(20):
                p = f[y][x]
                if not p[3]:
                    continue
                st = smap[p[0]]
                g[y][x] = ramp[st] + (p[3],)
                mapping["#%02x%02x%02x" % p[:3]] = st
                counts[st] = counts.get(st, 0) + 1
        out[vname] = g

    for vname, f in src.items():
        g = out[vname]
        moved = sum(1 for j in range(20) for i in range(20)
                    if f[j][i][3] != g[j][i][3])
        assert moved == 0, f"{name}/{vname}: alpha changed in {moved} cells"
        assert bbox(f) == bbox(g), f"{name}/{vname}: bounding box moved"

    os.makedirs(os.path.join(ref, "source"), exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    for srcf, dst in ((src_png, "hat.png"), (src_json, "hat.json")):
        shutil.copy2(srcf, os.path.join(ref, "source", dst))
    kept = md5(os.path.join(ref, "source", "hat.png"))
    assert kept == md5(src_png), f"{name}: preserved copy is not byte-identical"

    for vname, g in out.items():
        write_rgba_png(os.path.join(out_dir, f"{vname}.png"), g)

    zones = {v: derive_zones(g) for v, g in out.items()}
    anchors = {}
    for zname in ("crown_top", "side", "band"):
        got = {v: [zones[v][zname][0], zones[v][zname][1]]
               for v in zones if zname in zones[v]}
        if got:
            anchors[zname] = got

    base = {
        "name": name,
        "family": spec["family"],
        "shape_variant": name,
        "slot": "HEAD",
        "classification": spec["classification"],
        "size": [20, 20],
        "views": [v for v, _ in layout],
        "mirrored_at_render": spec["mirrored"],
        "style": spec["style"],
        "provenance": f"{spec['classification']}-ONLY: {spec['attribution']} "
                      f"({spec['source']}). "
                      f"See authored/source_bases/{spec['family']}/{name}/provenance.json",
        "derived_from": spec["source"],
        "normalised": f"{len(shades)} source greys -> {STEPS} body steps, "
                      f"{spec['normalise']}",
        "anchors": anchors,
        "zones": zones,
    }
    with open(os.path.join(out_dir, "base.json"), "w") as fh:
        json.dump(base, fh, indent=2)
        fh.write("\n")

    prov = {
        "id": name,
        "family": spec["family"],
        "classification": spec["classification"],
        "classification_reason": spec["classification_reason"],
        "attribution": spec["attribution"],
        "source": {
            "path": spec["source"],
            "internal_name": spec["internal_name"],
            "md5": md5(src_png),
            "json_md5": md5(src_json),
            "size": [20, len(sheet)],
            "layout": {n: y for n, y in layout},
            "read_only": True,
            "preserved_copy":
                f"authored/source_bases/{spec['family']}/{name}/source/hat.png",
            "preserved_copy_md5": kept,
        },
        "normalisation": {
            "what": "greyscale ramp only",
            "from_shades": len(shades),
            "to_steps": STEPS,
            "policy": spec["normalise"],
            "role": "body",
            "step_colours": BODY,
            "step_pixel_counts": {str(k): v for k, v in sorted(counts.items())},
            "source_grey_to_step": dict(sorted(mapping.items())),
            "preserved_exactly": ["alpha", "silhouette", "bounding box",
                                  "per-direction geometry", "direction layout"],
            "changed": ["shading resolution within the silhouette"],
        },
        "directions": {
            "authored": [n for n, _ in layout],
            "mirrored": spec["mirrored"],
            "note": "authored views are carried through unchanged; a mirrored "
                    "view is produced at render time from its opposite, which "
                    "is what the source's own hat.json specifies",
        },
        "geometry_check": {n: {"bbox": list(bbox(src[n])),
                               "opaque": sum(1 for y in range(20) for x in range(20)
                                             if src[n][y][x][3])}
                           for n, _ in layout},
    }
    with open(os.path.join(ref, "provenance.json"), "w") as fh:
        json.dump(prov, fh, indent=2)
        fh.write("\n")
    return base, prov, zones


def main():
    which = sys.argv[1:] or sorted(SPECS)
    for name in which:
        spec = SPECS[name]
        base, prov, zones = ingest(name, spec)
        print(f"== {name}   family={spec['family']}   {spec['classification']}")
        print(f"   source     {spec['source']}")
        print(f"              md5 {prov['source']['md5']}  READ-ONLY")
        print(f"   preserved  {prov['source']['preserved_copy']}")
        print(f"   normalise  {prov['normalisation']['from_shades']} greys -> "
              f"{STEPS} steps ({spec['normalise']})  "
              f"counts {prov['normalisation']['step_pixel_counts']}")
        print(f"   authored   {', '.join(prov['directions']['authored'])}"
              + (f"   mirrored at render: {', '.join(spec['mirrored'])}"
                 if spec["mirrored"] else ""))
        for v, _ in spec["layout"]:
            print(f"     {v:6} bbox {prov['geometry_check'][v]['bbox']}  "
                  f"zones {sorted(zones[v])}")
        print()


if __name__ == "__main__":
    main()
