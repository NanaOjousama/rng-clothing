"""Batch-level V3 diversity and design-quality gates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from generator.renderers.fashionsense.surface_v3 import FSV3Diagnostics, FSV3SurfaceRender
from generator.v3.engine import design_signature, load_v3_data, validate_recipe_v3


@dataclass(frozen=True)
class V3BatchValidation:
    passes: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict[str, Any]


def _jaccard(a: set[tuple[str, int, int]], b: set[tuple[str, int, int]]) -> float:
    union = a | b
    return 0.0 if not union else len(a & b) / len(union)


def _surface_mask(render: FSV3SurfaceRender) -> set[tuple[str, int, int]]:
    return {
        (direction, x, y)
        for direction, frame in render.surface_roles.items()
        for y, row in enumerate(frame)
        for x, role in enumerate(row)
        if role is not None
    }


def _theme_compatibility(recipe: dict[str, Any], vocabulary: dict[str, Any]) -> list[str]:
    profile = vocabulary["themeFamilies"][recipe["themeFamily"]]
    errors = []
    motif = recipe["surfaceDesign"]["motif"]["family"]
    trim = recipe["surfaceDesign"]["trim"]["type"]
    pattern = recipe["surfaceDesign"]["pattern"]["type"]
    if motif != "none" and motif not in profile["motifs"]:
        errors.append(f"motif {motif} is outside {recipe['themeFamily']} vocabulary")
    if trim != "none" and trim not in profile["trims"]:
        errors.append(f"trim {trim} is outside {recipe['themeFamily']} vocabulary")
    if pattern != "none" and pattern not in profile["patterns"]:
        errors.append(f"pattern {pattern} is outside {recipe['themeFamily']} vocabulary")
    if recipe["concept"]["designMood"] not in profile["moods"]:
        errors.append(f"mood {recipe['concept']['designMood']} is outside {recipe['themeFamily']} vocabulary")
    return errors


def validate_v3_batch(
    recipes: list[dict[str, Any]],
    renders: list[FSV3SurfaceRender],
    diagnostics: list[FSV3Diagnostics],
) -> V3BatchValidation:
    data = load_v3_data(); errors: list[str] = []; warnings: list[str] = []
    if len(recipes) != 12 or len(renders) != 12 or len(diagnostics) != 12:
        errors.append("controlled V3 benchmark must contain exactly twelve garments")
    rarity_counts = {rarity: sum(recipe["rarity"] == rarity for recipe in recipes) for rarity in ("Common", "Uncommon", "Rare")}
    if rarity_counts != {"Common": 4, "Uncommon": 4, "Rare": 4}:
        errors.append(f"expected 4/4/4 rarity distribution, found {rarity_counts}")
    for recipe, diagnostic in zip(recipes, diagnostics):
        result = validate_recipe_v3(recipe, data)
        errors.extend(f"{recipe['id']}: {message}" for message in result.errors)
        errors.extend(f"{recipe['id']}: {message}" for message in diagnostic.errors)
        warnings.extend(f"{recipe['id']}: {message}" for message in diagnostic.warnings)
        errors.extend(f"{recipe['id']}: {message}" for message in _theme_compatibility(recipe, data["vocabulary"]))
        if not diagnostic.metrics["designInterestWithoutShading"]:
            errors.append(f"{recipe['id']}: fails shading-independent design-interest test")
        if any(diagnostic.metrics["bodyCoverageMissing"].values()):
            errors.append(f"{recipe['id']}: body coverage regression")

    axes = {
        "themeFamily": {recipe["themeFamily"] for recipe in recipes},
        "archetype": {recipe["archetype"] for recipe in recipes},
        "compositionType": {recipe["surfaceDesign"]["compositionType"] for recipe in recipes},
        "focalArea": {recipe["concept"]["focalArea"] for recipe in recipes},
        "symmetryBias": {recipe["concept"]["symmetryBias"] for recipe in recipes},
        "colorBlock": {recipe["colorBlocking"]["type"] for recipe in recipes},
        "trim": {recipe["surfaceDesign"]["trim"]["type"] for recipe in recipes},
        "motif": {recipe["surfaceDesign"]["motif"]["family"] for recipe in recipes},
        "pattern": {recipe["surfaceDesign"]["pattern"]["type"] for recipe in recipes},
        "paletteStory": {recipe["paletteStory"] for recipe in recipes},
    }
    minima = {"themeFamily": 10, "archetype": 4, "compositionType": 5, "focalArea": 5, "symmetryBias": 3, "colorBlock": 4, "trim": 7, "motif": 8, "pattern": 3, "paletteStory": 10}
    for axis, values in axes.items():
        if len(values) < minima[axis]:
            errors.append(f"diversity axis {axis} has only {len(values)} values; requires {minima[axis]}")

    pairwise = []
    masks = [_surface_mask(render) for render in renders]
    for left in range(len(recipes)):
        for right in range(left + 1, len(recipes)):
            ls = design_signature(recipes[left]); rs = design_signature(recipes[right])
            semantic = sum(a == b for a, b in zip(ls, rs)) / len(ls)
            surface = _jaccard(masks[left], masks[right])
            pairwise.append({"left": recipes[left]["id"], "right": recipes[right]["id"], "semanticSimilarity": round(semantic, 4), "surfaceMaskJaccard": round(surface, 4)})
            if semantic >= 0.75:
                errors.append(f"{recipes[left]['id']} and {recipes[right]['id']} are semantic near-duplicates ({semantic:.2f})")
            if recipes[left]["archetype"] == recipes[right]["archetype"] and surface >= 0.80 and semantic >= 0.50:
                errors.append(f"{recipes[left]['id']} and {recipes[right]['id']} collapse to near-identical surface placement")

    average_cells = {}
    for rarity in ("Common", "Uncommon", "Rare"):
        indices = [i for i, recipe in enumerate(recipes) if recipe["rarity"] == rarity]
        average_cells[rarity] = round(sum(sum(diagnostics[i].metrics["visibleSurfaceCells"].values()) / 4 for i in indices) / len(indices), 3)
    if not average_cells["Common"] < average_cells["Uncommon"] < average_cells["Rare"]:
        warnings.append(f"surface-cell averages are not strictly tiered: {average_cells}; inspect hierarchy rather than adding clutter")
    metrics = {
        "rarityCounts": rarity_counts,
        "uniqueAxisCounts": {axis: len(values) for axis, values in axes.items()},
        "averageSurfaceCellsPerView": average_cells,
        "maximumSemanticSimilarity": max((pair["semanticSimilarity"] for pair in pairwise), default=0),
        "maximumSurfaceMaskJaccard": max((pair["surfaceMaskJaccard"] for pair in pairwise), default=0),
        "pairwise": pairwise,
    }
    return V3BatchValidation(not errors, tuple(errors), tuple(warnings), metrics)
