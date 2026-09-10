"""Static V5D construction, diversity, and Fashion Sense guardrails."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER
from generator.v5d.engine import validate_v5d_recipe


@dataclass(frozen=True)
class V5DArticleDiagnostics:
    passes: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict[str, Any]


@dataclass(frozen=True)
class V5DCollectionDiagnostics:
    passes: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict[str, Any]


ROLE_REQUIREMENTS = {
    "CASUAL_SHIRT": {"opening": 4, "pattern": 20},
    "WORK_SHIRT": {"opening": 8, "pockets": 10, "panels": 12},
    "KNIT_SWEATER": {"pattern": 40, "trim": 30},
    "STREET_HOODIE": {"collar": 60, "pockets": 20, "trim": 30},
    "CARDIGAN": {"opening": 30, "layering": 25, "pockets": 10},
    "FORMAL_WAISTCOAT": {"opening": 12, "layering": 6, "pockets": 4},
    "UTILITY_VEST": {"opening": 10, "pockets": 24, "panels": 16},
    "CROPPED_FIELD_JACKET": {"opening": 12, "layering": 14, "pockets": 10},
    "FORMAL_BLAZER": {"collar": 8, "layering": 6, "opening": 8},
    "PERIOD_TOP": {"collar": 8, "motif": 10, "opening": 4},
    "MILITARY_TOP": {"collar": 16, "pockets": 10, "panels": 16},
    "ADVENTURER_TUNIC": {"layering": 4, "trim": 15, "panels": 8},
    "ARMOR_TABARD": {"layering": 50, "panels": 40, "motif": 4},
    "ALT_STREET_TOP": {"opening": 16, "panels": 10, "motif": 4},
}


def _opaque(frame):
    return frozenset((x, y) for y, row in enumerate(frame) for x, pixel in enumerate(row) if pixel[3])


def _count(render, system: str, direction: str | None = None) -> int:
    return sum(len(render.signal_cells[system][d]) for d in ([direction] if direction else DIRECTION_ORDER))


def diagnose_v5d_article(render) -> V5DArticleDiagnostics:
    recipe = render.recipe
    errors: list[str] = []
    warnings: list[str] = []
    result = validate_v5d_recipe(recipe)
    errors.extend(result.errors)
    warnings.extend(result.warnings)
    if len(render.texture) != 64 or any(len(row) != 16 for row in render.texture):
        errors.append("V5D Shirt texture must be 16x64 with four direct 16x16 frames")
    alpha = sorted({pixel[3] for row in render.texture for pixel in row})
    if any(value not in {0, 255} for value in alpha):
        errors.append(f"non-binary Shirt alpha: {alpha}")
    if render.hide_native_sleeves:
        errors.append("V5D may not globally hide the arm/sleeve layer")
    if any(render.coverage_missing.values()):
        errors.append(f"body-coverage gaps: {render.coverage_missing}")
    role = recipe["articleRole"]
    for system, minimum in ROLE_REQUIREMENTS[role].items():
        actual = _count(render, system)
        if actual < minimum:
            errors.append(f"{role} lacks {system} evidence ({actual} < {minimum})")
    authored = sum(_count(render, system) for system in render.signal_cells if system != "silhouette")
    rarity = recipe["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]["rarity"]
    floor = {"Common": 35, "Uncommon": 55, "Rare": 65}[rarity]
    if authored < floor:
        errors.append(f"{rarity} shading-independent construction interest too low ({authored} < {floor})")
    active_systems = [system for system in render.signal_cells if system != "silhouette" and _count(render, system)]
    if len(active_systems) > {"Common": 6, "Uncommon": 7, "Rare": 8}[rarity]:
        errors.append(f"{rarity} activates too many equal surface systems: {active_systems}")
    nonfront = sum(len(render.signal_cells[system][direction]) for system in render.signal_cells for direction in ("right", "left", "back"))
    if nonfront < 12:
        errors.append(f"side/back reconstruction is under-authored ({nonfront} cells)")
    if recipe["sleeveIntent"] == "SHORT_SLEEVE":
        if render.companion_required or render.sleeves_texture is not None:
            errors.append("short sleeve should use Fashion Sense's default animated short sleeve")
    else:
        if not render.companion_required or render.sleeves_texture is None or render.sleeves_json is None:
            errors.append("long/cuffed/layered sleeve requires coordinated generated Sleeves companion")
        else:
            if len(render.sleeves_texture) != 1344 or any(len(row) != 384 for row in render.sleeves_texture):
                errors.append("Sleeves atlas must be 384x1344")
            sleeve_alpha = sorted({pixel[3] for row in render.sleeves_texture for pixel in row})
            if any(value not in {0, 255} for value in sleeve_alpha):
                errors.append(f"non-binary Sleeves alpha: {sleeve_alpha}")
    metrics = {
        "articleRole": role,
        "fashionFamily": recipe["fashionFamily"],
        "rarity": rarity,
        "logicalFrame": [16, 16],
        "scale": 2,
        "bodyPosition": [0, 32],
        "alphaValues": alpha,
        "opaqueCells": {direction: len(_opaque(render.frames[direction])) for direction in DIRECTION_ORDER},
        "signalCells": {system: {direction: len(render.signal_cells[system][direction]) for direction in DIRECTION_ORDER} for system in render.signal_cells},
        "activeSystems": active_systems,
        "authoredCells": authored,
        "nonFrontAuthoredCells": nonfront,
        "lightPalette": recipe["lightPalette"],
        "companionRequired": render.companion_required,
        "sleeveMetrics": render.sleeve_metrics,
        "promotion": "EXPERIMENTAL",
        "runtimeClaim": "NOT_TESTED",
    }
    return V5DArticleDiagnostics(not errors, tuple(errors), tuple(warnings), metrics)


def _jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a or b else 1.0


def diagnose_v5d_collection(recipes, renders, diagnostics) -> V5DCollectionDiagnostics:
    errors: list[str] = []
    warnings: list[str] = []
    if len(recipes) != 14 or len(renders) != 14:
        errors.append("V5D must contain exactly fourteen visible garments")
    roles = [recipe["articleRole"] for recipe in recipes]
    if len(set(roles)) != 14:
        errors.append("the fourteen requested article roles are not unique")
    rarities = {rarity: sum(recipe["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]["rarity"] == rarity for recipe in recipes) for rarity in ("Common", "Uncommon", "Rare")}
    if rarities != {"Common": 3, "Uncommon": 4, "Rare": 7}:
        errors.append(f"wrong requested rarity distribution: {rarities}")
    light_count = sum(recipe["lightPalette"] for recipe in recipes)
    if light_count < 3:
        errors.append(f"only {light_count} garments prove light/colorful masculine styling")
    for recipe, diagnostic in zip(recipes, diagnostics):
        errors.extend(f"{recipe['id']}: {message}" for message in diagnostic.errors)
        warnings.extend(f"{recipe['id']}: {message}" for message in diagnostic.warnings)
    signatures = [
        {recipe["articleRole"], recipe["articleSubtype"], recipe["sleeveIntent"], recipe["collarIntent"], recipe["openingIntent"], recipe["hemIntent"], recipe["surfacePlan"]["primaryGesture"], recipe["surfacePlan"]["panelSystem"], recipe["surfacePlan"]["trimSystem"]}
        for recipe in recipes
    ]
    closest = (0.0, None)
    for left in range(len(signatures)):
        for right in range(left + 1, len(signatures)):
            score = _jaccard(signatures[left], signatures[right])
            if score > closest[0]:
                closest = (score, (recipes[left]["id"], recipes[right]["id"]))
    if closest[0] > 0.55:
        errors.append(f"semantic cousins exceed diversity ceiling: {closest}")
    visual_signatures = [tuple((system, direction, x, y) for system in render.signal_cells for direction in DIRECTION_ORDER for x, y in sorted(render.signal_cells[system][direction])) for render in renders]
    if len(set(visual_signatures)) != 14:
        errors.append("two garments share an identical authored structural/surface signature")
    metrics = {
        "roleCount": len(set(roles)),
        "fashionFamilies": sorted({recipe["fashionFamily"] for recipe in recipes}),
        "rarityCounts": rarities,
        "lightOrColorfulCount": light_count,
        "closestSemanticPair": closest[1],
        "maximumSemanticJaccard": round(closest[0], 4),
        "uniqueVisualSignatures": len(set(visual_signatures)),
        "promotion": "EXPERIMENTAL",
        "beautyClaim": "HUMAN_REVIEW_REQUIRED",
    }
    return V5DCollectionDiagnostics(not errors, tuple(errors), tuple(warnings), metrics)
