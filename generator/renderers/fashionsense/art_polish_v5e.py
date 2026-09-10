"""Reusable gameplay-footprint art polish for established upper garments.

This pass changes shade roles only. It cannot add/remove alpha, alter anchors,
change a Fashion Sense category, or replace article-specific construction.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from generator.png_utils import RGBA
from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER
from generator.renderers.fashionsense.upper_v5b import _default_value, _mask_value

ROOT = Path(__file__).resolve().parents[3]
GRAMMAR = ROOT / "generator" / "data" / "fashionsense" / "art_polish_v5e.json"


@dataclass(frozen=True)
class PolishedUpperFrames:
    frames: dict[str, list[list[RGBA]]]
    default_frames: dict[str, list[list[RGBA]]]
    metrics: dict[str, Any]


def load_art_polish_grammar() -> dict[str, Any]:
    return json.loads(GRAMMAR.read_text(encoding="utf-8"))


def _copy(frames):
    return {direction: [list(row) for row in frames[direction]] for direction in DIRECTION_ORDER}


def _exterior(frame, x: int, y: int) -> bool:
    return any(nx < 0 or nx >= 16 or ny < 0 or ny >= 16 or not frame[ny][nx][3] for nx, ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)))


def _bounds(frame, y: int):
    xs = [x for x, pixel in enumerate(frame[y]) if pixel[3]]
    return None if not xs else (min(xs), max(xs))


def polish_upper_frames(base, source_frames, source_defaults, *, article_family: str) -> PolishedUpperFrames:
    """Apply selective optical weight while preserving every opaque cell."""
    frames = _copy(source_frames); defaults = _copy(source_defaults)
    before_alpha = {d: {(x,y) for y,row in enumerate(frames[d]) for x,p in enumerate(row) if p[3]} for d in DIRECTION_ORDER}
    changed = {d: set() for d in DIRECTION_ORDER}
    anchor_counts: dict[str, int] = {}
    for direction in DIRECTION_ORDER:
        frame = frames[direction]
        for y in range(16):
            bounds = _bounds(frame, y)
            if not bounds: continue
            lo, hi = bounds
            for x in range(lo, hi + 1):
                if not frame[y][x][3] or not _exterior(frame, x, y): continue
                neck_anchor = y <= 2 and 5 <= x <= 10
                side_anchor = y >= 4 and x in {lo, hi}
                hem_anchor = y >= 11 and (x in {lo, hi} or (direction in {"front", "back"} and x in {7, 8}))
                # A native animated sleeve begins immediately outside this
                # upper torso edge. A full contour here visually amputates the
                # sleeve and makes a jacket read as a vest. Preserve a mid-dark
                # fabric bridge for structured outerwear, then restore the
                # strong contour below the arm junction.
                native_sleeve_bridge = article_family == "STRUCTURED_FIELD_JACKET" and 3 <= y <= 6 and x in {lo, hi}
                underarm_anchor = 7 == y and x in {lo, hi}
                lit_upper_left = y <= 4 and x <= 7 and not neck_anchor and x not in {lo, hi}
                if native_sleeve_bridge:
                    role = "SHADOW"
                elif neck_anchor or side_anchor or hem_anchor or underarm_anchor:
                    role = "EXTERIOR_CONTOUR" if side_anchor or neck_anchor else "DEEP_CREASE"
                elif lit_upper_left:
                    role = "SHADOW"
                else:
                    continue
                target = _mask_value(base, role); default = _default_value(base, role)
                if frames[direction][y][x] != target or defaults[direction][y][x] != default:
                    frames[direction][y][x] = target; defaults[direction][y][x] = default; changed[direction].add((x,y))
        # Reinforce only the shadow-facing right side at connected intervals.
        reinforcement_rows = (8, 11) if article_family == "STRUCTURED_FIELD_JACKET" else range(5, 12, 3)
        for y in reinforcement_rows:
            bounds = _bounds(frame, y)
            if bounds and bounds[1] - bounds[0] >= 5:
                x = bounds[1] - 1
                if frame[y][x][3]:
                    frames[direction][y][x] = _mask_value(base, "SHADOW")
                    defaults[direction][y][x] = _default_value(base, "SHADOW")
                    changed[direction].add((x,y))
        anchor_counts[direction] = sum(1 for y,row in enumerate(frames[direction]) for x,p in enumerate(row) if p[3] and _exterior(frames[direction],x,y) and p == _mask_value(base,"EXTERIOR_CONTOUR"))
    after_alpha = {d: {(x,y) for y,row in enumerate(frames[d]) for x,p in enumerate(row) if p[3]} for d in DIRECTION_ORDER}
    if before_alpha != after_alpha:
        raise ValueError("art polish changed frozen alpha geometry")
    return PolishedUpperFrames(frames, defaults, {
        "grammar": "POST_V5E_GAMEPLAY_ART_POLISH",
        "articleFamily": article_family,
        "changedShadeRoleCells": {d: len(cells) for d,cells in changed.items()},
        "darkExteriorAnchors": anchor_counts,
        "alphaGeometryPreserved": True,
        "runtimeFieldsChanged": False,
    })


def soften_shared_rear_neck(
    base,
    polished: PolishedUpperFrames,
    *,
    protected_cells: frozenset[tuple[int, int]] = frozenset(),
) -> PolishedUpperFrames:
    """Remove an inherited pointed back-opening crease beneath rear collars.

    The HD foundation can carry a narrow V-shaped opening down the upper back.
    That is useful for some front constructions, but beneath a rear collar it
    reads as a stamped upside-down triangle.  This micro-pass only restores
    the unprotected lower point to adjacent proven fabric shade roles.  It
    changes neither alpha nor any front/side cell, and article-authored rear
    collar/yoke cells supplied in ``protected_cells`` remain untouched.
    """
    frames = _copy(polished.frames)
    defaults = _copy(polished.default_frames)
    before_alpha = {(x, y) for y, row in enumerate(frames["back"]) for x, pixel in enumerate(row) if pixel[3]}
    deep_roles = {_mask_value(base, "DEEP_CREASE"), _mask_value(base, "STRUCTURAL_EDGE")}
    candidates = {
        (x, y)
        for y in range(2, 6)
        for x in range(4, 12)
        if (x, y) not in protected_cells and frames["back"][y][x] in deep_roles
    }
    # A shallow neckline has no lower point to remove.  This keeps quiet tees
    # unchanged while allowing all garments to share the same safe function.
    if not any(y >= 3 for _, y in candidates):
        metrics = dict(polished.metrics)
        metrics["rearNeckMicroFix"] = {
            "changedCells": 0,
            "removedPointDepth": 0,
            "protectedCells": len(protected_cells),
            "frontSideUntouched": True,
            "alphaGeometryPreserved": True,
        }
        return PolishedUpperFrames(frames, defaults, metrics)

    changed: set[tuple[int, int]] = set()
    removed_depth = max(y for _, y in candidates)
    for x, y in sorted(candidates, key=lambda cell: (cell[1], abs(cell[0] - 7.5)), reverse=True):
        # Sample the nearest non-crease fabric plane on the corresponding side
        # of the same row. This preserves the existing light direction and
        # material shading instead of painting a new flat color.
        if x <= 7:
            search = list(range(x - 1, -1, -1)) + list(range(x + 1, 16))
        else:
            search = list(range(x + 1, 16)) + list(range(x - 1, -1, -1))
        source = next(
            (
                sx
                for sx in search
                if frames["back"][y][sx][3]
                and frames["back"][y][sx] not in deep_roles
                and (sx, y) not in candidates
            ),
            None,
        )
        if source is None:
            frames["back"][y][x] = _mask_value(base, "BASE")
            defaults["back"][y][x] = _default_value(base, "BASE")
        else:
            frames["back"][y][x] = frames["back"][y][source]
            defaults["back"][y][x] = defaults["back"][y][source]
        changed.add((x, y))

    after_alpha = {(x, y) for y, row in enumerate(frames["back"]) for x, pixel in enumerate(row) if pixel[3]}
    if before_alpha != after_alpha:
        raise ValueError("rear-neck micro-fix changed frozen alpha geometry")
    metrics = dict(polished.metrics)
    metrics["rearNeckMicroFix"] = {
        "changedCells": len(changed),
        "changedCoordinates": sorted(changed),
        "removedPointDepth": removed_depth,
        "protectedCells": len(protected_cells),
        "frontSideUntouched": True,
        "alphaGeometryPreserved": True,
    }
    return PolishedUpperFrames(frames, defaults, metrics)


def polish_open_cardigan_premium_execution(
    base,
    polished: PolishedUpperFrames,
    *,
    signal_cells: dict[str, dict[str, set[tuple[int, int]]]],
) -> PolishedUpperFrames:
    """Optional higher-craft shade/construction finish for an open cardigan.

    This is a bounded execution profile, not a renderer or a rarity layer. It
    keeps the established alpha silhouette and existing cardigan topology,
    but gives the opening, patch pockets, hem, side depth and rear knit field
    clearer connected planes. Fixed semantic opening/collar colors are left
    for the palette adapter to shade according to their signal ownership.
    """
    frames = _copy(polished.frames)
    defaults = _copy(polished.default_frames)
    before_alpha = {
        direction: {(x, y) for y, row in enumerate(frames[direction]) for x, pixel in enumerate(row) if pixel[3]}
        for direction in DIRECTION_ORDER
    }
    changed = {direction: set() for direction in DIRECTION_ORDER}

    def put(direction: str, x: int, y: int, role: str) -> None:
        if not (0 <= x < 16 and 0 <= y < 16 and frames[direction][y][x][3]):
            return
        target = _mask_value(base, role)
        default = _default_value(base, role)
        if frames[direction][y][x] != target or defaults[direction][y][x] != default:
            frames[direction][y][x] = target
            defaults[direction][y][x] = default
            changed[direction].add((x, y))

    # Front: model the two knit leaves as fabric planes around the existing
    # semantic opening. The lit leaf receives a short connected upper plane;
    # the shadow leaf receives a longer, quieter return plane.
    front_opening = signal_cells.get("opening", {}).get("front", set())
    by_row: dict[int, list[int]] = {}
    for x, y in front_opening:
        by_row.setdefault(y, []).append(x)
    for y, xs in by_row.items():
        lo, hi = min(xs), max(xs)
        if y <= 8:
            put("front", lo - 1, y, "LIGHT" if y <= 5 else "BASE")
        if y <= 10:
            put("front", hi + 1, y, "SHADOW")

    # Rebuild the two existing patch-pocket carriers as clean outward cloth
    # planes instead of dark horizontal bars. The inner corners still meet the
    # opening leaves; the broad inner shirt remains unobstructed.
    for xs, lit in (((3, 4, 5), True), ((10, 11, 12), False)):
        for x in xs:
            put("front", x, 10, "SHADOW")
            put("front", x, 11, "LIGHT" if lit and x <= 3 else "BASE" if lit else "SHADOW")
            put("front", x, 12, "BASE" if lit else "SHADOW")
        put("front", xs[0], 12, "SHADOW")
        put("front", xs[-1], 12, "SHADOW")

    # A continuous two-plane ribbed termination reads cleaner than isolated
    # dark squares. It remains restrained and uses no added color or motif.
    for direction in DIRECTION_ORDER:
        occupied = [y for y in range(16) if any(pixel[3] for pixel in frames[direction][y])]
        if not occupied:
            continue
        bottom = max(occupied)
        bounds = _bounds(frames[direction], max(0, bottom - 1))
        if bounds:
            lo, hi = bounds
            for x in range(lo + 1, hi):
                put(direction, x, bottom - 1, "BASE")
            for x in range(lo + 2, hi - 1):
                put(direction, x, bottom, "SHADOW")
            for x in (lo + 1, hi - 1):
                put(direction, x, bottom, "DEEP_CREASE")

    # Side views retain one hanging knit edge, then gain a compressed pocket
    # plane and lower fold so they no longer read as generic shirt crops.
    for direction, edge, inner_step in (("right", 10, -1), ("left", 5, 1)):
        opening = signal_cells.get("opening", {}).get(direction, set())
        for x, y in opening:
            if 4 <= y <= 9:
                put(direction, x + inner_step, y, "LIGHT" if direction == "left" and y <= 6 else "SHADOW")
        pocket_xs = (edge - 2, edge - 1, edge) if direction == "right" else (edge, edge + 1, edge + 2)
        for x in pocket_xs:
            put(direction, x, 10, "SHADOW")
            put(direction, x, 11, "BASE" if x != edge else "DEEP_CREASE")
        put(direction, edge - 1 if direction == "right" else edge + 1, 12, "SHADOW")

    # Back: preserve the soft rear-neck correction and a coherent knit mass.
    # Long inherited side creases are softened into fabric shade; restraint is
    # preferable to adding small rear marks that could read as decoration.
    for y in range(6, 11):
        put("back", 1, y, "SHADOW")
        put("back", 14, y, "SHADOW")

    after_alpha = {
        direction: {(x, y) for y, row in enumerate(frames[direction]) for x, pixel in enumerate(row) if pixel[3]}
        for direction in DIRECTION_ORDER
    }
    if before_alpha != after_alpha:
        raise ValueError("premium cardigan execution changed frozen alpha geometry")
    metrics = dict(polished.metrics)
    metrics["premiumCardiganExecution"] = {
        "changedShadeRoleCells": {direction: len(cells) for direction, cells in changed.items()},
        "alphaGeometryPreserved": True,
        "runtimeFieldsChanged": False,
        "newMotifs": 0,
        "newPaletteRoles": 0,
        "derivedTrimShadeRoles": ["SHADOW", "LIGHT"],
        "constructionSystems": ["opening_planes", "patch_pocket_planes", "ribbed_termination", "side_depth", "rear_knit_plane_cleanup"],
    }
    return PolishedUpperFrames(frames, defaults, metrics)


def refine_open_cardigan_premium_construction(
    base,
    polished: PolishedUpperFrames,
    *,
    signal_cells: dict[str, dict[str, set[tuple[int, int]]]],
) -> PolishedUpperFrames:
    """Bounded silhouette/drape refinement for the OPEN_CARDIGAN proof.

    The first three rows are frozen because they carry the proven Farmer body
    coverage contract. Lower rows may taper and flare within the same 16x16
    upper-body frame. The helper also rebuilds the existing opening/layering
    signals into curved knit leaves; it adds no new decorative system.
    """
    frames = _copy(polished.frames)
    defaults = _copy(polished.default_frames)
    before = _copy(polished.frames)
    before_alpha = {
        direction: {(x, y) for y, row in enumerate(frames[direction]) for x, pixel in enumerate(row) if pixel[3]}
        for direction in DIRECTION_ORDER
    }
    changed = {direction: set() for direction in DIRECTION_ORDER}
    added = {direction: set() for direction in DIRECTION_ORDER}
    removed = {direction: set() for direction in DIRECTION_ORDER}

    # Rows 0-2 are intentionally absent: the proven body-coverage carrier is
    # byte-preserved. Bounds are inclusive and never leave the logical frame.
    target_bounds = {
        "front": {**{y: (1, 14) for y in range(3, 15)}, 15: (2, 13)},
        "back": {**{y: (1, 14) for y in range(3, 15)}, 15: (2, 13)},
        "right": {3: (1, 14), 4: (1, 14), **{y: (2, 14) for y in range(5, 8)}, **{y: (3, 14) for y in range(8, 10)}, **{y: (4, 14) for y in range(10, 12)}, **{y: (4, 13) for y in range(12, 15)}, 15: (4, 13)},
        "left": {3: (1, 14), 4: (1, 14), **{y: (1, 13) for y in range(5, 8)}, **{y: (1, 12) for y in range(8, 10)}, **{y: (1, 11) for y in range(10, 12)}, **{y: (2, 11) for y in range(12, 15)}, 15: (2, 11)},
    }

    def nearest_source(direction: str, y: int, x: int):
        candidates = [sx for sx in range(16) if before[direction][y][sx][3]]
        if not candidates:
            return _mask_value(base, "BASE"), _default_value(base, "BASE")
        sx = min(candidates, key=lambda value: abs(value - x))
        return before[direction][y][sx], polished.default_frames[direction][y][sx]

    for direction, rows in target_bounds.items():
        for y, (lo, hi) in rows.items():
            for x in range(16):
                wanted = lo <= x <= hi
                opaque = bool(frames[direction][y][x][3])
                if opaque and not wanted:
                    frames[direction][y][x] = (0, 0, 0, 0)
                    defaults[direction][y][x] = (0, 0, 0, 0)
                    removed[direction].add((x, y)); changed[direction].add((x, y))
                elif wanted and not opaque:
                    frames[direction][y][x], defaults[direction][y][x] = nearest_source(direction, y, x)
                    added[direction].add((x, y)); changed[direction].add((x, y))

    def put(direction: str, x: int, y: int, role: str) -> None:
        if not frames[direction][y][x][3]:
            return
        target = _mask_value(base, role); default = _default_value(base, role)
        if frames[direction][y][x] != target or defaults[direction][y][x] != default:
            frames[direction][y][x] = target; defaults[direction][y][x] = default; changed[direction].add((x, y))

    # Remove obsolete straight opening/inner carriers before authoring the
    # curved leaves. Signal ownership lets the palette adapter reconstruct the
    # same Trim and SecondaryFabric roles without fixed RGB painting.
    for system in ("opening", "layering", "pockets"):
        for x, y in signal_cells.get(system, {}).get("front", set()):
            put("front", x, y, "BASE")
    new_opening: set[tuple[int, int]] = set()
    new_layering: set[tuple[int, int]] = set()
    for y in range(2, 14):
        if y <= 3 or y >= 10:
            left, right = 6, 9
        else:
            left, right = 5, 10
        new_opening.update(((left, y), (right, y)))
        new_layering.update((x, y) for x in range(left + 1, right))
    signal_cells.setdefault("opening", {})["front"] = new_opening
    signal_cells.setdefault("layering", {})["front"] = new_layering

    # Hanging side edges bow outward once, then return into the hem.
    for direction, upper, lower in (("right", 10, 11), ("left", 5, 4)):
        for x, y in signal_cells.get("opening", {}).get(direction, set()):
            put(direction, x, y, "BASE")
        edge = {(upper if y <= 6 or y >= 12 else lower, y) for y in range(3, 14)}
        signal_cells["opening"][direction] = edge

    # Patch pockets become shallow trapezoids attached to the outer leaves.
    new_pockets = {
        (x, y)
        for y, xs in ((10, (3, 4, 11, 12)), (11, (2, 3, 4, 11, 12, 13)), (12, (2, 3, 4, 11, 12, 13)))
        for x in xs
    }
    signal_cells.setdefault("pockets", {})["front"] = new_pockets
    for x, y in new_pockets:
        put("front", x, y, "SHADOW" if y == 10 or x in {2, 13} else "LIGHT" if x <= 3 and y == 11 else "BASE" if x <= 4 else "SHADOW")

    # Recompute selective contour weight after alpha refinement. Newly interior
    # old contours return to fabric planes; new outer bounds gain clean anchors.
    for direction in DIRECTION_ORDER:
        for y in range(3, 16):
            bounds = _bounds(frames[direction], y)
            if not bounds:
                continue
            lo, hi = bounds
            for x in range(lo + 1, hi):
                if frames[direction][y][x] == _mask_value(base, "EXTERIOR_CONTOUR"):
                    put(direction, x, y, "BASE" if x <= 7 else "SHADOW")
            put(direction, lo, y, "SHADOW" if y <= 7 else "EXTERIOR_CONTOUR")
            put(direction, hi, y, "EXTERIOR_CONTOUR")
        bottom = max(y for y in range(16) if any(pixel[3] for pixel in frames[direction][y]))
        lo, hi = _bounds(frames[direction], bottom)
        for x in range(lo + 1, hi):
            put(direction, x, bottom, "SHADOW")

    after_alpha = {
        direction: {(x, y) for y, row in enumerate(frames[direction]) for x, pixel in enumerate(row) if pixel[3]}
        for direction in DIRECTION_ORDER
    }
    # A single connected component is required in every direction.
    for direction, cells in after_alpha.items():
        pending = [next(iter(cells))]; visited = set()
        while pending:
            cell = pending.pop()
            if cell in visited: continue
            visited.add(cell)
            x, y = cell
            pending.extend((nx, ny) for nx, ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)) if (nx, ny) in cells and (nx, ny) not in visited)
        if visited != cells:
            raise ValueError(f"premium cardigan construction detached alpha in {direction}")
    if any(y <= 2 for cells in removed.values() for _, y in cells):
        raise ValueError("premium cardigan construction changed frozen coverage rows")

    metrics = dict(polished.metrics)
    metrics["premiumCardiganConstruction"] = {
        "alphaAdded": {direction: len(cells) for direction, cells in added.items()},
        "alphaRemoved": {direction: len(cells) for direction, cells in removed.items()},
        "addedCoordinates": {direction: sorted(cells) for direction, cells in added.items()},
        "removedCoordinates": {direction: sorted(cells) for direction, cells in removed.items()},
        "coverageRowsZeroToTwoPreserved": all(before_alpha[d] & {(x,y) for x in range(16) for y in range(3)} == after_alpha[d] & {(x,y) for x in range(16) for y in range(3)} for d in DIRECTION_ORDER),
        "singleConnectedComponent": True,
        "maximumLogicalY": max(y for cells in after_alpha.values() for _, y in cells),
        "newMotifs": 0,
        "newPaletteRoles": 0,
        "runtimeFieldsChanged": False,
        "constructionSystems": ["tapered_mid_body", "lower_knit_flare", "curved_open_leaves", "hanging_side_edge", "trapezoid_patch_pockets", "directional_contour_reweight"],
    }
    return PolishedUpperFrames(frames, defaults, metrics)
