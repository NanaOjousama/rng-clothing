"""Guardrails for V4 article identity, rarity parity, and collection diversity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER
from generator.renderers.fashionsense.surface_v3 import diagnose_fs_v3


@dataclass(frozen=True)
class V4ArticleDiagnostics:
    passes: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict[str, Any]


@dataclass(frozen=True)
class V4CollectionDiagnostics:
    passes: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict[str, Any]


def diagnose_v4_article(render) -> V4ArticleDiagnostics:
    recipe = render.recipe; article = recipe["articleType"]
    errors: list[str] = []; warnings: list[str] = []
    v3 = diagnose_fs_v3(render.design)
    errors.extend(f"underlying V3: {value}" for value in v3.errors)
    warnings.extend(f"underlying V3: {value}" for value in v3.warnings)
    if any(render.coverage_missing.values()):
        errors.append("article translation broke required torso/shoulder coverage")
    removed = sum(len(v) for v in render.removed_cells.values())
    translated = sum(len(v) for v in render.translated_material_cells.values())
    max_y = {d: max(y for _, y in render.article_cells[d]) for d in DIRECTION_ORDER}
    row_widths = {d: [sum((x, y) in render.article_cells[d] for x in range(16)) for y in range(16)] for d in DIRECTION_ORDER}
    if article == "FITTED_SHIRT":
        if removed < 32 or any(row_widths[d][15] >= row_widths[d][9] for d in DIRECTION_ORDER):
            errors.append("fitted shirt did not produce a persistent lower-torso taper")
    elif article == "SWEATER_TOP":
        if recipe["designRecipe"]["archetype"] != "SWEATER" or any(y != 15 for y in max_y.values()):
            errors.append("sweater lost its full soft-mass termination")
    elif article == "VEST_TOP":
        if translated < 160:
            errors.append("vest material frame is too weak to separate from a normal shirt")
        if len(set(render.sleeve_colors)) < 3:
            errors.append("vest under-shirt sleeve ramp collapsed")
    elif article == "CROPPED_JACKET":
        if any(y != 13 for y in max_y.values()) or removed < 70:
            errors.append("cropped jacket does not terminate two logical rows above standard outerwear")
    elif article == "SHORT_OUTERWEAR":
        if any(y != 15 for y in max_y.values()):
            errors.append("short outerwear does not preserve the full proven shirt-layer length")
    # The name-removed classifier uses rendered evidence only.
    inferred = (
        "CROPPED_JACKET" if all(y == 13 for y in max_y.values()) else
        "VEST_TOP" if translated >= 160 else
        "FITTED_SHIRT" if removed >= 32 else
        "SWEATER_TOP" if render.design.recipe["archetype"] == "SWEATER" else
        "SHORT_OUTERWEAR"
    )
    if inferred != article:
        errors.append(f"name-removed article classifier read {inferred}, expected {article}")
    active = v3.metrics["activeSystems"]
    visible_surface = sum(
        1 for system in render.design.system_cells.values() for direction in DIRECTION_ORDER
        for x, y in system[direction] if (x, y) in render.article_cells[direction]
    )
    article_evidence = min(24, removed // 4 + translated // 12)
    quality = 10 + len(active) * 7 + min(22, visible_surface // 4) + article_evidence
    quality += {"Common": 0, "Uncommon": 5, "Rare": 10}[recipe["designRecipe"]["rarity"]]
    metrics = {
        "inferredArticle": inferred, "removedCells": removed, "translatedMaterialCells": translated,
        "maximumOccupiedY": max_y, "rowWidths": row_widths, "activeSurfaceSystems": active,
        "actualVisibleSurfaceCells": visible_surface, "qualityEvidenceIndex": quality,
        "underlyingV3Passes": v3.passes, "bodyCoveragePasses": not any(render.coverage_missing.values()),
    }
    return V4ArticleDiagnostics(not errors, tuple(errors), tuple(warnings), metrics)


def diagnose_v4_collection(recipes, renders, diagnostics, *, expected_counts: dict[str, int]) -> V4CollectionDiagnostics:
    errors: list[str] = []; warnings: list[str] = []
    if len(recipes) != sum(expected_counts.values()):
        errors.append("collection count differs from exact requested count")
    actual_counts = {rarity: sum(r["designRecipe"]["rarity"] == rarity for r in recipes) for rarity in expected_counts}
    if actual_counts != expected_counts:
        errors.append(f"rarity distribution is {actual_counts}, expected {expected_counts}")
    if any(not d.passes for d in diagnostics):
        errors.append("one or more article renders failed individual diagnostics")
    types = {r["articleType"] for r in recipes}
    if len(types) < 4:
        errors.append("collection uses fewer than four article types")
    if any(r["articleType"] == "LONG_OUTERWEAR" for r in recipes):
        errors.append("unproven long outerwear entered a V4 output collection")
    # Cross-article quality-tier parity. These are evidence bands, not beauty scores.
    by_rarity = {
        rarity: [d.metrics["qualityEvidenceIndex"] for r, d in zip(recipes, diagnostics) if r["designRecipe"]["rarity"] == rarity]
        for rarity in expected_counts
    }
    averages = {rarity: sum(values) / len(values) for rarity, values in by_rarity.items()}
    if not (averages["Common"] < averages["Uncommon"] < averages["Rare"]):
        errors.append(f"cross-article rarity evidence does not progress: {averages}")
    for rarity, values in by_rarity.items():
        if max(values) - min(values) > 28:
            warnings.append(f"{rarity} article quality evidence has a wide cross-article spread")
    signatures = []
    for recipe, diagnostic in zip(recipes, diagnostics):
        m = diagnostic.metrics
        signature = (recipe["articleType"], tuple(m["maximumOccupiedY"].values()), m["translatedMaterialCells"] > 0,
                     tuple(m["rowWidths"]["front"][9:16]))
        signatures.append(signature)
    if len(set(signatures)) < min(len(signatures), len(types) + 1):
        warnings.append("some same-article siblings share a silhouette signature; surface composition must carry their distinction")
    metrics = {"articleTypes": sorted(types), "rarityCounts": actual_counts, "qualityEvidenceByRarity": by_rarity,
               "averageQualityEvidenceByRarity": averages, "articleSignatures": [list(value) for value in signatures]}
    return V4CollectionDiagnostics(not errors, tuple(errors), tuple(warnings), metrics)

