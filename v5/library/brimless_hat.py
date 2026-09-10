"""BRIMLESS_HAT — caps, beanies and other crown-only headwear.

The second HEAD Architecture.  Measured across 188 shipping hats, 59 are not
brimmed (crown no narrower than 1.15x its widest row) — 31% of real headwear
that `BRIMMED_HAT` cannot express at all.

Their envelope is almost identical to the brimmed group, which is why this
reuses the placement model wholesale rather than deriving a new one:

    cells 107   bbox 14 x 11   top row 4   bottom row 12   widest row 10
    (brimmed:   108        14 x 11              3       13            10)

So the only structural difference is the brim: a cap's crown descends to the
head instead of flaring away from it.  Everything else — HEAD_BOX, centring,
outlining, no enclosed holes, hair policy, the crown profile vocabulary and the
protrusion library — is shared with BRIMMED_HAT and imported from it.
"""

from __future__ import annotations

from ..construction import Construction, Piece
from ..contracts import ArchitectureContract, IdentitySeparation, register_architecture
from ..grammar import (HAT_BRIMLESS_BOUNDS, HEAD_BOX, PLANE, Envelope,
                       head_box, terminate_inboard)
from ..schema import (APPEARANCE, IDENTITY, ORNAMENT, REPAIR_RETRY, STRUCTURAL,
                      Variable)
from .brimmed_hat import (ASYM_LEFT, ASYM_RIGHT, CROWN_MIN_ROW, CROWN_PROFILES,
                          HAT, _crown_shading, apply_asymmetry,
                          asymmetry_options, crown_median_width, fill_back,
                          span)
from . import hat_templates
from .hat_motifs import (DIRECTIONAL_OPTIONS, PROTRUSIONS, apply_protrusion,
                         directional_cells, directional_options,
                         protrusion_options)

# The Family gains a second Architecture.  Weighted below BRIMMED because the
# corpus is 59 brimless against 129 brimmed.
HAT.architectures["BRIMLESS_HAT"] = 0.44

# A cap's crown reaches the bottom of the head box; the corpus median bottom
# row for this group is 12, which is HEAD_BOX's last row.
HEM_ROWS = (11, 12, 13)

# Above this the shape stops reading as a cap and starts reading as a brimmed
# hat whose brim happens to be short.  `crown_metrics` uses the same 1.15.
MAX_FLARE = 1.15

# A cap is a shaped dome over a straight section.  The straight rows must
# outnumber the shaped ones or the median crown row falls below the widest and
# the shape reads as brimmed.
#
# The dome takes each profile's OWN length — its rows up to the point it
# reaches full width — capped so the straight section still dominates.  A fixed
# three rows collapsed the vocabulary: ROUND and DOMED both truncated to
# (4, 3, 2), and between them they are 46% of brimless rolls, so nearly every
# cap came out the same dome and the whole Architecture read as one shape in
# different colours.
CAP_HEIGHT = 11
DOME_ROWS = 3

# Inset applied to the last rows, BOTTOM ROW FIRST — the cap curving in onto
# the head rather than ending as a flat slab.  The corpus always narrows here
# (56 of 59 narrower at the bottom, 3 flat, none widen), so there is no
# beanie-cuff shape to author — but it narrows in several distinct ways, and we
# had exactly one of them hardcoded, and it was among the rarest.
#
# Measured over the 59 brimless corpus hats, rows below the last full-width row:
#     (1,)      8 hats   one row, barely in      <- commonest
#     (3, 6)    7        two rows, dropping fast
#     (3,)      6        one row, sharply in
#     (1, 2, 3) 2        three rows, gentle      <- what we had hardcoded
HEM_TAPERS = {
    "TIGHT": (1,),
    "DROP":  (3,),
    "FLARE": (6, 3),
    "SOFT":  (3, 2, 1),
}

