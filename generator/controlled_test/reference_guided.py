"""Bounded translator for the three-item reference-guided quality proof.

This module is not a fashion generator and not a renderer.  It loads three
human-approved semantic design specifications, selects an existing V5/HD
construction carrier, authors the design-specific regions on that carrier,
then delegates optical polish and semantic color resolution to the proven
pipeline.  Reference artwork is never loaded by this module.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from generator.controlled_test.hd_adapter import (
    MASK_ROLE_BY_VALUE,
    _palette_ramps,
    _permanent_from_base,
    _remove_closed_opening_from_hd_regions,
)
from generator.png_utils import RGBA, TRANSPARENT, blank_image
from generator.renderers.fashionsense.art_polish_v5e import (
    _default_value,
    _mask_value,
    polish_upper_frames,
    soften_shared_rear_neck,
)
from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER
from generator.renderers.fashionsense.upper_v5b import _coverage_missing, _stack, render_fs_v5b
from generator.renderers.fashionsense.upper_v5d import render_fs_v5d
from generator.v5b.engine import generate_v5b_benchmark, validate_v5b_recipe
from generator.v5d.engine import generate_v5d_batch, validate_v5d_recipe


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "specs" / "reference_guided" / "three_garment_quality_proof.json"
PALETTES = ROOT / "specs" / "palettes" / "palette_stories.json"
SUPPORTED = ("HARBORFOLD_CAMP_SHIRT", "ALDERWICK_KNIT_VEST", "BLUECURRENT_SADDLE_SHELL")


@dataclass(frozen=True)
class ReferenceGuidedRender:
    design: dict[str, Any]
    backend_recipe: dict[str, Any]
    backend: str
    stage_trace: tuple[str, ...]
    mask_frames: dict[str, list[list[RGBA]]]
    frames: dict[str, list[list[RGBA]]]
    role_frames: dict[str, list[list[str | None]]]
    texture: list[list[RGBA]]
    sleeve_colors: tuple[tuple[int, int, int], ...]
    fabric_assignments: dict[str, dict[tuple[int, int], str]]
    construction_signals: dict[str, dict[str, frozenset[tuple[int, int]]]]
    coverage_missing: dict[str, tuple[tuple[int, int], ...]]
    polish_metrics: dict[str, Any]
    material_evidence: dict[str, Any]
    construction_metrics: dict[str, Any]


def load_reference_guided_specs() -> list[dict[str, Any]]:
    return json.loads(SPEC.read_text(encoding="utf-8"))["garments"]


def _design(design_id: str) -> dict[str, Any]:
    if design_id not in SUPPORTED:
        raise ValueError(f"reference-guided proof is bounded to {SUPPORTED}; got {design_id}")
    return copy.deepcopy(next(item for item in load_reference_guided_specs() if item["id"] == design_id))


def _palette(story_id: str) -> dict[str, Any]:
    stories = json.loads(PALETTES.read_text(encoding="utf-8"))["stories"]
    return copy.deepcopy(next(item for item in stories if item["id"] == story_id))


def _signals() -> dict[str, dict[str, set[tuple[int, int]]]]:
    systems = ("silhouette", "collar", "opening", "layering", "sleeves", "hem", "panels", "pockets", "seams", "accent")
    return {system: {direction: set() for direction in DIRECTION_ORDER} for system in systems}


def _copy_frames(frames):
    return {direction: [list(row) for row in frames[direction]] for direction in DIRECTION_ORDER}


def _reset_to_proven_hd_planes(base, frames, defaults) -> None:
    """Remove inherited named-garment surface art without replacing HD light.

    The chosen V5 carrier owns alpha/body interaction. Every surviving cell is
    restored from the underlying permanent HD shade field. This keeps the
    proven region/edge/lighting topology while preventing a source V5 recipe's
    pockets, stripe, or motif from leaking into the authored design.
    """
    permanent = _permanent_from_base(base)
    for direction in DIRECTION_ORDER:
        for y in range(16):
            for x in range(16):
                if not frames[direction][y][x][3]:
                    continue
                if permanent.frames[direction][y][x][3]:
                    frames[direction][y][x] = permanent.frames[direction][y][x]
                    defaults[direction][y][x] = permanent.default_frames[direction][y][x]


def _bounds(frame, y: int) -> tuple[int, int] | None:
    xs = [x for x, pixel in enumerate(frame[y]) if pixel[3]]
    return (min(xs), max(xs)) if xs else None


def _paint(base, frames, defaults, signals, fabrics, system, direction, x, y, shade, fabric="PrimaryFabric") -> None:
    if not (0 <= x < 16 and 0 <= y < 16 and frames[direction][y][x][3]):
        return
    frames[direction][y][x] = _mask_value(base, shade)
    defaults[direction][y][x] = _default_value(base, shade)
    signals[system][direction].add((x, y))
    fabrics[direction][(x, y)] = fabric


def _clear(frames, defaults, signals, fabrics, direction, x, y) -> None:
    if not (0 <= x < 16 and 0 <= y < 16):
        return
    frames[direction][y][x] = TRANSPARENT
    defaults[direction][y][x] = TRANSPARENT
    fabrics[direction].pop((x, y), None)
    for system in signals.values():
        system[direction].discard((x, y))


def _hem_band(base, frames, defaults, signals, fabrics, *, fabric="Trim", gathered=False) -> None:
    for direction in DIRECTION_ORDER:
        occupied = [y for y in range(16) if any(pixel[3] for pixel in frames[direction][y])]
        if not occupied:
            continue
        bottom = max(occupied)
        for y in range(max(0, bottom - 1), bottom + 1):
            bounds = _bounds(frames[direction], y)
            if not bounds:
                continue
            lo, hi = bounds
            for x in range(lo + 1, hi):
                if gathered:
                    shade = "DEEP_CREASE" if (x - lo) % 4 == 0 else "SHADOW" if y == bottom else "BASE"
                else:
                    shade = "SHADOW" if y == bottom else "BASE"
                _paint(base, frames, defaults, signals, fabrics, "hem", direction, x, y, shade, fabric)


def _harborfold(base, frames, defaults, signals, fabrics) -> dict[str, Any]:
    # Relax the torso without unsafe length: keep the carrier's full body mass,
    # but give the bottom a rounded shirttail and two side-split recesses.
    alpha_before = {d: {(x, y) for y, row in enumerate(frames[d]) for x, p in enumerate(row) if p[3]} for d in DIRECTION_ORDER}
    for direction in DIRECTION_ORDER:
        for x in (0, 15):
            _clear(frames, defaults, signals, fabrics, direction, x, 15)
        bounds = _bounds(frames[direction], 14)
        if bounds:
            for x in (bounds[0], bounds[1]):
                _paint(base, frames, defaults, signals, fabrics, "silhouette", direction, x, 14, "DEEP_CREASE")

    # Wide camp collar and shallow open neck. The two leaves are broad shapes,
    # never a narrow central V or a borrowed blazer lapel.
    for x, y, shade in (
        (4, 1, "STRUCTURAL_EDGE"), (5, 1, "LIGHT"), (5, 2, "BASE"), (6, 2, "SHADOW"),
        (11, 1, "DEEP_CREASE"), (10, 1, "BASE"), (10, 2, "SHADOW"), (9, 2, "DEEP_CREASE"),
    ):
        _paint(base, frames, defaults, signals, fabrics, "collar", "front", x, y, shade, "SecondaryFabric")
    for x, y in ((7, 1), (8, 1), (7, 2), (8, 2)):
        _paint(base, frames, defaults, signals, fabrics, "layering", "front", x, y, "SHADOW", "SecondaryFabric")
    for y in range(3, 6):
        _paint(base, frames, defaults, signals, fabrics, "opening", "front", 7, y, "DEEP_CREASE", "Trim")
    for y in range(6, 13):
        _paint(base, frames, defaults, signals, fabrics, "opening", "front", 7, y, "SHADOW", "PrimaryFabric")
    for x, y in ((8, 6), (8, 9), (8, 12)):
        _paint(base, frames, defaults, signals, fabrics, "opening", "front", x, y, "BASE", "Trim")

    # One asymmetric pocket with an integrated flap and a tiny functional tab.
    for x in range(3, 7):
        _paint(base, frames, defaults, signals, fabrics, "pockets", "front", x, 7, "STRUCTURAL_EDGE")
    for y in (8, 9, 10):
        for x in range(3, 7):
            shade = "LIGHT" if x == 3 and y == 8 else "SHADOW" if x == 6 or y == 10 else "BASE"
            _paint(base, frames, defaults, signals, fabrics, "pockets", "front", x, y, shade)
    _paint(base, frames, defaults, signals, fabrics, "accent", "front", 3, 8, "BASE", "Accent")

    # Side collar depth, hanging seam and a side split; only the pocket-facing
    # side receives a compressed pocket plane.
    for direction, outer, inner in (("right", 11, 10), ("left", 4, 5)):
        for x, y, shade in ((inner, 1, "LIGHT"), (outer, 1, "STRUCTURAL_EDGE"), (outer, 2, "DEEP_CREASE"), (inner, 2, "BASE")):
            _paint(base, frames, defaults, signals, fabrics, "collar", direction, x, y, shade, "SecondaryFabric")
        for y in range(5, 14):
            _paint(base, frames, defaults, signals, fabrics, "seams", direction, outer, y, "SHADOW" if y < 12 else "DEEP_CREASE")
    for x in range(7, 11):
        _paint(base, frames, defaults, signals, fabrics, "pockets", "right", x, 8, "STRUCTURAL_EDGE")
        _paint(base, frames, defaults, signals, fabrics, "pockets", "right", x, 9, "SHADOW")

    # Rear shirt carrier: collar band, shoulder yoke, and a short center pleat.
    for x in range(5, 11):
        y = 1 if 6 <= x <= 9 else 2
        _paint(base, frames, defaults, signals, fabrics, "collar", "back", x, y, "BASE", "SecondaryFabric")
    for x in range(2, 14):
        y = 3 if 4 <= x <= 11 else 4
        _paint(base, frames, defaults, signals, fabrics, "panels", "back", x, y, "STRUCTURAL_EDGE")
    for y in range(4, 9):
        for x in (7, 8):
            _paint(base, frames, defaults, signals, fabrics, "seams", "back", x, y, "SHADOW" if x == 8 else "LIGHT")
    _hem_band(base, frames, defaults, signals, fabrics, fabric="PrimaryFabric")
    alpha_after = {d: {(x, y) for y, row in enumerate(frames[d]) for x, p in enumerate(row) if p[3]} for d in DIRECTION_ORDER}
    return {"alphaAdded": {d: len(alpha_after[d] - alpha_before[d]) for d in DIRECTION_ORDER}, "alphaRemoved": {d: len(alpha_before[d] - alpha_after[d]) for d in DIRECTION_ORDER}}


def _alderwick(base, frames, defaults, signals, fabrics) -> dict[str, Any]:
    alpha_before = {d: {(x, y) for y, row in enumerate(frames[d]) for x, p in enumerate(row) if p[3]} for d in DIRECTION_ORDER}
    # Deep bound V with a broad woven-shirt reveal. The vest remains closed.
    inner = {(7, 1), (8, 1), (6, 2), (7, 2), (8, 2), (9, 2), (7, 3), (8, 3)}
    for x, y in inner:
        _paint(base, frames, defaults, signals, fabrics, "layering", "front", x, y, "BASE" if y <= 2 else "SHADOW", "SecondaryFabric")
    for x, y in ((4, 1), (11, 1), (5, 2), (10, 2), (6, 3), (9, 3), (7, 4), (8, 4)):
        _paint(base, frames, defaults, signals, fabrics, "collar", "front", x, y, "DEEP_CREASE" if y >= 3 else "BASE", "Trim")
    for x, y in ((6, 1), (9, 1), (7, 2), (8, 2)):
        _paint(base, frames, defaults, signals, fabrics, "layering", "front", x, y, "LIGHT", "SecondaryFabric")

    # Bind the cut-in armholes to make the missing shirt-layer geometry read as
    # intentional sleeveless knit rather than detached/missing arms.
    for direction in DIRECTION_ORDER:
        for y in range(1, 9):
            bounds = _bounds(frames[direction], y)
            if not bounds:
                continue
            lo, hi = bounds
            for x in {lo, hi}:
                _paint(base, frames, defaults, signals, fabrics, "sleeves", direction, x, y, "STRUCTURAL_EDGE" if y >= 4 else "BASE", "Trim")

    # Quiet paired knit ribs—construction, not a graphic motif.
    for direction, rib_columns in (("front", (5, 10)), ("back", (6, 9))):
        for x in rib_columns:
            for y in range(5, 14):
                shade = "LIGHT" if x == rib_columns[0] and y % 3 != 0 else "SHADOW" if x == rib_columns[1] else "BASE"
                _paint(base, frames, defaults, signals, fabrics, "panels", direction, x, y, shade)
    for direction, edge in (("right", 10), ("left", 5)):
        for y in range(4, 13):
            _paint(base, frames, defaults, signals, fabrics, "seams", direction, edge, y, "SHADOW")

    for x in range(5, 11):
        y = 1 if 6 <= x <= 9 else 2
        _paint(base, frames, defaults, signals, fabrics, "collar", "back", x, y, "BASE", "Trim")
    for x in range(3, 13):
        shade = "LIGHT" if x <= 6 else "BASE" if x <= 9 else "SHADOW"
        _paint(base, frames, defaults, signals, fabrics, "panels", "back", x, 4, shade)
    _hem_band(base, frames, defaults, signals, fabrics, fabric="Trim")
    alpha_after = {d: {(x, y) for y, row in enumerate(frames[d]) for x, p in enumerate(row) if p[3]} for d in DIRECTION_ORDER}
    return {"alphaAdded": {d: len(alpha_after[d] - alpha_before[d]) for d in DIRECTION_ORDER}, "alphaRemoved": {d: len(alpha_before[d] - alpha_after[d]) for d in DIRECTION_ORDER}}


def _bluecurrent(base, frames, defaults, signals, fabrics) -> dict[str, Any]:
    alpha_before = {d: {(x, y) for y, row in enumerate(frames[d]) for x, p in enumerate(row) if p[3]} for d in DIRECTION_ORDER}
    # Tall stand collar with a contained half zip.
    for direction in DIRECTION_ORDER:
        for y, xs in ((0, range(6, 10)), (1, range(5, 11)), (2, range(5, 11))):
            for x in xs:
                boundary = x in {min(xs), max(xs)} or y == 0
                _paint(base, frames, defaults, signals, fabrics, "collar", direction, x, y, "DEEP_CREASE" if boundary else "BASE", "Trim")
    for y in range(2, 7):
        _paint(base, frames, defaults, signals, fabrics, "opening", "front", 7, y, "DEEP_CREASE" if y < 5 else "STRUCTURAL_EDGE", "Trim")
    _paint(base, frames, defaults, signals, fabrics, "accent", "front", 8, 5, "BASE", "Accent")

    # Broad curved saddle. It wraps and terminates at the side seam instead of
    # becoming another bright vertical center panel.
    for direction in ("front", "back"):
        for y in range(3, 7):
            inset = max(0, y - 3)
            for x in range(2 + inset, 14 - inset):
                if direction == "front" and x in {7, 8} and y <= 5:
                    continue
                shade = "LIGHT" if x <= 7 and y <= 4 else "BASE" if y <= 5 else "SHADOW"
                _paint(base, frames, defaults, signals, fabrics, "panels", direction, x, y, shade, "SecondaryFabric")
    for direction in ("right", "left"):
        for y in range(3, 7):
            for x in range(4 + (y - 3), 12 - (y - 3)):
                _paint(base, frames, defaults, signals, fabrics, "panels", direction, x, y, "LIGHT" if direction == "left" else "BASE", "SecondaryFabric")

    # Low diagonal pocket entries and side panel carrier.
    for x, y in ((3, 10), (4, 10), (4, 11), (5, 11), (10, 11), (11, 11), (11, 10), (12, 10)):
        _paint(base, frames, defaults, signals, fabrics, "pockets", "front", x, y, "STRUCTURAL_EDGE", "Trim")
    for direction, xs in (("right", range(9, 13)), ("left", range(3, 7))):
        for x in xs:
            _paint(base, frames, defaults, signals, fabrics, "pockets", direction, x, 10, "STRUCTURAL_EDGE", "Trim")
        edge = max(xs) if direction == "right" else min(xs)
        for y in range(7, 14):
            _paint(base, frames, defaults, signals, fabrics, "seams", direction, edge, y, "SHADOW")

    # Rear shaping seams below the saddle remain short and subordinate.
    for x in (5, 10):
        for y in range(7, 11):
            _paint(base, frames, defaults, signals, fabrics, "seams", "back", x, y, "SHADOW")
    _hem_band(base, frames, defaults, signals, fabrics, fabric="Trim", gathered=True)
    alpha_after = {d: {(x, y) for y, row in enumerate(frames[d]) for x, p in enumerate(row) if p[3]} for d in DIRECTION_ORDER}
    return {"alphaAdded": {d: len(alpha_after[d] - alpha_before[d]) for d in DIRECTION_ORDER}, "alphaRemoved": {d: len(alpha_before[d] - alpha_after[d]) for d in DIRECTION_ORDER}}


def _backend(design_id: str):
    v5b = generate_v5b_benchmark()["recipes"]
    if design_id == "HARBORFOLD_CAMP_SHIRT":
        recipe = copy.deepcopy(v5b[1])
        recipe["id"] = "reference-guided-harborfold"
        recipe.update({"articleType": "FITTED_SHIRT", "constructionVariant": "structured_shirt", "sleeveIntent": "FITTED_LONG_SLEEVE", "shoulderIntent": "standard", "necklineIntent": "open", "collarIntent": "shirt_collar", "openingIntent": "buttoned", "layeringIntent": "single_layer"})
        recipe["baseArticleRecipe"]["designRecipe"]["itemName"] = "Harborfold Camp Shirt"
        check = validate_v5b_recipe(recipe)
        if not check.valid:
            raise ValueError("invalid camp-shirt carrier: " + "; ".join(check.errors))
        raw = render_fs_v5b(recipe)
        return recipe, raw, raw, "V5B_STRUCTURED_SHIRT_OVER_HD"
    if design_id == "ALDERWICK_KNIT_VEST":
        recipe = copy.deepcopy(v5b[4])
        recipe["id"] = "reference-guided-alderwick"
        recipe.update({"articleType": "VEST_TOP", "constructionVariant": "waistcoat", "sleeveIntent": "SLEEVELESS", "shoulderIntent": "narrow", "necklineIntent": "v_neck", "collarIntent": "none", "openingIntent": "buttoned", "layeringIntent": "vest_over_inner"})
        recipe["baseArticleRecipe"]["designRecipe"]["itemName"] = "Alderwick Knit Vest"
        check = validate_v5b_recipe(recipe)
        if not check.valid:
            raise ValueError("invalid sweater-vest carrier: " + "; ".join(check.errors))
        raw = render_fs_v5b(recipe)
        return recipe, raw, raw, "V5B_SLEEVELESS_VEST_OVER_HD"
    recipe = copy.deepcopy(generate_v5d_batch()["recipes"][1])
    recipe.update({"id": "v5d-97", "fashionFamily": "JACKET_OUTERWEAR", "articleRole": "WORK_SHIRT", "articleSubtype": "boxy_sport_windbreaker", "fitIntent": "regular", "sleeveIntent": "FITTED_LONG_SLEEVE", "shoulderIntent": "reinforced", "necklineIntent": "high", "collarIntent": "high_collar", "openingIntent": "buttoned", "layeringIntent": "single_layer", "hemIntent": "structured"})
    base_recipe = copy.deepcopy(v5b[8])
    base_recipe.update({"id": "v5b-97", "articleType": "STANDARD_JACKET", "constructionVariant": "utility_jacket", "sleeveIntent": "FITTED_LONG_SLEEVE", "shoulderIntent": "dropped", "necklineIntent": "high", "collarIntent": "high_collar", "layeringIntent": "single_layer", "openingIntent": "center_open"})
    base_recipe["baseArticleRecipe"]["designRecipe"]["itemName"] = "Bluecurrent Saddle Shell"
    recipe["baseUpperRecipe"] = base_recipe
    check = validate_v5d_recipe(recipe)
    if not check.valid:
        raise ValueError("invalid windbreaker carrier: " + "; ".join(check.errors))
    raw = render_fs_v5d(recipe)
    return recipe, raw, raw.base, "V5D_WORK_SHELL_OVER_STANDARD_JACKET_HD"


def _resolve(design, polished, fabrics):
    palette_recipe = {"materialId": design["material"], "paletteStory": _palette(design["paletteStory"])}
    ramps = _palette_ramps(palette_recipe)
    frames = {}; role_frames = {}; counts = {fabric: 0 for fabric in ("PrimaryFabric", "SecondaryFabric", "Trim", "Accent")}
    shade_counts = {shade: 0 for shade in MASK_ROLE_BY_VALUE.values()}
    for direction in DIRECTION_ORDER:
        frame = blank_image(16, 16); roles = [[None] * 16 for _ in range(16)]
        for y, row in enumerate(polished.frames[direction]):
            for x, pixel in enumerate(row):
                if not pixel[3]:
                    continue
                shade = MASK_ROLE_BY_VALUE.get(pixel[0]) if pixel[0] == pixel[1] == pixel[2] else None
                if shade is None:
                    # All named source surface systems were reset. This branch
                    # only catches a fixed V5 carrier cell and maps it back to
                    # the nearest proven shade role before semantic coloring.
                    shade = min(MASK_ROLE_BY_VALUE.values(), key=lambda role: abs(pixel[0] - {v: k for k, v in MASK_ROLE_BY_VALUE.items()}[role]))
                fabric = fabrics[direction].get((x, y), "PrimaryFabric")
                if fabric == "Accent":
                    output_shade = "BASE"
                elif fabric == "Trim":
                    output_shade = "LIGHT" if shade in {"LIGHT", "OPTIONAL_HIGHLIGHT"} else "SHADOW" if shade in {"EXTERIOR_CONTOUR", "DEEP_CREASE", "STRUCTURAL_EDGE", "SHADOW"} else "BASE"
                else:
                    output_shade = shade
                frame[y][x] = ramps[fabric][output_shade]
                roles[y][x] = f"{fabric}.{output_shade}"
                counts[fabric] += 1; shade_counts[shade] += 1
        frames[direction] = frame; role_frames[direction] = roles
    evidence = {"materialId": design["material"], "fabricRoleCells": counts, "shadeRoleCells": shade_counts, "pixelLevelEvidence": sum(shade_counts[s] for s in ("LIGHT", "SHADOW", "STRUCTURAL_EDGE", "DEEP_CREASE")) > 0}
    return frames, role_frames, ramps, evidence


def _connected_components(frame) -> int:
    cells = {(x, y) for y, row in enumerate(frame) for x, pixel in enumerate(row) if pixel[3]}
    components = 0
    while cells:
        components += 1; todo = [cells.pop()]
        while todo:
            x, y = todo.pop()
            for nxt in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if nxt in cells:
                    cells.remove(nxt); todo.append(nxt)
    return components


def render_reference_guided(design_id: str) -> ReferenceGuidedRender:
    design = _design(design_id)
    backend_recipe, raw, base, backend = _backend(design_id)
    source_frames = _copy_frames(raw.frames)
    source_defaults = _copy_frames(raw.default_frames)
    _reset_to_proven_hd_planes(base, source_frames, source_defaults)
    _remove_closed_opening_from_hd_regions(base, source_frames, source_defaults)
    signals = _signals(); fabrics = {direction: {} for direction in DIRECTION_ORDER}
    helper = {"HARBORFOLD_CAMP_SHIRT": _harborfold, "ALDERWICK_KNIT_VEST": _alderwick, "BLUECURRENT_SADDLE_SHELL": _bluecurrent}[design_id]
    construction = helper(base, source_frames, source_defaults, signals, fabrics)
    allow_sleeve_exposure = design_id == "ALDERWICK_KNIT_VEST"
    coverage = _coverage_missing(base, source_frames, allow_sleeve_exposure=allow_sleeve_exposure)
    if any(coverage.values()):
        raise ValueError(f"{design_id} broke proven body coverage: {coverage}")
    polished = polish_upper_frames(base, source_frames, source_defaults, article_family=design["article"])
    protected_back = frozenset(cell for system in signals.values() for cell in system["back"])
    polished = soften_shared_rear_neck(base, polished, protected_cells=protected_back)
    frames, role_frames, ramps, material_evidence = _resolve(design, polished, fabrics)
    sleeve_fabric = "SecondaryFabric" if design_id == "ALDERWICK_KNIT_VEST" else "PrimaryFabric"
    sleeve_ramp = ramps[sleeve_fabric]
    sleeve_colors = tuple(color[:3] for color in (sleeve_ramp["DEEP_CREASE"], sleeve_ramp["BASE"], sleeve_ramp["LIGHT"]))
    components = {direction: _connected_components(frames[direction]) for direction in DIRECTION_ORDER}
    allowed_components = {direction: 1 for direction in DIRECTION_ORDER}
    # A sleeveless VEST_TOP legitimately exposes the native Farmer arm between
    # its front/back knit strap in side view. Both islands remain cells in one
    # anchored Shirt frame; this is not a separately positioned FS component.
    if design_id == "ALDERWICK_KNIT_VEST":
        allowed_components.update({"right": 2, "left": 2})
    if any(components[direction] > allowed_components[direction] for direction in DIRECTION_ORDER):
        raise ValueError(f"{design_id} has unexpected alpha components: {components}")
    construction.update({"connectedComponents": components, "maximumLogicalY": max(y for direction in DIRECTION_ORDER for y, row in enumerate(frames[direction]) if any(pixel[3] for pixel in row)), "referenceArtworkLoaded": False, "customSleeves": False})
    frozen_signals = {system: {direction: frozenset(cells) for direction, cells in views.items()} for system, views in signals.items()}
    trace = ("semantic_reference_guided_spec", "select_existing_V5_carrier", "render_fs_hd_v2", "render_fs_v3_surface", "render_fs_v4", "render_fs_v5b", "render_fs_v5d_if_required", "reset_named_surface_to_proven_hd_planes", f"author_{design_id.lower()}_construction", "polish_upper_frames", "soften_shared_rear_neck", "semantic_palette_material_adapter")
    return ReferenceGuidedRender(design, backend_recipe, backend, trace, polished.frames, frames, role_frames, _stack(frames), sleeve_colors, fabrics, frozen_signals, coverage, polished.metrics, material_evidence, construction)


def render_reference_guided_set() -> list[ReferenceGuidedRender]:
    return [render_reference_guided(design_id) for design_id in SUPPORTED]
