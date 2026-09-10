"""Vanilla-disciplined V5C2 upper garment and Hoodie renderer.

The renderer is additive over V5B: it preserves the proven Scale-2 shirt,
body-position, body-coverage, and full-motion sleeves contracts. It removes the
previous random surface pass and reconstructs each article with reusable
article signals, semantic surface programs, and direct 16x16 logical pixels.
Reference images and vanilla assets are never read by this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from generator.png_utils import RGBA, TRANSPARENT, blank_image
from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER
from generator.renderers.fashionsense.upper_v5b import (
    FSV5BUpperRender,
    _coverage_missing,
    _default_value,
    _mask_value,
    _stack,
    _story,
    render_fs_v5b,
)
from generator.v5c2.engine import load_v5c2_data, validate_v5c2_recipe


@dataclass(frozen=True)
class FSV5C2UpperRender:
    recipe: dict[str, Any]
    base: FSV5BUpperRender
    frames: dict[str, list[list[RGBA]]]
    default_frames: dict[str, list[list[RGBA]]]
    texture: list[list[RGBA]]
    signal_cells: dict[str, dict[str, frozenset[tuple[int, int]]]]
    removed_cells: dict[str, frozenset[tuple[int, int]]]
    coverage_missing: dict[str, tuple[tuple[int, int], ...]]
    sleeve_colors: tuple[tuple[int, int, int], ...]
    hide_native_sleeves: bool
    companion_required: bool
    sleeves_texture: list[list[RGBA]] | None
    sleeves_json: dict[str, Any] | None
    sleeve_idle_frames: dict[str, list[list[RGBA]]] | None
    sleeve_metrics: dict[str, Any]


SIGNAL_NAMES = ("silhouette", "construction", "opening", "pocket", "trim", "pattern", "motif", "hood")


def _signals():
    return {name: {direction: set() for direction in DIRECTION_ORDER} for name in SIGNAL_NAMES}


def _bounds(frame: list[list[RGBA]], y: int) -> tuple[int, int] | None:
    xs = [x for x, pixel in enumerate(frame[y]) if pixel[3]]
    return None if not xs else (min(xs), max(xs))


def _fixed(render: FSV5BUpperRender, role: str) -> RGBA:
    story = _story(render)
    key = {
        "secondary": "secondary",
        "accent": "accent",
        "light_accent": "lightAccent",
        "dark_accent": "darkAccent",
    }[role]
    return tuple(story[key]) + (255,)


def _put_mask(render, frames, defaults, signals, system, direction, x, y, role):
    if 0 <= x < 16 and 0 <= y < 16 and frames[direction][y][x][3]:
        frames[direction][y][x] = _mask_value(render, role)
        defaults[direction][y][x] = _default_value(render, role)
        signals[system][direction].add((x, y))


def _put_fixed(render, frames, defaults, signals, system, direction, x, y, role):
    if 0 <= x < 16 and 0 <= y < 16 and frames[direction][y][x][3]:
        color = _fixed(render, role)
        frames[direction][y][x] = color
        defaults[direction][y][x] = color
        signals[system][direction].add((x, y))


def _clear(frames, defaults, signals, removed, direction, x, y):
    if 0 <= x < 16 and 0 <= y < 16 and frames[direction][y][x][3]:
        frames[direction][y][x] = TRANSPARENT
        defaults[direction][y][x] = TRANSPARENT
        signals["silhouette"][direction].add((x, y))
        removed[direction].add((x, y))


def _reset_v3_surface(base: FSV5BUpperRender, frames, defaults) -> None:
    design = base.base.design
    permanent = design.base
    translated = base.base.translated_material_cells
    for system_views in design.system_cells.values():
        for direction, cells in system_views.items():
            for x, y in cells:
                if not frames[direction][y][x][3]:
                    continue
                if (x, y) in base.modified_cells[direction] or (x, y) in translated[direction]:
                    continue
                frames[direction][y][x] = permanent.frames[direction][y][x]
                defaults[direction][y][x] = permanent.default_frames[direction][y][x]


def _shape_silhouette(recipe, frames, defaults, signals, removed) -> None:
    article = recipe["articleType"]
    fit = recipe["fitIntent"]
    for direction in DIRECTION_ORDER:
        if article == "CROPPED_JACKET":
            for y in range(13, 16):
                for x in range(16):
                    _clear(frames, defaults, signals, removed, direction, x, y)
        elif article == "HOODIE" and fit == "cropped":
            for y in range(13, 16):
                for x in range(16):
                    _clear(frames, defaults, signals, removed, direction, x, y)
        elif article in {"VEST_TOP", "BLOUSE"} or fit == "fitted":
            for y in range(10, 16):
                bounds = _bounds(frames[direction], y)
                if bounds and bounds[1] - bounds[0] >= 10:
                    for x in {bounds[0], bounds[1]}:
                        _clear(frames, defaults, signals, removed, direction, x, y)
        # Baggy intentionally preserves the proven heavy sweater mass. The
        # dropped shoulder and broad ribbing provide the silhouette signal.


def _article_regions(render: FSV5BUpperRender):
    return render.base.design.base.regions


def _waistcoat(render, frames, defaults, signals) -> None:
    # A high-value inner shirt makes the vest an outer layer. The V descends
    # only four rows, then a narrow placket takes over.
    for x, y in ((5, 1), (10, 1), (6, 2), (9, 2), (7, 3), (8, 3)):
        _put_fixed(render, frames, defaults, signals, "construction", "front", x, y, "light_accent")
    for x, y in ((4, 1), (11, 1), (5, 2), (10, 2), (6, 3), (9, 3), (7, 4), (8, 4)):
        _put_mask(render, frames, defaults, signals, "opening", "front", x, y, "DEEP_CREASE")
    for y in range(5, 14):
        _put_mask(render, frames, defaults, signals, "opening", "front", 7, y, "STRUCTURAL_EDGE")
    for y in (7, 10, 13):
        _put_fixed(render, frames, defaults, signals, "trim", "front", 8, y, "accent")
    # Quiet broad back-neck cue; no fake center opening.
    for y, xs in ((1, range(5, 11)), (2, range(6, 10))):
        for x in xs:
            _put_fixed(render, frames, defaults, signals, "construction", "back", x, y, "secondary")
    for direction in ("right", "left"):
        edge = ((8, 2), (9, 3), (10, 4), (10, 5)) if direction == "right" else ((7, 2), (6, 3), (5, 4), (5, 5))
        for x, y in edge:
            _put_mask(render, frames, defaults, signals, "opening", direction, x, y, "STRUCTURAL_EDGE")


def _blouse(render, frames, defaults, signals) -> None:
    # Rounded collar/yoke uses a broad area; the bow is a subordinate cluster.
    for x, y in ((4, 1), (5, 1), (10, 1), (11, 1), (5, 2), (6, 2), (9, 2), (10, 2), (6, 3), (9, 3)):
        _put_fixed(render, frames, defaults, signals, "construction", "front", x, y, "light_accent")
    for x, y in ((4, 2), (11, 2), (5, 3), (10, 3)):
        _put_fixed(render, frames, defaults, signals, "construction", "front", x, y, "secondary")
    for direction in ("right", "left"):
        for x, y in ((6, 1), (7, 1), (7, 2), (8, 2), (8, 3)):
            xx = x if direction == "right" else 15 - x
            _put_fixed(render, frames, defaults, signals, "construction", direction, xx, y, "secondary")
    for y, span in ((1, range(4, 12)), (2, range(5, 11)), (3, range(6, 10))):
        for x in span:
            _put_fixed(render, frames, defaults, signals, "construction", "back", x, y, "secondary")
    # Two small attached waist folds avoid a full horizontal belt.
    for x, y in ((4, 11), (5, 12), (10, 12), (11, 11)):
        _put_mask(render, frames, defaults, signals, "trim", "front", x, y, "SHADOW")


def _ribbed_hem(render, frames, defaults, signals, *, cropped: bool = False) -> None:
    for direction in DIRECTION_ORDER:
        occupied_rows = [y for y in range(16) if any(pixel[3] for pixel in frames[direction][y])]
        if not occupied_rows:
            continue
        bottom = max(occupied_rows)
        rows = [bottom] if cropped else [max(0, bottom - 1), bottom]
        for y in rows:
            bounds = _bounds(frames[direction], y)
            if not bounds:
                continue
            for x in range(bounds[0], bounds[1] + 1):
                role = "STRUCTURAL_EDGE" if y < bottom and (x - bounds[0]) % 4 in {0, 1} else "SHADOW" if x in {bounds[0], bounds[1]} else "BASE"
                _put_mask(render, frames, defaults, signals, "trim", direction, x, y, role)


def _sweater(render, frames, defaults, signals) -> None:
    for direction in DIRECTION_ORDER:
        for y in range(0, 3):
            for x in range(5, 11):
                if (x + y) % 3:
                    _put_fixed(render, frames, defaults, signals, "construction", direction, x, y, "secondary")
    _ribbed_hem(render, frames, defaults, signals)


def _jacket(render, frames, defaults, signals, *, cropped: bool) -> None:
    # Front outer-shell opening and lapels: two diagonals meet a visible inner
    # layer without becoming a full-height decorative stripe.
    for x, y in ((5, 1), (10, 1), (6, 2), (9, 2), (6, 3), (9, 3), (7, 4), (8, 4), (7, 5), (8, 5)):
        _put_mask(render, frames, defaults, signals, "opening", "front", x, y, "DEEP_CREASE")
    for y in range(3, 12 if cropped else 14):
        for x in (7, 8):
            _put_fixed(render, frames, defaults, signals, "construction", "front", x, y, "secondary")
    # Paired pocket tabs are compact connected rectangles, not isolated dots.
    pocket_y = 8 if cropped else 9
    for start in (3, 10):
        for x in range(start, start + 3):
            _put_mask(render, frames, defaults, signals, "pocket", "front", x, pocket_y, "STRUCTURAL_EDGE")
            _put_fixed(render, frames, defaults, signals, "pocket", "front", x, pocket_y + 1, "light_accent")
    # Back chooses one dominant yoke. It terminates before the outer contour.
    for x in range(3, 13):
        y = 3 if x in range(5, 11) else 2
        _put_mask(render, frames, defaults, signals, "construction", "back", x, y, "STRUCTURAL_EDGE")
    for direction in ("right", "left"):
        diagonal = ((7, 1), (8, 2), (9, 3), (9, 4), (10, 5))
        for x, y in diagonal:
            xx = x if direction == "right" else 15 - x
            _put_mask(render, frames, defaults, signals, "opening", direction, xx, y, "DEEP_CREASE")
        for x in range(7, 10):
            xx = x if direction == "right" else 15 - x
            _put_mask(render, frames, defaults, signals, "pocket", direction, xx, pocket_y, "STRUCTURAL_EDGE")
    # A cropped jacket ends with a compact waist; the standard field jacket
    # gets a two-corner structured hem, not a broad dark bar.
    for direction in DIRECTION_ORDER:
        occupied_rows = [y for y in range(16) if any(p[3] for p in frames[direction][y])]
        bottom = max(occupied_rows)
        bounds = _bounds(frames[direction], bottom)
        if bounds:
            for x in (bounds[0], bounds[0] + 1, bounds[1] - 1, bounds[1]):
                _put_mask(render, frames, defaults, signals, "trim", direction, x, bottom, "SHADOW")


def _hood(render, frames, defaults, signals, recipe) -> None:
    contrast = recipe["hoodIntent"]["lining"] == "contrast"
    interior_role = "secondary" if contrast else "dark_accent"
    # Front hood ring preserves an intentional central face/neck opening.
    for x, y in ((4, 0), (5, 0), (10, 0), (11, 0), (3, 1), (4, 1), (11, 1), (12, 1), (4, 2), (5, 2), (10, 2), (11, 2), (5, 3), (10, 3)):
        _put_fixed(render, frames, defaults, signals, "hood", "front", x, y, interior_role)
    for x, y in ((3, 0), (12, 0), (2, 1), (13, 1), (3, 2), (12, 2), (4, 3), (11, 3)):
        _put_mask(render, frames, defaults, signals, "hood", "front", x, y, "DEEP_CREASE")
    # Back hood is a broad nested mass, immediately separating a hoodie from a
    # sweater even when no strings or front motif are visible.
    back_rows = ((0, range(4, 12)), (1, range(3, 13)), (2, range(4, 12)), (3, range(5, 11)), (4, range(6, 10)))
    for y, xs in back_rows:
        for x in xs:
            boundary = x in {min(xs), max(xs)} or y == 0
            if boundary:
                _put_mask(render, frames, defaults, signals, "hood", "back", x, y, "DEEP_CREASE")
            else:
                _put_fixed(render, frames, defaults, signals, "hood", "back", x, y, interior_role)
    for direction in ("right", "left"):
        for y, xs in ((0, range(4, 10)), (1, range(3, 11)), (2, range(4, 11)), (3, range(5, 11)), (4, range(6, 10))):
            for x in xs:
                xx = x if direction == "right" else 15 - x
                if x in {min(xs), max(xs)}:
                    _put_mask(render, frames, defaults, signals, "hood", direction, xx, y, "DEEP_CREASE")
                else:
                    _put_fixed(render, frames, defaults, signals, "hood", direction, xx, y, interior_role)
    if recipe["hoodIntent"]["drawstrings"]:
        for x in (6, 9):
            for y in range(3, 6):
                _put_fixed(render, frames, defaults, signals, "trim", "front", x, y, "light_accent")
            _put_fixed(render, frames, defaults, signals, "trim", "front", x, 6, "accent")


def _zip(render, frames, defaults, signals) -> None:
    for y in range(4, 15):
        _put_mask(render, frames, defaults, signals, "opening", "front", 7, y, "DEEP_CREASE")
        _put_fixed(render, frames, defaults, signals, "opening", "front", 8, y, "light_accent" if y % 3 == 1 else "secondary")
    for direction in ("right", "left"):
        x = 10 if direction == "right" else 5
        for y in range(5, 13):
            _put_mask(render, frames, defaults, signals, "opening", direction, x, y, "STRUCTURAL_EDGE")


def _pouch(render, frames, defaults, signals) -> None:
    for x in range(5, 11):
        _put_mask(render, frames, defaults, signals, "pocket", "front", x, 9, "STRUCTURAL_EDGE")
        _put_fixed(render, frames, defaults, signals, "pocket", "front", x, 12, "secondary")
    for y in range(10, 12):
        for x in (4, 11):
            _put_mask(render, frames, defaults, signals, "pocket", "front", x, y, "DEEP_CREASE")
        for x in range(5, 11):
            _put_fixed(render, frames, defaults, signals, "pocket", "front", x, y, "secondary")
    for direction in ("right", "left"):
        cells = ((8, 9), (9, 9), (9, 10), (9, 11))
        for x, y in cells:
            xx = x if direction == "right" else 15 - x
            _put_mask(render, frames, defaults, signals, "pocket", direction, xx, y, "STRUCTURAL_EDGE")


def _pattern(render, frames, defaults, signals, pattern: str) -> None:
    if pattern == "none":
        return
    if pattern == "knit_yoke":
        for direction in DIRECTION_ORDER:
            for y in (4, 5, 6):
                bounds = _bounds(frames[direction], y)
                if not bounds:
                    continue
                for x in range(bounds[0] + 2, bounds[1] - 1):
                    if (x + y) % 4 in {0, 1}:
                        _put_fixed(render, frames, defaults, signals, "pattern", direction, x, y, "secondary")
    elif pattern == "shoulder_panel":
        for direction in DIRECTION_ORDER:
            for x in range(4, 12):
                _put_fixed(render, frames, defaults, signals, "pattern", direction, x, 4, "secondary")
    elif pattern == "windowpane":
        for direction in ("front", "back"):
            for y in (6, 10):
                for x in range(4, 12, 2):
                    _put_fixed(render, frames, defaults, signals, "pattern", direction, x, y, "secondary")
    elif pattern == "tonal_repeat":
        for direction in ("front", "back"):
            for x, y in ((4, 6), (11, 6), (5, 11), (10, 11)):
                _put_fixed(render, frames, defaults, signals, "pattern", direction, x, y, "secondary")


def _motif(render, frames, defaults, signals, recipe) -> None:
    name = recipe["surfacePlan"]["motif"]
    if name == "none":
        return
    grammar = load_v5c2_data()["grammar"]
    rows = grammar["motifs"][name]
    legend = grammar["motifLegend"]
    width = max(len(row) for row in rows)
    height = len(rows)
    focal = recipe["surfacePlan"]["focalArea"]
    if focal == "side_chest":
        # Keep the complete small cluster inside the cloth mass; the older
        # x=9 placement clipped the far wing and collapsed it into an L mark.
        x0, y0 = 8, 5
    elif focal in {"upper_chest", "yoke"}:
        x0, y0 = 8 - width // 2, 4
    elif focal == "pocket":
        x0, y0 = 8 - width // 2, 8
    else:
        x0, y0 = 8 - width // 2, 5
    points = []
    for y, row in enumerate(rows):
        for x, symbol in enumerate(row):
            role = legend.get(symbol)
            if role:
                points.append((x0 + x, y0 + y, role))
    for x, y, role in points:
        _put_fixed(render, frames, defaults, signals, "motif", "front", x, y, role)
    topology = recipe["surfacePlan"]["topology"]
    if topology == "front_back_pair":
        # The back cue is a reduced relative mark, not a copied front emblem.
        for index, (x, y, role) in enumerate(points):
            if index % 3 == 0:
                bx = 8 + (x - (x0 + width // 2)) // 2
                by = 6 + (y - y0) // 2
                _put_fixed(render, frames, defaults, signals, "motif", "back", bx, by, role)
    elif topology == "asymmetric_front":
        for x, y, role in points[:2]:
            _put_fixed(render, frames, defaults, signals, "motif", "right", 9, 6 + (y - y0) // 2, role)


def _apply_surface_plan(render, frames, defaults, signals, recipe) -> None:
    _pattern(render, frames, defaults, signals, recipe["surfacePlan"]["pattern"])
    _motif(render, frames, defaults, signals, recipe)


def _freeze_signals(signals):
    return {name: {direction: frozenset(cells) for direction, cells in views.items()} for name, views in signals.items()}


def render_fs_v5c2(recipe: dict[str, Any]) -> FSV5C2UpperRender:
    validation = validate_v5c2_recipe(recipe)
    if not validation.valid:
        raise ValueError("invalid V5C2 recipe: " + "; ".join(validation.errors))
    base = render_fs_v5b(recipe["baseUpperRecipe"])
    frames = {direction: [list(row) for row in base.frames[direction]] for direction in DIRECTION_ORDER}
    defaults = {direction: [list(row) for row in base.default_frames[direction]] for direction in DIRECTION_ORDER}
    signals = _signals()
    removed = {direction: set() for direction in DIRECTION_ORDER}
    _reset_v3_surface(base, frames, defaults)
    _shape_silhouette(recipe, frames, defaults, signals, removed)
    article = recipe["articleType"]
    if article == "VEST_TOP":
        _waistcoat(base, frames, defaults, signals)
    elif article == "BLOUSE":
        _blouse(base, frames, defaults, signals)
    elif article == "SWEATER":
        _sweater(base, frames, defaults, signals)
    elif article == "CROPPED_JACKET":
        _jacket(base, frames, defaults, signals, cropped=True)
    elif article == "STANDARD_JACKET":
        _jacket(base, frames, defaults, signals, cropped=False)
    elif article == "HOODIE":
        _hood(base, frames, defaults, signals, recipe)
        if recipe["openingIntent"] == "zip":
            _zip(base, frames, defaults, signals)
        if "pouch_pocket" in recipe["constructionFeatures"]:
            _pouch(base, frames, defaults, signals)
        _ribbed_hem(base, frames, defaults, signals, cropped=recipe["fitIntent"] == "cropped")
    else:
        raise ValueError(f"unsupported V5C2 article {article}")
    _apply_surface_plan(base, frames, defaults, signals, recipe)
    coverage = _coverage_missing(base, frames, allow_sleeve_exposure=False)
    if any(coverage.values()):
        raise ValueError(f"V5C2 body coverage failed: {coverage}")
    return FSV5C2UpperRender(
        recipe=recipe,
        base=base,
        frames=frames,
        default_frames=defaults,
        texture=_stack(frames),
        signal_cells=_freeze_signals(signals),
        removed_cells={direction: frozenset(cells) for direction, cells in removed.items()},
        coverage_missing=coverage,
        sleeve_colors=base.sleeve_colors,
        hide_native_sleeves=base.hide_native_sleeves,
        companion_required=base.companion_required,
        sleeves_texture=base.sleeves_texture,
        sleeves_json=base.sleeves_json,
        sleeve_idle_frames=base.sleeve_idle_frames,
        sleeve_metrics=base.sleeve_metrics,
    )