# Caps get their OWN authored domes rather than borrowing the brimmed crown
# profiles.  Two reasons, both measured:
#
#  * Truncating the brimmed profiles to the rows a cap can afford collapsed the
#    vocabulary — ROUND and DOMED both became (4, 3, 2), and together they are
#    46% of brimless rolls, so nearly every cap came out the same dome in a
#    different colour.
#  * The dome cannot simply be deepened to separate them.  `crown_metrics`
#    classifies by the MEDIAN row, so the full-width section has to outnumber
#    the shaped rows; with an 11-row cap and a 3-row hem taper that caps the
#    dome at 3.  Deeper domes pushed 50 of 62 caps back over the 1.15 flare and
#    they re-classified as brimmed.
#
# So the fix is authored shape, not more rows: seven distinct three-row domes.
CAP_DOMES = {
    "ROUND":     (3, 2, 1),
    "DOMED":     (4, 2, 1),
    "SHALLOW":   (2, 1, 0),
    "TALL_FLAT": (1, 1, 0),      # a flat-topped cap
    "STOVEPIPE": (4, 3, 3),      # straight-sided, narrow
    "PINCHED":   (3, 1, 1),
    "STEPPED":   (4, 4, 3),      # a squared shoulder, sharp enough for side ears
    # A fast shoulder: apex, one transitional row, then full width.  This is
    # the baseball/trucker cap shape — Trucker Hat #16 runs 4, 8, 10 and then
    # holds 10 for six rows.  Every other dome here eases in over three rows.
    "FAST":      (3, 1, 0),
}

# A cap's HEIGHT belongs to its authored dome, exactly as a brimmed crown's
# height belongs to its authored profile.  It was a single module constant,
# which meant every cap was eleven rows tall whatever shape it was — and the
# baseball family is not: vanilla's Trucker #16 runs from row 4 to row 12, nine
# rows, and forcing it to eleven put two rows of crown above the reference and
# accounted for most of that reconstruction's error.  Everything except FAST
# keeps the eleven rows it had, so nothing else changes.
CAP_HEIGHTS = {name: CAP_HEIGHT for name in CAP_DOMES}
CAP_HEIGHTS["FAST"] = 9


def cap_height(crown_profile: str) -> int:
    return CAP_HEIGHTS.get(crown_profile, CAP_HEIGHT)


def dome_of(crown_profile: str) -> tuple:
    return CAP_DOMES[crown_profile]


# --- BASE FLARE (a knitted cuff) --------------------------------------------
#
# 25 of the 112 vanilla hats (22%) end WIDER than the row above rather than
# narrowing in — a rolled cuff on a beanie, the fur band on a winter hat, the
# turn-up on a watch cap.  Every shape in this Architecture narrows at the
# bottom, so a fifth of real headwear had no expression here at all.
#
# It is not a brim: it does not overhang the head, it is two rows tall, and it
# is the crown's own fabric turned back on itself.  `crown_metrics` still has
# to read the cap as brimless, so the flare is capped at +2 columns and is only
# offered where the resulting ratio stays under the 1.15 that separates the two
# Architectures — which is crown_width 14 and up.
CUFF_ROWS = 2
CUFF_FLARE = 1                   # inset per side, so the base is 2 columns wider
CUFF_MIN_WIDTH = 14              # (14+2)/14 = 1.14, just inside the threshold


def cuff_options(crown_width: int, contract=None) -> tuple:
    if not getattr(contract, "allows_base_flare", False):
        return ("NONE",)
    if crown_width < CUFF_MIN_WIDTH:
        return ("NONE",)
    return ("NONE", "CUFF")


