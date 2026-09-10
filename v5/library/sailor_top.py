"""SAILOR_TOP family + CLASSIC_SQUARE_FLAP architecture.

This module is pure authoring: a Family vocabulary, one Architecture
commitment, the child schema that Architecture publishes, and the authored
8x8 construction pieces it realizes.  The resolver contains no sailor-specific
control flow.
"""

from __future__ import annotations

from ..color import COLOR_ARCHITECTURES, HARMONIES
from ..construction import Construction, Piece, parse_art, parse_shading
from ..contracts import (ArchitectureContract, FamilyContract, IdentitySeparation,
                         register_architecture, register_family)
from ..grammar import GIRTH, PLANE, Envelope
from ..material import MATERIALS
from ..ornament import DETAIL_PACKAGES, ORNAMENTS
from .sailor_motifs import (FLAP_EDGES, SLEEVE_CAPS, TIE_EXTENT, TIE_LIBRARY,
                            apply_flap_edge, build_tie, flap_outline, hem_shadow)
from ..schema import (APPEARANCE, IDENTITY, ORNAMENT, REPAIR_DROP, REPAIR_RETRY,
                      STRUCTURAL, SUBTLE, SURFACE, Variable)

# ---------------------------------------------------------------------------
# TIER 3 — FAMILY VOCABULARY (what is conceivable)
# ---------------------------------------------------------------------------

SAILOR_TOP = register_family(FamilyContract(
    name="SAILOR_TOP",
    slot="TOP",
    architectures={"CLASSIC_SQUARE_FLAP": 0.5, "MIDDY_YOKE": 0.5},
    closure_vocabulary=("PULLOVER",),
    aperture_vocabulary=("SAILOR_FLAP",),
    limb_vocabulary=("SLEEVED",),
    # The reference sheets present the sailor as a mix-and-match kit: any collar
    # with any tie with any flap edge.  So the tie is ONE family-level slot that
    # every Architecture opens, not a per-Architecture invention.
    layer_slot_vocabulary=("neck_tie",),
    material_vocabulary=("cotton_drill", "wool_melton", "linen", "heavy_canvas", "silk_satin"),
    coverage_domain=("REGULAR",),
    color_architecture_vocabulary=(
        "DARK_BODY_LIGHT_COLLAR", "LIGHT_BODY_DARK_COLLAR", "MONOCHROME_CONTRAST_TRIM",
        "LOW_CONTRAST_STRONG_ACCENT", "SPLIT_BODY_ACCENT", "CONTRAST_UNDER_LAYER",
        "DARK_YOKE_LIGHT_BLOUSE", "DARK_YOKE_TONAL", "SAILOR_WHITE_NAVY",
    ),
    surface_capabilities=("body", "insert", "shell", "blouse"),
    style_hook=None,
))


# ---------------------------------------------------------------------------
# AUTHORED SILHOUETTES (closed set — INV-10)
# ---------------------------------------------------------------------------

CLASSIC_SQUARE_FLAP_NAME = "CLASSIC_SQUARE_FLAP"

# The back's shoulder line: row 0 is the collar/yoke over the neck, so the
# shoulder corner where the shirt re-emerges beside the flap starts one row
# below it.  Shared by both Architectures.
SHOULDER_ROW = 1

# The tie wraps onto the side view, tapering back from the front edge, instead
# of stopping at the shoulder seam.  Offsets from (front edge, tie row).
# A tie seen in PROFILE is a sliver at the front edge, not a slab.  Authored
# four cells wide at the knot row it put a large accent-coloured triangle on
# the front half of the side frame — the chest mass that "protrudes too much
# and reads blocky/stiff instead of a natural side wrap" (000).  Two cells at
# the knot, tapering to one, is what the reference side frames carry.
TIE_SIDE_SHADING = {(0, 0): -1, (-1, 0): 0,
                    (0, 1): 1, (-1, 1): 2,
                    (0, 2): 2}

# Same silhouette treatment as MIDDY, with CLASSIC's own assets: a two-row neck
# opening (the corpus floor, opaque at cols 3-4 in only 5% of frames) so the V
# reads as an opening rather than a shape painted on a solid bar, plus one
# notched-shoulder variant.
SILHOUETTES = {
    "tailored_regular": {
        "front": ["###..###", "###..###", "########", "########",
                  "########", "########", ".######.", ".######."],
        "side":  ["###.##..", "#######.", "#######.", "#######.",
                  "#######.", "#######.", ".#####..", ".#####.."],
        "back":  ["########", "########", "########", "########",
                  "########", "########", ".######.", ".######."],
    },
    "relaxed_regular": {
        "front": ["###..###", "###..###", "########", "########",
                  "########", "########", "########", "########"],
        "side":  ["###.##..", "#######.", "#######.", "#######.",
                  "#######.", "#######.", "######..", "######.."],
        "back":  ["########", "########", "########", "########",
                  "########", "########", "########", "########"],
    },
    # The strap read is carried by the collar treatment, NOT by holes in the
    # silhouette.  Authored with gaps it produced three separate in-game
    # defects: row 0 `##.##.##` split the neck opening into two 1px slots
    # either side of a fabric bridge (001, "reads as a split hole"), the third
    # notch row put the opening a row deeper than any shipping sailor shirt,
    # and back row 2 `.######.` bit a 1px notch out of each side with fabric
    # both above and below it (002, 011, "armpit / side hole").  No frame in
    # the reference pack contains an enclosed gap of any kind.
    "strap_regular": {
        "front": ["###..###", "###..###", "########", "########",
                  "########", "########", "########", ".######."],
        "side":  ["###.##..", "#######.", "#######.", "#######.",
                  "#######.", "#######.", "######..", "######.."],
        "back":  ["########", "########", "########", "########",
                  "########", "########", ".######.", ".######."],
    },
}

# First fully opaque centre row: where the V may begin.
CLASSIC_NOTCH = {"tailored_regular": 2, "relaxed_regular": 2, "strap_regular": 2}

# Authored dickey interiors, keyed by neckline depth.  The insert is a lit panel
# with its lowest row shaded where the collar tip closes over it.
# The top row carries the neck shadow at the two centre columns — the cells
# directly under the neck opening, where the dickey recedes into the collar.
# Authored `..MLLM..` it did the opposite: the cells under the chin were the
# BRIGHTEST on the panel and its top edge butted flat against the 2-wide neck
# hole, so the dickey read as a rectangular box under the chin (083).
#
# The shadow is written as light on the outer pair rather than dark on the
# centre pair.  A dickey whose role sits at the bottom of its ramp — every
# DARK_BODY_LIGHT_COLLAR roll — cannot be darkened any further, so authoring
# the centre darker collapsed all four cells into one colour.  Lightening
# outward keeps the same one-step relationship at every ramp position.
#
# Measured over seeds 0-95: `..MLLM..` put the brightest cells of the panel
# under the chin on 46 of 47 CLASSIC rolls; `..HMMH..` leaves 12, every one of
# them a roll where the AA edge pass spent the ramp separating a light collar
# from a light dickey.  That override is correct and is left alone.
INSERT_STENCILS = {
    2: ["..HMMH..",
        "...SS..."],
    3: ["..HMMH..",
        "..LHHL..",
        "...SS..."],
    4: ["..HMMH..",
        "..LHHL..",
        "..MLLM..",
        "...SS..."],
}

