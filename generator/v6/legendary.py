"""Legendary ceiling calibration over frozen, proven V5 garment contracts.

Legendary is a semantic/presentation tier: each piece keeps the established
runtime assembly for its article, but adds one memorable identity system above
the premium-minimal Rare ceiling.  The frozen V5 recipe schemas therefore stay
at their highest supported internal rarity while this wrapper owns Legendary.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from generator.hoodie_layers import generate_hoodie_layer_batch
from generator.v5d import generate_v5d_batch
from generator.v5d.engine import _base_upper, validate_v5d_recipe


@dataclass(frozen=True)
class LegendaryValidation:
    passes: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict[str, Any]


SPECS = (
    dict(source="Sproutwing Cropped Hoodie", name="Graphite Tide Hood",
         family="signature hoodie", assembly="coordinated_hoodie",
         identity="white and teal street hood with graphite framing and a cropped pouch body",
         hook="high-contrast head-framing hood", secondary="cropped pouch-and-cuff rhythm",
         palette="legendary_white_teal_graphite", paletteLabel="white / teal / dark graphite",
         silhouette="raised hood with compact dropped-shoulder body", closure="pullover closed front", collar="full raised hood",
         focal="teal hood opening over a quiet graphite pouch", back="broad teal-lined hood with a single vertical fold", role="STREET_HOODIE",
         custom=["PrimaryFabric", "SecondaryFabric", "HoodOuter", "HoodInner", "Sleeve", "Cuff", "Trim", "Accent", "MotifSocket"]),
    dict(source="Sunfield Scout Jacket", name="Crimson Arc Relay Jacket",
         family="signature structured jacket", assembly="native_sleeve_upper",
         identity="crimson cropped shell split by ivory lapels over a charcoal inner layer",
         hook="crimson split-shell arc", secondary="paired ivory flap-and-waist termination",
         palette="legendary_crimson_charcoal_ivory", paletteLabel="crimson / charcoal / ivory",
         silhouette="cropped square-shoulder shell", closure="wide center-open lapel split", collar="short folded lapels",
         focal="paired ivory relay bars across the crimson shell", back="compact yoke with centered arc mark", role="CROPPED_FIELD_JACKET",
         custom=["PrimaryFabric", "SecondaryFabric", "Collar", "Lapel", "Sleeve", "Cuff", "Pocket", "Trim", "Accent", "EmblemSocket"]),
    dict(source="Copperwick Gentleman Top", name="Jade Conservatory Coat",
         family="statement coat-top", assembly="native_sleeve_upper",
         identity="jade period coat-top with a cream cravat and warm bronze procession edge",
         hook="cream cravat-to-bronze brocade gesture", secondary="offset closure and long tailored corners",
         palette="legendary_jade_cream_bronze", paletteLabel="jade / cream / bronze",
         silhouette="flared divided period coat-top", closure="offset double-breasted rhythm", collar="high cravat collar",
         focal="bright cravat above bronze edgework", back="cream nape inset with descending jade seam", role="PERIOD_TOP",
         custom=["PrimaryFabric", "SecondaryFabric", "Collar", "Sleeve", "Cuff", "Trim", "Accent", "MotifSocket"]),
    dict(source="Midnight Laurel Blazer", name="Pearl Nocturne Ceremonial Blazer",
         family="ceremonial fitted top", assembly="native_sleeve_upper",
         identity="pearl ceremonial blazer crossed by a midnight lapel and restrained gold meridian",
         hook="gold meridian across pearl formal planes", secondary="midnight lapel and quiet back chevron",
         palette="legendary_pearl_midnight_gold", paletteLabel="pearl / midnight / gold",
         silhouette="narrow-waist fitted blazer with pointed front hem", closure="single-button diagonal meridian", collar="deep satin lapels",
         focal="gold diagonal crossing the midnight lapel", back="pearl shoulder plane with small midnight chevron", role="FORMAL_BLAZER",
         custom=["PrimaryFabric", "SecondaryFabric", "Collar", "Lapel", "Sleeve", "Cuff", "Pocket", "Trim", "Accent", "MotifSocket"]),
    dict(source="Greywatch Officer Jacket", name="Frostguard Standard Jacket",
         family="themed fieldwear", assembly="native_sleeve_upper",
         identity="frost-blue field jacket with silver standard geometry over black structural panels",
         hook="silver guarded collar and shoulder standard", secondary="frost chest tabs and black wrapped yoke",
         palette="legendary_frost_silver_black", paletteLabel="frost blue / silver / black",
         silhouette="broad-shoulder high-neck field shell with sharp lower taper", closure="disciplined paired-button front", collar="guarded high collar",
         focal="silver shoulder standard above paired chest tabs", back="silver angular yoke standard on a black field", role="MILITARY_TOP",
         custom=["PrimaryFabric", "SecondaryFabric", "Collar", "Sleeve", "Cuff", "Strap", "Pocket", "Trim", "Accent", "EmblemSocket"]),
    dict(source="Amethyst Wayfarer Tunic", name="Sundown Waymark Tunic",
         family="adventure statement top", assembly="native_sleeve_upper",
         identity="sunset-amber waymark sash crossing a deep-indigo layered travel tunic",
         hook="asymmetric amber waymark sash", secondary="indigo shoulder wrap and belted waist",
         palette="legendary_sunset_amber_indigo", paletteLabel="sunset amber / deep indigo",
         silhouette="one-shoulder wrapped tunic with asymmetric lower termination", closure="diagonal wrap with belt termination", collar="layered asymmetric V",
         focal="luminous amber diagonal across indigo", back="quiet indigo field with amber nape and belt cues", role="ADVENTURER_TUNIC",
         custom=["PrimaryFabric", "SecondaryFabric", "Collar", "Sleeve", "Cuff", "Strap", "Trim", "Accent", "MotifSocket"]),
)


def _design(recipe: dict[str, Any]) -> dict[str, Any]:
    return recipe["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]


def _rename_values(value: Any, old: str, new: str) -> Any:
    if isinstance(value, dict):
        return {key: _rename_values(item, old, new) for key, item in value.items()}
    if isinstance(value, list):
        return [_rename_values(item, old, new) for item in value]
    return new if value == old else value


def _set_palette_story(value: Any, palette: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "paletteStory": value[key] = palette
            else: _set_palette_story(item, palette)
    elif isinstance(value, list):
        for item in value: _set_palette_story(item, palette)


def _upper_recipe(source: dict[str, Any], spec: dict[str, Any], index: int) -> dict[str, Any]:
    recipe = copy.deepcopy(source)
    old_upper = recipe["baseUpperRecipe"]
    old_design = _design(recipe)
    runtime = {
        "baseArticle": old_upper["articleType"], "variant": old_upper["constructionVariant"],
        "sleeve": old_upper["sleeveIntent"], "baseShoulder": old_upper["shoulderIntent"],
        "baseNeckline": old_upper["necklineIntent"], "baseCollar": old_upper["collarIntent"],
        "baseLayering": old_upper["layeringIntent"], "baseOpening": old_upper["openingIntent"],
        "zone": old_upper["surfaceTranslation"]["primaryZone"], "theme": old_design["themeFamily"],
        "rarity": "Rare", "archetype": old_design["archetype"], "name": spec["name"],
        "description": spec["identity"], "palette": spec["palette"],
    }
    recipe["baseUpperRecipe"] = _base_upper(index, runtime)
    recipe["paletteStory"] = spec["palette"]
    result = validate_v5d_recipe(recipe)
    if not result.valid:
        raise ValueError(f"invalid Legendary foundation {spec['name']}: {'; '.join(result.errors)}")
    return recipe


def generate_legendary_batch() -> dict[str, Any]:
    upper_sources = {_design(r)["itemName"]: r for r in generate_v5d_batch()["recipes"]}
    hood_sources = {r["itemName"]: r for r in generate_hoodie_layer_batch()["recipes"]}
    entries: list[dict[str, Any]] = []
    for index, raw_spec in enumerate(SPECS, 1):
        spec = dict(raw_spec)
        if spec["assembly"] == "coordinated_hoodie":
            recipe = _rename_values(copy.deepcopy(hood_sources[spec["source"]]), spec["source"], spec["name"])
            recipe["itemName"] = spec["name"]
            recipe["itemDescription"] = spec["identity"]
            _set_palette_story(recipe, spec["palette"])
        else:
            recipe = _upper_recipe(upper_sources[spec["source"]], spec, index)
        entries.append({
            "id": f"v6-legendary-{index:02d}", "name": spec["name"], "rarity": "Legendary",
            "garmentFamily": spec["family"], "articleRole": spec["role"],
            "rendererTier": "FS_LEGENDARY_SIGNATURE_GARMENT_V1",
            "runtimeAssembly": spec["assembly"], "coreIdentity": spec["identity"],
            "paletteStory": spec["palette"], "paletteLabel": spec["paletteLabel"],
            "silhouetteIdentity": spec["silhouette"], "closureIdentity": spec["closure"],
            "collarIdentity": spec["collar"], "focalComposition": spec["focal"], "backTreatment": spec["back"],
            "signatureHook": spec["hook"], "substantialSecondaryRegion": spec["secondary"],
            "presentationSystems": [spec["hook"], spec["secondary"]],
            "stateBehavior": "none", "vfx": "none", "mythicReserved": ["VFX", "transformation", "multi-stage motif spectacle"],
            "whyLegendary": f"It clears Rare through {spec['hook']} plus {spec['secondary']}; the identity survives without shading.",
            "customization": {"roles": spec["custom"], "protected": ["ExteriorContour", "StructuralSeams", "SignatureSilhouette", "SignatureHook"]},
            "recipe": recipe,
        })
    validation = validate_legendary_batch(entries)
    if not validation.passes:
        raise ValueError("Legendary batch rejected: " + "; ".join(validation.errors))
    return {"formatVersion": "6.2.0", "rarity": "Legendary", "count": len(entries), "entries": entries, "metrics": validation.metrics}


def validate_legendary_batch(entries: list[dict[str, Any]]) -> LegendaryValidation:
    errors: list[str] = []
    warnings: list[str] = []
    if len(entries) != 6: errors.append(f"expected six Legendary garments, found {len(entries)}")
    if len({e["garmentFamily"] for e in entries}) != 6: errors.append("Legendary garment families repeat")
    if sum(e["articleRole"] == "STREET_HOODIE" for e in entries) != 1: errors.append("Legendary calibration requires exactly one hoodie")
    for field in ("paletteStory", "silhouetteIdentity", "closureIdentity", "collarIdentity", "focalComposition", "backTreatment"):
        if len({e[field] for e in entries}) != len(entries): errors.append(f"Legendary {field} values are not unique")
    for entry in entries:
        if entry["rarity"] != "Legendary": errors.append(f"{entry['id']}: wrapper rarity is not Legendary")
        if not entry["signatureHook"] or not entry["substantialSecondaryRegion"]: errors.append(f"{entry['id']}: lacks signature/secondary identity")
        if len(entry["presentationSystems"]) > 2: errors.append(f"{entry['id']}: presentation crosses controlled Legendary ceiling")
        if entry["vfx"] != "none": errors.append(f"{entry['id']}: VFX reserved above this calibration")
        if len(entry["customization"]["roles"]) < 7: errors.append(f"{entry['id']}: customization topology is incomplete")
    metrics = {
        "familyCount": len({e["garmentFamily"] for e in entries}),
        "signatureHookCount": sum(bool(e["signatureHook"]) for e in entries),
        "coordinatedLayerCount": sum(e["runtimeAssembly"] == "coordinated_hoodie" for e in entries),
        "vfxCount": sum(e["vfx"] != "none" for e in entries),
        "maximumPresentationSystems": max((len(e["presentationSystems"]) for e in entries), default=0),
        "uniquePaletteStories": len({e["paletteStory"] for e in entries}),
        "uniqueSilhouettes": len({e["silhouetteIdentity"] for e in entries}),
        "uniqueClosures": len({e["closureIdentity"] for e in entries}),
        "uniqueCollars": len({e["collarIdentity"] for e in entries}),
        "uniqueFocalCompositions": len({e["focalComposition"] for e in entries}),
        "uniqueBackTreatments": len({e["backTreatment"] for e in entries}),
    }
    return LegendaryValidation(not errors, tuple(errors), tuple(warnings), metrics)
