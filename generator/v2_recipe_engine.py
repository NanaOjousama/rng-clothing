"""Construction-first V2 recipe generation, migration, and validation.

This module deliberately has no renderer import.  Phase 0 must be able to
validate the semantic system before any logical pixel is authored.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
V1_DATA_DIR = ROOT / "generator" / "data"
V2_DATA_DIR = V1_DATA_DIR / "v2"
V2_ARCHETYPE_DIR = V2_DATA_DIR / "archetypes"
V2_SCHEMA_PATH = ROOT / "generator" / "schema" / "garment_recipe_v2.schema.json"
V1_RECIPE_PATH = ROOT / "output" / "recipes" / "lifestyle_v1_recipes.json"

GENERATOR_V2_VERSION = "2.0.0"
GENERATOR_V2_SEED = 202608282200
ARCHETYPE_ORDER = ("T_SHIRT", "SWEATER", "BUTTON_SHIRT", "JACKET", "SAILOR_TOP")
CONSTRUCTION_FIELDS = (
    "fit",
    "neckline",
    "collar",
    "closure",
    "layering",
    "hem",
    "panelLayout",
)
RARITY_SCHEDULE = {
    "T_SHIRT": ("Common", "Common", "Uncommon", "Rare"),
    "SWEATER": ("Common", "Uncommon", "Uncommon", "Rare"),
    "BUTTON_SHIRT": ("Common", "Uncommon", "Rare", "Uncommon"),
    "JACKET": ("Common", "Uncommon", "Rare", "Rare"),
    "SAILOR_TOP": ("Common", "Uncommon", "Rare", "Uncommon"),
}
PALETTE_SCHEDULE = {
    "T_SHIRT": ("sage_tan", "navy_ivory", "warm_neutral", "denim_cream"),
    "SWEATER": ("rust_brown", "forest_cream", "cool_neutral", "charcoal_burgundy"),
    "BUTTON_SHIRT": ("warm_neutral", "sage_tan", "navy_ivory", "denim_cream"),
    "JACKET": ("forest_cream", "charcoal_burgundy", "rust_brown", "cool_neutral"),
    "SAILOR_TOP": ("navy_ivory", "sage_tan", "charcoal_burgundy", "denim_cream"),
}
PALETTE_PREFIX = {
    "forest_cream": "Woodland",
    "navy_ivory": "Harbor",
    "rust_brown": "Hearth",
    "charcoal_burgundy": "Garnet",
    "denim_cream": "Bluebell",
    "sage_tan": "Meadow",
    "warm_neutral": "Cedar",
    "cool_neutral": "Mistral",
}
FEATURE_PRIORITY = (
    "contrast_inner_layer",
    "yoke",
    "broad_collar",
    "ribbed_hem",
    "center_placket",
    "major_panel_contrast",
    "structured_lower_band",
    "wrapping_stripe",
    "split_outer_panels",
)
FEATURE_QUALITY = {
    "contrast_inner_layer": 11,
    "broad_collar": 8,
    "ribbed_hem": 8,
    "major_panel_contrast": 7,
    "center_placket": 8,
    "wrapping_stripe": 6,
    "yoke": 9,
    "split_outer_panels": 7,
    "structured_lower_band": 6,
}
COORDINATE_KEYS = {
    "x",
    "y",
    "xy",
    "point",
    "points",
    "pixel",
    "pixels",
    "coordinate",
    "coordinates",
    "row",
    "rows",
    "column",
    "columns",
    "offset",
    "offsets",
    "frame",
    "frames",
}


@dataclass(frozen=True)
class V2RecipeValidation:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    complexity: dict[str, int]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_v2_data() -> dict[str, Any]:
    archetypes = {path.stem: load_json(path) for path in sorted(V2_ARCHETYPE_DIR.glob("*.json"))}
    if set(archetypes) != set(ARCHETYPE_ORDER):
        raise ValueError(f"expected exactly five V2 archetypes, found {sorted(archetypes)}")
    return {
        "grammar": load_json(V1_DATA_DIR / "vanilla_shirt_grammar.json"),
        "palettes": load_json(V1_DATA_DIR / "palette_rules.json"),
        "schema": load_json(V2_SCHEMA_PATH),
        "vocabulary": load_json(V2_DATA_DIR / "construction_vocabulary.json"),
        "budgets": load_json(V2_DATA_DIR / "rarity_budgets.json"),
        "structuralMasks": load_json(V2_DATA_DIR / "structural_masks.json"),
        "archetypes": archetypes,
    }


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def _schema_errors(value: Any, schema: dict[str, Any], path: str = "$.") -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type and not _type_matches(value, expected_type):
        return [f"{path.rstrip('.')}: expected {expected_type}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path.rstrip('.')}: must be {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path.rstrip('.')}: unsupported value {value!r}")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        missing = sorted(set(schema.get("required", ())) - set(value))
        if missing:
            errors.append(f"{path.rstrip('.')}: missing {', '.join(missing)}")
        if schema.get("additionalProperties") is False:
            extras = sorted(set(value) - set(properties))
            if extras:
                errors.append(f"{path.rstrip('.')}: unexpected {', '.join(extras)}")
        for key, child in value.items():
            if key in properties:
                errors.extend(_schema_errors(child, properties[key], f"{path}{key}."))
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path.rstrip('.')}: too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path.rstrip('.')}: too many items")
        if schema.get("uniqueItems"):
            serialized = [json.dumps(item, sort_keys=True) for item in value]
            if len(serialized) != len(set(serialized)):
                errors.append(f"{path.rstrip('.')}: items must be unique")
        item_schema = schema.get("items")
        if item_schema:
            for index, child in enumerate(value):
                errors.extend(_schema_errors(child, item_schema, f"{path}{index}."))
    elif isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path.rstrip('.')}: too short")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path.rstrip('.')}: too long")
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            errors.append(f"{path.rstrip('.')}: does not match {schema['pattern']}")
    elif isinstance(value, int) and not isinstance(value, bool):
        if value < schema.get("minimum", value):
            errors.append(f"{path.rstrip('.')}: below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path.rstrip('.')}: above maximum")
    return errors


def _coordinate_key_errors(value: Any, path: str = "recipe") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z]", "", key.lower())
            if normalized in COORDINATE_KEYS:
                errors.append(f"{path}.{key}: semantic recipes may not contain pixel coordinates")
            errors.extend(_coordinate_key_errors(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_coordinate_key_errors(child, f"{path}[{index}]"))
    return errors


def _get_field(recipe: dict[str, Any], dotted_field: str) -> Any:
    value: Any = recipe
    for part in dotted_field.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _matches(recipe: dict[str, Any], condition: dict[str, Any]) -> bool:
    return _get_field(recipe, condition["field"]) in condition["values"]


def _derived_panel_region(panel_layout: str) -> str:
    return {
        "center_placket": "placket",
        "split_outer_panels": "inner_layer",
        "yoke": "yoke",
        "upper_lower_split": "hem",
    }.get(panel_layout, "body")


def feature_color_region(feature: str, recipe: dict[str, Any], data: dict[str, Any]) -> str:
    model = data["vocabulary"]["substantialFeatures"][feature]
    region = model["colorRegion"]
    if region == "derived_panel":
        return _derived_panel_region(recipe["construction"]["panelLayout"])
    return region


def required_features_for_construction(
    construction: dict[str, str], archetype: dict[str, Any]
) -> set[str]:
    required: set[str] = set()
    for link in archetype.get("constructionFeatureLinks", ()): 
        if construction.get(link["field"]) in link["values"]:
            choices = link["requiresAnyFeature"]
            if len(choices) == 1:
                required.add(choices[0])
    return required


def _validate_construction_rules(
    recipe: dict[str, Any], archetype: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    construction = recipe.get("construction", {})
    for field in CONSTRUCTION_FIELDS:
        value = construction.get(field)
        if value not in archetype["allowedConstruction"][field]:
            errors.append(f"{archetype['id']} does not allow construction.{field}={value!r}")
    rarity_rules = archetype.get("rarityConstruction", {}).get(recipe.get("rarity"), {})
    for field, allowed_values in rarity_rules.items():
        if construction.get(field) not in allowed_values:
            errors.append(
                f"{recipe.get('rarity')} {archetype['id']} does not allow "
                f"construction.{field}={construction.get(field)!r}"
            )
    for rule in archetype.get("constructionRules", ()):
        when = rule["when"]
        if construction.get(when["field"]) not in when["values"]:
            continue
        for requirement in rule.get("requiresAll", ()):
            if construction.get(requirement["field"]) not in requirement["values"]:
                errors.append(
                    f"construction.{when['field']}={construction.get(when['field'])!r} requires "
                    f"construction.{requirement['field']} in {requirement['values']}"
                )
        for exclusion in rule.get("excludes", ()):
            if construction.get(exclusion["field"]) in exclusion["values"]:
                errors.append(
                    f"construction.{when['field']}={construction.get(when['field'])!r} excludes "
                    f"construction.{exclusion['field']} in {exclusion['values']}"
                )
    if construction.get("collar") == "wide" and construction.get("neckline") not in {
        "shallow_v",
        "open",
    }:
        errors.append("wide collar requires shallow_v or open neckline")
    if construction.get("collar") == "sailor" and construction.get("neckline") != "open":
        errors.append("sailor collar requires open neckline")
    if construction.get("closure") in {"center_open", "buttons"} and construction.get("neckline") != "open":
        errors.append("center closure requires open neckline")
    return errors


def validate_recipe_v2(
    recipe: dict[str, Any], data: dict[str, Any], *, schema: bool = True
) -> V2RecipeValidation:
    errors: list[str] = []
    warnings: list[str] = []
    if schema:
        errors.extend(_schema_errors(recipe, data["schema"]))
    errors.extend(_coordinate_key_errors(recipe))
    archetype_id = recipe.get("archetype")
    archetype = data["archetypes"].get(archetype_id)
    if archetype is None:
        errors.append(f"unknown archetype {archetype_id!r}")
        return V2RecipeValidation(False, tuple(errors), tuple(warnings), {})

    errors.extend(_validate_construction_rules(recipe, archetype))
    substantial = recipe.get("substantialFeatures", [])
    micro = recipe.get("microDetails", [])
    if len(substantial) != len(set(substantial)):
        errors.append("substantialFeatures must be unique")
    if len(micro) != len(set(micro)):
        errors.append("microDetails must be unique")
    for feature in substantial:
        model = data["vocabulary"]["substantialFeatures"].get(feature)
        if model is None:
            errors.append(f"unknown substantial feature {feature!r}")
            continue
        if archetype_id not in model["allowedArchetypes"] or feature not in archetype["allowedSubstantialFeatures"]:
            errors.append(f"{feature} is incompatible with {archetype_id}")
        for requirement in model["requiresAll"]:
            if not _matches(recipe, requirement):
                errors.append(f"{feature} requires {requirement['field']} in {requirement['values']}")
    if len(substantial) > 1:
        feature_regions = [
            feature_color_region(feature, recipe, data)
            for feature in substantial
            if feature in data["vocabulary"]["substantialFeatures"]
        ]
        if len(feature_regions) != len(set(feature_regions)):
            errors.append(
                "substantial features may not be aliases for the same major region: "
                + ", ".join(feature_regions)
            )
    for detail in micro:
        model = data["vocabulary"]["microDetails"].get(detail)
        if model is None:
            errors.append(f"unknown micro detail {detail!r}")
            continue
        if archetype_id not in model["allowedArchetypes"] or detail not in archetype["allowedMicroDetails"]:
            errors.append(f"{detail} is incompatible with {archetype_id}")
        for requirement in model["requiresAll"]:
            if not _matches(recipe, requirement):
                errors.append(f"{detail} requires {requirement['field']} in {requirement['values']}")

    construction = recipe.get("construction", {})
    for link in archetype.get("constructionFeatureLinks", ()):
        if construction.get(link["field"]) in link["values"] and not any(
            feature in substantial for feature in link["requiresAnyFeature"]
        ):
            errors.append(
                f"construction.{link['field']}={construction.get(link['field'])!r} requires a feature in "
                f"{link['requiresAnyFeature']}"
            )

    rarity = recipe.get("rarity")
    rarity_budget = data["budgets"]["rarities"].get(rarity)
    if rarity_budget is None:
        errors.append(f"unknown rarity {rarity!r}")
        rarity_budget = {}
    else:
        if not rarity_budget["minimumSubstantialFeatures"] <= len(substantial) <= rarity_budget["maximumSubstantialFeatures"]:
            errors.append(
                f"{rarity} requires {rarity_budget['minimumSubstantialFeatures']}.."
                f"{rarity_budget['maximumSubstantialFeatures']} substantial features, got {len(substantial)}"
            )
        if len(micro) > rarity_budget["maximumMicroDetails"]:
            errors.append(f"{rarity} allows at most {rarity_budget['maximumMicroDetails']} micro details")
        if rarity == "Rare" and not substantial:
            errors.append("Rare identity must be structural, not micro-only")
        if rarity == "Rare" and len(substantial) == 1:
            warnings.append("Rare recipe uses one substantial feature; valid, but composition needs human review")

    blocking = recipe.get("colorBlocking", {})
    primary = blocking.get("primaryRegion")
    secondary = blocking.get("secondaryRegion")
    accent_region = blocking.get("accentRegion")
    if primary not in archetype["primaryRegions"]:
        errors.append(f"{archetype_id} cannot use primaryRegion={primary!r}")
    if secondary != "none" and secondary not in archetype["availableColorRegions"]:
        errors.append(f"{archetype_id} cannot use secondaryRegion={secondary!r}")
    if accent_region != "none" and accent_region not in archetype["availableColorRegions"]:
        errors.append(f"{archetype_id} cannot use accentRegion={accent_region!r}")
    if substantial:
        visible_regions = {
            feature_color_region(feature, recipe, data)
            for feature in substantial
            if feature in data["vocabulary"]["substantialFeatures"]
        }
        if secondary == "none":
            errors.append("substantial features require an explicit secondary structural region")
        elif secondary not in visible_regions:
            errors.append(
                f"secondaryRegion={secondary!r} does not describe any substantial feature region "
                f"{sorted(visible_regions)}"
            )
    if micro:
        if recipe.get("accent") == "none" or accent_region == "none":
            errors.append("micro details require an authored accent and accentRegion")
        expected_micro_regions = {
            data["vocabulary"]["microDetails"][detail]["colorRegion"]
            for detail in micro
            if detail in data["vocabulary"]["microDetails"]
        }
        if accent_region not in expected_micro_regions:
            errors.append(
                f"accentRegion={accent_region!r} does not match micro detail region "
                f"{sorted(expected_micro_regions)}"
            )
    elif recipe.get("accent") != "none" or accent_region != "none":
        errors.append("accent and accentRegion must both be none when no micro detail exists")

    major_regions = 1 + int(secondary != "none") + int(accent_region != "none")
    if rarity_budget and major_regions > rarity_budget["maximumMajorColorRegions"]:
        errors.append(
            f"{rarity} allows at most {rarity_budget['maximumMajorColorRegions']} color regions, got {major_regions}"
        )
    if construction.get("closure") == "buttons" and archetype_id == "JACKET":
        warnings.append("Closed button jacket is legal but visually riskier than split open outerwear")
    if "single_accent_pixel" in micro:
        warnings.append("Intentional single-pixel accent requires visual review at normal game scale")
    complexity = {
        "substantialFeatures": len(substantial),
        "microDetails": len(micro),
        "majorColorRegions": major_regions,
        "motifs": int(bool(micro)),
    }
    return V2RecipeValidation(not errors, tuple(errors), tuple(warnings), complexity)


def _construction_product(archetype: dict[str, Any]) -> Iterable[dict[str, str]]:
    allowed = archetype["allowedConstruction"]
    for values in itertools.product(*(allowed[field] for field in CONSTRUCTION_FIELDS)):
        yield dict(zip(CONSTRUCTION_FIELDS, values, strict=True))


def _stable_tiebreak(value: Any, seed: int) -> int:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return int(hashlib.sha256(f"{seed}:{payload}".encode("utf-8")).hexdigest()[:16], 16)


def _micro_options(
    archetype: dict[str, Any], construction: dict[str, str], want_micro: bool
) -> list[list[str]]:
    if not want_micro:
        return [[]]
    options: list[list[str]] = []
    for detail in archetype["allowedMicroDetails"]:
        if detail == "tiny_button" and construction["closure"] != "buttons":
            continue
        if detail == "tiny_trim_mark" and construction["hem"] == "plain":
            continue
        options.append([detail])
    return options or [[]]


def derive_color_blocking(
    archetype_id: str,
    construction: dict[str, str],
    substantial: list[str],
    micro: list[str],
    data: dict[str, Any],
) -> dict[str, str]:
    shell = {
        "archetype": archetype_id,
        "construction": construction,
    }
    primary = "outer_panels" if archetype_id == "JACKET" else "body"
    regions = {
        feature: feature_color_region(feature, shell, data)
        for feature in substantial
    }
    secondary = "none"
    for feature in FEATURE_PRIORITY:
        if feature in regions:
            secondary = regions[feature]
            break
    if micro:
        accent_region = data["vocabulary"]["microDetails"][micro[0]]["colorRegion"]
    else:
        accent_region = "none"
    return {
        "primaryRegion": primary,
        "secondaryRegion": secondary,
        "accentRegion": accent_region,
    }


def _reference_traits(archetype_id: str, construction: dict[str, str]) -> list[str]:
    traits = ["compact_straight", "restrained_palette", "practical_fit"]
    if construction["layering"] != "single_layer":
        traits[1] = "clean_layering"
    if construction["collar"] != "none":
        traits.append("disciplined_collar")
    else:
        traits.append("localized_contrast")
    if construction["panelLayout"] != "solid":
        traits[-1] = "structural_color_blocking"
    return traits[:4]


def _descriptor(archetype_id: str, construction: dict[str, str], substantial: list[str]) -> str:
    features = set(substantial)
    if archetype_id == "T_SHIRT":
        if "wrapping_stripe" in features:
            return "Stripe Tee"
        if "major_panel_contrast" in features:
            return "Block Tee"
        if "structured_lower_band" in features:
            return "Band Tee"
        return "Everyday Tee"
    if archetype_id == "SWEATER":
        if "yoke" in features:
            return "Yoke Sweater"
        if "broad_collar" in features:
            return "Collar Sweater"
        if "wrapping_stripe" in features:
            return "Stripe Sweater"
        if "major_panel_contrast" in features:
            return "Block Sweater"
        if "structured_lower_band" in features:
            return "Band Sweater"
        return "Ribbed Sweater"
    if archetype_id == "BUTTON_SHIRT":
        if "yoke" in features:
            return "Yoke Work Shirt"
        if "structured_lower_band" in features:
            return "Band-Placket Shirt"
        return "Placket Shirt"
    if archetype_id == "JACKET":
        if construction["closure"] == "buttons":
            return "Button Work Jacket"
        if "broad_collar" in features:
            return "Lapel Layer Jacket"
        if "contrast_inner_layer" in features:
            return "Layered Panel Jacket"
        return "Open Panel Jacket"
    if "broad_collar" in features:
        return "Broad-Collar Top"
    if "wrapping_stripe" in features:
        return "Yoke-Stripe Top"
    if "major_panel_contrast" in features:
        return "Block-Collar Top"
    return "Yoke Top"


def _description(
    archetype_id: str,
    rarity: str,
    construction: dict[str, str],
    substantial: list[str],
    palette_family: str,
) -> str:
    garment = {
        "T_SHIRT": "everyday tee",
        "SWEATER": "weighty sweater",
        "BUTTON_SHIRT": "tailored work shirt",
        "JACKET": "outer jacket",
        "SAILOR_TOP": "sailor top",
    }[archetype_id]
    fit = {
        "fitted": "fitted",
        "regular": "classic-cut",
        "relaxed": "relaxed",
    }[construction["fit"]]
    feature_names = {
        "contrast_inner_layer": "a contrast inner layer",
        "broad_collar": "a broad collar",
        "ribbed_hem": "a broad ribbed hem",
        "major_panel_contrast": "major panel blocking",
        "center_placket": "a tailored center placket",
        "wrapping_stripe": "a wrapping stripe",
        "yoke": "a broad yoke",
        "split_outer_panels": "split outer panels",
        "structured_lower_band": "a structured lower band",
    }
    if substantial:
        named_features = [feature_names[feature] for feature in substantial]
        feature_text = (
            named_features[0]
            if len(named_features) == 1
            else f"{named_features[0]} and {named_features[1]}"
        )
        construction_sentence = f"built around {feature_text}"
    else:
        construction_sentence = "finished with clean, simple construction"
    rarity_article = "an" if rarity == "Uncommon" else "a"
    return (
        f"A {fit} {garment} {construction_sentence}. "
        f"{rarity_article.capitalize()} {rarity} Lifestyle design in "
        f"{palette_family.replace('_', ' / ')} tones."
    )


def _accent_for(
    palette_family: str,
    micro: list[str],
    data: dict[str, Any],
    seed: int,
    signature: Any,
) -> str:
    if not micro:
        return "none"
    choices = data["palettes"]["families"][palette_family]["allowedAccents"]
    return choices[_stable_tiebreak(signature, seed) % len(choices)]


def structural_signature(recipe: dict[str, Any]) -> tuple[Any, ...]:
    return (
        recipe["archetype"],
        *(recipe["construction"][field] for field in CONSTRUCTION_FIELDS),
        tuple(sorted(recipe["substantialFeatures"])),
        recipe["colorBlocking"]["primaryRegion"],
        recipe["colorBlocking"]["secondaryRegion"],
    )


def structural_distance(first: dict[str, Any], second: dict[str, Any]) -> int:
    if first["archetype"] != second["archetype"]:
        return 99
    distance = sum(
        first["construction"][field] != second["construction"][field]
        for field in CONSTRUCTION_FIELDS
    )
    distance += len(set(first["substantialFeatures"]) ^ set(second["substantialFeatures"]))
    distance += first["colorBlocking"]["secondaryRegion"] != second["colorBlocking"]["secondaryRegion"]
    return distance


def _candidate_quality(recipe: dict[str, Any]) -> int:
    construction = recipe["construction"]
    score = sum(FEATURE_QUALITY[feature] for feature in recipe["substantialFeatures"])
    score += 3 * (construction["panelLayout"] != "solid")
    score += 2 * (construction["layering"] != "single_layer")
    score += 2 * (construction["hem"] != "plain")
    if recipe["archetype"] == "T_SHIRT" and recipe["rarity"] == "Common":
        score += 8 * (not recipe["substantialFeatures"])
    if recipe["archetype"] == "SWEATER":
        score += 7 * ("ribbed_hem" in recipe["substantialFeatures"])
    if recipe["archetype"] == "BUTTON_SHIRT":
        score += 7 * (construction["panelLayout"] == "center_placket")
    if recipe["archetype"] == "JACKET":
        score += 12 * (construction["panelLayout"] == "split_outer_panels")
        score += 8 * (construction["layering"] == "visible_inner_layer")
    if recipe["archetype"] == "SAILOR_TOP":
        score += 10 * (construction["panelLayout"] == "yoke")
        score += 6 * (construction["collar"] == "sailor")
    return score


def _feature_combinations(
    archetype: dict[str, Any], construction: dict[str, str], count: int
) -> Iterable[list[str]]:
    required = required_features_for_construction(construction, archetype)
    if len(required) > count:
        return []
    combinations = []
    for values in itertools.combinations(archetype["allowedSubstantialFeatures"], count):
        if required <= set(values):
            combinations.append(list(values))
    return combinations


def _build_candidates(
    archetype_id: str,
    rarity: str,
    palette_family: str,
    generation_index: int,
    substantial_count: int,
    want_micro: bool,
    seed: int,
    data: dict[str, Any],
) -> list[dict[str, Any]]:
    archetype = data["archetypes"][archetype_id]
    candidates: list[dict[str, Any]] = []
    for construction in _construction_product(archetype):
        shell = {
            "archetype": archetype_id,
            "construction": construction,
            "substantialFeatures": [],
            "microDetails": [],
            "rarity": rarity,
            "colorBlocking": {"primaryRegion": "body", "secondaryRegion": "none", "accentRegion": "none"},
            "accent": "none",
        }
        if _validate_construction_rules(shell, archetype):
            continue
        for substantial in _feature_combinations(archetype, construction, substantial_count):
            for micro in _micro_options(archetype, construction, want_micro):
                blocking = derive_color_blocking(archetype_id, construction, substantial, micro, data)
                signature = (archetype_id, construction, substantial, micro, palette_family)
                accent = _accent_for(palette_family, micro, data, seed, signature)
                item_name = f"{PALETTE_PREFIX[palette_family]} {_descriptor(archetype_id, construction, substantial)}"
                recipe = {
                    "id": f"lifestyle-v2-{generation_index:02d}",
                    "generationIndex": generation_index,
                    "seed": seed + generation_index * 7919,
                    "category": "Lifestyle",
                    "styleProfile": "General",
                    "referenceTraits": _reference_traits(archetype_id, construction),
                    "archetype": archetype_id,
                    "rarity": rarity,
                    "construction": construction,
                    "substantialFeatures": substantial,
                    "microDetails": micro,
                    "colorBlocking": blocking,
                    "paletteFamily": palette_family,
                    "accent": accent,
                    "dyeable": True,
                    "itemName": item_name,
                    "itemDescription": _description(
                        archetype_id, rarity, construction, substantial, palette_family
                    ),
                }
                if validate_recipe_v2(recipe, data).valid:
                    candidates.append(recipe)
    return candidates


def generate_v2_recipes(
    data: dict[str, Any], seed: int = GENERATOR_V2_SEED
) -> list[dict[str, Any]]:
    recipes: list[dict[str, Any]] = []
    generation_index = 0
    common_seen: dict[str, int] = {archetype: 0 for archetype in ARCHETYPE_ORDER}
    for archetype_position, archetype_id in enumerate(ARCHETYPE_ORDER):
        chosen_for_archetype: list[dict[str, Any]] = []
        for slot, rarity in enumerate(RARITY_SCHEDULE[archetype_id]):
            generation_index += 1
            if rarity == "Common":
                substantial_count = 0 if archetype_id == "T_SHIRT" and common_seen[archetype_id] == 0 else 1
                common_seen[archetype_id] += 1
            elif rarity == "Uncommon":
                substantial_count = 1
            else:
                substantial_count = 2
            want_micro = rarity != "Common" and (generation_index + archetype_position) % 2 == 0
            palette = PALETTE_SCHEDULE[archetype_id][slot]
            candidates = _build_candidates(
                archetype_id,
                rarity,
                palette,
                generation_index,
                substantial_count,
                want_micro,
                seed,
                data,
            )
            if not candidates:
                raise RuntimeError(
                    f"no V2 candidates for {archetype_id} {rarity} with {substantial_count} substantial features"
                )
            diverse_candidates = [
                candidate
                for candidate in candidates
                if all(
                    structural_distance(candidate, prior) >= 2
                    for prior in chosen_for_archetype
                )
            ]
            if not diverse_candidates:
                raise RuntimeError(
                    f"no non-redundant V2 candidate remains for {archetype_id} slot {slot + 1}"
                )

            def rank(candidate: dict[str, Any]) -> tuple[int, int, int, int]:
                minimum_distance = min(
                    (structural_distance(candidate, prior) for prior in chosen_for_archetype),
                    default=99,
                )
                quality = _candidate_quality(candidate)
                return (
                    quality + minimum_distance * 2,
                    quality,
                    minimum_distance,
                    _stable_tiebreak(structural_signature(candidate), seed),
                )

            chosen = max(diverse_candidates, key=rank)
            chosen_for_archetype.append(chosen)
            recipes.append(chosen)
    if len(recipes) != 20:
        raise RuntimeError(f"expected 20 V2 recipes, got {len(recipes)}")
    return recipes


def review_v2_redundancy(recipes: list[dict[str, Any]]) -> dict[str, Any]:
    exact: list[list[str]] = []
    near: list[dict[str, Any]] = []
    for index, first in enumerate(recipes):
        for second in recipes[index + 1 :]:
            if first["archetype"] != second["archetype"]:
                continue
            if structural_signature(first) == structural_signature(second):
                exact.append([first["id"], second["id"]])
                continue
            distance = structural_distance(first, second)
            if distance < 2:
                near.append({"recipeIds": [first["id"], second["id"]], "distance": distance})
    return {
        "exactDuplicateCount": len(exact),
        "nearDuplicateCount": len(near),
        "minimumAcceptedStructuralDistance": 2,
        "exactDuplicates": exact,
        "nearDuplicates": near,
    }


def _migration_base_construction(v1: dict[str, Any]) -> dict[str, str]:
    archetype = v1["archetype"]
    fit = v1["fit"]
    neckline = v1["neckline"]
    collar = v1["collar"]
    closure = v1["closure"]
    if archetype == "T_SHIRT":
        return {
            "fit": fit,
            "neckline": neckline,
            "collar": "none",
            "closure": "none",
            "layering": "single_layer",
            "hem": "contrast_band" if v1["detail"] == "lower_trim" or v1["pattern"] == "simple_border" else "plain",
            "panelLayout": "upper_lower_split" if "center_stripe" in {v1["detail"], v1.get("secondaryDetail")} else "solid",
        }
    if archetype == "SWEATER":
        use_yoke = collar == "wide"
        return {
            "fit": fit,
            "neckline": neckline,
            "collar": collar,
            "closure": "none",
            "layering": "overlay_panel" if use_yoke else "single_layer",
            "hem": (
                "structured"
                if use_yoke
                else "ribbed"
                if "lower_trim" in {v1["detail"], v1.get("secondaryDetail")}
                else "structured"
            ),
            "panelLayout": "yoke" if use_yoke else "solid",
        }
    if archetype == "BUTTON_SHIRT":
        return {
            "fit": fit,
            "neckline": "open",
            "collar": "small_folded",
            "closure": "buttons",
            "layering": "single_layer",
            "hem": "contrast_band" if v1["pattern"] == "simple_border" else "plain",
            "panelLayout": "center_placket",
        }
    if archetype == "JACKET":
        is_open = closure == "center_open"
        return {
            "fit": fit,
            "neckline": "open",
            "collar": collar if collar != "none" else "small_folded",
            "closure": closure,
            "layering": "visible_inner_layer" if is_open else "overlay_panel",
            "hem": "contrast_band" if "lower_trim" in {v1["detail"], v1.get("secondaryDetail")} or v1["pattern"] == "simple_border" else "structured",
            "panelLayout": "split_outer_panels" if is_open else "center_placket",
        }
    sailor_hem = (
        "contrast_band"
        if v1["rarity"] == "Rare"
        and (
            "lower_trim" in {v1["detail"], v1.get("secondaryDetail")}
            or v1["pattern"] == "simple_border"
        )
        else "plain"
    )
    return {
        "fit": fit,
        "neckline": neckline,
        "collar": collar,
        "closure": "none",
        "layering": "overlay_panel",
        "hem": sailor_hem,
        "panelLayout": "yoke",
    }


def _migration_candidates(v1: dict[str, Any], construction: dict[str, str]) -> tuple[list[str], list[str], list[str]]:
    archetype = v1["archetype"]
    old_details = [value for value in (v1["detail"], v1.get("secondaryDetail")) if value and value != "none"]
    substantial: list[str] = []
    micro: list[str] = []
    notes: list[str] = []
    required = required_features_for_construction(construction, {**{}, "constructionFeatureLinks": []})
    # Archetype-defining construction links are inserted by the caller; this
    # placeholder keeps the old-field translation below independent.
    del required
    detail_map = {
        "lower_trim": "ribbed_hem" if archetype == "SWEATER" else "structured_lower_band",
        "inner_layer": "contrast_inner_layer",
        "button_line": "center_placket",
        "center_stripe": "major_panel_contrast" if archetype in {"T_SHIRT", "SAILOR_TOP"} else "wrapping_stripe",
    }
    for old in old_details:
        if old == "chest_accent":
            micro.append("small_chest_accent")
            notes.append("detail chest_accent -> microDetails small_chest_accent")
        elif old in detail_map:
            substantial.append(detail_map[old])
            notes.append(f"detail {old} -> substantialFeatures {detail_map[old]}")
    if v1["pattern"] == "horizontal_stripe":
        substantial.append("wrapping_stripe")
        notes.append("pattern horizontal_stripe -> substantialFeatures wrapping_stripe")
    elif v1["pattern"] == "vertical_trim":
        substantial.append("center_placket" if archetype in {"BUTTON_SHIRT", "JACKET"} else "major_panel_contrast")
        notes.append("pattern vertical_trim -> placket/panel construction rather than a decorative pixel line")
    elif v1["pattern"] == "simple_border":
        substantial.append("structured_lower_band")
        notes.append("pattern simple_border -> hem construction plus structured_lower_band")
    if "button_line" in old_details:
        micro.append("tiny_button")
        notes.append("button pixels were demoted to microDetails tiny_button; the placket remains structural")
    return list(dict.fromkeys(substantial)), list(dict.fromkeys(micro)), notes


def migrate_v1_recipes(
    data: dict[str, Any], v1_batch: dict[str, Any] | None = None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if v1_batch is None:
        v1_batch = load_json(V1_RECIPE_PATH)
    migrated: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    for index, v1 in enumerate(v1_batch["recipes"], start=1):
        archetype = data["archetypes"][v1["archetype"]]
        construction = _migration_base_construction(v1)
        substantial, micro, notes = _migration_candidates(v1, construction)
        required = required_features_for_construction(construction, archetype)
        substantial = list(dict.fromkeys([*required, *substantial]))
        budget = data["budgets"]["rarities"][v1["rarity"]]
        allowed_features = set(archetype["allowedSubstantialFeatures"])
        removed_incompatible = [feature for feature in substantial if feature not in allowed_features]
        if removed_incompatible:
            notes.append(
                "incompatible V1 translations removed: " + ", ".join(removed_incompatible)
            )
        substantial = [feature for feature in substantial if feature in allowed_features]
        priority = [feature for feature in FEATURE_PRIORITY if feature in required]
        priority += [feature for feature in FEATURE_PRIORITY if feature in substantial]
        substantial = list(dict.fromkeys(priority))
        dropped_features = substantial[budget["maximumSubstantialFeatures"] :]
        substantial = substantial[: budget["maximumSubstantialFeatures"]]
        if dropped_features:
            notes.append(
                f"{v1['rarity']} budget retained construction-first features and dropped/deferred: "
                + ", ".join(dropped_features)
            )
        # A link can become invalid after budget clipping. Prefer the linked
        # feature, then re-clip while preserving order.
        required = required_features_for_construction(construction, archetype)
        ordered_required = [feature for feature in FEATURE_PRIORITY if feature in required]
        substantial = list(dict.fromkeys([*ordered_required, *substantial]))[
            : budget["maximumSubstantialFeatures"]
        ]
        allowed_micro = set(archetype["allowedMicroDetails"])
        micro = [detail for detail in micro if detail in allowed_micro]
        dropped_micro = micro[budget["maximumMicroDetails"] :]
        micro = micro[: budget["maximumMicroDetails"]]
        if dropped_micro:
            notes.append(
                f"{v1['rarity']} micro budget dropped/deferred: " + ", ".join(dropped_micro)
            )
        blocking = derive_color_blocking(v1["archetype"], construction, substantial, micro, data)
        accent = v1["accent"] if micro and v1["accent"] != "none" else "none"
        if micro and accent == "none":
            accent = data["palettes"]["families"][v1["paletteFamily"]]["allowedAccents"][0]
        recipe = {
            "id": f"lifestyle-v2-migrated-{index:02d}",
            "generationIndex": index,
            "seed": v1["seed"],
            "category": v1["category"],
            "styleProfile": v1["styleProfile"],
            "referenceTraits": list(v1["referenceTraits"]),
            "archetype": v1["archetype"],
            "rarity": v1["rarity"],
            "construction": construction,
            "substantialFeatures": substantial,
            "microDetails": micro,
            "colorBlocking": blocking,
            "paletteFamily": v1["paletteFamily"],
            "accent": accent,
            "dyeable": True,
            "itemName": v1["itemName"],
            "itemDescription": v1["itemDescription"],
        }
        validation = validate_recipe_v2(recipe, data)
        if not validation.valid:
            raise RuntimeError(
                f"migration failed for {v1['id']}: {'; '.join(validation.errors)}"
            )
        migrated.append(recipe)
        records.append(
            {
                "sourceRecipeId": v1["id"],
                "sourceName": v1["itemName"],
                "sourceFlatFields": {
                    "detail": v1["detail"],
                    "secondaryDetail": v1.get("secondaryDetail"),
                    "pattern": v1["pattern"],
                },
                "targetRecipeId": recipe["id"],
                "construction": construction,
                "substantialFeatures": substantial,
                "microDetails": micro,
                "colorBlocking": blocking,
                "mappingNotes": notes or ["No V1 decoration existed; construction was inferred from archetype."],
                "warning": "Faithful deterministic migration for regression comparison; not an optimal V2 redesign.",
            }
        )
    if len(migrated) != 20:
        raise RuntimeError(f"expected 20 migrated V1 recipes, got {len(migrated)}")
    return migrated, records


def slugify(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    if not result:
        raise ValueError("cannot slugify empty value")
    return result


def pascal_identifier(value: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", value)
    if not words:
        raise ValueError("cannot build identifier")
    return "".join(word[:1].upper() + word[1:] for word in words)
