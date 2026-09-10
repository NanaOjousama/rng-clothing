"""Named-region V2 structural masks and the unshaded two-color gate."""

from __future__ import annotations

import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from generator.png_utils import (
    RGBA,
    TRANSPARENT,
    blank_image,
    blit,
    draw_rect,
    draw_text,
    nearest_scale,
    text_width,
    write_rgba_png,
)
from generator.v2_recipe_engine import ARCHETYPE_ORDER, load_v2_data, validate_recipe_v2


ROOT = Path(__file__).resolve().parents[1]
STRUCTURAL_OUTPUT = ROOT / "output" / "structural-tests" / "v2"
FRAME_SIZE = 8
DIRECTION_ORDER = ("front", "back", "left", "right")
VANILLA_DIRECTION_Y = {"front": 0, "right": 8, "left": 16, "back": 24}
PREVIEW_SCALE = 8
COLOR_A: RGBA = (74, 104, 122, 255)
COLOR_B: RGBA = (235, 217, 177, 255)


@dataclass
class StructuralGarment:
    recipe: dict[str, Any]
    regions: dict[str, list[list[str | None]]]


def _mirror_rows(rows: list[str], swaps: dict[str, str] | None = None) -> list[str]:
    swaps = swaps or {}
    return ["".join(swaps.get(value, value) for value in reversed(row)) for row in rows]


def _resolve_rows(model: dict[str, Any], direction: str) -> list[str]:
    value = model[direction]
    if isinstance(value, dict) and "mirrorOf" in value:
        return _mirror_rows(
            _resolve_rows(model, value["mirrorOf"]), value.get("swapRegions")
        )
    if not isinstance(value, list) or len(value) != FRAME_SIZE:
        raise ValueError(f"invalid structural rows for {direction}")
    if any(not isinstance(row, str) or len(row) != FRAME_SIZE for row in value):
        raise ValueError(f"invalid structural row width for {direction}")
    return value


def _resolve_silhouette_rows(grammar: dict[str, Any], fit: str, direction: str) -> list[str]:
    model = grammar["silhouetteTemplates"][fit]
    value = model[direction]
    if isinstance(value, dict) and "mirrorOf" in value:
        return [row[::-1] for row in _resolve_silhouette_rows(grammar, fit, value["mirrorOf"])]
    return value


def _canonical_regions(
    archetype_id: str, fit: str, data: dict[str, Any]
) -> dict[str, list[list[str | None]]]:
    contract = data["structuralMasks"]
    legend = contract["regionLegend"]
    model = contract["archetypeMasks"][archetype_id]
    result: dict[str, list[list[str | None]]] = {}
    for direction in ("front", "right", "left", "back"):
        rows = _resolve_rows(model, direction)
        silhouette = _resolve_silhouette_rows(data["grammar"], fit, direction)
        frame: list[list[str | None]] = []
        for y in range(FRAME_SIZE):
            logical_row: list[str | None] = []
            for x in range(FRAME_SIZE):
                if silhouette[y][x] == ".":
                    logical_row.append(None)
                else:
                    symbol = rows[y][x]
                    if symbol == ".":
                        logical_row.append("BODY")
                    elif symbol not in legend:
                        raise ValueError(f"unknown region symbol {symbol!r}")
                    else:
                        logical_row.append(legend[symbol])
            frame.append(logical_row)
        result[direction] = frame
    return result


def _paint(
    frame: list[list[str | None]], points: Iterable[tuple[int, int]], region: str
) -> None:
    for x, y in points:
        if 0 <= x < FRAME_SIZE and 0 <= y < FRAME_SIZE and frame[y][x] is not None:
            frame[y][x] = region


def _paint_row(
    frame: list[list[str | None]], y: int, xs: Iterable[int], region: str
) -> None:
    _paint(frame, ((x, y) for x in xs), region)


def _replace_region(
    frames: dict[str, list[list[str | None]]], old: str, new: str
) -> None:
    for frame in frames.values():
        for row in frame:
            for x, region in enumerate(row):
                if region == old:
                    row[x] = new


def _sync_left_from_right(frames: dict[str, list[list[str | None]]]) -> None:
    swaps = {
        "OUTER_PANEL_RIGHT": "OUTER_PANEL_LEFT",
        "OUTER_PANEL_LEFT": "OUTER_PANEL_RIGHT",
    }
    frames["left"] = [
        [swaps.get(value, value) for value in reversed(row)]
        for row in frames["right"]
    ]


