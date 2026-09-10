"""AoTInspired profile adapter for the frozen Generator V3 architecture.

This module selects existing V3 semantic systems. It contains no pixels,
Fashion Sense positions, anchors, masks, or renderer branches.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from generator.v3.engine import active_surface_systems, design_signature, load_v3_data, validate_recipe_v3


ROOT = Path(__file__).resolve().parents[3]
PROFILE_PATH = ROOT / "style-profiles" / "AoTInspired" / "v3_profile.json"
COLLECTION_PATH = ROOT / "generator" / "data" / "v3" / "style_profiles" / "aot_inspired_collection.json"


@dataclass(frozen=True)
class AoTCollectionValidation:
    passes: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict[str, Any]


@dataclass(frozen=True)
class AoTRenderValidation:
    passes: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict[str, Any]


def load_aot_v3_profile() -> dict[str, Any]:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def _source() -> dict[str, Any]:
    return json.loads(COLLECTION_PATH.read_text(encoding="utf-8"))


def generate_aot_v3_collection() -> dict[str, Any]:
    source = _source(); recipes = []; concepts = []
    for index, item in enumerate(source["concepts"], 1):
        concept_record = {
            "id": item["id"], "garmentRole": item["concept"]["garmentRole"], "rarity": item["rarity"],
            "branch": item["branch"], "silhouetteGoal": item["concept"]["silhouetteGoal"],
            "primaryVisualGesture": item["concept"]["primaryGesture"], "secondaryVisualGesture": item["concept"]["secondaryGesture"],
            "focalArea": item["concept"]["focalArea"], "surfaceCompositionType": item["surfaceDesign"]["compositionType"],
            "colorStory": next(name for name, mapped in load_aot_v3_profile()["paletteStories"].items() if mapped == item["paletteStory"]),
            "renderPaletteStory": item["paletteStory"], "symmetryBias": item["concept"]["symmetryBias"],
            "designDensity": item["concept"]["designDensity"], "themeRecognitionTarget": item["themeRecognitionTarget"],
            "uniquenessTarget": item["uniquenessTarget"],
        }
        recipe = {
            "formatVersion": 3, "id": item["id"], "generationIndex": index,
            "seed": source["seed"] + index * 104729, "category": "Lifestyle", "styleProfile": "AoTInspired",
            "themeFamily": "formal_elegant" if item["branch"] in {"civilian_everyday", "dark_formal"} else "military_structured",
            "rarity": item["rarity"], "archetype": item["archetype"], "concept": item["concept"],
            "construction": item["construction"], "substantialFeatures": item["substantialFeatures"],
            "colorBlocking": item["colorBlocking"], "surfaceDesign": item["surfaceDesign"],
            "paletteStory": item["paletteStory"], "dyeable": True,
            "itemName": item["itemName"], "itemDescription": item["itemDescription"],
        }
        result = validate_recipe_v3(recipe)
        if not result.valid:
            raise ValueError(f"invalid AoT V3 concept {item['id']}: {'; '.join(result.errors)}")
        concepts.append(concept_record); recipes.append(recipe)
    collection = {
        "generatorVersion": source["generatorVersion"], "profile": source["profile"], "seed": source["seed"],
        "count": len(recipes), "hiddenCandidateCount": 0,
        "rarityCounts": {rarity: sum(recipe["rarity"] == rarity for recipe in recipes) for rarity in ("Common", "Uncommon", "Rare")},
        "designConcepts": concepts, "recipes": recipes,
    }
    validation = validate_aot_v3_collection(collection)
    if not validation.passes:
        raise ValueError("invalid AoT V3 collection: " + "; ".join(validation.errors))
    return collection


def _similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    a = design_signature(left); b = design_signature(right)
    return sum(x == y for x, y in zip(a, b)) / len(a)


def validate_aot_v3_collection(collection: dict[str, Any]) -> AoTCollectionValidation:
    profile = load_aot_v3_profile(); errors: list[str] = []; warnings: list[str] = []
    recipes = collection["recipes"]; concepts = collection["designConcepts"]
    if len(recipes) != 6 or collection.get("hiddenCandidateCount") != 0:
        errors.append("AoT V3 test must expose exactly six concepts and no hidden candidate pool")
    rarity_counts = {rarity: sum(recipe["rarity"] == rarity for recipe in recipes) for rarity in ("Common", "Uncommon", "Rare")}
    if rarity_counts != {"Common": 2, "Uncommon": 2, "Rare": 2}:
        errors.append(f"expected 2/2/2 rarity distribution, found {rarity_counts}")
    allowed = profile["surfaceVocabulary"]
    for recipe, concept in zip(recipes, concepts):
        result = validate_recipe_v3(recipe)
        errors.extend(f"{recipe['id']}: {message}" for message in result.errors)
        if recipe["styleProfile"] != "AoTInspired": errors.append(f"{recipe['id']}: wrong style profile")
        if recipe["colorBlocking"]["type"] != "none" and recipe["colorBlocking"]["type"] not in allowed["colorBlocks"]:
            errors.append(f"{recipe['id']}: color block outside profile vocabulary")
        trim = recipe["surfaceDesign"]["trim"]["type"]
        if trim != "none" and trim not in allowed["trims"]: errors.append(f"{recipe['id']}: trim outside profile vocabulary")
        pattern = recipe["surfaceDesign"]["pattern"]["type"]
        if pattern != "none" and pattern not in allowed["patterns"]: errors.append(f"{recipe['id']}: pattern outside profile vocabulary")
        motif = recipe["surfaceDesign"]["motif"]["family"]
        if motif != "none" and motif not in allowed["motifs"]: errors.append(f"{recipe['id']}: motif outside profile vocabulary")
        expected_systems = {"Common": 1, "Uncommon": 2, "Rare": 3}[recipe["rarity"]]
        if len(active_surface_systems(recipe)) != expected_systems: errors.append(f"{recipe['id']}: wrong rarity surface-system count")
        if concept["themeRecognitionTarget"] not in profile["branches"][concept["branch"]]["recognitionRange"]:
            errors.append(f"{recipe['id']}: recognition target outside branch range")

    iconic = next((recipe for recipe in recipes if recipe["id"] == "aot-v3-05"), None)
    if iconic is None:
        errors.append("missing required iconic Rare 1")
    else:
        required = {
            "archetype": iconic["archetype"] == "JACKET",
            "wideCollar": iconic["construction"]["collar"] == "wide",
            "splitShell": iconic["construction"]["panelLayout"] == "split_outer_panels",
            "innerLayer": iconic["construction"]["layering"] == "visible_inner_layer",
            "structuredWaist": iconic["construction"]["hem"] == "structured",
            "lapel": iconic["surfaceDesign"]["trim"]["type"] == "lapel_trim",
            "shoulderPanel": iconic["colorBlocking"]["type"] == "shoulder_block",
            "originalCrest": iconic["surfaceDesign"]["motif"]["family"] == "star",
            "crestPlacement": iconic["surfaceDesign"]["motif"]["topology"] == "asymmetric_front",
            "controlledSystems": set(active_surface_systems(iconic)) == {"color_block", "trim", "motif"},
        }
        if not all(required.values()): errors.append(f"iconic Rare 1 misses required compound cues: {required}")

    pairwise = []
    for i in range(len(recipes)):
        for j in range(i + 1, len(recipes)):
            value = _similarity(recipes[i], recipes[j])
            pairwise.append({"left": recipes[i]["id"], "right": recipes[j]["id"], "semanticSimilarity": round(value, 4)})
            if value >= 0.75: errors.append(f"{recipes[i]['id']} and {recipes[j]['id']} are semantic near-clones ({value:.2f})")
    rare1 = next(recipe for recipe in recipes if recipe["id"] == "aot-v3-05")
    rare2 = next(recipe for recipe in recipes if recipe["id"] == "aot-v3-06")
    rare_differences = sum(a != b for a, b in zip(design_signature(rare1), design_signature(rare2)))
    if rare_differences < 6: errors.append("Rare 2 is insufficiently distinct from iconic Rare 1")
    metrics = {
        "rarityCounts": rarity_counts,
        "branches": sorted({concept["branch"] for concept in concepts}),
        "archetypes": sorted({recipe["archetype"] for recipe in recipes}),
        "compositionTypes": sorted({recipe["surfaceDesign"]["compositionType"] for recipe in recipes}),
        "focalAreas": sorted({recipe["concept"]["focalArea"] for recipe in recipes}),
        "paletteStories": sorted({recipe["paletteStory"] for recipe in recipes}),
        "maximumSemanticSimilarity": max((pair["semanticSimilarity"] for pair in pairwise), default=0),
        "rareSignatureDifferences": rare_differences,
        "pairwise": pairwise,
    }
    return AoTCollectionValidation(not errors, tuple(errors), tuple(warnings), metrics)


def _render_surface_mask(render: Any, directions: tuple[str, ...]) -> set[tuple[str, int, int]]:
    return {
        (direction, x, y)
        for direction in directions
        for y, row in enumerate(render.surface_roles[direction])
        for x, role in enumerate(row)
        if role is not None
    }


def _jaccard(left: set[tuple[str, int, int]], right: set[tuple[str, int, int]]) -> float:
    union = left | right
    return 0.0 if not union else len(left & right) / len(union)


def validate_aot_v3_renders(
    collection: dict[str, Any], renders: list[Any], diagnostics: list[Any]
) -> AoTRenderValidation:
    """Apply collection-specific render and diversity gates without changing V3."""

    errors: list[str] = []; warnings: list[str] = []
    art_profiles = load_aot_v3_profile()["rarityArtProfiles"]
    recipes = collection["recipes"]
    if len(renders) != 6 or len(diagnostics) != 6:
        errors.append("AoT V3 render gate requires exactly six visible garments")
    for recipe, render, diagnostic in zip(recipes, renders, diagnostics):
        errors.extend(f"{recipe['id']}: {message}" for message in diagnostic.errors)
        warnings.extend(f"{recipe['id']}: {message}" for message in diagnostic.warnings)
        if any(diagnostic.metrics["bodyCoverageMissing"].values()):
            errors.append(f"{recipe['id']}: body-coverage envelope regression")
        if recipe["rarity"] in {"Uncommon", "Rare"} and not diagnostic.metrics["designInterestWithoutShading"]:
            errors.append(f"{recipe['id']}: surface composition collapses without shading")
        if recipe["rarity"] == "Rare" and len(diagnostic.metrics["activeSystems"]) != 3:
            errors.append(f"{recipe['id']}: Rare must visibly coordinate three surface systems")

        art = art_profiles[recipe["rarity"]]
        counts = diagnostic.metrics["systemCells"]
        visible = diagnostic.metrics["visibleSurfaceCells"]
        colors = diagnostic.metrics["surfaceColors"]
        if len(diagnostic.metrics["activeSystems"]) != art["activeSystems"]:
            errors.append(f"{recipe['id']}: wrong active-system count for AoT rarity art profile")
        if visible["front"] < art["minimumFrontSurfaceCells"]:
            errors.append(f"{recipe['id']}: front falls below {recipe['rarity']} visual-richness floor")
        if visible["front"] > art["maximumFrontSurfaceCells"]:
            errors.append(f"{recipe['id']}: front exceeds {recipe['rarity']} complexity ceiling")
        if colors > art["maximumSurfaceColors"]:
            errors.append(f"{recipe['id']}: surface colors exceed {recipe['rarity']} art-profile ceiling")
        if "minimumThemedViews" in art and diagnostic.metrics["themedViews"] < art["minimumThemedViews"]:
            errors.append(f"{recipe['id']}: insufficient directional identity for {recipe['rarity']}")
        motif_front = counts["motif"]["front"]
        if "maximumMotifCellsPerFront" in art and motif_front > art["maximumMotifCellsPerFront"]:
            errors.append(f"{recipe['id']}: emblem exceeds {recipe['rarity']} prominence ceiling")

        if recipe["rarity"] == "Rare":
            if visible["back"] < art["minimumBackSurfaceCells"] or visible["back"] > art["maximumBackSurfaceCells"]:
                errors.append(f"{recipe['id']}: back falls outside controlled Rare richness range")
            if min(visible["left"], visible["right"]) < art["minimumSideSurfaceCells"]:
                errors.append(f"{recipe['id']}: Rare side treatment is too empty")
            focal_cells = max(
                counts["motif"]["front"], counts["pattern"]["front"], counts["pattern"]["back"]
            )
            if focal_cells < art["minimumVisibleFocalCells"]:
                errors.append(f"{recipe['id']}: Rare lacks a renderer-visible focal feature")
            supports = recipe["surfaceDesign"]["supportSystems"]
            substantial_support = max(
                max(counts[system]["front"], counts[system]["back"]) for system in supports
            )
            if substantial_support < art["minimumVisibleSecondaryCells"]:
                errors.append(f"{recipe['id']}: Rare lacks a substantial secondary design region")
            if max(counts["trim"].values()) < art["minimumFinishingCells"]:
                errors.append(f"{recipe['id']}: Rare lacks coordinated finishing treatment")
            if counts["motif"]["front"] and counts["pattern"]["front"]:
                errors.append(f"{recipe['id']}: Rare activates both motif and pattern on front; reserve that density for future tiers")

    pairwise = []
    all_masks = [_render_surface_mask(render, ("front", "back", "left", "right")) for render in renders]
    side_masks = [_render_surface_mask(render, ("left", "right")) for render in renders]
    for left in range(len(renders)):
        for right in range(left + 1, len(renders)):
            surface = _jaccard(all_masks[left], all_masks[right])
            side = _jaccard(side_masks[left], side_masks[right])
            pairwise.append({
                "left": recipes[left]["id"], "right": recipes[right]["id"],
                "surfaceMaskJaccard": round(surface, 4), "sideMaskJaccard": round(side, 4),
            })
            same_archetype = recipes[left]["archetype"] == recipes[right]["archetype"]
            if surface >= (0.80 if same_archetype else 0.88):
                errors.append(f"{recipes[left]['id']} and {recipes[right]['id']} collapse to nearly identical surface placement")
            if same_archetype and side >= 0.88:
                errors.append(f"{recipes[left]['id']} and {recipes[right]['id']} have an insufficiently distinct side read")

    rare_renders = [render for recipe, render in zip(recipes, renders) if recipe["rarity"] == "Rare"]
    rare_side_templates = [render.base.side_template for render in rare_renders]
    if len(set(rare_side_templates)) < 2:
        warnings.append("the two Rare jackets share a base side template; surface and closure differences require visual review")
    metrics = {
        "maximumSurfaceMaskJaccard": max((pair["surfaceMaskJaccard"] for pair in pairwise), default=0),
        "maximumSideMaskJaccard": max((pair["sideMaskJaccard"] for pair in pairwise), default=0),
        "rareSideTemplates": rare_side_templates,
        "rarityArtProfiles": art_profiles,
        "garmentArtBudgets": {
            recipe["id"]: {
                "rarity": recipe["rarity"],
                "frontSurfaceCells": diagnostic.metrics["visibleSurfaceCells"]["front"],
                "backSurfaceCells": diagnostic.metrics["visibleSurfaceCells"]["back"],
                "minimumSideSurfaceCells": min(
                    diagnostic.metrics["visibleSurfaceCells"]["left"],
                    diagnostic.metrics["visibleSurfaceCells"]["right"],
                ),
                "surfaceColors": diagnostic.metrics["surfaceColors"],
                "frontMotifCells": diagnostic.metrics["systemCells"]["motif"]["front"],
                "frontPatternCells": diagnostic.metrics["systemCells"]["pattern"]["front"],
            }
            for recipe, diagnostic in zip(recipes, diagnostics)
        },
        "pairwise": pairwise,
    }
    return AoTRenderValidation(not errors, tuple(errors), tuple(warnings), metrics)
