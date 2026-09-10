"""BRIMMED_HAT — the first HEAD-slot Architecture.

Geometry is derived from the 120 vanilla hats in `Characters/Farmer/hats.png`,
measured by the helpers in `v5.grammar` and frozen as `HAT_BRIMMED_BOUNDS` /
`HEAD_BOX` / `HAT_DIRECTION_PROFILE`.  74 of those 120 are brimmed (brim wider
than crown by more than 1.15x); this Architecture reproduces that subset.

What is deliberately different from the TOP slot:

  * Placement is the primitive.  A hat occupies a median 27% of its frame, so
    the question is where the object sits, not which cells are open.  Every
    piece is registered to HEAD_BOX.
  * No coverage obligation — the SlotContract declares it, and a small hat
    simply leaves the head visible.
  * Split rows are legal (82/120 vanilla hats have them); the shirt's
    one-span-per-row rule is not imported.
  * The silhouette is outlined, via RENDER_CLASS_OUTLINE["head_20x20"].
  * Identity is geometric, so the chromatic identity machinery is nearly
    unused: a hat rendered in mud is still a hat.
"""

from __future__ import annotations

from ..color import COLOR_ARCHITECTURES
from ..construction import Construction, Piece
from ..contracts import (ArchitectureContract, FamilyContract, IdentitySeparation,
                         register_architecture, register_family)
from ..grammar import (HAT_ENVELOPE, HAT_SIDE_BRIM_RISE, HAT_SIDE_BRIM_SKEW,
                       HEAD_BOX, PLANE,
                       Envelope, back_view, head_box, overhang,
                       terminate_inboard)
from ..material import MATERIALS
from ..schema import (APPEARANCE, IDENTITY, ORNAMENT, REPAIR_RETRY, STRUCTURAL,
                      Variable)
from . import hat_templates
from .hat_templates import TEMPLATES
from .hat_motifs import (DIRECTIONAL_MAX_CELLS, DIRECTIONAL_OPTIONS,
                         PROTRUSION_MAX_CELLS, PROTRUSIONS,
                         apply_protrusion, directional_cells,
                         directional_options, protrusion_options)

# ---------------------------------------------------------------------------
# authored profiles (INV-10: closed sets, never procedural silhouettes)
# ---------------------------------------------------------------------------
#
# Per-row inset from the nominal width, top row first.  The last entry repeats
# for any remaining rows, so a profile describes a shape rather than a height.

# Per-row inset from the widest row, top first.  These are the shape families
# that fall out of the 74 vanilla brimmed hats when each crown is reduced to
# its row-width profile — proportions derived from the corpus, not traced from
# it.  The PROFILE decides the crown height: a crown is an authored silhouette,
# not a rectangle with a height parameter.
#
#   ROUND      6 hats   the single commonest profile
#   DOMED      4        a slower shoulder
#   SHALLOW    2 + kin  low, quick taper — a cap
#   TALL_FLAT  4 + 3    narrow for several rows, then a hard flare (boater)
#   STOVEPIPE  2        very tall, straight-sided
#   PINCHED    3        a creased crown — the fedora read
#   STEPPED    2 + 2    a squared shoulder rather than a curve
CROWN_PROFILES = {
    # Bowler Hat #1 opens at 4 cells from a 14 base — an inset of 5.  Our
    # profiles stopped at 4, so every reconstruction came out with a 6-wide
    # apex and a blunter dome than the reference.
    "ROUND":     (5, 4, 3, 2, 2, 1, 0, 0),
    "DOMED":     (4, 3, 2, 2, 1, 1, 0, 0),
    "SHALLOW":   (3, 2, 1, 0, 0),
    # Both of these were authored too NARROW at the top and read as goblets.
    # Vanilla #2 is the real top hat: a constant 8-wide crown for seven rows
    # then a three-row flare into the brim, which is the corpus tuple used
    # verbatim below.  Mine held 6 of 14 (43%) where the reference holds 8 of
    # 14 (57%), and that difference is the whole chess-piece read.
    "TALL_FLAT": (3, 2, 2, 1, 0),
    "STOVEPIPE": (4, 3, 3, 3, 3, 3, 3, 1, 0, 0),
    "PINCHED":   (3, 1, 1, 2, 2, 2, 1, 1, 0, 0),
    "STEPPED":   (4, 4, 3, 2, 1, 0, 0),
    # --- profiles that need ODD rows (half-integer insets) -----------------
    # CONE: a tall narrow cone that flares late — witch, wizard, party, dunce.
    # The 5.5/5 alternation is the cone's edge stepping, not noise: it is what
    # keeps a 1-in-2 diagonal reading as a straight taper at this size.
    "CONE":      (5.5, 5, 5.5, 5, 5, 4, 2, 1, 0),
    # DROOP: a soft crown that swells, waists, then meets the brim — the
    # knitted/cloth family (santa, nightcap, slouch beanie).  Non-monotonic by
    # design: the inset goes 1.5 -> 1.0 -> 0.5 -> 1.0, which is the bulge.
    "DROOP":     (4.5, 3.5, 2.5, 1.5, 1.0, 0.5, 1.0, 1.0, 1.0, 0),
    # --- a crown that stays NARROW all the way to the brim -----------------
    # Every profile above opens to its full width before the brim line, which
    # is why BRIM_WINGS was unreachable: a wing has to sit outboard of the
    # crown ON THE BRIM'S OWN ROW, and there was never any daylight left there.
    # COLUMN is the missing shape rather than a special case for one hat: a
    # short straight-sided crown under a wide brim is the cowboy / gaucho /
    # sombrero / boater family, and vanilla #0 holds 8 cells across all four
    # of its crown rows before the brim flares to 18.
    "COLUMN":    (0, 0, 0, 0),
}

# Brim rows, widest first.  Same derivation: the row-width profile of the mass
# at and below each vanilla hat's brim line.  The top row is always the widest
# so the measured brim_line stays unambiguous.
#
#   TAPERED     8 hats  the commonest brim by a clear margin
#   DEEP_TAPER  4       a long droop
#   SHARP       4       falls away immediately — a thin brim seen edge-on
#   DIPPED      4       one full row then a sharp dip
#   STEPPED     3       full, full, then a hard step in
#   CURLED      3       curls up tight at the edge
#   FLOPPY      4       wide and slack, the deepest profile in the corpus
BRIM_PROFILES = {
    "TAPERED":    (0, 1, 2),
    "DEEP_TAPER": (0, 1, 2, 3, 4),
    "SHARP":      (0, 3),
    "DIPPED":     (0, 2, 5),
    "STEPPED":    (0, 1, 4),
    "CURLED":     (0, 3, 6),
    # SWEEP: four rows — a gentle taper that then drops away.  The vocabulary
    # had 2-row (SHARP), 3-row (TAPERED/DIPPED/STEPPED/CURLED) and 5-row
    # (DEEP_TAPER/FLOPPY, both retired) brims but nothing at 4, which is what
    # a wide sweeping brim needs.
    "SWEEP":      (0, 1, 2, 4),
    "FLOPPY":     (0, 1, 2, 4, 5),
    # ROLLED: full width for two rows, then rolling down and in.  The brim of
    # a wide-brimmed hat is a surface seen nearly edge-on, so it holds its
    # width and then falls away — unlike the tapers above, which start
    # narrowing immediately.  Five rows, so it is only legal on the crowns
    # that declare WIDE_BRIM_CROWNS.
    "ROLLED":     (0, 0, 1, 2, 4),
}


# Which side an odd row's extra cell falls on.  Constant per hat, so a hat with
# odd rows leans consistently instead of jittering row to row.
ODD_BIAS_LEFT = 1
ODD_BIAS_RIGHT = 0


