"""DETERMINISTIC PROJECTION (Pass 13) — zero design RNG.

Derives front / right / left / back, the dye mask and the Fashion Sense export
metadata from one already-resolved garment.  Projection may never change
colour, pattern, ornament, trim, layer occupancy, architecture or silhouette.
If the views disagree, that is a bug — and `check_continuity` says so.
"""

from __future__ import annotations

from dataclasses import dataclass

from .ag import TRANSPARENT, to_rows
from .grammar import (ATLAS_ORDER, FS_DISABLE_GRAYSCALE, FS_FORMAT, GIRTH,
                      HAT_HEAD_POSITION_Y, required_coverage)
from .pngio import blank_image, nearest_scale

# authored view -> runtime directions it serves
VIEW_FOR_DIRECTION = {"front": "front", "right": "side", "left": "side", "back": "back"}
MIRRORED = {"left"}


@dataclass
class Projection:
    directions: dict          # direction -> rows of RGBA
    dye_mask: dict            # direction -> rows of RGBA (white = dyeable body)
    envelope: object
    notes: list


def _mirror(rows):
    return [list(reversed(r)) for r in rows]


def project(spec, construction, art, raster) -> Projection:
    env = spec.envelope
    directions, masks, notes = {}, {}, []
    body_features = set(construction.surface_domains.get("body", ()))
    for direction in ATLAS_ORDER:
        view = VIEW_FOR_DIRECTION[direction]
        rows = to_rows(raster[view], env)
        mask_cells = {c for c, pc in art.paint[view].items() if pc.feature in body_features}
        mask = [[(255, 255, 255, 255) if (x, y) in mask_cells else TRANSPARENT
                 for x in range(env.width)] for y in range(env.height)]
        if direction in MIRRORED:
            rows, mask = _mirror(rows), _mirror(mask)
        directions[direction] = rows
        masks[direction] = mask
    return Projection(directions, masks, env, notes)


def check_continuity(spec, construction, art) -> list:
    """Girth features must occupy the same rows in every view (section 38)."""
    problems = []
    # A girth feature must exist in every view and be anchored to the same rows.
    # Its extent may still differ per view — a sailor collar descends into a V on
    # the front — so continuity is anchor agreement, not identical cell counts.
    for piece in construction.pieces:
        if piece.wrap != GIRTH:
            continue
        rows = {v: {y for _, y in piece.view_cells(v)} for v in ("front", "side", "back")}
        missing = [v for v, r in rows.items() if not r]
        if missing:
            problems.append(f"girth piece {piece.name} absent from {missing}")
            continue
        edge = min if piece.girth_anchor == "top" else max
        anchors = {edge(r) for r in rows.values()}
        if len(anchors) > 1:
            problems.append(
                f"girth piece {piece.name} ({piece.girth_anchor}-anchored) "
                f"sits at different rows per view: {rows}")
    # A girth surface must obey ONE rule in every view.  Which cells are visible
    # differs per view (the flap covers the back), but the rule may not.
    if spec.surface:
        from .surface import SURFACES
        surface = SURFACES[spec.surface["family"]]
        period, phase = spec.surface.get("period"), spec.surface.get("phase")
        if (surface.wrap == GIRTH and surface.periodic
                and period is not None and phase is not None):
            axis = 1 if spec.surface["family"] == "horizontal_stripe" else 0
            for view in ("front", "side", "back"):
                for cell, pc in art.paint[view].items():
                    if pc.feature.startswith("surface:") and (cell[axis] + phase) % period:
                        problems.append(
                            f"{view}: surface cell {cell} breaks the girth rule "
                            f"(period {period}, phase {phase})")
    return problems


def check_coverage(spec, projection) -> list:
    """The Farmer shows skin wherever the garment fails to cover the top rows.

    Only meaningful for slots that actually owe coverage.  A hat owes none: it
    is an object resting on the head, not a layer over skin, and the vanilla
    corpus occupies a median 27% of its frame.  Gated on the SlotContract so
    the torso rule cannot leak into other slots.
    """
    from .contracts import SLOT_LIBRARY
    if not SLOT_LIBRARY[spec.slot].requires_coverage:
        return []
    problems = []
    need = required_coverage(spec.envelope)
    for direction, rows in projection.directions.items():
        view = VIEW_FOR_DIRECTION[direction]
        want = need[view]
        for y, pattern in enumerate(want):
            pat = pattern[::-1] if direction in MIRRORED else pattern
            for x, ch in enumerate(pat):
                if ch == "#" and rows[y][x][3] == 0:
                    problems.append(f"{direction}: uncovered required cell ({x},{y})")
    return problems


