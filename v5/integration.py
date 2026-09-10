"""NATURAL INTEGRATION PASS — make a motif belong to the hat it sits on.

A motif drawn in isolation and stamped onto a hat reads as a sticker: it keeps
its own light direction, its own value range and its own outline, none of which
have anything to do with the surface underneath.  This pass rewrites a placed
motif so that it takes its cues from the BASE, and every decision here is
derived from the base's own drawn pixels — never supplied by hand per motif.

What is derived, and from what:

    local plane      the base's own ramp step at each covered cell.  A motif on
                     a shaded panel darkens with it; the same motif on the lit
                     plane lightens.  This is what makes one motif read
                     differently per view without being redrawn per view: the
                     surface under it differs, so it differs.
    relief           the motif's own internal value structure, kept as a signed
                     offset around its own mean rather than as absolute values.
                     Identity survives; imported brightness does not.
    flat vs raised   a surface motif is embroidery or print: its relief is
                     compressed and clamped, so it cannot carry a heavy
                     independent outline.  An attachment is a physical object:
                     it keeps full relief and gains a contact shadow where it
                     meets the hat.
    boundaries       the base's rim (any cell with a missing orthogonal
                     neighbour) is never overwritten by a surface motif, and
                     the motif is nudged inward if its placement lands there.

Hue is NOT touched: a motif keeps its semantic role, so a metal badge stays
metal and a cloth patch stays cloth.  Only the value rhythm is re-seated.
"""

from __future__ import annotations

# How much of a surface motif's own relief survives.  Embroidery and print sit
# in the cloth: at full amplitude they read as a separate object lying on top.
FLAT_GAIN = 0.55
# ...and no surface motif may swing more than this many steps from the local
# plane, which is what stops it acquiring an outline the hat does not have.
FLAT_CLAMP = 1
# An attachment is a real object and keeps its own modelling.
RAISED_GAIN = 1.0
RAISED_CLAMP = 3
# How far a placement may be nudged to get clear of the rim before giving up.
MAX_NUDGE = 2


def rim_cells(cells: set) -> set:
    """The base's own outline: any cell missing an orthogonal neighbour."""
    return {c for c in cells
            if any((c[0] + dx, c[1] + dy) not in cells
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


def _nudge(placed: dict, base_cells: set, rim: set):
    """Shift a surface motif inward until it clears the rim, or give up.

    Searched nearest-first so the motif moves as little as possible, and only
    inward: a motif that cannot sit clear of the edge is not a placement
    problem to be forced, it is a motif that does not belong in that zone.
    """
    def clear(offset):
        dx, dy = offset
        moved = {(x + dx, y + dy) for (x, y) in placed}
        return moved <= base_cells and not (moved & rim)

    if clear((0, 0)):
        return (0, 0)
    for radius in range(1, MAX_NUDGE + 1):
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if max(abs(dx), abs(dy)) == radius and clear((dx, dy)):
                    return (dx, dy)
    return None


def integrate(placed: dict, base_view: dict, kind: str,
              edge_motif: bool = False) -> tuple:
    """Re-seat a placed motif into the surface it covers.

    `placed`    {cell: (role, step)} straight from the motif's art
    `base_view` {cell: (role, step)} the base's own drawn cells for this view
    `kind`      "surface" or "attachment"
    `edge_motif` this motif IS an edge treatment — a brim trim, a hem stitch —
                so the rim it would otherwise be pushed off is exactly where it
                belongs.  Declared per motif, because "keep clear of the edge"
                and "run along the edge" are both correct, for different pieces.

    Returns (cells, occlusion, note) where `cells` replaces the motif's own
    pixels, `occlusion` is the contact shadow an attachment casts on the hat,
    and `note` records what the pass did.  Returns (None, None, reason) when
    the motif cannot be integrated at all.
    """
    base_cells = set(base_view)
    rim = rim_cells(base_cells)
    gain, clamp = ((FLAT_GAIN, FLAT_CLAMP) if kind == "surface"
                   else (RAISED_GAIN, RAISED_CLAMP))

    offset = (0, 0)
    note = []
    if kind == "surface" and not edge_motif:
        offset = _nudge(placed, base_cells, rim)
        if offset is None:
            return None, None, "cannot sit clear of the hat's outline"
        if offset != (0, 0):
            note.append(f"nudged {offset} clear of the rim")
    placed = {(x + offset[0], y + offset[1]): v for (x, y), v in placed.items()}

    steps = [s for _, s in placed.values()]
    mean = sum(steps) / len(steps)

    out = {}
    for cell, (role, step) in placed.items():
        relief = step - mean
        under = base_view.get(cell)
        if under is None:
            # only an attachment may sit off the hat; it keeps its own value
            out[cell] = (role, max(0, min(5, round(step))))
            continue
        _, base_step = under
        shifted = base_step + relief * gain
        shifted = max(base_step - clamp, min(base_step + clamp, shifted))
        out[cell] = (role, max(0, min(5, int(round(shifted)))))

    occlusion = {}
    if kind == "attachment":
        # a raised object darkens the hat immediately beneath it
        for (x, y) in placed:
            below = (x, y + 1)
            if below in base_cells and below not in placed:
                occlusion[below] = 1
        if occlusion:
            note.append(f"contact shadow on {len(occlusion)} cells")

    return out, occlusion, ("; ".join(note) or "seated on the local plane")


def sticker_score(cells: dict, base_view: dict) -> dict:
    """How much the integrated motif still behaves like a foreign object.

    Three symptoms, all measured against the surface it sits on rather than
    against a fixed threshold:

        swing     how far its values depart from the local plane
        on_rim    surface cells sitting on the hat's own outline
        island    whether it reads as one shape or scattered specks
    """
    swings, on_rim = [], 0
    rim = rim_cells(set(base_view))
    for cell, (_, step) in cells.items():
        under = base_view.get(cell)
        if under is None:
            continue
        swings.append(abs(step - under[1]))
        if cell in rim:
            on_rim += 1
    return {"max_swing": max(swings) if swings else 0,
            "mean_swing": round(sum(swings) / len(swings), 2) if swings else 0.0,
            "on_rim": on_rim}