def _apply_lightweight_neckline(
    frames: dict[str, list[list[str | None]]], neckline: str, *, heavy: bool
) -> None:
    _replace_region(frames, "NECKLINE", "BODY")
    front, back, right = frames["front"], frames["back"], frames["right"]
    if neckline == "crew":
        _paint(front, ((x, 1) for x in range(2, 6)), "NECKLINE")
        if heavy:
            _paint(front, ((3, 2), (4, 2)), "NECKLINE")
        _paint(back, ((x, 0) for x in range(2, 6)), "NECKLINE")
        _paint(right, ((2, 0), (4, 0), (5, 0), (4, 1), (5, 1)), "NECKLINE")
    elif neckline == "round":
        _paint(front, ((3, 1), (4, 1), (3, 2), (4, 2)), "NECKLINE")
        if heavy:
            _paint(front, ((2, 1), (5, 1)), "NECKLINE")
        _paint(back, ((3, 0), (4, 0)), "NECKLINE")
        _paint(right, ((4, 0), (5, 0), (4, 1)), "NECKLINE")
    elif neckline == "shallow_v":
        _paint(front, ((2, 1), (5, 1), (3, 2), (4, 2), (3, 3), (4, 3)), "NECKLINE")
        _paint(back, ((3, 0), (4, 0)), "NECKLINE")
        _paint(right, ((4, 0), (5, 0), (5, 1), (5, 2)), "NECKLINE")
    else:
        raise ValueError(f"unsupported pullover neckline {neckline}")
    _sync_left_from_right(frames)


def _apply_wide_collar(frames: dict[str, list[list[str | None]]]) -> None:
    front, back, right = frames["front"], frames["back"], frames["right"]
    _paint(front, ((x, 1) for x in (1, 2, 5, 6)), "COLLAR")
    _paint(front, ((x, 2) for x in range(2, 6)), "COLLAR")
    _paint(front, ((3, 3), (4, 3)), "COLLAR")
    _paint(back, ((x, 0) for x in range(1, 7)), "COLLAR")
    _paint(back, ((x, 1) for x in range(2, 6)), "COLLAR")
    _paint(right, ((2, 0), (4, 0), (5, 0), (3, 1), (4, 1), (5, 1)), "COLLAR")
    _sync_left_from_right(frames)


def _apply_jacket_lapels(frames: dict[str, list[list[str | None]]]) -> None:
    """Broaden jacket lapels without turning them into a deep horizontal band."""
    front, back, right = frames["front"], frames["back"], frames["right"]
    # Two shallow diagonals frame an uninterrupted central inner layer.
    _paint(front, ((1, 1), (2, 1), (5, 1), (6, 1)), "COLLAR")
    _paint(front, ((2, 2), (5, 2)), "COLLAR")
    # The rear collar is broad but only one cell deep; the tapered yoke below
    # carries shoulder anatomy without forming a full-width stripe.
    _paint(back, ((x, 0) for x in range(2, 6)), "COLLAR")
    # Side lapels slope toward the forward opening and end after two rows.
    _paint(right, ((2, 0), (4, 0), (5, 0), (3, 1), (6, 1)), "COLLAR")
    _sync_left_from_right(frames)


def _apply_hem(
    frames: dict[str, list[list[str | None]]], region: str, *, depth: int = 1
) -> None:
    for direction, frame in frames.items():
        start = FRAME_SIZE - depth
        for y in range(start, FRAME_SIZE):
            _paint_row(frame, y, range(FRAME_SIZE), region)


def _apply_wrapping_stripe(frames: dict[str, list[list[str | None]]], row: int = 4) -> None:
    for frame in frames.values():
        _paint_row(frame, row, range(FRAME_SIZE), "STRIPE")


def _apply_yoke(frames: dict[str, list[list[str | None]]], *, deep: bool) -> None:
    front, back, right = frames["front"], frames["back"], frames["right"]
    _paint_row(front, 1, range(8), "YOKE")
    _paint_row(front, 2, range(1, 7), "YOKE")
    if deep:
        _paint_row(front, 3, range(2, 6), "YOKE")
    for y in range(0, 3 if deep else 2):
        _paint_row(back, y, range(8), "YOKE")
    _paint_row(right, 0, range(8), "YOKE")
    _paint_row(right, 1, range(8), "YOKE")
    if deep:
        _paint_row(right, 2, range(1, 7), "YOKE")
    _sync_left_from_right(frames)


