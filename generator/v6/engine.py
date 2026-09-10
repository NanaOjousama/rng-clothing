"""Deterministic V6 production batch over the frozen renderer architecture.

V6 adds no pixel grammar.  It routes fresh/curated semantic concepts through
the proven vanilla, simple Fashion Sense, and Rare+ renderer families, then
enforces collection-level diversity before any exporter accepts the batch.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from generator.rarity_renderer_policy import select_renderer_route
from generator.v2_recipe_engine import generate_v2_recipes, load_v2_data, validate_recipe_v2
from generator.v5b.engine import _base, _design, load_v5b_data, validate_v5b_recipe
from generator.v5c2 import generate_v5c2_batch
from generator.v5d import generate_v5d_batch
from generator.v5e import generate_v5e_recipe


SEED = 2026083106


@dataclass(frozen=True)
class V6BatchValidation:
    passes: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict[str, Any]


COMMON_SELECTIONS = (
    # seed delta, source generation index, player-facing name, palette
    (0, 1, "Saltwind Everyday Tee", "sage_tan"),
    (0, 2, "Harbor Block Tee", "navy_ivory"),
    (1, 1, "Cloudmint Round Tee", "cool_neutral"),
    (2, 2, "Bluebell Fitted Tee", "denim_cream"),
    (0, 5, "Hearth Ribbed Sweater", "rust_brown"),
    (1, 5, "Pinecream V-Knit", "forest_cream"),
    (4, 5, "Garnet Crew Sweater", "charcoal_burgundy"),
    (0, 9, "Cedar Placket Shirt", "warm_neutral"),
    (1, 9, "Sageband Work Shirt", "sage_tan"),
    (3, 9, "Bluebell Button Shirt", "denim_cream"),
    (0, 17, "Ivory Harbor Sail Top", "navy_ivory"),
    (2, 17, "Mistral Yoke Top", "cool_neutral"),
)


UNCOMMON_SPECS = (
    # article, variant, sleeve, shoulder, neckline, collar, layering, opening,
    # theme, archetype, name, zone, continuation, cuff, article label
    ("FITTED_SHIRT", "structured_shirt", "ROLLED_CUFFED_SLEEVE", "narrow", "high", "utility", "single_layer", "buttoned", "cyber_tech", "BUTTON_SHIRT", "Tidewire Rolled Shirt", "yoke", "trim_echo", "contrast", "structured shirt"),
    ("FITTED_SHIRT", "polo_like", "SHORT_SLEEVE", "standard", "open", "shirt_collar", "single_layer", "buttoned", "dessert_cute", "BUTTON_SHIRT", "Coralglass Club Shirt", "collar", "fabric_match", "simple", "casual collared shirt"),
    ("SWEATER", "patterned_knit", "FITTED_LONG_SLEEVE", "dropped", "high", "rounded", "single_layer", "closed", "witchy_dark", "SWEATER", "Bluebell Ridge Knit", "hem", "trim_echo", "simple", "patterned sweater"),
    ("SWEATER", "relaxed_knit", "FITTED_LONG_SLEEVE", "standard", "v_neck", "none", "single_layer", "closed", "creature_inspired", "SWEATER", "Fernpaw Relaxed Knit", "chest", "fabric_match", "simple", "relaxed sweater"),
    ("VEST_TOP", "waistcoat", "FITTED_LONG_SLEEVE", "narrow", "v_neck", "none", "vest_over_inner", "buttoned", "celestial_fantasy", "BUTTON_SHIRT", "Silver Reed Waistcoat", "placket", "inner_layer_match", "simple", "formal waistcoat"),
    ("VEST_TOP", "utility_vest", "ROLLED_CUFFED_SLEEVE", "standard", "high", "utility", "vest_over_inner", "buttoned", "military_structured", "BUTTON_SHIRT", "Brassleaf Work Vest", "chest", "inner_layer_match", "contrast", "utility vest"),
    ("STANDARD_JACKET", "cardigan", "FITTED_LONG_SLEEVE", "dropped", "crew", "none", "visible_inner_layer", "center_open", "storybook_whimsical", "JACKET", "Rosewood Morning Cardigan", "hem", "fabric_match", "simple", "open cardigan"),
    ("CROPPED_JACKET", "moto_jacket", "ROLLED_CUFFED_SLEEVE", "dropped", "open", "lapel", "visible_inner_layer", "partial_open", "elemental", "JACKET", "Cinderlane Moto Jacket", "outer_panels", "trim_echo", "contrast", "cropped moto jacket"),
    ("CROPPED_JACKET", "casual_zip_jacket", "FITTED_LONG_SLEEVE", "standard", "high", "high_collar", "visible_inner_layer", "center_open", "cyber_tech", "JACKET", "Night Relay Zip Jacket", "outer_panels", "trim_echo", "simple", "cropped zip jacket"),
    ("BLOUSE", "sailor_blouse", "SHORT_SLEEVE", "narrow", "square", "sailor_like", "collar_overlay", "partial_open", "storybook_whimsical", "BUTTON_SHIRT", "Rosewake Sail Blouse", "collar", "fabric_match", "simple", "sailor blouse"),
    ("STANDARD_JACKET", "bomber_jacket", "FITTED_LONG_SLEEVE", "dropped", "high", "high_collar", "visible_inner_layer", "partial_open", "elemental", "JACKET", "Saffron Harbor Bomber", "chest", "trim_echo", "simple", "bomber jacket"),
)


def _common_entries() -> list[dict[str, Any]]:
    entries = []; data = load_v2_data()
    cache: dict[int, dict[int, dict[str, Any]]] = {}
    for index, (seed_delta, source_index, name, palette) in enumerate(COMMON_SELECTIONS, 1):
        seed = SEED + seed_delta
        if seed not in cache:
            cache[seed] = {recipe["generationIndex"]: recipe for recipe in generate_v2_recipes(data, seed)}
        vanilla = copy.deepcopy(cache[seed][source_index])
        vanilla["paletteFamily"] = palette
        vanilla["itemName"] = name
        vanilla["itemDescription"] = f"A clean everyday {vanilla['archetype'].lower().replace('_', ' ')} with restrained construction and a readable {vanilla['construction']['neckline'].replace('_', ' ')} neckline."
        result = validate_recipe_v2(vanilla, data)
        if not result.valid:
            raise ValueError(f"invalid V6 Common {name}: {'; '.join(result.errors)}")
        construction = vanilla["construction"]
        entries.append({
            "id": f"v6-common-{index:02d}", "tier": "Common", "name": name,
            "article": "basic vanilla " + vanilla["archetype"].lower().replace("_", " "),
            "sourceEngine": "V2 enhanced vanilla renderer", "recipe": vanilla,
            "axes": {
                "silhouette": ":".join((vanilla["archetype"], construction["fit"], construction["neckline"])), "collar": construction["collar"],
                "opening": construction["closure"], "pocketPanel": construction["panelLayout"],
                "motif": "none", "colorBlock": vanilla["colorBlocking"]["secondaryRegion"],
                "palette": vanilla["paletteFamily"], "primary": vanilla["substantialFeatures"][0] if vanilla["substantialFeatures"] else construction["panelLayout"],
            },
        })
    return entries


def _make_v5b_uncommon(index: int, spec: tuple[str, ...]) -> dict[str, Any]:
    article, variant, sleeve, shoulder, neckline, collar, layering, opening, theme, archetype, name, zone, continuation, cuff, _ = spec
    design = _design(index, theme, "Uncommon", archetype, name)
    base_article = load_v5b_data()["articles"]["articles"][article]["baseArticle"]
    base = _base(index, design, base_article)
    recipe = {
        "formatVersion": "5.2.0", "id": f"v6-uncommon-{index:02d}", "collection": "V5BUpperBenchmark",
        "articleType": article, "constructionVariant": variant, "sleeveIntent": sleeve,
        "shoulderIntent": shoulder, "necklineIntent": neckline, "collarIntent": collar,
        "layeringIntent": layering, "openingIntent": opening,
        "surfaceTranslation": {"primaryZone": zone, "sleeveContinuation": continuation, "cuffTreatment": cuff},
        "baseArticleRecipe": base,
    }
    result = validate_v5b_recipe(recipe)
    if not result.valid:
        raise ValueError(f"invalid V6 Uncommon {name}: {'; '.join(result.errors)}")
    return recipe


def _fs_axes(recipe: dict[str, Any], article: str) -> dict[str, str]:
    design = recipe["baseArticleRecipe"]["designRecipe"] if "baseArticleRecipe" in recipe else recipe["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]
    construction = design["construction"]; surface = design["surfaceDesign"]
    return {
        "silhouette": article, "collar": recipe.get("collarIntent", construction["collar"]),
        "opening": recipe.get("openingIntent", construction["closure"]),
        "pocketPanel": recipe.get("constructionVariant", construction["panelLayout"]),
        "motif": surface["motif"]["family"], "colorBlock": design["colorBlocking"]["type"],
        "palette": design["paletteStory"], "primary": surface["compositionType"],
    }


def _uncommon_entries() -> list[dict[str, Any]]:
    entries = []
    for index, spec in enumerate(UNCOMMON_SPECS, 1):
        recipe = _make_v5b_uncommon(index, spec)
        article = spec[-1]
        entries.append({
            "id": f"v6-uncommon-{index:02d}", "tier": "Uncommon", "name": spec[10],
            "article": article, "sourceEngine": "V5B simple FS article", "renderKind": "v5b",
            "recipe": recipe, "axes": _fs_axes(recipe, article),
        })
    # Two hoodie grammars are intentionally sourced from the vanilla-informed
    # V5C2 family rather than faking a hood through generic sweater semantics.
    hoodies = {r["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]["itemName"]: r for r in generate_v5c2_batch()["recipes"]}
    for offset, (source_name, article) in enumerate((("Cloudberry Pouch Hoodie", "pouch hoodie"),), 12):
        recipe = copy.deepcopy(hoodies[source_name])
        name = recipe["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]["itemName"]
        entries.append({
            "id": f"v6-uncommon-{offset:02d}", "tier": "Uncommon", "name": name, "article": article,
            "sourceEngine": "V5C2 vanilla-informed hoodie", "renderKind": "v5c2",
            "recipe": recipe, "axes": _fs_axes(recipe, article),
        })
    return entries


def _rare_entries() -> list[dict[str, Any]]:
    entries = []
    sunfield = generate_v5e_recipe()
    entries.append({
        "id": "v6-rareplus-01", "tier": "Rare+", "name": "Sunfield Pathfinder Jacket",
        "article": "structured field jacket", "sourceEngine": "V5E Rare+ structured outerwear", "renderKind": "v5e",
        "recipe": sunfield,
        "axes": _fs_axes(sunfield, "structured field jacket") | {"motif": "field_tab", "primary": "lapel_pocket_hierarchy"},
    })
    source = {r["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]["itemName"]: r for r in generate_v5d_batch()["recipes"]}
    choices = (
        ("Midnight Laurel Blazer", "formal blazer"),
        ("Copperwick Gentleman Top", "period gentleman top"),
        ("Amethyst Wayfarer Tunic", "adventurer tunic"),
        ("Emberward Tabard Armor", "armor tabard"),
        ("Berry Static Cross-Zip Top", "asymmetric street top"),
    )
    for index, (name, article) in enumerate(choices, 2):
        recipe = copy.deepcopy(source[name])
        entries.append({
            "id": f"v6-rareplus-{index:02d}", "tier": "Rare+", "name": name, "article": article,
            "sourceEngine": "V5D premium article + Rare+ native sleeve route", "renderKind": "v5d",
            "recipe": recipe, "axes": _fs_axes(recipe, article),
        })
    return entries


def _similarity(left: dict[str, str], right: dict[str, str]) -> float:
    keys = tuple(left)
    return sum(left[key] == right[key] for key in keys) / len(keys)


def generate_v6_batch() -> dict[str, Any]:
    entries = _common_entries() + _uncommon_entries() + _rare_entries()
    result = validate_v6_batch(entries)
    if not result.passes:
        raise ValueError("V6 semantic batch rejected: " + "; ".join(result.errors))
    return {"generatorVersion": "6.0.0", "seed": SEED, "count": len(entries), "entries": entries, "diversity": result.metrics}


def validate_v6_batch(entries: list[dict[str, Any]]) -> V6BatchValidation:
    errors: list[str] = []; warnings: list[str] = []
    counts = {tier: sum(e["tier"] == tier for e in entries) for tier in ("Common", "Uncommon", "Rare+")}
    if counts != {"Common": 12, "Uncommon": 12, "Rare+": 6}:
        errors.append(f"expected 12/12/6 tier distribution, found {counts}")
    if len({e["id"] for e in entries}) != len(entries): errors.append("duplicate V6 ids")
    if len({e["name"] for e in entries}) != len(entries): errors.append("duplicate player-facing names")
    for entry in entries:
        policy_rarity = "Rare" if entry["tier"] == "Rare+" else entry["tier"]
        route = select_renderer_route(policy_rarity)
        expected = "vanilla" if entry["tier"] == "Common" else "fashionsense"
        if route.backend != expected: errors.append(f"{entry['id']}: wrong renderer route {route.backend}")
        if entry["tier"] == "Common" and entry.get("renderKind"):
            errors.append(f"{entry['id']}: Common leaked into Fashion Sense")
    pairwise = []
    for tier in ("Common", "Uncommon", "Rare+"):
        group = [e for e in entries if e["tier"] == tier]
        threshold = 0.80 if tier == "Common" else 0.75
        for i, left in enumerate(group):
            for right in group[i + 1:]:
                score = _similarity(left["axes"], right["axes"])
                pairwise.append({"tier": tier, "left": left["id"], "right": right["id"], "similarity": round(score, 3)})
                if score >= threshold:
                    errors.append(f"{left['id']} and {right['id']} substantially repeat ({score:.2f})")
    axes = {key: {e["axes"][key] for e in entries} for key in next(iter(entries))["axes"]}
    minima = {"silhouette": 10, "collar": 6, "opening": 6, "pocketPanel": 10, "motif": 7, "colorBlock": 6, "palette": 12, "primary": 8}
    for axis, minimum in minima.items():
        if len(axes[axis]) < minimum: errors.append(f"diversity axis {axis} has {len(axes[axis])}; needs {minimum}")
    center_dominated = [e["id"] for e in entries if e["axes"]["colorBlock"] == "center_panel"]
    if len(center_dominated) > 4: errors.append(f"center-panel composition overrepresented: {center_dominated}")
    metrics = {
        "tierCounts": counts,
        "uniqueAxisCounts": {key: len(values) for key, values in axes.items()},
        "maximumWithinTierSimilarity": max((p["similarity"] for p in pairwise), default=0),
        "centerPanelCount": len(center_dominated),
        "pairwise": pairwise,
    }
    return V6BatchValidation(not errors, tuple(errors), tuple(warnings), metrics)