def atlas(projection, scale: int | None = None):
    """Fashion Sense sheet: the four directions stacked in ATLAS_ORDER."""
    env = projection.envelope
    sheet = blank_image(env.width, env.height * len(ATLAS_ORDER))
    for i, direction in enumerate(ATLAS_ORDER):
        for y, row in enumerate(projection.directions[direction]):
            for x, px in enumerate(row):
                sheet[i * env.height + y][x] = px
    if scale:
        sheet = nearest_scale(sheet, scale)
    return sheet


def mask_atlas(projection, scale: int | None = None):
    env = projection.envelope
    sheet = blank_image(env.width, env.height * len(ATLAS_ORDER))
    for i, direction in enumerate(ATLAS_ORDER):
        for y, row in enumerate(projection.dye_mask[direction]):
            for x, px in enumerate(row):
                sheet[i * env.height + y][x] = px
    if scale:
        sheet = nearest_scale(sheet, scale)
    return sheet


def fs_metadata(spec) -> dict:
    """Fashion Sense content.json entry for one generated shirt."""
    env = spec.envelope
    return {
        "Format": FS_FORMAT,
        "Name": f"V5 {spec.family} {spec.architecture} {spec.seed}",
        "Id": f"v5.sailor.{spec.seed}",
        "ShirtSize": {"Width": env.width, "Height": env.height},
        "Texture": f"sailor_{spec.seed}.png",
        "DisableGrayscale": FS_DISABLE_GRAYSCALE,
        "HideSleeves": False,
        "SleeveColors": [
            list(spec.palette.color("body", step))[:3]
            for step in ("shadow", "base", "light") if step in spec.palette.steps
        ],
    }


HAT_DIRECTION_KEYS = {"front": "FrontHat", "right": "RightHat",
                      "left": "LeftHat", "back": "BackHat"}


def fs_hat_metadata(spec, hide_hair: bool) -> dict:
    """Fashion Sense hat.json for one generated hat.

    HeadPosition.X is COMPUTED, never authored: FS centres a hat frame on a
    20-vanilla-pixel head box, so X = (width - 20*(4/Scale)) / 2.  At our
    native 20x20 @ Scale 4 that is exactly 0, which is why this Architecture
    needs no horizontal placement maths.  Verified against 746 shipping FS hat
    models (width 20 -> 0, 16 -> -2, 32@2.0 -> -4, 24@2.0 -> -8).

    HeadPosition.Y is the MEASURED seating correction (grammar.HAT_HEAD_POSITION_Y).
    Captured in game, our hats sat two sprite pixels higher on the head than
    vanilla hats with the same sprite geometry — half a Fashion-Sense-vs-vanilla
    transform difference, half our own content sitting a row higher in frame.
    It is corrected here rather than in the geometry so the authored silhouettes
    and every corpus-derived placement number keep their meaning.

    HideHair is the Architecture's declared hair policy.  Fashion Sense exposes
    no other lever over hair for a custom hat — it never applies the vanilla
    per-hairstyle offset — so the policy is binary by construction.
    """
    env = spec.envelope
    head_x = int((env.width - 20 * (4 / env.scale)) / 2)
    block = {}
    for i, direction in enumerate(ATLAS_ORDER):
        block[HAT_DIRECTION_KEYS[direction]] = {
            "DisableGrayscale": FS_DISABLE_GRAYSCALE,
            "HideHair": hide_hair,
            "HatSize": {"Width": env.width, "Length": env.height},
            "StartingPosition": {"X": 0, "Y": i * env.height},
            "HeadPosition": {"X": head_x,
                             "Y": env.bp_for(direction)[1] + HAT_HEAD_POSITION_Y},
        }
    return block
