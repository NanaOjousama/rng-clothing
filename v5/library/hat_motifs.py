"""HAT PROTRUSIONS — authored, closed-set, profile-scoped.

Measured across 188 shipping hats (72 from a community sheet, 116 vanilla):

  * 140 of 188 (74%) have at least one SPLIT ROW — ears, gaps, feathers.
    Our generator sits at exactly 1.00 runs per row against a corpus median of
    1.24, and that single number is most of why our hats read as primitives.
  * 33 of 188 (18%) are a real crown PLUS a protrusion above or beside it,
    which is the group these motifs reproduce.  The rest of the split-row hats
    are horn/antler shapes with no crown at all — a different topology, not
    something to bolt onto a brimmed hat.
  * split rows per hat: median 2, max runs on a row: median 2.

Protrusions are ATTACHED: every motif merges into the crown on the row below,
so the gap between a pair is open upward and is therefore not an enclosed hole.
`grammar.enclosed_holes` requires opaque on all four sides, so every existing
hat invariant survives untouched — nothing here relaxes a rule.

Authored from these corpus examples:

  EARS_TOP    a pair rising above the apex, gap between them
              ......##..##........
              ......########......

  EARS_SIDE   a pair flanking a narrow crown row, one-cell gap
              ...##.########.##...
              ...##############...

  EARS_TALL   a three-row tapering pair, widening downward
              ....##.######.##....
              ...###.######.###...
              ..###.########.###..
              ..################..
"""

from __future__ import annotations

# Per-row (outward width, gap) beside the crown, top row first.  A gap of 0
# would merge the ear into the crown and produce no split at all.
# Widths per row, TOP first.  Side motifs are anchored to the crown's widest
# row and stack upward from it, each row's outer edge stepping one column in —
# which is exactly what the corpus draws (see the ASCII above): the ears form a
# connected diagonal band resting on solid fabric.
PROTRUSIONS = {
    "EARS_TOP":   {"where": "apex", "rows": (2,)},
    "EARS_SIDE":  {"where": "side", "rows": (2,)},
    "EARS_TALL":  {"where": "side", "rows": (2, 3, 3)},
    # A pinch taken OUT of the apex rather than added to it.  Vanilla's Cowboy
    # Hat opens its top row as `.......##..##.......` — the felt creased down
    # the middle.  It is the same split-row idea as an ear pair, inverted, and
    # it generalises to every creased or pinched crown.
    "CROWN_CREASE": {"where": "crease", "rows": (2,)},
    # Wings resting on the BRIM rather than the crown.  A distinct anchor: the
    # Cowboy Hat's side flashes sit on the brim's widest row, outboard of a
    # crown that is nowhere near them.  Reusable for any wide-brimmed hat that
    # carries something on the brim — pinned sides, feathers, badges.
    "BRIM_WINGS": {"where": "brim", "rows": (2,)},
}
MIN_GAP = 1             # cells of daylight between an ear and the crown

# Crown profiles each motif may sit on.  A profile absent from every entry
# stays plain.  Apex motifs need a top row broad enough to hold a gap between
# the ears; side motifs need a crown that is still narrow where they attach.
PROTRUSION_SCOPE = {
    "CROWN_CREASE": ("ROUND", "DOMED", "TALL_FLAT", "STEPPED", "STOVEPIPE",
                     "COLUMN"),
    # COLUMN is the profile this motif was waiting for: it is the only crown
    # that is still narrow where the brim is widest, which is the geometry a
    # wing needs.  The rest stay listed because they become legal the moment
    # they are paired with a brim wide enough, and the clearance check below
    # decides — the scope is what MAY carry it, not what does.
    "BRIM_WINGS": ("ROUND", "DOMED", "TALL_FLAT", "STEPPED", "STOVEPIPE",
                   "SHALLOW", "PINCHED", "CONE", "DROOP", "COLUMN"),
    "EARS_TOP":  ("ROUND", "DOMED", "SHALLOW", "STEPPED", "TALL_FLAT"),
    "EARS_SIDE": ("ROUND", "DOMED", "TALL_FLAT", "STEPPED", "STOVEPIPE"),
    "EARS_TALL": ("ROUND", "DOMED", "STOVEPIPE", "PINCHED"),
}

