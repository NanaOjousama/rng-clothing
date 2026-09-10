"""Guardrail diagnostics for permanent Fashion Sense HD garment renders."""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from typing import Any


DARK_ANCHORS = {
    "neck_anchor",
    "outer_side_anchor",
    "underarm_anchor",
    "overlap_anchor",
    "hem_corner_anchor",
}
LINE_ROLES = {"EXTERIOR_CONTOUR", "DEEP_CREASE", "STRUCTURAL_EDGE", "SHADOW"}
LIGHT_ROLES = {"LIGHT", "OPTIONAL_HIGHLIGHT"}


@dataclass(frozen=True)
class FSHDQualityDiagnostics:
    passes: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict[str, Any]


def _neighbors(x: int, y: int):
    for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
        if 0 <= nx < 16 and 0 <= ny < 16:
            yield nx, ny


def _is_exterior(frame, x: int, y: int) -> bool:
    return (
        x == 0
        or x == 15
        or y == 0
        or y == 15
        or any(frame[ny][nx] is None for nx, ny in _neighbors(x, y))
    )


def _components(points: set[tuple[int, int]]) -> list[int]:
    remaining = set(points)
    sizes = []
    while remaining:
        queue = deque([remaining.pop()])
        size = 0
        while queue:
            x, y = queue.popleft()
            size += 1
            for neighbor in _neighbors(x, y):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def _boundary(frame, x: int, y: int) -> bool:
    region = frame[y][x]
    return any(frame[ny][nx] not in {None, region} for nx, ny in _neighbors(x, y))


def _side_required_regions(archetype: str, recipe: dict[str, Any]) -> set[str]:
    if archetype == "JACKET":
        return {"COLLAR", "INNER_LAYER", "SLEEVE"}
    if archetype == "BUTTON_SHIRT":
        required = {"COLLAR", "PLACKET", "SLEEVE"}
        if recipe["construction"]["panelLayout"] == "yoke":
            required.add("YOKE")
        return required
    if archetype == "SAILOR_TOP":
        return {"YOKE", "SLEEVE"}
    if archetype == "SWEATER":
        return {"NECKLINE", "SLEEVE", "RIBBING" if recipe["construction"]["hem"] == "ribbed" else "HEM"}
    return set()


