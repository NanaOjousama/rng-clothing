"""Design-first Generator V3.

V3 remains coordinate-free. It chooses an authored design concept, compatible
V2 construction, a hierarchical surface composition, and a color story. The
Fashion Sense backend alone owns logical-cell placement.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from generator.v2_recipe_engine import (
    _coordinate_key_errors,
    _schema_errors,
    load_v2_data,
    validate_recipe_v2,
)


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "generator" / "data" / "v3"
SCHEMA_PATH = ROOT / "generator" / "schema" / "garment_recipe_v3.schema.json"
GENERATOR_V3_VERSION = "3.0.0"


@dataclass(frozen=True)
class V3RecipeValidation:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    active_systems: tuple[str, ...]
    design_signature: tuple[str, ...]


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_v3_data() -> dict[str, Any]:
    return {
        "schema": _json(SCHEMA_PATH),
        "vocabulary": _json(DATA_DIR / "design_vocabulary.json"),
        "budgets": _json(DATA_DIR / "rarity_budgets.json"),
        "palettes": _json(DATA_DIR / "palette_stories.json"),
        "surfaceGrammar": _json(DATA_DIR / "surface_grammar.json"),
        "benchmarkRequests": _json(DATA_DIR / "benchmark_requests.json"),
    }


def _stable_index(seed: int, key: str, size: int) -> int:
    digest = hashlib.sha256(f"{seed}|{key}".encode()).digest()
    return int.from_bytes(digest[:8], "big") % size


CONSTRUCTION_PRESETS = {
    "SWEATER": (
        ({"fit": "regular", "neckline": "crew", "collar": "none", "closure": "none", "layering": "single_layer", "hem": "ribbed", "panelLayout": "solid"}, ["ribbed_hem"]),
        ({"fit": "relaxed", "neckline": "shallow_v", "collar": "wide", "closure": "none", "layering": "single_layer", "hem": "structured", "panelLayout": "solid"}, ["broad_collar"]),
        ({"fit": "regular", "neckline": "round", "collar": "none", "closure": "none", "layering": "overlay_panel", "hem": "ribbed", "panelLayout": "yoke"}, ["yoke", "ribbed_hem"]),
    ),
    "BUTTON_SHIRT": (
        ({"fit": "regular", "neckline": "open", "collar": "small_folded", "closure": "buttons", "layering": "single_layer", "hem": "plain", "panelLayout": "center_placket"}, ["center_placket"]),
        ({"fit": "fitted", "neckline": "open", "collar": "small_folded", "closure": "buttons", "layering": "overlay_panel", "hem": "plain", "panelLayout": "yoke"}, ["yoke"]),
        ({"fit": "regular", "neckline": "open", "collar": "small_folded", "closure": "buttons", "layering": "single_layer", "hem": "contrast_band", "panelLayout": "center_placket"}, ["center_placket", "structured_lower_band"]),
    ),
    "JACKET": (
        ({"fit": "regular", "neckline": "open", "collar": "small_folded", "closure": "center_open", "layering": "visible_inner_layer", "hem": "structured", "panelLayout": "split_outer_panels"}, ["contrast_inner_layer"]),
        ({"fit": "regular", "neckline": "open", "collar": "small_folded", "closure": "center_open", "layering": "visible_inner_layer", "hem": "structured", "panelLayout": "split_outer_panels"}, ["contrast_inner_layer"]),
        ({"fit": "relaxed", "neckline": "open", "collar": "small_folded", "closure": "buttons", "layering": "overlay_panel", "hem": "contrast_band", "panelLayout": "center_placket"}, ["center_placket", "structured_lower_band"]),
    ),
    "SAILOR_TOP": (
        ({"fit": "regular", "neckline": "open", "collar": "sailor", "closure": "none", "layering": "overlay_panel", "hem": "plain", "panelLayout": "yoke"}, ["yoke"]),
        ({"fit": "fitted", "neckline": "open", "collar": "sailor", "closure": "none", "layering": "overlay_panel", "hem": "plain", "panelLayout": "yoke"}, ["yoke"]),
        ({"fit": "regular", "neckline": "open", "collar": "sailor", "closure": "none", "layering": "overlay_panel", "hem": "contrast_band", "panelLayout": "yoke"}, ["yoke", "structured_lower_band"]),
    ),
}


THEME_PLAN = {
    "beach_casual": dict(palette="seafoam_coral", mood="bright", composition="trim_led", primary="trim", trim="double_stripe", motif="none", pattern="none", block="none", focal="hem", symmetry="symmetric"),
    "seasonal_soft": dict(palette="harvest_cream", mood="cozy", composition="pattern_led", primary="pattern", trim="none", motif="none", pattern="soft_repeat", block="none", focal="center_chest", symmetry="symmetric"),
    "formal_elegant": dict(palette="ink_ivory", mood="refined", composition="collar_led", primary="trim", trim="collar_trim", motif="none", pattern="none", block="none", focal="collar", symmetry="symmetric"),
    "floral_romantic": dict(palette="rose_sage", mood="romantic", composition="motif_led", primary="motif", trim="none", motif="flower", pattern="none", block="none", focal="side_chest", symmetry="soft_asymmetric"),
    "dessert_cute": dict(palette="berry_cream", mood="playful", composition="motif_led", primary="motif", trim="scalloped_trim", motif="dessert", pattern="none", block="none", focal="center_chest", symmetry="symmetric"),
    "witchy_dark": dict(palette="plum_moon", mood="mysterious", composition="motif_led", primary="motif", trim="cuff_trim", motif="crystal", pattern="none", block="none", focal="center_chest", symmetry="symmetric"),
    "cyber_tech": dict(palette="teal_circuit", mood="technical", composition="color_block_led", primary="color_block", trim="none", motif="cyber_glyph", pattern="none", block="center_panel", focal="upper_chest", symmetry="asymmetric"),
    "military_structured": dict(palette="field_tan", mood="rugged", composition="trim_led", primary="trim", trim="lapel_trim", motif="none", pattern="none", block="shoulder_block", focal="shoulders", symmetry="symmetric"),
    "celestial_fantasy": dict(palette="midnight_gold", mood="magical", composition="motif_led", primary="motif", trim="piping", motif="star", pattern="diamonds", block="none", focal="center_chest", symmetry="symmetric"),
    "storybook_whimsical": dict(palette="storybook_blue", mood="whimsical", composition="motif_led", primary="motif", trim="scalloped_trim", motif="ribbon", pattern="none", block="yoke_block", focal="upper_chest", symmetry="soft_asymmetric"),
    "elemental": dict(palette="ember_charcoal", mood="energetic", composition="asymmetric_accent_led", primary="motif", trim="lapel_trim", motif="lightning", pattern="none", block="side_panels", focal="side_chest", symmetry="asymmetric"),
    "creature_inspired": dict(palette="moss_creature", mood="playful", composition="motif_led", primary="motif", trim="hem_trim", motif="creature", pattern="soft_repeat", block="none", focal="center_chest", symmetry="symmetric"),
}


def _role_for_archetype(archetype: str) -> tuple[str, str]:
    return {
        "SWEATER": ("soft_sweater", "soft_mass"),
        "BUTTON_SHIRT": ("tailored_shirt", "fitted_tailored"),
        "JACKET": ("outer_jacket", "layered_outerwear"),
        "SAILOR_TOP": ("dressy_top", "broad_yoke"),
    }[archetype]


def _preset(archetype: str, rarity: str, seed: int) -> tuple[dict[str, str], list[str]]:
    choices = CONSTRUCTION_PRESETS[archetype]
    tier = {"Common": 0, "Uncommon": 1, "Rare": 2}[rarity]
    # Common always uses the restrained preset; other tiers use the upper two.
    allowed = choices[:1] if rarity == "Common" else choices[1:2] if rarity == "Uncommon" else choices[1:]
    construction, features = allowed[_stable_index(seed, f"construction:{archetype}:{rarity}", len(allowed))]
    return dict(construction), list(features[: max(1, tier)])


def _systems(plan: dict[str, str], rarity: str) -> tuple[list[str], dict[str, bool]]:
    available = {
        "color_block": plan["block"] != "none",
        "trim": plan["trim"] != "none",
        "motif": plan["motif"] != "none",
        "pattern": plan["pattern"] != "none",
    }
    primary = plan["primary"]
    ordered = [primary] + [name for name in ("color_block", "trim", "motif", "pattern") if name != primary and available[name]]
    target = {"Common": 1, "Uncommon": 2, "Rare": 3}[rarity]
    active = ordered[:target]
    if len(active) != target:
        raise ValueError(f"{rarity} theme plan does not provide {target} active systems: {plan}")
    return active, available


def generate_v3_recipe(request: dict[str, Any], generation_index: int, seed: int) -> dict[str, Any]:
    theme = request["themeFamily"]
    rarity = request["rarity"]
    archetype = request.get("archetype")
    if theme not in THEME_PLAN:
        raise ValueError(f"unsupported V3 theme family {theme!r}")
    if archetype not in CONSTRUCTION_PRESETS:
        preferred = load_v3_data()["vocabulary"]["themeFamilies"][theme]["preferredArchetypes"]
        archetype = preferred[_stable_index(seed, f"archetype:{theme}", len(preferred))]
    plan = THEME_PLAN[theme]
    active, available = _systems(plan, rarity)
    construction, features = _preset(archetype, rarity, seed)
    role, silhouette = _role_for_archetype(archetype)
    supports = active[1:]
    topologies = {
        "color_block": "shoulder_wrap" if plan["block"] in {"shoulder_block", "yoke_block"} else "wrap" if plan["block"] in {"chest_band", "lower_band", "waist_block"} else "front_back" if plan["block"] == "center_panel" else "construction_bound",
        "trim": "wrap" if plan["trim"] in {"hem_trim", "double_stripe", "scalloped_trim", "lace_border", "decorative_edge_band"} else "construction_bound",
        "motif": "front_back_pair" if rarity == "Rare" else "asymmetric_front" if plan["symmetry"] != "symmetric" else "front_only",
        "pattern": "wrap" if plan["pattern"] in {"stripes", "soft_repeat", "diamonds", "chevrons"} else "front_back",
    }
    inactive = lambda name: name not in active
    description = f"An original {plan['mood']} {role.replace('_', ' ')} with a {plan['composition'].replace('_', ' ')} design."
    recipe = {
        "formatVersion": 3,
        "id": f"v3-benchmark-{generation_index:02d}",
        "generationIndex": generation_index,
        "seed": seed,
        "category": "Lifestyle",
        "styleProfile": "V3Benchmark",
        "themeFamily": theme,
        "rarity": rarity,
        "archetype": archetype,
        "concept": {
            "garmentRole": role,
            "silhouetteGoal": silhouette,
            "designMood": plan["mood"],
            "primaryGesture": "color_block" if plan["primary"] == "color_block" else plan["primary"],
            "secondaryGesture": supports[0] if supports else "none",
            "focalArea": plan["focal"],
            "symmetryBias": plan["symmetry"],
            "designDensity": {"Common": "low", "Uncommon": "moderate", "Rare": "rich_restrained"}[rarity],
            "themeEmphasis": {"Common": "subtle", "Uncommon": "moderate", "Rare": "strong"}[rarity],
        },
        "construction": construction,
        "substantialFeatures": features,
        "colorBlocking": {
            "type": plan["block"] if not inactive("color_block") else "none",
            "topology": topologies["color_block"],
            "colorRole": "secondary",
        },
        "surfaceDesign": {
            "compositionType": plan["composition"],
            "supportSystems": supports,
            "trim": {"type": plan["trim"] if not inactive("trim") else "none", "topology": topologies["trim"], "colorRole": "light_accent" if theme in {"formal_elegant", "celestial_fantasy"} else "accent"},
            "motif": {"family": plan["motif"] if not inactive("motif") else "none", "scale": "small" if rarity == "Common" else "medium" if rarity == "Uncommon" else "focal", "topology": topologies["motif"], "colorRoles": [] if inactive("motif") else ["accent", "light_accent"] if rarity == "Common" else ["dark_accent", "accent", "light_accent"]},
            "pattern": {"type": plan["pattern"] if not inactive("pattern") else "none", "density": "sparse" if rarity != "Rare" else "moderate", "topology": topologies["pattern"], "colorRole": "secondary"},
            "detailLayout": "front_back_pair" if rarity == "Rare" and "motif" in active else "coordinated_directional" if "trim" in active else "front_focal" if "motif" in active else "none",
        },
        "paletteStory": plan["palette"],
        "dyeable": True,
        "itemName": request["itemName"],
        "itemDescription": description,
    }
    validation = validate_recipe_v3(recipe)
    if not validation.valid:
        raise ValueError(f"generated invalid V3 recipe {recipe['id']}: {'; '.join(validation.errors)}")
    return recipe


def to_v2_base_recipe(recipe: dict[str, Any]) -> dict[str, Any]:
    palette = load_v3_data()["palettes"]["stories"][recipe["paletteStory"]]
    construction = recipe["construction"]
    if recipe["archetype"] == "JACKET":
        primary = "outer_panels"
        secondary = "inner_layer" if construction["layering"] == "visible_inner_layer" else "placket"
    elif construction["panelLayout"] == "yoke":
        primary, secondary = "body", "yoke"
    elif construction["collar"] in {"wide", "sailor"}:
        primary, secondary = "body", "collar"
    elif construction["panelLayout"] == "center_placket":
        primary, secondary = "body", "placket"
    elif construction["hem"] == "ribbed":
        primary, secondary = "body", "ribbing"
    elif construction["hem"] == "contrast_band":
        primary, secondary = "body", "hem"
    else:
        primary, secondary = "body", "none"
    return {
        "id": f"lifestyle-v2-{recipe['generationIndex']:02d}",
        "generationIndex": recipe["generationIndex"],
        "seed": recipe["seed"],
        "category": "Lifestyle",
        "styleProfile": "General",
        "referenceTraits": ["compact_straight", "structural_color_blocking", "restrained_palette"],
        "archetype": recipe["archetype"],
        "rarity": recipe["rarity"],
        "construction": dict(construction),
        "substantialFeatures": list(recipe["substantialFeatures"]),
        "microDetails": [],
        "colorBlocking": {"primaryRegion": primary, "secondaryRegion": secondary, "accentRegion": "none"},
        "paletteFamily": palette["baseFamily"],
        "accent": "none",
        "dyeable": True,
        "itemName": recipe["itemName"],
        "itemDescription": recipe["itemDescription"],
    }


def active_surface_systems(recipe: dict[str, Any]) -> tuple[str, ...]:
    active = []
    if recipe["colorBlocking"]["type"] != "none": active.append("color_block")
    if recipe["surfaceDesign"]["trim"]["type"] != "none": active.append("trim")
    if recipe["surfaceDesign"]["motif"]["family"] != "none": active.append("motif")
    if recipe["surfaceDesign"]["pattern"]["type"] != "none": active.append("pattern")
    return tuple(active)


def design_signature(recipe: dict[str, Any]) -> tuple[str, ...]:
    return (
        recipe["themeFamily"], recipe["archetype"], recipe["surfaceDesign"]["compositionType"],
        recipe["concept"]["focalArea"], recipe["concept"]["symmetryBias"],
        recipe["colorBlocking"]["type"], recipe["surfaceDesign"]["trim"]["type"],
        recipe["surfaceDesign"]["motif"]["family"], recipe["surfaceDesign"]["pattern"]["type"],
        recipe["paletteStory"], recipe["construction"]["panelLayout"], recipe["construction"]["hem"],
    )


def validate_recipe_v3(recipe: dict[str, Any], data: dict[str, Any] | None = None) -> V3RecipeValidation:
    data = data or load_v3_data()
    errors = _schema_errors(recipe, data["schema"])
    errors.extend(_coordinate_key_errors(recipe))
    active = active_surface_systems(recipe) if not errors else ()
    warnings: list[str] = []
    if not errors:
        budget = data["budgets"]["rarities"][recipe["rarity"]]
        if not budget["minimumActiveSurfaceSystems"] <= len(active) <= budget["maximumActiveSurfaceSystems"]:
            errors.append(f"{recipe['rarity']} requires {budget['minimumActiveSurfaceSystems']}..{budget['maximumActiveSurfaceSystems']} active surface systems, found {len(active)}")
        if recipe["concept"]["designDensity"] not in budget["allowedDensity"]:
            errors.append(f"{recipe['rarity']} does not allow density {recipe['concept']['designDensity']}")
        supports = recipe["surfaceDesign"]["supportSystems"]
        if len(supports) > budget["maximumSupportSystems"]:
            errors.append(f"{recipe['rarity']} support-system budget exceeded")
        primary = data["vocabulary"]["compositionFamilies"][recipe["surfaceDesign"]["compositionType"]]["primary"]
        if primary not in active:
            errors.append(f"composition primary {primary} is not active")
        if set(supports) != set(active) - {primary}:
            errors.append("supportSystems must name every active non-primary surface system exactly once")
        v2 = to_v2_base_recipe(recipe)
        v2_result = validate_recipe_v2(v2, load_v2_data())
        errors.extend(f"V2 construction adapter: {message}" for message in v2_result.errors)
        warnings.extend(f"V2 construction adapter: {message}" for message in v2_result.warnings)
    return V3RecipeValidation(not errors, tuple(errors), tuple(warnings), active, design_signature(recipe) if not errors else ())


def generate_benchmark_batch() -> dict[str, Any]:
    data = load_v3_data()
    request_data = data["benchmarkRequests"]
    recipes = []
    for index, request in enumerate(request_data["requests"], 1):
        seed = request_data["seed"] + index * 7919
        recipes.append(generate_v3_recipe(request, index, seed))
    signatures = [design_signature(recipe) for recipe in recipes]
    if len(signatures) != len(set(signatures)):
        raise ValueError("V3 benchmark contains duplicate design signatures")
    return {
        "generatorVersion": GENERATOR_V3_VERSION,
        "seed": request_data["seed"],
        "count": len(recipes),
        "rarityCounts": {rarity: sum(r["rarity"] == rarity for r in recipes) for rarity in ("Common", "Uncommon", "Rare")},
        "recipes": recipes,
    }
