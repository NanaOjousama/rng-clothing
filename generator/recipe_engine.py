"""Deterministic semantic recipe generation and compatibility validation."""

from __future__ import annotations

import itertools
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "generator" / "data"
ARCHETYPE_DIR = DATA_DIR / "archetypes"
SCHEMA_PATH = ROOT / "generator" / "schema" / "garment_recipe.schema.json"

GENERATOR_SEED = 202608281615
ARCHETYPE_ORDER = ("T_SHIRT", "SWEATER", "BUTTON_SHIRT", "JACKET", "SAILOR_TOP")
RARITY_SCHEDULE = {
    "T_SHIRT": ("Common", "Common", "Uncommon", "Rare"),
    "SWEATER": ("Common", "Uncommon", "Uncommon", "Rare"),
    "BUTTON_SHIRT": ("Common", "Uncommon", "Rare", "Uncommon"),
    "JACKET": ("Common", "Uncommon", "Rare", "Rare"),
    "SAILOR_TOP": ("Common", "Uncommon", "Rare", "Uncommon"),
}
PALETTE_SCHEDULE = {
    "T_SHIRT": ("navy_ivory", "sage_tan", "denim_cream", "warm_neutral"),
    "SWEATER": ("rust_brown", "forest_cream", "cool_neutral", "charcoal_burgundy"),
    "BUTTON_SHIRT": ("warm_neutral", "sage_tan", "navy_ivory", "denim_cream"),
    "JACKET": ("forest_cream", "charcoal_burgundy", "rust_brown", "cool_neutral"),
    "SAILOR_TOP": ("navy_ivory", "sage_tan", "charcoal_burgundy", "denim_cream"),
}
SELECTED_RARITY = {
    "T_SHIRT": "Uncommon",
    "SWEATER": "Common",
    "BUTTON_SHIRT": "Common",
    "JACKET": "Rare",
    "SAILOR_TOP": "Rare",
}

SEMANTIC_FIELDS = (
    "fit",
    "neckline",
    "collar",
    "closure",
    "detail",
    "secondaryDetail",
    "pattern",
    "paletteFamily",
    "accent",
    "rarity",
)
VISUAL_FIELDS = (
    "fit",
    "neckline",
    "collar",
    "closure",
    "detail",
    "secondaryDetail",
    "pattern",
    "accent",
)

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


@dataclass(frozen=True)
class RecipeValidation:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    complexity: dict[str, int]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_data() -> dict[str, Any]:
    archetypes = {
        path.stem: load_json(path)
        for path in sorted(ARCHETYPE_DIR.glob("*.json"))
    }
    if tuple(sorted(archetypes)) != tuple(sorted(ARCHETYPE_ORDER)):
        raise ValueError(f"expected exactly five V1 archetypes, found {sorted(archetypes)}")
    return {
        "grammar": load_json(DATA_DIR / "vanilla_shirt_grammar.json"),
        "palettes": load_json(DATA_DIR / "palette_rules.json"),
        "budgets": load_json(DATA_DIR / "complexity_budgets.json"),
        "components": load_json(DATA_DIR / "components.json"),
        "schema": load_json(SCHEMA_PATH),
        "archetypes": archetypes,
    }


def recipe_details(recipe: dict[str, Any]) -> list[str]:
    details = []
    if recipe.get("detail") not in (None, "none"):
        details.append(recipe["detail"])
    if recipe.get("secondaryDetail") not in (None, "none"):
        details.append(recipe["secondaryDetail"])
    return details


def _field_value_matches(recipe: dict[str, Any], field: str, values: list[str]) -> bool:
    if field == "detail":
        return any(detail in values for detail in recipe_details(recipe))
    return recipe.get(field) in values