# Authored collar interior for the rows ABOVE the V — the same idea as MIDDY's
# YOKE_STENCILS, and the reason MIDDY's fronts read as a yoke worn on shoulders
# while CLASSIC's read as a slab.  Filling these rows with one flat value gave
# every roll two or three rows of a single colour across the whole frame, which
# in-game validation called a flat horizontal band (013, 014) and "front collar
# mass too wide/flat relative to the centre insert" (040).
#
# A sailor collar lies ON the shoulders: the outer shoulder turns away from the
# light and the fold beside the neck opening catches it.  Keyed by silhouette,
# not by depth, because each silhouette cuts its neck opening differently and a
# stencil has to line up with the hole it is drawn around.
#   D deepest  S shadow  M base  L light  H highlight  . no opinion
COLLAR_SHOULDER_STENCILS = {
    "tailored_regular": ["SML..LMS",
                         "MLH..HLM"],
    "relaxed_regular":  ["SML..LMS",
                         "MLH..HLM"],
    # `##.##.##`: the neck opening is cut either side of a centre strap, so the
    # strap carries the light and the two gaps sit outboard of it.
    "strap_regular":    ["SM.LL.MS",
                         "SML..LMS",
                         "MLH..HLM"],
}

# CLASSIC side motifs, offset from (front edge, collar row).  The V does not stop
# at the shoulder seam: its end wraps onto the side, and the dickey shows below
# it, so the side frame describes the same garment as the front.
COLLAR_SIDE_TAIL = {(0, 0): 0, (-1, 0): 1, (0, 1): 1}
INSERT_SIDE_MOTIF = {(0, 0): -1, (0, 1): 0}


def _tie_variable(arch, anchor_row_of, last_row: int = 7):
    """The shared tie slot.  T8 "None" is the variable never existing (INV-03)."""
    def fits(value, record, ctx):
        # A tie may not run into the rows another piece owns: the hem stays the
        # hem, and on MIDDY the blouse keeps its row.  Bounded repair picks a
        # shorter tie from the same domain rather than moving anything else.
        return anchor_row_of(record) + TIE_EXTENT[value] <= last_row

    def opened(record, ctx):
        # "Open collar, no tie" is 1 of the 5 classic variants on both reference
        # sheets, so the slot stays shut about a fifth of the time.  When it is
        # shut the variable is never instantiated — there is no tie_style=None.
        return ("neck_tie" in arch.layer_slots_opened
                and ctx.streams("layer").chance(0.80)
                and ctx.claim_layer("neck_tie"))

    return Variable(
        "tie_style", arch.name, "layer", tuple(TIE_LIBRARY),
        weights={"STANDARD_KNOT": 0.26, "SHORT_KNOT": 0.12, "LONG_TIE": 0.14,
                 "LARGE_BOW": 0.20, "DOUBLE_BOW": 0.10, "THIN_RIBBON": 0.10,
                 "CROSS_TIE": 0.08},
        significance=APPEARANCE, activation=opened,
        # The plain knots are family identity, not added busyness, so they cost
        # nothing; only the elaborate bows spend from the pool.
        cost={"STANDARD_KNOT": 0, "SHORT_KNOT": 0, "THIN_RIBBON": 0,
              "LONG_TIE": 1, "LARGE_BOW": 1, "DOUBLE_BOW": 1, "CROSS_TIE": 1},
        cost_tag=ORNAMENT, repair=REPAIR_RETRY, validate=fits, stream="layer")


def _flap_edge_variable(arch):
    """Reference section 4: F4 Rounded / F5 Pointed change the flap OUTLINE only."""
    return Variable("flap_edge", arch.name, "structural", FLAP_EDGES,
                    weights={"SQUARE": 0.52, "ROUNDED": 0.30, "POINTED": 0.18},
                    significance=APPEARANCE, cost=0, cost_tag=STRUCTURAL,
                    stream="structure")


def _sleeve_cap_variable(arch):
    return Variable("sleeve_cap", arch.name, "structural", tuple(SLEEVE_CAPS),
                    weights={"PLAIN": 0.72, "PUFF": 0.28}, significance=SUBTLE,
                    cost=0, cost_tag=STRUCTURAL, stream="structure")


def _build_tie_piece(front_cells, front_shading, front_edge, tie_row, sil, *, z):
    """One tie piece, built the same way for every Architecture."""
    side_cells, side_shading = set(), {}
    for (dx, dy), shade in TIE_SIDE_SHADING.items():
        cell = (front_edge + dx, tie_row + dy)
        if cell in sil["side"] and dy <= max(c[1] for c in front_cells) - tie_row:
            side_cells.add(cell)
            side_shading[cell] = shade
    tie = Piece("tie", "accent", z=z, wrap=PLANE, identity=True,
                zones=("chest:center",), form="knot",
                cells={"front": set(front_cells), "side": side_cells})
    tie.shading["front"] = dict(front_shading)
    tie.shading["side"] = side_shading
    tie.free_edges["front"] = {c for c in front_cells
                               if (c[0], c[1] + 1) not in front_cells}
    tie.free_edges["side"] = {c for c in side_cells if (c[0], c[1] + 1) not in side_cells}
    tie.occlusion["front"] = {(x, r + 1): 1 for (x, r) in tie.free_edges["front"]
                              if (x, r + 1) in sil["front"] and (x, r + 1) not in front_cells}
    tie.occlusion["side"] = {(x, r + 1): 1 for (x, r) in tie.free_edges["side"]
                             if (x, r + 1) in sil["side"] and (x, r + 1) not in side_cells}
    return tie


def _budget_left(n):
    return lambda record, ctx: ctx.budget.remaining >= n


def _surface_is_periodic(record, ctx):
    # period is a child of the DOMAIN, not of the family: if no domain could
    # take the pattern, there is no period to resolve.
    return (record.has("surface_domain")
            and record.opt("surface_family") in ("horizontal_stripe", "vertical_stripe"))


def _surface_is_patterned(record, ctx):
    return record.has("surface_family") and record.get("surface_family") != "solid"


# Base presence odds per ornament, before Detail Package affinity and Style
# Context bias.  Kept here (authoring) rather than in the resolver (engine).
_ORNAMENT_ODDS = {"chest_emblem": 0.50, "hem_band": 0.45, "cuff_band": 0.45,
                  "flap_stud": 0.38}


def _ornament_activation(name):
    def activate(record, ctx):
        orn = ORNAMENTS[name]
        if not ctx.budget.can_afford(orn.cost):
            return False
        # Suppress optional detail once the construction is already carrying
        # enough appearance features to read as busy.
        if not ctx.under_feature_limit(ctx.architecture_feature_limit):
            return False
        pkg = record.opt("detail_package")
        mult = DETAIL_PACKAGES[pkg].affinity.get(name, 1.0) if pkg else 1.0
        if mult <= 0.0:
            return False
        odds = min(0.92, _ORNAMENT_ODDS[name] * mult)
        if not ctx.streams("ornament_presence").chance(odds):
            return False
        return ctx.claim_ornament(name)
    return activate