def span(width: int, env: Envelope, odd_bias: int = ODD_BIAS_RIGHT) -> range:
    """Columns for a mass of `width`, centred on the frame.

    Vanilla centring is absolute for EVEN widths — bbox centre offset from the
    frame centre is 0.0 at both p10 and p90 across all 120 hats.  But vanilla
    also uses ODD widths freely (Witch 5/6/5, Santa 3/5/7/9/11), and an odd
    mass cannot sit exactly centred on a 20-wide frame: it lands half a pixel
    off.  Vanilla accepts that — Witch measures 0.95 symmetry, Santa 0.94.

    So odd widths are supported, and the half-pixel always falls on the same
    declared side.  An Architecture that never authors odd insets is unaffected
    and stays pixel-exact.
    """
    half = width // 2
    start = env.width // 2 - half
    if width % 2:
        start -= odd_bias
    return range(start, start + width)


def row_width(crown_width: int, inset: float) -> int:
    """A profile inset may be a half-integer, which yields an ODD row."""
    return int(round(crown_width - 2 * inset))


# ---------------------------------------------------------------------------
# CONTROLLED ASYMMETRY  (authored, closed-set, profile-scoped)
# ---------------------------------------------------------------------------
#
# Measured over the 67 vanilla brimmed hats with a real mass (>= 40 cells):
#
#   28% carry some asymmetry (19 of 67); the other 72% are exact mirrors
#   their symmetry score runs median 0.94, min 0.80 — mild, never wild
#   magnitude is median 6 unmirrored cells, p90 13
#   location is 59% crown top, 24% crown body, 17% brim
#   side bias runs about 2:1 to the LEFT
#
# So asymmetry is a garnish on a symmetric form, not an alternative to it.
# Symmetry stays the default; these motifs are a closed set, each authored as
# explicit cells at a named landmark, and each is scoped to the profile
# families whose shape can actually carry it.  There is no procedural jitter.

ASYM_LEFT, ASYM_RIGHT = "LEFT", "RIGHT"

# motif -> crown profiles that may carry it.  A profile absent from every entry
# stays strictly symmetric.
ASYMMETRY_SCOPE = {
    # the tip leans: needs a crown that tapers to a top worth leaning
    "TIP_LEAN":   ("ROUND", "DOMED", "PINCHED", "STOVEPIPE"),
    # DISABLED.  The plume is authored from vanilla #85's (2,3,2,1) profile and
    # the mechanism is sound, but at 20x20 the shape does not read as a feather
    # rising off the crown — and the invariants it must respect (brim ratio,
    # crown-width ceiling, mass) squeeze it to about 3 rolls in 200, so it adds
    # risk without adding variety.  Kept in the library, scoped to nothing.
    "SIDE_TUFT":  (),
    # a pressed dent in a broad top: needs a broad top
    "CROWN_DENT": ("TALL_FLAT", "STEPPED", "STOVEPIPE"),
    # the brim kicks up on one side: scoped by BRIM profile, see below
    "BRIM_FLICK": ("ROUND", "DOMED", "SHALLOW", "TALL_FLAT", "STEPPED",
                   "PINCHED", "STOVEPIPE"),
    # A PROGRESSIVE lean: the displacement grows toward the tip instead of
    # being the same on every row.  TIP_LEAN shifts up to three rows by one
    # column each, which slides a block sideways; a soft point does not do
    # that, it curves.  Vanilla's Witch #70 runs its tip centre 11, 10.5, 10
    # against a body centred on 9.5 — offsets of 2, 1, 1 — and Santa #25 does
    # the same in mirror.  Scoped to the crowns that have a point to droop.
    "TIP_DROOP": ("CONE", "DROOP", "STOVEPIPE"),
}

# Columns of displacement per row, TOP FIRST.  Authored from the two corpus
# examples above rather than computed from the crown height, so a tall cone and
# a short one droop by the same authored amount instead of one of them folding
# over.  The last entry does NOT repeat: rows past the end stay put.
DROOP_STEPS = (2, 1, 1)
# BRIM_FLICK additionally needs a brim with enough depth to show the kick
BRIM_FLICK_BRIMS = ("TAPERED", "DEEP_TAPER", "FLOPPY", "DIPPED")

# Plume widths per row, top first — vanilla #85's profile (2, 3, 2, 1).
# It needs a crown tall enough to rise along, so SIDE_TUFT also requires a
# profile of at least this many rows plus the apex it starts below.
SIDE_TUFT_WIDTHS = (2, 3, 2, 1)
SIDE_TUFT_MIN_CROWN = len(SIDE_TUFT_WIDTHS) + 1


SIDE_TUFT_CELLS = sum(SIDE_TUFT_WIDTHS)      # worst-case mass a plume adds


def tuft_has_headroom(crown_profile: str, crown_width: int,
                      brim_profile: str, brim_width: int) -> bool:
    """Whether a plume can be added without breaking the Architecture.

    A plume fills the crown's taper, which raises the MEDIAN crown row that
    `crown_metrics` reports — so the brim has to clear the crown's WIDEST row,
    not its median, or the 1.15x ratio that defines a brimmed hat collapses.
    It also adds mass the earlier estimate could not know about.
    """
    # The plume also pushes the reported median crown width up by a cell or
    # two as it fills the taper, so the crown must start with room under the
    # corpus ceiling of 12 rather than already sitting on it.
    return (brim_width >= crown_width + 3
            and crown_median_width(crown_profile, crown_width) <= 10
            and estimate_cells(crown_profile, crown_width,
                               brim_profile, brim_width) + SIDE_TUFT_CELLS <= 149)


def asymmetry_options(crown_profile: str, brim_profile: str) -> tuple:
    """The motifs this shape may carry.  Always includes NONE."""
    out = ["NONE"]
    for motif, profiles in ASYMMETRY_SCOPE.items():
        if crown_profile not in profiles:
            continue
        if motif == "BRIM_FLICK" and brim_profile not in BRIM_FLICK_BRIMS:
            continue
        if (motif == "SIDE_TUFT"
                and len(CROWN_PROFILES[crown_profile]) < SIDE_TUFT_MIN_CROWN):
            continue
        out.append(motif)
    return tuple(out)


