"""AUTHORED CONSTRUCTION TEMPLATES — headwear interiors.

A template is the INTERIOR of a construction tradition, authored once: which
planes a crown breaks into, where the light patch sits and how big it may be,
which rows are the contact edge, where a band seats when the roll says there is
one, and what the crown casts onto the brim.  It is not a pipeline stage and it
is not reachable from outside the Architecture that declares it.

Ownership, deliberately narrow:

    Architecture   legality, topology, silhouette vocabulary, which variables
                   exist and what they may take, WHETHER a band exists.
    Template       the interior of pieces the Architecture already built —
                   planes, light, contact, band seat, occlusion.
    Neither        the template never adds, removes or moves a silhouette cell.
                   `apply()` asserts it, and that assertion IS the one-owner
                   guarantee: a template cannot change what a hat is.

Which template a hat gets is DERIVED from geometry the Architecture already
resolved, never rolled — the rule Projection follows.  A crown ten rows tall is
a TALL_CROWN because it is one; no second entropy source, no variable to keep
in sync.

Every number is measured over 194 reference hats — 120 vanilla
(`Characters/Farmer/hats.png`) and 74 from the mod-author sheet (`female.png`)
— by `tools/analyze_hat_construction_corpus.py`, plus the four hats the user
picked as good.  Family medians are quoted at each field.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..grammar import terminate_inboard


# ---------------------------------------------------------------------------
# the contract
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CrownPlanes:
    """How a crown breaks into planes.

    A crown is a form made of PLANES with hard boundaries, not a glazed
    surface.  Both turns are fractions of THAT ROW's own width, so a boundary
    follows a carved profile instead of cutting a straight line down a shaped
    crown.

    Offsets are ramp steps, positive DARKER.  Nothing is lighter than base
    except the light patch itself: a plane painted one step light covers half
    the crown, and half a sprite at the light step is what measured as 20.5%
    "highlight" — the vase.  The corpus runs the other way: a mid body, a
    turned side, a dark underside, and a small patch above base.
    """
    top_turn: float = 0.62
    side_turn: float = 0.55
    shoulder_tolerance: int = 1
    top_lit: int = -1
    top_turned: int = 0
    side_lit: int = 0
    side_shade: int = 1
    lit_share: float = 0.18         # cap on the lit part of the top plane
    rim_min: int = 0                # the crown's own rim is never lighter


@dataclass(frozen=True)
class HighlightSpec:
    """A small hard patch.

    The four reference hats put 5.2% of the front frame within 12 luminance of
    their brightest pixel; vanilla 6.9%; ours 20.5% before templates.  `share`
    is of the CROWN, so it reads a little higher than those figures.

    Placement is measured, and it is NOT the upper-left the shirt grammar
    assumes.  Of 84 one-sided reference highlights, 70 sit right of centre and
    9 left; across the four hats the user chose, the patch sits at x 0.46-0.55
    of the sprite and y 0.24-0.48 down it.  So: near the crown's centre line,
    in its upper third, optionally mirrored into a pair — half the vanilla
    corpus and two of the four references draw it symmetrically.
    """
    share: float = 0.07
    rows: int = 3                   # how far down from the crown top it may run
    depth: int = 2                  # ramp steps toward the light
    anchor: str = "centre"          # "centre" | "right" | "left"
    symmetric: bool = False         # mirror the patch about the crown centre
    inset_from_edge: bool = True    # never on the rim: the outline eats it


@dataclass(frozen=True)
class ContactSpec:
    """The bottom edge that seats the hat into the hair.

    Second-from-bottom row against the sprite body: TALL_CROWN -28, CLOSE_FIT
    -20, WIDE_BRIM -10, BRIMMED_FELT 0, the four references -22.  A hat with no
    contact edge hovers; one with too much reads as a shadow stuck to the hair.
    Ramp steps, bottom row first.
    """
    steps: tuple = (2, 1)


@dataclass(frozen=True)
class BandSeat:
    """Where a band goes IF the Architecture rolled one.

    The template does not decide whether a band exists — that is an ornament
    variable the Architecture declares and the budget pays for.

    Measured with a LOCAL-ANOMALY detector (a row differing from the rows both
    above and below it; a gradient step differs from one side only): a true
    band is a minority feature, 30 of 194 hats.  Where it appears it sits 2-3
    rows above the brim line on a felt hat, and the felt family draws it
    RECESSED in the body's own hue (value -16, hue gap 0) while the tall and
    wide families draw it chromatic (hue 50-100 degrees, value +2 to +64).
    """
    rows_above_brim: int = 2
    inset: int = 1                  # cells pulled back from each end
    depth: int = 2                  # shaded DOWN: pressed in, not laid on
    chromatic: bool = False         # is a lighter, different-hue band correct here?


@dataclass(frozen=True)
class CrownShadow:
    """What the crown casts onto the brim it sits on.

    The cue that separates two planes without an outline: in both corpora the
    brim's upper surface is darker in the ring immediately around the crown.
    Declared as local OCCLUSION, not shading, so it composes by MAX (section
    35) and cannot double-count against the contact rows.
    """
    depth: int = 1
    reach: int = 1                  # rows of brim below the crown footprint


@dataclass(frozen=True)
class BrimPlanes:
    """A brim is two surfaces seen nearly edge-on.

    Its outer edge turns away from the camera and is never its lightest step —
    without that rule the widest row's ends render at the upper-surface step
    and swallow the outline margin (seed 44 measured -9.9 against the corpus
    bar of -10).
    """
    upper: int = 0                  # the surface you look down on
    mid: int = 1
    under: int = 2                  # the edge you see from below
    rim_min: int = 1                # outer edge, never lighter than this


@dataclass(frozen=True)
class Targets:
    """What this template claims its output will measure, for QC.

    Ranges, not points: a template is a construction tradition, not one hat.
    `verify()` reads these instead of hardcoding thresholds, so a family with a
    legitimately different interior does not force a shared bar to be weakened.
    """
    highlight_share: tuple = (0.0, 0.13)     # of the crown, rendered
    contact_delta: tuple = (-70.0, -5.0)     # 2nd-from-bottom row vs body
    min_crown_levels: int = 4                # distinct crown luminances
    band_value_sign: int = -1                # -1 recessed, +1 raised, 0 either


@dataclass(frozen=True)
class ConstructionTemplate:
    """One authored interior, referenced BY the Architectures that declare it."""
    name: str
    architectures: tuple
    applies: object                 # (meta) -> bool; derived selection, no RNG
    crown_piece: str = "crown"
    brim_piece: str | None = "brim"
    planes: CrownPlanes = field(default_factory=CrownPlanes)
    highlight: HighlightSpec = field(default_factory=HighlightSpec)
    contact: ContactSpec = field(default_factory=ContactSpec)
    band: BandSeat = field(default_factory=BandSeat)
    crown_shadow: CrownShadow = field(default_factory=CrownShadow)
    brim: BrimPlanes = field(default_factory=BrimPlanes)
    targets: Targets = field(default_factory=Targets)


# ---------------------------------------------------------------------------
# the library
# ---------------------------------------------------------------------------
#
# Families come out of clustering 194 reference hats on geometry alone
# (`analyze_hat_construction_corpus.family`).  Five are reachable with the
# Architectures that exist.  EARED_OR_SPLIT — 51 hats, cat ears, bows, detached
# mass — is deliberately absent: it needs an Architecture that declares
# detached mass and enclosed holes, not a template.

def _tall(meta):    return meta.get("crown_height", 0) >= 8
def _wide(meta):    return (meta.get("brim_width", 0) >= 16
                            or max(meta.get("overhang", (0, 0))) >= 3)
def _shallow(meta): return meta.get("crown_height", 0) <= 4
def _always(meta):  return True


# TALL_CROWN — 53 hats, the largest brimmed family.  Top hat, stovepipe, witch,
# wizard.  Crown 8-10 rows, 8 colours, span 200, the deepest contact edge in
# the corpus (-28), and a chromatic band when it has one (hue gap 50).
TALL_CROWN = ConstructionTemplate(
    name="TALL_CROWN",
    architectures=("BRIMMED_HAT",),
    applies=_tall,
    planes=CrownPlanes(lit_share=0.14, side_shade=2),
    highlight=HighlightSpec(share=0.05, rows=3),
    contact=ContactSpec(steps=(2, 1)),
    band=BandSeat(rows_above_brim=3, chromatic=True),
    targets=Targets(highlight_share=(0.0, 0.11), contact_delta=(-70.0, -8.0),
                    min_crown_levels=5, band_value_sign=0),
)

# WIDE_BRIM — 25 hats.  Cowboy, sombrero, sun hat, boater.  A small crown on a
# brim that is the dominant mass: bbox 16 wide, brim ratio 2.0, crown 5 rows.
# The brim catches more of the crown's shadow, and the contact edge is
# shallower (-10) because the brim, not the crown, meets the head.
WIDE_BRIM = ConstructionTemplate(
    name="WIDE_BRIM",
    architectures=("BRIMMED_HAT",),
    applies=_wide,
    planes=CrownPlanes(lit_share=0.16),
    highlight=HighlightSpec(share=0.06, rows=2),
    contact=ContactSpec(steps=(1, 1)),
    band=BandSeat(rows_above_brim=2, chromatic=True),
    crown_shadow=CrownShadow(depth=1, reach=2),
    targets=Targets(highlight_share=(0.0, 0.12), contact_delta=(-60.0, -3.0),
                    min_crown_levels=4, band_value_sign=0),
)

# FELT_BRIMMED — 33 hats.  The plain brimmed felt hat: fedora, bowler, trilby.
# Crown 4-7 rows over a 2-3 row brim.  Its band is the one that is NOT
# chromatic: same hue, value -16, pressed in.
FELT_BRIMMED = ConstructionTemplate(
    name="FELT_BRIMMED",
    architectures=("BRIMMED_HAT",),
    applies=_always,                       # this family's fallback
    highlight=HighlightSpec(share=0.07, rows=3),
    band=BandSeat(rows_above_brim=2, chromatic=False),
    targets=Targets(highlight_share=(0.0, 0.13), contact_delta=(-70.0, -5.0),
                    min_crown_levels=4, band_value_sign=-1),
)

# SOFT_CAP — 11 hats.  Beret, flat cap, toque: a shallow crown of 2-3 rows, no
# brim to speak of, and the strongest outline in the corpus (-70).  With so few
# rows the planes carry the form, so the lit share is the largest here.
SOFT_CAP = ConstructionTemplate(
    name="SOFT_CAP",
    architectures=("BRIMLESS_HAT",),
    applies=_shallow,
    brim_piece=None,
    planes=CrownPlanes(lit_share=0.22),
    highlight=HighlightSpec(share=0.08, rows=2, symmetric=True),
    band=BandSeat(rows_above_brim=1, chromatic=False),
    targets=Targets(highlight_share=(0.0, 0.16), contact_delta=(-70.0, -2.0),
                    min_crown_levels=3, band_value_sign=0),
)

# CLOSE_FIT — 21 hats.  Beanie, cloche, knitted cap: no brim at all (ratio
# 1.00), crown 6-7 rows, 7 colours, span 172, contact -20.  A knitted form is
# soft, so its planes turn later than a felt crown's.
CLOSE_FIT = ConstructionTemplate(
    name="CLOSE_FIT",
    architectures=("BRIMLESS_HAT",),
    applies=_always,                       # this family's fallback
    brim_piece=None,
    planes=CrownPlanes(top_turn=0.66, side_turn=0.58, lit_share=0.20),
    highlight=HighlightSpec(share=0.07, rows=3, symmetric=True),
    band=BandSeat(rows_above_brim=1, chromatic=False),
    targets=Targets(highlight_share=(0.0, 0.14), contact_delta=(-70.0, -4.0),
                    min_crown_levels=4, band_value_sign=-1),
)

TEMPLATES = {t.name: t for t in (TALL_CROWN, WIDE_BRIM, FELT_BRIMMED,
                                 SOFT_CAP, CLOSE_FIT)}


def select(names, meta: dict):
    """The template for this construction — DERIVED, never rolled.

    `names` is the Architecture's declared tuple, in priority order: the first
    whose `applies` predicate matches the geometry already resolved wins, and
    the family's fallback (`_always`) closes the set.  Returns None when the
    Architecture declares none, which keeps the old path reachable.
    """
    for name in names or ():
        tpl = TEMPLATES.get(name)
        if tpl is not None and tpl.applies(meta):
            return tpl
    return None


# ---------------------------------------------------------------------------
# realization — every routine takes cells and returns a plan over them
# ---------------------------------------------------------------------------

def _rows_of(cells: set) -> dict:
    out: dict[int, list[int]] = {}
    for (x, y) in cells:
        out.setdefault(y, []).append(x)
    return out


def _anchor_column(xs: list, anchor: str) -> float:
    lo, hi = xs[0], xs[-1]
    if anchor == "left":
        return lo + 0.25 * (hi - lo)
    if anchor == "right":
        return lo + 0.75 * (hi - lo)
    return (lo + hi) / 2.0


def crown_interior(cells: set, tpl: ConstructionTemplate) -> dict:
    """Planes + light patch + contact for one crown frame, as ramp offsets."""
    if not cells:
        return {}
    rows = _rows_of(cells)
    ys = sorted(rows)
    bottom = ys[-1]
    widest = max(len(r) for r in rows.values())
    tol = tpl.planes.shoulder_tolerance
    shoulder = next((y for y in ys if len(rows[y]) >= widest - tol), bottom)
    xs_all = sorted({x for x, _ in cells})
    col = _anchor_column(xs_all, tpl.highlight.anchor)

    out: dict = {}
    for y in ys:
        row = sorted(rows[y])
        lo, hi = row[0], row[-1]
        span = max(1, hi - lo)
        for x in row:
            t = (x - lo) / span
            if y <= shoulder:
                out[(x, y)] = (tpl.planes.top_lit if t < tpl.planes.top_turn
                               else tpl.planes.top_turned)
            else:
                out[(x, y)] = (tpl.planes.side_lit if t < tpl.planes.side_turn
                               else tpl.planes.side_shade)

    # the crown's own rim is never lighter than rim_min
    for (x, y) in list(out):
        if any((x + dx, y + dy) not in cells
               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            out[(x, y)] = max(out[(x, y)], tpl.planes.rim_min)

    # cap the lit part of the top plane, nearest the anchor column first
    if tpl.planes.top_lit < 0:
        lit_cells = [c for c, v in out.items() if v == tpl.planes.top_lit]
        allowed = max(1, round(len(cells) * tpl.planes.lit_share))
        if len(lit_cells) > allowed:
            lit_cells.sort(key=lambda c: (c[1], abs(c[0] - col), c[0]))
            for c in lit_cells[allowed:]:
                out[c] = tpl.planes.top_turned

    # the light patch: top plane, off the rim, near the anchor column
    lit = [c for c in cells if c[1] <= shoulder]
    if tpl.highlight.inset_from_edge:
        inner = [c for c in lit
                 if all((c[0] + dx, c[1] + dy) in cells
                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        lit = inner or lit
    if lit:
        budget = max(1, round(len(cells) * tpl.highlight.share))
        anchor_row = min(c[1] for c in lit)
        band = [c for c in lit if c[1] < anchor_row + tpl.highlight.rows]
        band.sort(key=lambda c: (c[1], abs(c[0] - col), c[0]))
        chosen = set(band[:budget])
        if tpl.highlight.symmetric:
            mid = xs_all[0] + xs_all[-1]
            chosen |= {(mid - x, y) for (x, y) in chosen if (mid - x, y) in cells}
        for c in chosen:
            out[c] = -tpl.highlight.depth

    # contact: the lowest rows step down, bottom first
    for i, y in enumerate(range(bottom, bottom - len(tpl.contact.steps), -1)):
        if y in rows:
            for x in rows[y]:
                out[(x, y)] = max(out.get((x, y), 0), 0) + tpl.contact.steps[i]
    return out


def brim_interior(cells: set, tpl: ConstructionTemplate) -> dict:
    """Upper surface / underside, per column, plus the same contact rows."""
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
                out[(x, y)] = tpl.brim.upper
            elif y == lowest:
                out[(x, y)] = tpl.brim.under
            else:
                out[(x, y)] = tpl.brim.mid
    for (x, y) in list(out):
        if (x + 1, y) not in cells or (x - 1, y) not in cells:
            out[(x, y)] = max(out[(x, y)], tpl.brim.rim_min)
    for i, y in enumerate(range(bottom, bottom - len(tpl.contact.steps), -1)):
        for x in cols:
            if y in cols[x]:
                out[(x, y)] = max(out.get((x, y), 0), tpl.contact.steps[i] + 1)
    return out


def crown_shadow_on_brim(crown: set, brim: set, tpl: ConstructionTemplate) -> dict:
    """Occlusion the crown casts on the brim's upper surface."""
    if not crown or not brim:
        return {}
    crown_cols = {x for x, _ in crown}
    crown_bottom = max(y for _, y in crown)
    return {(x, y): tpl.crown_shadow.depth for (x, y) in brim
            if x in crown_cols
            and crown_bottom < y <= crown_bottom + tpl.crown_shadow.reach}


