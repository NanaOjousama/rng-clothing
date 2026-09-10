"""NEW AA — ART ARCHITECTURE (Pass 11).

AA receives a coherent semantic Garment Specification plus its realized
Construction and decides large visual organisation: mass hierarchy, focal
structure, contrast distribution, where Surface actually lands, where Ornament
lands, and the accent economy.

AA may not invent undeclared garment features.  Everything it places traces
back to a piece the Construction realized or an ornament the spec instantiated.
It also may not invent colour: contrast repair moves a role to a different step
*inside that role's own authored ramp*.
"""

from __future__ import annotations

import math

from dataclasses import dataclass, field

from .grammar import GIRTH, VIEWS, terminate_inboard
from .ornament import DETAIL_PACKAGES, ORNAMENTS
from .surface import SURFACES, domain_cells, figure_cells

# Accent economy: the corpus shows 1-2px high-contrast accents in ~86% of
# garments.  Bands (hem, cuff) are construction-scale trim, not point accents,
# so they are budgeted separately from point accents.
POINT_ACCENT_CAP = 4
POINT_ACCENT_FEATURES = 2


@dataclass(frozen=True)
class PaintCell:
    role: str
    step: str
    feature: str


@dataclass
class ArtPlan:
    paint: dict = field(default_factory=dict)        # view -> {cell: PaintCell}
    hierarchy: list = field(default_factory=list)    # (feature, area) primary first
    focal: dict = field(default_factory=dict)        # view -> cell
    point_accents: dict = field(default_factory=dict)
    role_steps: dict = field(default_factory=dict)   # role -> chosen base step
    structural: dict = field(default_factory=dict)  # view -> {cell: piece name}
    notes: list = field(default_factory=list)

    def at(self, view: str, cell) -> PaintCell | None:
        return self.paint.get(view, {}).get(cell)


def _best_contrasting_step(palette, role, against_rgba, floor):
    """Pick the step inside `role`'s own ramp that best separates from a colour."""
    best, best_c = None, -1.0
    for step in palette.steps:
        c = palette.separation(palette.color(role, step), against_rgba)
        if c > best_c:
            best, best_c = step, c
        if c >= floor and step == "base":
            return step, c
    return best, best_c


