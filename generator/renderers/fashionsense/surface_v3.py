"""Fashion Sense V3 surface-design renderer.

The permanent V2 HD renderer remains the construction/shading authority. This
additive backend applies coordinate-free V3 concepts through renderer-owned
color-block, trim, motif, pattern, and directional-topology grammar.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

from generator.png_utils import RGBA, blank_image
from generator.renderers.fashionsense.hd_garment_v2 import (
    DIRECTION_ORDER,
    FSPermanentGarmentRender,
    render_fs_hd_v2,
)
from generator.v3.engine import load_v3_data, to_v2_base_recipe, validate_recipe_v3


PROTECTED_BASE_ROLES = frozenset({"EXTERIOR_CONTOUR", "DEEP_CREASE"})
SYSTEM_ORDER = ("color_block", "pattern", "trim", "motif")


@dataclass(frozen=True)
class FSV3SurfaceRender:
    recipe: dict[str, Any]
    base: FSPermanentGarmentRender
    surface_roles: dict[str, list[list[str | None]]]
    system_cells: dict[str, dict[str, frozenset[tuple[int, int]]]]
    frames: dict[str, list[list[RGBA]]]
    default_frames: dict[str, list[list[RGBA]]]
    texture: list[list[RGBA]]


@dataclass(frozen=True)
class FSV3Diagnostics:
    passes: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict[str, Any]


def _empty_roles() -> dict[str, list[list[str | None]]]:
    return {direction: [[None for _ in range(16)] for _ in range(16)] for direction in DIRECTION_ORDER}


def _empty_system_cells() -> dict[str, dict[str, set[tuple[int, int]]]]:
    return {system: {direction: set() for direction in DIRECTION_ORDER} for system in SYSTEM_ORDER}


def _dirs(topology: str) -> tuple[str, ...]:
    return {
        "front_only": ("front",),
        "asymmetric_front": ("front", "right"),
        "front_back": ("front", "back"),
        "front_back_pair": ("front", "back"),
        "wrap": DIRECTION_ORDER,
        "shoulder_wrap": DIRECTION_ORDER,
        "construction_bound": DIRECTION_ORDER,
        "upper_only": ("front", "back", "left", "right"),
        "lower_only": DIRECTION_ORDER,
    }.get(topology, ("front",))


def _eligible(base: FSPermanentGarmentRender, direction: str, x: int, y: int, *, dark_trim: bool = False) -> bool:
    if not (0 <= x < 16 and 0 <= y < 16):
        return False
    if base.regions[direction][y][x] is None:
        return False
    return dark_trim or base.roles[direction][y][x] not in PROTECTED_BASE_ROLES


def _put(roles, cells, base, system: str, direction: str, x: int, y: int, role: str, *, dark_trim: bool = False) -> None:
    if _eligible(base, direction, x, y, dark_trim=dark_trim):
        roles[direction][y][x] = role
        cells[system][direction].add((x, y))


def _occupied_bounds(frame, y: int) -> tuple[int, int] | None:
    xs = [x for x, region in enumerate(frame[y]) if region is not None]
    return None if not xs else (min(xs), max(xs))


def _boundary(frame, x: int, y: int, region_names: set[str]) -> bool:
    if frame[y][x] not in region_names:
        return False
    for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
        if not (0 <= nx < 16 and 0 <= ny < 16) or frame[ny][nx] not in region_names:
            return True
    return False


def _apply_color_block(recipe, base, roles, cells) -> None:
    spec = recipe["colorBlocking"]
    kind = spec["type"]
    if kind == "none":
        return
    role = spec["colorRole"]
    for direction in _dirs(spec["topology"]):
        frame = base.regions[direction]
        for y in range(16):
            bounds = _occupied_bounds(frame, y)
            for x in range(16):
                region = frame[y][x]
                if region is None or bounds is None:
                    continue
                chosen = False
                if kind == "shoulder_block":
                    chosen = 2 <= x <= 13 and y <= 2 and region in {"SHOULDER_CAP", "YOKE", "COLLAR", "BODY", "OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT"}
                elif kind == "yoke_block":
                    chosen = y <= 3 and region in {"YOKE", "COLLAR"}
                elif kind == "chest_band":
                    chosen = y in {6, 7}
                elif kind == "vertical_split":
                    chosen = x >= 8 if direction != "left" else x <= 7
                elif kind == "side_panels":
                    if direction == "right":
                        chosen = x >= bounds[1] - 1
                    elif direction == "left":
                        chosen = x <= bounds[0] + 1
                    else:
                        chosen = x == bounds[0] + 1 or x == bounds[1] - 1
                elif kind == "lower_band":
                    chosen = 10 <= y <= 13
                elif kind == "contrast_sleeves":
                    chosen = region == "SLEEVE"
                elif kind == "inner_layer_emphasis":
                    chosen = region == "INNER_LAYER"
                elif kind == "waist_block":
                    chosen = 9 <= y <= 11
                elif kind == "center_panel":
                    x_range = range(7, 9) if direction == "back" else range(5, 11)
                    chosen = x in x_range and 4 <= y <= 12 and region not in {"SLEEVE", "COLLAR"}
                if chosen:
                    _put(roles, cells, base, "color_block", direction, x, y, role)


def _apply_trim(recipe, base, roles, cells) -> None:
    spec = recipe["surfaceDesign"]["trim"]
    kind = spec["type"]
    if kind == "none":
        return
    role = spec["colorRole"]
    for direction in _dirs(spec["topology"]):
        frame = base.regions[direction]
        if kind in {"collar_trim", "piping", "lapel_trim", "seam_emphasis"}:
            target = {
                "collar_trim": {"COLLAR", "NECKLINE"},
                "piping": {"COLLAR", "YOKE", "PLACKET"},
                "lapel_trim": {"COLLAR", "OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT"},
                "seam_emphasis": {"YOKE", "PLACKET", "OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT"},
            }[kind]
            candidates = [(x, y) for y in range(1, 13) for x in range(16) if _boundary(frame, x, y, target)]
            # A trim is a gesture, not a traced region: keep a staggered connected rhythm.
            for index, (x, y) in enumerate(candidates):
                if kind == "lapel_trim" and not (2 <= y <= 9 and 4 <= x <= 11):
                    continue
                if kind == "seam_emphasis" and index % 2:
                    continue
                if _eligible(base, direction, x, y):
                    _put(roles, cells, base, "trim", direction, x, y, role)
                else:
                    # Preserve the dark construction anchor and place the trim
                    # on its inward cloth plane instead of erasing the outline.
                    inward = x + 1 if x < 8 else x - 1
                    _put(roles, cells, base, "trim", direction, inward, y, role)
        elif kind == "cuff_trim":
            sleeve = [(x, y) for y in range(16) for x in range(16) if frame[y][x] == "SLEEVE"]
            if sleeve:
                max_y = max(y for _, y in sleeve)
                for x, y in sleeve:
                    if y == max_y:
                        _put(roles, cells, base, "trim", direction, x, y, role)
        elif kind in {"hem_trim", "decorative_edge_band", "scalloped_trim", "lace_border"}:
            occupied_y = [y for y in range(16) if any(frame[y][x] is not None for x in range(16))]
            y = max(occupied_y) - (1 if kind in {"hem_trim", "decorative_edge_band"} else 2)
            bounds = _occupied_bounds(frame, y)
            if bounds:
                for x in range(bounds[0] + 1, bounds[1]):
                    chosen = kind in {"hem_trim", "decorative_edge_band"}
                    if kind == "scalloped_trim": chosen = (x - bounds[0]) % 3 in {0, 1}
                    if kind == "lace_border": chosen = (x - bounds[0]) % 4 in {0, 1}
                    if chosen: _put(roles, cells, base, "trim", direction, x, y, role)
        elif kind == "double_stripe":
            for y in (8, 10):
                bounds = _occupied_bounds(frame, y)
                if bounds:
                    for x in range(bounds[0] + 1, bounds[1]):
                        _put(roles, cells, base, "trim", direction, x, y, role)


def _pattern_points(kind: str, direction: str) -> list[tuple[int, int]]:
    if kind == "dots":
        return [(x, y) for y in (5, 9) for x in (4, 8, 12)]
    if kind == "stripes":
        return [(x, y) for y in (7, 10) for x in range(3, 13)]
    if kind == "chevrons":
        return [(5, 6), (6, 7), (7, 8), (8, 7), (9, 6), (7, 10), (8, 9), (9, 10)]
    if kind == "diamonds":
        return [(5, 7), (6, 6), (7, 7), (6, 8), (9, 7), (10, 6), (11, 7), (10, 8)]
    if kind == "checks":
        return [(x, y) for x in range(4, 12) for y in range(6, 10) if ((x // 2) + (y // 2)) % 2 == 0]
    if kind == "soft_repeat":
        return [(4, 6), (5, 6), (10, 8), (11, 8), (6, 11), (7, 11)]
    if kind == "military_repeat":
        return [(4, 6), (5, 7), (6, 6), (9, 6), (10, 7), (11, 6)]
    if kind == "themed_band":
        return [(x, 9 + (x % 2)) for x in range(4, 12)]
    return []


def _apply_pattern(recipe, base, roles, cells) -> None:
    spec = recipe["surfaceDesign"]["pattern"]
    if spec["type"] == "none":
        return
    for direction in _dirs(spec["topology"]):
        points = _pattern_points(spec["type"], direction)
        if direction in {"left", "right"}:
            # Side reconstruction keeps only the wrapping phase, not a compressed front pattern.
            points = [(x, y) for x, y in points if 6 <= x <= 10][:5]
        if spec["density"] == "sparse" and spec["type"] != "soft_repeat":
            points = points[::2]
        for x, y in points:
            _put(roles, cells, base, "pattern", direction, x, y, spec["colorRole"])


def _motif_cells(rows: list[str], max_cells: int) -> list[tuple[int, int, str]]:
    points = [(x, y, symbol) for y, row in enumerate(rows) for x, symbol in enumerate(row) if symbol != "."]
    center_x = (len(rows[0]) - 1) / 2
    center_y = (len(rows) - 1) / 2
    priority = {"d": 0, "a": 1, "s": 2, "l": 3}
    # Preserve a motif's vertical silhouette before adding density. A nearest-
    # center truncation can turn a cake, leaf, or creature into one chest dot.
    chosen: set[tuple[int, int, str]] = set()
    for y in sorted({point[1] for point in points}):
        row_points = [point for point in points if point[1] == y]
        row_points.sort(key=lambda p: (abs(p[0] - center_x), priority[p[2]], p[0]))
        chosen.add(row_points[0])
        if len(chosen) >= max_cells:
            break
    remaining = [point for point in points if point not in chosen]
    remaining.sort(key=lambda p: (abs(p[0] - center_x) + abs(p[1] - center_y), priority[p[2]], p[1], p[0]))
    chosen.update(remaining[: max(0, max_cells - len(chosen))])
    return [(x, y, symbol) for y, row in enumerate(rows) for x, symbol in enumerate(row) if (x, y, symbol) in chosen]


def _apply_motif(recipe, base, roles, cells, data) -> None:
    spec = recipe["surfaceDesign"]["motif"]
    family = spec["family"]
    if family == "none":
        return
    rows = data["surfaceGrammar"]["motifs"][family]
    legend = data["surfaceGrammar"]["motifLegend"]
    allowed_roles = set(spec["colorRoles"])
    budget = data["budgets"]["rarities"][recipe["rarity"]]["maximumMotifCellsPerView"]
    points = _motif_cells(rows, budget)
    focal = recipe["concept"]["focalArea"]
    focal_model = data["surfaceGrammar"]["focalAreas"][focal]
    for direction in _dirs(spec["topology"]):
        if direction in {"left", "right"}:
            if spec["topology"] == "asymmetric_front" and direction == "right":
                for x, y, symbol in points[:2]:
                    _put(roles, cells, base, "motif", direction, 9, 6 + y % 2, legend[symbol])
            continue
        use_points = points
        if direction == "back":
            if spec["topology"] != "front_back_pair":
                continue
            use_points = points[:3]
        width = len(rows[0])
        x0 = 8 - width // 2
        if focal == "side_chest": x0 = 4 if recipe["concept"]["symmetryBias"] != "asymmetric" else 9
        if focal == "shoulders": x0 = 3
        top = focal_model["backTop" if direction == "back" else "frontTop"]
        if direction == "front" and recipe["archetype"] == "SAILOR_TOP" and focal in {"upper_chest", "center_chest"}:
            top += 1
        for x, y, symbol in use_points:
            role = legend[symbol]
            if role not in allowed_roles:
                role = "accent" if "accent" in allowed_roles else next(iter(allowed_roles))
            _put(roles, cells, base, "motif", direction, x0 + x, top + y, role)


def _surface_color(recipe: dict[str, Any], role: str, data: dict[str, Any]) -> RGBA:
    story = data["palettes"]["stories"][recipe["paletteStory"]]
    key = {"secondary": "secondary", "accent": "accent", "light_accent": "lightAccent", "dark_accent": "darkAccent"}[role]
    rgb = story[key]
    return rgb[0], rgb[1], rgb[2], 255


def _stack(frames: dict[str, list[list[RGBA]]]) -> list[list[RGBA]]:
    texture = blank_image(16, 64)
    for index, direction in enumerate(DIRECTION_ORDER):
        for y, row in enumerate(frames[direction]):
            texture[index * 16 + y] = list(row)
    return texture


def render_fs_v3(recipe: dict[str, Any]) -> FSV3SurfaceRender:
    data = load_v3_data()
    validation = validate_recipe_v3(recipe, data)
    if not validation.valid:
        raise ValueError("invalid V3 recipe: " + "; ".join(validation.errors))
    base = render_fs_hd_v2(to_v2_base_recipe(recipe))
    roles = _empty_roles()
    cells = _empty_system_cells()
    _apply_color_block(recipe, base, roles, cells)
    _apply_pattern(recipe, base, roles, cells)
    _apply_trim(recipe, base, roles, cells)
    _apply_motif(recipe, base, roles, cells, data)
    frames = {direction: [list(row) for row in base.frames[direction]] for direction in DIRECTION_ORDER}
    defaults = {direction: [list(row) for row in base.default_frames[direction]] for direction in DIRECTION_ORDER}
    for direction in DIRECTION_ORDER:
        for y in range(16):
            for x in range(16):
                role = roles[direction][y][x]
                if role is not None:
                    color = _surface_color(recipe, role, data)
                    frames[direction][y][x] = color
                    defaults[direction][y][x] = color
    frozen_cells = {system: {direction: frozenset(points) for direction, points in views.items()} for system, views in cells.items()}
    return FSV3SurfaceRender(recipe, base, roles, frozen_cells, frames, defaults, _stack(frames))


def _components(points: set[tuple[int, int]]) -> list[int]:
    remaining = set(points); sizes = []
    while remaining:
        queue = deque([remaining.pop()]); size = 0
        while queue:
            x, y = queue.popleft(); size += 1
            for point in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1),
                          (x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1), (x + 1, y + 1)):
                if point in remaining:
                    remaining.remove(point); queue.append(point)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def diagnose_fs_v3(render: FSV3SurfaceRender) -> FSV3Diagnostics:
    data = load_v3_data(); recipe = render.recipe
    budget = data["budgets"]["rarities"][recipe["rarity"]]
    errors: list[str] = []; warnings: list[str] = []
    active = [system for system in SYSTEM_ORDER if any(render.system_cells[system][d] for d in DIRECTION_ORDER)]
    counts = {system: {d: len(render.system_cells[system][d]) for d in DIRECTION_ORDER} for system in SYSTEM_ORDER}
    visible = {d: set().union(*(render.system_cells[s][d] for s in SYSTEM_ORDER)) for d in DIRECTION_ORDER}
    for direction, points in visible.items():
        if len(points) > budget["maximumSurfaceCellsPerView"]:
            errors.append(f"{direction}: surface cell budget exceeded ({len(points)} > {budget['maximumSurfaceCellsPerView']})")
        protected = {(x, y) for y in range(16) for x in range(16) if render.base.roles[direction][y][x] in PROTECTED_BASE_ROLES}
        if points & protected:
            errors.append(f"{direction}: surface design overwrote {len(points & protected)} protected contour/crease cells")
        singleton_count = _components(points).count(1)
        if singleton_count > (2 if recipe["rarity"] == "Common" else 3):
            warnings.append(f"{direction}: {singleton_count} isolated surface cells need visual review")
    for direction, count in counts["motif"].items():
        if count > budget["maximumMotifCellsPerView"]:
            errors.append(f"{direction}: motif budget exceeded")
    for direction, count in counts["pattern"].items():
        if count > budget["maximumPatternCellsPerView"]:
            errors.append(f"{direction}: pattern budget exceeded")
    themed_views = sum(bool(points) for points in visible.values())
    if themed_views < budget["minimumThemedViews"]:
        errors.append(f"only {themed_views} directions retain surface identity; {recipe['rarity']} requires {budget['minimumThemedViews']}")
    primary = data["vocabulary"]["compositionFamilies"][recipe["surfaceDesign"]["compositionType"]]["primary"]
    primary_total = sum(counts[primary].values())
    if primary_total == 0:
        errors.append("primary surface gesture rendered no cells")
    for support in recipe["surfaceDesign"]["supportSystems"]:
        support_total = sum(counts[support].values())
        if support_total == 0:
            errors.append(f"support system {support} rendered no cells")
        visual_weight = {"color_block": 0.12, "trim": 0.20, "pattern": 0.25, "motif": 1.0}
        if support_total * visual_weight[support] > primary_total * visual_weight[primary] * 1.25:
            warnings.append(f"support system {support} may visually compete with primary {primary}")
    # Design-interest guard: count semantic surface regions independent of base shading.
    if len(active) == 1 and sum(len(points) for points in visible.values()) < 4:
        errors.append("design-interest test failed: surface composition collapses without shading")
    # Topological guards.
    for system, spec in (
        ("color_block", recipe["colorBlocking"]),
        ("trim", recipe["surfaceDesign"]["trim"]),
        ("motif", recipe["surfaceDesign"]["motif"]),
        ("pattern", recipe["surfaceDesign"]["pattern"]),
    ):
        if system not in active: continue
        topology = spec["topology"]
        if topology == "wrap" and any(not render.system_cells[system][d] for d in DIRECTION_ORDER):
            errors.append(f"{system}: wrap topology does not survive all directions")
        if topology == "front_only" and any(render.system_cells[system][d] for d in ("back", "left", "right")):
            errors.append(f"{system}: front-only topology leaked into another direction")
        if topology == "front_back_pair" and not render.system_cells[system]["back"]:
            errors.append(f"{system}: paired-back topology has no back cue")
    colors = {render.frames[d][y][x] for d in DIRECTION_ORDER for x, y in visible[d]}
    if len(colors) > budget["maximumDistinctSurfaceColors"]:
        errors.append(f"surface palette uses {len(colors)} colors; budget is {budget['maximumDistinctSurfaceColors']}")
    metrics = {
        "activeSystems": active,
        "primarySystem": primary,
        "systemCells": counts,
        "visibleSurfaceCells": {d: len(points) for d, points in visible.items()},
        "themedViews": themed_views,
        "surfaceColors": len(colors),
        "baseSideTemplate": render.base.side_template,
        "bodyCoverageMissing": {d: list(v) for d, v in render.base.coverage_missing.items()},
        "designInterestWithoutShading": primary_total >= 4,
    }
    return FSV3Diagnostics(not errors, tuple(errors), tuple(warnings), metrics)