def _schema_errors(recipe: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = set(schema["required"])
    properties = schema["properties"]
    missing = sorted(required - set(recipe))
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
    if schema.get("additionalProperties") is False:
        extras = sorted(set(recipe) - set(properties))
        if extras:
            errors.append(f"unexpected fields: {', '.join(extras)}")
    for field, rules in properties.items():
        if field not in recipe:
            continue
        value = recipe[field]
        if "const" in rules and value != rules["const"]:
            errors.append(f"{field} must be {rules['const']!r}")
        if "enum" in rules and value not in rules["enum"]:
            errors.append(f"{field} has unsupported value {value!r}")
        expected_type = rules.get("type")
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"{field} must be a string")
        elif expected_type == "integer" and (not isinstance(value, int) or isinstance(value, bool)):
            errors.append(f"{field} must be an integer")
        elif expected_type == "array" and not isinstance(value, list):
            errors.append(f"{field} must be an array")
        if isinstance(value, str):
            if "minLength" in rules and len(value) < rules["minLength"]:
                errors.append(f"{field} is too short")
            if "maxLength" in rules and len(value) > rules["maxLength"]:
                errors.append(f"{field} is too long")
            if "pattern" in rules and not re.match(rules["pattern"], value):
                errors.append(f"{field} does not match {rules['pattern']}")
        if isinstance(value, int) and not isinstance(value, bool):
            if "minimum" in rules and value < rules["minimum"]:
                errors.append(f"{field} is below its minimum")
            if "maximum" in rules and value > rules["maximum"]:
                errors.append(f"{field} is above its maximum")
        if isinstance(value, list):
            if "minItems" in rules and len(value) < rules["minItems"]:
                errors.append(f"{field} has too few items")
            if "maxItems" in rules and len(value) > rules["maxItems"]:
                errors.append(f"{field} has too many items")
            if rules.get("uniqueItems") and len(value) != len({json.dumps(item, sort_keys=True) for item in value}):
                errors.append(f"{field} must contain unique items")
            item_rules = rules.get("items", {})
            if "enum" in item_rules:
                for item in value:
                    if item not in item_rules["enum"]:
                        errors.append(f"{field} contains unsupported item {item!r}")
    return errors