def declare_schema(family: FamilyContract, arch: "ArchitectureContract", ctx, record):
    """Only the Architecture may declare downstream structural variables."""
    materials = {m: w for m, w in arch.materials.items()}
    return [
        # --- Pass 5: structural parameters ---------------------------------
        Variable("silhouette", arch.name, "structural", tuple(arch.silhouettes),
                 weights=arch.silhouettes, significance=IDENTITY,
                 cost=0, cost_tag=STRUCTURAL, stream="structure"),
        Variable("collar_width", arch.name, "structural", (1, 2),
                 weights={1: 0.62, 2: 0.38}, significance=IDENTITY,
                 cost={1: 0, 2: 1}, cost_tag=STRUCTURAL, stream="structure"),
        # The V starts below the neck opening, so its depth is bounded by how
        # much room is left above the hem.
        Variable("neckline_depth", arch.name, "structural", (2, 3, 4),
                 weights={2: 0.30, 3: 0.45, 4: 0.25}, significance=IDENTITY,
                 cost=0, cost_tag=STRUCTURAL, stream="structure", repair=REPAIR_RETRY,
                 # The V point is where the tie hangs from, so it has to sit at
                 # mid-chest with room below it — as it does on every reference.
                 validate=lambda v, r, c: CLASSIC_NOTCH[r.get("silhouette")] + v <= 5),
        Variable("rear_flap_depth", arch.name, "structural", (3, 4, 5),
                 weights={3: 0.34, 4: 0.44, 5: 0.22}, significance=IDENTITY,
                 cost=0, cost_tag=STRUCTURAL, stream="structure"),
        _flap_edge_variable(arch),
        _sleeve_cap_variable(arch),
        # --- Pass 6A: material ---------------------------------------------
        Variable("material", arch.name, "material", tuple(materials), weights=materials,
                 significance=APPEARANCE, cost=0, cost_tag=STRUCTURAL, stream="material"),
        # --- Pass 6B: colour ------------------------------------------------
        Variable("color_architecture", arch.name, "color", tuple(arch.color_architectures),
                 weights=arch.color_architectures, significance=APPEARANCE,
                 cost=0, cost_tag=STRUCTURAL, stream="color"),
        Variable("harmony", arch.name, "color", tuple(HARMONIES),
                 weights={"monochrome": 0.18, "analogous": 0.32,
                          "complementary": 0.30, "split_complement": 0.20},
                 significance=APPEARANCE, cost=0, cost_tag=STRUCTURAL, stream="color"),
        # --- Pass 7: surface -------------------------------------------------
        Variable("surface_family", arch.name, "surface",
                 ("solid", "horizontal_stripe", "vertical_stripe", "panel"),
                 weights={"solid": 0.44, "horizontal_stripe": 0.28,
                          "vertical_stripe": 0.14, "panel": 0.14},
                 significance=APPEARANCE,
                 cost={"solid": 0, "horizontal_stripe": 1, "vertical_stripe": 1, "panel": 1},
                 cost_tag=SURFACE, repair=REPAIR_DROP,
                 validate=lambda v, r, c: c.material_permits_surface(v), stream="surface"),
        Variable("surface_domain", arch.name, "surface", arch.surface_domains,
                 weights={"body": 0.68, "insert": 0.32}, significance=APPEARANCE,
                 activation=_surface_is_patterned, cost=0, cost_tag=SURFACE,
                 repair=REPAIR_DROP,
                 validate=lambda v, r, c: c.surface_reads(v), stream="surface"),
        # Period 2 puts a stripe on every other row of the shell — at 8x8 that
        # is banding, not a Breton stripe, and it is what made the trim read as
        # too thick/heavy (025).  Stripe cells are always one row, so spacing is
        # the only lever the envelope has; the domain keeps 2 because on a
        # shallow domain period 3 is the only value that reads, and dropping
        # both would take the whole Surface feature with it.
        Variable("surface_period", arch.name, "surface", (2, 3),
                 weights={2: 0.25, 3: 0.75}, significance=APPEARANCE,
                 activation=_surface_is_periodic, cost=0, cost_tag=SURFACE,
                 repair=REPAIR_RETRY,
                 validate=lambda v, r, c: c.period_reads(v), stream="surface"),
        Variable("surface_phase", arch.name, "surface", (0, 1),
                 weights={0: 0.5, 1: 0.5}, significance=SUBTLE,
                 activation=_surface_is_periodic, cost=0, cost_tag=SURFACE,
                 stream="surface"),
        # --- layer slot: exists only because the Architecture opened it -----
        _tie_variable(arch, lambda r: CLASSIC_NOTCH[r.get("silhouette")]
                      + r.get("neckline_depth")),
        Variable("collar_trim", arch.name, "trim",
                 ("SINGLE_STRIPE", "DOUBLE_STRIPE", "PIPED_EDGE"),
                 weights={"SINGLE_STRIPE": 0.46, "DOUBLE_STRIPE": 0.30, "PIPED_EDGE": 0.24},
                 significance=IDENTITY, activation=_budget_left(2),
                 cost={"SINGLE_STRIPE": 1, "DOUBLE_STRIPE": 2, "PIPED_EDGE": 1},
                 cost_tag=ORNAMENT, repair=REPAIR_DROP, stream="structure",
                 # A double stripe cannot read on a 1px collar; bounded repair
                 # picks another value from this variable's own domain (INV-06).
                 validate=lambda v, r, c: v != "DOUBLE_STRIPE" or r.get("collar_width") == 2),
        # --- Pass 8: ornament / detail ---------------------------------------
        Variable("detail_package", arch.name, "ornament", tuple(DETAIL_PACKAGES),
                 weights={n: 1.0 for n in DETAIL_PACKAGES}, significance=APPEARANCE,
                 activation=_budget_left(1), cost=0, cost_tag=ORNAMENT, stream="ornament"),
        *[
            Variable(name, arch.name, "ornament", ("present",),
                     weights={"present": 1.0}, significance=APPEARANCE,
                     activation=_ornament_activation(name),
                     cost=ORNAMENTS[name].cost, cost_tag=ORNAMENT, repair=REPAIR_DROP,
                     stream="ornament")
            # focal ornament first: it has the strongest claim on remaining budget
            for name in ("chest_emblem", "hem_band", "cuff_band", "flap_stud")
        ],
    ]


# ---------------------------------------------------------------------------
# TIER 4 — ARCHITECTURE: authored construction
# ---------------------------------------------------------------------------

def _v_geometry(depth: int, width: int, env: Envelope, top: int):
    """Bounded parametric modification of the authored sailor V.

    `top` is the first fully opaque centre row — the V begins below the neck
    opening rather than at the frame edge.  Returns (insert_rows, collar_rows,
    tip_row) as {row: span}.
    """
    cl, cr = env.width // 2 - 1, env.width // 2          # 3, 4 at width 8
    insert, collar = {}, {}
    for i in range(depth):
        y = top + i
        k = 1 if i < depth - 1 else 0
        a, b = cl - k, cr + k
        insert[y] = (a, b)
        collar[y] = ((a - width, a - 1), (b + 1, b + width))
    return insert, collar, top + depth


