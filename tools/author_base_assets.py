"""AUTHORING SOURCE for the pre-drawn asset library.

Run once (or after editing the art here) to emit `authored/`:

    authored/bases/<name>/{front,back,left}.png + base.json
    authored/decals/<name>.png + <name>.json
    authored/palettes.json

The art below IS the source of truth, kept as text so it can be read and
diffed.  The PNGs are the runtime asset and are indexed: every pixel is an
exact colour from INDEX, which decodes to (role, ramp step).  That is what
"recolor-ready" means here — the sprite carries roles and values, never a hue,
so a palette is applied by lookup and nothing has to be re-drawn.

Views: FRONT, BACK and LEFT are authored.  RIGHT is the mirror of LEFT and is
never drawn — Fashion Sense wants four frames, and a hand-drawn right view is
one more thing that can disagree with its own left.

    body   1-6   the garment's own cloth, deep -> highlight

Shading vocabulary, held to across every base (measured against the 194
reference hats, and QC'd by `tools/qc_authored_bases.py`):

    1  the rim, the deepest shadow, undersides.  Outlines are drawn at the
       BOTTOM of the ramp — the corpus runs -44 to -71 border-to-interior and
       a rim drawn one step down only reached -33.
    2  the shadowed side and the contact rows
    3  the turned side, the lower body
    4  the body's own base plane
    5  the lit plane
    6  the light patch: 3-5 cells, never a band.  Using step 6 at all is what
       gives a sprite the corpus's luminance span (172-209); art that stopped
       at 5 measured 132.
    trim   a-f   collars, bands, cuffs: a second cloth
    accent p-u   buttons, buckles, feathers: small hard punctuation
    .            transparent
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5.pngio import write_rgba_png

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "authored")

# --- the index ---------------------------------------------------------------
# Six steps per role.  Body is true grayscale so a base reads as lineart in any
# editor; trim and accent are tinted so the three roles stay separable by eye
# without a second image or a channel trick.
STEPS = 6
BODY = [(32, 32, 32), (64, 64, 64), (96, 96, 96), (128, 128, 128),
        (176, 176, 176), (224, 224, 224)]
TRIM = [(48, 16, 16), (80, 24, 24), (112, 32, 32), (144, 40, 40),
        (192, 56, 56), (232, 96, 96)]
ACCENT = [(16, 16, 48), (24, 24, 80), (32, 32, 112), (40, 40, 144),
          (56, 56, 192), (96, 96, 232)]
# HARDWARE is buckles, buttons, rivets, clasps: a METAL, not a cloth.  It gets
# its own role because a palette resolves it from the story's own metal colour
# rather than from the garment's cloth, and because a decoration that is metal
# should stay metal when the hat is recoloured.
HARDWARE = [(16, 48, 16), (24, 80, 24), (32, 112, 32), (40, 144, 40),
            (56, 192, 56), (96, 232, 96)]

CHARS = {}
for i in range(STEPS):
    CHARS[str(i + 1)] = ("body", i, BODY[i])
    CHARS["abcdef"[i]] = ("trim", i, TRIM[i])
    CHARS["pqrstu"[i]] = ("accent", i, ACCENT[i])
    CHARS["ABCDEF"[i]] = ("hardware", i, HARDWARE[i])


def grid(rows, w, h):
    """ASCII art -> RGBA rows, padded to w x h."""
    out = []
    for y in range(h):
        line = rows[y] if y < len(rows) else ""
        line = line + "." * (w - len(line))
        out.append([(0, 0, 0, 0) if ch == "." else (*CHARS[ch][2], 255)
                    for ch in line[:w]])
    return out


# =============================================================================
# BASE 1 — FELT HAT, 20x20, the plain brimmed felt hat
# =============================================================================
#
# Proportions are the corpus medians for the BRIMMED_FELT family measured over
# 194 reference hats: bbox 14 wide, crown 6-7 rows over a 2-row brim, brim line
# at row 10, crown 8 wide.  Shading follows what those hats do and ours did not:
# a mid body, a small light patch near the centre line in the upper third, the
# right side turning away, a dark rim, and two contact rows at the bottom.
#
# Drawn WITHOUT a band — a band is a decal, so one base serves the plain hat,
# the ribboned hat and the buckled hat.

HAT_FRONT = [
    "",
    "",
    "",
    "........1331........",
    ".......134631.......",
    "......13466321......",
    "......13454321......",
    "......13343321......",
    "......12333221......",
    "......12222221......",
    "...12333333333221...",
    ".....1122222211.....",
]

HAT_LEFT = [
    "",
    "",
    "",
    "........1331........",
    ".......134631.......",
    "......13466321......",
    "......13454321......",
    "......12333221......",
    "......12222221......",
    "...12333333333221...",
    ".....1122222211.....",
]

# The back is the same hat seen from behind: one row lower, no light patch —
# the crown turns away from the light, which is what the corpus draws.
HAT_BACK = [
    "",
    "",
    "",
    "",
    "........1331........",
    ".......134431.......",
    "......13445321......",
    "......13444321......",
    "......13343321......",
    "......12333221......",
    "......12222221......",
    "...12333333333221...",
    ".....1122222211.....",
]

HAT_BASE = {
    "name": "felt_hat",
    "slot": "HEAD",
    "size": [20, 20],
    "style": ["formal", "work", "smart"],
    "description": "plain brimmed felt hat: 7-row crown over a 2-row brim",
    # Where decals attach, per view, as the TOP-LEFT cell of the decal.
    # A decal that lands off the base is dropped, never drawn floating.
    "anchors": {
        "band_line": {"front": [7, 8], "left": [7, 7], "back": [7, 9]},
        "band_side": {"front": [11, 7], "left": [11, 6], "back": [11, 8]},
        "brim_edge": {"front": [3, 10], "left": [3, 9], "back": [3, 11]},
        "crown_face": {"front": [8, 6], "left": [8, 5], "back": [8, 7]}
    },
    "views": {"front": HAT_FRONT, "left": HAT_LEFT, "back": HAT_BACK},
}




# ---------------------------------------------------------------------------
# LEGAL DECORATION ZONES
# ---------------------------------------------------------------------------
#
# A zone is a REGION of a base where decoration may legally sit, per view.
# Anchors alone were not enough once decals varied in size: an anchor says
# "start drawing here", a zone says "this whole area is the band, and a piece
# must fit inside it".  Placement is authored either way — a decal is centred
# in its zone, never scattered — and anything that does not fit is dropped.
#
# Zones are DERIVED from the base's own drawn cells so they cannot point at
# empty space, then written into the manifest so they are inspectable and
# hand-editable like everything else here.

def _rows_of(cells):
    """Row -> its widest CONTIGUOUS run of cells, as (x0, x1).

    Not min..max: several of these constructions legitimately split a row — the
    cap inherits a split bottom row from vanilla 016 — and a zone spanning the
    gap would place a band across a hole, which is then dropped as "off the
    base".  A zone must be a region a motif can actually sit on.
    """
    rows = {}
    for (x, y) in cells:
        rows.setdefault(y, []).append(x)
    out = {}
    for y, xs in rows.items():
        xs = sorted(xs)
        best = run = (xs[0], xs[0])
        for a, b in zip(xs, xs[1:]):
            run = (run[0], b) if b == a + 1 else (b, b)
            if run[1] - run[0] > best[1] - best[0]:
                best = run
        out[y] = best
    return out


def _clip_to_cells(box, cells):
    """Shrink a zone until every cell inside it is actually drawn.

    A zone is a rectangle and these silhouettes are curved, so a rectangle laid
    on the shoulder of a crown has corners hanging in space.  Rather than let a
    motif be dropped later for landing on one of them, the zone is shrunk now:
    a zone should be legal BY CONSTRUCTION, and then a motif that fits inside it
    always draws.
    """
    x0, y0, x1, y1 = box
    while x1 >= x0 and y1 >= y0:
        missing = [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)
                   if (x, y) not in cells]
        if not missing:
            return [x0, y0, x1, y1]
        # drop whichever edge carries the most holes
        edges = {"x0": sum(1 for x, _ in missing if x == x0),
                 "x1": sum(1 for x, _ in missing if x == x1),
                 "y0": sum(1 for _, y in missing if y == y0),
                 "y1": sum(1 for _, y in missing if y == y1)}
        worst = max(edges, key=lambda k: edges[k])
        if edges[worst] == 0:
            return None
        if worst == "x0":
            x0 += 1
        elif worst == "x1":
            x1 -= 1
        elif worst == "y0":
            y0 += 1
        else:
            y1 -= 1
    return None


def zones_for(cells_by_view: dict, kind: str) -> dict:
    """Named rectangles per view: (x0, y0, x1, y1) inclusive.

    `kind` picks the vocabulary a construction actually has — a brimmed hat has
    a band and a brim; a knitted cap has a cuff and no brim at all.
    """
    out = {}
    for view, cells in cells_by_view.items():
        rows = _rows_of(cells)
        ys = sorted(rows)
        top, bottom = ys[0], ys[-1]
        widest = max(ys, key=lambda y: rows[y][1] - rows[y][0])
        z = {}
        # the crown's own face: the middle band of the mass, inset one cell so
        # a motif never lands on the outline
        mid = (top + widest) // 2
        lo, hi = rows[mid]
        z["crown_face"] = [lo + 1, max(top + 1, mid - 1), hi - 1, min(bottom - 1, mid + 1)]
        # the top of the crown, for a button or a pom
        tlo, thi = rows[top]
        z["crown_top"] = [tlo, top, thi, min(top + 1, bottom)]
        def width(y):
            return rows[y][1] - rows[y][0] + 1

        def lowest_wide_row(upper_bound, min_frac=0.6):
            """The lowest row at or above `upper_bound` still wide enough to
            carry a band.

            Measured against the widest row IN RANGE, not the widest row of the
            whole hat: on a brimmed hat the widest row is the brim, and judging
            a crown band against a 14-wide brim rejected every 8-wide crown row
            and slid the band down onto the brim itself.
            """
            candidates = [y for y in range(upper_bound, top - 1, -1) if y in rows]
            if not candidates:
                return widest
            need = max(width(y) for y in candidates) * min_frac
            for y in candidates:
                if width(y) >= need:
                    return y
            return candidates[0]

        if kind == "brimmed":
            # the band sits on the crown row just above the brim line
            band = lowest_wide_row(max(top, widest - 1))
            blo, bhi = rows[band]
            z["band"] = [blo + 1, band - 1, bhi - 1, band]
            wlo, whi = rows[widest]
            z["brim"] = [wlo, widest, whi, bottom]
        elif kind == "cuffed":
            cuff = lowest_wide_row(max(top, bottom - 2))
            clo, chi = rows[cuff]
            z["cuff"] = [clo + 1, cuff, chi - 1, min(bottom - 1, cuff + 1)]
        else:                      # a cap: a sweatband row, no brim
            band = lowest_wide_row(max(top, bottom - 1))
            blo, bhi = rows[band]
            z["band"] = [blo + 1, band, bhi - 1, band]
        # The side of the CROWN, for a feather or a pin — not the side of the
        # widest row, which on a brimmed hat is the brim and leaves a zone one
        # cell wide once it is clipped to drawn cells.
        mlo, mhi = rows[mid]
        z["side"] = [mhi - 2, max(top + 1, mid - 1), mhi, min(bottom - 1, mid + 1)]
        clipped = {}
        for name, box in z.items():
            fixed = _clip_to_cells(box, cells)
            if fixed:
                clipped[name] = fixed
        out[view] = clipped
    return out


# =============================================================================
# DECALS — small pre-drawn pieces with anchor metadata
# =============================================================================
#
# A decal draws only where the base already has cloth.  Cells that fall outside
# the base silhouette are dropped, so a decal can never change what the garment
# IS — the same one-owner rule the procedural templates follow.

# =============================================================================
# WORK SHIRT — unchanged control
# =============================================================================
SHIRT_FRONT = [
    ".233332.",
    "23445332",
    "23445332",
    "23344332",
    ".334433.",
    ".333333.",
    ".233332.",
    ".222222.",
]

SHIRT_LEFT = [
    "..2332..",
    ".233432.",
    ".233432.",
    ".233432.",
    "..3343..",
    "..3333..",
    "..2332..",
    "..2222..",
]

SHIRT_BACK = [
    ".233332.",
    "23344332",
    "23344332",
    "23344332",
    ".334433.",
    ".333333.",
    ".233332.",
    ".222222.",
]

SHIRT_BASE = {
    "name": "work_shirt",
    "slot": "TOP",
    "size": [8, 8],
    "style": ["work", "casual", "cottagecore"],
    "description": "plain long-body work shirt with set sleeves",
    "anchors": {
        "neck": {"front": [2, 0], "left": [2, 0], "back": [2, 0]},
        "placket": {"front": [3, 1], "left": None, "back": None},
        "chest_left": {"front": [2, 2], "left": None, "back": None},
        "hem": {"front": [1, 6], "left": [2, 6], "back": [1, 6]},
    },
    "views": {"front": SHIRT_FRONT, "left": SHIRT_LEFT, "back": SHIRT_BACK},
}


# =============================================================================
# WIDE BRIM HAT — unchanged control
# =============================================================================
WIDE_FRONT = [
    "",
    "",
    "",
    ".......123321.......",
    "......13466321......",
    "......13466521......",
    "......13345321......",
    "......12333321......",
    "......12222221......",
    "..1233444444333221..",
    "..1222333333222221..",
    "...111111111111111..",
]

WIDE_LEFT = [
    "",
    "",
    "",
    ".......123321.......",
    "......13466321......",
    "......13465321......",
    "......13344321......",
    "......12222221......",
    "..1233444444333221..",
    "..1222333333222221..",
    "...111111111111111..",
]

WIDE_BACK = [
    "",
    "",
    "",
    "",
    ".......123321.......",
    "......13445321......",
    "......13444321......",
    "......13343321......",
    "......12333321......",
    "......12222221......",
    "..1233444444333221..",
    "..1222333333222221..",
    "...111111111111111..",
]

WIDE_BASE = {
    "name": "wide_brim_hat",
    "slot": "HEAD",
    "size": [20, 20],
    "style": ["work", "casual", "festival", "cottagecore"],
    "description": "small crown under a 16-wide three-row brim: sun hat / cowboy",
    "anchors": {
        "band_line": {"front": [7, 8], "left": [7, 8], "back": [7, 9]},
        "band_side": {"front": [11, 7], "left": [11, 7], "back": [11, 8]},
        "brim_edge": {"front": [2, 9], "left": [2, 9], "back": [2, 10]},
        "crown_face": {"front": [8, 6], "left": [8, 6], "back": [8, 7]},
    },
    "views": {"front": WIDE_FRONT, "left": WIDE_LEFT, "back": WIDE_BACK},
}


# =============================================================================
# SOFT CAP — from ONE reference, not a family average
# =============================================================================
CAP_FRONT = [
    "",
    "",
    "",
    "........3443........",
    "......22444422......",
    ".....2456666542.....",
    "....244555666552....",
    "....244455566552....",
    "....244433335662....",
    "...24443455435552...",
    "...23334333343332...",
    "....22.......222....",
]

CAP_LEFT = [
    "",
    "",
    "",
    "........3443........",
    "......33444432......",
    ".....3555555432.....",
    "..33335666554432....",
    ".354436665545442....",
    ".345536655545442....",
    ".3455455554544432...",
    "..322443322222222...",
]

CAP_BACK = [
    "",
    "",
    "",
    "",
    "......33333333......",
    ".....3445555443.....",
    "....344454565443....",
    "....344445455553....",
    "....144444545441....",
    "...13334444443331...",
    "...13333111133331...",
    "....131......131....",
    ".....1111111111.....",
]

CAP_BASE = {
    "name": "soft_cap",
    "slot": "HEAD",
    "size": [20, 20],
    "style": ["casual", "work", "cottagecore", "smart"],
    "derived_from": "vanilla hats.png #16",
    "hand_adjusted": "side peak raised one row so it tucks into the "
                     "crown instead of hanging below it",
    "tone_profile": "vanilla_016",
    "description": "peaked cap derived from ONE reference (vanilla hats.png #16): its row rhythm, split bottom row, forward peak and per-view differences are preserved exactly; only its colours are restated as semantic role/step so a palette stays replaceable.",
    "anchors": {
        "crown_top": {"front": [10, 4], "left": [10, 4], "back": [10, 6]},
        "peak_edge": {"front": None, "left": [1, 9], "back": None},
        "crown_face": {"front": [9, 7], "left": [9, 7], "back": [9, 9]},
    },
    "views": {"front": CAP_FRONT, "left": CAP_LEFT, "back": CAP_BACK},
}


# =============================================================================
# KNIT CAP — from ONE reference, not a family average
# =============================================================================
KNIT_FRONT = [
    "",
    "",
    "",
    "",
    "........2222........",
    ".......245542.......",
    "......22445522......",
    ".....1524445252.....",
    ".....1522445552.....",
    ".....1452245542.....",
    ".....1155445411.....",
    "......12444421......",
    ".......111111.......",
]

KNIT_LEFT = [
    "",
    "",
    "",
    "",
    "",
    ".........22111......",
    "......222455421.....",
    "....224555544421....",
    "...2455554444221....",
    "...2111111242421....",
    "........11222221....",
    ".............111....",
    "...............1....",
]

KNIT_BACK = [
    "",
    "",
    "",
    "",
    "",
    "",
    "........2222........",
    ".......244442.......",
    "......24455542......",
    ".....1445455541.....",
    ".....1244545521.....",
    ".....1244445421.....",
    ".....1224444221.....",
    "......12222221......",
    "......12222221......",
    ".......111111.......",
]

KNIT_BASE = {
    "name": "knit_cap",
    "slot": "HEAD",
    "size": [20, 20],
    "style": ["casual", "work", "cottagecore", "festival"],
    "derived_from": "vanilla hats.png #33",
    "hand_adjusted": "hem widened and a lower edge row added, so the "
                     "bottom keeps some volume at game scale",
    "tone_profile": "vanilla_033",
    "description": "knitted cap derived from ONE reference (vanilla hats.png #33): a soft lumpy crown that narrows at the top and draws back in at the hem, with the reference's own value structure restated as role/step.",
    "anchors": {
        "crown_top": {"front": [10, 4], "left": [11, 5], "back": [10, 6]},
        "cuff_line": {"front": [6, 10], "left": [5, 9], "back": [6, 13]},
        "crown_face": {"front": [9, 7], "left": [10, 8], "back": [9, 9]},
    },
    "views": {"front": KNIT_FRONT, "left": KNIT_LEFT, "back": KNIT_BACK},
}


DECALS = [
    # ------------------------------------------------------------------
    # SOFT_CAP EMBLEM SET — converted from the Gemini emblem sheet
    # (motif/gemini_emblem_sheet.png).  Each was downsampled to the cap's own
    # zone sizes and restated in role/step; the design language — dashed patch
    # border, five-point star, faceted gem, round badge rim — is preserved,
    # the colours are not, because colour is the palette's job.
    #
    # The cap's zones are SMALL: crown_face 4x2, crown_top 2x2, band 8x1,
    # side 3x2.  So flat cloth things (patch, tag, stitch run, button) are
    # surface motifs sized to fit, and the emblems that want to be objects
    # (star, heart, leaf, flower, gem, badge) are attachments pinned at the
    # side — which the soft_cap audit showed is where this base reads best.
    # ------------------------------------------------------------------
    {
        "name": "patch_cap",
        "motif_class": "patch",
        "pending": True,
        "slot": "HEAD", "zone": "front_panel", "z": 2,
        "style": ["work", "casual"],
        "views": ["front"],
        "fits": ["soft_cap"],
        "art": ["bddb", "bffb"],
        "description": "a small stitched patch on the front panel",
    },
    {
        "name": "tag_cap",
        "motif_class": "tag",
        "pending": True,
        "slot": "HEAD", "zone": "side_panel", "z": 2,
        "style": ["casual", "smart"],
        # the cap's left frame has no side zone once clipped to drawn cells
        "views": ["front", "back"],
        "fits": ["soft_cap"],
        "art": ["cfc", "dfa"],
        "description": "a woven side tag stitched to the panel seam",
    },
    {
        "name": "stitch_run_cap",
        "motif_class": "stitch_accent",
        "pending": True,
        "slot": "HEAD", "zone": "visor", "z": 2,
        "style": ["casual", "work"],
        "views": ["front", "left"],
        "fits": ["soft_cap"],
        # alternation, but in the ACCENT role: band_striped proved that a
        # hue-separated alternation survives on this base where a trim-on-trim
        # one fragments
        "art": ["ctctctct"],
        "description": "a run of contrast stitches along the band",
    },
    {
        "name": "button_top_cap",
        "motif_class": "button",
        "pending": True,
        "slot": "HEAD", "zone": "top", "z": 3,
        "style": ["smart", "work", "casual"],
        "views": ["front", "left", "back"],
        "fits": ["soft_cap"],
        "art": ["DF", "AC"],
        "description": "the metal button at the crown seam",
    },
    {
        "name": "star_pin",
        "motif_class": "star",
        "pending": True,
        "slot": "HEAD", "zone": "front_panel", "z": 3,
        "kind": "attachment", "max_extent": 7,
        "anchor_cell": [1, 2], "anchor_point": "top_right",
        "style": ["casual", "smart"],
        "views": ["front"],
        "fits": ["soft_cap"],
        "art": [".D.", "DFD", "D.D"],
        "description": "a five-point star pin",
    },
    {
        "name": "heart_pin",
        "motif_class": "heart",
        "pending": True,
        "slot": "HEAD", "zone": "front_panel", "z": 3,
        "kind": "attachment", "max_extent": 7,
        "anchor_cell": [1, 2], "anchor_point": "top_right",
        "style": ["cottagecore", "casual"],
        "views": ["front"],
        "fits": ["soft_cap"],
        "art": ["t.t", "tut", ".t."],
        "description": "a small heart pin",
    },
    {
        "name": "leaf_pin",
        "motif_class": "leaf",
        "pending": True,
        "slot": "HEAD", "zone": "side_panel", "z": 3,
        "kind": "attachment", "max_extent": 7,
        "anchor_cell": [0, 2], "anchor_point": "top_right",
        "style": ["cottagecore", "work"],
        "views": ["front", "left"],
        "fits": ["soft_cap"],
        "art": [".tu", "tut", "s.."],
        "description": "a single leaf pinned to the panel",
    },
    {
        "name": "flower_tiny",
        "motif_class": "flower",
        "pending": True,
        "slot": "HEAD", "zone": "side_panel", "z": 3,
        "kind": "attachment", "max_extent": 6,
        "anchor_cell": [1, 2], "anchor_point": "top_right",
        "style": ["cottagecore"],
        "views": ["front", "left", "back"],
        "fits": ["soft_cap"],
        "art": [".t.", "tFt", ".t."],
        "description": "a single small blossom",
    },
    {
        "name": "gem_drop",
        "motif_class": "gem",
        "pending": True,
        "slot": "HEAD", "zone": "front_panel", "z": 3,
        "kind": "attachment", "max_extent": 6,
        "anchor_cell": [0, 2], "anchor_point": "top_right",
        "style": ["smart", "cottagecore"],
        "views": ["front"],
        "fits": ["soft_cap"],
        "art": ["tu", "uu", "qq"],
        "description": "a faceted drop gem, bright above and dark below",
    },
    {
        "name": "badge_round_cap",
        "motif_class": "badge",
        "pending": True,
        "slot": "HEAD", "zone": "front_panel", "z": 3,
        "kind": "attachment", "max_extent": 7,
        "anchor_cell": [1, 2], "anchor_point": "top_right",
        "style": ["smart", "work"],
        "views": ["front"],
        "fits": ["soft_cap"],
        "art": ["CDC", "DFD", "CDC"],
        "description": "a round metal badge with a rimmed edge",
    },
    # ------------------------------------------------------------------
    # EXPANDED LIBRARY — derived from the motif reference sheet
    # (Hats n Hats family, Charasan, licensed for modification WITH
    # ATTRIBUTION).  Each entry names its kind, zone, views and the bases it
    # can legally reach; none of them changes architecture.
    # ------------------------------------------------------------------

    # --- bands ---------------------------------------------------------
    {
        "name": "band_braided",
        "motif_class": "woven_trim",
        "slot": "HEAD", "zone": "band", "z": 2,
        "style": ["work", "casual", "cottagecore"],
        "views": ["front", "left", "back"],
        "fits": ["felt_hat", "wide_brim_hat"],
        # Measured in game: single alternating cells fragment into three pieces
        # (4 changed cells, 3 fragments).  Two-cell runs carry the same braid
        # rhythm and stay one connected shape.
        "art": ["cceecc"],
        "description": "a braided cord: paired strands, light against shadow",
    },
    {
        "name": "band_striped",
        "motif_class": "band",
        "slot": "HEAD", "zone": "band", "z": 2,
        "style": ["casual", "festival", "cottagecore"],
        "views": ["front", "left", "back"],
        "fits": ["wide_brim_hat"],
        "art": ["dtdtdt"],
        "description": "a ribbon striped in the accent colour",
    },
    {
        "name": "band_woven_wide",
        "motif_class": "woven_trim",
        "slot": "HEAD", "zone": "band", "z": 2,
        "style": ["cottagecore", "casual", "festival"],
        "views": ["front", "left", "back"],
        "fits": ["wide_brim_hat"],
        # The same idea rebuilt for a crown that shades across the band: solid
        # runs instead of single cells, and the light strand takes the accent
        # role so it separates from the cloth by hue as well as value.
        "art": ["ccttcc"],
        "description": "a woven band for the wide brim: solid strands, accent light",
    },
    {
        "name": "band_laced",
        "motif_class": "band",
        "slot": "HEAD", "zone": "band", "z": 2,
        "style": ["formal", "smart", "cottagecore"],
        "views": ["front", "left", "back"],
        "fits": ["felt_hat", "wide_brim_hat"],
        "art": ["cddddc", "cfcfcf"],
        "description": "a band with a laced stitch line under it",
    },
    {
        "name": "buckle_square",
        "motif_class": "buckled_band",
        "slot": "HEAD", "zone": "band", "z": 2,
        "style": ["formal", "smart"],
        "views": ["front", "left", "back"],
        "fits": ["felt_hat"],
        "art": ["cdCFCd", "ccDDcc"],
        "description": "a wide belt buckle seated on the band",
    },

    # --- bows and ribbons ----------------------------------------------
    {
        "name": "bow_knot",
        "motif_class": "bow",
        "slot": "HEAD", "zone": "side", "z": 3,
        "kind": "attachment", "max_extent": 7,
        "anchor_cell": [1, 1], "anchor_point": "top_right",
        "style": ["cottagecore", "festival", "casual"],
        "views": ["front", "left", "back"],
        "fits": ["wide_brim_hat", "knit_cap"],
        "art": ["e.e", "dcd", "e.e"],
        "description": "a ribbon bow tied at the side of the crown",
    },
    {
        "name": "ribbon_tail",
        "motif_class": "ribbon_tag",
        "slot": "HEAD", "zone": "side", "z": 3,
        "kind": "attachment", "max_extent": 6,
        "anchor_cell": [0, 0], "anchor_point": "top_right",
        "style": ["cottagecore", "festival"],
        "views": ["front", "left"],
        "fits": ["wide_brim_hat", "knit_cap"],
        "art": ["dd", "cd", "cc", ".c"],
        "description": "a ribbon end trailing from the band",
    },

    # --- flowers and leaves --------------------------------------------
    {
        "name": "flower_daisy",
        "motif_class": "flower",
        "slot": "HEAD", "zone": "side", "z": 3,
        "kind": "attachment", "max_extent": 7,
        "anchor_cell": [1, 2], "anchor_point": "top_right",
        "style": ["cottagecore", "festival"],
        "views": ["front", "left", "back"],
        "fits": ["wide_brim_hat", "knit_cap"],
        "art": ["tut", "uFu", "tut"],
        "description": "a round flower head, petals alternating around a bright centre",
    },
    {
        "name": "flower_rose",
        "motif_class": "flower",
        "slot": "HEAD", "zone": "side", "z": 3,
        "kind": "attachment", "max_extent": 7,
        "anchor_cell": [1, 2], "anchor_point": "top_right",
        "style": ["cottagecore", "festival"],
        "views": ["front", "left"],
        "fits": ["wide_brim_hat", "knit_cap"],
        "art": ["ut.", "tut", ".s."],
        "description": "a tight rose head, darker at its base",
    },
    {
        "name": "leaf_sprig",
        "motif_class": "leaf",
        "slot": "HEAD", "zone": "side", "z": 3,
        "kind": "attachment", "max_extent": 6,
        "anchor_cell": [0, 3], "anchor_point": "top_right",
        "style": ["cottagecore", "work"],
        "views": ["front", "left"],
        "fits": ["wide_brim_hat", "knit_cap"],
        "art": [".tt", "tu.", ".st", "s.."],
        "description": "two leaves on a short stem",
    },

    # --- badges, gems, brooches ----------------------------------------
    {
        "name": "badge_star",
        "motif_class": "badge",
        "slot": "HEAD", "zone": "crown_face", "z": 3,
        "style": ["formal", "festival", "smart"],
        "views": ["front", "back"],
        "fits": ["felt_hat", "wide_brim_hat"],
        "art": ["bDb", "DFD", "bDb"],
        "description": "a metal star badge, rimmed dark so it reads as applied",
    },
    {
        "name": "gem_oval",
        "motif_class": "gem",
        "slot": "HEAD", "zone": "crown_face", "z": 3,
        "style": ["formal", "festival"],
        "views": ["front", "back"],
        "fits": ["felt_hat", "wide_brim_hat"],
        "art": ["CDC", "DuD", "CDC"],
        "description": "an oval gem in a metal setting",
    },
    {
        "name": "brooch_round",
        "motif_class": "badge",
        "slot": "HEAD", "zone": "side", "z": 3,
        "style": ["formal", "smart"],
        "views": ["front", "left"],
        # the caps' side zone is 3x2 and this needs three rows
        "fits": ["felt_hat"],
        "art": ["bCb", "CFC", "bCb"],
        "description": "a round brooch, rimmed dark, on the side of the crown",
    },

    # --- patches --------------------------------------------------------
    {
        "name": "patch_square",
        "motif_class": "patch",
        "slot": "HEAD", "zone": "crown_face", "z": 2,
        "style": ["work", "casual"],
        "views": ["front", "back"],
        "fits": ["felt_hat", "wide_brim_hat"],
        "art": ["bbbb", "bffb", "bbbb"],
        "description": "a bright patch inside a dark border, sewn to the crown",
    },

    # --- feathers -------------------------------------------------------
    {
        "name": "feather_short",
        "motif_class": "long_feather",
        "slot": "HEAD", "zone": "side", "z": 3,
        "kind": "attachment", "max_extent": 5,
        "anchor_cell": [0, 2], "anchor_point": "top_right",
        "style": ["casual", "work", "cottagecore"],
        "views": ["front", "left"],
        "fits": ["knit_cap"],
        "art": ["..tu", ".stu", "q..."],
        "description": "a short quill with a two-cell vane, for a cap",
    },

    # --- pom styles -----------------------------------------------------
    {
        "name": "pom_small",
        "motif_class": "pom",
        "slot": "HEAD", "zone": "crown_top", "z": 3,
        "kind": "attachment", "max_extent": 5,
        "anchor_cell": [1, 1], "anchor_point": "top_centre",
        "style": ["casual", "work"],
        "views": ["front", "left", "back"],
        "fits": ["knit_cap"],
        "art": ["def", "cdc"],
        "description": "a small tight bobble",
    },
    {
        "name": "pom_tassel",
        "motif_class": "tassel",
        "slot": "HEAD", "zone": "crown_top", "z": 3,
        "kind": "attachment", "max_extent": 8,
        "anchor_cell": [1, 3], "anchor_point": "top_centre",
        "style": ["cottagecore", "festival"],
        "views": ["front", "left", "back"],
        "fits": ["knit_cap"],
        "art": [".dd.", "dfed", ".cc.", ".c.."],
        "description": "a pom with a short tie hanging beneath it",
    },

    # --- charms and tassels ---------------------------------------------
    {
        "name": "charm_pendant",
        "slot": "HEAD", "zone": "side", "z": 3,
        "kind": "attachment", "max_extent": 5,
        "anchor_cell": [0, 0], "anchor_point": "top_right",
        "style": ["festival", "formal"],
        "views": ["front", "left"],
        "fits": ["wide_brim_hat", "felt_hat"],
        "art": [".C.", ".C.", "CFC", ".C."],
        "description": "a charm on a visible chain, hanging clear of the brim",
    },
    {
        "name": "tassel_hang",
        "motif_class": "tassel",
        "slot": "HEAD", "zone": "side", "z": 3,
        "kind": "attachment", "max_extent": 6,
        "anchor_cell": [0, 0], "anchor_point": "top_right",
        "style": ["festival", "cottagecore"],
        "views": ["front", "left"],
        "fits": ["wide_brim_hat", "knit_cap"],
        "art": ["dd", "ce", "cc", "c."],
        "description": "a short tassel swinging from the band",
    },

    # --- brim trim ------------------------------------------------------
    {
        "name": "brim_band",
        "motif_class": "edge_accent",
        "edge": True,
        "slot": "HEAD", "zone": "brim", "z": 2,
        "style": ["formal", "smart", "work"],
        "views": ["front", "left"],
        "fits": ["felt_hat", "wide_brim_hat"],
        "art": ["dddddddddddd"],
        "description": "a solid trim line laid along the brim",
    },
    {
        "name": "brim_lace",
        "motif_class": "lace",
        "edge": True,
        "slot": "HEAD", "zone": "brim", "z": 2,
        "style": ["cottagecore", "festival"],
        "views": ["front", "left"],
        "fits": ["wide_brim_hat"],
        # Alternating single cells fragmented into four pieces in two separate
        # captures.  A solid run carries the trim and the scallops hang off it,
        # so every lit cell is connected to the line above and the whole thing
        # reads as one edging.
        "art": ["dddddddddddd",
                "f.f.f.f.f.f."],
        "description": "a solid brim line with lace scalloped beneath it",
    },
    # ---------------------------------------------------------------------
    # MOTIF LIBRARY — zone-anchored decoration
    # ---------------------------------------------------------------------
    #
    # Each motif declares the BASES it was drawn for, the VIEWS it supports and
    # the ZONE it belongs in.  Placement is authored: a motif is centred in its
    # zone and skipped whole if it will not fit, so decoration can change a
    # hat's personality without ever changing its silhouette.
    #
    # `a`-`f` trim, `p`-`u` accent, `A`-`F` hardware, `1`-`6` body.
    {
        "name": "band_plain",
        "motif_class": "band",
        "slot": "HEAD", "zone": "band", "z": 2,
        "style": ["formal", "smart", "work"],
        "views": ["front", "left", "back"],
        "fits": ["felt_hat", "wide_brim_hat"],
        "art": ["cddddc"],
        "description": "a plain ribbon seated where the crown meets the brim",
    },
    {
        "name": "band_buckled",
        "motif_class": "buckled_band",
        "slot": "HEAD", "zone": "band", "z": 2,
        "style": ["formal", "smart"],
        "views": ["front", "left", "back"],
        # formal/smart, and wide_brim_hat is work/casual/festival/cottagecore:
        # the two can never legally meet, so only felt_hat is declared.
        "fits": ["felt_hat"],
        # the band itself was dark trim on a dark crown and only the buckle
        # read; the ribbon moves up the trim ramp so the whole thing carries
        "art": ["deDFed"],
        "description": "ribbon with a small metal buckle on the centre line",
    },
    {
        # ATTACHMENT.  A feather that stays inside the crown is a blotch: its
        # identity IS the protrusion, which is why the in-game pass could not
        # read the surface version.  It may leave the silhouette, but only by
        # `max_extent` cells, only while every cell stays connected back to the
        # base, and only with pixels authored per view — a feather rising to
        # the right head-on sweeps BACKWARD in profile.
        "name": "side_feather",
        "motif_class": "long_feather",
        "slot": "HEAD", "zone": "side", "z": 3,
        "kind": "attachment", "max_extent": 7,
        # the quill's base cell is its lower-left; it aligns to the outer top
        # corner of the side zone so the feather rises away from the crown
        "anchor_cell": [0, 3], "anchor_point": "top_right",
        "style": ["festival", "cottagecore"],
        "views": ["front", "left"],
        # felt_hat is formal/work/smart and this is festival/cottagecore, so it
        # could never legally land there: declaring it was a lie the tests now
        # catch.
        "fits": ["wide_brim_hat"],
        # One quill shape for both views: anchored at the OUTER top corner of
        # the side zone it rises away from the crown head-on and sweeps
        # backward in profile, which is the same gesture seen twice.  The left
        # variant that mirrored it pointed into the wearer's face.
        #
        # Shape derived from the motif reference sheet (Hats n Hats family,
        # Charasan, CC-with-attribution) by downsampling its feather to this
        # scale: a 1px diagonal was a scratch, and what the reference actually
        # carries at 4x5 is a QUILL with a two-cell blade and a dark spine.
        # Third pass: a wider VANE with a real taper, and the shaft called out
        # one step darker than the vane it carries.  The two-cell blade still
        # read as a stroke; a feather is a shaft with barbs either side of it,
        # and at this size that needs three cells across the middle.
        # Four rows, not five: the wider vane costs cells, and the motif's own
        # bound of 7 outside the silhouette is a declared rule rather than
        # something to raise whenever the art grows.  Losing the fifth row keeps
        # it compact AND inside the bound, which is the trade the constraint is
        # there to force.
        "art": ["..tu",
                ".stu",
                ".rs.",
                "q..."],
        "description": "a quill rising out of the band, past the crown",
    },
    {
        # Reclassified from surface to ATTACHMENT.  In game this read as a
        # highlight, because a pin drawn flat on a crown is just a light patch;
        # what makes a hat pin legible is the needle leaving the hat.
        "name": "side_pin",
        "motif_class": "pin",
        "slot": "HEAD", "zone": "side", "z": 3,
        "kind": "attachment", "max_extent": 6,
        "anchor_cell": [0, 3], "anchor_point": "top_right",
        "style": ["formal", "smart", "festival"],
        "views": ["front", "left"],
        "fits": ["felt_hat", "wide_brim_hat"],
        "art": ["..FF", "..C.", ".CC.", "C..."],
        "description": "a hat pin: a bead head on a needle leaving the crown",
    },
    {
        "name": "crown_patch",
        "motif_class": "patch",
        "slot": "HEAD", "zone": "crown_face", "z": 2,
        "style": ["work", "casual", "cottagecore"],
        "views": ["front", "back"],
        # A bordered patch needs three rows, and the caps' crown faces are two
        # deep once clipped to drawn cells.  Declaring them would be a lie the
        # tests catch; the caps keep crown_button in that region instead.
        "fits": ["felt_hat", "wide_brim_hat"],
        # a fill with no border merged into the crown; the patch now carries
        # its own dark edge, which is what makes a patch read as applied
        "art": ["bbbb", "bdeb", "bbbb"],
        "description": "a stitched patch, bordered, on the face of the crown",
    },
    {
        "name": "crown_button",
        "motif_class": "button",
        "slot": "HEAD", "zone": "crown_top", "z": 3,
        "style": ["casual", "work", "smart"],
        "views": ["front", "left", "back"],
        "fits": ["knit_cap"],
        "art": ["F"],
        "description": "the metal button at the centre of a cap's crown",
    },
    {
        # ATTACHMENT.  A pom sits ON TOP of the crown; drawn inside it, it was
        # only a lighter lump.  The bottom row overlaps the crown so it is
        # anchored, and the ball itself rises out of the silhouette.
        "name": "top_pom",
        "motif_class": "pom",
        "slot": "HEAD", "zone": "crown_top", "z": 3,
        "kind": "attachment", "max_extent": 8,
        # the pom's bottom-centre rests on the crown top
        "anchor_cell": [1, 2], "anchor_point": "top_centre",
        "style": ["casual", "cottagecore", "festival"],
        "views": ["front", "left", "back"],
        "fits": ["knit_cap"],
        # Derived from the reference sheet's poms the same way: downsampled,
        # they are a BALL — a rounded top, one specular cell, and a dark
        # underside where it meets the crown.  The old version had no specular
        # and no dark side, so it read as a lump rather than a sphere.
        # Third pass: the outline is deliberately IRREGULAR.  A symmetric ring
        # of cells reads as a smooth ball — a bauble, not wool — so one corner
        # of the top and one of the base are knocked out of step, which is what
        # gives a knitted pom its fuzzy edge without losing the round read.
        "art": {
            "front": [".ddc", "dfed", "cdc."],
            "left":  [".ddc", "dfed", "cdc."],
            "back":  [".ddc", "deed", "cdc."],
        },
        "description": "a soft pom sitting on the crown of a knitted cap",
    },
    {
        "name": "cuff_stripe",
        "motif_class": "band",
        "slot": "HEAD", "zone": "cuff", "z": 2,
        "style": ["casual", "work", "cottagecore"],
        "views": ["front", "left", "back"],
        "fits": ["knit_cap"],
        "art": ["dddddd"],
        "description": "a contrast stripe knitted into the cuff",
    },
    {
        "name": "brim_edge",
        "motif_class": "edge_accent",
        "edge": True,
        "slot": "HEAD", "zone": "brim", "z": 2,
        "style": ["formal", "festival", "cottagecore"],
        "views": ["front", "left"],
        "fits": ["felt_hat", "wide_brim_hat"],
        "art": ["cdddddddddddc"],
        "description": "a contrast edge run around the brim",
    },
    {
        "name": "collar_flat",
        "slot": "TOP", "attach": "neck", "z": 2,
        "style": ["work", "casual", "smart", "cottagecore"],
        "views": ["front", "left", "back"],
        "art": ["cddc"],
        "description": "a flat collar sitting across the shoulders",
    },
    {
        "name": "collar_pointed",
        "slot": "TOP", "attach": "neck", "z": 2,
        "style": ["formal", "smart"],
        "views": ["front", "back"],
        "art": ["cddc", ".cc."],
        "description": "a pointed collar with a short fall",
    },
    {
        "name": "buttons_placket",
        "slot": "TOP", "attach": "placket", "z": 3,
        "style": ["work", "smart", "formal"],
        "views": ["front"],
        "art": ["t", ".", "t", ".", "t"],
        "description": "a run of buttons down the centre front",
    },
    {
        "name": "pocket_patch",
        "slot": "TOP", "attach": "chest_left", "z": 2,
        "style": ["work", "casual"],
        "views": ["front"],
        "art": ["cc", "cc"],
        "description": "a patch pocket on the wearer's left chest",
    },
]


# =============================================================================
# PALETTES — curated harmonies, not rolled RGB
# =============================================================================
#
# Built from the 19 hand-picked stories in PALETTE_STORY_LIBRARY.json, which
# were authored as RELATIONSHIPS (a cloth, a structural dark, a bounded accent)
# rather than sampled.  Each story becomes three 6-step ramps by interpolating
# between its own anchor colours: no new hues are invented here, the ramp only
# fills in the values between colours the story already names.
#
# Style tags are assigned per story from its stated identity, and they are what
# stops the combinator putting a neon cyber palette on a cottagecore shirt.

STYLE_BY_STORY = {
    "EVERYDAY_STONE_BLUE": ["work", "casual", "smart"],
    "COASTAL_SEAFOAM_CORAL": ["casual", "festival", "cottagecore"],
    "AUTUMN_OCHRE_PLUM": ["cottagecore", "casual", "work"],
    "SPRING_SAGE_PETAL": ["cottagecore", "festival"],
    "WINTER_FROST_INK": ["formal", "smart"],
    "FIELD_CANVAS_MOSS": ["work", "cottagecore"],
    "FORMAL_PEARL_MIDNIGHT": ["formal", "smart"],
    "LUXURY_JADE_BRONZE": ["formal", "festival"],
    "GOTHIC_WINE_ASH": ["formal", "festival"],
    "STREET_TEAL_GRAPHITE": ["casual", "smart"],
    "SAILOR_COBALT_CREAM": ["smart", "casual"],
    "CELESTIAL_INDIGO_STAR": ["festival", "formal"],
    "ARCANE_VIOLET_COPPER": ["festival", "formal"],
    "EMBER_SUN_CHARCOAL": ["work", "festival"],
    "CYBER_CYAN_MAGENTA": ["festival"],
    "CEREMONIAL_CRIMSON_IVORY": ["formal", "festival"],
    "PASTEL_PEACH_LILAC": ["cottagecore", "casual"],
    "WORKWEAR_DENIM_RUST": ["work", "casual"],
    "DESERT_CLAY_TURQUOISE": ["casual", "festival", "work"],
}


def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _at_luminance(c, target):
    """Push a colour to a target luminance, keeping its hue.

    Scaling toward black or toward white, which is what a pixel artist does
    when extending a ramp: the colour keeps its identity and only its value
    moves.
    """
    have = _lum(c)
    if target <= have:
        t = 0.0 if have <= 0 else target / have
        return tuple(round(v * t) for v in c)
    t = (target - have) / max(1.0, 255 - have)
    return tuple(round(v + (255 - v) * t) for v in c)


# The value ladder every curated ramp is held to.  Reference hats measure a
# luminance span of 157 and vanilla 176; a story whose own anchors sit close
# together (a pearl on a pearl) renders as one flat mass, which is exactly the
# blob the first authored batch produced on FORMAL_PEARL_MIDNIGHT.  Spreading
# the ladder does not invent hues — the story's colours keep their identity and
# only their values move.
RAMP_SPAN = 165.0
RAMP_FLOOR = 14.0


def _ramp(anchors):
    """Six steps through the story's own anchor colours, deep -> highlight."""
    if len(anchors) == 1:
        base = anchors[0]
        anchors = [_mix(base, (12, 10, 16), 0.65), base,
                   _mix(base, (255, 252, 244), 0.55)]
    out = []
    for i in range(STEPS):
        t = i / (STEPS - 1) * (len(anchors) - 1)
        lo = min(int(t), len(anchors) - 2)
        out.append(_mix(anchors[lo], anchors[lo + 1], t - lo))
    lo_l = min(_lum(c) for c in out)
    hi_l = max(_lum(c) for c in out)
    span = max(hi_l - lo_l, RAMP_SPAN)
    base_l = max(RAMP_FLOOR, min(lo_l, 255 - span))
    return [_at_luminance(c, base_l + span * i / (STEPS - 1))
            for i, c in enumerate(out)]