def validate_recipe(recipe: dict[str, Any], data: dict[str, Any], *, partial: bool = False) -> RecipeValidation:
    errors: list[str] = []
    warnings: list[str] = []
    if not partial:
        errors.extend(_schema_errors(recipe, data["schema"]))
    archetype_id = recipe.get("archetype")
    archetype = data["archetypes"].get(archetype_id)
    if archetype is None:
        errors.append(f"unknown archetype {archetype_id!r}")
        return RecipeValidation(False, tuple(errors), tuple(warnings), {})

    archetype_fields = {
        "fit": "validFits",
        "neckline": "validNecklines",
        "collar": "validCollars",
        "closure": "validClosures",
        "detail": "validDetails",
        "pattern": "validPatterns",
    }
    for field, allowed_field in archetype_fields.items():
        value = recipe.get(field)
        if value not in archetype[allowed_field]:
            errors.append(f"{archetype_id} does not allow {field}={value!r}")
    secondary = recipe.get("secondaryDetail")
    if secondary is not None and secondary not in archetype["validDetails"]:
        errors.append(f"{archetype_id} does not allow secondaryDetail={secondary!r}")

    components = data["components"]
    component_values = {
        "fit": [recipe.get("fit")],
        "neckline": [recipe.get("neckline")],
        "collar": [recipe.get("collar")],
        "closure": [recipe.get("closure")],
        "detail": [recipe.get("detail")] + ([secondary] if secondary else []),
        "pattern": [recipe.get("pattern")],
    }
    for component_type, values in component_values.items():
        for value in values:
            model = components[component_type].get(value)
            if model is None:
                errors.append(f"unknown {component_type} component {value!r}")
                continue
            if archetype_id not in model["allowedArchetypes"]:
                errors.append(f"{component_type}={value!r} is incompatible with {archetype_id}")
            for requirement in model["requiresAll"]:
                if not _field_value_matches(recipe, requirement["field"], requirement["values"]):
                    errors.append(
                        f"{component_type}={value!r} requires "
                        f"{requirement['field']} in {requirement['values']}"
                    )
            for exclusion in model["excludes"]:
                if _field_value_matches(recipe, exclusion["field"], exclusion["values"]):
                    errors.append(
                        f"{component_type}={value!r} excludes "
                        f"{exclusion['field']} in {exclusion['values']}"
                    )

    details = recipe_details(recipe)
    if secondary == "none":
        errors.append("secondaryDetail must be null or a non-none detail")
    if secondary is not None and recipe.get("detail") == "none":
        errors.append("secondaryDetail requires a non-none primary detail")
    if secondary is not None and secondary == recipe.get("detail"):
        errors.append("primary and secondary details must differ")
    if secondary is not None and recipe.get("rarity") != "Rare":
        errors.append("secondaryDetail is only allowed for Rare recipes")
    if "center_stripe" in details and recipe.get("pattern") == "horizontal_stripe":
        errors.append("center_stripe conflicts with horizontal_stripe")
    if "lower_trim" in details and recipe.get("pattern") == "simple_border":
        errors.append("lower_trim conflicts with simple_border")
    if "inner_layer" in details and recipe.get("pattern") == "vertical_trim":
        errors.append("inner_layer conflicts with vertical_trim")
    if "inner_layer" in details and recipe.get("closure") != "center_open":
        errors.append("inner_layer requires center_open")
    if "button_line" in details and recipe.get("closure") != "buttons":
        errors.append("button_line requires buttons")
    has_chest_accent = "chest_accent" in details
    has_button_line = "button_line" in details
    if has_chest_accent and recipe.get("accent") == "none":
        errors.append("chest_accent requires an accent color")
    if recipe.get("accent") != "none" and not (has_chest_accent or has_button_line):
        errors.append("accent color requires chest_accent or button_line")

    palette = data["palettes"]["families"].get(recipe.get("paletteFamily"))
    if palette is None:
        errors.append(f"unknown palette family {recipe.get('paletteFamily')!r}")
    elif recipe.get("accent") != "none" and recipe.get("accent") not in palette["allowedAccents"]:
        errors.append(
            f"accent {recipe.get('accent')!r} is not allowed by palette {recipe.get('paletteFamily')!r}"
        )

    details_count = len(details)
    patterns_count = int(recipe.get("pattern") != "none")
    secondary_features = details_count + patterns_count
    motifs = int(has_chest_accent) + int(recipe.get("pattern") == "horizontal_stripe")
    complexity = {
        "details": details_count,
        "patterns": patterns_count,
        "secondaryFeatures": secondary_features,
        "motifs": motifs,
    }
    rarity = recipe.get("rarity")
    budget = data["budgets"]["rarities"].get(rarity)
    if budget is None:
        errors.append(f"unknown rarity {rarity!r}")
    else:
        limits = {
            "details": budget["maximumDetails"],
            "patterns": budget["maximumPatterns"],
            "secondaryFeatures": budget["maximumSecondaryFeatures"],
            "motifs": budget["maximumMotifs"],
        }
        for key, limit in limits.items():
            if complexity[key] > limit:
                errors.append(f"{rarity} budget exceeded: {key}={complexity[key]} > {limit}")
    if recipe.get("rarity") == "Common" and recipe.get("pattern") != "none":
        errors.append("Common recipes cannot use a pattern")

    if not errors and details_count == 0 and recipe.get("pattern") == "none":
        warnings.append("intentionally minimal recipe; identity depends on archetype and neckline")
    return RecipeValidation(not errors, tuple(errors), tuple(warnings), complexity)


def _candidate_quality(candidate: dict[str, Any], data: dict[str, Any]) -> float:
    score = 50.0
    archetype = candidate["archetype"]
    detail_set = set(recipe_details(candidate))
    if archetype == "T_SHIRT":
        score += {"crew": 5, "round": 4, "shallow_v": 3}[candidate["neckline"]]
        score += {"fitted": 2, "regular": 4, "relaxed": 3}[candidate["fit"]]
        score += 4 if detail_set & {"chest_accent", "lower_trim"} else 1
        score += 3 if candidate["pattern"] == "horizontal_stripe" else 0
    elif archetype == "SWEATER":
        score += {"round": 3, "crew": 5, "shallow_v": 4}[candidate["neckline"]]
        score += 5 if candidate["fit"] == "relaxed" else 3
        score += 5 if "lower_trim" in detail_set else 0
        score += 4 if candidate["pattern"] in {"horizontal_stripe", "simple_border"} else 0
        score -= 2 if candidate["collar"] == "wide" else 0
    elif archetype == "BUTTON_SHIRT":
        score += 10
        score += 6 if "button_line" in detail_set else 0
        score += 3 if "chest_accent" in detail_set else 0
        score += 3 if candidate["pattern"] == "vertical_trim" else 0
        score += 2 if candidate["fit"] == "regular" else 1
    elif archetype == "JACKET":
        score += 6 if candidate["closure"] == "center_open" else 3
        score += 5 if candidate["collar"] == "small_folded" else 2
        score += 8 if "inner_layer" in detail_set else 0
        score += 4 if "button_line" in detail_set else 0
        score += 3 if "lower_trim" in detail_set else 0
        score += 3 if candidate["fit"] == "relaxed" else 2
    elif archetype == "SAILOR_TOP":
        score += 10 if candidate["collar"] == "sailor" else 5
        score += 5 if candidate["neckline"] == "open" else 2
        score += 5 if detail_set & {"center_stripe", "chest_accent"} else 1
        score += 4 if candidate["pattern"] == "simple_border" else 0
        score += 2 if candidate["fit"] == "regular" else 1
    if candidate["secondaryDetail"] is not None:
        score -= 2
    if candidate["pattern"] != "none" and detail_set:
        score -= 1
    palette = data["palettes"]["families"][candidate["paletteFamily"]]
    dye = palette["defaultDye"]
    secondary = palette["secondary"]["base"]
    score += min(6.0, abs(_luminance(dye) - _luminance(secondary)) / 22.0)
    return round(score, 4)