def _build_closed_jacket(frames: dict[str, list[list[str | None]]]) -> None:
    for direction, frame in frames.items():
        for y, row in enumerate(frame):
            for x, region in enumerate(row):
                if region is not None and region not in {"COLLAR", "YOKE", "HEM"}:
                    if direction == "left":
                        row[x] = "OUTER_PANEL_LEFT"
                    elif direction == "right":
                        row[x] = "OUTER_PANEL_RIGHT"
                    else:
                        row[x] = "OUTER_PANEL_LEFT" if x < 4 else "OUTER_PANEL_RIGHT"
    front, right = frames["front"], frames["right"]
    _paint(front, ((x, y) for y in range(2, 8) for x in (3, 4)), "PLACKET")
    _paint(right, ((x, y) for y in range(2, 8) for x in (6, 7)), "PLACKET")
    _sync_left_from_right(frames)


def build_structural_regions(
    recipe: dict[str, Any], data: dict[str, Any]
) -> dict[str, list[list[str | None]]]:
    validation = validate_recipe_v2(recipe, data)
    if not validation.valid:
        raise ValueError(f"invalid V2 recipe: {'; '.join(validation.errors)}")
    construction = recipe["construction"]
    archetype = recipe["archetype"]
    frames = _canonical_regions(archetype, construction["fit"], data)

    if archetype == "T_SHIRT":
        _apply_lightweight_neckline(frames, construction["neckline"], heavy=False)
        if construction["panelLayout"] == "upper_lower_split":
            _apply_hem(frames, "HEM", depth=3)
        elif construction["hem"] == "contrast_band":
            _apply_hem(frames, "HEM", depth=1)
    elif archetype == "SWEATER":
        _apply_lightweight_neckline(frames, construction["neckline"], heavy=True)
        if construction["hem"] == "ribbed":
            _apply_hem(frames, "RIBBING", depth=2)
        elif construction["hem"] in {"structured", "contrast_band"}:
            _replace_region(frames, "RIBBING", "BODY")
            _apply_hem(frames, "HEM", depth=1 if construction["hem"] == "structured" else 2)
        if construction["panelLayout"] == "yoke":
            _apply_yoke(frames, deep=False)
        elif construction["panelLayout"] == "upper_lower_split":
            _apply_hem(frames, "HEM", depth=3)
        if construction["collar"] == "wide":
            _apply_wide_collar(frames)
    elif archetype == "BUTTON_SHIRT":
        if construction["panelLayout"] == "yoke":
            _apply_yoke(frames, deep=False)
            # The closure always retains a real placket through the overlay.
            _paint(frames["front"], ((x, y) for y in range(2, 8) for x in (3, 4)), "PLACKET")
            _paint(frames["right"], ((x, y) for y in range(2, 8) for x in (6, 7)), "PLACKET")
            _sync_left_from_right(frames)
        if construction["hem"] in {"structured", "contrast_band"}:
            _apply_hem(frames, "HEM", depth=1)
    elif archetype == "JACKET":
        if construction["panelLayout"] == "center_placket":
            _build_closed_jacket(frames)
        if construction["hem"] in {"structured", "contrast_band"}:
            # Preserve the open inner layer at the center/forward edge.
            if construction["panelLayout"] == "split_outer_panels":
                _paint(frames["front"], ((x, 7) for x in (0, 1, 6, 7)), "HEM")
                _paint(frames["back"], ((x, 7) for x in range(1, 7)), "HEM")
                _paint(frames["right"], ((x, 7) for x in range(1, 6)), "HEM")
                _sync_left_from_right(frames)
            else:
                _apply_hem(frames, "HEM", depth=1)
        if construction["collar"] == "wide" or "broad_collar" in recipe["substantialFeatures"]:
            _apply_jacket_lapels(frames)
    elif archetype == "SAILOR_TOP":
        if construction["panelLayout"] == "upper_lower_split":
            _replace_region(frames, "YOKE", "BODY")
            _paint_row(frames["front"], 1, range(8), "YOKE")
            _paint_row(frames["front"], 2, range(1, 7), "YOKE")
            _paint_row(frames["back"], 0, range(8), "YOKE")
            _paint_row(frames["back"], 1, range(8), "YOKE")
            _paint_row(frames["right"], 0, range(8), "YOKE")
            _paint_row(frames["right"], 1, range(8), "YOKE")
            _sync_left_from_right(frames)
            _apply_hem(frames, "HEM", depth=3)
        if construction["hem"] in {"structured", "contrast_band"}:
            _apply_hem(frames, "HEM", depth=1)
        if construction["collar"] == "wide":
            _apply_wide_collar(frames)

    if "wrapping_stripe" in recipe["substantialFeatures"]:
        _apply_wrapping_stripe(frames)
    return frames


