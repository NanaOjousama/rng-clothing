"""Three-grammar semantic adapter into the proven V5/HD render stack.

This module is deliberately not a renderer. It selects and configures existing
V5 construction programs, preserves their HD mask/exposure/gesture output,
runs the post-V5E polish pass, and then resolves those shade roles through the
new semantic palette and material specifications.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from generator.controlled_test.engine import generate_controlled_test_recipes
from generator.png_utils import RGBA, blank_image
from generator.renderers.fashionsense.art_polish_v5e import (
    polish_open_cardigan_premium_execution,
    polish_upper_frames,
    refine_open_cardigan_premium_construction,
    soften_shared_rear_neck,
)
from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER
from generator.renderers.fashionsense.upper_v5b import _coverage_missing, _stack, _story, render_fs_v5b
from generator.renderers.fashionsense.upper_v5c2 import _reset_v3_surface
from generator.renderers.fashionsense.upper_v5d import render_fs_v5d
from generator.v5b.engine import generate_v5b_benchmark, validate_v5b_recipe
from generator.v5d.engine import generate_v5d_batch, validate_v5d_recipe


SUPPORTED = ("FITTED_TEE", "OPEN_CARDIGAN", "WORK_JACKET")
MASK_ROLE_BY_VALUE = {
    48: "EXTERIOR_CONTOUR",
    72: "DEEP_CREASE",
    104: "STRUCTURAL_EDGE",
    136: "SHADOW",
    184: "BASE",
    224: "LIGHT",
    244: "OPTIONAL_HIGHLIGHT",
}

# These values interpret the written material behaviors as palette-ramp
# spacing. They change colors assigned to the proven shade-role geometry; they
# do not create or reposition art cells.
MATERIAL_RAMP_POLICY = {
    "COTTON_TEE": {"shadowTowardFabric": 0.48, "lightTowardLight": 0.58, "secondaryShadowTowardFabric": 0.42},
    "WOVEN_SHIRT": {"shadowTowardFabric": 0.43, "lightTowardLight": 0.66, "secondaryShadowTowardFabric": 0.40},
    "KNIT": {"shadowTowardFabric": 0.62, "lightTowardLight": 0.48, "secondaryShadowTowardFabric": 0.56},
    "CARDIGAN": {"shadowTowardFabric": 0.64, "lightTowardLight": 0.46, "secondaryShadowTowardFabric": 0.58},
    "DENIM_WORKWEAR": {"shadowTowardFabric": 0.34, "lightTowardLight": 0.76, "secondaryShadowTowardFabric": 0.38},
    "SPORT_SHELL": {"shadowTowardFabric": 0.38, "lightTowardLight": 0.72, "secondaryShadowTowardFabric": 0.36},
    # Direct interpretations of the already-approved material specification.
    # These extend semantic color resolution only; no geometry or raster stage
    # is introduced here.
    "SWEATSHIRT": {"shadowTowardFabric": 0.56, "lightTowardLight": 0.52, "secondaryShadowTowardFabric": 0.50},
    "UTILITY_SHELL": {"shadowTowardFabric": 0.36, "lightTowardLight": 0.70, "secondaryShadowTowardFabric": 0.38},
    "BOMBER_OUTERWEAR": {"shadowTowardFabric": 0.40, "lightTowardLight": 0.68, "secondaryShadowTowardFabric": 0.38},
    "BLAZER_FORMAL": {"shadowTowardFabric": 0.40, "lightTowardLight": 0.72, "secondaryShadowTowardFabric": 0.36},
    "CEREMONIAL_FABRIC": {"shadowTowardFabric": 0.38, "lightTowardLight": 0.76, "secondaryShadowTowardFabric": 0.34},
}


@dataclass(frozen=True)
class ControlledHDAdapterRender:
    recipe: dict[str, Any]
    backend_recipe: dict[str, Any]
    backend: str
    stage_trace: tuple[str, ...]
    mask_frames: dict[str, list[list[RGBA]]]
    frames: dict[str, list[list[RGBA]]]
    role_frames: dict[str, list[list[str | None]]]
    texture: list[list[RGBA]]
    sleeve_colors: tuple[tuple[int, int, int], ...]
    construction_signals: dict[str, dict[str, frozenset[tuple[int, int]]]]
    coverage_missing: dict[str, tuple[tuple[int, int], ...]]
    polish_metrics: dict[str, Any]
    palette_ramps: dict[str, dict[str, RGBA]]
    material_evidence: dict[str, Any]
    execution_profile: str


def _rgba(value: str) -> RGBA:
    value = value.lstrip("#")
    return int(value[:2], 16), int(value[2:4], 16), int(value[4:6], 16), 255


def _blend(left: RGBA, right: RGBA, amount: float) -> RGBA:
    return tuple(round(left[i] + (right[i] - left[i]) * amount) for i in range(3)) + (255,)


def _semantic_recipe(grammar_id: str) -> dict[str, Any]:
    return copy.deepcopy(next(recipe for recipe in generate_controlled_test_recipes() if recipe["grammarId"] == grammar_id))


def _tee_backend_recipe() -> dict[str, Any]:
    recipe = copy.deepcopy(generate_v5b_benchmark()["recipes"][0])
    recipe["id"] = "v5b-91"
    recipe["baseArticleRecipe"]["designRecipe"]["itemName"] = "Orchard Bound Tee"
    recipe["baseArticleRecipe"]["designRecipe"]["itemDescription"] = "A fitted spring-green tee with a clean bound neck and disciplined fabric planes."
    validation = validate_v5b_recipe(recipe)
    if not validation.valid:
        raise ValueError("invalid fitted-tee backend: " + "; ".join(validation.errors))
    return recipe


def _cardigan_backend_recipe() -> dict[str, Any]:
    recipe = copy.deepcopy(generate_v5d_batch()["recipes"][4])
    recipe["id"] = "v5d-95"
    recipe["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]["itemName"] = "Lavender Hearth Cardigan"
    validation = validate_v5d_recipe(recipe)
    if not validation.valid:
        raise ValueError("invalid cardigan backend: " + "; ".join(validation.errors))
    return recipe


def _work_jacket_backend_recipe() -> dict[str, Any]:
    v5b = generate_v5b_benchmark()["recipes"]
    recipe = copy.deepcopy(generate_v5d_batch()["recipes"][1])
    recipe.update({
        "id": "v5d-96",
        "articleSubtype": "boxy_work_jacket",
        "fitIntent": "regular",
        "sleeveIntent": "FITTED_LONG_SLEEVE",
        "shoulderIntent": "standard",
        "necklineIntent": "open",
        "collarIntent": "shirt_collar",
        "openingIntent": "buttoned",
        "layeringIntent": "single_layer",
        "hemIntent": "structured",
    })
    base = copy.deepcopy(v5b[8])
    base.update({
        "id": "v5b-96",
        "articleType": "STANDARD_JACKET",
        "constructionVariant": "utility_jacket",
        "sleeveIntent": "FITTED_LONG_SLEEVE",
        "shoulderIntent": "standard",
        "necklineIntent": "open",
        "collarIntent": "shirt_collar",
        "layeringIntent": "single_layer",
        # V5B correctly requires an outerwear opening. V5D's WORK_SHIRT
        # construction then rebuilds that carrier as a firm work placket.
        "openingIntent": "center_open",
    })
    base["baseArticleRecipe"]["designRecipe"]["itemName"] = "Indigo Foundry Work Jacket"
    recipe["baseUpperRecipe"] = base
    validation = validate_v5d_recipe(recipe)
    if not validation.valid:
        raise ValueError("invalid work-jacket backend: " + "; ".join(validation.errors))
    return recipe


def _permanent_from_base(base):
    current = base
    for _ in range(8):
        if hasattr(current, "config") and hasattr(current, "regions") and hasattr(current, "edge_exposure"):
            return current
        if hasattr(current, "base"):
            current = current.base
        elif hasattr(current, "design"):
            current = current.design
        else:
            break
    raise TypeError("could not find FSPermanentGarmentRender in proven backend chain")


def _remove_closed_opening_from_hd_regions(base, frames, defaults) -> int:
    """Translate a BUTTON_SHIRT foundation into a closed tee fabric plane.

    Coordinates come from the proven HD semantic region model. The adapter
    removes the PLACKET carrier and its immediately adjacent crease, sampling
    the existing lit/shadow fabric on the corresponding side. It introduces no
    new shade geometry.
    """
    permanent = _permanent_from_base(base)
    changed = 0
    for direction in DIRECTION_ORDER:
        for y, region_row in enumerate(permanent.regions[direction]):
            placket = [x for x, region in enumerate(region_row) if region == "PLACKET" and frames[direction][y][x][3]]
            if not placket:
                continue
            lo, hi = min(placket), max(placket)
            body = [x for x, region in enumerate(region_row) if region == "BODY" and frames[direction][y][x][3]]
            left = [x for x in body if x < lo - 1]
            right = [x for x in body if x > hi + 1]
            left_source = max(left) if left else min(body)
            right_source = min(right) if right else max(body)
            targets = set(placket)
            for neighbor in (lo - 1, hi + 1):
                if neighbor in body and frames[direction][y][neighbor][0] in {72, 104}:
                    targets.add(neighbor)
            midpoint = (lo + hi) / 2
            for x in targets:
                source = left_source if x <= midpoint else right_source
                frames[direction][y][x] = frames[direction][y][source]
                defaults[direction][y][x] = defaults[direction][y][source]
                changed += 1
    return changed


def _palette_ramps(recipe: dict[str, Any]) -> dict[str, dict[str, RGBA]]:
    story = recipe["paletteStory"]["roles"]
    policy = MATERIAL_RAMP_POLICY[recipe["materialId"]]
    deep = _rgba(story["DeepShadow"])
    structural = _rgba(story["StructuralDark"])
    primary = _rgba(story["PrimaryFabric"])
    primary_light = _rgba(story["PrimaryFabricLight"])
    secondary = _rgba(story.get("SecondaryFabric", story["PrimaryFabric"] ))
    trim = _rgba(story.get("Trim", story["StructuralDark"]))
    accent = _rgba(story.get("Accent", story.get("Trim", story["StructuralDark"])))
    primary_ramp = {
        "EXTERIOR_CONTOUR": deep,
        "DEEP_CREASE": _blend(deep, structural, 0.55),
        "STRUCTURAL_EDGE": structural,
        "SHADOW": _blend(structural, primary, policy["shadowTowardFabric"]),
        "BASE": primary,
        "LIGHT": _blend(primary, primary_light, policy["lightTowardLight"]),
        "OPTIONAL_HIGHLIGHT": primary_light,
    }
    secondary_ramp = {
        "EXTERIOR_CONTOUR": deep,
        "DEEP_CREASE": _blend(deep, structural, 0.62),
        "STRUCTURAL_EDGE": structural,
        "SHADOW": _blend(structural, secondary, policy["secondaryShadowTowardFabric"]),
        "BASE": secondary,
        "LIGHT": _blend(secondary, primary_light, 0.42 if recipe["materialId"] == "CARDIGAN" else 0.30),
        "OPTIONAL_HIGHLIGHT": _blend(secondary, primary_light, 0.64),
    }
    trim_ramp = {
        "SHADOW": _blend(structural, trim, 0.48),
        "BASE": trim,
        "LIGHT": _blend(trim, primary_light, 0.42),
    }
    return {"PrimaryFabric": primary_ramp, "SecondaryFabric": secondary_ramp, "Trim": trim_ramp, "Accent": {"BASE": accent}}


def _old_fixed_role(pixel: RGBA, old_story: dict[str, Any]) -> str:
    candidates = {
        "secondary": tuple(old_story["secondary"]) + (255,),
        "accent": tuple(old_story["accent"]) + (255,),
        "lightAccent": tuple(old_story["lightAccent"]) + (255,),
        "darkAccent": tuple(old_story["darkAccent"]) + (255,),
    }
    exact = [name for name, color in candidates.items() if pixel == color]
    if exact:
        return exact[0]
    return min(candidates, key=lambda name: sum((pixel[i] - candidates[name][i]) ** 2 for i in range(3)))


def _secondary_shade(direction: str, x: int, y: int) -> str:
    if y <= 4 and x <= 7:
        return "LIGHT"
    if y >= 10 or x >= 10:
        return "SHADOW"
    return "BASE"


def _resolve_frames(recipe, base, polished, signals, *, execution_profile: str):
    ramps = _palette_ramps(recipe)
    old_story = _story(base)
    resolved: dict[str, list[list[RGBA]]] = {}
    role_frames: dict[str, list[list[str | None]]] = {}
    fixed_counts: dict[str, int] = {"secondary": 0, "accent": 0, "lightAccent": 0, "darkAccent": 0}
    shade_counts: dict[str, int] = {role: 0 for role in MASK_ROLE_BY_VALUE.values()}
    grammar = recipe["grammarId"]
    for direction in DIRECTION_ORDER:
        frame = blank_image(16, 16)
        role_frame: list[list[str | None]] = [[None] * 16 for _ in range(16)]
        for y, row in enumerate(polished.frames[direction]):
            for x, pixel in enumerate(row):
                if not pixel[3]:
                    continue
                if execution_profile in {"PREMIUM_CARDIGAN_V1", "PREMIUM_CONSTRUCTION_CARDIGAN_V1"}:
                    cell = (x, y)
                    layer_cells = signals.get("layering", {}).get(direction, set())
                    opening_cells = signals.get("opening", {}).get(direction, set())
                    collar_cells = signals.get("collar", {}).get(direction, set())
                    if cell in layer_cells:
                        shade = _secondary_shade(direction, x, y)
                        if direction == "front" and y == 2:
                            shade = "SHADOW"
                        elif direction == "front" and y <= 5 and x <= 7:
                            shade = "LIGHT"
                        elif direction == "front" and y <= 12:
                            shade = "BASE"
                        elif direction == "front":
                            shade = "SHADOW"
                        frame[y][x] = ramps["SecondaryFabric"][shade]
                        role_frame[y][x] = f"SecondaryFabric.{shade}"
                        continue
                    if cell in opening_cells or cell in collar_cells:
                        shade = "BASE"
                        if cell in opening_cells:
                            if direction == "front":
                                peers = [cx for cx, cy in opening_cells if cy == y]
                                shade = "LIGHT" if x == min(peers) and y <= 8 else "SHADOW" if x == max(peers) else "BASE"
                            else:
                                shade = "SHADOW" if direction == "right" else "LIGHT"
                        elif cell in collar_cells:
                            shade = "LIGHT" if x <= 7 else "SHADOW" if x >= 9 else "BASE"
                        frame[y][x] = ramps["Trim"][shade]
                        role_frame[y][x] = f"Trim.{shade}"
                        continue
                if pixel[0] == pixel[1] == pixel[2] and pixel[0] in MASK_ROLE_BY_VALUE:
                    shade = MASK_ROLE_BY_VALUE[pixel[0]]
                    frame[y][x] = ramps["PrimaryFabric"][shade]
                    role_frame[y][x] = f"PrimaryFabric.{shade}"
                    shade_counts[shade] += 1
                    continue
                fixed = _old_fixed_role(pixel, old_story)
                fixed_counts[fixed] += 1
                if grammar == "OPEN_CARDIGAN":
                    fabric = "SecondaryFabric" if fixed == "lightAccent" else "Trim" if fixed in {"secondary", "darkAccent"} else "Accent"
                elif grammar == "WORK_JACKET":
                    fabric = "SecondaryFabric" if fixed == "secondary" else "PrimaryFabric" if fixed == "lightAccent" else "Trim" if fixed == "darkAccent" else "Accent"
                else:
                    fabric = "Trim" if fixed in {"secondary", "darkAccent"} else "PrimaryFabric" if fixed == "lightAccent" else "Accent"
                shade = _secondary_shade(direction, x, y) if fabric in {"PrimaryFabric", "SecondaryFabric"} else "BASE"
                if execution_profile in {"PREMIUM_CARDIGAN_V1", "PREMIUM_CONSTRUCTION_CARDIGAN_V1"} and fabric == "Trim":
                    cell = (x, y)
                    if cell in signals.get("opening", {}).get(direction, set()):
                        if direction == "front":
                            peers = [cx for cx, cy in signals["opening"]["front"] if cy == y]
                            shade = "LIGHT" if x == min(peers) and y <= 8 else "SHADOW" if x == max(peers) else "BASE"
                        else:
                            shade = "SHADOW" if direction == "right" else "LIGHT"
                    elif cell in signals.get("collar", {}).get(direction, set()):
                        shade = "LIGHT" if x <= 7 else "SHADOW" if x >= 9 else "BASE"
                frame[y][x] = ramps[fabric][shade]
                role_frame[y][x] = f"{fabric}.{shade}"
        resolved[direction] = frame
        role_frames[direction] = role_frame

    policy = MATERIAL_RAMP_POLICY[recipe["materialId"]]
    generic = {"shadowTowardFabric": 0.50, "lightTowardLight": 0.60, "secondaryShadowTowardFabric": 0.50}
    changed_roles = [key for key in policy if policy[key] != generic[key]]
    affected = sum(shade_counts[name] for name in ("SHADOW", "LIGHT", "OPTIONAL_HIGHLIGHT"))
    evidence = {
        "materialId": recipe["materialId"],
        "policy": policy,
        "genericComparison": generic,
        "materialSpecificPolicyFields": changed_roles,
        "materialAffectedShadeCells": affected,
        "provenMaskShadeCounts": shade_counts,
        "translatedFixedRoleCounts": fixed_counts,
        "pixelLevelEvidence": affected > 0 and bool(changed_roles),
    }
    return resolved, role_frames, ramps, evidence


def _freeze_signals(signals):
    if not signals:
        return {}
    return {name: {direction: frozenset(cells) for direction, cells in views.items()} for name, views in signals.items()}


def render_controlled_hd_adapter(
    grammar_id: str,
    *,
    soften_back_neck: bool = True,
    execution_profile: str = "BASELINE",
) -> ControlledHDAdapterRender:
    if grammar_id not in SUPPORTED:
        raise ValueError(f"HD adapter is bounded to {SUPPORTED}; got {grammar_id}")
    if execution_profile not in {"BASELINE", "PREMIUM_CARDIGAN_V1", "PREMIUM_CONSTRUCTION_CARDIGAN_V1"}:
        raise ValueError(f"unsupported execution profile {execution_profile!r}")
    if execution_profile != "BASELINE" and grammar_id != "OPEN_CARDIGAN":
        raise ValueError("the premium execution proof is bounded to OPEN_CARDIGAN")
    recipe = _semantic_recipe(grammar_id)
    if grammar_id == "FITTED_TEE":
        backend_recipe = _tee_backend_recipe()
        raw = render_fs_v5b(backend_recipe)
        # Existing V5C2 helper restores the underlying HD role field and keeps
        # V5B's body/neckline modifications. It removes inherited V3 surface
        # decoration without inventing a replacement renderer.
        source_frames = {d: [list(row) for row in raw.frames[d]] for d in DIRECTION_ORDER}
        source_defaults = {d: [list(row) for row in raw.default_frames[d]] for d in DIRECTION_ORDER}
        _reset_v3_surface(raw, source_frames, source_defaults)
        # Resetting inherited surface art exposes the BUTTON_SHIRT foundation's
        # structural placket. Translate its semantic PLACKET region back into
        # the adjacent proven light/shadow fabric planes for a closed tee.
        _remove_closed_opening_from_hd_regions(raw, source_frames, source_defaults)
        base = raw
        backend = "V5B_PLAIN_TEE_OVER_RENDER_FS_HD_V2"
        signals = {}
        coverage = raw.coverage_missing
        trace = ("render_fs_hd_v2", "render_fs_v3_surface", "render_fs_v4", "render_fs_v5b", "reset_v3_surface", "adapter.closed_opening_from_hd_regions", "polish_upper_frames", "semantic_palette_material_adapter")
    elif grammar_id == "OPEN_CARDIGAN":
        backend_recipe = _cardigan_backend_recipe()
        raw = render_fs_v5d(backend_recipe)
        source_frames, source_defaults = raw.frames, raw.default_frames
        base = raw.base
        backend = "V5D_CARDIGAN_OVER_V5B_HD"
        signals = raw.signal_cells
        coverage = raw.coverage_missing
        trace = ("render_fs_hd_v2", "render_fs_v3_surface", "render_fs_v4", "render_fs_v5b", "render_fs_v5d.CARDIGAN", "polish_upper_frames", "semantic_palette_material_adapter")
    else:
        backend_recipe = _work_jacket_backend_recipe()
        raw = render_fs_v5d(backend_recipe)
        source_frames, source_defaults = raw.frames, raw.default_frames
        base = raw.base
        backend = "V5D_WORKWEAR_PROGRAM_OVER_STANDARD_JACKET_HD"
        signals = raw.signal_cells
        coverage = raw.coverage_missing
        trace = ("render_fs_hd_v2", "render_fs_v3_surface", "render_fs_v4.SHORT_OUTERWEAR", "render_fs_v5b.utility_jacket", "render_fs_v5d.WORK_SHIRT_CONSTRUCTION", "polish_upper_frames", "semantic_palette_material_adapter")

    signals = {
        system: {direction: set(cells) for direction, cells in views.items()}
        for system, views in signals.items()
    }

    # This assertion is the adapter's proof that the permanent HD region and
    # edge-exposure object really exists underneath the selected V5 route.
    _permanent_from_base(base)
    polished = polish_upper_frames(base, source_frames, source_defaults, article_family=grammar_id)
    if soften_back_neck:
        protected_back = frozenset(
            cell
            for system in signals.values()
            for cell in system.get("back", ())
        )
        polished = soften_shared_rear_neck(base, polished, protected_cells=protected_back)
        trace = trace[:-1] + ("soften_shared_rear_neck", trace[-1])
    if execution_profile in {"PREMIUM_CARDIGAN_V1", "PREMIUM_CONSTRUCTION_CARDIGAN_V1"}:
        polished = polish_open_cardigan_premium_execution(base, polished, signal_cells=signals)
        trace = trace[:-1] + ("polish_open_cardigan_premium_execution", trace[-1])
    if execution_profile == "PREMIUM_CONSTRUCTION_CARDIGAN_V1":
        polished = refine_open_cardigan_premium_construction(base, polished, signal_cells=signals)
        trace = trace[:-1] + ("refine_open_cardigan_premium_construction", trace[-1])
        coverage = _coverage_missing(base, polished.frames, allow_sleeve_exposure=False)
        if any(coverage.values()):
            raise ValueError(f"premium cardigan construction broke body coverage: {coverage}")
    frames, role_frames, ramps, material_evidence = _resolve_frames(
        recipe,
        base,
        polished,
        signals,
        execution_profile=execution_profile,
    )
    material_evidence = dict(material_evidence)
    material_evidence["executionProfile"] = execution_profile
    sleeve_ramp = ramps["PrimaryFabric"]
    sleeve_colors = tuple(color[:3] for color in (sleeve_ramp["DEEP_CREASE"], sleeve_ramp["BASE"], sleeve_ramp["LIGHT"]))
    return ControlledHDAdapterRender(
        recipe=recipe,
        backend_recipe=backend_recipe,
        backend=backend,
        stage_trace=trace,
        mask_frames=polished.frames,
        frames=frames,
        role_frames=role_frames,
        texture=_stack(frames),
        sleeve_colors=sleeve_colors,
        construction_signals=_freeze_signals(signals),
        coverage_missing=coverage,
        polish_metrics=polished.metrics,
        palette_ramps=ramps,
        material_evidence=material_evidence,
        execution_profile=execution_profile,
    )


def render_repair_set(*, soften_back_neck: bool = True) -> list[ControlledHDAdapterRender]:
    return [render_controlled_hd_adapter(grammar_id, soften_back_neck=soften_back_neck) for grammar_id in SUPPORTED]