MIN_APEX_WIDTH = 6      # an apex pair needs room for a >=2 cell gap between
MIN_CREASE_WIDTH = 6    # a crease removes 2 cells and must leave fabric either side
MAX_RUNS_PER_ROW = 3    # corpus median is 2, max 5; we stay conservative
# Worst-case cells a motif adds, for the mass ceiling check.
PROTRUSION_MAX_CELLS = max(
    sum(2 * w for w in m["rows"]) for m in PROTRUSIONS.values())


def crown_row_profile(crown_profile: str, architecture: str) -> tuple:
    """The per-row insets THIS Architecture will actually draw.

    The two Architectures name their crowns from the same vocabulary but draw
    different shapes: BRIMLESS authors its own three-row domes (CAP_DOMES)
    because truncating a brimmed profile collapsed the vocabulary.  Reading the
    brimmed table for a cap was a latent bug — it happened to agree for the
    names both tables share, and raised KeyError the moment one did not.
    """
    if architecture == "BRIMLESS_HAT":
        from .brimless_hat import CAP_DOMES
        return CAP_DOMES[crown_profile]
    from .brimmed_hat import CROWN_PROFILES
    return CROWN_PROFILES[crown_profile]


def protrusion_options(crown_profile: str, architecture: str = "BRIMMED_HAT",
                       crown_width: int = 14, brim_width: int | None = None) -> tuple:
    """Motifs this crown may carry.  Always includes NONE.

    A side motif needs the crown to TAPER enough that its ears clear it: the
    topmost ear sits `n-1` columns outside the base plus its own width plus a
    gap, so the profile must reach an inset of at least `n + 2`.  Without this
    check a motif could be rolled and then silently render nothing — the
    variable claimed an ear the geometry never produced, which is worse than
    not offering it.  EARS_TALL needs an inset of 5 and our deepest profile is
    4, so it is currently unreachable for every crown; it stays in the library
    and becomes available again the moment a deeper profile is authored.
    """
    profile = crown_row_profile(crown_profile, architecture)
    out = ["NONE"]
    for name, profiles in PROTRUSION_SCOPE.items():
        if crown_profile not in profiles:
            continue
        spec = PROTRUSIONS[name]
        if spec["where"] == "brim":
            # A wing sits on the brim's widest row, outboard of the crown AT
            # THAT ROW — which is the crown's LAST row, not its narrow apex.
            # Every current profile reaches full width before the brim, so the
            # clearance is brim_width - crown_width, and no legal combination
            # gets to 8.  BRIM_WINGS is therefore unreachable today: vanilla's
            # Cowboy keeps its crown 8 wide where ours has already opened to
            # 12.  Same situation as EARS_TALL — the motif is right, the crown
            # vocabulary cannot yet carry it.  It becomes available the moment
            # a profile is authored that stays narrow to the brim line.
            last = profile[-1]
            if brim_width is None or brim_width - (crown_width - 2 * last) < 8:
                continue
        if spec["where"] == "crease":
            # A crease needs an apex wide enough to lose two cells and still
            # leave fabric either side of the gap.
            if crown_width - 2 * profile[0] < MIN_CREASE_WIDTH:
                continue
        if spec["where"] == "apex":
            # The apex pair needs a top row wide enough to hold both ears and
            # at least two cells of daylight between them.  Rolling the motif
            # on a narrow apex meant declaring an ear the geometry could not
            # draw, which is worse than not offering it.
            if crown_width - 2 * profile[0] < MIN_APEX_WIDTH:
                continue
        if spec["where"] == "side":
            need = len(spec["rows"]) + 2
            # The inset that matters is the one on the row JUST ABOVE the
            # crown's widest row, not the profile's deepest.  A BRIMMED crown
            # tapers gradually and reaches its full width through an inset of
            # 1, so an ear there has nowhere to sit — it either merges into the
            # crown or hangs off it.  A BRIMLESS cap truncates its dome and
            # jumps straight to full width, which is the sharp shoulder the
            # corpus rests its ears on.
            if architecture == "BRIMLESS_HAT":
                from .brimless_hat import dome_of
                dome = dome_of(crown_profile)
                shoulder = dome[-1] if dome else 0
            else:
                zero = next((i for i, v in enumerate(profile) if v == 0), None)
                shoulder = profile[zero - 1] if zero else 0
            if shoulder < need:
                continue
        out.append(name)
    return tuple(out)