def plan(spec, construction, architecture) -> ArtPlan:
    palette = spec.palette
    p = spec.parameters
    meta = construction.meta
    art = ArtPlan()

    # ---------------------------------------------------------------------
    # 1. contrast distribution + identity enforcement
    # ---------------------------------------------------------------------
    role_steps = {r: "base" for r in palette.ramps}
    role_steps["hardware"] = "light" if "light" in palette.steps else palette.steps[-1]
    body_rgba = palette.color("body", role_steps["body"])

    # Identity is carried by declared role pairs (section 56).  AA never invents
    # a colour to fix one: it moves a role to a different step INSIDE that
    # role's own authored ramp.
    del body_rgba
    for rule in architecture.separation_rules:
        role, against = rule.role, rule.against
        if role not in palette.ramps or against not in palette.ramps:
            continue
        if role == against or palette.ramps[role] is palette.ramps[against]:
            continue        # aliased to the same ramp: separation is by form
        floor = architecture.identity_floor * rule.floor_scale
        target = palette.color(against, role_steps[against])
        got = palette.separation(palette.color(role, role_steps[role]), target)
        if got >= floor:
            continue
        step, reached = _best_contrasting_step(palette, role, target, floor)
        role_steps[role] = step
        art.notes.append(
            f"identity repair: {role} -> {step} vs {against} ({got:.0f}->{reached:.0f})"
            + ("" if reached >= floor else "  [floor not reached]"))
    art.role_steps = role_steps

    # ---------------------------------------------------------------------
    # 2. structural masses
    # ---------------------------------------------------------------------
    structural = {}
    for view in VIEWS:
        region = construction.region_map(view)
        structural[view] = {
            cell: PaintCell(construction.by_name(name).role,
                            role_steps[construction.by_name(name).role], name)
            for cell, name in region.items()
        }
        art.paint[view] = dict(structural[view])
        art.structural[view] = {c: pc.feature for c, pc in structural[view].items()}
    art.hierarchy = sorted(
        ((piece.name, piece.area()) for piece in construction.pieces),
        key=lambda kv: -kv[1])

    # ---------------------------------------------------------------------
    # 3. surface placement (only where it reads; PLANE surfaces stay on front)
    # ---------------------------------------------------------------------
    # A periodic family with no resolved period is ABSENT, not defaulted
    # (INV-04).  `period = spec.surface.get("period", 2)` minted a period no
    # variable had rolled: the surface painted anyway, and check_continuity
    # then crashed reading the key that was never set.  An unresolvable pattern
    # drops, the same outcome readable() gives a pattern that cannot read.
    surface_renderable = False
    if spec.surface:
        surface = SURFACES[spec.surface["family"]]
        domain = spec.surface["domain"]
        period = spec.surface.get("period")
        phase = spec.surface.get("phase")
        surface_renderable = not surface.periodic or None not in (period, phase)
    if surface_renderable:
        views = VIEWS if surface.wrap == GIRTH else ("front",)
        ground, figure = surface.role_map
        for view in views:
            cells = domain_cells(construction, domain, view)
            fig = figure_cells(surface, cells, period, phase, registration=0)
            for cell in fig:
                prior = art.paint[view][cell]
                art.paint[view][cell] = PaintCell(figure, role_steps.get(figure, "base"),
                                                  f"surface:{surface.name}")
                del prior
        # Focal hierarchy: a repeating surface must not run straight into the
        # construction that carries family identity, or the V and the flap stop
        # reading.  AA reverts the figure in a one-cell quiet zone around every
        # identity piece.  This is contrast distribution, not a new feature.
        quieted = 0
        for view in views:
            ident = set()
            for piece in construction.pieces:
                if piece.identity:
                    ident |= piece.view_cells(view)
            quiet = {n for c in ident for n in _neighbours(c)} - ident
            for cell in quiet:
                pc = art.paint[view].get(cell)
                if pc is not None and pc.feature.startswith("surface:"):
                    art.paint[view][cell] = structural[view][cell]
                    quieted += 1
        art.notes.append(f"surface {surface.name} on {domain} across {len(views)} view(s), "
                         f"{quieted} cell(s) quieted around identity construction")

    # ---------------------------------------------------------------------
    # 4. collar trim — reinforces identity, never its only source
    # ---------------------------------------------------------------------
    trim_var, trim_pieces = (architecture.trim or (None, ()))
    if trim_var and trim_var in p:
        style = p[trim_var]
        trim_role = "secondary_accent"
        for view in VIEWS:
            for piece_name in trim_pieces:
                piece = construction.by_name(piece_name)
                if piece is None or not piece.view_cells(view):
                    continue
                cells = piece.view_cells(view)
                sil = construction.silhouette[view]
                # Layer 0 is the fabric the FREE edge terminates over (exactly
                # the cells the piece declares that it shadows); layers 1..n
                # walk inward through the piece itself.
                termination = set(piece.occlusion.get(view, {})) & sil
                layers = _distance_layers(cells, termination, sil)
                # A stripe can sit ON a piece only where that piece is at least
                # two cells thick; otherwise it consumes the piece entirely.
                on_piece = style != "PIPED_EDGE" and len(layers) > 2
                if style == "PIPED_EDGE":
                    target = layers[0]
                elif style == "SINGLE_STRIPE":
                    target = layers[1] if len(layers) > 2 else layers[0]
                else:                                    # DOUBLE_STRIPE
                    target = set(layers[1]) if len(layers) > 1 else set()
                    if len(layers) > 3:
                        target |= layers[3]              # one-cell gap between stripes
                floor = (piece.min_retention if piece.min_retention is not None
                         else architecture.identity_retention)
                before = len(target)
                target = retain_identity(target, piece, view, floor, layers)
                if len(target) < before:
                    art.notes.append(
                        f"retention: held {before - len(target)} trim cell(s) off "
                        f"{piece.name} on {view}")
                for cell in target:
                    current = art.paint[view].get(cell)
                    if current is None or current.role == "trim" and not on_piece:
                        continue
                    if current.feature.startswith(f"{trim_var}"):
                        continue
                    # Trim may only paint the piece it belongs to (or the fabric
                    # that piece terminates over).  Without this it also eats
                    # whatever sits on top — the shoulder articulation vanished
                    # under a braid that had no business being there.
                    owner = art.structural[view].get(cell)
                    if on_piece and owner != piece_name:
                        continue
                    if not on_piece and owner == piece_name:
                        continue
                    art.paint[view][cell] = PaintCell(
                        trim_role, role_steps.get(trim_role, "base"),
                        f"collar_trim:{style}")

    # ---------------------------------------------------------------------
    # 5. layer slot: neck accessory (overlay claim on collar:center)
    # ---------------------------------------------------------------------
    point_accents = {v: [] for v in VIEWS}
    if "neck_accessory" in spec.layers:
        kind = spec.layers["neck_accessory"]
        tip = meta["tip_row"]
        cx = construction.env.width // 2
        if kind == "NECKERCHIEF":
            cells = [(cx - 1, tip), (cx, tip)]
        else:                                     # TIE_KNOT
            cells = [(cx - 1, tip), (cx, tip), (cx - 1, tip + 1)]
        for cell in cells:
            if cell in construction.silhouette["front"]:
                point_accents["front"].append(("neck_accessory", cell, "accent"))

    # ---------------------------------------------------------------------
    # 6. ornaments
    # ---------------------------------------------------------------------
    identity_cells = {v: {c for p in construction.pieces if p.identity
                          for c in p.view_cells(v)} for v in VIEWS}
    for name in spec.ornaments:
        orn = ORNAMENTS[name]
        for view in orn.views:
            cells = _ornament_cells(name, view, construction, meta)[: orn.max_cells]
            # An ornament never gets to eat an identity piece; occupancy governs
            # whether it may coexist, this governs whether it may overwrite.
            if architecture.identity_retention < 1.0:
                cells = [c for c in cells if c not in identity_cells[view]]
            for cell in cells:
                if name in ("chest_emblem", "flap_stud"):
                    point_accents[view].append((name, cell, orn.role))
                else:
                    art.paint[view][cell] = PaintCell(
                        orn.role, role_steps.get(orn.role, "base"), name)

    # Accent economy: cap the number of distinct point-accent FEATURES per view,
    # not raw cells — the corpus reads 1-2 accents, of 1-2 cells each.
    for view in VIEWS:
        kept, features = [], []
        for entry in point_accents[view]:
            if entry[0] not in features:
                if len(features) >= POINT_ACCENT_FEATURES:
                    continue
                features.append(entry[0])
            kept.append(entry)
        kept = kept[:POINT_ACCENT_CAP + 1]
        dropped = len(point_accents[view]) - len(kept)
        if dropped:
            art.notes.append(f"accent economy: dropped {dropped} point accent(s) on {view}")
        art.point_accents[view] = {c for _, c, _ in kept}
        for feature, cell, role in kept:
            if cell in art.paint[view]:
                art.paint[view][cell] = PaintCell(role, role_steps.get(role, "base"), feature)

    # ---------------------------------------------------------------------
    # 7. retention: give detail back until every identity piece still reads
    # ---------------------------------------------------------------------
    _enforce_retention(art, construction, structural, architecture)

    # ---------------------------------------------------------------------
    # 8. focal structure
    # ---------------------------------------------------------------------
    # Focal points are named by the Architecture's own construction metadata
    # where it has an opinion, and otherwise fall back to the centre of each
    # view's occupied mass.  Reading sailor-specific keys unconditionally made
    # this pass unusable by any other Family.
    cx = construction.env.width // 2
    hem = construction.env.height - 1

    def _mass_centre(view):
        cells = construction.silhouette.get(view) or set()
        if not cells:
            return (cx - 1, hem // 2)
        ys = [c[1] for c in cells]
        return (cx - 1, (min(ys) + max(ys)) // 2)

    if "tip_row" in meta:
        art.focal["front"] = (cx - 1, min(meta["tip_row"], hem))
    else:
        art.focal["front"] = _mass_centre("front")
    if "flap_depth" in meta:
        art.focal["back"] = (cx - 1, meta["flap_depth"] - 1)
        art.focal["side"] = (0, meta["flap_depth"] - 1)
    else:
        art.focal["back"] = _mass_centre("back")
        art.focal["side"] = _mass_centre("side")

    return art


def _neighbours(cell):
    x, y = cell
    return ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))