def _collar_shading(collar_rows, tip_row, width, env, shoulder_rows, shape):
    """Authored collar interior.

    A sailor collar is a band lying on the shoulders: its outer edge turns away
    from the light and its inner edge — the fold over the dickey — catches it.
    The rows above the V come from an authored stencil; the V's own arms are
    written as a rule, because their cell set is parametric.
    """
    stencil = COLLAR_SHOULDER_STENCILS[shape]
    out = {c: v for c, v in parse_shading(stencil).items() if c[1] in shoulder_rows}
    for y, ((la, lb), (ra, rb)) in collar_rows.items():
        for x in range(la, lb + 1):
            out[(x, y)] = 1 if (x == la and width > 1) else -1
        for x in range(ra, rb + 1):
            out[(x, y)] = 1 if (x == rb and width > 1) else -1
    for x in range(env.width // 2 - width, env.width // 2 + width):
        out[(x, tip_row)] = 2
    return out


def _outline_cells(cells: set) -> set:
    """Cells of a piece that have a free boundary: its hem and its shaped sides."""
    return {c for c in cells
            if any((c[0] + dx, c[1] + dy) not in cells
                   for dx, dy in ((1, 0), (-1, 0), (0, 1)))}


# The two top corners of the frame are where the Farmer's arm and shoulder are
# drawn.  Every back and front frame in the reference pack keeps its DARKEST
# value there (`o##..##o`, `o######o`) — never its identity trim and never a
# highlight.  Identity trim placed on them read in game as a collar "lying on
# the arm" (003) and, when the articulation lit them, as a white seam
# separating the sleeve from the arm (004) and as bars crossing the elbows
# (045).  One rule, applied by both Architectures.
SHOULDER_CORNERS = frozenset({(0, 0), (7, 0)})


def _off_corners(cells: set) -> set:
    """Identity trim never occupies the frame's top shoulder corners."""
    return {c for c in cells if c not in SHOULDER_CORNERS}


def _span(lo: int, hi: int, y: int, sil: set) -> set:
    return {(x, y) for x in range(lo, hi + 1) if (x, y) in sil}


def realize(spec, env: Envelope) -> Construction:
    """Pass 10 — authored pieces + bounded parametric modification."""
    if (env.width, env.height) != (8, 8):
        raise ValueError(
            f"{CLASSIC_SQUARE_FLAP_NAME} has no authored silhouette for "
            f"{env.width}x{env.height}; author one before using this envelope")
    p = spec.parameters
    shape = p["silhouette"]
    sil = {view: parse_art(rows) for view, rows in SILHOUETTES[shape].items()}
    top = CLASSIC_NOTCH[shape]
    w, d, f = p["collar_width"], p["neckline_depth"], p["rear_flap_depth"]
    insert_rows, collar_rows, tip_row = _v_geometry(d, w, env, top)
    hem = env.height - 1
    front_edge = max(x for (x, y) in sil["side"] if y == 3)

    pieces: list[Piece] = []

    # --- body: the primary mass -------------------------------------------
    pieces.append(Piece("body", "body", z=0, wrap=PLANE, surface_domain="body",
                        cells={v: set(sil[v]) for v in sil}))

    # --- sleeves: same fabric, attached edge, own region for cuff detail ----
    cap = SLEEVE_CAPS[p["sleeve_cap"]]
    cap_cols = tuple(range(0, cap)) + tuple(range(env.width - cap, env.width))
    pieces.append(Piece("sleeve", "body", z=1, wrap=PLANE, surface_domain="body",
                        cells={
                            "front": {(x, y) for x in cap_cols
                                      for y in range(top, top + 3)} & sil["front"],
                            "back":  {(x, y) for x in cap_cols
                                      for y in range(top, top + 3)} & sil["back"],
                            "side":  {(x, y) for x in (4, 5, 6)
                                      for y in (2, 3, 4)} & sil["side"],
                        }))

    # --- front insert: real fabric-over-fabric layering ---------------------
    insert_cells = set()
    for y, (a, b) in insert_rows.items():
        insert_cells |= _span(a, b, y, sil["front"])
    insert_side = {(front_edge + dx, top + dy) for dx, dy in INSERT_SIDE_MOTIF} & sil["side"]
    insert = Piece("front_insert", "under_layer", z=2, wrap=PLANE,
                   surface_domain="insert", identity=True, zones=("chest:center",),
                   # piping belongs ON the dickey, so it may be largely covered
                   min_retention=0.34,
                   cells={"front": insert_cells, "side": insert_side})
    insert.shading["front"] = parse_shading(INSERT_STENCILS[d], origin=(0, top))
    insert.shading["side"] = {(front_edge + dx, top + dy): v
                              for (dx, dy), v in INSERT_SIDE_MOTIF.items()}
    pieces.append(insert)

    # --- collar: girth feature, wraps front -> side -> back -----------------
    collar_cells = {v: set() for v in sil}
    # Every row above the V belongs to the collar, so the band runs continuously
    # into the V instead of floating as a separate bar across the top.
    shoulder_rows = [y for y in range(0, top) if any(c[1] == y for c in sil["front"])]
    for y in shoulder_rows:
        collar_cells["front"] |= _off_corners({c for c in sil["front"] if c[1] == y})
    for y, ((la, lb), (ra, rb)) in collar_rows.items():
        collar_cells["front"] |= _span(la, lb, y, sil["front"])
        collar_cells["front"] |= _span(ra, rb, y, sil["front"])
    collar_cells["front"] |= _span(env.width // 2 - w, env.width // 2 - 1 + w,
                                   tip_row, sil["front"])
    # GIRTH: the band continues through front, side and back at the same anchor
    # rows.  On the back the rear flap paints over it.
    for y in range(0, w):
        collar_cells["side"] |= {c for c in sil["side"] if c[1] == y}
        collar_cells["back"] |= {c for c in sil["back"] if c[1] == y}
    # side motif: the V's end wraps past the shoulder seam
    collar_cells["side"] |= {(front_edge + dx, w + dy)
                             for dx, dy in COLLAR_SIDE_TAIL} & sil["side"]
    collar = Piece("collar", "trim", z=3, wrap=GIRTH, identity=True,
                   zones=("collar:center",), cells=collar_cells)
    collar.shading["front"] = _collar_shading(collar_rows, tip_row, w, env,
                                              shoulder_rows, shape)
    collar.shading["side"] = {(x, y): 1 for (x, y) in collar_cells["side"] if y < w}
    collar.shading["side"].update({(front_edge + dx, w + dy): v
                                   for (dx, dy), v in COLLAR_SIDE_TAIL.items()})
    # FREE edges: where the collar terminates over other fabric.  The shoulder
    # boundary is ATTACHED (it is the silhouette edge) and gets no termination.
    collar.free_edges["front"] = {
        c for c in collar_cells["front"]
        if any((c[0] + dx, c[1] + dy) in insert_cells
               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    }
    collar.free_edges["side"] = {c for c in collar_cells["side"] if c[1] == w - 1}
    collar.occlusion["side"] = {(x, w): 1 for x in range(env.width)
                                if (x, w) in sil["side"]
                                and (x, w - 1) in collar_cells["side"]
                                and (x, w) not in collar_cells["side"]}
    collar.occlusion["front"] = {c: 1 for c in insert_cells
                                 if (c[0] - 1, c[1]) in collar_cells["front"]
                                 or (c[0] + 1, c[1]) in collar_cells["front"]}
    pieces.append(collar)

    # --- shoulder articulation ----------------------------------------------
    # The shirt re-emerges outboard of the collar.  Without it the collar band
    # reads as a bar laid across the sprite rather than a collar worn on it.
    #
    # It is a SHOULDER corner, so its depth is the sleeve cap on the back exactly
    # as it is on the front.  Running it to the flap depth instead made a 1px
    # column of the lightest colour on the sheet fall down the outer edge of the
    # back frame, where the Farmer's arm is: in-game validation read it as
    # "back straps too far outward" (003) and "two white bars passing through
    # the elbows/hands" (045), and where it also crossed the sleeve it detached
    # the sleeve from the shoulder (004).
    shoulder_cells = {
        # OUTBOARD of the collar, never on top of it.  The collar's V arms are
        # widest at their first row, so an articulation cell placed there
        # rendered a two-wide collar one cell wide and the collar mass dropped
        # straight from full width to a single pixel — the step in-game
        # validation read as a box under the chin (083) and as a collar "too
        # wide/flat relative to the centre insert" (040).
        "front": ({(x, top + k) for x in (0, env.width - 1)
                   for k in range(cap)} & sil["front"]) - collar_cells["front"],
        # No BACK articulation.  The back's top rows are covered by the collar
        # band and the flap, so this cell was never "the shirt re-emerging at
        # the shoulder" — it was a body-coloured hole punched through the
        # middle of the trim.  On a light-bodied palette (SAILOR_WHITE_NAVY,
        # seed 004) that is a 209-against-34 pixel at the armpit: the reported
        # white seam detaching the sleeve, and the cut-in under the flap (002,
        # 011).  No reference back frame carries a light articulation.
    }
    # BODY, not under_layer.  As a contrasting light role this cell painted the
    # blouse colour at the frame's outer column: measured over seeds 0-95 it
    # sat a median +165 luminance above its inboard neighbour on 76 of 96
    # rolls — a lone near-white pixel at the armpit.  In game that read as a
    # cut-in under the flap (002, 011), a seam detaching the sleeve (004), a
    # strap sitting out on the arm (003) and bars through the elbows (045).
    # Shading it darker could not fix that: the offset moves within the role's
    # own ramp, and this role's ramp starts far lighter than the fabric around
    # it.  The reference puts a BODY-tone shadow here, so that is what it is.
    shoulder = Piece("shoulder", "body", z=4, wrap=PLANE,
                     cells={v: c for v, c in shoulder_cells.items() if c})
    # A shadow at the frame's outer edge, not a highlight: this cell sits
    # against the Farmer's arm, and lighting it drew a pale seam there (004).
    for view, cells in shoulder.cells.items():
        shoulder.shading[view] = {c: (1 if c in SHOULDER_CORNERS or c[0] in (0, 7)
                                      else -1) for c in cells}
    if any(shoulder.cells.values()):
        pieces.append(shoulder)

    # --- rear flap: the classic square, stencilled, with a free bottom edge --
    flap_back = apply_flap_edge(flap_outline(f, env.width) & sil["back"], p["flap_edge"])
    flap_side = {(x, y) for x in range(0, w + 1) for y in range(0, f)} & sil["side"]
    flap = Piece("rear_flap", "trim", z=5, wrap=PLANE, identity=True,
                 min_retention=0.55,          # the braid legitimately bands it
                 cells={"back": flap_back, "side": flap_side})
    flap.shading["back"] = parse_shading(FLAP_STENCILS[f])
    # Every cell on the flap's own outline is a free edge — the hem AND the
    # shaped sides.  Read off the cell set rather than a nominal span, so the
    # termination follows the carved outline instead of a straight rectangle.
    flap.free_edges["back"] = _outline_cells(flap_back)
    flap.free_edges["side"] = {c for c in flap_side if c[1] == f - 1}
    flap.occlusion["back"] = hem_shadow(flap_back, sil["back"])
    flap.occlusion["side"] = hem_shadow(flap_side, sil["side"])
    pieces.append(flap)

    # --- tie: the same family slot MIDDY opens, hanging from the V point ----
    tie_name = spec.layers.get("tie_style")      # a layer slot, not a parameter
    if tie_name:
        tie_cells, tie_shading, _gap = build_tie(tie_name, (env.width // 2, tip_row),
                                                 sil["front"])
        if tie_cells:
            pieces.append(_build_tie_piece(tie_cells, tie_shading, front_edge, tip_row,
                                           sil, z=6))

    # --- hem band closes the value rhythm, as it does on MIDDY --------------
    pieces.append(Piece("hem_edge", "body", z=7, wrap=GIRTH,
                        cells={v: {c for c in sil[v] if c[1] == hem} for v in sil},
                        shading={v: {c: 1 for c in sil[v] if c[1] == hem} for v in sil}))

    construction = Construction(env=env, silhouette=sil, pieces=pieces,
                                surface_domains={"body": ("body", "sleeve", "hem_edge"),
                                                 "insert": ("front_insert",)})
    construction.meta = {"insert_rows": insert_rows, "collar_rows": collar_rows,
                         "tip_row": tip_row,
                         # measured off the carved outline, not a nominal span
                         "flap_span": (min(x for x, _ in flap_back),
                                       max(x for x, _ in flap_back)),
                         "flap_depth": f, "collar_width": w, "neckline_depth": d,
                         "notch_depth": top}
    return construction


# ---------------------------------------------------------------------------
# Style Context hooks — reweight only, never introduce (INV-02)
# ---------------------------------------------------------------------------

def style_hook(var, weights, record, ctx):
    formality = ctx.formality
    out = dict(weights)
    if var.name == "material":
        for name, w in list(out.items()):
            out[name] = w * MATERIALS[name].formality_weight.get(formality, 1.0)
    elif var.name == "color_architecture":
        for name, w in list(out.items()):
            out[name] = w * COLOR_ARCHITECTURES[name].formality_weight.get(formality, 1.0)
    elif var.name == "detail_package":
        for name, w in list(out.items()):
            out[name] = w * DETAIL_PACKAGES[name].formality_weight.get(formality, 1.0)
    elif var.name in ORNAMENTS:
        base = ORNAMENTS[var.name].formality_weight.get(formality, 1.0)
        pkg = record.opt("detail_package")
        mult = DETAIL_PACKAGES[pkg].affinity.get(var.name, 1.0) if pkg else 1.0
        out = {k: v * base * mult for k, v in out.items()}
    elif var.name == "surface_family":
        # formal dress restrains pattern; work-wear likes it
        bias = {"work": 1.25, "casual": 1.10, "smart": 0.85, "formal": 0.55}[formality]
        out = {k: (v / bias if k == "solid" else v * bias) for k, v in out.items()}
    elif var.name == "collar_width" and ctx.novelty_tier == "adventurous":
        out = {k: (v * 1.5 if k == 2 else v) for k, v in out.items()}
    return out


CLASSIC_SQUARE_FLAP = register_architecture(ArchitectureContract(
    name="CLASSIC_SQUARE_FLAP",
    family="SAILOR_TOP",
    closure="PULLOVER",
    aperture="SAILOR_FLAP",
    limb="SLEEVED",
    topology=("body", "sleeve", "front_insert", "collar", "shoulder",
              "rear_flap", "tie", "hem_edge"),
    silhouettes={"tailored_regular": 0.34, "relaxed_regular": 0.30, "strap_regular": 0.36},
    layer_slots_opened=("neck_tie",),
    coverage_range=("REGULAR",),
    surface_domains=("body", "insert"),
    occupancy=(("chest:center", "front_insert", "conditional_share"),
               ("collar:center", "collar", "conditional_share")),
    base_cost=1,
    trim=("collar_trim", ("collar", "rear_flap")),
    identity_pairs=(
        # the collar against the body is what says "sailor" at a glance
        IdentitySeparation("trim", "body"),
        # The dickey must separate from the collar that frames it, or the V and
        # the insert fuse into one mass and there is no V left to see.  Held at a
        # deliberately conservative floor: it is a safety net for the extreme
        # merges, not a taste filter.
        IdentitySeparation("under_layer", "trim", floor_scale=0.50),
        # and the tie must read against the body, but only when there IS a tie
        IdentitySeparation("accent", "body", floor_scale=0.70, needs="tie"),
        # CLASSIC's tie hangs FROM the collar point, so it also has to read
        # against the collar it hangs from — the same reasoning that put MIDDY's
        # tie against the shell it lies on.  This was the cue that was missing.
        IdentitySeparation("accent", "trim", floor_scale=0.80, needs="tie"),
    ),
    # A one-pixel V is the most fragile identity feature in the family: a braid
    # was repainting up to half of it and the collar disappeared.
    identity_retention=0.80,
    # A single flat relationship is carried when the rest of the identity is
    # strong; the garment is only rejected when the whole reading collapses.
    identity_composite_floor=1.20,
    max_appearance_features=3,
    # Narrowed to the relationships that keep the collar reading against the
    # body.  Measured p10 separation across the material x harmony x temperament
    # grid, against the declared floor of 80:
    #
    #   DARK_BODY_LIGHT_COLLAR   136   admitted
    #   LIGHT_BODY_DARK_COLLAR   117   admitted
    #   SPLIT_BODY_ACCENT         88   admitted, low affinity (chromatically loud)
    #   CONTRAST_UNDER_LAYER      42 -> retuned to a light collar, then admitted
    #   MONOCHROME_CONTRAST_TRIM  44   INCOMPATIBLE: a tonal trim cannot carry a
    #                                  1-2px collar at 8x8
    #   LOW_CONTRAST_STRONG_ACCENT 3   INCOMPATIBLE: erases the V entirely
    color_architectures={
        "SAILOR_WHITE_NAVY": 0.34, "DARK_BODY_LIGHT_COLLAR": 0.26,
        "LIGHT_BODY_DARK_COLLAR": 0.14, "CONTRAST_UNDER_LAYER": 0.16,
        "SPLIT_BODY_ACCENT": 0.10,
    },
    identity_floor=80.0,
    materials={"cotton_drill": 0.34, "wool_melton": 0.20, "linen": 0.22,
               "heavy_canvas": 0.14, "silk_satin": 0.10},
    declare_schema=declare_schema,
    realize=realize,
    style_hook=style_hook,
))


# ===========================================================================
# TIER 4 — ARCHITECTURE: MIDDY_YOKE
# ===========================================================================
#
# Authored against references/style-profiles/SailorStyles (19 hand-drawn 8x8
# sailor tops).  Different construction topology from CLASSIC_SQUARE_FLAP, so it
# is an Architecture and not a parameter (section 13):
#
#     CLASSIC_SQUARE_FLAP   collar frames a V; the body is the dominant mass
#     MIDDY_YOKE            a dark yoke is the dominant mass over a light
#                           blouse, with a saturated tie at the junction
#
# The measured reference row-luminance rhythm is 39/71/121/116/72/76/145/86:
# dark yoke, light shoulder, saturated tie, bright blouse, dark waistband.  That
# rhythm comes from region topology, not from shading.

# Both neck treatments are traced from the corpus: `###..###` over `###..###`
# (8 of 19) and the notched shoulder line `##.##.##` (11 of 19).  Both break the
# solid bar across the top rows that made the earlier output read as assembled
# rectangles.
MIDDY_SILHOUETTES = {
    "middy_vee": {
        "front": ["###..###", "###..###", "########", "########",
                  "########", "########", "########", "########"],
        "side":  ["###.##..", "#######.", "#######.", "#######.",
                  "#######.", "#######.", "######..", "######.."],
        "back":  ["########", "########", "########", "########",
                  "########", "########", ".######.", ".######."],
    },
    "middy_vee_tapered": {
        "front": ["###..###", "###..###", "########", "########",
                  "########", "########", "########", ".######."],
        "side":  ["###.##..", "#######.", "#######.", "#######.",
                  "#######.", "#######.", ".#####..", ".#####.."],
        "back":  ["########", "########", "########", "########",
                  "########", "########", ".######.", ".######."],
    },
    # Same three corrections as CLASSIC's strap_regular — see the note there.
    "middy_strap": {
        "front": ["###..###", "###..###", "########", "########",
                  "########", "########", "########", "########"],
        "side":  ["###.##..", "#######.", "#######.", "#######.",
                  "#######.", "#######.", "######..", "######.."],
        "back":  ["########", "########", "########", "########",
                  "########", "########", ".######.", ".######."],
    },
}

# How deep the neck opening runs for each silhouette — the yoke's authored
# stencil is keyed on this, because the first opaque centre row is where the
# neck shadow belongs.
NOTCH_DEPTH = {"middy_vee": 2, "middy_vee_tapered": 2, "middy_strap": 2}

# Authored yoke shading, keyed by (notch depth, yoke depth).
#   D deepest  S shadow  M base  L light  H highlight  . no opinion
# Traced from the reference value structure: the top row is flat and darkest,
# rows below it ramp from a dark lateral edge inward toward the neck, and the
# first opaque cell under the neck opening carries the deepest shadow.
YOKE_STENCILS = {
    # notch 2 rows, yoke 2 rows: no opaque centre inside the yoke at all
    (2, 2): ["DDD..DDD",
             "SML..LMS"],
    # notch 2 rows, yoke 3: row 2 is the first opaque centre row, so it carries
    # the neck shadow
    (2, 3): ["DDD..DDD",
             "SML..LMS",
             "SMLDDLMS"],
    # notched shoulder line: the centre strap reads light against dark shoulders
    (3, 3): ["DD.LL.DD",
             "SML..LMS",
             "SML..LMS"],
}

# Authored rear-flap interiors, keyed by flap depth.  Traced from the reference
# backs: the flap is lit through its middle rows and its free bottom edge is the
# darkest line on the garment, with the blouse re-emerging at the shoulder
# corners outside it.  '.' columns are not the flap.
# The top row is the neck junction and is inset two columns either side (see
# FLAP_NECK_INSET), so its interior is authored at that narrower width.
FLAP_STENCILS = {
    3: ["..SMMS..",
        ".MLLLLM.",
        ".SDDDDS."],
    4: ["..SMMS..",
        ".MLLLLM.",
        ".MLLLLM.",
        ".SDDDDS."],
    5: ["..SMMS..",
        ".MLLLLM.",
        ".LHHHHL.",
        ".MLLLLM.",
        ".SDDDDS."],
}


# The tie wraps: on the side it tapers back from the front edge instead of
# sitting there as a two-cell sliver.  Offsets are (dx from the front edge, dy
# from the tie row).

# Authored bow interior: lit across the top, shaded into the knot, so the mass
# does not read as a rectangle of one colour.

# The blouse shows THROUGH the knot rather than the shirt showing behind it.
# In the references those cells are the brightest on the garment; leaving them
# to the dark body punched a hole in the middle of the bow.


def declare_middy_schema(family: FamilyContract, arch, ctx, record):
    return [
        Variable("silhouette", arch.name, "structural", tuple(arch.silhouettes),
                 weights=arch.silhouettes, significance=IDENTITY,
                 cost=0, cost_tag=STRUCTURAL, stream="structure"),
        # The yoke must at least reach the first opaque row under the neck
        # opening, or the neck shadow lands on the wrong piece.
        # Row budget is 8: yoke + 3 rows of tie + at least one row of blouse +
        # the waistband.  A four-row yoke leaves the blouse nowhere to show.
        Variable("yoke_depth", arch.name, "structural", (2, 3),
                 weights={2: 0.38, 3: 0.62}, significance=IDENTITY,
                 cost=0, cost_tag=STRUCTURAL, stream="structure", repair=REPAIR_RETRY,
                 validate=lambda v, r, c: (v, r.get("silhouette")) and
                 v >= NOTCH_DEPTH[r.get("silhouette")]
                 and (NOTCH_DEPTH[r.get("silhouette")], v) in YOKE_STENCILS),
        Variable("blouse_reveal", arch.name, "structural", (1, 2),
                 weights={1: 0.55, 2: 0.45}, significance=IDENTITY,
                 cost=0, cost_tag=STRUCTURAL, stream="structure"),
        Variable("rear_flap_depth", arch.name, "structural", (3, 4, 5),
                 weights={3: 0.28, 4: 0.46, 5: 0.26}, significance=IDENTITY,
                 cost=0, cost_tag=STRUCTURAL, stream="structure"),
        _flap_edge_variable(arch),
        _sleeve_cap_variable(arch),
        Variable("material", arch.name, "material", tuple(arch.materials),
                 weights=dict(arch.materials), significance=APPEARANCE,
                 cost=0, cost_tag=STRUCTURAL, stream="material"),
        Variable("color_architecture", arch.name, "color", tuple(arch.color_architectures),
                 weights=arch.color_architectures, significance=APPEARANCE,
                 cost=0, cost_tag=STRUCTURAL, stream="color"),
        Variable("harmony", arch.name, "color", tuple(HARMONIES),
                 weights={"monochrome": 0.10, "analogous": 0.22,
                          "complementary": 0.44, "split_complement": 0.24},
                 significance=APPEARANCE, cost=0, cost_tag=STRUCTURAL, stream="color"),
        # Reference sailor shells are solid; the stripes live on the trim.
        Variable("surface_family", arch.name, "surface", ("solid", "horizontal_stripe"),
                 weights={"solid": 0.88, "horizontal_stripe": 0.12},
                 significance=APPEARANCE, cost={"solid": 0, "horizontal_stripe": 1},
                 cost_tag=SURFACE, repair=REPAIR_DROP,
                 validate=lambda v, r, c: c.material_permits_surface(v), stream="surface"),
        Variable("surface_domain", arch.name, "surface", arch.surface_domains,
                 weights={"shell": 0.62, "blouse": 0.38}, significance=APPEARANCE,
                 activation=_surface_is_patterned, cost=0, cost_tag=SURFACE,
                 repair=REPAIR_DROP, validate=lambda v, r, c: c.surface_reads(v),
                 stream="surface"),
        # Period 2 puts a stripe on every other row of the shell — at 8x8 that
        # is banding, not a Breton stripe, and it is what made the trim read as
        # too thick/heavy (025).  Stripe cells are always one row, so spacing is
        # the only lever the envelope has; the domain keeps 2 because on a
        # shallow domain period 3 is the only value that reads, and dropping
        # both would take the whole Surface feature with it.
        Variable("surface_period", arch.name, "surface", (2, 3),
                 weights={2: 0.25, 3: 0.75}, significance=APPEARANCE,
                 activation=_surface_is_periodic, cost=0, cost_tag=SURFACE,
                 repair=REPAIR_RETRY, validate=lambda v, r, c: c.period_reads(v),
                 stream="surface"),
        Variable("surface_phase", arch.name, "surface", (0, 1),
                 weights={0: 0.5, 1: 0.5}, significance=SUBTLE,
                 activation=_surface_is_periodic, cost=0, cost_tag=SURFACE,
                 stream="surface"),
        # The tie is the iconic element, so it gets first call on the ornament
        # pool — ahead of any braid.
        _tie_variable(arch, lambda r: r.get("yoke_depth"), last_row=6),
        # A braid across a 3-row yoke reads as a hard band, so it has to earn a
        # bigger slice of the pool than trim does on the classic collar.
        Variable("yoke_trim", arch.name, "trim", ("SINGLE_STRIPE", "PIPED_EDGE"),
                 weights={"SINGLE_STRIPE": 0.55, "PIPED_EDGE": 0.45},
                 significance=APPEARANCE, activation=_budget_left(3),
                 cost={"SINGLE_STRIPE": 2, "PIPED_EDGE": 1},
                 cost_tag=ORNAMENT, repair=REPAIR_DROP, stream="structure"),
        Variable("detail_package", arch.name, "ornament", tuple(DETAIL_PACKAGES),
                 weights={n: 1.0 for n in DETAIL_PACKAGES}, significance=APPEARANCE,
                 activation=_budget_left(1), cost=0, cost_tag=ORNAMENT, stream="ornament"),
        *[
            Variable(name, arch.name, "ornament", ("present",), weights={"present": 1.0},
                     significance=APPEARANCE, activation=_ornament_activation(name),
                     cost=ORNAMENTS[name].cost, cost_tag=ORNAMENT, repair=REPAIR_DROP,
                     stream="ornament")
            # No cuff band: a light accent at the sleeve hem turns the blouse
            # row into a wall-to-wall band and the garment reads as stripes.
            for name in ("flap_stud",)
        ],
    ]


def realize_middy(spec, env: Envelope) -> Construction:
    if (env.width, env.height) != (8, 8):
        raise ValueError(f"MIDDY_YOKE has no authored silhouette for "
                         f"{env.width}x{env.height}")
    p = spec.parameters
    shape = p["silhouette"]
    sil = {v: parse_art(rows) for v, rows in MIDDY_SILHOUETTES[shape].items()}
    notch = NOTCH_DEPTH[shape]
    y = p["yoke_depth"]
    reveal = p["blouse_reveal"]
    flap = p["rear_flap_depth"]
    cx = env.width // 2
    hem = env.height - 1
    front_edge = max(x for (x, _) in sil["side"] if _ == 2)

    tie_row = y
    tie_cells, tie_shading, knot_gap = (set(), {}, set())
    tie_name = spec.layers.get("tie_style")      # a layer slot, not a parameter
    if tie_name:
        tie_cells, tie_shading, knot_gap = build_tie(
            tie_name, (cx, tie_row), sil["front"])
    tie_bottom = max((c[1] for c in tie_cells), default=tie_row - 1)
    blouse_top = max(tie_bottom + 1, hem - reveal)

    pieces: list[Piece] = []

    # --- body: the shirt itself; the dominant dark mass ---------------------
    pieces.append(Piece("body", "body", z=0, wrap=PLANE, surface_domain="shell",
                        cells={v: set(sil[v]) for v in sil}))

    # --- sleeves ------------------------------------------------------------
    cap = SLEEVE_CAPS[p["sleeve_cap"]]
    cap_cols = tuple(range(0, cap)) + tuple(range(env.width - cap, env.width))
    pieces.append(Piece("sleeve", "body", z=1, wrap=PLANE, surface_domain="shell",
                        cells={
                            "front": {(x, r) for x in cap_cols
                                      for r in range(1, blouse_top)} & sil["front"],
                            "back":  {(x, r) for x in cap_cols
                                      for r in range(1, blouse_top)} & sil["back"],
                            "side":  {(x, r) for x in (4, 5, 6)
                                      for r in range(2, 5)} & sil["side"],
                        }))

    # --- blouse: the light under layer showing below the yoke ---------------
    blouse_cells = {v: set() for v in sil}
    blouse_cells["front"] = {(x, r) for x in range(1, env.width - 1)
                             for r in range(blouse_top, hem)} & sil["front"]
    blouse_cells["front"] |= knot_gap
    blouse_cells["back"] = {(x, r) for x in range(1, env.width - 1)
                            for r in range(flap, hem)} & sil["back"]
    blouse_cells["side"] = {(x, r) for x in range(1, env.width - 2)
                            for r in range(blouse_top, hem)} & sil["side"]
    pieces.append(Piece("blouse", "under_layer", z=2, wrap=GIRTH, identity=True,
                        surface_domain="blouse", zones=("midriff:center",),
                        girth_anchor="hem", cells=blouse_cells,
                        shading={"front": {c: -1 for c in knot_gap}}))

    # --- yoke: the sailor collar mass, girth, authored interior -------------
    yoke_cells = {v: (_off_corners({c for c in sil[v] if c[1] < y}) if v == "front"
                      else {c for c in sil[v] if c[1] < y}) for v in sil}
    yoke = Piece("yoke", "trim", z=3, wrap=GIRTH, identity=True,
                 zones=("collar:center", "chest:left", "chest:right"), cells=yoke_cells)
    stencil = YOKE_STENCILS.get((notch, y)) or YOKE_STENCILS[(2, 2)]
    yoke.shading["front"] = parse_shading(stencil)
    yoke.free_edges["front"] = {c for c in yoke_cells["front"] if c[1] == y - 1}
    yoke.free_edges["side"] = {c for c in yoke_cells["side"] if c[1] == y - 1}
    # Shadow only where the yoke actually overhangs: with a notched neck there
    # are columns where nothing sits above the row below it.
    yoke.occlusion["front"] = {(x, y): 1 for x in range(env.width)
                               if (x, y) in sil["front"] and (x, y - 1) in yoke_cells["front"]}
    yoke.occlusion["side"] = {(x, y): 1 for x in range(env.width)
                              if (x, y) in sil["side"] and (x, y - 1) in yoke_cells["side"]}
    pieces.append(yoke)

    # --- shoulder articulation ----------------------------------------------
    # In every reference the blouse re-emerges at the shoulder corner, one cell
    # of light against the yoke.  Without it the yoke reads as a slab that has
    # been laid on top of the sprite rather than worn under it.
    shoulder_cells = {
        "front": {(x, y - 1 + k) for x in (0, env.width - 1)
                  for k in range(cap)} & sil["front"],
        "side": {(0, y - 1)} & sil["side"],
        # no back articulation — see the note in CLASSIC's realize()
    }
    # BODY, not under_layer.  As a contrasting light role this cell painted the
    # blouse colour at the frame's outer column: measured over seeds 0-95 it
    # sat a median +165 luminance above its inboard neighbour on 76 of 96
    # rolls — a lone near-white pixel at the armpit.  In game that read as a
    # cut-in under the flap (002, 011), a seam detaching the sleeve (004), a
    # strap sitting out on the arm (003) and bars through the elbows (045).
    # Shading it darker could not fix that: the offset moves within the role's
    # own ramp, and this role's ramp starts far lighter than the fabric around
    # it.  The reference puts a BODY-tone shadow here, so that is what it is.
    shoulder = Piece("shoulder", "body", z=4, wrap=PLANE,
                     cells={v: c for v, c in shoulder_cells.items() if c})
    # A shadow at the frame's outer edge, not a highlight: this cell sits
    # against the Farmer's arm, and lighting it drew a pale seam there (004).
    for view, cells in shoulder.cells.items():
        shoulder.shading[view] = {c: (1 if c in SHOULDER_CORNERS or c[0] in (0, 7)
                                      else -1) for c in cells}
    if any(shoulder.cells.values()):
        pieces.append(shoulder)

    # --- rear flap: the square, hanging off the yoke on the back ------------
    # Inset by one column so the blouse re-emerges at the shoulder corners, as
    # it does on every reference back, and stencilled so the slab has an inside.
    flap_back = apply_flap_edge(flap_outline(flap, env.width) & sil["back"],
                                p["flap_edge"])
    flap_side = {(x, r) for x in range(0, 2) for r in range(0, flap)} & sil["side"]
    rear = Piece("rear_flap", "trim", z=5, wrap=PLANE, identity=True,
                 min_retention=0.55,          # the braid legitimately bands it
                 cells={"back": flap_back, "side": flap_side})
    rear.shading["back"] = parse_shading(FLAP_STENCILS[flap])
    rear.free_edges["back"] = _outline_cells(flap_back)
    rear.free_edges["side"] = {c for c in flap_side if c[1] == flap - 1}
    rear.occlusion["back"] = hem_shadow(flap_back, sil["back"])
    rear.occlusion["side"] = hem_shadow(flap_side, sil["side"])
    pieces.append(rear)

    # --- tie: opened through the family layer slot, authored in the motif
    #     library, and it wraps onto the side rather than stopping at the seam.
    if tie_cells:
        pieces.append(_build_tie_piece(tie_cells, tie_shading, front_edge, tie_row,
                                       sil, z=6))

    # --- waistband: girth, closes the value rhythm at the hem ---------------
    # Inset from the frame's outer columns, for the same reason as hem_band:
    # taken edge to edge in the trim role this was a hard uniform bar across
    # the full width of the sprite, and on a light-trim palette it is the
    # reported "white/yellow rectangle wrapped around the torso".  It owned 29
    # of the 43 such bands measured over seeds 0-95.
    pieces.append(Piece("waistband", "trim", z=7, wrap=GIRTH,
                        cells={v: {c for c in sil[v]
                                   if c[1] == hem and 0 < c[0] < env.width - 1}
                               for v in sil}))

    construction = Construction(env=env, silhouette=sil, pieces=pieces,
                                surface_domains={"shell": ("body", "sleeve"),
                                                 "blouse": ("blouse",)})
    construction.meta = {"yoke_depth": y, "tie_row": tie_row, "tie_bottom": tie_bottom,
                         "blouse_top": blouse_top, "flap_depth": flap,
                         "notch_depth": notch, "tip_row": tie_row, "collar_width": 1}
    return construction


def middy_style_hook(var, weights, record, ctx):
    out = style_hook(var, weights, record, ctx)
    if var.name == "tie_style" and ctx.formality == "formal":
        out = {k: (v * 1.4 if k == "FLAT_TIE" else v) for k, v in out.items()}
    return out


MIDDY_YOKE = register_architecture(ArchitectureContract(
    name="MIDDY_YOKE",
    family="SAILOR_TOP",
    closure="PULLOVER",
    aperture="SAILOR_FLAP",
    limb="SLEEVED",
    topology=("body", "sleeve", "blouse", "yoke", "rear_flap", "tie", "waistband"),
    silhouettes={"middy_vee": 0.34, "middy_vee_tapered": 0.28, "middy_strap": 0.38},
    layer_slots_opened=("neck_tie",),
    coverage_range=("REGULAR",),
    surface_domains=("shell", "blouse"),
    occupancy=(("collar:center", "yoke", "conditional_share"),
               ("chest:center", "tie", "exclusive"),
               ("hem:girth", "waistband", "exclusive")),
    base_cost=1,
    # The reference set carries no braid across the front yoke — the light row
    # it produced was the single loudest wrong note.  The braid lives on the
    # back square, which is where those garments actually band it.
    trim=("yoke_trim", ("rear_flap",)),
    identity_pairs=(
        # the blouse against the yoke is MIDDY's primary read
        IdentitySeparation("under_layer", "trim"),
        # MIDDY's tie hangs BELOW the yoke, onto the shell — so the separation
        # that matters is against the fabric it actually lies on.
        IdentitySeparation("accent", "body", floor_scale=0.70, needs="tie"),
        IdentitySeparation("accent", "under_layer", floor_scale=0.40,
                           required=False, needs="tie"),
    ),
    identity_retention=0.80,
    # A single flat relationship is carried when the rest of the identity is
    # strong; the garment is only rejected when the whole reading collapses.
    identity_composite_floor=1.20,
    max_appearance_features=3,
    # MIDDY's under_layer IS the blouse, so only palettes that keep the under
    # layer light are legal here.  LIGHT_BODY_DARK_COLLAR inverts that and the
    # garment stops reading — the gate caught it, the vocabulary now prevents it.
    # Both are dark-anchor: MIDDY's yoke uses the trim role, so any palette that
    # makes trim light inverts the garment and it stops reading as a middy.
    color_architectures={"DARK_YOKE_LIGHT_BLOUSE": 0.46, "SAILOR_WHITE_NAVY": 0.32,
                         "DARK_YOKE_TONAL": 0.22},
    identity_floor=80.0,
    materials={"cotton_drill": 0.42, "wool_melton": 0.24, "linen": 0.20, "heavy_canvas": 0.14},
    declare_schema=declare_middy_schema,
    realize=realize_middy,
    style_hook=middy_style_hook,
))