def diagnose_fs_hd_render(render) -> FSHDQualityDiagnostics:
    errors: list[str] = []
    warnings: list[str] = []
    direction_metrics: dict[str, Any] = {}
    maximum_contour = render.config["edgePolicy"]["maximumDarkestExteriorShare"]
    minimum_anchor = render.config["edgePolicy"]["minimumDarkAnchorExteriorShare"]

    for direction in ("front", "right", "left", "back"):
        regions = render.regions[direction]
        roles = render.roles[direction]
        exposure = render.edge_exposure[direction]
        occupied = {
            (x, y)
            for y, row in enumerate(regions)
            for x, region in enumerate(row)
            if region is not None
        }
        components = _components(occupied)
        if components != [len(occupied)]:
            errors.append(f"{direction}: garment occupancy is disconnected {components}")

        exterior = {(x, y) for x, y in occupied if _is_exterior(regions, x, y)}
        darkest = {(x, y) for x, y in exterior if roles[y][x] == "EXTERIOR_CONTOUR"}
        anchor_cells = {
            (x, y)
            for y, row in enumerate(exposure)
            for x, edge in enumerate(row)
            if edge in DARK_ANCHORS
        }
        anchored = {
            (x, y)
            for x, y in anchor_cells
            if roles[y][x] in {"EXTERIOR_CONTOUR", "DEEP_CREASE", "SECONDARY_SHADOW"}
        }
        darkest_share = len(darkest) / max(1, len(exterior))
        anchor_share = len(anchored) / max(1, len(anchor_cells))
        if darkest_share >= 0.999:
            errors.append(f"{direction}: 100% darkest exterior contour collapse")
        elif darkest_share > maximum_contour:
            errors.append(f"{direction}: darkest exterior share {darkest_share:.3f} exceeds {maximum_contour:.3f}")
        if anchor_share < minimum_anchor:
            errors.append(f"{direction}: dark-anchor coverage {anchor_share:.3f} below {minimum_anchor:.3f}")

        highlights = {
            (x, y)
            for y, row in enumerate(roles)
            for x, role in enumerate(row)
            if role == "OPTIONAL_HIGHLIGHT"
        }
        highlight_components = _components(highlights)
        if len(highlight_components) > render.config["lightPolicy"]["maximumHighlightClustersPerDirection"]:
            errors.append(f"{direction}: too many highlight clusters {highlight_components}")
        if len(highlights) > render.config["lightPolicy"]["maximumHighlightCellsPerDirection"]:
            errors.append(f"{direction}: highlight cell budget exceeded")
        for x, y in highlights:
            if not any(roles[ny][nx] == "LIGHT" for nx, ny in _neighbors(x, y)):
                errors.append(f"{direction}: highlight at {(x, y)} is detached from light plane")

        left_light = sum(
            roles[y][x] in LIGHT_ROLES for y in range(16) for x in range(0, 8)
        )
        right_light = sum(
            roles[y][x] in LIGHT_ROLES for y in range(16) for x in range(8, 16)
        )
        if direction in {"front", "back"} and left_light == right_light and left_light + right_light >= 4:
            errors.append(f"{direction}: symmetric-lighting collapse ({left_light}:{right_light})")

        hierarchy = render.gesture_hierarchy[direction]
        gesture_strength = {}
        weights = {
            "EXTERIOR_CONTOUR": 5,
            "DEEP_CREASE": 4,
            "STRUCTURAL_EDGE": 3,
            "SECONDARY_SHADOW": 3,
            "SHADOW": 2,
            "LIGHT": 1,
            "OPTIONAL_HIGHLIGHT": 1,
        }
        for strength in ("PRIMARY", "SECONDARY", "SUBORDINATE"):
            region_names = set(hierarchy[strength])
            gesture_strength[strength] = sum(
                weights.get(roles[y][x], 0)
                for y, row in enumerate(regions)
                for x, region in enumerate(row)
                if region in region_names and _boundary(regions, x, y) and not _is_exterior(regions, x, y)
            )
        if gesture_strength["PRIMARY"] == 0:
            warnings.append(f"{direction}: primary construction gesture has no internal contrast cells")
        if gesture_strength["SECONDARY"] > gesture_strength["PRIMARY"] * 1.25 and gesture_strength["PRIMARY"]:
            errors.append(f"{direction}: secondary construction competes with primary {gesture_strength}")

        lower_bar_rows = []
        allow_band = render.recipe["construction"]["hem"] in {"contrast_band", "ribbed"}
        for y in range(12, 16):
            row_cells = [(x, roles[y][x]) for x, region in enumerate(regions[y]) if region is not None]
            if row_cells:
                dark_share = sum(role in LINE_ROLES or role == "SECONDARY_SHADOW" for _, role in row_cells) / len(row_cells)
                if dark_share >= 0.8:
                    lower_bar_rows.append((y, round(dark_share, 3)))
        if lower_bar_rows and not allow_band:
            errors.append(f"{direction}: accidental full-width lower shadow bar {lower_bar_rows}")

        side_regions = {region for row in regions for region in row if region}
        if direction in {"left", "right"}:
            missing_side = _side_required_regions(render.recipe["archetype"], render.recipe) - side_regions
            if missing_side:
                errors.append(f"{direction}: side template loses semantic regions {sorted(missing_side)}")

        sleeve = {(x, y) for x, y in occupied if regions[y][x] == "SLEEVE"}
        sleeve_junction = any(
            regions[ny][nx] not in {None, "SLEEVE"}
            for x, y in sleeve
            for nx, ny in _neighbors(x, y)
        )
        if not sleeve or not sleeve_junction:
            errors.append(f"{direction}: sleeve/body junction is absent")

        role_counts = Counter(role for row in roles for role in row if role)
        direction_metrics[direction] = {
            "occupiedPixels": len(occupied),
            "connectedComponents": components,
            "exteriorPixels": len(exterior),
            "darkestExteriorPixels": len(darkest),
            "darkestExteriorShare": round(darkest_share, 4),
            "darkAnchorCells": len(anchor_cells),
            "darkAnchorCoverageShare": round(anchor_share, 4),
            "leftLightCells": left_light,
            "rightLightCells": right_light,
            "highlightClusterSizes": highlight_components,
            "gestureStrength": gesture_strength,
            "lowerBarRows": lower_bar_rows,
            "roleCounts": dict(role_counts),
        }

    if any(render.coverage_missing.values()):
        errors.append(f"body coverage missing: {render.coverage_missing}")
    if not all(render.regions["front"][0][x] is None for x in range(6, 10)):
        errors.append("front neck opening is not preserved")

    actual_main_roles = {
        role
        for frame in render.roles.values()
        for row in frame
        for role in row
        if role in render.config["outerMaskRamp"]
    }
    declared = set(render.active_main_roles)
    if actual_main_roles != declared:
        errors.append(f"active shade-role declaration drift: {sorted(declared)} vs {sorted(actual_main_roles)}")

    metrics = {
        "archetype": render.recipe["archetype"],
        "recipeId": render.recipe["id"],
        "sideTemplate": render.side_template,
        "activeMainRoles": list(render.active_main_roles),
        "activeMainRoleCount": len(render.active_main_roles),
        "directions": direction_metrics,
    }
    return FSHDQualityDiagnostics(not errors, tuple(errors), tuple(warnings), metrics)
