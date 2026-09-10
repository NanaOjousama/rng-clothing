"""Static quality and contract guardrails for the V5C2 study batch.

These checks can reject broken masks and under-specified designs. They do not
claim runtime safety or artistic beauty; both still require in-game review.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER
from generator.v5c2.engine import load_v5c2_data, validate_v5c2_recipe


@dataclass(frozen=True)
class V5C2ArticleDiagnostics:
    passes: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict[str, Any]


@dataclass(frozen=True)
class V5C2CollectionDiagnostics:
    passes: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict[str, Any]


def _opaque(frame) -> frozenset[tuple[int, int]]:
    return frozenset((x, y) for y, row in enumerate(frame) for x, pixel in enumerate(row) if pixel[3])


def _signal_count(render, name: str, direction: str | None = None) -> int:
    views = render.signal_cells[name]
    return sum(len(views[d]) for d in ([direction] if direction else DIRECTION_ORDER))


def diagnose_v5c2_article(render) -> V5C2ArticleDiagnostics:
    recipe = render.recipe
    errors: list[str] = []
    warnings: list[str] = []
    result = validate_v5c2_recipe(recipe)
    errors.extend(result.errors)
    warnings.extend(result.warnings)
    if len(render.texture) != 64 or any(len(row) != 16 for row in render.texture):
        errors.append("shirt texture must contain four direct 16x16 frames in a 16x64 sheet")
    alpha = sorted({pixel[3] for row in render.texture for pixel in row})
    if any(value not in {0, 255} for value in alpha):
        errors.append(f"logical artwork has non-binary alpha: {alpha}")
    if any(render.coverage_missing.values()):
        errors.append(f"body coverage envelope has gaps: {render.coverage_missing}")
    if render.hide_native_sleeves:
        errors.append("V5C2 may not globally hide the arm/sleeve layer")
    if not render.companion_required or render.sleeves_texture is None:
        errors.append("every V5C2 diagnostic garment requires its coordinated full-motion Sleeves companion")
    elif len(render.sleeves_texture) != 1344 or any(len(row) != 384 for row in render.sleeves_texture):
        errors.append("custom Sleeves atlas must be 384x1344")
    article = recipe["articleType"]
    if article == "VEST_TOP":
        if _signal_count(render, "opening", "front") < 8 or _signal_count(render, "construction", "front") < 6:
            errors.append("waistcoat lacks a readable inner-shirt/V-opening construction signal")
    elif article == "BLOUSE":
        if _signal_count(render, "construction") < 30 or _signal_count(render, "motif", "front") < 3:
            errors.append("blouse lacks a wrapped yoke and attached focal cluster")
    elif article == "SWEATER":
        if _signal_count(render, "pattern") < 16 or _signal_count(render, "trim") < 16:
            errors.append("heritage knit lacks yoke/ribbing construction")
    elif article in {"CROPPED_JACKET", "STANDARD_JACKET"}:
        if _signal_count(render, "opening") < 20 or _signal_count(render, "pocket") < 12:
            errors.append("jacket lacks dominant opening and paired pocket structure")
        if article == "CROPPED_JACKET" and sum(len(c) for c in render.removed_cells.values()) < 8:
            errors.append("cropped jacket did not create a materially short silhouette")
    elif article == "HOODIE":
        if any(len(render.signal_cells["hood"][d]) < 18 for d in DIRECTION_ORDER):
            errors.append("hoodie hood mass is not readable in every direction")
        subtype = recipe["articleSubtype"]
        if subtype == "zip" and _signal_count(render, "opening", "front") < 16:
            errors.append("zip hoodie lacks a readable zipper/opening")
        if "pouch_pocket" in recipe["constructionFeatures"] and _signal_count(render, "pocket", "front") < 18:
            errors.append("pouch hoodie lacks a connected pouch construction")
        if subtype in {"cropped_charm", "baggy_crest"} and _signal_count(render, "motif", "front") < 8:
            errors.append("Rare reference-derived hoodie lacks a clustered original focal motif")
    # A design must remain authored before shading: construction/surface cells
    # are counted, but base-render lighting pixels are deliberately ignored.
    authored = sum(
        _signal_count(render, name)
        for name in ("construction", "opening", "pocket", "trim", "pattern", "motif", "hood")
    )
    rarity = recipe["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]["rarity"]
    floor = {"Common": 24, "Uncommon": 34, "Rare": 45}[rarity]
    if authored < floor:
        errors.append(f"{rarity} shading-independent design interest is too low ({authored} < {floor})")
    fixed_colors = sorted({pixel[:3] for frame in render.default_frames.values() for row in frame for pixel in row if pixel[3]})
    if len(fixed_colors) > 11:
        warnings.append(f"palette uses {len(fixed_colors)} visible colors; inspect for muddy role proliferation")
    metrics = {
        "articleType": article,
        "articleSubtype": recipe["articleSubtype"],
        "rarity": rarity,
        "logicalFrame": [16, 16],
        "scale": 2,
        "bodyPosition": [0, 32],
        "alphaValues": alpha,
        "opaqueCells": {direction: len(_opaque(render.frames[direction])) for direction in DIRECTION_ORDER},
        "signalCells": {name: {direction: len(render.signal_cells[name][direction]) for direction in DIRECTION_ORDER} for name in render.signal_cells},
        "authoredCells": authored,
        "visibleDefaultColors": len(fixed_colors),
        "missingCoverage": {direction: list(cells) for direction, cells in render.coverage_missing.items()},
        "hideNativeSleeves": render.hide_native_sleeves,
        "companionRequired": render.companion_required,
        "promotion": "EXPERIMENTAL",
        "runtimeClaim": "NOT_TESTED",
    }
    return V5C2ArticleDiagnostics(not errors, tuple(errors), tuple(warnings), metrics)


def diagnose_v5c2_collection(recipes, renders, diagnostics) -> V5C2CollectionDiagnostics:
    errors: list[str] = []
    warnings: list[str] = []
    if len(recipes) != 10 or len(renders) != 10:
        errors.append("V5C2 must contain exactly ten visible diagnostic garments")
    articles = {name: sum(r["articleType"] == name for r in recipes) for name in ("VEST_TOP", "BLOUSE", "SWEATER", "CROPPED_JACKET", "STANDARD_JACKET", "HOODIE")}
    expected = {"VEST_TOP": 1, "BLOUSE": 1, "SWEATER": 1, "CROPPED_JACKET": 1, "STANDARD_JACKET": 1, "HOODIE": 5}
    if articles != expected:
        errors.append(f"wrong V5C2 article distribution: {articles}")
    rarities = {rarity: sum(r["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]["rarity"] == rarity for r in recipes) for rarity in ("Common", "Uncommon", "Rare")}
    if rarities != {"Common": 2, "Uncommon": 4, "Rare": 4}:
        errors.append(f"unexpected rarity distribution: {rarities}")
    for recipe, diagnostic in zip(recipes, diagnostics):
        errors.extend(f"{recipe['id']}: {message}" for message in diagnostic.errors)
        warnings.extend(f"{recipe['id']}: {message}" for message in diagnostic.warnings)
    semantic = [
        (r["articleType"], r["articleSubtype"], r["fitIntent"], r["sleeveIntent"], r["necklineIntent"], r["openingIntent"], r["surfacePlan"]["composition"], r["surfacePlan"]["motif"])
        for r in recipes
    ]
    if len(set(semantic)) != 10:
        errors.append("exact semantic duplicate detected")
    silhouettes = [tuple((d, x, y) for d in DIRECTION_ORDER for x, y in sorted(_opaque(render.frames[d]))) for render in renders]
    unique_silhouettes = len(set(silhouettes))
    if unique_silhouettes < 5:
        errors.append(f"articles collapsed to only {unique_silhouettes} silhouettes")
    # Hoodie identity may share an outer footprint, but construction signatures
    # must not collapse to recolors.
    hoodie_signatures = []
    for recipe, render in zip(recipes, renders):
        if recipe["articleType"] == "HOODIE":
            hoodie_signatures.append(tuple((name, d, x, y) for name in ("hood", "opening", "pocket", "pattern", "motif") for d in DIRECTION_ORDER for x, y in sorted(render.signal_cells[name][d])))
    if len(set(hoodie_signatures)) != 5:
        errors.append("hoodie subtypes collapsed to duplicate structural/surface compositions")
    metrics = {
        "articleCounts": articles,
        "rarityCounts": rarities,
        "uniqueSemanticSignatures": len(set(semantic)),
        "uniqueSilhouettes": unique_silhouettes,
        "uniqueHoodieCompositions": len(set(hoodie_signatures)),
        "promotion": "EXPERIMENTAL",
        "beautyClaim": "HUMAN_REVIEW_REQUIRED",
    }
    return V5C2CollectionDiagnostics(not errors, tuple(errors), tuple(warnings), metrics)