def band_cells(crown: set, tpl: ConstructionTemplate,
               brim_line: int | None = None) -> set:
    """The row a band seats on, terminated inboard.  Subset of the crown.

    `brim_line` is the Architecture's own reference row — the widest row of a
    brimmed hat, the hem of a brimless one.  Without it the crown's own base
    stands in, which is the same row for any construction with no brim.
    """
    if not crown:
        return set()
    base = max(y for _, y in crown)
    ref = brim_line if brim_line is not None else base + 1
    row = ref - tpl.band.rows_above_brim
    cells = {c for c in crown if c[1] == row}
    if not cells:                       # a crown too short for its declared seat
        cells = {c for c in crown if c[1] == base}
    for _ in range(tpl.band.inset):
        cells = terminate_inboard(cells, run_axis=0)
    return cells


# ---------------------------------------------------------------------------
# application — called BY the Architecture's realize step
# ---------------------------------------------------------------------------

def apply(tpl: ConstructionTemplate, pieces: dict,
          views=("front", "side", "back")) -> None:
    """Author the interior of pieces the Architecture has already built.

    `pieces` is {name: Piece}.  Mutates shading and occlusion in place, then
    asserts no cell was added or removed.
    """
    crown = pieces.get(tpl.crown_piece)
    if crown is None:
        raise ValueError(f"{tpl.name} requires a '{tpl.crown_piece}' piece")
    brim = pieces.get(tpl.brim_piece) if tpl.brim_piece else None

    before = {name: {v: set(p.cells.get(v, set())) for v in views}
              for name, p in pieces.items()}

    crown.shading = {v: crown_interior(crown.cells.get(v, set()), tpl) for v in views}
    if brim is not None:
        brim.shading = {v: brim_interior(brim.cells.get(v, set()), tpl) for v in views}
        brim.occlusion = {v: crown_shadow_on_brim(crown.cells.get(v, set()),
                                                  brim.cells.get(v, set()), tpl)
                          for v in views}

    _assert_unchanged(tpl, pieces, before, views)