def control_recipes(data: dict[str, Any]) -> list[dict[str, Any]]:
    definitions = [
        (
            "T_SHIRT",
            "t-shirt",
            "Stonefield Essential Tee",
            "A clean neutral tee used to prove V2's intentionally simple base construction.",
            "Common",
            {"fit": "regular", "neckline": "crew", "collar": "none", "closure": "none", "layering": "single_layer", "hem": "plain", "panelLayout": "solid"},
            [],
            "none",
        ),
        (
            "SWEATER",
            "sweater",
            "Stonefield Rib-Knit Sweater",
            "A neutral pullover whose neckline weight and broad ribbing carry its identity.",
            "Common",
            {"fit": "relaxed", "neckline": "crew", "collar": "none", "closure": "none", "layering": "single_layer", "hem": "ribbed", "panelLayout": "solid"},
            ["ribbed_hem"],
            "ribbing",
        ),
        (
            "BUTTON_SHIRT",
            "button-shirt",
            "Stonefield Tailored Shirt",
            "A neutral work shirt organized around a folded collar and continuous placket.",
            "Common",
            {"fit": "regular", "neckline": "open", "collar": "small_folded", "closure": "buttons", "layering": "single_layer", "hem": "plain", "panelLayout": "center_placket"},
            ["center_placket"],
            "placket",
        ),
        (
            "JACKET",
            "jacket",
            "Stonefield Layer Jacket",
            "A neutral outer layer with split panels wrapped around a visible inner garment.",
            "Common",
            {"fit": "regular", "neckline": "open", "collar": "small_folded", "closure": "center_open", "layering": "visible_inner_layer", "hem": "structured", "panelLayout": "split_outer_panels"},
            ["contrast_inner_layer"],
            "inner_layer",
        ),
        (
            "SAILOR_TOP",
            "sailor-top",
            "Stonefield Sailor-Yoke Top",
            "A neutral broad-collar top whose upper yoke remains clear from every direction.",
            "Common",
            {"fit": "regular", "neckline": "open", "collar": "sailor", "closure": "none", "layering": "overlay_panel", "hem": "plain", "panelLayout": "yoke"},
            ["yoke"],
            "yoke",
        ),
    ]
    recipes = []
    for index, (
        archetype,
        slug,
        name,
        description,
        rarity,
        construction,
        substantial,
        secondary,
    ) in enumerate(definitions, start=1):
        recipe = {
            "id": f"lifestyle-v2-control-{slug}",
            "generationIndex": index,
            "seed": 202608282200 + index,
            "category": "Lifestyle",
            "styleProfile": "General",
            "referenceTraits": ["compact_straight", "restrained_palette", "structural_color_blocking"],
            "archetype": archetype,
            "rarity": rarity,
            "construction": construction,
            "substantialFeatures": substantial,
            "microDetails": [],
            "colorBlocking": {
                "primaryRegion": "outer_panels" if archetype == "JACKET" else "body",
                "secondaryRegion": secondary,
                "accentRegion": "none",
            },
            "paletteFamily": "cool_neutral",
            "accent": "none",
            "dyeable": True,
            "itemName": name,
            "itemDescription": description,
        }
        validation = validate_recipe_v2(recipe, data)
        if not validation.valid:
            raise ValueError(f"invalid control recipe {recipe['id']}: {validation.errors}")
        recipes.append(recipe)
    return recipes


def _two_color_frame(
    archetype_id: str,
    frame: list[list[str | None]],
    data: dict[str, Any],
) -> list[list[RGBA]]:
    groups = data["structuralMasks"]["twoColorGroups"][archetype_id]
    primary = set(groups["primary"])
    secondary = set(groups["secondary"])
    pixels = blank_image(8, 8)
    for y, row in enumerate(frame):
        for x, region in enumerate(row):
            if region is None:
                continue
            if region in secondary:
                pixels[y][x] = COLOR_B
            elif region in primary:
                pixels[y][x] = COLOR_A
            else:
                raise ValueError(f"{archetype_id}: region {region} is missing from its two-color groups")
    return pixels