def _luminance(rgb: list[int] | tuple[int, int, int]) -> float:
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def _reference_traits(candidate: dict[str, Any]) -> list[str]:
    traits = ["compact_straight", "restrained_palette"]
    if candidate["archetype"] == "JACKET" or "inner_layer" in recipe_details(candidate):
        traits.append("clean_layering")
    if candidate["fit"] in {"regular", "relaxed"}:
        traits.append("practical_fit")
    if candidate["collar"] != "none":
        traits.append("disciplined_collar")
    if recipe_details(candidate) or candidate["pattern"] != "none":
        traits.append("localized_contrast")
    if "lower_trim" in recipe_details(candidate) or candidate["pattern"] == "simple_border":
        traits.append("simple_hem")
    ordered = []
    for trait in traits:
        if trait not in ordered:
            ordered.append(trait)
    return ordered[:4]


def _item_suffix(candidate: dict[str, Any]) -> str:
    details = set(recipe_details(candidate))
    archetype = candidate["archetype"]
    if archetype == "T_SHIRT":
        if candidate["pattern"] == "horizontal_stripe":
            return "Stripe Tee"
        if "chest_accent" in details:
            return "Pin Tee"
        if "lower_trim" in details:
            return "Band Tee"
        return "Everyday Tee"
    if archetype == "SWEATER":
        if "lower_trim" in details:
            return "Ribbed Sweater"
        if candidate["pattern"] == "horizontal_stripe":
            return "Stripe Sweater"
        if "chest_accent" in details:
            return "Pin Sweater"
        return "Knit Sweater"
    if archetype == "BUTTON_SHIRT":
        if "button_line" in details:
            return "Button Shirt"
        if "chest_accent" in details:
            return "Pocket Shirt"
        return "Work Shirt"
    if archetype == "JACKET":
        if "inner_layer" in details:
            return "Layer Jacket"
        if "button_line" in details:
            return "Button Jacket"
        if "lower_trim" in details:
            return "Band Jacket"
        return "Town Jacket"
    if "chest_accent" in details:
        return "Pin-Collar Top"
    if "center_stripe" in details:
        return "Center-Trim Top"
    if candidate["pattern"] == "simple_border":
        return "Border-Collar Top"
    return "Broad-Collar Top"


def _description(candidate: dict[str, Any], data: dict[str, Any]) -> str:
    archetype_phrases = {
        "T_SHIRT": "everyday tee",
        "SWEATER": "soft pullover",
        "BUTTON_SHIRT": "tailored work shirt",
        "JACKET": "compact outer layer",
        "SAILOR_TOP": "broad-collar top",
    }
    features = []
    if candidate["collar"] == "small_folded":
        features.append("a neat folded collar")
    elif candidate["collar"] == "wide":
        features.append("a wide collar")
    elif candidate["collar"] == "sailor":
        features.append("a crisp back yoke")
    details = recipe_details(candidate)
    detail_phrases = {
        "center_stripe": "center trim",
        "chest_accent": "a small chest accent",
        "lower_trim": "a clean lower band",
        "inner_layer": "a contrasting inner layer",
        "button_line": "a restrained button line",
    }
    features.extend(detail_phrases[detail] for detail in details)
    pattern_phrases = {
        "horizontal_stripe": "one wrapping stripe",
        "vertical_trim": "vertical panel trim",
        "simple_border": "a simple border",
    }
    if candidate["pattern"] != "none":
        features.append(pattern_phrases[candidate["pattern"]])
    feature_text = ", ".join(features) if features else "clean, quiet construction"
    palette_label = data["palettes"]["families"][candidate["paletteFamily"]]["label"].lower()
    return (
        f"A {candidate['fit']} {archetype_phrases[candidate['archetype']]} with "
        f"{feature_text} in {palette_label} tones."
    )