def palettes():
    with open(os.path.join(os.path.dirname(ROOT),
                           "PALETTE_STORY_LIBRARY.json")) as fh:
        src = json.load(fh)
    out = []
    for story in src["stories"]:
        r = story["roles"]
        body = _ramp([_hex(r["DeepShadow"]), _hex(r["StructuralDark"]),
                      _hex(r["PrimaryFabric"]), _hex(r["PrimaryLight"])])
        trim = _ramp([_hex(r["DeepShadow"]), _hex(r["Trim"]),
                      _hex(r.get("SecondaryFabric", r["PrimaryLight"]))])
        accent = _ramp([_hex(r["Accent"])])
        # The stories already name a metal (OptionalMetal); a story without one
        # gets a neutral steel, never a tint borrowed from its cloth — hardware
        # that drifts with the garment stops reading as metal.
        metal = _hex(r["OptionalMetal"]) if r.get("OptionalMetal") else (169, 176, 182)
        hardware = _ramp([metal])
        out.append({
            "id": story["id"],
            "identity": story["identity"],
            "relationship": story["relationship"],
            "style": STYLE_BY_STORY.get(story["id"], ["casual"]),
            "accent_budget": story.get("accentBudget", "low"),
            "ramps": {"body": ["#%02X%02X%02X" % c for c in body],
                      "trim": ["#%02X%02X%02X" % c for c in trim],
                      "accent": ["#%02X%02X%02X" % c for c in accent],
                      "hardware": ["#%02X%02X%02X" % c for c in hardware]},
        })
    return out