def apply_asymmetry(motif: str, side: str, crown: dict, brim: dict,
                    crown_rows: dict, env) -> None:
    """Mutate the FRONT crown/brim in place.

    Side views are left alone: a profile already shows one side of the hat, so
    leaning it again would double-count the same displacement.  The BACK frame
    is not touched either — it is derived from the front once every motif has
    been applied (grammar.back_view), so a lean reaches it automatically and
    the two frames cannot drift apart."""
    if motif == "NONE" or not crown_rows:
        return
    sign = -1 if side == ASYM_LEFT else 1
    ys = sorted(crown_rows)
    top = ys[0]
    # A motif may never push the mass outside the corpus bbox (10, 18).
    existing = crown["front"] | brim["front"]
    xs = [x for x, _ in existing]
    lo_x, hi_x = min(xs), max(xs)

    def allowed(cx: int) -> bool:
        return (max(hi_x, cx) - min(lo_x, cx) + 1) <= 18

    # A plume FILLS THE TAPER: it may never make a crown row wider than the
    # crown's own widest row.  That is what the corpus does — #85 and #90 both
    # sit beside the narrow upper crown, occupying the space the taper vacates
    # — and it keeps two invariants safe at once.  `crown_metrics` finds the
    # brim line by taking the widest row, so a crown row that outgrew the brim
    # would move the measured brim line up into the crown and the hat would
    # stop reading as brimmed; and the median crown row would climb past the
    # 1.15x brim ratio that defines this Architecture.
    crown_max = max((len(cols) for cols in crown_rows.values()), default=0)

    def row_has_room(view: str, row: int) -> bool:
        # strictly BELOW the widest row, not up to it: filling a taper row all
        # the way to the crown's full width drags the median crown width that
        # `crown_metrics` reports past the corpus ceiling of 12
        return sum(1 for (_, yy) in crown[view] if yy == row) < crown_max - 1

    def edge(row, direction):
        cols = crown_rows.get(row)
        if not cols:
            return None
        return (cols.start if direction < 0 else cols.stop - 1)

    for view in ("front",):
        if motif == "TIP_DROOP":
            # Move the top rows by a DECREASING amount, so the silhouette
            # curves toward the lean instead of stepping over to it.  Rows are
            # rewritten top-down and each row's cells are taken from the
            # original crown, so the offsets cannot compound.
            for i, step in enumerate(DROOP_STEPS):
                if i >= len(ys):
                    break
                row = ys[i]
                cells = {c for c in crown[view] if c[1] == row}
                crown[view] -= cells
                crown[view] |= {(x + sign * step, y) for (x, y) in cells
                                if 0 <= x + sign * step < env.width
                                and allowed(x + sign * step)}
        elif motif == "TIP_LEAN":
            # Lean a FRACTION of the taper, never the whole of it.  A fixed
            # three rows is a third of a brimmed crown's taper — a lean — but
            # it is the ENTIRE dome of a brimless cap, which slides the whole
            # top sideways as a displaced block rather than tilting it.  That
            # is the "random chunk stuck on the hat" read.
            widest = max(len(c) for c in crown_rows.values())
            tapered = sum(1 for c in crown_rows.values() if len(c) < widest)
            lean_rows = max(1, min(3, tapered // 3))
            for row in ys[:lean_rows]:
                cells = {c for c in crown[view] if c[1] == row}
                crown[view] -= cells
                crown[view] |= {(x + sign, y) for (x, y) in cells
                                if 0 <= x + sign < env.width and allowed(x + sign)}
        elif motif == "SIDE_TUFT":
            # A plume RISING off the shoulder, not a nub beside it.
            #
            # Authored from the corpus rather than invented: vanilla #85 runs
            # widths 2,3,2,1 down its plume and #90 runs 3,3,2, both sitting in
            # the crown's UPPER half, widest near the top and tapering as they
            # descend, with every row hugging that row's own crown edge so the
            # mass reads as growing out of the hat.  The previous authoring put
            # three cells at a single row, level with the crown's side, which
            # read as a wart stuck on rather than a feather rising off.
            for i, width in enumerate(SIDE_TUFT_WIDTHS):
                row = ys[0] + 1 + i
                if row not in crown_rows:
                    break
                x = edge(row, sign)
                if x is None:
                    continue
                for step in range(1, width + 1):
                    cx = x + sign * step
                    if (0 <= cx < env.width and allowed(cx)
                            and row_has_room(view, row)):
                        crown[view].add((cx, row))
        elif motif == "CROWN_DENT":
            # two cells pressed out of the broad top row
            x = edge(top, sign)
            if x is None:
                continue
            crown[view] -= {(x, top), (x - sign, top)}
        elif motif == "BRIM_FLICK":
            if not brim[view]:
                continue
            bl = min(y for _, y in brim[view])
            row = [x for (x, y) in brim[view] if y == bl]
            x = min(row) if sign < 0 else max(row)
            # Each flick cell must touch fabric, or it is a floating pixel:
            # the row above the brim line is narrower, so a cell placed one
            # column outside it landed detached with a gap between.
            for dy in (0, 1):
                cx, cy = x + sign, bl - dy
                if not (0 <= cx < env.width and 0 <= cy < env.height):
                    continue
                if not allowed(cx):
                    continue
                touching = brim[view] | crown[view]
                if any((cx + ax, cy + ay) in touching
                       for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    brim[view].add((cx, cy))


# The contract is registered at the bottom of this module but `realize` needs
# to read its declarations, so it is held in a one-slot list that registration
# fills.  Reading the declaration rather than a constant is the point: a rule
# that is right for one Architecture and wrong for another is declared, never
# hardcoded into the geometry.
BRIMMED_HAT_CONTRACT: list = [None]

# Share of the crown that may sit at peak brightness.  The references run 5.2%
# and vanilla 6.4%; the old radial field produced 19.9%, which reads as a glaze.
CROWN_HIGHLIGHT_SHARE = 0.06

# How far the lowest two rows step DOWN the ramp, bottom row first.  Vanilla
# darkens the bottom row by 35 luminance and the one above it by 19; we darkened
# the bottom row and nothing else, so nothing seated the hat into the hair.
CONTACT_STEPS = (2, 1)

CROWN_MIN_ROW = 4      # narrowest legible crown row at 20x20
BRIM_MIN_ROW = 4


# Profiles that are narrow BY DESIGN.  The 0.55 proportion rule exists to stop
# an accidental stem-and-dish read; a cone is supposed to be a stem, so it is
# exempt.  Declared per profile rather than relaxing the rule for everyone.
NARROW_BY_DESIGN = ("CONE", "COLUMN")

# Crown profiles that are the STEM of a wide-brimmed hat rather than the body
# of one.  Two rules relax for these, and both are declared here rather than
# loosened for every Architecture:
#
#   * the brim may be DEEPER than half the crown height.  That rule exists to
#     stop the goblet read — brim mass mirroring crown mass — but on a short
#     straight crown a deep brim IS the shape, not a failure of it.
#   * the brim line may sit at row 8.  A brim that high normally floats above
#     the head; under a wide brim it is where the corpus puts it (vanilla #0).
WIDE_BRIM_CROWNS = ("COLUMN",)
WIDE_BRIM_MAX_DEPTH = 4          # rows below the brim line
# A wide-brim crown must actually be UNDER a wide brim.  The ordinary +3 rule
# is the point at which a brim becomes visible at all; on a four-row straight
# crown that is not enough to read as a hat — the crown and the brim come out
# nearly the same width and the sprite is a dish.  Vanilla #0 runs 18 against
# 8.  Declared for these crowns only; every other profile keeps +3.
WIDE_BRIM_MIN_FLARE = 6

# --- a wide brim SEEN EDGE-ON splits ----------------------------------------
#
# 47 of the 112 vanilla hats split a row at their BASE, and on a wide-brimmed
# hat the reason is geometric rather than decorative: an upturned brim viewed
# in profile shows its front and back ends hanging below the middle, with
# daylight between them.  Vanilla #0 draws exactly that — its side frame runs
# `..####......#####...` where the front frame is solid.
#
# This is a DIRECTIONAL REALIZATION of a structural piece, not a motif: the
# same brim, same rows, same columns, drawn as what the profile actually shows.
# It is gated on `allows_split_rows` because opening a row is a topology
# change, and scoped to the brim profiles that curl.
# KEEP EXPERIMENTAL — scoped to nothing, like SIDE_TUFT and (until phase 3)
# BRIM_WINGS.  The concept is corpus-supported (47 of 112 hats split at the
# base) and the machinery is correct and guarded, but on the one reconstruction
# it applies to it makes things WORSE: Cowboy's side frame goes 31.0% -> 35.1%,
# because our profile brim sits a row higher and a row deeper than vanilla's,
# so the curl opens the wrong two rows.  Shipping a split in the wrong place is
# worse than not splitting.  It becomes live the moment the profile brim's
# placement is settled (gap #27).
SIDE_CURL_BRIMS: tuple = ()
SIDE_CURL_CANDIDATES = ("ROLLED", "CURLED")
SIDE_CURL_ROWS = 2               # only the LAST rows open; the brim stays solid
                                 # where it is still flat.  Vanilla #0 splits
                                 # one row and stubs the next, out of four.
SIDE_CURL_WIDTH = 4              # cells kept at each end


def has_odd_rows(profile: str, architecture: str = "BRIMMED_HAT") -> bool:
    """True when the profile authors half-integer insets, i.e. ODD-width rows.

    An odd mass cannot sit exactly centred on a 20-wide frame, so such a hat is
    half a pixel off by construction.  Vanilla does the same (Witch 0.95,
    Santa 0.94).  This is the declared exception the symmetry and side-brim
    contracts consult — it is NOT a general relaxation: every integer-inset
    profile stays pixel-exact.
    """
    from .hat_motifs import crown_row_profile
    return any(float(i) != int(i)
               for i in crown_row_profile(profile, architecture))


def crown_median_width(profile: str, widest: int) -> int:
    """The crown width the corpus metric will actually report.

    `crown_width` is the WIDEST crown row, because that is what the authored
    profile insets are measured from.  `crown_metrics` reports the MEDIAN row
    above the brim line, which is what the corpus bound (5, 12) describes.
    Confusing the two collapsed every crown to the minimum row and made the
    hats read as chimneys: width/height ran 1.00 against vanilla's 1.43.
    """
    widths = sorted(max(CROWN_MIN_ROW, int(round(widest - 2 * i)))
                    for i in CROWN_PROFILES[profile])
    return widths[len(widths) // 2]


def estimate_cells(crown_profile: str, crown_width: int,
                   brim_profile: str, brim_width: int) -> int:
    """Front-frame mass a combination would draw, before it is drawn.

    The corpus bounds total occupied cells at (24, 149); a tall crown with a
    deep, wide brim overshoots that even though every individual parameter is
    in range.  Checking it during resolution keeps the constraint inside the
    declared schema instead of clamping the geometry afterwards.
    """
    crown = sum(max(CROWN_MIN_ROW, int(round(crown_width - 2 * i)))
                for i in CROWN_PROFILES[crown_profile])   # crown_width = widest row
    brim = sum(max(BRIM_MIN_ROW, int(round(brim_width - 2 * i)))
               for i in BRIM_PROFILES[brim_profile])
    return crown + brim


BRIM_WIDTHS = (12, 14, 16, 18)
RETIRED_BRIMS = ("DEEP_TAPER", "FLOPPY")     # see the weights in declare_schema


def brim_depth_limit(crown_profile: str) -> float:
    """How many rows a brim may put BELOW the brim line, for this crown."""
    if crown_profile in WIDE_BRIM_CROWNS:
        return WIDE_BRIM_MAX_DEPTH
    return len(CROWN_PROFILES[crown_profile]) / 2


def viable_brims(crown_profile: str, crown_width: int) -> int:
    """How many (brim profile, brim width) pairs a crown still allows."""
    med = crown_median_width(crown_profile, crown_width)
    return sum(1 for bp in BRIM_PROFILES for bw in BRIM_WIDTHS
               if bp not in RETIRED_BRIMS
               and bw >= med + (WIDE_BRIM_MIN_FLARE
                                if crown_profile in WIDE_BRIM_CROWNS else 3)
               and (len(BRIM_PROFILES[bp]) - 1) <= brim_depth_limit(crown_profile)
               and 24 <= estimate_cells(crown_profile, crown_width, bp, bw) <= 149)


def fill_back(views: dict, env: Envelope, extend: bool = False) -> dict:
    """Derive one piece's BACK frame from its own FRONT frame, in place."""
    views["back"] = back_view(views["front"], env, extend)
    return views


def _rows_of(cells: set) -> dict:
    out: dict[int, list[int]] = {}
    for (x, y) in cells:
        out.setdefault(y, []).append(x)
    return out


def _crown_shading(cells: set) -> dict:
    """A crown is a FORM MADE OF PLANES, not a glazed surface.

    The previous pass took each cell's distance from a light origin and
    quantised it into four bands.  That is a continuous radial falloff, which on
    a symmetric dome is exactly the shading of a pot — and "vases pasted on my
    head" is what it produced in game.  Measured against 116 vanilla hats and
    the four hats the user picked as good:

        highlight spread, share of the sprite   good 5.2%   vanilla 6.4%
                                                OURS 19.9%

    A fifth of the sprite at peak brightness is not a highlight, it is a sheen.
    So the crown is now shaded as discrete regions with hard boundaries between
    them, which is what pixel art actually does:

        TOP PLANE     the crown rows above the shoulder, catching the light
        HIGHLIGHT     a small hard patch near the top-left of the top plane,
                      about a twentieth of the crown and never more
        SIDE          the lit side, base value
        SHADE         the far side and the rows below the widest point
        CONTACT       the lowest TWO rows, stepped down twice

    Vanilla and the references both darken the second-from-bottom row (vanilla
    -19, references -10 against the body); we darkened exactly one row, which is
    the other half of why the hats do not seat.
    """
    if not cells:
        return {}
    rows = _rows_of(cells)
    ys = sorted(rows)
    top, bottom = ys[0], ys[-1]
    widest = max(len(r) for r in rows.values())
    # the shoulder: the first row at (or near) full width, where the top plane
    # turns into the side
    shoulder = next((y for y in ys if len(rows[y]) >= widest - 1), bottom)
    xs_all = [x for x, _ in cells]
    lo_x, hi_x = min(xs_all), max(xs_all)
    span = max(1, hi_x - lo_x)

    out = {}
    for y in ys:
        row = sorted(rows[y])
        for x in row:
            t = (x - lo_x) / span                   # 0 left .. 1 right
            if y <= shoulder:
                offset = -1 if t < 0.62 else 0      # top plane, lit from the left
            else:
                offset = 0 if t < 0.55 else 1       # side, turning away
            out[(x, y)] = offset

    # --- the highlight: SMALL, HARD-EDGED, and on the upper crown ----------
    # Placed on the top plane rather than derived from a distance field, so its
    # size is authored instead of emergent.
    lit = [c for c in cells if c[1] <= shoulder]
    if lit:
        budget = max(1, round(len(cells) * CROWN_HIGHLIGHT_SHARE))
        lit.sort(key=lambda c: (c[1], c[0]))        # top rows first, left first
        anchor_row = min(c[1] for c in lit)
        band = [c for c in lit if c[1] <= anchor_row + 1]
        band.sort(key=lambda c: (c[1], c[0]))
        for c in band[:budget]:
            out[c] = -2

    # --- contact: the lowest two rows step down ---------------------------
    for i, y in enumerate((bottom, bottom - 1)):
        if y in rows:
            step = CONTACT_STEPS[i]
            for x in rows[y]:
                out[(x, y)] = max(out.get((x, y), 0), 0) + step
    return out


def _brim_shading(cells: set) -> dict:
    """The brim is two planes: an upper surface and an underside in shadow.

    Per column, so a dipped or curled brim shades along its own outline rather
    than along a straight row.  The lowest two rows also step down, for the same
    reason the crown's do: that is the contact edge, and it is what reads as the
    hat meeting the head instead of hovering over it.
    """
    if not cells:
        return {}
    cols: dict[int, list[int]] = {}
    for (x, y) in cells:
        cols.setdefault(x, []).append(y)
    top = min(y for _, y in cells)
    bottom = max(y for _, y in cells)
    out = {}
    for x, ys in cols.items():
        lowest = max(ys)
        for y in ys:
            if y == top:
                out[(x, y)] = -1          # upper surface catches the light
            elif y == lowest:
                out[(x, y)] = 2           # the underside edge
            else:
                out[(x, y)] = 1
    for i, y in enumerate((bottom, bottom - 1)):
        for x in cols:
            if y in cols[x]:
                out[(x, y)] = max(out.get((x, y), 0), CONTACT_STEPS[i] + 1)
    return out


# ---------------------------------------------------------------------------
# hair policy
# ---------------------------------------------------------------------------

def covers_whole_head(construction) -> bool:
    """Does the headwear actually cover the head box, all of it?

    Every column AND every row of HEAD_BOX must be occupied.  The earlier test
    asked only whether each column had *some* cell within the top five rows,
    which any crown satisfies — it measured "a hat is present" rather than "the
    head is covered", and returned HIDE for 78 of 89 rolls.
    """
    x0, x1, y0, y1 = head_box(construction.env)
    cells = construction.silhouette["front"]
    return all((x, y) in cells
               for x in range(x0, x1 + 1)
               for y in range(y0, y1 + 1))


def hair_policy_for(construction, architecture=None) -> str:
    """Hair is PRESERVED unless the Architecture declares otherwise AND earns it.

    Two gates, in this order:

      1. The Architecture must declare `hair_policy = "HIDE"`.  Hiding hair is
         a design decision about a kind of headwear, not something geometry may
         opt into on its own.  BRIMMED_HAT declares PRESERVE: a brimmed hat sits
         ON the head and hair falls below and behind it, so hiding hair makes
         the Farmer look bald from the back and sides — which is exactly the
         reported bug.
      2. Even when declared, the geometry must actually cover the head box, or
         the declaration is ignored.

    Fashion Sense evaluates HideHair per facing direction
    (`GetCurrentlyEquippedModels(who, facingDirection)` feeds
    `IsHatHidingHair`), so a hat that only covers the head from some angles
    would flicker between bald and haired as the Farmer turns.  The policy is
    therefore resolved once per garment and written to all four directions.
    """
    declared = getattr(architecture, "hair_policy", None) if architecture else None
    if declared is None:
        from ..contracts import ARCHITECTURE_LIBRARY
        declared = ARCHITECTURE_LIBRARY["BRIMMED_HAT"].hair_policy
    if declared != "HIDE":
        return "PRESERVE"
    return "HIDE" if covers_whole_head(construction) else "PRESERVE"


# ---------------------------------------------------------------------------
# family
# ---------------------------------------------------------------------------

HAT = register_family(FamilyContract(
    name="HAT",
    slot="HEAD",
    architectures={"BRIMMED_HAT": 1.0},
    closure_vocabulary=("NONE",),
    aperture_vocabulary=("OPEN_BASE",),
    limb_vocabulary=("NONE",),
    layer_slot_vocabulary=(),
    material_vocabulary=("cotton_drill", "wool_melton", "linen", "heavy_canvas",
                         "silk_satin"),
    coverage_domain=("HEAD",),
    color_architecture_vocabulary=(
        "MONOCHROME_CONTRAST_TRIM", "DARK_BODY_LIGHT_COLLAR",
        "LIGHT_BODY_DARK_COLLAR", "LOW_CONTRAST_STRONG_ACCENT",
        "CHROMATIC_BAND", "MUTED_BAND",
    ),
    surface_capabilities=("crown",),
    style_hook=None,
))


def declare_schema(family: FamilyContract, arch, ctx, record):
    return [
        # The authored closed set (INV-10).  One member today; BRIMLESS will
        # arrive as its own Architecture, not as another member here, because
        # the crown/brim split is a topology difference.
        Variable("silhouette", arch.name, "structural", tuple(arch.silhouettes),
                 weights=arch.silhouettes, significance=IDENTITY,
                 cost=0, cost_tag=STRUCTURAL, stream="structure"),
        # Which side an odd row's half-pixel falls on.  Constant per hat, so
        # a hat with odd rows leans consistently rather than jittering.
        Variable("odd_bias", arch.name, "structural", ("LEFT", "RIGHT"),
                 weights={"LEFT": 0.5, "RIGHT": 0.5}, significance=APPEARANCE,
                 cost=0, cost_tag=STRUCTURAL, stream="structure"),
        Variable("crown_profile", arch.name, "structural", tuple(CROWN_PROFILES),
                 weights={"ROUND": 0.19, "DOMED": 0.15, "SHALLOW": 0.12,
                          "TALL_FLAT": 0.13, "STOVEPIPE": 0.07,
                          "PINCHED": 0.09, "STEPPED": 0.09,
                          "CONE": 0.06, "DROOP": 0.05, "COLUMN": 0.05},
                 significance=IDENTITY, cost=0, cost_tag=STRUCTURAL,
                 stream="structure"),
        # The WIDEST crown row — the reference the authored insets are measured
        # from.  Even, so the mass centres exactly.  Validated on the median
        # row it produces, which is what the corpus bound (5, 12) measures.
        # 8 and 10 exist for the narrow straight crowns: COLUMN at 14 or 16
        # reports a median of 14/16 and is rejected by the corpus ceiling of
        # 12, so the two ends of this domain select each other.  A wide crown
        # never rolls 8 either — every taper collapses under the floor of 5.
        Variable("crown_width", arch.name, "structural", (8, 10, 12, 14, 16),
                 weights={8: 0.04, 10: 0.10, 12: 0.42, 14: 0.30, 16: 0.14},
                 significance=IDENTITY,
                 cost=0, cost_tag=STRUCTURAL, stream="structure",
                 repair=REPAIR_RETRY, repair_attempts=8,
                 # Requires HEADROOM, not merely one legal descendant: a
                 # crown that leaves a single viable brim is a knife edge, and
                 # in-domain repair does not reliably find it.  Below the
                 # threshold the crown itself is rerolled instead.
                 # The crown must also hold a real proportion of its own base.
                 # Vanilla's top hat (#2) carries 8 of 14 through its straight
                 # section — 57%.  Below about 55% the crown stops reading as a
                 # crown and becomes a stem with a dish on it, which is the
                 # chess-piece/goblet look.
                 validate=lambda v, r, c: (
                     5 <= crown_median_width(r.get("crown_profile"), v) <= 12
                     and (r.get("crown_profile") in NARROW_BY_DESIGN
                          or crown_median_width(r.get("crown_profile"), v) >= 0.55 * v)
                     and viable_brims(r.get("crown_profile"), v) >= 8)),
        # NOTE: there is no crown_height variable.  The authored profile owns
        # its own height, which is the point of authoring silhouettes rather
        # than parameterising a rectangle.
        # Corpus: median 10, p90 12.  This is the row the brim sits on, and it
        # is the single number that decides whether a hat rests on the head or
        # sits down over the face — the frame is anchored to the head, so a
        # brim two rows below the corpus median lands on the brow.
        #
        # It was widened to 13 to give tall crowns somewhere to go, because
        # crown_top = brim_line - crown_height.  That was the wrong direction:
        # a tall crown should grow UPWARD into rows 0-3, which vanilla occupies
        # 16-53% of the time, rather than push its brim down onto the face.
        Variable("brim_line", arch.name, "structural", (8, 9, 10, 11, 12),
                 weights={8: 0.04, 9: 0.25, 10: 0.42, 11: 0.19, 12: 0.10},
                 significance=IDENTITY, cost=0, cost_tag=STRUCTURAL,
                 stream="structure", repair=REPAIR_RETRY, repair_attempts=8,
                 # the crown has to start inside the frame and no lower than
                 # the top of the head box plus its clearance
                 validate=lambda v, r, c: (
                     0 <= v - len(CROWN_PROFILES[r.get("crown_profile")]) <= 6
                     # row 8 is only for the crowns that declare it
                     and (v >= 9
                          or r.get("crown_profile") in WIDE_BRIM_CROWNS))),
        # Brim must clear the crown by enough to read as a brim at all: the
        # corpus threshold for "brimmed" is 1.15x, and +4 columns clears it for
        # every crown width in the domain.
        # Corpus median is 14 with 2 columns of overhang per side; batch 01 ran
        # 16 and 3.  Weighted down, and 18 is now rare rather than common.
        # 12 is usually excluded by the brim-vs-crown rule once the crown is
        # its corpus width, so the weight is concentrated on 14 to keep the
        # realised median at the vanilla figure rather than one step above it.
        Variable("brim_width", arch.name, "structural", (12, 14, 16, 18),
                 weights={12: 0.14, 14: 0.60, 16: 0.20, 18: 0.06},
                 significance=IDENTITY, cost=0, cost_tag=STRUCTURAL,
                 stream="structure", repair=REPAIR_RETRY,
                 # Measured against the crown width the metric will report,
                 # not against the widest row.  Also requires that at least one
                 # brim profile still fits under the corpus mass ceiling —
                 # otherwise brim_profile could find no legal value at all and
                 # would go absent, taking the brim with it.
                 validate=lambda v, r, c: (
                     v >= crown_median_width(r.get("crown_profile"),
                                             r.get("crown_width"))
                     + (WIDE_BRIM_MIN_FLARE
                        if r.get("crown_profile") in WIDE_BRIM_CROWNS else 3)
                     and any(estimate_cells(r.get("crown_profile"),
                                            r.get("crown_width"), bp, v) <= 149
                             for bp in BRIM_PROFILES))),
        Variable("brim_profile", arch.name, "structural", tuple(BRIM_PROFILES),
                 # DEEP_TAPER and FLOPPY are RETIRED for now, not deleted.
                 # Both put four rows below the brim line where the vanilla
                 # median is two, and a four-row cone under any crown produces
                 # the goblet: the mass below the brim mirrors the crown above
                 # it.  The reference hats that do carry a deep brim are floppy
                 # sun hats whose brim DROOPS rather than tapering to a point,
                 # and that is a brim treatment this Architecture has not
                 # authored yet.  Shipping a wrong shape to keep two entries in
                 # the table is the wrong trade.  The remaining five all sit at
                 # the corpus median of two rows below the line.
                 weights={"TAPERED": 0.25, "DEEP_TAPER": 0.0, "SHARP": 0.17,
                          "DIPPED": 0.16, "STEPPED": 0.13, "CURLED": 0.11,
                          "SWEEP": 0.12, "FLOPPY": 0.0, "ROLLED": 0.06},
                 significance=IDENTITY, cost=0, cost_tag=STRUCTURAL,
                 stream="structure", repair=REPAIR_RETRY, repair_attempts=8,
                 # Rolled last of the shape variables, so it is where the
                 # combined mass can finally be checked against the corpus —
                 # and where the brim's DEPTH is checked against the crown.
                 #
                 # Vanilla puts a median of 2 rows below the brim line, and the
                 # ratio of that depth to crown height has a median of 0.29.  A
                 # four-row brim under a five-row crown runs 0.8, which is deep
                 # in the corpus tail and is exactly the goblet silhouette: the
                 # mass below the brim mirrors the crown above it and the hat
                 # reads as a lens rather than a hat.  Half the crown height
                 # covers 49 of 67 reference hats.
                 validate=lambda v, r, c: (
                     24 <= estimate_cells(r.get("crown_profile"),
                                          r.get("crown_width"), v,
                                          r.get("brim_width")) <= 149
                     and (len(BRIM_PROFILES[v]) - 1)
                     <= brim_depth_limit(r.get("crown_profile"))
                     # the mass must still end inside the corpus range
                     and r.get("brim_line") + len(BRIM_PROFILES[v]) - 1 <= 14)),
        # Protrusions — ears and the like.  Closed set, profile-scoped, and
        # ATTACHED, so they split a row without opening an enclosed hole.
        # 33 of 188 shipping hats (18%) are a crown plus a protrusion.
        Variable("protrusion", arch.name, "structural",
                 ("NONE",) + tuple(PROTRUSIONS),
                 # BRIM_WINGS carries a high weight because it is legal on
                 # almost nothing: it needs COLUMN and a brim of 16 or more.
                 # Weights are renormalised over the options that pass
                 # `validate`, so this is the share it takes WHEN legal, not
                 # overall — at 0.06 it fired under once in a thousand rolls,
                 # which is a capability on paper only.
                 weights={"NONE": 0.74, "EARS_TOP": 0.12, "EARS_SIDE": 0.0,
                          "EARS_TALL": 0.0, "CROWN_CREASE": 0.08,
                          "BRIM_WINGS": 0.30},
                 significance=IDENTITY, cost=0, cost_tag=STRUCTURAL,
                 stream="structure", repair=REPAIR_RETRY, repair_attempts=8,
                 validate=lambda v, r, c: (
                     v in protrusion_options(r.get("crown_profile"), arch.name,
                                             r.get("crown_width"),
                                             r.get("brim_width"))
                     and (v == "NONE" or estimate_cells(
                         r.get("crown_profile"), r.get("crown_width"),
                         r.get("brim_profile"), r.get("brim_width"))
                         + PROTRUSION_MAX_CELLS <= 149))),
        # A piece that exists in some frames and not others.  Gated on the
        # Architecture's `allows_directional_pieces` declaration, so this
        # collapses to ("NONE",) for any Architecture that has not opted in.
        Variable("directional", arch.name, "structural", DIRECTIONAL_OPTIONS,
                 weights={"NONE": 0.84, "VISOR": 0.0, "TAIL": 0.16},
                 significance=IDENTITY, cost=0, cost_tag=STRUCTURAL,
                 stream="structure", repair=REPAIR_RETRY,
                 validate=lambda v, r, c: (
                     v in directional_options(arch.name,
                                              r.get("crown_profile"), arch)
                     # A tail hangs off a soft crown's HEM.  On a brimmed hat
                     # the lowest mass is the brim, so this only reads when
                     # that brim is really a cuff — two rows, like vanilla
                     # #25's fur band.  Hung off a three-row 16-wide brim it
                     # looks like the brim is dripping.
                     and (v != "TAIL"
                          or len(BRIM_PROFILES[r.get("brim_profile")]) <= 2))),
        # Controlled asymmetry.  Closed set, profile-scoped, symmetric by
        # default: the corpus is 72% exact mirrors, so NONE carries most of the
        # weight and the motifs share the rest.
        Variable("asymmetry", arch.name, "structural",
                 ("NONE", "TIP_LEAN", "TIP_DROOP", "SIDE_TUFT", "CROWN_DENT",
                  "BRIM_FLICK"),
                 weights={"NONE": 0.60, "TIP_LEAN": 0.17, "TIP_DROOP": 0.09,
                          "SIDE_TUFT": 0.0, "CROWN_DENT": 0.06,
                          "BRIM_FLICK": 0.08},
                 significance=APPEARANCE, cost=0, cost_tag=STRUCTURAL,
                 stream="structure", repair=REPAIR_RETRY, repair_attempts=8,
                 # One shape decision per hat — see brimless_hat for why.
                 activation=lambda r, c: r.opt("protrusion") in (None, "NONE"),
                 validate=lambda v, r, c: (
                     v in asymmetry_options(r.get("crown_profile"),
                                            r.get("brim_profile"))
                     and (v != "SIDE_TUFT" or tuft_has_headroom(
                         r.get("crown_profile"), r.get("crown_width"),
                         r.get("brim_profile"), r.get("brim_width"))))),
        # Vanilla asymmetry leans left about 2:1.
        Variable("asym_side", arch.name, "structural", (ASYM_LEFT, ASYM_RIGHT),
                 weights={ASYM_LEFT: 0.66, ASYM_RIGHT: 0.34},
                 significance=APPEARANCE, cost=0, cost_tag=STRUCTURAL,
                 stream="structure",
                 activation=lambda r, c: r.opt("asymmetry") not in (None, "NONE")),
        Variable("material", arch.name, "structural", tuple(arch.materials),
                 weights=dict(arch.materials), significance=APPEARANCE,
                 cost=0, cost_tag=STRUCTURAL, stream="material"),
        Variable("color_architecture", arch.name, "structural",
                 tuple(arch.color_architectures), weights=dict(arch.color_architectures),
                 significance=IDENTITY, cost=0, cost_tag=STRUCTURAL, stream="color"),
        Variable("harmony", arch.name, "structural",
                 ("complementary", "analogous", "split_complement"),
                 weights={"complementary": 0.4, "analogous": 0.4,
                          "split_complement": 0.2},
                 significance=APPEARANCE, cost=0, cost_tag=STRUCTURAL,
                 stream="color"),
        # A band at the crown/brim junction is the commonest hat detail and the
        # only thing here that spends budget.
        Variable("band", arch.name, "ornament", (True, False),
                 weights={True: 0.62, False: 0.38}, significance=APPEARANCE,
                 cost={True: 1, False: 0}, cost_tag=ORNAMENT,
                 stream="ornament",
                 activation=lambda r, c: c.budget.remaining >= 1),
    ]


# ---------------------------------------------------------------------------
# construction
# ---------------------------------------------------------------------------

def realize(spec, env: Envelope) -> Construction:
    if (env.width, env.height) != (20, 20):
        raise ValueError(
            f"BRIMMED_HAT has no authored geometry for {env.width}x{env.height}; "
            f"hats are authored at 20x20 (see HAT_ENVELOPE)")
    p = spec.parameters
    x0, x1, y0, y1 = head_box(env)
    # `realize` is also called for PROVISIONAL geometry partway through
    # resolution (resolver.py builds ctx.geometry before every variable is
    # settled), so every parameter is read defensively.  The defaults are the
    # most-weighted member of each domain, never a new value.
    cw = p.get("crown_width", 12)
    bl, bw = p.get("brim_line", 10), p.get("brim_width", 14)
    insets = CROWN_PROFILES[p.get("crown_profile", "ROUND")]
    odd_bias = ODD_BIAS_LEFT if p.get("odd_bias") == "LEFT" else ODD_BIAS_RIGHT
    ch = len(insets)
    crown_top = bl - ch

    # --- crown -------------------------------------------------------------
    # An authored silhouette, and ANCHORED: identical columns in every view.
    # A hat does not slide sideways when the Farmer turns, and shifting the
    # side crown by a column was what made the first batch's profile look
    # unmoored.  Corpus supports reuse: front and side crowns agree at the
    # median on height, width and top row.
    crown = {"front": set(), "side": set(), "back": set()}
    crown_rows = {}
    for i, inset in enumerate(insets):
        row = crown_top + i
        # Floor of 6: a profile carrying a 4-cell inset would otherwise pinch a
        # narrow crown down to nothing, and the median row width would fall
        # under the corpus floor of 5.  Six keeps every authored shape legible
        # at this size without flattening the profile that distinguishes it.
        cols = span(max(CROWN_MIN_ROW, row_width(cw, inset)), env, odd_bias)
        crown_rows[row] = cols
        cells = {(x, row) for x in cols}
        crown["front"] |= cells
        crown["side"] |= cells

    # NOTE: no authored back.  `_derive_back` builds every piece's back frame
    # from its own front frame once all the motifs have been applied, which is
    # the corpus rule (see grammar.back_view) and removes the possibility of
    # the two frames disagreeing.

    # --- brim --------------------------------------------------------------
    # In profile the brim is SYMMETRIC about the crown and the same width as it
    # is head-on — that is what the corpus does (ratio median 1.00, 45 of 73
    # exactly equal, side and front brim widths both median 14).  Perspective
    # is worth one cell forward on the widest row only, and no more; the face
    # is at high x, as in every other V5 side view.
    brim = {"front": set(), "side": set(), "back": set()}
    side_bl = max(crown_top + 1, bl - HAT_SIDE_BRIM_RISE)
    # The curl opens a row, and a gap that closes again underneath is an
    # ENCLOSED HOLE — the one thing every hat is required not to have.  So the
    # curl is only taken when EVERY row from SIDE_CURL_FROM down is still wide
    # enough to split, which means it stays open all the way to the brim's
    # edge.  That restricts it to genuinely wide brims, which is also the only
    # place the corpus draws it.
    _bp = BRIM_PROFILES[p.get("brim_profile", "TAPERED")]
    side_curl = (p.get("brim_profile") in SIDE_CURL_BRIMS
                 and getattr(BRIMMED_HAT_CONTRACT[0], "allows_split_rows", False)
                 and all(max(BRIM_MIN_ROW, row_width(bw, ins)) > 2 * SIDE_CURL_WIDTH + 1
                         for ins in _bp[-SIDE_CURL_ROWS:]))
    for i, inset in enumerate(BRIM_PROFILES[p.get("brim_profile", "TAPERED")]):
        cols = span(max(BRIM_MIN_ROW, row_width(bw, inset)), env, odd_bias)
        row = bl + i
        if row < env.height:
            brim["front"] |= {(x, row) for x in cols}
        # Same brim, same width, same centre — one row higher.
        srow = side_bl + i
        if srow < env.height:
            lo = cols.start - HAT_SIDE_BRIM_SKEW
            hi = cols.stop - 1 + HAT_SIDE_BRIM_SKEW
            xs = [x for x in range(lo, hi + 1) if 0 <= x < env.width]
            if (side_curl and i >= len(_bp) - SIDE_CURL_ROWS
                    and len(xs) > 2 * SIDE_CURL_WIDTH + 1):
                xs = xs[:SIDE_CURL_WIDTH] + xs[-SIDE_CURL_WIDTH:]
            brim["side"] |= {(x, srow) for x in xs}

    # --- controlled asymmetry ----------------------------------------------
    apply_asymmetry(p.get("asymmetry", "NONE"), p.get("asym_side", ASYM_LEFT),
                    crown, brim, crown_rows, env)

    # --- protrusions --------------------------------------------------------
    # After asymmetry, so a lean displaces the crown rather than the ears.
    brim_rows = {}
    for (bx, by) in brim["front"]:
        brim_rows.setdefault(by, []).append(bx)
    brim_rows = {k: range(min(v), max(v) + 1) for k, v in brim_rows.items()}
    apply_protrusion(p.get("protrusion", "NONE"), crown, crown_rows, env,
                     brim, brim_rows)

    # --- the back frame ----------------------------------------------------
    # Derived last, from the finished front, so every motif above reaches it
    # without being authored twice.  Only the LOWEST piece repeats its bottom
    # row: that is the underside the camera gains when it moves behind the
    # head, and doing it per piece would double-count it.
    fill_back(crown, env)
    fill_back(brim, env, extend=True)

    crown_piece = Piece("crown", "body", z=0, wrap=PLANE,
                        surface_domain="crown", cells=crown)
    brim_piece = Piece("brim", "body", z=1, wrap=PLANE, cells=brim)

    # Shading FOLLOWS THE FORM, not the row index.  The previous pass shaded
    # "every brim cell below the brim line", which is a horizontal rule: on a
    # carved profile it drew a straight band across a shaped edge, the same
    # defect the Sailor flap had.  Both surfaces are now shaded from their own
    # geometry.
    # An Architecture that declares an authored interior builds its pieces with
    # it here, inside its own realize step.  It is the same two surfaces either
    # way; what changes is that the interior has NAMES, which is what lets the
    # quality gate say "the band came off the crown" instead of "score 0.71".
    # The interior is DERIVED from the geometry this Architecture just
    # resolved: a crown 8 rows tall is a TALL_CROWN because it is one.  No
    # variable, no second entropy source, nothing to keep in sync.
    tpl_meta = {"crown_height": ch, "crown_width": cw, "brim_width": bw,
                "brim_line": bl,
                "overhang": overhang(crown["front"] | brim["front"], (x0, x1, y0, y1))}
    tpl = hat_templates.select(
        BRIMMED_HAT_CONTRACT[0].construction_templates
        if BRIMMED_HAT_CONTRACT[0] is not None else (), tpl_meta)
    if tpl is not None:
        hat_templates.apply(tpl, {"crown": crown_piece, "brim": brim_piece})
    else:
        crown_piece.shading = {v: _crown_shading(cells) for v, cells in crown.items()}
        brim_piece.shading = {v: _brim_shading(cells) for v, cells in brim.items()}
    brim_piece.free_edges = {v: set(cells) for v, cells in brim.items()}
    pieces = [crown_piece, brim_piece]

    # --- directional piece --------------------------------------------------
    # Built from the FINISHED silhouette, as its own Piece, so it can never
    # move a cell the crown or brim already owns.  Absent from the frames it
    # does not declare, which is the whole point of it.
    dmotif = p.get("directional", "NONE")
    if dmotif != "NONE":
        base = {v: crown[v] | brim[v] for v in ("front", "side", "back")}
        dcells = directional_cells(dmotif, base, env)
        if any(dcells.values()):
            dp = Piece("hanging", "body", z=1, wrap=PLANE, cells=dcells)
            dp.shading = {v: _brim_shading(c) for v, c in dcells.items()}
            pieces.append(dp)

    # --- band --------------------------------------------------------------
    # A hat band in the corpus is a thin, RECESSED line, not a bright bar.
    # Batch 01 painted the full crown row in the trim role and it dominated the
    # sprite.  Two corrections, both drawn from rules that already exist:
    #   * it is decorative linework, so it terminates one cell inboard of the
    #     crown edge (grammar.terminate_inboard, the shared rule);
    #   * it is shaded DOWN, so it reads as a band pressed into the crown
    #     rather than a light stripe laid across it.
    if spec.parameters.get("band"):
        band, shading = {}, {}
        for view in ("front", "side"):
            if tpl is not None:
                # WHETHER there is a band is an ornament variable this
                # Architecture declares and the budget pays for; WHERE it seats
                # and how it reads belongs to the authored interior.  The seat
                # is measured from the view's own brim line.
                ref = side_bl if view == "side" else bl
                row_cells = hat_templates.band_cells(crown[view], tpl, ref)
                depth = tpl.band.depth
            else:
                # the band sits just above that view's own brim line
                band_row = (side_bl if view == "side" else bl) - 1
                row_cells = {c for c in crown[view] if c[1] == band_row}
                row_cells = terminate_inboard(row_cells, run_axis=0)
                depth = 1
            band[view] = row_cells
            shading[view] = {c: depth for c in row_cells}
        fill_back(band, env)
        shading["back"] = {c: (tpl.band.depth if tpl is not None else 1)
                           for c in band["back"]}
        if any(band.values()):
            pieces.append(Piece("band", "trim", z=2, wrap=PLANE, identity=True,
                                zones=("collar:center",), cells=band,
                                shading=shading))

    silhouette = {v: set().union(*(pc.cells.get(v, set()) for pc in pieces))
                  for v in ("front", "side", "back")}
    construction = Construction(env=env, silhouette=silhouette, pieces=pieces,
                                surface_domains={"crown": ("crown",)})
    # The meta a construction exposes is the SAME dict the template selection
    # ran on, plus the template it chose.  They were two dicts for one commit
    # and they disagreed: anything reading `construction.meta` saw no
    # crown_height and selected the shallow-crown template for every hat.
    construction.meta = dict(tpl_meta)
    construction.meta.update({
        "crown_top": crown_top, "head_box": (x0, x1, y0, y1),
        "template": tpl.name if tpl is not None else None,
    })
    return construction


BRIMMED_HAT = register_architecture(ArchitectureContract(
    name="BRIMMED_HAT",
    family="HAT",
    closure="NONE",
    aperture="OPEN_BASE",
    limb="NONE",
    topology=("crown", "brim"),
    silhouettes={"brimmed": 1.0},
    layer_slots_opened=(),
    coverage_range=("HEAD",),
    surface_domains=("crown",),
    occupancy=(("collar:center", "band", "conditional_share"),),
    base_cost=1,
    trim=("band", ("band",)),
    # Hat identity is GEOMETRIC — brim wider than crown — and that is enforced
    # by construction and by the corpus-bound tests, not by colour QC.  The one
    # chromatic relationship worth a floor is the band against the crown it
    # sits on, and only when a band exists.
    identity_pairs=(
        IdentitySeparation("trim", "body", floor_scale=0.60, needs="band"),
    ),
    identity_floor=38.0,
    identity_retention=1.0,
    identity_composite_floor=0.0,
    max_appearance_features=3,
    hair_policy="PRESERVE",
    # The authored interior this Architecture builds its crown and brim with.
    construction_templates=("TALL_CROWN", "WIDE_BRIM", "FELT_BRIMMED"),
    # A soft pointed crown may hang a tail behind it in profile — CONE, DROOP
    # and STOVEPIPE only, per DIRECTIONAL_SCOPE.  A visor is not offered here:
    # a brimmed hat already carries an all-round version of the same surface.
    allows_directional_pieces=True,
    # A curled brim opens in profile — see SIDE_CURL_BRIMS.
    allows_split_rows=True,
    # LOW_CONTRAST_STRONG_ACCENT is declared incompatible, not merely unlikely.
    # A hat's identity cue is its outlined silhouette, and that palette's body
    # ramp spans about 34 luminance end to end (106 -> 140 on wool), so the
    # outline pass has nowhere to go: measured over seeds 0-95 it produced 7 of
    # the 10 rejections while supplying only 18 of the 96 rolls, and it was the
    # only palette whose worst outline failed the corpus threshold.  Same
    # reasoning that narrowed CLASSIC's vocabulary — a palette that cannot
    # carry the Architecture's identity cue is incompatible with it, and no
    # amount of geometry polish rescues it.
    color_architectures={"MONOCHROME_CONTRAST_TRIM": 0.18,
                         "DARK_BODY_LIGHT_COLLAR": 0.20,
                         "LIGHT_BODY_DARK_COLLAR": 0.18,
                         "CHROMATIC_BAND": 0.26,
                         "MUTED_BAND": 0.18},
    materials={"cotton_drill": 0.24, "wool_melton": 0.26, "linen": 0.18,
               "heavy_canvas": 0.20, "silk_satin": 0.12},
    declare_schema=declare_schema,
    realize=realize,
    style_hook=None,
))

BRIMMED_HAT_CONTRACT[0] = BRIMMED_HAT