def _signature_distance(first: dict[str, Any], second: dict[str, Any]) -> int:
    return sum(first[field] != second[field] for field in SEMANTIC_FIELDS)


def _visual_distance(first: dict[str, Any], second: dict[str, Any]) -> int:
    return sum(first[field] != second[field] for field in VISUAL_FIELDS)


def _candidate_pool(archetype_id: str, rarity: str, data: dict[str, Any]) -> list[dict[str, Any]]:
    archetype = data["archetypes"][archetype_id]
    candidates: list[dict[str, Any]] = []
    for fit, neckline, collar, closure, detail, pattern, palette_family in itertools.product(
        archetype["validFits"],
        archetype["validNecklines"],
        archetype["validCollars"],
        archetype["validClosures"],
        archetype["validDetails"],
        archetype["validPatterns"],
        data["palettes"]["families"],
    ):
        secondary_options = [None]
        if rarity == "Rare":
            secondary_options.extend(
                value
                for value in archetype["validDetails"]
                if value not in {"none", detail}
            )
        for secondary in secondary_options:
            detail_set = {value for value in (detail, secondary) if value not in (None, "none")}
            palette = data["palettes"]["families"][palette_family]
            if "chest_accent" in detail_set:
                accent_options = palette["allowedAccents"]
            elif "button_line" in detail_set and rarity != "Common":
                accent_options = ["none", palette["allowedAccents"][0]]
            else:
                accent_options = ["none"]
            for accent in accent_options:
                candidate = {
                    "archetype": archetype_id,
                    "fit": fit,
                    "neckline": neckline,
                    "collar": collar,
                    "closure": closure,
                    "detail": detail,
                    "secondaryDetail": secondary,
                    "pattern": pattern,
                    "paletteFamily": palette_family,
                    "accent": accent,
                    "rarity": rarity,
                }
                validation = validate_recipe(candidate, data, partial=True)
                if validation.valid:
                    candidates.append(candidate)
    return candidates


def generate_recipes(data: dict[str, Any], seed: int = GENERATOR_SEED) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    chosen: list[dict[str, Any]] = []
    for archetype_id in ARCHETYPE_ORDER:
        archetype_chosen: list[dict[str, Any]] = []
        for slot_index, rarity in enumerate(RARITY_SCHEDULE[archetype_id]):
            target_palette = PALETTE_SCHEDULE[archetype_id][slot_index]
            pool = [
                candidate
                for candidate in _candidate_pool(archetype_id, rarity, data)
                if candidate["paletteFamily"] == target_palette
            ]
            if not pool:
                raise RuntimeError(f"no legal candidates for {archetype_id}/{rarity}")
            ranked = []
            for candidate in pool:
                minimum_distance = (
                    min(_signature_distance(candidate, other) for other in archetype_chosen)
                    if archetype_chosen
                    else len(SEMANTIC_FIELDS)
                )
                minimum_visual_distance = (
                    min(_visual_distance(candidate, other) for other in archetype_chosen)
                    if archetype_chosen
                    else len(VISUAL_FIELDS)
                )
                palette_bonus = 7 if all(
                    candidate["paletteFamily"] != other["paletteFamily"]
                    for other in archetype_chosen
                ) else 0
                diversity_bonus = min(8, minimum_distance * 1.2) + min(
                    9, minimum_visual_distance * 2.2
                )
                ranked.append(
                    (
                        _candidate_quality(candidate, data) + palette_bonus + diversity_bonus,
                        rng.random(),
                        candidate,
                    )
                )
            ranked.sort(key=lambda row: (-row[0], row[1]))
            selected = next(
                (
                    candidate
                    for _, _, candidate in ranked
                    if not archetype_chosen
                    or (
                        min(_signature_distance(candidate, other) for other in archetype_chosen) >= 3
                        and min(_visual_distance(candidate, other) for other in archetype_chosen) >= 2
                    )
                ),
                ranked[0][2],
            )
            archetype_chosen.append(selected)
        chosen.extend(archetype_chosen)

    recipes: list[dict[str, Any]] = []
    for index, candidate in enumerate(chosen, start=1):
        recipe = {
            "id": f"lifestyle-v1-{index:02d}",
            "generationIndex": index,
            "seed": seed + index * 7919,
            "category": "Lifestyle",
            "styleProfile": "General",
            "referenceTraits": _reference_traits(candidate),
            **candidate,
            "dyeable": True,
        }
        recipe["itemName"] = f"{PALETTE_PREFIX[recipe['paletteFamily']]} {_item_suffix(recipe)}"
        recipe["itemDescription"] = _description(recipe, data)
        validation = validate_recipe(recipe, data)
        if not validation.valid:
            raise RuntimeError(f"generated invalid recipe {recipe['id']}: {validation.errors}")
        recipes.append(recipe)
    if len(recipes) != 20:
        raise RuntimeError(f"expected exactly 20 recipes, generated {len(recipes)}")
    return recipes