def _outer_ring(cells: set, silhouette: set) -> set:
    """Cells of a region that touch something outside it (or the frame edge)."""
    out = set()
    for (x, y) in cells:
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) not in cells:
                out.add((x, y))
                break
    return out


# Details are reverted in this order when an identity piece is over-painted:
# a braid is the most expendable, a declared construction piece is not revertible
# at all.
_DETAIL_PRIORITY = ("collar_trim", "yoke_trim", "surface:")


def _enforce_retention(art, construction, structural, architecture) -> None:
    """Post-composition guard: no detail may cost an identity piece its read.

    Runs after every writer has had its turn, because occupancy and budget can
    each be satisfied while the composed result still buries the construction.
    """
    for view in VIEWS:
        for piece in construction.pieces:
            floor = (piece.min_retention if piece.min_retention is not None
                     else architecture.identity_retention)
            own = piece.view_cells(view)
            if not piece.identity or not own or floor >= 1.0:
                continue
            # Only DETAIL burial counts.  Another construction piece lying over
            # this one — a tie crossing the collar point — is the layering the
            # garment is made of, not a loss of identity.
            revertible = [
                c for c in own
                if art.paint[view].get(c)
                and any(art.paint[view][c].feature.startswith(p) for p in _DETAIL_PRIORITY)
            ]
            claimed = len(own) - len(revertible)
            need = math.ceil(len(own) * floor - 1e-9)
            if claimed >= need:
                continue
            revertible.sort(key=lambda c: (c[1], c[0]))
            given = 0
            for cell in revertible:
                if claimed + given >= need:
                    break
                art.paint[view][cell] = structural[view][cell]
                given += 1
            if given:
                art.notes.append(
                    f"retention: gave {given} cell(s) back to {piece.name} on {view}")