def apply_protrusion(motif: str, crown: dict, crown_rows: dict, env,
                     brim: dict | None = None, brim_rows: dict | None = None) -> None:
    """Add the motif to the crown, in place.

    Which views get the motif follows the corpus, not a blanket rule:

      * APEX pairs appear in PROFILE too.  Ears rising off the top of the head
        are both visible from the side, one nearer than the other — the
        EARS_TOP source draws `......##.##..##.....` in its right frame.
      * SIDE pairs do NOT.  An ear mounted on the side of the head is seen
        edge-on, and the EARS_TALL source has no split row in either profile
        frame.  Drawing one there would invent a silhouette the corpus avoids.
    """
    if motif == "NONE" or motif not in PROTRUSIONS or not crown_rows:
        return
    spec = PROTRUSIONS[motif]
    ys = sorted(crown_rows)
    top = ys[0]
    before = {v: set(c) for v, c in crown.items()}

    # The BACK frame is derived from the front after every motif has run
    # (grammar.back_view), so nothing here writes to it.
    views = (("front", "side") if spec["where"] in ("apex", "crease")
             else ("front",))
    if spec["where"] == "brim":
        if not brim or not brim_rows:
            return
        widest = max(len(c) for c in brim_rows.values())
        anchor = min(r for r, c in brim_rows.items() if len(c) == widest)
        base = brim_rows[anchor]
        width = spec["rows"][0]
        row = anchor - 1
        if row < 0 or row not in crown_rows:
            return
        cols = crown_rows[row]
        lo, hi = base.start + 1, base.stop - 2
        # daylight between wing and crown, or it is not a protrusion
        if lo + width - 1 >= cols.start - MIN_GAP:
            return
        if hi - width + 1 <= cols.stop - 1 + MIN_GAP:
            return
        for view in ("front",):
            crown[view] |= {(x, row) for x in range(lo, lo + width)}
            crown[view] |= {(x, row) for x in range(hi - width + 1, hi + 1)}
        return
    for view in views:
        if spec["where"] == "crease":
            cols = crown_rows[top]
            if len(cols) < MIN_CREASE_WIDTH:
                return
            mid = (cols.start + cols.stop) // 2
            crown[view] -= {(mid - 1, top), (mid, top)}
            continue
        if spec["where"] == "apex":
            cols = crown_rows[top]
            if len(cols) < MIN_APEX_WIDTH:
                return
            row = top - 1
            if row < 0:
                return
            width = spec["rows"][0]
            left = range(cols.start, cols.start + width)
            right = range(cols.stop - width, cols.stop)
            # a gap must survive between the pair, or it is not a split row
            if right.start - left.stop < 2:
                return
            crown[view] |= {(x, row) for x in left}
            crown[view] |= {(x, row) for x in right}
        else:
            # ANCHOR TO THE WIDEST ROW, stacking upward.  Placing ears from the
            # crown's TOP downward put them beside its narrowest rows, so the
            # row underneath was still narrow and the ear hung in the air with
            # a gap below it — a floating cluster, not an appendage.  The
            # corpus rests every ear directly on the full-width row.
            widest = max(len(c) for c in crown_rows.values())
            anchor = min(r for r, c in crown_rows.items() if len(c) == widest)
            base = crown_rows[anchor]
            n = len(spec["rows"])
            if anchor - n < 0:
                return
            for i, width in enumerate(spec["rows"]):
                row = anchor - n + i
                cols = crown_rows.get(row)
                if cols is None:
                    return
                # outer edge steps outward as the pair descends to the anchor
                step = n - 1 - i
                lo = base.start + step
                hi = base.stop - 1 - step
                if lo < 0 or hi >= env.width:
                    return
                # daylight between ear and crown, or it is not a protrusion
                if lo + width - 1 >= cols.start - MIN_GAP:
                    return
                if hi - width + 1 <= cols.stop - 1 + MIN_GAP:
                    return
                crown[view] |= {(x, row) for x in range(lo, lo + width)}
                crown[view] |= {(x, row) for x in range(hi - width + 1, hi + 1)}

    # The gap between a pair must stay open UPWARD.  Where the crown is wider
    # above the ears than between them, it closes over and becomes an enclosed
    # hole — which every hat is required not to have.  Revert rather than ship
    # one: the motif is a garnish, the invariant is not.
    from ..grammar import enclosed_holes
    if any(enclosed_holes(crown[v], env) for v in views):
        for v, cells in before.items():
            crown[v] = cells