def review_redundancy(recipes: list[dict[str, Any]]) -> dict[str, Any]:
    exact_duplicates = []
    near_duplicates = []
    for first, second in itertools.combinations(recipes, 2):
        if first["archetype"] != second["archetype"]:
            continue
        semantic_distance = _signature_distance(first, second)
        visual_distance = _visual_distance(first, second)
        if semantic_distance == 0:
            exact_duplicates.append([first["id"], second["id"]])
        elif semantic_distance <= 2 or visual_distance <= 1:
            near_duplicates.append(
                {
                    "recipeIds": [first["id"], second["id"]],
                    "semanticDistance": semantic_distance,
                    "visualStructureDistance": visual_distance,
                }
            )
    return {
        "exactDuplicateCount": len(exact_duplicates),
        "nearDuplicateCount": len(near_duplicates),
        "minimumAcceptedSemanticDistanceWithinArchetype": 3,
        "minimumAcceptedVisualStructureDistanceWithinArchetype": 2,
        "exactDuplicates": exact_duplicates,
        "nearDuplicates": near_duplicates,
    }


def select_best_five(recipes: list[dict[str, Any]], data: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    selected: list[dict[str, Any]] = []
    reasons: dict[str, str] = {}
    used_palettes: set[str] = set()
    reason_templates = {
        "T_SHIRT": "Keeps the simplest archetype readable while adding one controlled Lifestyle cue.",
        "SWEATER": "Uses neckline and hem mass to read as knitwear without surface noise.",
        "BUTTON_SHIRT": "The collar and center closure remain legible in all directions with restrained detail.",
        "JACKET": "Outer panels and a compatible inner-layer/closure relationship create the clearest layered identity.",
        "SAILOR_TOP": "The front collar and simplified back yoke provide a strong four-direction identity without an emblem.",
    }
    for archetype_id in ARCHETYPE_ORDER:
        candidates = [
            recipe
            for recipe in recipes
            if recipe["archetype"] == archetype_id
            and recipe["rarity"] == SELECTED_RARITY[archetype_id]
        ]
        if not candidates:
            raise RuntimeError(f"batch has no selectable {archetype_id}")
        candidates.sort(
            key=lambda recipe: (
                -(
                    _candidate_quality(recipe, data)
                    + (8 if recipe["paletteFamily"] not in used_palettes else 0)
                ),
                recipe["generationIndex"],
            )
        )
        recipe = candidates[0]
        selected.append(recipe)
        used_palettes.add(recipe["paletteFamily"])
        reasons[recipe["id"]] = reason_templates[archetype_id]
    if len(selected) != 5 or {recipe["archetype"] for recipe in selected} != set(ARCHETYPE_ORDER):
        raise RuntimeError("selection must contain exactly one of each V1 archetype")
    return selected, reasons


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    if not value:
        raise ValueError("cannot slugify an empty value")
    return value


def pascal_identifier(value: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", value)
    if not words:
        raise ValueError("cannot build an item identifier")
    return "".join(word[:1].upper() + word[1:] for word in words)