def retain_identity(target: set, piece, view: str, retention: float, layers=None) -> set:
    """Trim a detail's target so an identity piece keeps enough of its own role.

    General composition rule, not a drawing rule: whatever wants to paint over a
    piece keeps only the cells nearest that piece's free edge — where a braid or
    a piping actually belongs — and gives the rest back.
    """
    own = piece.view_cells(view)
    if not piece.identity or not own or retention >= 1.0:
        return target
    inside = {c for c in target if c in own}
    if not inside:
        return target
    allowed = int(len(own) * (1.0 - retention))
    if len(inside) <= allowed:
        return target
    order = {}
    for i, layer in enumerate(layers or []):
        for cell in layer:
            order.setdefault(cell, i)
    keep = sorted(inside, key=lambda c: (order.get(c, 99), c[1], c[0]))[:allowed]
    return (target - inside) | set(keep)


def _distance_layers(piece_cells: set, termination: set, silhouette: set) -> list:
    """[cells the free edge lies over, then rings walking inward through the piece]."""
    layers = [set(termination)]
    seen, frontier = set(termination), set(termination)
    while frontier:
        nxt = set()
        for (x, y) in frontier:
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if n in piece_cells and n not in seen:
                    nxt.add(n)
        if not nxt:
            break
        layers.append(nxt)
        seen |= nxt
        frontier = nxt
    return layers


def _adjacent_ring(edge_cells: set, own_cells: set, silhouette: set) -> set:
    """The one-cell ring just outside a piece, along its free edges."""
    out = set()
    for (x, y) in edge_cells:
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if n not in own_cells and n in silhouette:
                out.add(n)
    return out


def _ornament_cells(name: str, view: str, construction, meta) -> list:
    env = construction.env
    sil = construction.silhouette[view]
    # hem_band and cuff_band are decorative BANDS — linework, not garment edge —
    # so both terminate one cell inboard (grammar.terminate_inboard).  Taken to
    # the boundary the hem band painted a hard bar across the full width of the
    # sprite (040's "yellow rectangle across the torso"), and the cuff band ends
    # on the sleeve's outer column, which is where the Farmer's arm is drawn.
    if name == "hem_band":
        rows = sorted({y for _, y in sil})
        band = {c for c in sil if c[1] == rows[-1]}
        return sorted(terminate_inboard(band, run_axis=0))
    if name == "cuff_band":
        sleeve = construction.by_name("sleeve")
        cells = sleeve.view_cells(view)
        if not cells:
            return []
        bottom = max(y for _, y in cells)
        return sorted(terminate_inboard(
            {c for c in cells if c[1] == bottom}, run_axis=0))
    if name == "chest_emblem" and view == "front":
        insert = construction.by_name("front_insert").view_cells("front")
        if not insert:
            return []
        row = max(y for _, y in insert)
        return sorted(c for c in insert if c[1] == row)
    if name == "flap_stud":
        flap = construction.by_name("rear_flap")
        cells = flap.view_cells(view)
        if not cells:
            return []
        bottom = max(y for _, y in cells)
        row = sorted(c for c in cells if c[1] == bottom)
        return [row[0], row[-1]] if len(row) > 1 else row
    return []