def runs_per_row(cells: set) -> dict:
    """Horizontal runs on each occupied row — the corpus's richness measure."""
    rows: dict[int, list[int]] = {}
    for (x, y) in cells:
        rows.setdefault(y, []).append(x)
    out = {}
    for y, xs in rows.items():
        xs = sorted(xs)
        out[y] = 1 + sum(1 for a, b in zip(xs, xs[1:]) if b - a > 1)
    return out


# ---------------------------------------------------------------------------
# DIRECTIONAL PIECES  (authored, closed-set, declaration-gated)
# ---------------------------------------------------------------------------
#
# Everything above is view-uniform: a protrusion is drawn the same way in every
# frame that carries it.  Real headwear is not always like that.  Vanilla's
# Trucker Hat #16 draws its visor in the two SIDE frames and nowhere else — a
# cap facing the camera has its visor pointing at you, so it is occluded by the
# crown; a cap seen from behind has it hidden by the head.  Vanilla's Santa Hat
# #25 does the mirror of that with its tail: three rows hanging down and BACK,
# visible only in profile.
#
# Both are the same concept.  A directional piece is:
#
#   * decided ONCE, at Construction time, from the same roll as everything
#     else — Projection still adds zero design entropy and the directions do
#     not reroll the garment;
#   * declared per FRAME, present or absent, never a different hat;
#   * ANCHORED to the crown that is already anchored, so the base identity —
#     crown columns, crown rows, placement on the head — is bit-identical in
#     every frame with or without it.  Removing the piece leaves the same hat.
#
# That last clause is the guard against the bug this Architecture was built to
# avoid: the hat visibly shifting as the Farmer turns.  A directional piece may
# ADD mass to one frame; it may never move the mass that is already there.
# `test_directional_piece_never_moves_the_hat` re-realizes the same spec with
# the piece switched off and requires every other cell to be identical.
#
# Gated on `ArchitectureContract.allows_directional_pieces`, so this is an
# opt-in capability of a named Architecture and not a global relaxation.

DIRECTIONAL_PIECES = {
    # A cap visor: five rows reaching FORWARD off the lower crown.  Measured
    # from vanilla #16, whose visor runs 4, 5, 5, 5, 4 cells clear of the crown
    # edge across rows 6-10.  Reusable for every peaked cap — baseball,
    # trucker, jockey, kepi, newsboy.
    "VISOR": {"views": ("side",), "extent": (4, 5, 5, 5, 4),
              "toward": +1, "anchor": "crown", "lift": 2},
    # A soft crown's point flopping DOWN and BACK.  Vanilla #25 hangs 6, 5, 2
    # below its lowest row, hugging the back edge.  Reusable for nightcap,
    # phrygian, elf and sleeping caps — the whole soft-pointed family.
    "TAIL":  {"views": ("side",), "extent": (6, 5, 2),
              "toward": -1, "anchor": "hem", "lift": 0},
}

