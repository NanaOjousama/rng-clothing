"""Coordinate-free deterministic V5D masculine garment recipes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from generator.v2_recipe_engine import _coordinate_key_errors, _schema_errors
from generator.v5b.engine import _base, _design, load_v5b_data, validate_v5b_recipe
from generator.v4.engine import _force_short_outerwear


ROOT = Path(__file__).resolve().parents[2]
GRAMMAR = ROOT / "generator" / "data" / "v5d" / "masculine_art_grammar.json"
SCHEMA = ROOT / "generator" / "schema" / "garment_recipe_v5d.schema.json"


@dataclass(frozen=True)
class V5DRecipeValidation:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_v5d_data() -> dict[str, Any]:
    return {"grammar": _json(GRAMMAR), "schema": _json(SCHEMA)}


def validate_v5d_recipe(recipe: dict[str, Any], data: dict[str, Any] | None = None) -> V5DRecipeValidation:
    data = data or load_v5d_data()
    errors = _schema_errors(recipe, data["schema"])
    errors.extend(_coordinate_key_errors({key: value for key, value in recipe.items() if key != "baseUpperRecipe"}))
    warnings: list[str] = []
    if errors:
        return V5DRecipeValidation(False, tuple(errors), tuple(warnings))
    base = validate_v5b_recipe(recipe["baseUpperRecipe"])
    errors.extend(f"V5B runtime base: {message}" for message in base.errors)
    warnings.extend(f"V5B runtime base: {message}" for message in base.warnings)
    rarity = recipe["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]["rarity"]
    budget = data["grammar"]["rarityBudgets"][rarity]
    support_count = len(recipe["surfacePlan"]["supportGestures"])
    if support_count > budget["maximumSupportSystems"]:
        errors.append(f"{rarity} support-system ceiling exceeded ({support_count})")
    if recipe["benchmarkBasis"]["copiedPixels"]:
        errors.append("benchmark pixels may never enter a semantic recipe")
    if recipe["fashionFamily"] not in data["grammar"]["families"]:
        errors.append(f"missing formal family grammar for {recipe['fashionFamily']}")
    if recipe["articleRole"] == "STREET_HOODIE" and recipe["necklineIntent"] != "hooded":
        errors.append("street hoodie requires hooded neckline")
    if recipe["articleRole"] in {"FORMAL_WAISTCOAT", "UTILITY_VEST"} and recipe["layeringIntent"] != "vest_over_inner":
        errors.append("vest roles require explicit vest-over-inner construction")
    return V5DRecipeValidation(not errors, tuple(errors), tuple(warnings))


def _base_upper(index: int, runtime: dict[str, Any]) -> dict[str, Any]:
    # Frozen V3's benchmark schema intentionally has twelve generation slots.
    # V5D owns the visible identity and may deterministically reuse a frozen
    # foundation slot for entries 13-14 without creating hidden candidates.
    foundation_index = (index - 1) % 12 + 1
    design = _design(foundation_index, runtime["theme"], runtime["rarity"], runtime["archetype"], runtime["name"])
    design["paletteStory"] = runtime["palette"]
    design["itemDescription"] = runtime["description"]
    article = runtime["baseArticle"]
    base_article = load_v5b_data()["articles"]["articles"][article]["baseArticle"]
    if base_article == "CROPPED_JACKET":
        # Frozen V4 exposes no distinct forcing helper for cropped jackets;
        # its short-outerwear normalization supplies the same required split
        # shell/inner-layer construction before the cropped adapter trims it.
        _force_short_outerwear(design)
    base = _base(foundation_index, design, base_article)
    recipe = {
        "formatVersion": "5.2.0",
        "id": f"v5b-{index:02d}",
        "collection": "V5BUpperBenchmark",
        "articleType": article,
        "constructionVariant": runtime["variant"],
        "sleeveIntent": runtime["sleeve"],
        "shoulderIntent": runtime["baseShoulder"],
        "necklineIntent": runtime["baseNeckline"],
        "collarIntent": runtime["baseCollar"],
        "layeringIntent": runtime["baseLayering"],
        "openingIntent": runtime["baseOpening"],
        "surfaceTranslation": {
            "primaryZone": runtime["zone"],
            "sleeveContinuation": "trim_echo" if runtime["sleeve"] != "SHORT_SLEEVE" else "fabric_match",
            "cuffTreatment": "layered" if runtime["sleeve"] == "LAYERED_INNER_OUTER_SLEEVE" else "contrast" if runtime["sleeve"] == "ROLLED_CUFFED_SLEEVE" else "simple"
        },
        "baseArticleRecipe": base,
    }
    result = validate_v5b_recipe(recipe)
    if not result.valid:
        raise ValueError(f"invalid V5D runtime base {index}: {'; '.join(result.errors)}")
    return recipe


def generate_v5d_batch() -> dict[str, Any]:
    """Return the exact fourteen requested concepts; no hidden candidates."""

    specs = [
        dict(fashionFamily="CASUAL", articleRole="CASUAL_SHIRT", articleSubtype="henley_tee", fitIntent="regular", sleeveIntent="SHORT_SLEEVE", shoulderIntent="standard", necklineIntent="crew", collarIntent="none", openingIntent="short_placket", layeringIntent="single_layer", hemIntent="plain", constructionFeatures=["crew_neck", "short_henley_placket", "clean_hem"], surfacePlan=dict(primaryGesture="henley_placket", supportGestures=["chest_stripe"], focalArea="upper_chest", panelSystem="solid_body", trimSystem="narrow_neck_trim", patternSystem="single_chest_stripe", motifSystem="none", topology="front_placket_hem_wrap"), paletteStory="seafoam_coral", lightPalette=True, benchmarkBasis=dict(primaryPacks=["GentlemansCollection", "ColourableBasics"], generalizedTraits=["simple_article_signal", "light_color_masculinity", "compact_center_detail"], mixedEvidenceRole="none", copiedPixels=False), runtime=dict(baseArticle="FITTED_SHIRT", variant="plain_tee", sleeve="SHORT_SLEEVE", baseShoulder="standard", baseNeckline="crew", baseCollar="none", baseLayering="single_layer", baseOpening="closed", zone="chest", theme="beach_casual", rarity="Common", archetype="BUTTON_SHIRT", name="Tideglass Henley", description="A light sea-glass henley with one crisp chest rhythm and an easy everyday fit.", palette="seafoam_coral")),
        dict(fashionFamily="WORKWEAR_FARMWEAR", articleRole="WORK_SHIRT", articleSubtype="rolled_farm_shirt", fitIntent="regular", sleeveIntent="ROLLED_CUFFED_SLEEVE", shoulderIntent="reinforced", necklineIntent="open", collarIntent="shirt_collar", openingIntent="buttoned", layeringIntent="single_layer", hemIntent="structured", constructionFeatures=["work_collar", "full_placket", "paired_chest_pockets", "back_yoke", "rolled_cuffs"], surfacePlan=dict(primaryGesture="work_yoke_pockets", supportGestures=[], focalArea="pockets", panelSystem="shoulder_yoke", trimSystem="utility_seams", patternSystem="none", motifSystem="none", topology="front_pockets_back_yoke"), paletteStory="harvest_cream", lightPalette=True, benchmarkBasis=dict(primaryPacks=["GentlemansCollection", "ColourableBasics"], generalizedTraits=["overall_workwear_rhythm", "paired_pocket_clarity", "rolled_sleeve_practicality"], mixedEvidenceRole="neutral_construction_reviewed", copiedPixels=False), runtime=dict(baseArticle="FITTED_SHIRT", variant="structured_shirt", sleeve="ROLLED_CUFFED_SLEEVE", baseShoulder="standard", baseNeckline="open", baseCollar="shirt_collar", baseLayering="single_layer", baseOpening="buttoned", zone="yoke", theme="seasonal_soft", rarity="Common", archetype="BUTTON_SHIRT", name="Orchard Hand Workshirt", description="A warm cream farm shirt with a reinforced yoke, useful pockets, and rolled cuffs.", palette="harvest_cream")),
        dict(fashionFamily="KNIT_CARDIGAN", articleRole="KNIT_SWEATER", articleSubtype="color_band_crew_knit", fitIntent="relaxed", sleeveIntent="FITTED_LONG_SLEEVE", shoulderIntent="standard", necklineIntent="crew", collarIntent="none", openingIntent="closed", layeringIntent="single_layer", hemIntent="ribbed", constructionFeatures=["crew_neck", "upper_knit_band", "ribbed_hem"], surfacePlan=dict(primaryGesture="knit_band", supportGestures=[], focalArea="upper_chest", panelSystem="continuous_knit", trimSystem="ribbed", patternSystem="stepped_knit_band", motifSystem="none", topology="upper_and_lower_wrap"), paletteStory="storybook_blue", lightPalette=True, benchmarkBasis=dict(primaryPacks=["GentlemansCollection", "ProjectHailMary"], generalizedTraits=["striped_knit_clarity", "continuous_cloth_mass", "colorful_sweatwear"], mixedEvidenceRole="none", copiedPixels=False), runtime=dict(baseArticle="SWEATER", variant="patterned_knit", sleeve="FITTED_LONG_SLEEVE", baseShoulder="standard", baseNeckline="crew", baseCollar="none", baseLayering="single_layer", baseOpening="closed", zone="hem", theme="seasonal_soft", rarity="Common", archetype="SWEATER", name="Skylark Cable Knit", description="A sky-blue crew knit with a stepped woven band and tidy ribbing.", palette="storybook_blue")),
        dict(fashionFamily="HOODIE_SWEATWEAR", articleRole="STREET_HOODIE", articleSubtype="street_pouch_hoodie", fitIntent="relaxed", sleeveIntent="LAYERED_INNER_OUTER_SLEEVE", shoulderIntent="dropped", necklineIntent="hooded", collarIntent="none", openingIntent="closed", layeringIntent="single_layer", hemIntent="ribbed", constructionFeatures=["hood_mass", "contrast_hood_lining", "pouch_pocket", "ribbed_hem", "sleeve_stripe"], surfacePlan=dict(primaryGesture="hood_pouch", supportGestures=["sleeve_stripe"], focalArea="pockets", panelSystem="soft_body", trimSystem="hood_and_cuff", patternSystem="single_sleeve_stripe", motifSystem="none", topology="hood_wrap_pouch_front_side_end"), paletteStory="teal_circuit", lightPalette=False, benchmarkBasis=dict(primaryPacks=["ProjectHailMary", "CoatsAndJackets"], generalizedTraits=["hood_depth", "pouch_readability", "streetwear_trim"], mixedEvidenceRole="none", copiedPixels=False), runtime=dict(baseArticle="SWEATER", variant="relaxed_knit", sleeve="LAYERED_INNER_OUTER_SLEEVE", baseShoulder="dropped", baseNeckline="high", baseCollar="rounded", baseLayering="single_layer", baseOpening="closed", zone="chest", theme="cyber_tech", rarity="Uncommon", archetype="SWEATER", name="Neon Harbor Street Hoodie", description="A relaxed teal street hoodie with a dark-lined hood, broad pouch, and one clean sleeve stripe.", palette="teal_circuit")),
        dict(fashionFamily="KNIT_CARDIGAN", articleRole="CARDIGAN", articleSubtype="shawl_cardigan", fitIntent="relaxed", sleeveIntent="FITTED_LONG_SLEEVE", shoulderIntent="dropped", necklineIntent="open", collarIntent="shawl", openingIntent="center_open", layeringIntent="visible_inner_layer", hemIntent="ribbed", constructionFeatures=["shawl_edge", "visible_inner_shirt", "lower_patch_pockets", "ribbed_hem"], surfacePlan=dict(primaryGesture="cardigan_opening", supportGestures=["lower_pockets"], focalArea="neck", panelSystem="open_knit_panels", trimSystem="ribbed_edge", patternSystem="none", motifSystem="none", topology="front_open_side_compressed_back_neck"), paletteStory="rose_sage", lightPalette=True, benchmarkBasis=dict(primaryPacks=["GentlemansCollection", "ColourableBasics"], generalizedTraits=["open_sweater_layering", "cardigan_edge", "soft_color_masculinity"], mixedEvidenceRole="none", copiedPixels=False), runtime=dict(baseArticle="STANDARD_JACKET", variant="cardigan", sleeve="FITTED_LONG_SLEEVE", baseShoulder="dropped", baseNeckline="crew", baseCollar="none", baseLayering="visible_inner_layer", baseOpening="center_open", zone="hem", theme="storybook_whimsical", rarity="Uncommon", archetype="JACKET", name="Rowan Morning Cardigan", description="A light sage cardigan with a soft shawl edge, rose undershirt, and useful knit pockets.", palette="rose_sage")),
        dict(fashionFamily="VEST_WAISTCOAT", articleRole="FORMAL_WAISTCOAT", articleSubtype="double_button_waistcoat", fitIntent="fitted", sleeveIntent="FITTED_LONG_SLEEVE", shoulderIntent="narrow", necklineIntent="v_neck", collarIntent="none", openingIntent="buttoned", layeringIntent="vest_over_inner", hemIntent="tailored", constructionFeatures=["deep_v", "inner_shirt", "double_button_rhythm", "welt_pockets", "tailored_points"], surfacePlan=dict(primaryGesture="waistcoat_frame", supportGestures=["formal_buttons"], focalArea="center_chest", panelSystem="fitted_vest_panels", trimSystem="fine_piping", patternSystem="none", motifSystem="none", topology="front_v_back_panel"), paletteStory="ink_ivory", lightPalette=False, benchmarkBasis=dict(primaryPacks=["FrogwaresSherlock", "GentlemansCollection"], generalizedTraits=["shirt_vest_value_hierarchy", "tailored_button_rhythm", "quiet_formal_back"], mixedEvidenceRole="none", copiedPixels=False), runtime=dict(baseArticle="VEST_TOP", variant="waistcoat", sleeve="FITTED_LONG_SLEEVE", baseShoulder="narrow", baseNeckline="v_neck", baseCollar="none", baseLayering="vest_over_inner", baseOpening="buttoned", zone="placket", theme="cyber_tech", rarity="Uncommon", archetype="BUTTON_SHIRT", name="Silverline Evening Waistcoat", description="A precise charcoal waistcoat over an ivory shirt, finished with paired silver buttons.", palette="ink_ivory")),
        dict(fashionFamily="VEST_WAISTCOAT", articleRole="UTILITY_VEST", articleSubtype="farm_utility_vest", fitIntent="regular", sleeveIntent="ROLLED_CUFFED_SLEEVE", shoulderIntent="standard", necklineIntent="high", collarIntent="utility", openingIntent="buttoned", layeringIntent="vest_over_inner", hemIntent="structured", constructionFeatures=["high_vest_edge", "inner_work_shirt", "utility_blocks", "shoulder_tabs", "waist_band"], surfacePlan=dict(primaryGesture="utility_blocks", supportGestures=["shoulder_tabs"], focalArea="pockets", panelSystem="split_utility_front", trimSystem="reinforced_edges", patternSystem="none", motifSystem="none", topology="front_blocks_side_seams_back_panel"), paletteStory="field_tan", lightPalette=True, benchmarkBasis=dict(primaryPacks=["ColourableBasics", "GentlemansCollection"], generalizedTraits=["overall_and_suspender_layering", "work_vest_blocks", "readable_inner_relationship"], mixedEvidenceRole="neutral_construction_reviewed", copiedPixels=False), runtime=dict(baseArticle="VEST_TOP", variant="utility_vest", sleeve="ROLLED_CUFFED_SLEEVE", baseShoulder="standard", baseNeckline="high", baseCollar="utility", baseLayering="vest_over_inner", baseOpening="buttoned", zone="chest", theme="military_structured", rarity="Uncommon", archetype="BUTTON_SHIRT", name="Brasshook Utility Vest", description="A practical tan utility vest over rolled cream sleeves, with reinforced pockets and shoulder tabs.", palette="field_tan")),
        dict(fashionFamily="JACKET_OUTERWEAR", articleRole="CROPPED_FIELD_JACKET", articleSubtype="short_field_shell", fitIntent="cropped", sleeveIntent="ROLLED_CUFFED_SLEEVE", shoulderIntent="reinforced", necklineIntent="open", collarIntent="lapel", openingIntent="center_open", layeringIntent="visible_inner_layer", hemIntent="cropped", constructionFeatures=["lapels", "visible_inner_layer", "paired_pocket_flaps", "shoulder_yoke", "short_waist", "cuffs"], surfacePlan=dict(primaryGesture="lapel_pockets", supportGestures=["shoulder_yoke", "waist_trim"], focalArea="pockets", panelSystem="split_outer_shell", trimSystem="lapel_and_cuff", patternSystem="none", motifSystem="field_tab", topology="front_shell_side_opening_back_yoke"), paletteStory="aot_high_contrast_field", lightPalette=True, benchmarkBasis=dict(primaryPacks=["CoatsAndJackets", "GentlemansCollection"], generalizedTraits=["short_outer_shell", "clear_lapel_opening", "pocket_flap_rhythm"], mixedEvidenceRole="none", copiedPixels=False), runtime=dict(baseArticle="CROPPED_JACKET", variant="field_jacket", sleeve="ROLLED_CUFFED_SLEEVE", baseShoulder="standard", baseNeckline="open", baseCollar="lapel", baseLayering="visible_inner_layer", baseOpening="center_open", zone="outer_panels", theme="celestial_fantasy", rarity="Rare", archetype="JACKET", name="Sunfield Scout Jacket", description="A bright cropped field shell with strong lapels, pocket flaps, and a fitted olive inner layer.", palette="aot_high_contrast_field")),
        dict(fashionFamily="FORMAL_SUIT", articleRole="FORMAL_BLAZER", articleSubtype="evening_blazer", fitIntent="fitted", sleeveIntent="LAYERED_INNER_OUTER_SLEEVE", shoulderIntent="standard", necklineIntent="open", collarIntent="lapel", openingIntent="partial_open", layeringIntent="visible_inner_layer", hemIntent="tailored", constructionFeatures=["balanced_lapels", "shirt_triangle", "narrow_tie", "single_button", "pocket_square", "tailored_corners"], surfacePlan=dict(primaryGesture="formal_hierarchy", supportGestures=["pocket_square", "button_rhythm"], focalArea="neck", panelSystem="tailored_outer_panels", trimSystem="satin_lapel", patternSystem="none", motifSystem="none", topology="front_hierarchy_back_neck_seam"), paletteStory="midnight_gold", lightPalette=False, benchmarkBasis=dict(primaryPacks=["FrogwaresSherlock", "TGAAClothing"], generalizedTraits=["lapel_shirt_tie_hierarchy", "small_formal_accent", "fitted_vertical_order"], mixedEvidenceRole="none", copiedPixels=False), runtime=dict(baseArticle="STANDARD_JACKET", variant="blazer", sleeve="LAYERED_INNER_OUTER_SLEEVE", baseShoulder="standard", baseNeckline="open", baseCollar="lapel", baseLayering="visible_inner_layer", baseOpening="partial_open", zone="collar", theme="celestial_fantasy", rarity="Rare", archetype="JACKET", name="Midnight Laurel Blazer", description="A midnight formal blazer with satin lapels, a narrow gold tie, and one laurel-green pocket square.", palette="midnight_gold")),
        dict(fashionFamily="PERIOD_GENTLEMAN", articleRole="PERIOD_TOP", articleSubtype="cravat_coat_top", fitIntent="fitted", sleeveIntent="FITTED_LONG_SLEEVE", shoulderIntent="standard", necklineIntent="high", collarIntent="cravat", openingIntent="double_breasted", layeringIntent="visible_inner_layer", hemIntent="tailored", constructionFeatures=["high_collar", "cravat", "offset_buttons", "brocade_edge", "watch_chain", "tailored_corners"], surfacePlan=dict(primaryGesture="cravat_brocade", supportGestures=["offset_buttons", "watch_chain"], focalArea="neck", panelSystem="period_coat_panels", trimSystem="brocade_edge", patternSystem="subtle_repeat", motifSystem="none", topology="front_focal_side_collar_back_seam"), paletteStory="aot_civilian_rust", lightPalette=False, benchmarkBasis=dict(primaryPacks=["FrogwaresSherlock", "TGAAClothing"], generalizedTraits=["cravat_focal", "offset_formal_closure", "jewel_accent_tailoring"], mixedEvidenceRole="none", copiedPixels=False), runtime=dict(baseArticle="STANDARD_JACKET", variant="blazer", sleeve="FITTED_LONG_SLEEVE", baseShoulder="standard", baseNeckline="high", baseCollar="high_collar", baseLayering="visible_inner_layer", baseOpening="partial_open", zone="collar", theme="storybook_whimsical", rarity="Rare", archetype="JACKET", name="Copperwick Gentleman Top", description="A rust period coat-top with a cream cravat, offset buttons, and restrained brocade edging.", palette="aot_civilian_rust")),
        dict(fashionFamily="MILITARY_FIELDWEAR", articleRole="MILITARY_TOP", articleSubtype="compact_officer_jacket", fitIntent="structured", sleeveIntent="LAYERED_INNER_OUTER_SLEEVE", shoulderIntent="reinforced", necklineIntent="high", collarIntent="high_collar", openingIntent="buttoned", layeringIntent="visible_inner_layer", hemIntent="structured", constructionFeatures=["high_field_collar", "epaulettes", "disciplined_buttons", "paired_chest_tabs", "short_belt_line", "back_yoke"], surfacePlan=dict(primaryGesture="field_panels", supportGestures=["epaulettes", "chest_tabs"], focalArea="upper_chest", panelSystem="disciplined_field_panels", trimSystem="collar_cuff_belt", patternSystem="none", motifSystem="small_angular_badge", topology="shoulder_wrap_front_tabs_back_yoke"), paletteStory="aot_field_olive", lightPalette=False, benchmarkBasis=dict(primaryPacks=["TGAAClothing", "CoatsAndJackets"], generalizedTraits=["service_collar", "ordered_chest_geometry", "short_field_waist"], mixedEvidenceRole="none", copiedPixels=False), runtime=dict(baseArticle="CROPPED_JACKET", variant="military_jacket", sleeve="LAYERED_INNER_OUTER_SLEEVE", baseShoulder="standard", baseNeckline="high", baseCollar="high_collar", baseLayering="visible_inner_layer", baseOpening="center_open", zone="yoke", theme="elemental", rarity="Rare", archetype="JACKET", name="Greywatch Officer Jacket", description="A compact olive officer jacket with a guarded collar, shoulder tabs, and disciplined chest geometry.", palette="aot_field_olive")),
        dict(fashionFamily="FANTASY_ADVENTURER", articleRole="ADVENTURER_TUNIC", articleSubtype="belted_wayfarer_tunic", fitIntent="regular", sleeveIntent="FITTED_LONG_SLEEVE", shoulderIntent="reinforced", necklineIntent="layered_v", collarIntent="utility", openingIntent="wrap", layeringIntent="tunic_over_inner", hemIntent="belted", constructionFeatures=["layered_v", "one_shoulder_wrap", "diagonal_sash", "waist_belt", "tunic_center", "utility_tab"], surfacePlan=dict(primaryGesture="tunic_sash", supportGestures=["shoulder_wrap", "waist_belt"], focalArea="shoulder", panelSystem="layered_tunic", trimSystem="leather_piping", patternSystem="none", motifSystem="small_waymark", topology="front_diagonal_side_resolution_back_belt"), paletteStory="plum_moon", lightPalette=False, benchmarkBasis=dict(primaryPacks=["AdventurersArmourAndOutfits", "MixedShire"], generalizedTraits=["tunic_layering", "sash_and_belt", "fantasy_utility_geometry"], mixedEvidenceRole="neutral_construction_reviewed", copiedPixels=False), runtime=dict(baseArticle="FITTED_SHIRT", variant="structured_shirt", sleeve="FITTED_LONG_SLEEVE", baseShoulder="standard", baseNeckline="high", baseCollar="utility", baseLayering="visible_inner_layer", baseOpening="wrap_suggestion", zone="waist", theme="storybook_whimsical", rarity="Rare", archetype="BUTTON_SHIRT", name="Amethyst Wayfarer Tunic", description="A layered violet wayfarer tunic with one wrapped shoulder, a leather sash, and a bright waymark.", palette="plum_moon")),
        dict(fashionFamily="ARMOR_TUNIC_TABARD", articleRole="ARMOR_TABARD", articleSubtype="light_plate_tabard", fitIntent="structured", sleeveIntent="FITTED_LONG_SLEEVE", shoulderIntent="armored", necklineIntent="high", collarIntent="guarded", openingIntent="tabard_center", layeringIntent="armor_over_underlayer", hemIntent="tabard", constructionFeatures=["guarded_neck", "shoulder_plates", "chest_segments", "center_tabard", "waist_belt", "small_crest"], surfacePlan=dict(primaryGesture="plate_tabard", supportGestures=["segmented_chest", "heraldic_crest"], focalArea="tabard", panelSystem="plate_over_cloth", trimSystem="metal_and_leather_edges", patternSystem="none", motifSystem="abstract_ember_crest", topology="plate_wrap_center_cloth_back_tabard"), paletteStory="ember_charcoal", lightPalette=False, benchmarkBasis=dict(primaryPacks=["AdventurersArmourAndOutfits", "BonestealerPack"], generalizedTraits=["plate_cloth_separation", "guarded_neck", "heraldic_center_without_logo"], mixedEvidenceRole="none", copiedPixels=False), runtime=dict(baseArticle="VEST_TOP", variant="utility_vest", sleeve="FITTED_LONG_SLEEVE", baseShoulder="standard", baseNeckline="high", baseCollar="utility", baseLayering="vest_over_inner", baseOpening="buttoned", zone="chest", theme="elemental", rarity="Rare", archetype="BUTTON_SHIRT", name="Emberward Tabard Armor", description="Light charcoal platework frames a crimson tabard and an original ember crest.", palette="ember_charcoal")),
        dict(fashionFamily="ALT_DARK_FASHION", articleRole="ALT_STREET_TOP", articleSubtype="asymmetric_cross_zip", fitIntent="fitted", sleeveIntent="FITTED_LONG_SLEEVE", shoulderIntent="narrow", necklineIntent="high", collarIntent="high_collar", openingIntent="cross_zip", layeringIntent="visible_inner_layer", hemIntent="structured", constructionFeatures=["asymmetric_collar", "cross_zip", "one_shoulder_panel", "contrast_underlayer", "sleeve_stripe", "short_hem"], surfacePlan=dict(primaryGesture="cross_zip", supportGestures=["shoulder_panel", "sleeve_stripe"], focalArea="side_chest", panelSystem="asymmetric_front", trimSystem="zip_and_cuff", patternSystem="single_sleeve_stripe", motifSystem="small_split_diamond", topology="front_diagonal_one_side_back_shoulder_cue"), paletteStory="berry_cream", lightPalette=True, benchmarkBasis=dict(primaryPacks=["BonestealerPack", "ProjectHailMary"], generalizedTraits=["asymmetric_paneling", "graphic_street_rhythm", "colorful_alt_styling"], mixedEvidenceRole="technique_only", copiedPixels=False), runtime=dict(baseArticle="FITTED_SHIRT", variant="structured_shirt", sleeve="FITTED_LONG_SLEEVE", baseShoulder="narrow", baseNeckline="high", baseCollar="high_collar", baseLayering="visible_inner_layer", baseOpening="wrap_suggestion", zone="chest", theme="creature_inspired", rarity="Rare", archetype="BUTTON_SHIRT", name="Berry Static Cross-Zip Top", description="A fitted berry street top with an asymmetric cross-zip, cream underlayer, and split-diamond mark.", palette="berry_cream"))
    ]
    recipes: list[dict[str, Any]] = []
    for index, spec in enumerate(specs, 1):
        runtime = spec.pop("runtime")
        recipe = {
            "formatVersion": "5.4.0",
            "id": f"v5d-{index:02d}",
            "collection": "V5DMasculineArtGrammar",
            **spec,
            "baseUpperRecipe": _base_upper(index, runtime),
        }
        result = validate_v5d_recipe(recipe)
        if not result.valid:
            raise ValueError(f"invalid V5D recipe {recipe['id']}: {'; '.join(result.errors)}")
        recipes.append(recipe)
    return {
        "generatorVersion": "5.4.0",
        "collection": "V5DMasculineArtGrammar",
        "seed": 2026083054,
        "count": len(recipes),
        "hiddenCandidateCount": 0,
        "recipes": recipes,
    }
