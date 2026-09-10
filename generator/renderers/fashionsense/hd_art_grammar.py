"""Art-grammar treatments for the one Fashion Sense HD jacket POC.

The semantic recipe and runtime contract stay unchanged. This module only
translates renderer-owned structural regions into deliberate edge/shade roles.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from generator.png_utils import RGBA
from generator.renderers.fashionsense.hd_jacket import (
    DIRECTION_ORDER,
    FashionSenseJacketRender,
    build_frames,
    composite_default_frame,
    render_mistral_hd_jacket,
    stack_frames,
    validate_body_coverage,
)
from generator.v2_recipe_engine import load_v2_data


ROOT = Path(__file__).resolve().parents[3]
ART_GRAMMAR_PATH = ROOT / "generator" / "data" / "fashionsense" / "hd_art_grammar.json"

OUTER_REGIONS = {
    "OUTER_PANEL_LEFT",
    "OUTER_PANEL_RIGHT",
    "COLLAR",
    "YOKE",
    "HEM",
    "SLEEVE",
    "SHOULDER_CAP",
}


@dataclass(frozen=True)
class HDArtTreatment:
    name: str
    recipe: dict[str, Any]
    backend_config: dict[str, Any]
    art_config: dict[str, Any]
    regions: dict[str, list[list[str | None]]]
    roles: dict[str, list[list[str | None]]]
    frames: dict[str, list[list[RGBA]]]
    texture: list[list[RGBA]]


def load_hd_art_grammar() -> dict[str, Any]:
    return json.loads(ART_GRAMMAR_PATH.read_text(encoding="utf-8"))


def _neighbors(x: int, y: int, width: int, height: int):
    for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
        if 0 <= nx < width and 0 <= ny < height:
            yield nx, ny
        else:
            yield None


def _is_exterior(frame: list[list[str | None]], x: int, y: int) -> bool:
    height = len(frame)
    width = len(frame[0])
    return any(
        neighbor is None or frame[neighbor[1]][neighbor[0]] is None
        for neighbor in _neighbors(x, y, width, height)
    )


def _adjacent_to_region(
    frame: list[list[str | None]], x: int, y: int, target: str
) -> bool:
    return any(
        neighbor is not None and frame[neighbor[1]][neighbor[0]] == target
        for neighbor in _neighbors(x, y, len(frame[0]), len(frame))
    )


def _bounds(frame: list[list[str | None]], region: str) -> tuple[int, int, int, int]:
    cells = [
        (x, y)
        for y, row in enumerate(frame)
        for x, value in enumerate(row)
        if value == region
    ]
    if not cells:
        raise ValueError(f"missing region {region}")
    return (
        min(x for x, _ in cells),
        min(y for _, y in cells),
        max(x for x, _ in cells),
        max(y for _, y in cells),
    )


def _polished_regions(
    source: dict[str, list[list[str | None]]]
) -> dict[str, list[list[str | None]]]:
    """Refine construction ownership without changing silhouette or recipe.

    The visible inner layer becomes a narrow torso opening with a short reveal
    below the jacket hem, and the two-row hem becomes one authored lower edge.
    """
    regions = copy.deepcopy(source)

    front = regions["front"]
    for y in range(5, 14):
        if front[y][6] == "INNER_LAYER":
            front[y][6] = "OUTER_PANEL_LEFT"
        if front[y][9] == "INNER_LAYER":
            front[y][9] = "OUTER_PANEL_RIGHT"
    for x in range(1, 6):
        if front[14][x] == "HEM":
            front[14][x] = "OUTER_PANEL_LEFT"
    for x in range(10, 15):
        if front[14][x] == "HEM":
            front[14][x] = "OUTER_PANEL_RIGHT"

    right = regions["right"]
    for y in range(5, 14):
        for x in (10, 11):
            if right[y][x] == "INNER_LAYER":
                right[y][x] = "OUTER_PANEL_RIGHT"
    for x in range(4, 10):
        if right[14][x] == "HEM":
            right[14][x] = "OUTER_PANEL_RIGHT"

    back = regions["back"]
    for x in range(1, 8):
        if back[14][x] == "HEM":
            back[14][x] = "OUTER_PANEL_LEFT"
    for x in range(8, 15):
        if back[14][x] == "HEM":
            back[14][x] = "OUTER_PANEL_RIGHT"

    # Derive left from the refined right so construction stays physically
    # mirrored while retaining the direction-specific panel name.
    swaps = {
        "OUTER_PANEL_RIGHT": "OUTER_PANEL_LEFT",
        "OUTER_PANEL_LEFT": "OUTER_PANEL_RIGHT",
    }
    regions["left"] = [
        [swaps.get(region, region) for region in reversed(row)] for row in right
    ]
    return regions


def _base_role(
    frame: list[list[str | None]], direction: str, region: str, x: int, y: int
) -> str:
    if region == "INNER_LAYER":
        min_x, min_y, max_x, _ = _bounds(frame, region)
        if x in {min_x, max_x}:
            return "INNER_SHADOW"
        # A short light cluster identifies the undershirt without turning the
        # entire opening into a bright, flat scarf/stripe.
        if y <= min_y + 1:
            return "INNER_LIGHT"
        return "INNER_BASE"

    min_x, min_y, max_x, max_y = _bounds(frame, region)
    if region == "COLLAR":
        return "LIGHT" if y <= min_y + 1 else "BASE"
    if region == "SHOULDER_CAP":
        return "LIGHT" if y == min_y else "BASE"
    if region == "YOKE":
        return "SHADOW" if y == max_y else "BASE"
    if region == "HEM":
        return "SHADOW" if y == min_y else "BASE"
    if region == "SLEEVE":
        if y >= max_y - 1:
            return "SHADOW"
        if y <= min_y + 2:
            return "LIGHT"
        return "BASE"
    if region in {"OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT"}:
        if y >= max_y - 2:
            return "SHADOW"
        # A connected upper-cloth light mass; no checker/noise pattern.
        inset_x = min_x < x < max_x
        if min_y + 1 <= y <= min_y + 3 and inset_x:
            return "LIGHT"
        return "BASE"
    raise ValueError(f"unsupported art-grammar region {region}")


def _assign_edge_hierarchy(
    regions: dict[str, list[list[str | None]]], *, polished: bool
) -> dict[str, list[list[str | None]]]:
    roles: dict[str, list[list[str | None]]] = {}
    for direction, frame in regions.items():
        role_frame: list[list[str | None]] = []
        for y, row in enumerate(frame):
            role_row: list[str | None] = []
            for x, region in enumerate(row):
                role_row.append(
                    None if region is None else _base_role(frame, direction, region, x, y)
                )
            role_frame.append(role_row)

        # Silhouette wins. This includes the cloth-facing rim of the neck
        # opening, but never outlines every internal cluster.
        for y, row in enumerate(frame):
            for x, region in enumerate(row):
                if region is not None and _is_exterior(frame, x, y):
                    role_frame[y][x] = "EXTERIOR_CONTOUR"

        # Panel overlap / lapel recess. Only the outer panel receives the dark
        # crease; the lighter inner layer remains a separate material.
        for y, row in enumerate(frame):
            for x, region in enumerate(row):
                if (
                    region in {"OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT", "COLLAR"}
                    and _adjacent_to_region(frame, x, y, "INNER_LAYER")
                    and not _is_exterior(frame, x, y)
                ):
                    role_frame[y][x] = "DEEP_CREASE"

        # Interior boundaries use a weaker role and only when they communicate
        # yoke, collar, or hem construction.
        for y, row in enumerate(frame):
            for x, region in enumerate(row):
                if _is_exterior(frame, x, y):
                    continue
                if region == "YOKE" and any(
                    neighbor is not None
                    and frame[neighbor[1]][neighbor[0]] != "YOKE"
                    for neighbor in _neighbors(x, y, len(row), len(frame))
                ):
                    role_frame[y][x] = "STRUCTURAL_EDGE"
                elif region == "HEM" and y == _bounds(frame, "HEM")[1]:
                    role_frame[y][x] = "STRUCTURAL_EDGE"

        if polished:
            _polish_role_clusters(direction, frame, role_frame)
        roles[direction] = role_frame
    return roles


def _set_if_region(
    frame: list[list[str | None]],
    roles: list[list[str | None]],
    cells: tuple[tuple[int, int], ...],
    regions: set[str],
    role: str,
) -> None:
    for x, y in cells:
        if frame[y][x] in regions and not _is_exterior(frame, x, y):
            roles[y][x] = role


def _polish_role_clusters(
    direction: str,
    frame: list[list[str | None]],
    roles: list[list[str | None]],
) -> None:
    """Small authored clusters that clarify construction at gameplay scale."""
    if direction == "front":
        # Paired lapel stair-steps: light face plus dark recessed opening.
        _set_if_region(
            frame, roles, ((4, 2), (5, 2), (10, 2), (11, 2)), {"COLLAR"}, "LIGHT"
        )
        _set_if_region(
            frame, roles, ((5, 3), (5, 4), (10, 3), (10, 4)), {"COLLAR"}, "DEEP_CREASE"
        )
        # Two restrained highlight pairs, attached to the lapel light mass.
        _set_if_region(
            frame,
            roles,
            ((4, 1), (5, 1), (10, 1), (11, 1)),
            {"COLLAR"},
            "OPTIONAL_HIGHLIGHT",
        )
        # Broad, connected upper-panel light blocks; the lower body stays calm.
        _set_if_region(
            frame,
            roles,
            ((3, 4), (4, 4), (3, 5), (4, 5), (11, 4), (12, 4), (11, 5), (12, 5)),
            {"OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT"},
            "LIGHT",
        )
    elif direction == "back":
        # A restrained yoke rim and one pair of cloth catches.
        _set_if_region(
            frame, roles, ((5, 2), (6, 2), (9, 2), (10, 2)), {"YOKE"}, "LIGHT"
        )
        _set_if_region(
            frame,
            roles,
            ((5, 2), (6, 2), (9, 2), (10, 2)),
            {"YOKE"},
            "OPTIONAL_HIGHLIGHT",
        )
    else:
        # Side lapel/opening reads as a descending construction cluster rather
        # than a flat stripe. The mirrored left receives mirrored coordinates.
        if direction == "right":
            light = ((7, 2), (8, 2), (8, 3), (9, 3))
            crease = ((9, 4), (10, 4), (10, 5), (11, 5))
            highlight = ((7, 1), (8, 1))
        else:
            light = tuple((15 - x, y) for x, y in ((7, 2), (8, 2), (8, 3), (9, 3)))
            crease = tuple((15 - x, y) for x, y in ((9, 4), (10, 4), (10, 5), (11, 5)))
            highlight = tuple((15 - x, y) for x, y in ((7, 1), (8, 1)))
        _set_if_region(frame, roles, light, {"COLLAR", "OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT"}, "LIGHT")
        _set_if_region(frame, roles, crease, {"COLLAR", "OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT"}, "DEEP_CREASE")
        _set_if_region(frame, roles, highlight, {"COLLAR"}, "OPTIONAL_HIGHLIGHT")


def _set_role(
    frame: list[list[str | None]],
    roles: list[list[str | None]],
    cells: tuple[tuple[int, int], ...],
    allowed_regions: set[str],
    role: str,
) -> None:
    """Assign an authored role, including deliberate exterior-edge breaks."""
    for x, y in cells:
        if frame[y][x] in allowed_regions:
            roles[y][x] = role


def _benchmark_refine_role_clusters(
    direction: str,
    frame: list[list[str | None]],
    roles: list[list[str | None]],
) -> None:
    """Apply pack-independent quality lessons from the attached benchmarks.

    This is intentionally structural and role-based. No benchmark coordinates,
    palette entries, motifs, or silhouettes are present here.
    """
    # The benchmark shirts normally choose one strong light gesture. Remove C's
    # extra highlight tier before authoring that gesture.
    for y, row in enumerate(roles):
        for x, role in enumerate(row):
            if role == "OPTIONAL_HIGHLIGHT":
                roles[y][x] = "LIGHT"

    panel_regions = {"OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT"}
    all_outer = OUTER_REGIONS

    # Avoid a mechanically full-width lower shadow band. The last occupied row
    # remains a strong contour; only attached lower-corner clusters retain
    # shadow above it.
    for y in range(12, 15):
        for x, region in enumerate(frame[y]):
            if region in panel_regions and not _is_exterior(frame, x, y):
                roles[y][x] = "BASE"

    if direction == "front":
        # Selective contour hierarchy: lit left shoulder, quiet right shoulder,
        # dark neck rims, sides, underarms, and bottom remain as anchors.
        _set_role(frame, roles, ((2, 0), (3, 0), (2, 1)), all_outer, "LIGHT")
        _set_role(frame, roles, ((4, 0), (3, 1)), all_outer, "SHADOW")
        _set_role(frame, roles, ((11, 0), (12, 0), (13, 0), (12, 1)), all_outer, "SHADOW")

        # One asymmetrical cloth-light path replaces equal square patches.
        _set_role(
            frame,
            roles,
            ((2, 3), (3, 3), (3, 4), (4, 4), (4, 5), (3, 5)),
            {"OUTER_PANEL_LEFT", "SLEEVE"},
            "LIGHT",
        )
        _set_role(
            frame,
            roles,
            ((11, 4), (12, 4), (11, 5)),
            {"OUTER_PANEL_RIGHT"},
            "BASE",
        )

        # Lapels use face / seam / recess, not symmetric highlight blocks.
        _set_role(
            frame,
            roles,
            ((4, 1), (4, 2), (5, 2)),
            {"COLLAR"},
            "OPTIONAL_HIGHLIGHT",
        )
        _set_role(frame, roles, ((11, 1), (11, 2)), {"COLLAR"}, "BASE")
        _set_role(frame, roles, ((5, 3), (5, 4), (10, 3), (10, 4)), {"COLLAR"}, "DEEP_CREASE")

        # A pair of attached lower shadows gives the hem weight without a bar.
        _set_role(frame, roles, ((1, 13), (2, 13), (13, 13), (14, 13)), panel_regions, "SHADOW")

    elif direction == "back":
        _set_role(frame, roles, ((2, 0), (3, 0), (4, 0), (2, 1)), all_outer, "LIGHT")
        _set_role(frame, roles, ((11, 0), (12, 0), (13, 0)), all_outer, "SHADOW")

        # The yoke remains the single construction gesture, but its long V is
        # mostly cloth shadow; only the center/ends receive structural anchors.
        for y, row in enumerate(frame):
            for x, region in enumerate(row):
                if region == "YOKE" and roles[y][x] == "STRUCTURAL_EDGE":
                    roles[y][x] = "SHADOW"
        _set_role(
            frame,
            roles,
            ((4, 2), (5, 3), (7, 5), (8, 5), (10, 3), (11, 2)),
            {"YOKE"},
            "STRUCTURAL_EDGE",
        )
        _set_role(frame, roles, ((4, 1), (5, 1), (5, 2), (6, 2)), {"YOKE"}, "LIGHT")
        _set_role(frame, roles, ((1, 13), (2, 13), (13, 13), (14, 13)), panel_regions, "SHADOW")

    else:
        right = direction == "right"
        mirror = (lambda cells: cells) if right else (lambda cells: tuple((15 - x, y) for x, y in cells))
        side_panel = {"OUTER_PANEL_RIGHT"} if right else {"OUTER_PANEL_LEFT"}

        _set_role(frame, roles, mirror(((2, 0), (3, 0), (2, 1))), all_outer, "LIGHT")
        _set_role(frame, roles, mirror(((4, 0), (5, 0), (6, 0))), all_outer, "SHADOW")
        _set_role(frame, roles, mirror(((10, 0), (11, 0))), all_outer, "SHADOW")

        # One descending lapel rhythm; opening recess remains darker than the
        # panel but the inner cloth is not traced by a second black outline.
        _set_role(frame, roles, mirror(((6, 2), (7, 2), (7, 3))), {"COLLAR"} | side_panel, "OPTIONAL_HIGHLIGHT")
        _set_role(frame, roles, mirror(((8, 3),)), {"COLLAR"} | side_panel, "LIGHT")
        _set_role(frame, roles, mirror(((8, 4), (9, 4), (9, 5), (10, 5))), {"COLLAR"} | side_panel, "DEEP_CREASE")
        _set_role(frame, roles, mirror(((4, 13), (5, 13), (8, 13), (9, 13))), side_panel, "SHADOW")

    # A one-cell deep crease immediately inside selected long exterior runs
    # restores Stardew optical weight at Scale 2 without a uniform 2-cell ring.
    for y in range(5, 12):
        occupied_x = [x for x, region in enumerate(frame[y]) if region is not None]
        if len(occupied_x) < 4:
            continue
        for x in (min(occupied_x) + 1, max(occupied_x) - 1):
            if frame[y][x] in all_outer and roles[y][x] not in {"LIGHT", "STRUCTURAL_EDGE"}:
                roles[y][x] = "DEEP_CREASE" if y >= 8 else "SHADOW"


def _role_color(
    role: str, recipe: dict[str, Any], art_config: dict[str, Any]
) -> RGBA:
    if role in art_config["outerMaskRamp"]:
        value = art_config["outerMaskRamp"][role]
        return value, value, value, 255
    secondary = load_v2_data()["palettes"]["families"][recipe["paletteFamily"]]["secondary"]
    key = {
        "INNER_SHADOW": "shadow",
        "INNER_BASE": "base",
        "INNER_LIGHT": "light",
    }[role]
    rgb = secondary[key]
    return rgb[0], rgb[1], rgb[2], 255


def _frames_for_roles(
    recipe: dict[str, Any],
    art_config: dict[str, Any],
    roles: dict[str, list[list[str | None]]],
) -> dict[str, list[list[RGBA]]]:
    return {
        direction: [
            [
                (0, 0, 0, 0) if role is None else _role_color(role, recipe, art_config)
                for role in row
            ]
            for row in roles[direction]
        ]
        for direction in DIRECTION_ORDER
    }


def render_hd_art_treatment(
    recipe: dict[str, Any], treatment: str
) -> HDArtTreatment:
    current: FashionSenseJacketRender = render_mistral_hd_jacket(recipe)
    art_config = load_hd_art_grammar()
    if treatment == "CURRENT":
        return HDArtTreatment(
            name=treatment,
            recipe=recipe,
            backend_config=current.config,
            art_config=art_config,
            regions=current.regions,
            roles=current.roles,
            frames=current.frames,
            texture=current.texture,
        )
    if treatment not in {"STRONGER_STARDEW", "POLISHED_HD", "BENCHMARK_REFINED"}:
        raise ValueError(f"unknown HD art treatment {treatment!r}")

    regions = current.regions if treatment == "STRONGER_STARDEW" else _polished_regions(current.regions)
    coverage = validate_body_coverage(regions, current.coverage_envelopes)
    if not coverage.passes:
        raise ValueError(f"{treatment} art pass regressed body coverage")
    roles = _assign_edge_hierarchy(
        regions,
        polished=treatment in {"POLISHED_HD", "BENCHMARK_REFINED"},
    )
    if treatment == "BENCHMARK_REFINED":
        for direction in DIRECTION_ORDER:
            _benchmark_refine_role_clusters(direction, regions[direction], roles[direction])
    frames = _frames_for_roles(recipe, art_config, roles)
    return HDArtTreatment(
        name=treatment,
        recipe=recipe,
        backend_config=current.config,
        art_config=art_config,
        regions=regions,
        roles=roles,
        frames=frames,
        texture=stack_frames(frames, current.config),
    )


def composite_art_default_frame(
    frame: list[list[RGBA]], art_config: dict[str, Any]
) -> list[list[RGBA]]:
    compatibility_config = {
        "primaryMaskRamp": {
            role.lower(): value for role, value in art_config["outerMaskRamp"].items()
        },
        "defaultPrimaryColor": art_config["defaultPrimaryColor"],
    }
    return composite_default_frame(frame, compatibility_config)
