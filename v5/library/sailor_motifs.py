"""SAILOR STRUCTURAL ASSET LIBRARY (canonical section 46, domain 8).

Authored motifs shared by every SAILOR_TOP Architecture.  The reference sheets
present the sailor as a mix-and-match kit — any collar with any tie with any
flap edge — so these live in one place and are opened through layer slots
rather than duplicated per Architecture.

Every motif is (cells, shading) as offsets from a declared anchor, so an
Architecture only has to say WHERE its tie hangs, not what a tie looks like.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# TIE / BOW LIBRARY  (reference section 3: T1-T8)
# ---------------------------------------------------------------------------
#
# Anchored at (centre-left column, anchor row) and growing downward.  dx is
# measured from the centre pair, so dx=-1 and dx=0 are the two middle columns.
#
# Shading follows the bows in the shipping corpus: lit on the upper fold, dark
# in the knot, darkest at the tails.  T8 "None" is not a value — the variable is
# simply never instantiated (INV-03).

TIE_LIBRARY = {
    # T1 — the standard neckerchief: small knot, two splayed tails
    "STANDARD_KNOT": {
        "cells": ((-1, 0), (0, 0), (-1, 1), (0, 1), (-2, 2), (1, 2)),
        "shading": {(-1, 0): -1, (0, 0): -1, (-1, 1): 1, (0, 1): 1,
                    (-2, 2): 2, (1, 2): 2},
    },
    # T2 — short knot, sits close under the collar point
    "SHORT_KNOT": {
        "cells": ((-1, 0), (0, 0), (-1, 1), (0, 1)),
        "shading": {(-1, 0): -1, (0, 0): -1, (-1, 1): 1, (0, 1): 1},
    },
    # T3 — long tie running down the chest
    "LONG_TIE": {
        "cells": ((-1, 0), (0, 0), (-1, 1), (0, 1), (-1, 2), (0, 2), (-1, 3), (0, 3)),
        "shading": {(-1, 0): -1, (0, 0): -1, (-1, 1): 0, (0, 1): 0,
                    (-1, 2): 1, (0, 2): 1, (-1, 3): 2, (0, 3): 2},
    },
    # T4 — large bow: six across, knot gap authored rather than shaded
    "LARGE_BOW": {
        "cells": ((-3, 0), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),
                  (-3, 1), (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1),
                  (-3, 2), (-2, 2), (1, 2), (2, 2)),
        "shading": {(-3, 0): 0, (-2, 0): -1, (-1, 0): 1, (0, 0): 1, (1, 0): -1, (2, 0): 0,
                    (-3, 1): 1, (-2, 1): 0, (-1, 1): 2, (0, 1): 2, (1, 1): 0, (2, 1): 1,
                    (-3, 2): 2, (-2, 2): 1, (1, 2): 1, (2, 2): 2},
        "gap": ((-1, 2), (0, 2)),
    },
    # T5 — double bow: two loops either side of a tight knot
    "DOUBLE_BOW": {
        "cells": ((-3, 0), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),
                  (-3, 1), (-2, 1), (1, 1), (2, 1),
                  (-3, 2), (2, 2)),
        "shading": {(-3, 0): 0, (-2, 0): -1, (-1, 0): 1, (0, 0): 1, (1, 0): -1, (2, 0): 0,
                    (-3, 1): 1, (-2, 1): 0, (1, 1): 0, (2, 1): 1,
                    (-3, 2): 2, (2, 2): 2},
        "gap": ((-1, 1), (0, 1), (-1, 2), (0, 2)),
    },
    # T6 — thin ribbon: a small flat bow, the quietest option that still reads
    "THIN_RIBBON": {
        "cells": ((-2, 0), (-1, 0), (0, 0), (1, 0), (-1, 1), (0, 1)),
        "shading": {(-2, 0): -1, (-1, 0): 1, (0, 0): 1, (1, 0): -1,
                    (-1, 1): 2, (0, 1): 2},
    },
    # T7 — cross tie
    "CROSS_TIE": {
        "cells": ((-2, 0), (1, 0), (-1, 1), (0, 1), (-2, 2), (1, 2)),
        "shading": {(-2, 0): -1, (1, 0): -1, (-1, 1): 1, (0, 1): 1,
                    (-2, 2): 0, (1, 2): 0},
    },
}

# How much vertical room each tie needs below its anchor.
TIE_EXTENT = {name: max(dy for _, dy in m["cells"]) + 1 for name, m in TIE_LIBRARY.items()}


def build_tie(name: str, anchor: tuple[int, int], silhouette: set):
    """Resolve a tie motif against an anchor.  Returns (cells, shading, gap)."""
    motif = TIE_LIBRARY[name]
    ax, ay = anchor
    cells, shading, gap = set(), {}, set()
    for dx, dy in motif["cells"]:
        cell = (ax + dx, ay + dy)
        if cell in silhouette:
            cells.add(cell)
            shading[cell] = motif["shading"][(dx, dy)]
    for dx, dy in motif.get("gap", ()):
        cell = (ax + dx, ay + dy)
        if cell in silhouette:
            gap.add(cell)
    return cells, shading, gap


# ---------------------------------------------------------------------------
# FLAP EDGE PROFILES  (reference section 4: F4 Rounded, F5 Pointed)
# ---------------------------------------------------------------------------
#
# The reference sheets vary the flap's OUTLINE, not its construction, so this is
# a cell-set transform on an authored piece rather than a separate piece.

FLAP_EDGES = ("SQUARE", "ROUNDED", "POINTED")

# How far the flap is inset from each side, per row from its top.  The flap is
# not a rectangle: it leaves the neck narrow and only reaches its full span once
# it is over the shoulders.  Authored as one profile shared by both
# Architectures, because both back frames are the same 8-wide shoulder line.
#
# Built as a rectangle it spanned six of eight columns for its whole depth with
# a straight hem, and in-game validation read the back as a horizontal bar laid
# across the shoulders rather than a collar hanging off them (013, 025, 040).
FLAP_NECK_INSET = 2
FLAP_BODY_INSET = 1
FLAP_HEM_INSET = 2


def flap_outline(depth: int, width: int = 8) -> set:
    """The authored flap footprint before its hem profile is carved."""
    return {(x, y)
            for y in range(depth)
            for x in range(_inset(y, depth), width - _inset(y, depth))}


def _inset(row: int, depth: int) -> int:
    """Narrow at the neck, full over the shoulders, drawn back in at the hem.

    Held at FLAP_BODY_INSET for its whole depth the flap was a straight-sided
    six-wide block whose outer columns ran down rows 2-4 — exactly where the
    Farmer's arms are drawn on the back frame.  In game that read as a
    horizontal bar across the shoulders (013, 025, 040) and, on a light flap
    over a dark shell, as two pale bars passing through the elbows (045).
    Tapering the hem rows ends the flap inboard of the arm.
    """
    if row == 0:
        return FLAP_NECK_INSET
    if depth >= 3 and row >= depth - (2 if depth >= 5 else 1):
        return FLAP_HEM_INSET
    return FLAP_BODY_INSET


def apply_flap_edge(cells: set, profile: str) -> set:
    """Carve an authored flap's bottom edge.  Never invents cells (INV-10).

    The curve runs over two rows where the flap is deep enough to spare them: a
    single row of corner cells is ~3% of the back frame and measured as no
    visual change at all.  On a shallow flap the two-row curve would consume
    every full-span row and hand back the rectangle it was carving away, so it
    is only taken when a full-span row still survives underneath the neck row.
    """
    if profile == "SQUARE" or not cells:
        return set(cells)
    bottom = max(y for _, y in cells)
    row = sorted(x for (x, y) in cells if y == bottom)
    if len(row) < 4:
        return set(cells)
    above = sorted(x for (x, y) in cells if y == bottom - 1)
    span = max(len(r) for r in (
        [x for (x, y) in cells if y == yy] for yy in {y for _, y in cells}))
    full_rows = sum(1 for yy in {y for _, y in cells}
                    if len([x for (x, y) in cells if y == yy]) == span)
    two_row = full_rows >= 3 and len(above) >= 6
    if profile == "ROUNDED":
        drop = {(row[0], bottom), (row[-1], bottom)}
    else:                                    # POINTED
        keep = set(row[len(row) // 2 - 1:len(row) // 2 + 1])
        drop = {(x, bottom) for x in row if x not in keep}
    if two_row:
        drop |= {(above[0], bottom - 1), (above[-1], bottom - 1)}
    return set(cells) - drop


def hem_shadow(cells: set, silhouette: set) -> dict:
    """Occlusion the flap casts on the fabric below its own shaped hem.

    Per column, not per row: taken off a nominal span it drew a straight line
    under a carved hem, which is what put a second hard band across the back.
    """
    out = {}
    for x in {c[0] for c in cells}:
        below = (x, max(y for (cx, y) in cells if cx == x) + 1)
        if below in silhouette and below not in cells:
            out[below] = 1
    return out


# ---------------------------------------------------------------------------
# SLEEVE CAP  (reference section 5: S1 Short vs S3 Puff)
# ---------------------------------------------------------------------------
#
# Sleeve LENGTH is not expressible in an 8x8 Fashion Sense shirt frame — the arm
# is the Farmer's own sprite, driven by SleeveColors.  What the shirt frame can
# say is how far the shoulder cap reaches inboard, so that is the only sleeve
# variable authored here.

# A puff cap cannot show as extra sleeve — the sleeve is the same fabric as the
# body — so what it actually changes is how far the under-layer articulation
# runs down the shoulder.
SLEEVE_CAPS = {"PLAIN": 1, "PUFF": 2}