# =============================================================================

ZONE_KIND = {"felt_hat": "brimmed", "wide_brim_hat": "brimmed",
             "soft_cap": "cap", "knit_cap": "cuffed", "work_shirt": "cap"}


def cap_zones(cells_by_view: dict) -> dict:
    """The soft_cap's own zone vocabulary, derived per direction.

    A baseball cap is not a fedora with a shallower crown: it has a FRONT PANEL
    that carries one emblem, a TOP where a button sits, SIDE PANELS for small
    pins and tags, and a VISOR that takes an edge accent and nothing else.
    Naming those regions is what makes the compatibility policy enforceable by
    geometry rather than by a list of banned names — a hat band has nowhere to
    go on a cap because a cap has no band zone.

    Derived from the drawn cells per view, then clipped so every zone is made
    of cells the base actually draws.
    """
    out = {}
    for view, cells in cells_by_view.items():
        rows = _rows_of(cells)
        ys = sorted(rows)
        top = ys[0]
        # the LOWEST row at full width: a cap holds its width for several rows,
        # and the visor is at the bottom of that run, not the top of it
        span = max(rows[y][1] - rows[y][0] for y in ys)
        widest = max(y for y in ys if rows[y][1] - rows[y][0] == span)
        bottom = ys[-1]
        z = {}
        # the apex: a button or a small bobble, nothing else
        tlo, thi = rows[top]
        z["top"] = [tlo, top, thi, min(top + 1, bottom)]
        if view == "back":
            # no visor behind, and the front panel is not visible
            mid = (top + widest) // 2
            mlo, mhi = rows[mid]
            z["side_panel"] = [mhi - 3, mid, mhi - 1, min(bottom - 1, mid + 1)]
        elif view == "front":
            # The panel the emblem goes on.  Inset two cells from the rim so a
            # motif reads as embroidered into the fabric rather than laid over
            # the seam, and stopped TWO rows above the visor so there is always
            # a band of plain cloth between emblem and visor — an emblem that
            # touches the visor reads as printed on the brim.
            # The panel is a feature of the CROWN, so it is measured from the
            # widest crown row — not from the widest row overall, which is the
            # visor once the visor projects past the crown as a real peak does.
            crown_row = max((y for y in ys if y < widest),
                            key=lambda y: (rows[y][1] - rows[y][0], y))
            plo, phi = rows[crown_row]
            z["front_panel"] = [plo + 2, top + 2, phi - 2, widest - 2]
            z["side_panel"] = [phi - 3, top + 3, phi - 1, widest - 2]
            # the visor is every row from the widest row down
            vlo, vhi = rows[widest]
            z["visor"] = [vlo, widest, vhi, bottom]
        else:
            # In profile the peak projects forward, to LOW x.  The visor is
            # exactly the part of the hat forward of the crown's own front
            # edge — derived, so it follows the art if the peak is redrawn.
            wlo, whi = rows[widest]
            crown_front = min(rows[y][0] for y in ys if y < widest)
            z["visor"] = [wlo, widest, crown_front - 1, bottom]
            # The front crown IS visible in profile, foreshortened into the
            # few columns just behind the peak.  An emblem placed here is the
            # view-specific compressed variant, not the full front emblem.
            z["front_panel"] = [crown_front, top + 2, crown_front + 3,
                                widest - 2]
            z["side_panel"] = [whi - 5, top + 2, whi - 1, widest - 2]
        clipped = {}
        for name, box in z.items():
            fixed = _clip_to_cells(box, cells)
            if fixed:
                clipped[name] = fixed
        out[view] = clipped
    return out