# Which Architecture may carry which piece, and on which crowns.  A visor needs
# a cap; a tail needs a crown with a point to flop.
DIRECTIONAL_SCOPE = {
    "VISOR": {"BRIMLESS_HAT": ("ROUND", "DOMED", "SHALLOW", "FAST",
                               "TALL_FLAT", "STEPPED")},
    "TAIL":  {"BRIMMED_HAT": ("CONE", "DROOP", "STOVEPIPE"),
              "BRIMLESS_HAT": ("ROUND", "DOMED", "STOVEPIPE")},
}
# The face is at high x in our side frame, as in every other V5 side view.
DIRECTIONAL_MAX_CELLS = max(sum(m["extent"]) for m in DIRECTIONAL_PIECES.values())
DIRECTIONAL_OPTIONS = ("NONE",) + tuple(DIRECTIONAL_PIECES)


def directional_options(architecture: str, crown_profile: str,
                        contract=None) -> tuple:
    """Directional pieces this Architecture and crown may carry.

    Returns ("NONE",) unless the Architecture DECLARES the capability.  The
    declaration is the gate; the scope table only narrows it.
    """
    if contract is None:
        from ..contracts import ARCHITECTURE_LIBRARY
        contract = ARCHITECTURE_LIBRARY.get(architecture)
    if not getattr(contract, "allows_directional_pieces", False):
        return ("NONE",)
    out = ["NONE"]
    for name, scope in DIRECTIONAL_SCOPE.items():
        if crown_profile in scope.get(architecture, ()):
            out.append(name)
    return tuple(out)


def directional_cells(motif: str, silhouette: dict, env) -> dict:
    """Cells for the directional piece, per view.  Never touches the crown.

    Anchored to the silhouette that already exists, so the piece grows out of
    the hat rather than being placed beside it.
    """
    empty = {"front": set(), "side": set(), "back": set()}
    if motif == "NONE" or motif not in DIRECTIONAL_PIECES:
        return empty
    spec = DIRECTIONAL_PIECES[motif]
    out = dict(empty)
    for view in spec["views"]:
        base = silhouette.get(view) or set()
        if not base:
            continue
        rows: dict[int, list[int]] = {}
        for (x, y) in base:
            rows.setdefault(y, []).append(x)
        extent = spec["extent"]
        cells = set()
        if spec["anchor"] == "crown":
            bottom = max(rows) - spec["lift"]
            first = bottom - len(extent) + 1
            if first < 0 or any(r not in rows for r in range(first, bottom + 1)):
                return empty          # crown too short: the motif does not render
            for i, n in enumerate(extent):
                r = first + i
                x = max(rows[r]) if spec["toward"] > 0 else min(rows[r])
                for k in range(1, n + 1):
                    cx = x + spec["toward"] * k
                    if 0 <= cx < env.width:
                        cells.add((cx, r))
        else:                          # "hem": hangs BELOW the lowest row
            # The tail hugs the edge it hangs off and spans inward from it, so
            # it stays attached to the hat instead of drifting off the side.
            bottom = max(rows)
            edge = (max(rows[bottom]) if spec["toward"] > 0 else min(rows[bottom]))
            inward = -spec["toward"]
            for i, n in enumerate(extent):
                r = bottom + 1 + i
                if r >= env.height:
                    return empty       # no room to hang: does not render
                for k in range(n):
                    cx = edge + inward * k
                    if 0 <= cx < env.width:
                        cells.add((cx, r))
        if not cells:
            return empty
        out[view] = cells
    return out
