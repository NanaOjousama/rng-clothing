"""Coordinate-free V5C2 article and hoodie recipes.

V5C2 keeps the proven V3 design concept, V4 article, and V5B sleeve contracts.
It adds vanilla-informed article signals and a formal Hoodie adapter. Logical
cells remain entirely in the renderer and its data grammar.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from generator.v2_recipe_engine import _coordinate_key_errors, _schema_errors
from generator.v5b.engine import _base, _design, load_v5b_data, validate_v5b_recipe


ROOT = Path(__file__).resolve().parents[2]
GRAMMAR = ROOT / "generator" / "data" / "v5c2" / "upper_quality_grammar.json"
SCHEMA = ROOT / "generator" / "schema" / "garment_recipe_v5c2.schema.json"


@dataclass(frozen=True)
class V5C2RecipeValidation:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_v5c2_data() -> dict[str, Any]:
    return {"grammar": _json(GRAMMAR), "schema": _json(SCHEMA)}


def _active_surface_systems(plan: dict[str, Any]) -> set[str]:
    systems = {plan["primarySystem"]}
    if plan["supportSystem"] != "none":
        systems.add(plan["supportSystem"])
    if plan["motif"] != "none":
        systems.add("motif")
    if plan["pattern"] != "none":
        systems.add("pattern")
    if plan["trim"] != "none":
        systems.add("trim")
    return systems


def _motif_cells(rows: list[str]) -> int:
    return sum(symbol != "." for row in rows for symbol in row)


def validate_v5c2_recipe(recipe: dict[str, Any], data: dict[str, Any] | None = None) -> V5C2RecipeValidation:
    data = data or load_v5c2_data()
    errors = _schema_errors(recipe, data["schema"])
    errors.extend(_coordinate_key_errors({key: value for key, value in recipe.items() if key != "baseUpperRecipe"}))
    warnings: list[str] = []
    if errors:
        return V5C2RecipeValidation(False, tuple(errors), tuple(warnings))
    grammar = data["grammar"]
    article = grammar["articles"].get(recipe["articleType"])
    if not article:
        errors.append(f"unsupported V5C2 article {recipe['articleType']}")
        return V5C2RecipeValidation(False, tuple(errors), tuple(warnings))
    if recipe["articleSubtype"] not in article["subtypes"]:
        errors.append(f"{recipe['articleType']} does not support subtype {recipe['articleSubtype']}")
    if recipe["sleeveIntent"] not in article["allowedSleeves"]:
        errors.append(f"{recipe['articleType']} does not support {recipe['sleeveIntent']}")
    base_result = validate_v5b_recipe(recipe["baseUpperRecipe"])
    errors.extend(f"V5B runtime base: {message}" for message in base_result.errors)
    warnings.extend(f"V5B runtime base: {message}" for message in base_result.warnings)
    base_article = recipe["baseUpperRecipe"].get("articleType")
    expected_base = "SWEATER" if recipe["articleType"] == "HOODIE" else recipe["articleType"]
    if base_article != expected_base:
        errors.append(f"{recipe['articleType']} requires V5B base article {expected_base}, found {base_article}")
    hood = recipe["hoodIntent"]
    if recipe["articleType"] == "HOODIE":
        if hood["state"] != "down" or hood["volume"] == "none":
            errors.append("V5C2 hoodies require a supported hood-down volume")
        required = {"hood_ring", "ribbed_hem"}
        if not required.issubset(recipe["constructionFeatures"]):
            errors.append(f"hoodie is missing required construction features {sorted(required)}")
    elif hood != {"state": "none", "lining": "none", "drawstrings": False, "volume": "none"}:
        errors.append("non-hoodie article cannot request hood construction")
    rarity = recipe["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]["rarity"]
    budget = grammar["rarityBudgets"][rarity]
    feature_count = len(recipe["constructionFeatures"])
    if not budget["minimumConstructionFeatures"] <= feature_count <= budget["maximumConstructionFeatures"]:
        errors.append(f"{rarity} construction feature count {feature_count} is outside {budget['minimumConstructionFeatures']}..{budget['maximumConstructionFeatures']}")
    plan = recipe["surfacePlan"]
    if plan["motif"] not in grammar["motifs"]:
        errors.append(f"unknown V5C2 motif {plan['motif']}")
    else:
        count = _motif_cells(grammar["motifs"][plan["motif"]])
        if count > budget["maximumMotifCells"]:
            errors.append(f"{rarity} motif cell ceiling exceeded ({count} > {budget['maximumMotifCells']})")
    systems = _active_surface_systems(plan)
    if len(systems) > budget["maximumSurfaceSystems"]:
        errors.append(f"{rarity} surface system ceiling exceeded ({len(systems)} > {budget['maximumSurfaceSystems']})")
    if recipe["referenceInfluence"]["copiedPixels"]:
        errors.append("reference pixels may never enter a V5C2 semantic recipe")
    return V5C2RecipeValidation(not errors, tuple(errors), tuple(warnings))


def _base_upper(
    index: int,
    *,
    article: str,
    variant: str,
    sleeve: str,
    shoulder: str,
    neckline: str,
    collar: str,
    layering: str,
    opening: str,
    theme: str,
    rarity: str,
    archetype: str,
    name: str,
    description: str,
    palette_story: str,
) -> dict[str, Any]:
    design = _design(index, theme, rarity, archetype, name)
    design["paletteStory"] = palette_story
    design["itemDescription"] = description
    base_article = load_v5b_data()["articles"]["articles"][article]["baseArticle"]
    base = _base(index, design, base_article)
    recipe = {
        "formatVersion": "5.2.0",
        "id": f"v5b-v5c2-{index:02d}",
        "collection": "V5BUpperBenchmark",
        "articleType": article,
        "constructionVariant": variant,
        "sleeveIntent": sleeve,
        "shoulderIntent": shoulder,
        "necklineIntent": neckline,
        "collarIntent": collar,
        "layeringIntent": layering,
        "openingIntent": opening,
        "surfaceTranslation": {
            "primaryZone": "chest",
            "sleeveContinuation": "fabric_match" if sleeve != "LAYERED_INNER_OUTER_SLEEVE" else "trim_echo",
            "cuffTreatment": "layered" if sleeve == "LAYERED_INNER_OUTER_SLEEVE" else "simple"
        },
        "baseArticleRecipe": base,
    }
    result = validate_v5b_recipe(recipe)
    if not result.valid:
        raise ValueError(f"invalid V5C2 runtime base {index}: {'; '.join(result.errors)}")
    return recipe


def generate_v5c2_batch() -> dict[str, Any]:
    """Return exactly ten visible concepts; there is no hidden candidate pool."""

    none_hood = {"state": "none", "lining": "none", "drawstrings": False, "volume": "none"}
    specs = [
        {
            "articleType": "VEST_TOP", "articleSubtype": "tailored_waistcoat", "fitIntent": "fitted",
            "sleeveIntent": "FITTED_LONG_SLEEVE", "necklineIntent": "v_neck", "collarIntent": "none",
            "openingIntent": "buttoned", "hemIntent": "tailored", "hoodIntent": none_hood,
            "constructionFeatures": ["v_opening", "buttoned_placket", "inner_shirt", "tapered_waist"],
            "surfacePlan": {"composition": "construction_led", "primarySystem": "construction", "supportSystem": "trim", "motif": "none", "pattern": "none", "trim": "piping", "focalArea": "collar", "topology": "construction_bound"},
            "referenceInfluence": {"source": "vanilla_aggregate", "traitsOnly": ["high_contrast_inner_shirt", "v_shaped_vest_opening", "quiet_back"], "copiedPixels": False},
            "runtime": dict(article="VEST_TOP", variant="waistcoat", sleeve="FITTED_LONG_SLEEVE", shoulder="narrow", neckline="v_neck", collar="none", layering="vest_over_inner", opening="buttoned", theme="formal_elegant", rarity="Common", archetype="BUTTON_SHIRT", name="Slate & Saffron Waistcoat", description="A crisp slate waistcoat over a warm, fully sleeved inner shirt.", palette_story="ink_ivory")
        },
        {
            "articleType": "BLOUSE", "articleSubtype": "bow_yoke_blouse", "fitIntent": "fitted",
            "sleeveIntent": "ROLLED_CUFFED_SLEEVE", "necklineIntent": "square", "collarIntent": "rounded",
            "openingIntent": "partial_open", "hemIntent": "plain", "hoodIntent": none_hood,
            "constructionFeatures": ["soft_yoke", "bow_knot", "shaped_neckline", "fitted_waist"],
            "surfacePlan": {"composition": "collar_led", "primarySystem": "collar", "supportSystem": "motif", "motif": "ribbon_knot", "pattern": "none", "trim": "none", "focalArea": "upper_chest", "topology": "front_only"},
            "referenceInfluence": {"source": "vanilla_aggregate", "traitsOnly": ["broad_collar_signal", "single_cluster_focal", "soft_side_reconstruction"], "copiedPixels": False},
            "runtime": dict(article="BLOUSE", variant="bow_blouse", sleeve="ROLLED_CUFFED_SLEEVE", shoulder="narrow", neckline="square", collar="rounded", layering="collar_overlay", opening="partial_open", theme="storybook_whimsical", rarity="Uncommon", archetype="BUTTON_SHIRT", name="Roseglass Yoke Blouse", description="A shaped yoke blouse finished with a compact ribbon knot and rolled cuffs.", palette_story="rose_sage")
        },
        {
            "articleType": "SWEATER", "articleSubtype": "heritage_knit", "fitIntent": "relaxed",
            "sleeveIntent": "LAYERED_INNER_OUTER_SLEEVE", "necklineIntent": "high", "collarIntent": "rounded",
            "openingIntent": "closed", "hemIntent": "ribbed", "hoodIntent": none_hood,
            "constructionFeatures": ["knit_yoke", "ribbed_hem", "substantial_neck", "cuff_echo", "continuous_cloth_mass"],
            "surfacePlan": {"composition": "pattern_led", "primarySystem": "pattern", "supportSystem": "trim", "motif": "knit_leaf_band", "pattern": "knit_yoke", "trim": "ribbed", "focalArea": "yoke", "topology": "upper_wrap"},
            "referenceInfluence": {"source": "vanilla_aggregate", "traitsOnly": ["unbroken_knit_mass", "upper_pattern_band", "ribbed_termination"], "copiedPixels": False},
            "runtime": dict(article="SWEATER", variant="patterned_knit", sleeve="LAYERED_INNER_OUTER_SLEEVE", shoulder="dropped", neckline="high", collar="rounded", layering="collar_overlay", opening="closed", theme="creature_inspired", rarity="Rare", archetype="SWEATER", name="Copperleaf Hearth Knit", description="A substantial patterned knit with a leaflike yoke rhythm and layered cuffs.", palette_story="harvest_cream")
        },
        {
            "articleType": "CROPPED_JACKET", "articleSubtype": "compact_field_jacket", "fitIntent": "regular",
            "sleeveIntent": "ROLLED_CUFFED_SLEEVE", "necklineIntent": "open", "collarIntent": "lapel",
            "openingIntent": "center_open", "hemIntent": "cropped", "hoodIntent": none_hood,
            "constructionFeatures": ["lapel_opening", "paired_pockets", "short_yoke", "cropped_hem", "visible_inner_layer"],
            "surfacePlan": {"composition": "pocket_led", "primarySystem": "pocket", "supportSystem": "trim", "motif": "field_tabs", "pattern": "none", "trim": "lapel_edge", "focalArea": "pocket", "topology": "construction_bound"},
            "referenceInfluence": {"source": "vanilla_aggregate", "traitsOnly": ["two_panel_outer_shell", "strong_short_hem", "paired_front_cues"], "copiedPixels": False},
            "runtime": dict(article="CROPPED_JACKET", variant="field_jacket", sleeve="ROLLED_CUFFED_SLEEVE", shoulder="standard", neckline="open", collar="lapel", layering="visible_inner_layer", opening="center_open", theme="military_structured", rarity="Uncommon", archetype="JACKET", name="Kestrel Cropped Field Jacket", description="A compact field jacket with readable lapels, paired pocket tabs, and a short structured waist.", palette_story="field_tan")
        },
        {
            "articleType": "STANDARD_JACKET", "articleSubtype": "field_jacket", "fitIntent": "regular",
            "sleeveIntent": "LAYERED_INNER_OUTER_SLEEVE", "necklineIntent": "open", "collarIntent": "utility",
            "openingIntent": "partial_open", "hemIntent": "structured", "hoodIntent": none_hood,
            "constructionFeatures": ["field_yoke", "structured_opening", "paired_pockets", "utility_collar", "finished_hem", "cuff_echo"],
            "surfacePlan": {"composition": "construction_led", "primarySystem": "construction", "supportSystem": "pocket", "motif": "field_tabs", "pattern": "none", "trim": "piping", "focalArea": "upper_chest", "topology": "construction_bound"},
            "referenceInfluence": {"source": "vanilla_aggregate", "traitsOnly": ["workwear_yoke", "clear_opening", "quiet_back_panel"], "copiedPixels": False},
            "runtime": dict(article="STANDARD_JACKET", variant="field_jacket", sleeve="LAYERED_INNER_OUTER_SLEEVE", shoulder="standard", neckline="open", collar="utility", layering="visible_inner_layer", opening="partial_open", theme="elemental", rarity="Rare", archetype="JACKET", name="Pinewatch Field Jacket", description="A full field jacket with disciplined panels, utility pockets, and a finished lower edge.", palette_story="moss_creature")
        },
        {
            "articleType": "HOODIE", "articleSubtype": "pullover", "fitIntent": "regular",
            "sleeveIntent": "FITTED_LONG_SLEEVE", "necklineIntent": "hooded", "collarIntent": "hood",
            "openingIntent": "closed", "hemIntent": "ribbed", "hoodIntent": {"state": "down", "lining": "self", "drawstrings": True, "volume": "standard"},
            "constructionFeatures": ["hood_ring", "drawstrings", "ribbed_hem"],
            "surfacePlan": {"composition": "collar_led", "primarySystem": "collar", "supportSystem": "none", "motif": "none", "pattern": "none", "trim": "hood_edge", "focalArea": "collar", "topology": "construction_bound"},
            "referenceInfluence": {"source": "hoodie_corpus_aggregate", "traitsOnly": ["simple_pullover_mass", "hood_opening", "quiet_body"], "copiedPixels": False},
            "runtime": dict(article="SWEATER", variant="fitted_knit", sleeve="FITTED_LONG_SLEEVE", shoulder="standard", neckline="crew", collar="none", layering="single_layer", opening="closed", theme="seasonal_soft", rarity="Common", archetype="SWEATER", name="Harbor Haze Pullover", description="A clean everyday pullover hoodie with a shaped hood opening and ribbed finish.", palette_story="seafoam_coral")
        },
        {
            "articleType": "HOODIE", "articleSubtype": "zip", "fitIntent": "fitted",
            "sleeveIntent": "FITTED_LONG_SLEEVE", "necklineIntent": "hooded", "collarIntent": "hood",
            "openingIntent": "zip", "hemIntent": "ribbed", "hoodIntent": {"state": "down", "lining": "self", "drawstrings": True, "volume": "compact"},
            "constructionFeatures": ["hood_ring", "drawstrings", "center_zip", "ribbed_hem"],
            "surfacePlan": {"composition": "opening_led", "primarySystem": "opening", "supportSystem": "trim", "motif": "rain_tab", "pattern": "none", "trim": "zip_edge", "focalArea": "upper_chest", "topology": "construction_bound"},
            "referenceInfluence": {"source": "hoodie_corpus_aggregate", "traitsOnly": ["zip_separation", "compact_hood", "fitted_lightweight_body"], "copiedPixels": False},
            "runtime": dict(article="SWEATER", variant="fitted_knit", sleeve="FITTED_LONG_SLEEVE", shoulder="standard", neckline="crew", collar="none", layering="single_layer", opening="closed", theme="military_structured", rarity="Uncommon", archetype="SWEATER", name="Rainline Zip Hoodie", description="A fitted rain-blue hoodie with a clean zip rhythm and compact hood.", palette_story="teal_circuit")
        },
        {
            "articleType": "HOODIE", "articleSubtype": "pouch_contrast", "fitIntent": "relaxed",
            "sleeveIntent": "LAYERED_INNER_OUTER_SLEEVE", "necklineIntent": "hooded", "collarIntent": "hood",
            "openingIntent": "closed", "hemIntent": "ribbed", "hoodIntent": {"state": "down", "lining": "contrast", "drawstrings": True, "volume": "standard"},
            "constructionFeatures": ["hood_ring", "contrast_hood", "drawstrings", "pouch_pocket", "ribbed_hem"],
            "surfacePlan": {"composition": "pocket_led", "primarySystem": "pocket", "supportSystem": "color_block", "motif": "none", "pattern": "none", "trim": "hood_edge", "focalArea": "pocket", "topology": "construction_bound"},
            "referenceInfluence": {"source": "hoodie_corpus_aggregate", "traitsOnly": ["large_pouch", "contrast_hood_interior", "relaxed_mass"], "copiedPixels": False},
            "runtime": dict(article="SWEATER", variant="relaxed_knit", sleeve="LAYERED_INNER_OUTER_SLEEVE", shoulder="dropped", neckline="crew", collar="rounded", layering="single_layer", opening="closed", theme="dessert_cute", rarity="Uncommon", archetype="SWEATER", name="Cloudberry Pouch Hoodie", description="A relaxed berry-toned hoodie with a contrasting hood and broad pouch pocket.", palette_story="berry_cream")
        },
        {
            "articleType": "HOODIE", "articleSubtype": "cropped_charm", "fitIntent": "cropped",
            "sleeveIntent": "LAYERED_INNER_OUTER_SLEEVE", "necklineIntent": "hooded", "collarIntent": "hood",
            "openingIntent": "closed", "hemIntent": "cropped", "hoodIntent": {"state": "down", "lining": "contrast", "drawstrings": True, "volume": "standard"},
            "constructionFeatures": ["hood_ring", "contrast_hood", "drawstrings", "pouch_pocket", "cropped_hem", "ribbed_hem", "cuff_echo"],
            "surfacePlan": {"composition": "motif_led", "primarySystem": "motif", "supportSystem": "pocket", "motif": "sproutwing_charm", "pattern": "none", "trim": "ribbed", "focalArea": "side_chest", "topology": "asymmetric_front"},
            "referenceInfluence": {"source": "hoodie_design1_traits", "traitsOnly": ["sage_like_softness", "small_asymmetric_charm", "drawstrings", "cropped_relaxed_form"], "copiedPixels": False},
            "runtime": dict(article="SWEATER", variant="patterned_knit", sleeve="LAYERED_INNER_OUTER_SLEEVE", shoulder="dropped", neckline="high", collar="rounded", layering="single_layer", opening="closed", theme="creature_inspired", rarity="Rare", archetype="SWEATER", name="Sproutwing Cropped Hoodie", description="A cropped soft hoodie with an original sprout-wing charm, pouch seam, and contrasting hood lining.", palette_story="moss_creature")
        },
        {
            "articleType": "HOODIE", "articleSubtype": "baggy_crest", "fitIntent": "baggy",
            "sleeveIntent": "LAYERED_INNER_OUTER_SLEEVE", "necklineIntent": "hooded", "collarIntent": "hood",
            "openingIntent": "closed", "hemIntent": "ribbed", "hoodIntent": {"state": "down", "lining": "self", "drawstrings": False, "volume": "baggy"},
            "constructionFeatures": ["hood_ring", "baggy_body", "ribbed_hem", "cuff_echo", "broad_focal_panel"],
            "surfacePlan": {"composition": "motif_led", "primarySystem": "motif", "supportSystem": "pattern", "motif": "nightgarden_crest", "pattern": "tonal_repeat", "trim": "ribbed", "focalArea": "center_chest", "topology": "front_back_pair"},
            "referenceInfluence": {"source": "hoodie_design2_traits", "traitsOnly": ["oversized_sweatshirt_mass", "tonal_center_crest", "restrained_monochrome", "ribbed_edges"], "copiedPixels": False},
            "runtime": dict(article="SWEATER", variant="patterned_knit", sleeve="LAYERED_INNER_OUTER_SLEEVE", shoulder="dropped", neckline="high", collar="rounded", layering="single_layer", opening="closed", theme="celestial_fantasy", rarity="Rare", archetype="SWEATER", name="Nightgarden Crest Hoodie", description="A baggy midnight hoodie with a restrained original garden crest and broad ribbing.", palette_story="plum_moon")
        }
    ]
    recipes = []
    for index, spec in enumerate(specs, 1):
        runtime = spec.pop("runtime")
        base = _base_upper(index, **runtime)
        recipe = {
            "formatVersion": "5.3.0",
            "id": f"v5c2-{index:02d}",
            "collection": "V5C2VanillaHoodieStudy",
            **spec,
            "baseUpperRecipe": base,
        }
        result = validate_v5c2_recipe(recipe)
        if not result.valid:
            raise ValueError(f"invalid V5C2 recipe {recipe['id']}: {'; '.join(result.errors)}")
        recipes.append(recipe)
    return {
        "generatorVersion": "5.3.0",
        "collection": "V5C2VanillaHoodieStudy",
        "seed": 2026083053,
        "count": len(recipes),
        "hiddenCandidateCount": 0,
        "recipes": recipes,
    }