def cap_anchors(zones: dict, cells_by_view: dict) -> dict:
    """Cap anchor points, read back off the derived zones.

    An anchor is the top-left cell a decal starts at, so it is the middle of
    its zone biased up and left — and it must be a cell the base draws, which
    is guaranteed here because the zones were already clipped to drawn cells.
    """
    def mid(view, name):
        box = zones.get(view, {}).get(name)
        if not box:
            return None
        x0, y0, x1, y1 = box
        cell = ((x0 + x1) // 2, (y0 + y1) // 2)
        if cell in cells_by_view[view]:
            return list(cell)
        # fall back to the zone's own top-left, which is always drawn
        return [x0, y0]

    out = {}
    for name, zone in (("crown_top", "top"), ("crown_face", "front_panel"),
                       ("side_face", "side_panel"), ("peak_edge", "visor")):
        out[name] = {v: mid(v, zone) for v in ("front", "left", "back")}
    return out


def write_base(spec):
    d = os.path.join(ROOT, "bases", spec["name"])
    os.makedirs(d, exist_ok=True)
    w, h = spec["size"]
    cells_by_view = {}
    for view, art in spec["views"].items():
        rows = grid(art, w, h)
        write_rgba_png(os.path.join(d, f"{view}.png"), rows)
        cells_by_view[view] = {(x, y) for y, r in enumerate(rows)
                               for x, px in enumerate(r) if px[3] > 0}
    manifest = {k: v for k, v in spec.items() if k != "views"}
    if spec["name"] == "soft_cap":
        manifest["zones"] = cap_zones(cells_by_view)
        # Anchors are DERIVED from those zones, never typed in.  Every time the
        # cap art has been redrawn, a hand-written anchor has silently drifted
        # off the garment; a zone already knows where its own middle is.
        manifest["anchors"] = cap_anchors(manifest["zones"], cells_by_view)
    else:
        manifest["zones"] = zones_for(cells_by_view, ZONE_KIND.get(spec["name"], "cap"))
    manifest["views"] = ["front", "back", "left"]
    manifest["mirror"] = {"right": "left"}
    with open(os.path.join(d, "base.json"), "w") as fh:
        json.dump(manifest, fh, indent=2)


def write_decal(spec):
    """A motif's art is either one grid for every view, or one per view.

    An ATTACHMENT needs per-view art: a feather that rises to the right in the
    front frame sweeps backward in profile, and drawing one shape for both is
    how you get a feather that points into the wearer's face.
    """
    d = os.path.join(ROOT, "decals")
    os.makedirs(d, exist_ok=True)
    art = spec["art"]
    manifest = {k: v for k, v in spec.items() if k != "art"}
    if isinstance(art, dict):
        sizes = {}
        for view, rows in art.items():
            w = max(len(r) for r in rows)
            write_rgba_png(os.path.join(d, f"{spec['name']}_{view}.png"),
                           grid(rows, w, len(rows)))
            sizes[view] = [w, len(rows)]
        manifest["per_view"] = True
        manifest["size"] = sizes[spec["views"][0]]
        manifest["sizes"] = sizes
    else:
        w = max(len(r) for r in art)
        write_rgba_png(os.path.join(d, f"{spec['name']}.png"), grid(art, w, len(art)))
        manifest["per_view"] = False
        manifest["size"] = [w, len(art)]
    with open(os.path.join(d, f"{spec['name']}.json"), "w") as fh:
        json.dump(manifest, fh, indent=2)


def main():
    for base in (HAT_BASE, WIDE_BASE, CAP_BASE, KNIT_BASE, SHIRT_BASE):
        write_base(base)
    for decal in DECALS:
        write_decal(decal)
    os.makedirs(ROOT, exist_ok=True)
    with open(os.path.join(ROOT, "palettes.json"), "w") as fh:
        json.dump({"source": "PALETTE_STORY_LIBRARY.json",
                   "steps": STEPS, "palettes": palettes()}, fh, indent=2)
    index = {"steps": STEPS,
             "roles": {"body": ["#%02X%02X%02X" % c for c in BODY],
                       "trim": ["#%02X%02X%02X" % c for c in TRIM],
                       "accent": ["#%02X%02X%02X" % c for c in ACCENT],
                       "hardware": ["#%02X%02X%02X" % c for c in HARDWARE]}}
    with open(os.path.join(ROOT, "index.json"), "w") as fh:
        json.dump(index, fh, indent=2)
    print(f"wrote {ROOT}")


if __name__ == "__main__":
    main()