def _assert_unchanged(tpl, pieces: dict, before: dict,
                      views=("front", "side", "back")) -> None:
    """The one-owner guarantee, as its own callable so a test can exercise it."""
    after = {name: {v: set(p.cells.get(v, set())) for v in views}
             for name, p in pieces.items()}
    if before != after:
        raise AssertionError(
            f"{tpl.name} changed the silhouette; a template owns interior only")


# ---------------------------------------------------------------------------
# what the templates make CHECKABLE
# ---------------------------------------------------------------------------
#
# Each check returns (name, message) so a report says WHICH landmark went wrong
# on WHICH seed, instead of a score.  Thresholds come from the template's own
# `targets`, so a family with a legitimately different interior does not force
# a shared bar to be weakened.

def _connected(cells: set) -> bool:
    if not cells:
        return True
    seen, stack = set(), [next(iter(cells))]
    while stack:
        c = stack.pop()
        if c in seen:
            continue
        seen.add(c)
        x, y = c
        stack += [n for n in ((x+1, y), (x-1, y), (x, y+1), (x, y-1),
                              (x+1, y+1), (x-1, y-1), (x+1, y-1), (x-1, y+1))
                  if n in cells and n not in seen]
    return len(seen) == len(cells)


def _chromatic(colors: dict, band: set, crown: set, threshold: float = 25.0) -> bool:
    """Is the band a different HUE from the crown, or just a lighter stripe?"""
    import colorsys

    def hue(cells):
        hs = []
        for c in cells:
            col = colors.get(c)
            if not col:
                continue
            h, sat, _ = colorsys.rgb_to_hsv(col[0] / 255, col[1] / 255, col[2] / 255)
            if sat > 0.12:
                hs.append(h)
        return sum(hs) / len(hs) if hs else None

    bh, ch = hue(band), hue(crown)
    if bh is None or ch is None:
        return False
    d = abs(bh - ch)
    return min(d, 1 - d) * 360 > threshold


