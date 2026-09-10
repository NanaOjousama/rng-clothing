"""Static article/quality diagnostics for V5A unified garments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER
from generator.renderers.fashionsense.unified_v5a import FSV5AUnifiedRender, connected_components
from generator.v5a.engine import validate_v5a_recipe


@dataclass(frozen=True)
class V5ADiagnostics:
    passes: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict[str, Any]


def _row_runs(points: set[tuple[int, int]], y: int) -> list[tuple[int, int]]:
    xs = sorted(x for x, py in points if py == y)
    if not xs:
        return []
    runs: list[tuple[int, int]] = []
    start = previous = xs[0]
    for x in xs[1:]:
        if x != previous + 1:
            runs.append((start, previous))
            start = x
        previous = x
    runs.append((start, previous))
    return runs


def _coverage_missing(render: FSV5AUnifiedRender) -> dict[str, list[tuple[int, int]]]:
    result: dict[str, list[tuple[int, int]]] = {}
    envelope = render.design.base.config["bodyCoverageEnvelope"]
    for direction in DIRECTION_ORDER:
        lookup = "right" if direction == "left" else direction
        rows = envelope[lookup]
        if direction == "left":
            rows = [row[::-1] for row in rows]
        missing = []
        for y, row in enumerate(rows[:3]):
            for x, marker in enumerate(row):
                if marker != "#":
                    continue
                if render.hide_sleeves and render.design.base.regions[direction][y][x] == "SLEEVE":
                    continue
                if not render.frames[direction][y][x][3]:
                    missing.append((x, y))
        result[direction] = missing
    return result


def diagnose_v5a(render: FSV5AUnifiedRender) -> V5ADiagnostics:
    recipe = render.recipe
    errors: list[str] = []
    warnings: list[str] = []
    validation = validate_v5a_recipe(recipe)
    errors.extend(validation.errors)
    warnings.extend(validation.warnings)
    expected_height = len(render.frames["front"])
    if expected_height != render.frame_height or any(len(render.frames[d]) != expected_height for d in DIRECTION_ORDER):
        errors.append("direction frame heights differ")
    alpha = {pixel[3] for direction in DIRECTION_ORDER for row in render.frames[direction] for pixel in row}
    if not alpha <= {0, 255}:
        errors.append("non-binary alpha found")
    if any(not render.extension_cells[direction] for direction in DIRECTION_ORDER):
        errors.append("article does not visibly extend past the frozen 16-row top footprint in every direction")
    coverage = _coverage_missing(render)
    if any(coverage.values()):
        errors.append(f"upper-body coverage regression: {coverage}")
    for direction in DIRECTION_ORDER:
        lower = {(x, y) for x, y in render.article_cells[direction] if y >= render.transition_y and render.regions[direction][y][x] != "SLEEVE"}
        components = connected_components(lower)
        if not components:
            errors.append(f"{direction}: no unified lower article mass")
        elif len(components) > 2:
            errors.append(f"{direction}: lower article fragments into {len(components)} components")
        transition = {x for x, y in lower if y == render.transition_y}
        if len(transition) < 5:
            errors.append(f"{direction}: waist/hip transition is too narrow")
    article = recipe["articleType"]
    front = set(render.article_cells["front"])
    back = set(render.article_cells["back"])
    hem_y = render.frame_height - 1
    front_runs = _row_runs(front, hem_y)
    back_runs = _row_runs(back, hem_y)
    if article == "DRESS":
        if len(front_runs) != 1 or len(back_runs) != 1:
            errors.append("dress hem must remain a deliberate unified mass in front and back")
        waist_runs = _row_runs(front, render.transition_y)
        if not waist_runs or front_runs[0][1] - front_runs[0][0] < waist_runs[0][1] - waist_runs[0][0]:
            errors.append("dress silhouette does not preserve/expand from waist to lower hem")
    elif article == "ONE_PIECE":
        regions = {render.regions["front"][y][x] for x, y in front if y >= render.transition_y}
        if not ({"BELT", "LOWER_PANEL", "CENTER_SEAM"} & regions):
            errors.append("one-piece lacks belt/lower-panel construction evidence")
        if recipe["articleIntent"]["lowerForm"] == "work_apron" and len(front_runs) != 2:
            errors.append("work one-piece lacks its intentional short apron/coverall notch")
    else:
        mid_y = min(render.frame_height - 2, render.transition_y + 2)
        mid_regions = {render.regions["front"][mid_y][x] for x in range(16)}
        if not {"OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT"} <= mid_regions:
            errors.append("long outerwear front lacks separate outer panels")
        if recipe["articleIntent"]["front"] == "open" and len(_row_runs(front, mid_y)) < 2:
            errors.append("open long outerwear lacks a visible center opening")
        if recipe["articleIntent"]["front"] == "partially_open" and "INNER_LAYER" not in mid_regions:
            errors.append("partially-open long outerwear lacks a visible inner layer")
        if not back_runs:
            errors.append("long outerwear back has no bounded extended hem")
    targets = [recipe["articleSurfacePlan"]["primaryTarget"], *recipe["articleSurfacePlan"]["supportTargets"]]
    target_counts = {target: sum(len(points) for points in render.surface_cells[target].values()) for target in targets}
    for target, count in target_counts.items():
        if count == 0:
            errors.append(f"article surface target {target} rendered no visible cells")
    if article == "BOUNDED_LONG_OUTERWEAR" and render.frame_height > 24:
        errors.append("bounded long outerwear exceeds the V5A 24-row ceiling")
    metrics = {
        "articleType": article,
        "promotionStatus": recipe["promotionStatus"],
        "frameSize": [16, render.frame_height],
        "Scale": 2.0,
        "BodyPosition": [0, 32],
        "extensionCells": {direction: len(points) for direction, points in render.extension_cells.items()},
        "surfaceTargetCells": target_counts,
        "bodyCoverageMissing": coverage,
        "frontHemRuns": front_runs,
        "backHemRuns": back_runs,
        "hideSleeves": render.hide_sleeves,
        "sleeveIntent": recipe["sleeveIntent"],
        "runtimeEvidence": "NOT_TESTED",
    }
    return V5ADiagnostics(not errors, tuple(errors), tuple(warnings), metrics)


def diagnose_v5a_collection(recipes, renders, diagnostics) -> V5ADiagnostics:
    errors: list[str] = []
    warnings: list[str] = []
    if len(recipes) != 9:
        errors.append("V5A collection must contain exactly nine garments")
    for article in ("DRESS", "ONE_PIECE", "BOUNDED_LONG_OUTERWEAR"):
        selected = [recipe for recipe in recipes if recipe["articleType"] == article]
        if len(selected) != 3:
            errors.append(f"{article} must have exactly three prototypes")
        if {recipe["designRecipe"]["rarity"] for recipe in selected} != {"Common", "Uncommon", "Rare"}:
            errors.append(f"{article} must include Common, Uncommon, and Rare")
    signatures = []
    for render in renders:
        signatures.append(tuple(tuple(_row_runs(set(render.article_cells[d]), render.frame_height - 1)) for d in DIRECTION_ORDER))
    if len(set(signatures)) < 6:
        errors.append("too many V5A lower silhouettes collapse to identical hem signatures")
    texture_signatures = [bytes(channel for row in render.texture for pixel in row for channel in pixel) for render in renders]
    if len(set(texture_signatures)) != len(texture_signatures):
        errors.append("two V5A garments are byte-identical")
    for recipe, diagnostic in zip(recipes, diagnostics):
        errors.extend(f"{recipe['id']}: {message}" for message in diagnostic.errors)
        warnings.extend(f"{recipe['id']}: {message}" for message in diagnostic.warnings)
    metrics = {
        "count": len(recipes),
        "articleCounts": {article: sum(recipe["articleType"] == article for recipe in recipes) for article in ("DRESS", "ONE_PIECE", "BOUNDED_LONG_OUTERWEAR")},
        "rarityCounts": {rarity: sum(recipe["designRecipe"]["rarity"] == rarity for recipe in recipes) for rarity in ("Common", "Uncommon", "Rare")},
        "uniqueHemSignatures": len(set(signatures)),
        "allExperimental": all(recipe["promotionStatus"] == "EXPERIMENTAL" for recipe in recipes),
    }
    return V5ADiagnostics(not errors, tuple(errors), tuple(warnings), metrics)
