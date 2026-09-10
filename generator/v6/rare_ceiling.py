"""Rare visual-ceiling calibration over the frozen V5D/V5E art pipeline."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from generator.v5d import generate_v5d_batch
from generator.v5d.engine import _base_upper, validate_v5d_recipe


@dataclass(frozen=True)
class RareCeilingValidation:
    passes: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict[str, Any]


SPECS = (
    {
        "source": "Skylark Cable Knit", "name": "Harborline Merino Crew", "family": "premium crewneck",
        "theme": "creature_inspired", "palette": "storybook_blue", "primary": "restrained knit band",
        "support": ["ribbed neckline and hem"], "complexity": "moderate",
        "whyRare": "Premium knit construction and finishing, but no focal motif or signature behavior.",
        "custom": ["PrimaryFabric", "SecondaryFabric", "Sleeve", "Cuff", "Collar", "Trim", "MotifSocket"],
    },
    {
        "source": "Tideglass Henley", "name": "Sea Glass Fine-Knit Henley", "family": "premium fitted knit",
        "theme": "celestial_fantasy", "palette": "seafoam_coral", "primary": "short fitted henley opening",
        "support": ["single quiet chest rhythm"], "complexity": "moderate",
        "whyRare": "Fine-gauge fit, neckline, and restrained banding create quality without a spectacle hook.",
        "custom": ["PrimaryFabric", "SecondaryFabric", "Sleeve", "Cuff", "Collar", "Trim", "MotifSocket"],
    },
    {
        "source": "Rowan Morning Cardigan", "name": "Juniper Vale Cardigan", "family": "refined cardigan",
        "theme": "storybook_whimsical", "palette": "rose_sage", "primary": "soft open cardigan edge",
        "support": ["paired low pockets"], "complexity": "moderate-plus",
        "whyRare": "Layering and pocket finish feel expensive, while the silhouette remains normal and wearable.",
        "custom": ["PrimaryFabric", "SecondaryFabric", "Sleeve", "Cuff", "Collar", "Trim", "Accent", "MotifSocket"],
    },
    {
        "source": "Silverline Evening Waistcoat", "name": "Nocturne Silver Waistcoat", "family": "polished waistcoat",
        "theme": "celestial_fantasy", "palette": "midnight_gold", "primary": "tailored vest frame",
        "support": ["quiet button rhythm"], "complexity": "moderate-plus",
        "whyRare": "The premium read comes from fit, lapel-like vest edges, and buttons—not a crest or theatrical layer.",
        "custom": ["PrimaryFabric", "SecondaryFabric", "Sleeve", "Cuff", "Collar", "Lapel", "Trim", "Accent", "MotifSocket"],
    },
    {
        "source": "Midnight Laurel Blazer", "name": "Cedarline Reserve Jacket", "family": "premium minimal jacket",
        "theme": "elemental", "palette": "aot_civilian_rust", "primary": "clean lapel opening",
        "support": ["single-button and pocket finish"], "complexity": "high-controlled",
        "whyRare": "Excellent tailoring and layered front construction stay minimal; there is no emblem, asymmetry, or state behavior.",
        "custom": ["PrimaryFabric", "SecondaryFabric", "Sleeve", "Cuff", "Collar", "Lapel", "Trim", "Accent", "MotifSocket"],
    },
    {
        "source": "Orchard Hand Workshirt", "name": "Orchard Reserve Workshirt", "family": "premium work shirt",
        "theme": "elemental", "palette": "harvest_cream", "primary": "structured yoke and pocket relationship",
        "support": ["rolled-cuff finish"], "complexity": "moderate-plus",
        "whyRare": "High-quality workwear construction elevates a normal shirt without turning it into a named hero piece.",
        "custom": ["PrimaryFabric", "SecondaryFabric", "Sleeve", "Cuff", "Collar", "Trim", "Accent", "MotifSocket"],
    },
)


def _design(recipe: dict[str, Any]) -> dict[str, Any]:
    return recipe["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]


def generate_rare_ceiling_batch() -> dict[str, Any]:
    sources = {_design(r)["itemName"]: r for r in generate_v5d_batch()["recipes"]}
    entries: list[dict[str, Any]] = []
    for index, spec in enumerate(SPECS, 1):
        recipe = copy.deepcopy(sources[spec["source"]])
        old_upper = recipe["baseUpperRecipe"]
        old_design = _design(recipe)
        runtime = {
            "baseArticle": old_upper["articleType"], "variant": old_upper["constructionVariant"],
            "sleeve": old_upper["sleeveIntent"], "baseShoulder": old_upper["shoulderIntent"],
            "baseNeckline": old_upper["necklineIntent"], "baseCollar": old_upper["collarIntent"],
            "baseLayering": old_upper["layeringIntent"], "baseOpening": old_upper["openingIntent"],
            "zone": old_upper["surfaceTranslation"]["primaryZone"], "theme": spec["theme"],
            "rarity": "Rare", "archetype": old_design["archetype"], "name": spec["name"],
            "description": spec["whyRare"], "palette": spec["palette"],
        }
        recipe["baseUpperRecipe"] = _base_upper(index, runtime)
        recipe["surfacePlan"]["primaryGesture"] = spec["primary"].replace(" ", "_")
        recipe["surfacePlan"]["supportGestures"] = [value.replace(" ", "_") for value in spec["support"]]
        recipe["surfacePlan"]["motifSystem"] = "none"
        recipe["surfacePlan"]["patternSystem"] = "none"
        recipe["paletteStory"] = spec["palette"]
        result = validate_v5d_recipe(recipe)
        if not result.valid:
            raise ValueError(f"invalid Rare ceiling recipe {spec['name']}: {'; '.join(result.errors)}")
        entries.append({
            "id": f"v6-rare-ceiling-{index:02d}", "name": spec["name"], "garmentFamily": spec["family"],
            "rarity": "Rare", "rendererTier": "FS_RARE_PLUS_COMPLEX_GARMENT",
            "constructionComplexity": spec["complexity"], "primaryConstruction": spec["primary"],
            "supportConstruction": spec["support"], "majorSpecialHooks": [], "visibleMotifPolicy": "none",
            "stateBehavior": "none", "vfx": "none", "whyRareNotLegendary": spec["whyRare"],
            "customization": {"roles": spec["custom"], "MotifSocket": "reserved_empty", "protected": ["ExteriorContour", "StructuralSeams"]},
            "sourceRole": recipe["articleRole"], "recipe": recipe,
        })
    validation = validate_rare_ceiling_batch(entries)
    if not validation.passes:
        raise ValueError("Rare ceiling batch rejected: " + "; ".join(validation.errors))
    return {"formatVersion": "6.1.0", "count": 6, "rarity": "Rare", "entries": entries, "ceilingMetrics": validation.metrics}


def validate_rare_ceiling_batch(entries: list[dict[str, Any]]) -> RareCeilingValidation:
    errors: list[str] = []; warnings: list[str] = []
    if len(entries) != 6: errors.append(f"expected six Rare garments, found {len(entries)}")
    if len({e["garmentFamily"] for e in entries}) != 6: errors.append("garment families are not unique")
    if any("HOOD" in e["sourceRole"] for e in entries): errors.append("hoodies are Legendary-only")
    for entry in entries:
        if entry["rarity"] != "Rare": errors.append(f"{entry['id']}: semantic rarity is not Rare")
        if len(entry["majorSpecialHooks"]) > 1: errors.append(f"{entry['id']}: crossed Rare hook ceiling")
        if entry["stateBehavior"] != "none" or entry["vfx"] != "none": errors.append(f"{entry['id']}: spectacle behavior belongs above Rare")
        if entry["visibleMotifPolicy"] not in {"none", "micro"}: errors.append(f"{entry['id']}: motif exceeds Rare ceiling")
        if entry["customization"]["MotifSocket"] != "reserved_empty": errors.append(f"{entry['id']}: customization socket must remain empty")
        result = validate_v5d_recipe(entry["recipe"])
        errors.extend(f"{entry['id']}: {message}" for message in result.errors)
    metrics = {
        "familyCount": len({e["garmentFamily"] for e in entries}),
        "specialHookMaximum": max((len(e["majorSpecialHooks"]) for e in entries), default=0),
        "visibleMotifCount": sum(e["visibleMotifPolicy"] != "none" for e in entries),
        "stateBehaviorCount": sum(e["stateBehavior"] != "none" for e in entries),
        "vfxCount": sum(e["vfx"] != "none" for e in entries),
        "hoodieCount": sum("HOOD" in e["sourceRole"] for e in entries),
    }
    return RareCeilingValidation(not errors, tuple(errors), tuple(warnings), metrics)