def cap_median_width(crown_profile: str, crown_width: int,
                    hem_taper: str = "TIGHT") -> int:
    """The crown width the corpus metric will report for a CAP.

    `crown_median_width` reads the BRIMMED profile table, which this
    Architecture does not draw.  Sharing it worked only while the two
    vocabularies happened to use the same names.
    """
    return sorted(cap_row_widths(crown_profile, crown_width, hem_taper))[
        cap_height(crown_profile) // 2]


def cap_row_widths(crown_profile: str, crown_width: int,
                   hem_taper: str) -> list:
    dome = CAP_DOMES[crown_profile]
    taper = HEM_TAPERS[hem_taper]
    height = cap_height(crown_profile)
    widths = []
    for i in range(height):
        inset = dome[i] if i < len(dome) else 0
        from_bottom = height - 1 - i
        if from_bottom < len(taper):
            inset = max(inset, taper[from_bottom])
        widths.append(max(CROWN_MIN_ROW, crown_width - 2 * inset))
    return widths


def estimate_fill(crown_profile: str, crown_width: int, hem_taper: str) -> float:
    """Bbox fill the combination would produce.

    The dome and the hem taper are the only two places a cap is shaped.  A fast
    dome plus a tight hem leaves almost nothing shaped and the cap renders as a
    rectangle — fill 0.96 against a corpus median of 0.78.  Neither choice is
    wrong alone; it is the pairing that fails, so it is checked as a pairing.
    """
    widths = cap_row_widths(crown_profile, crown_width, hem_taper)
    return sum(widths) / (max(widths) * len(widths))


def declare_schema(family, arch, ctx, record):
    return [
        Variable("silhouette", arch.name, "structural", tuple(arch.silhouettes),
                 weights=arch.silhouettes, significance=IDENTITY,
                 cost=0, cost_tag=STRUCTURAL, stream="structure"),
        Variable("crown_profile", arch.name, "structural", tuple(CAP_DOMES),
                 weights={"ROUND": 0.21, "DOMED": 0.19, "SHALLOW": 0.17,
                          "TALL_FLAT": 0.11, "STOVEPIPE": 0.05,
                          "PINCHED": 0.07, "STEPPED": 0.08, "FAST": 0.12},
                 significance=IDENTITY, cost=0, cost_tag=STRUCTURAL,
                 stream="structure"),
        # The widest crown row, as in BRIMMED_HAT.
        # 10 is the corpus floor for a brimless crown and the width the
        # baseball family actually uses (vanilla #16 holds 10 for six rows).
        Variable("crown_width", arch.name, "structural", (10, 12, 14, 16),
                 weights={10: 0.14, 12: 0.36, 14: 0.34, 16: 0.16},
                 significance=IDENTITY,
                 cost=0, cost_tag=STRUCTURAL, stream="structure",
                 repair=REPAIR_RETRY, repair_attempts=8,
                 # Measured against the BRIMLESS corpus bound (10-16, median
                 # 14), not the brimmed one (5-12).  This validator used
                 # `crown_median_width`, which reads the brimmed profile table
                 # this Architecture does not draw — it agreed by accident for
                 # the names both tables share.  Pointing it at the cap's own
                 # rows exposed the second half of the mistake: against a 12
                 # ceiling meant for crowns that taper, no cap wider than 12
                 # was admissible at all, and the corpus median is 14.
                 validate=lambda v, r, c: (
                     HAT_BRIMLESS_BOUNDS["crown_width"][0]
                     <= cap_median_width(r.get("crown_profile"), v)
                     <= HAT_BRIMLESS_BOUNDS["crown_width"][1]
                     and cap_median_width(r.get("crown_profile"), v) >= 0.55 * v)),
        # Where the cap meets the head.  Corpus median bottom row is 12.
        Variable("hem_row", arch.name, "structural", HEM_ROWS,
                 weights={11: 0.28, 12: 0.46, 13: 0.26}, significance=IDENTITY,
                 cost=0, cost_tag=STRUCTURAL, stream="structure",
                 repair=REPAIR_RETRY, repair_attempts=8,
                 # The cap must fit above the hem and still start in frame.
                 # This read the BRIMMED profile length, not the cap's own
                 # height, so it was checking a number this Architecture does
                 # not use.
                 validate=lambda v, r, c: 0 <= v - cap_height(
                     r.get("crown_profile")) + 1 <= 7),
        Variable("hem_taper", arch.name, "structural", tuple(HEM_TAPERS),
                 weights={"TIGHT": 0.34, "DROP": 0.26, "FLARE": 0.24,
                          "SOFT": 0.16}, significance=IDENTITY,
                 cost=0, cost_tag=STRUCTURAL, stream="structure",
                 repair=REPAIR_RETRY, repair_attempts=8,
                 validate=lambda v, r, c: estimate_fill(
                     r.get("crown_profile"), r.get("crown_width"), v) < 0.92),
        Variable("protrusion", arch.name, "structural",
                 ("NONE",) + tuple(PROTRUSIONS),
                 # EARS_SIDE is weighted high because it is legal on only two
                 # crown profiles — the ones with a sharp enough shoulder — so
                 # its realised rate lands beside EARS_TOP rather than above it.
                 weights={"NONE": 0.72, "EARS_TOP": 0.09, "EARS_SIDE": 0.15,
                          "EARS_TALL": 0.0, "CROWN_CREASE": 0.04},
                 significance=IDENTITY, cost=0, cost_tag=STRUCTURAL,
                 stream="structure", repair=REPAIR_RETRY, repair_attempts=8,
                 validate=lambda v, r, c: v in protrusion_options(
                     r.get("crown_profile"), arch.name, r.get("crown_width"))),
        # A turned-back cuff at the base.  Declaration-gated on
        # `allows_base_flare`, and only offered on crowns wide enough that the
        # flare stays under the brimless/brimmed threshold.
        Variable("cuff", arch.name, "structural", ("NONE", "CUFF"),
                 weights={"NONE": 0.74, "CUFF": 0.26}, significance=IDENTITY,
                 cost=0, cost_tag=STRUCTURAL, stream="structure",
                 repair=REPAIR_RETRY,
                 validate=lambda v, r, c: v in cuff_options(
                     r.get("crown_width"), arch)),
        Variable("directional", arch.name, "structural", DIRECTIONAL_OPTIONS,
                 weights={"NONE": 0.70, "VISOR": 0.22, "TAIL": 0.08},
                 significance=IDENTITY, cost=0, cost_tag=STRUCTURAL,
                 stream="structure", repair=REPAIR_RETRY, repair_attempts=8,
                 validate=lambda v, r, c: v in directional_options(
                     arch.name, r.get("crown_profile"), arch)),
        Variable("asymmetry", arch.name, "structural",
                 ("NONE", "TIP_LEAN", "CROWN_DENT"),
                 weights={"NONE": 0.70, "TIP_LEAN": 0.18, "CROWN_DENT": 0.12},
                 significance=APPEARANCE, cost=0, cost_tag=STRUCTURAL,
                 stream="structure", repair=REPAIR_RETRY,
                 # One shape decision per hat: asymmetry displaces the crown
                 # that a protrusion is anchored to, so a leaned or dented
                 # crown left the ears sitting on geometry that had moved.
                 activation=lambda r, c: r.opt("protrusion") in (None, "NONE"),
                 # BRIM_FLICK and SIDE_TUFT need a brim / are retired
                 validate=lambda v, r, c: v in asymmetry_options(
                     r.get("crown_profile"), "TAPERED")),
        Variable("asym_side", arch.name, "structural", (ASYM_LEFT, ASYM_RIGHT),
                 weights={ASYM_LEFT: 0.66, ASYM_RIGHT: 0.34},
                 significance=APPEARANCE, cost=0, cost_tag=STRUCTURAL,
                 stream="structure",
                 activation=lambda r, c: r.opt("asymmetry") not in (None, "NONE")),
        Variable("material", arch.name, "structural", tuple(arch.materials),
                 weights=dict(arch.materials), significance=APPEARANCE,
                 cost=0, cost_tag=STRUCTURAL, stream="material"),
        Variable("color_architecture", arch.name, "structural",
                 tuple(arch.color_architectures),
                 weights=dict(arch.color_architectures), significance=IDENTITY,
                 cost=0, cost_tag=STRUCTURAL, stream="color"),
        Variable("harmony", arch.name, "structural",
                 ("complementary", "analogous", "split_complement"),
                 weights={"complementary": 0.4, "analogous": 0.4,
                          "split_complement": 0.2},
                 significance=APPEARANCE, cost=0, cost_tag=STRUCTURAL,
                 stream="color"),
        Variable("band", arch.name, "ornament", (True, False),
                 weights={True: 0.55, False: 0.45}, significance=APPEARANCE,
                 cost={True: 1, False: 0}, cost_tag=ORNAMENT, stream="ornament",
                 activation=lambda r, c: c.budget.remaining >= 1),
    ]


# Late-bound so `realize` can read the contract that declares it, the same
# pattern BRIMMED_HAT uses.
BRIMLESS_HAT_CONTRACT = [None]


def realize(spec, env: Envelope) -> Construction:
    if (env.width, env.height) != (20, 20):
        raise ValueError(
            f"BRIMLESS_HAT has no authored geometry for {env.width}x{env.height}")
    p = spec.parameters
    x0, x1, y0, y1 = head_box(env)
    cw = p.get("crown_width", 14)
    hem = p.get("hem_row", 12)
    # Only the TOP of the profile is used — a cap is a dome over a straight
    # section, not a full-height silhouette.  Taking the whole profile left no
    # straight rows at all, so the median crown row came out narrower than the
    # widest and `crown_metrics` reported a 1.20 flare: the shape classified as
    # brimmed, which is the one thing this Architecture must not be.
    profile = p.get("crown_profile", "ROUND")
    insets = dome_of(profile)
    crown_top = max(0, hem - cap_height(profile) + 1)

    crown = {"front": set(), "side": set(), "back": set()}
    crown_rows = {}
    for row in range(crown_top, hem + 1):
        i = row - crown_top
        inset = insets[i] if i < len(insets) else 0
        # The cap also draws back in where it meets the head.  Without it the
        # shape is a solid block: fill ratio 0.88 against the corpus median of
        # 0.78, and the mass overran the cell bound.
        from_bottom = hem - row
        taper = HEM_TAPERS[p.get("hem_taper", "TIGHT")]
        if from_bottom < len(taper):
            inset = max(inset, taper[from_bottom])
        # A cuff REPLACES the hem taper on the rows it occupies: the fabric is
        # turned back, so the base flares out instead of drawing in.
        if p.get("cuff") == "CUFF" and from_bottom < CUFF_ROWS:
            inset = -CUFF_FLARE
        cols = span(max(CROWN_MIN_ROW, cw - 2 * inset), env)
        crown_rows[row] = cols
        cells = {(x, row) for x in cols}
        crown["front"] |= cells
        crown["side"] |= cells

    apply_asymmetry(p.get("asymmetry", "NONE"), p.get("asym_side", ASYM_LEFT),
                    crown, {v: set() for v in crown}, crown_rows, env)
    apply_protrusion(p.get("protrusion", "NONE"), crown, crown_rows, env)

    # Back frame derived from the finished front — the corpus rule, shared
    # with BRIMMED_HAT.  A cap's crown IS its lowest piece, so it extends.
    fill_back(crown, env, extend=True)

    crown_piece = Piece("crown", "body", z=0, wrap=PLANE,
                        surface_domain="crown", cells=crown)
    # Same rule as BRIMMED_HAT: the interior is derived from the geometry this
    # Architecture just resolved.  A 2-row crown is a SOFT_CAP; anything deeper
    # is a CLOSE_FIT knitted form.  No brim piece exists here, and the template
    # declares that rather than assuming one.
    tpl_meta = {"crown_height": hem - crown_top + 1, "crown_width": cw,
                "brim_width": 0, "brim_line": hem + 1, "overhang": (0, 0)}
    tpl = hat_templates.select(
        BRIMLESS_HAT_CONTRACT[0].construction_templates
        if BRIMLESS_HAT_CONTRACT[0] is not None else (), tpl_meta)
    if tpl is not None:
        hat_templates.apply(tpl, {"crown": crown_piece})
    else:
        crown_piece.shading = {v: _crown_shading(c) for v, c in crown.items()}
    pieces = [crown_piece]

    # A visor or a hanging tail: present in the side frames only, built from
    # the finished crown so it cannot displace a single cell of it.
    dmotif = p.get("directional", "NONE")
    if dmotif != "NONE":
        dcells = directional_cells(dmotif, crown, env)
        if any(dcells.values()):
            dp = Piece("hanging", "body", z=1, wrap=PLANE, cells=dcells)
            dp.shading = {v: {c: 1 for c in cells} for v, cells in dcells.items()}
            pieces.append(dp)

    if p.get("band"):
        band_row = hem - 1
        band, shading = {}, {}
        depth = tpl.band.depth if tpl is not None else 1
        for view in ("front", "side"):
            if tpl is not None:
                cells = hat_templates.band_cells(crown[view], tpl, hem + 1)
            else:
                cells = terminate_inboard(
                    {c for c in crown[view] if c[1] == band_row}, run_axis=0)
            band[view] = cells
            shading[view] = {c: depth for c in cells}
        fill_back(band, env)
        shading["back"] = {c: depth for c in band["back"]}
        if any(band.values()):
            pieces.append(Piece("band", "trim", z=1, wrap=PLANE, identity=True,
                                zones=("collar:center",), cells=band,
                                shading=shading))

    silhouette = {v: set().union(*(pc.cells.get(v, set()) for pc in pieces))
                  for v in ("front", "side", "back")}
    construction = Construction(env=env, silhouette=silhouette, pieces=pieces,
                                surface_domains={"crown": ("crown",)})
    # Same dict the template selection ran on, plus the template it chose.
    construction.meta = dict(tpl_meta)
    construction.meta.update({"crown_top": crown_top, "hem_row": hem,
                             "head_box": (x0, x1, y0, y1),
                             "template": tpl.name if tpl is not None else None})
    return construction


BRIMLESS_HAT = register_architecture(ArchitectureContract(
    name="BRIMLESS_HAT",
    family="HAT",
    closure="NONE",
    aperture="OPEN_BASE",
    limb="NONE",
    topology=("crown",),
    silhouettes={"brimless": 1.0},
    layer_slots_opened=(),
    coverage_range=("HEAD",),
    surface_domains=("crown",),
    occupancy=(("collar:center", "band", "conditional_share"),),
    base_cost=1,
    trim=("band", ("band",)),
    identity_pairs=(
        IdentitySeparation("trim", "body", floor_scale=0.60, needs="band"),
    ),
    identity_floor=38.0,
    identity_retention=1.0,
    identity_composite_floor=0.0,
    max_appearance_features=3,
    # A cap can genuinely enclose the head, so this is the first Architecture
    # where HIDE is a live option — but it must still pass `covers_whole_head`,
    # and PRESERVE stays the default until in-game review says otherwise.
    hair_policy="PRESERVE",
    # A 2-3 row crown is a beret / flat cap; anything deeper is a knitted
    # close-fitting form.  Derived from the resolved geometry, not rolled.
    construction_templates=("SOFT_CAP", "CLOSE_FIT"),
    # A cap is where a directional piece belongs: the peaked-cap family is
    # defined by a visor that only exists in profile.
    allows_directional_pieces=True,
    # A cap may end in a turned-back cuff — 22% of the corpus does.
    allows_base_flare=True,
    color_architectures={"MONOCHROME_CONTRAST_TRIM": 0.18,
                         "DARK_BODY_LIGHT_COLLAR": 0.20,
                         "LIGHT_BODY_DARK_COLLAR": 0.18,
                         "CHROMATIC_BAND": 0.26,
                         "MUTED_BAND": 0.18},
    materials={"cotton_drill": 0.26, "wool_melton": 0.28, "linen": 0.18,
               "heavy_canvas": 0.18, "silk_satin": 0.10},
    declare_schema=declare_schema,
    realize=realize,
    style_hook=None,
))

BRIMLESS_HAT_CONTRACT[0] = BRIMLESS_HAT