def structural_two_color_frames(
    garment: StructuralGarment, data: dict[str, Any]
) -> dict[str, list[list[RGBA]]]:
    return {
        direction: _two_color_frame(garment.recipe["archetype"], frame, data)
        for direction, frame in garment.regions.items()
    }


def _stack_directions(frames: dict[str, list[list[RGBA]]]) -> list[list[RGBA]]:
    pixels = blank_image(8, 32)
    for direction, y0 in VANILLA_DIRECTION_Y.items():
        blit(pixels, frames[direction], 0, y0)
    return pixels


def _checker_tile(canvas: list[list[RGBA]], x0: int, y0: int, scale: int) -> None:
    checker = ((211, 201, 188, 255), (191, 181, 169, 255))
    for y in range(8):
        for x in range(8):
            draw_rect(canvas, x0 + x * scale, y0 + y * scale, scale, scale, checker[(x + y) % 2])


def make_direction_contact(
    frames: dict[str, list[list[RGBA]]], title: str
) -> list[list[RGBA]]:
    width, height = 352, 128
    pixels = blank_image(width, height, (235, 226, 214, 255))
    label = title.upper()
    draw_text(pixels, label, max(8, (width - text_width(label)) // 2), 6)
    start_x, tile_y, gap = 12, 52, 16
    for index, direction in enumerate(DIRECTION_ORDER):
        x0 = start_x + index * (64 + gap)
        draw_text(
            pixels,
            direction.upper(),
            x0 + (64 - text_width(direction)) // 2,
            31,
        )
        draw_rect(pixels, x0 - 2, tile_y - 2, 68, 68, (101, 86, 73, 255))
        _checker_tile(pixels, x0, tile_y, PREVIEW_SCALE)
        blit(pixels, nearest_scale(frames[direction], PREVIEW_SCALE), x0, tile_y)
    return pixels


def make_archetype_comparison(
    garments: list[StructuralGarment], data: dict[str, Any]
) -> list[list[RGBA]]:
    width, height = 390, 500
    pixels = blank_image(width, height, (235, 226, 214, 255))
    title = "V2 TWO-COLOR ARCHETYPE COMPARISON"
    draw_text(pixels, title, (width - text_width(title)) // 2, 8)
    for direction_index, direction in enumerate(DIRECTION_ORDER):
        draw_text(pixels, direction, 110 + direction_index * 68, 28)
    for row_index, garment in enumerate(garments):
        y0 = 52 + row_index * 86
        label = garment.recipe["archetype"].replace("_", "-")
        draw_text(pixels, label, 8, y0 + 28)
        frames = structural_two_color_frames(garment, data)
        for direction_index, direction in enumerate(DIRECTION_ORDER):
            x0 = 106 + direction_index * 68
            draw_rect(pixels, x0 - 1, y0 - 1, 66, 66, (101, 86, 73, 255))
            _checker_tile(pixels, x0, y0, PREVIEW_SCALE)
            blit(pixels, nearest_scale(frames[direction], PREVIEW_SCALE), x0, y0)
    draw_text(pixels, "COLOR-A PRIMARY   COLOR-B STRUCTURE", 87, 482)
    return pixels


def _secondary_points(
    archetype_id: str,
    regions: dict[str, list[list[str | None]]],
    data: dict[str, Any],
    direction: str,
) -> set[tuple[int, int]]:
    secondary = set(data["structuralMasks"]["twoColorGroups"][archetype_id]["secondary"])
    return {
        (x, y)
        for y, row in enumerate(regions[direction])
        for x, region in enumerate(row)
        if region in secondary
    }


def validate_structural_similarity(
    garments: list[StructuralGarment], data: dict[str, Any]
) -> dict[str, Any]:
    policy = data["structuralMasks"]["similarityGate"]
    directions = policy["directionsCompared"]
    comparisons = []
    rejected = []
    warnings = []
    for first, second in itertools.combinations(garments, 2):
        differences: dict[str, int] = {}
        jaccards: dict[str, float] = {}
        exact_region_match = True
        for direction in directions:
            first_points = _secondary_points(first.recipe["archetype"], first.regions, data, direction)
            second_points = _secondary_points(second.recipe["archetype"], second.regions, data, direction)
            differences[direction] = len(first_points ^ second_points)
            union = first_points | second_points
            jaccards[direction] = round(len(first_points & second_points) / len(union), 4) if union else 1.0
            if first.regions[direction] != second.regions[direction]:
                exact_region_match = False
        total_difference = sum(differences.values())
        directions_different = sum(
            value >= policy["minimumDifferentCellsPerDirection"]
            for value in differences.values()
        )
        reasons = []
        if policy["rejectExactMajorRegionMatch"] and exact_region_match:
            reasons.append("exact named-region match")
        if total_difference <= policy["rejectTotalTwoColorDifferenceAtOrBelow"]:
            reasons.append("two-color masks differ by too few cells")
        if directions_different < policy["rejectIfFewerThanDirectionsDiffer"]:
            reasons.append("archetype difference does not survive all compared directions")
        pair = f"{first.recipe['archetype']} vs {second.recipe['archetype']}"
        warning = any(
            value >= policy["warningTwoColorJaccardAtOrAbove"]
            for value in jaccards.values()
        )
        record = {
            "pair": pair,
            "differentCellsByDirection": differences,
            "totalDifferentCells": total_difference,
            "secondaryMaskJaccardByDirection": jaccards,
            "directionsWithMaterialDifference": directions_different,
            "exactNamedRegionMatch": exact_region_match,
            "status": "REJECT" if reasons else "PASS",
            "reasons": reasons,
        }
        comparisons.append(record)
        if reasons:
            rejected.append(record)
        elif warning:
            warnings.append(
                {"pair": pair, "reason": "one directional secondary mask has high Jaccard overlap"}
            )
    return {
        "status": "PASS" if not rejected else "FAIL",
        "meaning": policy["meaning"],
        "policy": policy,
        "comparisonCount": len(comparisons),
        "rejectedCount": len(rejected),
        "warningCount": len(warnings),
        "comparisons": comparisons,
        "warnings": warnings,
    }


def generate_structural_tests() -> dict[str, Any]:
    data = load_v2_data()
    recipes = control_recipes(data)
    garments = [
        StructuralGarment(recipe, build_structural_regions(recipe, data))
        for recipe in recipes
    ]
    STRUCTURAL_OUTPUT.mkdir(parents=True, exist_ok=True)
    records = []
    for garment in garments:
        archetype_slug = garment.recipe["archetype"].lower()
        frames = structural_two_color_frames(garment, data)
        logical = _stack_directions(frames)
        logical_path = STRUCTURAL_OUTPUT / f"{archetype_slug}-two-color-8x32.png"
        preview_path = STRUCTURAL_OUTPUT / f"{archetype_slug}-two-color-8x.png"
        contact_path = STRUCTURAL_OUTPUT / f"{archetype_slug}-two-color-directions-8x.png"
        write_rgba_png(logical_path, logical)
        write_rgba_png(preview_path, nearest_scale(logical, PREVIEW_SCALE))
        write_rgba_png(contact_path, make_direction_contact(frames, garment.recipe["archetype"]))
        records.append(
            {
                "archetype": garment.recipe["archetype"],
                "recipeId": garment.recipe["id"],
                "logicalPath": str(logical_path.relative_to(ROOT)),
                "previewPath": str(preview_path.relative_to(ROOT)),
                "contactPath": str(contact_path.relative_to(ROOT)),
                "regionsByDirection": {
                    direction: sorted(
                        {region for row in frame for region in row if region is not None}
                    )
                    for direction, frame in garment.regions.items()
                },
            }
        )
    comparison_path = STRUCTURAL_OUTPUT / "V2_TWO_COLOR_ARCHETYPE_COMPARISON.png"
    write_rgba_png(comparison_path, make_archetype_comparison(garments, data))
    similarity = validate_structural_similarity(garments, data)
    validation = {
        "status": similarity["status"],
        "stage": "unshaded two-color major-region gate",
        "colors": {"A": list(COLOR_A), "B": list(COLOR_B)},
        "garments": records,
        "comparisonPath": str(comparison_path.relative_to(ROOT)),
        "similarity": similarity,
    }
    validation_path = STRUCTURAL_OUTPUT / "structural_validation.json"
    validation_path.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    if validation["status"] != "PASS":
        raise RuntimeError(f"V2 structural gate failed; see {validation_path}")
    return validation


def main() -> None:
    validation = generate_structural_tests()
    print(
        f"V2 two-color structural gate {validation['status']}: "
        f"{len(validation['garments'])} archetypes, "
        f"{validation['similarity']['rejectedCount']} rejected similarities."
    )
    print(f"Comparison: {validation['comparisonPath']}")


if __name__ == "__main__":
    main()
