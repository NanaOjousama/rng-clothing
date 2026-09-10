"""TIER 0 — GRAMMAR.  Zero design RNG.

Layered exactly as the canonical architecture asks:

    CORE GARMENT GRAMMAR  +  RENDER-CLASS GRAMMAR  +  FASHION SENSE EXPORT CONTRACT

Grammar owns: envelope semantics, landmarks, semantic zones, occupancy modes,
palette/ramp capability, base lighting, edge semantics, occlusion composition,
projection/wrap semantics, legibility constraints, and the export contract.
Nothing here is ever rolled.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# CORE GARMENT GRAMMAR
# ---------------------------------------------------------------------------

VIEWS = ("front", "side", "back")                 # authored views
DIRECTIONS = ("front", "right", "back", "left")   # runtime directions
ATLAS_ORDER = ("front", "right", "left", "back")  # Fashion Sense stacking


@dataclass(frozen=True)
class Envelope:
    """Frame extent is a first-class capability (canonical section 4)."""
    width: int = 8
    height: int = 8
    scale: float = 4.0
    body_position: tuple[int, int] = (0, 0)
    # optional directional overrides, e.g. {"right": (0, 1)}
    direction_body_position: tuple[tuple[str, tuple[int, int]], ...] = ()

    def bp_for(self, direction: str) -> tuple[int, int]:
        for d, bp in self.direction_body_position:
            if d == direction:
                return bp
        return self.body_position

    def inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    @property
    def atlas(self) -> tuple[int, int]:
        return self.width, self.height * len(ATLAS_ORDER)


STANDARD_ENVELOPE = Envelope()          # 8x8 @ Scale 4, the corpus-dominant target

# --- HATS -------------------------------------------------------------------
#
# Native 20x20 @ Scale 4, matching vanilla `Characters/Farmer/hats.png`
# (240x880, 20x20 frames, four directions stacked per 20x80 block, 12 per row).
# At width 20 / Scale 4 the Fashion Sense HeadPosition.X that centres the frame
# on the head is exactly 0 — verified across 746 shipping FS hat models, where
# X correlates with frame width as (w - 20*(4/Scale)) / 2:
#   width 20 -> 0 (192/204), 16 -> -2 (382), 32@2.0 -> -4 (64/64), 24@2.0 -> -8.
HAT_ENVELOPE = Envelope(width=20, height=20, scale=4.0)

# The region of the frame the head actually occupies, as (x0, x1, y0, y1)
# inclusive.  Derived from per-row / per-column occupancy over all 120 vanilla
# hats: columns 5-14 are covered by 95-100% of hats and rows 4-12 by 79-95%,
# with sharp falloff outside both.  Everything a hat draws registers to this
# box; it is a Grammar constant and is never rolled.
HEAD_BOX = (5, 14, 4, 12)

# Measured bounds for the BRIMMED subset: 74 of the 120 vanilla hats, where
# "brimmed" is crown_metrics()["brim_ratio"] > 1.15.  (p05, p95) — QC ranges,
# not domains.  Produced by running the helpers at the bottom of this module
# over hats.png; `VanillaHatCorpus` re-derives them at test time so they cannot
# drift from the corpus or from the helper that defines them.
HAT_BRIMMED_BOUNDS = {
    "cells": (24, 149),          # median 108 of 400 -> 27% occupancy
    "bbox_w": (10, 18),
    "bbox_h": (5, 16),
    "crown_top": (0, 6),
    "brim_line": (7, 13),        # the widest row
    "brim_width": (7, 18),
    "crown_height": (2, 10),
    "crown_width": (5, 12),
    "overhang": (0, 4),          # per side, outside HEAD_BOX
    "colors": (5, 10),           # median 7 distinct colours
}

# How far a side-view brim may lean forward, in cells.
#
# Measured on the 74 vanilla brimmed hats, taking each side frame's brim reach
# about its own CROWN centre: the front:back ratio has a median of 1.00, 45 of
# 73 reach EXACTLY equally in both directions, 65 of 73 are within one cell,
# and the side brim's total width matches the front view's (both median 14).
# The crown centre sits at the frame centre (offset 0.00).
#
# So a side brim is SYMMETRIC about the crown.  The deviations are not a
# forward perspective lean either: they run backward more often than forward
# (15 hats at -1 against 5 at +1) and correlate with nothing measurable, so
# there is no rule to derive.  An earlier 1:3 front:back split was invented
# rather than measured and read as one side having been cut short.  Directional
# asymmetry belongs to an Architecture or motif that explicitly justifies it —
# a swept brim, a front emblem — not to ordinary brimmed hats.
HAT_SIDE_BRIM_SKEW = 0

# What DOES differ in profile.  Front and side frames disagree on 31% of their
# mask, but every gross parameter matches at the median — crown height, crown
# width, brim width and crown top all delta 0.  The single consistent
# difference is that the brim line sits one row higher in profile (delta -1),
# which is why the side frame also carries slightly less mass (99.5 vs 108).
HAT_SIDE_BRIM_RISE = 1

# --- the BACK frame is DERIVED, not authored ---------------------------------
#
# Measured over the 112 vanilla hats with mass in all four frames:
#
#     back top row    front + 1   (p10 0, p90 2)
#     back bottom row front + 2   (p10 -1, p90 3)
#     back cells      front + 10  (p10 -12, p90 28)
#
# Exactly 1 of 112 draws the back as a copy of the front, so "same crown, plus
# a stub below the brim line" — what this generator did — is not what vanilla
# does.  The rule that reproduces all three medians at once is simpler: the
# back is the SAME hat, drawn one row lower, with its lowest row repeated once.
# Seen from behind the head is a little further away and a little below the
# camera, so the hat rides down the frame and you see more of its underside.
#
# Deriving it rather than authoring it also removes a whole class of bug: the
# back frame can no longer disagree with the front about anything, because it
# is a function of the front.  Zero design entropy, like Projection itself.
HAT_BACK_DROP = 1
HAT_BACK_EXTEND = 1

# --- vertical seating on the head: MEASURED, AND NO CORRECTION IS NEEDED ----
#
# A first pass concluded our hats render two sprite pixels higher on the head
# than vanilla ones and set this to -2.  That was WRONG, and the way it was
# wrong is worth keeping: the vanilla captures came from one game session and
# ours from another, and a restart moves the farmer and redraws the hair, which
# shifted every offset by a pixel.
#
# Re-measured inside a SINGLE session, 22 vanilla hats against 24 of ours:
#
#     (rendered hat top, relative to the head) minus (the hat's own top row
#      inside its 20x20 frame)
#         vanilla  -4.00   (p10 -6, p90 -3)
#         ours     -4.00   (p10 -4, p90 -4)
#
# Identical.  Fashion Sense draws a custom hat exactly where vanilla draws a
# vanilla one, and every worn-fit metric — seating, floating, face intrusion,
# turn stability — sits inside the vanilla range on a like-for-like capture.
#
# So placement is NOT the defect, and this stays at zero.  The rule that came
# out of it: a before/after or a cross-group comparison must come from ONE game
# session, or it is measuring the session.
HAT_HEAD_POSITION_Y = 0


def back_view(front: set, env: Envelope, extend: bool = False) -> set:
    """The back frame for one piece, derived from its front frame."""
    if not front:
        return set()
    out = {(x, y + HAT_BACK_DROP) for (x, y) in front
           if y + HAT_BACK_DROP < env.height}
    if extend:
        bottom = max(y for _, y in front)
        for i in range(1, HAT_BACK_EXTEND + 1):
            row = bottom + HAT_BACK_DROP + i
            if row < env.height:
                out |= {(x, row) for (x, y) in front if y == bottom}
    return out

# Measured bounds for the BRIMLESS subset: 59 of the 188 shipping hats whose
# crown is no narrower than 1.15x its widest row — caps, beanies, crown-only
# headwear.  Same envelope as the brimmed group, which is why BRIMLESS_HAT
# reuses HEAD_BOX and the placement model unchanged.
HAT_BRIMLESS_BOUNDS = {
    "cells": (52, 166),          # median 107
    "bbox_w": (10, 18),          # median 14
    "bbox_h": (5, 14),           # median 11
    "crown_top": (0, 7),         # median 4
    "bottom_row": (10, 18),      # median 12
    "crown_width": (10, 16),     # median 14
    "fill_ratio": 0.78,          # median; a cap is not a solid block
}

# Per-direction mass, medians over the same 74 hats.  Only 28 of 120 vanilla
# hats start on the same row in all four directions, so vertical placement is
# per-direction, not one envelope for all views.  The back carries the most
# mass and reaches lowest (it covers the back of the head).
HAT_DIRECTION_PROFILE = {
    "front": {"top_row": 3, "cells": 108},
    "right": {"top_row": 3, "cells": 100},
    "left":  {"top_row": 3, "cells": 100},
    "back":  {"top_row": 4, "cells": 118},
}


def head_box(env: Envelope) -> tuple[int, int, int, int]:
    """HEAD_BOX for an envelope; only the authored 20x20 hat frame is defined."""
    if (env.width, env.height) != (20, 20):
        raise ValueError(
            f"no authored head box for {env.width}x{env.height}; "
            f"hats are authored at 20x20 (see HAT_ENVELOPE)")
    return HEAD_BOX


# --- named landmarks, resolved against an envelope --------------------------

def landmarks(env: Envelope) -> dict[str, int]:
    """Envelope-relative rows/columns. Never hardcoded downstream."""
    return {
        "neck_row": 0,
        "shoulder_row": 1,
        "chest_row": env.height // 2 - 1,
        "waist_row": env.height - 3,
        "hem_row": env.height - 1,
        "center_left": env.width // 2 - 1,
        "center_right": env.width // 2,
        "left_edge": 0,
        "right_edge": env.width - 1,
    }


# --- semantic spatial zones (canonical section 19) --------------------------

ZONES = (
    "collar:center",
    "chest:left", "chest:center", "chest:right",
    "midriff:center",
    "waist:girth",
    "hip:left", "hip:right",
    "hem:girth",
)

# occupancy claim modes
EXCLUSIVE = "exclusive"
CONDITIONAL_SHARE = "conditional_share"
OVERLAY = "overlay"
CLAIM_MODES = (EXCLUSIVE, CONDITIONAL_SHARE, OVERLAY)


# --- palette / ramp capability (canonical sections 23, 24) ------------------
#
# The canonical role list mixes two orthogonal axes. See the implementation
# report: we treat a FABRIC ROLE (which cloth) and a RAMP STEP (which value)
# as separate axes rather than one flat enum, which is the smallest change
# that makes section 23 and section 35 ("occlusion modifies ramp indices")
# consistent.

FABRIC_ROLES = ("body", "trim", "accent", "secondary_accent", "hardware", "under_layer")
RAMP_STEPS = ("deep", "shadow", "mid", "base", "light", "highlight")
MIN_RAMP_DEPTH, MAX_RAMP_DEPTH = 4, 6   # corpus: commonly 4-6 steps

# corpus capability targets (distribution guidance, never quotas)
COLOR_TARGET_MEDIAN = 10
COLOR_TARGET_P90 = 17
COLOR_HARD_CEILING = 24


# --- base lighting is Grammar (canonical section 35) ------------------------
#
# Two shading models exist.  Which one a garment gets is a RENDER-CLASS law, not
# a design choice, so it is selected here and never rolled.
#
#   "directional"  light from screen upper-left, three coarse bands.
#   "form"         value follows FORM: each semantic region ramps from a darker
#                  boundary to a lighter interior, mirrored about the centre
#                  column.  Measured against 19 hand-authored 8x8 sailor tops:
#                  left/right symmetry 0.98, and the outer border sits ~34
#                  luminance darker than the interior in 17 of 19.  A directional
#                  gradient cannot produce either number.

RENDER_CLASS_SHADING = {"torso_8x8": "form", "head_20x20": "form"}
DEFAULT_SHADING = "directional"

# Whether a render class carries a darker border around its whole silhouette.
#
# This is NOT a stylistic preference, it is a measured difference between the
# two corpora.  Of 120 vanilla hats, 117 have a border darker than their own
# interior (median -59 luminance).  Shirts do the opposite: V5 asserts and
# tests that there is no global dark outline, because a torso reads as part of
# the body.  A hat is a separate object sitting on the head, and the corpus
# outlines it.  Keep this keyed by render class so neither rule leaks.
RENDER_CLASS_OUTLINE = {"torso_8x8": False, "head_20x20": True}

# Which way a form-shaded region ramps, and how much of it may reach the light.
#
#   "stacked"  a torso: the top of a mass reads darker and the bottom lighter,
#              which is how stacked 8x8 masses separate from one another.
#   "domed"    a hat: it is a lit OBJECT sitting on the head.  The crown top
#              catches the light and the underside of the crown, where it meets
#              the brim, is the darkest part.  Stacked shading on a hat puts a
#              pale band all the way round the bottom of the crown, which is
#              exactly the "vase" read the user reported.
RENDER_CLASS_LIGHT_MODEL = {"torso_8x8": "stacked", "head_20x20": "domed"}

# Whether a render class spends a highlight BUDGET rather than lighting every
# cell the form model calls lit.  Measured on the front frame: 120 vanilla hats
# put 6.9% of the sprite within 12 luminance of their brightest pixel and the
# four hats the user picked as good put 5.2% there; ours put 20.5%.  A hat
# highlight is a small hard patch on the lit shoulder of the crown, not a band.
# The torso does NOT budget: a shirt's lit region IS the mass separation.
RENDER_CLASS_HIGHLIGHT_BUDGET = {"torso_8x8": False, "head_20x20": True}

def base_lighting(mask: set[tuple[int, int]], env: Envelope) -> dict[tuple[int, int], int]:
    """Deterministic base illumination for a render class.

    Returns a ramp-step INDEX offset per cell, relative to a fabric's `base`
    step: -1 lighter, 0 base, +1 shadow, +2 deep.  Garments may not author
    arbitrary global gradients; they may only add declared local occlusion.

    Light comes from screen upper-left, which is the vanilla and corpus
    convention.  Kept deliberately coarse: at 8x8 a three-band field is all
    that reads.
    """
    if not mask:
        return {}
    field: dict[tuple[int, int], int] = {}
    xs = [c[0] for c in mask]
    lo, hi = min(xs), max(xs)
    span = max(1, hi - lo)
    for (x, y) in mask:
        fx = (x - lo) / span
        fy = y / max(1, env.height - 1)
        if fx <= 0.34 and fy <= 0.55:
            step = -1                     # upper-left catch light
        elif fx >= 0.75 or fy >= 0.86:
            step = 1                      # shadow side and underside
        else:
            step = 0
        field[(x, y)] = step
    return field


def form_lighting(silhouette: set, regions: dict, env: Envelope,
                  *, forms: dict | None = None,
                  specular: tuple | None = None,
                  light_model: str = "stacked") -> dict[tuple[int, int], int]:
    """Form shading: value follows each region's own form, not a light source.

    Two components, both symmetric about the centre column:

      vertical   within a region, the top reads darker and the bottom lighter,
                 which is how a hand-drawn 8x8 torso separates stacked masses.
      lateral    a cell on the left or right edge of its own region takes one
                 further shadow step, so every mass gets a drawn border.

    Returns a ramp-step offset per cell: positive is darker.  Measured against
    19 hand-authored sailor tops: left/right symmetry 0.98, and the outer border
    sits ~34 luminance darker than the interior in 17 of 19.  `specular`, if
    given, is the one cell allowed to break symmetry with a highlight.
    """
    if not silhouette:
        return {}
    by_region: dict[object, list] = {}
    for cell in silhouette:
        by_region.setdefault(regions.get(cell), []).append(cell)

    forms = forms or {}
    field: dict[tuple[int, int], int] = {}
    centre = (env.width - 1) / 2.0
    for key, cells in by_region.items():
        own = set(cells)
        rows = sorted({y for _, y in cells})
        span = len(rows)
        knot = forms.get(key) == "knot"
        for (x, y) in cells:
            i = rows.index(y)
            if span == 1:
                v = 0
            elif span == 2:
                v = 1 if i == 0 else 0
            else:
                t = i / (span - 1)
                v = 1 if t < 0.34 else (0 if t < 0.67 else -1)
            if light_model == "domed":
                # A dome is lit on top and darkest where it turns under.
                v = -v
            if knot:
                # a knot is lit on top and shaded into its centre
                v = -v
                lateral = 1 if abs(x - centre) < 1.0 else 0
            else:
                lateral = 1 if ((x + 1, y) not in own or (x - 1, y) not in own) else 0
            field[(x, y)] = max(-2, min(2, v + lateral))

    # Symmetrise explicitly: the result must read as drawn, not as lit.
    for (x, y) in list(field):
        mirror = (env.width - 1 - x, y)
        if mirror in field:
            v = field[(x, y)] if x <= mirror[0] else field[mirror]
            field[(x, y)] = field[mirror] = v
    if specular is not None and specular in field:
        field[specular] -= 1
    return field


# --- edge semantics (canonical section 33) ----------------------------------

ATTACHED = "attached"
FREE = "free"
EDGE_KINDS = (ATTACHED, FREE)


# --- occlusion composition (canonical section 35) ---------------------------

def compose_occlusion(stamps: list[dict[tuple[int, int], int]]) -> dict[tuple[int, int], int]:
    """Multiple declared shadow stamps compose by MAX, never by addition."""
    out: dict[tuple[int, int], int] = {}
    for stamp in stamps:
        for cell, depth in stamp.items():
            if depth > out.get(cell, 0):
                out[cell] = depth
    return out


# --- wrap semantics (canonical section 38) ----------------------------------

GIRTH = "girth"   # may continue through front/side/back
PLANE = "plane"   # local; does not automatically wrap
WRAP_MODES = (GIRTH, PLANE)


# --- legibility constraints -------------------------------------------------
#
# Calibration from the modded corpus, not eternal law (canonical section 34).
# 8,476 measured non-dominant regions: median 2 cells at 84 luminance contrast,
# p25 at 39.  Contrast is the gate; area is close to irrelevant at 8x8.

SEPARATION_SUFFICIENT = 45.0   # above this, adjacent regions need no outline
IDENTITY_CONTRAST_FLOOR = 38.0  # below this an identity feature is not reading


def luminance(rgba) -> float:
    return 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]


def perceptual_distance(a, b) -> float:
    """Separation between two colours, value AND chroma.

    Value alone is the right measure for edge treatment — an outline works by
    value — but it badly under-reads a saturated tie against a saturated ground:
    a red bow on a dark purple shirt is unmistakable to the eye and nearly
    identical in luminance.  Cheap opponent-channel terms fix that without
    pulling a colour-space library in.
    """
    dl = luminance(a) - luminance(b)
    rg = (a[0] - a[1]) - (b[0] - b[1])
    yb = ((a[0] + a[1]) / 2 - a[2]) - ((b[0] + b[1]) / 2 - b[2])
    return (dl * dl + (0.55 * rg) ** 2 + (0.55 * yb) ** 2) ** 0.5


# ---------------------------------------------------------------------------
# FASHION SENSE EXPORT CONTRACT
# ---------------------------------------------------------------------------

FS_FORMAT = "7.5.0"
FS_DISABLE_GRAYSCALE = True
FS_SLEEVE_STEPS = ("shadow", "base", "light")   # three colours, dark -> light
FS_HIDE_SLEEVES_DEFAULT = False                 # native Farmer sleeves


def required_coverage(env: Envelope) -> dict[str, list[str]]:
    """Shoulder rows that must stay opaque or the Farmer shows skin.

    Measured, not assumed: the intersection of 38 shipping hand-authored 8x8
    sailor frames (19 garments x male/female sheets).  The earlier figure was
    traced from the vanilla plain shirt and was far too strict — it forced a
    solid bar across row 1, which is exactly the block-assembled look we are
    trying to lose.  In the reference corpus row 1 columns 3-4 are opaque in
    only 5% of frames, and row 0 columns 2 and 5 in only 42%: a two-row neck
    opening is the norm and a notched shoulder line is common.
    """
    if (env.width, env.height) != (8, 8):
        top = required_coverage(STANDARD_ENVELOPE)
        pad = "." * max(0, env.width - 8)
        return {k: [r + pad for r in v] for k, v in top.items()}
    return {
        "front": ["##....##", "###..###"],
        "side":  ["###.##..", "####.##."],
        "back":  ["########", "########"],
    }


# ---------------------------------------------------------------------------
# DECORATIVE LINE TERMINATION
# ---------------------------------------------------------------------------
#
# A general 8x8 sprite rule, confirmed independently by three motifs (hem_band,
# the MIDDY waistband, and horizontal stripes): any decorative line or band
# whose run ENDS on the silhouette boundary should end one cell inboard
# instead.  The garment boundary is where the Farmer's arm and body edge are
# drawn, so a line terminating exactly there reads as passing through the
# figure rather than as part of the shirt.
#
# This is for DECORATIVE linework only.  It must NOT be applied to structural
# panels, seams, outlines, or any motif whose job is to define the garment
# edge — for those the boundary is the point.

LINE_MIN_RUN = 4        # cells a run needs before it can afford two endpoints


def terminate_inboard(cells: set, run_axis: int,
                      min_run: int = LINE_MIN_RUN) -> set:
    """Pull a decorative line's endpoints one cell back from the boundary.

    `run_axis` is the axis the line TRAVELS along: 0 for a horizontal line
    (constant y, varying x), 1 for a vertical one.  Cells are grouped by the
    other axis and the outermost cell at each end of every group is dropped.

    The min_run guard is the point of the helper.  Insetting a short run would
    erase the pattern rather than soften it — the same class of failure as a
    period whose values all fail readability, which silently dropped Surface
    and crashed continuity.  A run shorter than `min_run` is returned intact.
    """
    if run_axis not in (0, 1):
        raise ValueError(f"run_axis must be 0 or 1, got {run_axis}")
    group_axis = 1 - run_axis
    runs: dict[int, set] = {}
    for cell in cells:
        runs.setdefault(cell[group_axis], set()).add(cell[run_axis])
    out = set()
    for group, values in runs.items():
        if len(values) >= min_run:
            values = values - {min(values), max(values)}
        for v in values:
            out.add((v, group) if run_axis == 0 else (group, v))
    return out


# ---------------------------------------------------------------------------
# HAT GEOMETRY  (shared by the Architecture, QC and the corpus tests)
# ---------------------------------------------------------------------------
#
# A hat is a small object in a mostly-empty frame, so its measurable properties
# are placement properties.  These are pure functions over a cell set so the
# same code measures the vanilla corpus and our own output — the constants
# above were produced by running them over `hats.png`.

def occupied_bbox(cells: set) -> tuple[int, int, int, int]:
    """(x0, x1, y0, y1) inclusive of the occupied mass."""
    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    return min(xs), max(xs), min(ys), max(ys)


def row_widths(cells: set) -> dict[int, int]:
    out: dict[int, int] = {}
    for _, y in cells:
        out[y] = out.get(y, 0) + 1
    return out


def brim_line(cells: set) -> int:
    """The widest row.  Ties resolve downward — a brim sits below its crown."""
    w = row_widths(cells)
    return max(w, key=lambda y: (w[y], y))


def crown_metrics(cells: set) -> dict:
    """Crown/brim split, measured the same way as the vanilla corpus."""
    w = row_widths(cells)
    brim = brim_line(cells)
    above = [w[y] for y in sorted(w) if y < brim]
    crown_w = sorted(above)[len(above) // 2] if above else w[brim]
    top = min(y for _, y in cells)
    return {
        "brim_line": brim,
        "brim_width": w[brim],
        "crown_top": top,
        "crown_height": brim - top,
        "crown_width": crown_w,
        "brim_ratio": w[brim] / crown_w if crown_w else 1.0,
    }


def enclosed_holes(cells: set, env: Envelope) -> set:
    """Transparent cells walled in on all four sides by the object."""
    return {(x, y)
            for y in range(env.height) for x in range(env.width)
            if (x, y) not in cells
            and any((i, y) in cells for i in range(0, x))
            and any((i, y) in cells for i in range(x + 1, env.width))
            and any((x, j) in cells for j in range(0, y))
            and any((x, j) in cells for j in range(y + 1, env.height))}


def overhang(cells: set, box: tuple[int, int, int, int]) -> tuple[int, int]:
    """Columns occupied outside the head box, (left, right)."""
    x0, x1, _, _ = box
    xs = [x for x, _ in cells]
    return max(0, x0 - min(xs)), max(0, max(xs) - x1)


def mirror_symmetry(cells: set, env: Envelope) -> float:
    """Fraction of cells whose horizontal mirror is also occupied."""
    if not cells:
        return 1.0
    return sum(1 for (x, y) in cells
               if (env.width - 1 - x, y) in cells) / len(cells)


def outline_delta(raster: dict) -> float:
    """Median border luminance minus median interior luminance.

    Negative means the object is outlined.  117 of 120 vanilla hats are.
    """
    cells = set(raster)
    border = [c for c in cells
              if any((c[0] + dx, c[1] + dy) not in cells
                     for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    inner = [c for c in cells if c not in border]
    if not border or not inner:
        return 0.0
    med = lambda v: sorted(v)[len(v) // 2]
    return (med([luminance(raster[c]) for c in border])
            - med([luminance(raster[c]) for c in inner]))