def verify(tpl: ConstructionTemplate, construction, raster, view: str = "front",
           art=None, architecture=None) -> list:
    """Named landmark checks against the FINAL pixels.  [] means clean.

    `art` is optional but strongly preferred: without it the crown checks read
    cells trim has painted over, and a band on the crown's own row makes the
    contact check report the band's colour instead of the crown's.  That was a
    real false positive — 13 of 40 seeds — and it is the kind of thing mistaken
    for a defect in the art rather than in the metric.
    """
    from ..grammar import luminance

    findings = []
    crown = construction.by_name(tpl.crown_piece)
    brim = construction.by_name(tpl.brim_piece) if tpl.brim_piece else None
    band = construction.by_name("band")
    colors = raster[view]
    if crown is None:
        return [("crown_missing", f"{tpl.name} declares a crown and there is none")]

    # Two sets, deliberately: the crown's GEOMETRY answers "is the band on its
    # declared seat"; the cells the crown still OWNS after trim composited
    # answer "how does the crown read".
    ccells = crown.view_cells(view)
    if not ccells:
        return [("crown_empty", "the crown has no cells in this view")]
    cpaint = ccells
    if art is not None:
        owned = {c for c, pc in art.paint.get(view, {}).items()
                 if pc.feature.split(":")[0] == tpl.crown_piece}
        cpaint = ccells & owned if owned else ccells
    lum = {c: luminance(colors[c]) for c in cpaint if c in colors}
    if not lum:
        return [("crown_unpainted", "the crown was painted over entirely")]

    top = min(y for _, y in ccells)
    bottom = max(y for _, y in ccells)
    peak = max(lum.values())
    body = sorted(lum.values())[len(lum) // 2]
    meta = getattr(construction, "meta", {}) or {}

    # 1. the light patch: planned vs rendered, then size, then shape.
    #
    # The template can recompute what it ASKED for, which is stronger than "is
    # it big": when more cells come out at peak than were ever planned, the
    # patch was painted over or two ramp steps merged.  Without a template both
    # cases look like the same number.
    hi = {c for c, v in lum.items() if v >= peak - 12}
    share = len(hi) / len(lum)
    plan = crown_interior(ccells, tpl)
    intended = {c for c, v in plan.items() if v == -tpl.highlight.depth}
    lo_t, hi_t = tpl.targets.highlight_share
    if intended and len(hi) > max(2, round(1.6 * len(intended))):
        findings.append(("highlight_bled",
                         f"{len(intended)} cells planned as highlight, {len(hi)} "
                         f"rendered at peak: painted over, or the top ramp steps merged"))
    elif not lo_t <= share <= hi_t:
        findings.append(("highlight_out_of_band",
                         f"{100*share:.0f}% of the crown is at peak; {tpl.name} "
                         f"declares {100*lo_t:.0f}-{100*hi_t:.0f}%"))
    if len(hi) > 2 and not tpl.highlight.symmetric and not _connected(hi):
        findings.append(("highlight_scattered",
                         f"the light is {len(hi)} cells in more than one patch"))
    if hi and min(y for _, y in hi) > top + tpl.highlight.rows:
        findings.append(("highlight_off_top_plane",
                         "the brightest cells are below the crown's top plane"))

    # 2. the contact edge, against this template's own declared range.
    #
    # Measured the way the corpus figure was measured: the SPRITE's
    # second-from-bottom row against the SPRITE's body median.  An earlier
    # version compared the crown's row against the crown's own median, which is
    # a different baseline — it reported 22 of 39 tall crowns as having no
    # contact edge while the same hats measured -30 against the corpus's -28.
    # A target is only meaningful next to the measurement it was derived from.
    sprite = {c: luminance(colors[c]) for c in construction.silhouette.get(view, set())
              if c in colors}
    row = [v for (x, y), v in sprite.items()
           if y == max(y for _, y in sprite) - 1] if sprite else []
    if row:
        sbody = sorted(sprite.values())[len(sprite) // 2]
        delta = sum(row) / len(row) - sbody
        lo_c, hi_c = tpl.targets.contact_delta
        if delta > hi_c:
            findings.append(("no_contact_edge",
                             f"the second-from-bottom crown row is {delta:+.0f} "
                             f"against the body; {tpl.name} wants {hi_c:+.0f} or darker"))
        elif delta < lo_c:
            findings.append(("contact_edge_too_heavy",
                             f"the contact row is {delta:+.0f}, past {tpl.name}'s "
                             f"floor of {lo_c:+.0f}"))

    # 3. the crown carries enough levels to read as a form
    levels = len({round(v) for v in lum.values()})
    if levels < tpl.targets.min_crown_levels:
        findings.append(("crown_too_flat",
                         f"{levels} luminance levels in the crown; {tpl.name} "
                         f"needs {tpl.targets.min_crown_levels}"))

    # 4. the band, if there is one, is SEATED and reads the right way round
    if band is not None:
        bcells = band.view_cells(view)
        expected = band_cells(ccells, tpl, meta.get("brim_line"))
        if bcells and not bcells <= ccells:
            findings.append(("band_off_crown",
                             f"{len(bcells - ccells)} band cells are not on the crown"))
        elif bcells and bcells != expected:
            findings.append(("band_unseated",
                             f"the band is not on {tpl.name}'s declared seat, "
                             f"{tpl.band.rows_above_brim} rows above the brim line"))
        blum = [luminance(colors[c]) for c in bcells if c in colors]
        # A same-hue band must read as pressed IN.  A chromatic accent is a
        # different material and is allowed to be lighter — BoysCap's is value
        # 74 against its crown — so only a same-hue one is flagged.
        if (blum and tpl.targets.band_value_sign < 0
                and sum(blum) / len(blum) > body
                and not _chromatic(colors, bcells, ccells)):
            findings.append(("band_not_recessed",
                             "a same-hue band is lighter than the crown it presses into"))

    # 5. the brim carries the crown's shadow
    if brim is not None and brim.view_cells(view):
        if not crown_shadow_on_brim(ccells, brim.view_cells(view), tpl):
            findings.append(("no_crown_shadow",
                             "the crown casts nothing onto the brim below it"))

    # 6. base flare — only where the Architecture has NOT declared it legal.
    #
    # A knitted cuff genuinely flares at the base and 22% of the corpus has one,
    # so this is a legality the Architecture declares (`allows_base_flare`), not
    # a universal.  Reported here because a flare that no Architecture asked for
    # means the hem taper and the cuff disagreed.
    if architecture is not None and not getattr(architecture, "allows_base_flare", False):
        sil = construction.silhouette.get(view, set())
        widths: dict = {}
        for (x, y) in sil:
            widths[y] = widths.get(y, 0) + 1
        if widths:
            lowest = max(widths)
            if widths[lowest] >= max(widths.values()) and lowest > min(widths) + 1:
                findings.append(("base_flare",
                                 "the lowest row is the widest and this "
                                 "Architecture does not declare a base flare"))
    return findings
