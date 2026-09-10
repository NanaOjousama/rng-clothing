"""Coherent autonomous garment concepts derived from the reference grammar.

This module chooses semantic construction.  It never draws pixels and never
loads reference artwork.  Option bundles encode compatibility learned by the
read-only corpus study; seeded choice supplies variation inside each family.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
GRAMMARS = ROOT / "specs/reference_corpus/garment_grammars.json"
PALETTES = ROOT / "specs/palettes/palette_stories.json"
SEED = 2026090106

# Each slot is a reliable renderer family, not a fixed garment.  Compatible
# bundles avoid random-axis soup while still allowing the engine to invent a
# concrete concept independently on every attempt.
FAMILIES: dict[str, dict[str, Any]] = {
    "FITTED_TEE": dict(category="simple_casual", material="COTTON_TEE", carrier="V5B_PLAIN_TEE", names=("Orchardline Tee", "Clearbrook Tee", "Mallowstep Tee"), silhouettes=("close_straight", "neat_tapered"), collars=("compact_bound_crew", "wide_shallow_crew"), hems=("clean_normal", "lightly_tucked"), details=("quiet_shoulder_break", "single_side_chest_plane"), backs=("quiet_bound_neck", "shallow_shoulder_arc"), palettes=("SPRING_ORCHARD", "WARM_EVERYDAY", "COOL_EVERYDAY")),
    "TEXTURED_KNIT": dict(category="knit_top", material="KNIT", carrier="V5D_KNIT", names=("Mossmere Crew Knit", "Snowbell Rib Knit", "Ambergrain Pullover"), silhouettes=("relaxed_continuous", "fitted_soft"), collars=("ribbed_crew", "modest_high_neck"), hems=("firm_rib_band", "soft_rib_band"), details=("paired_vertical_ribs", "broad_chest_knit_band"), backs=("quiet_knit_field", "reduced_rear_rib_rhythm"), palettes=("FOREST_LIBRARY", "SNOWBERRY", "AUTUMN_KNIT")),
    "SWEATER_VEST": dict(category="sweater_vest", material="KNIT", carrier="V5B_VEST", names=("Pollenridge Sweater Vest", "Cloudberry Scholar Vest", "Cedarcheck Knit Vest"), silhouettes=("compact_tapered", "regular_knit_shell"), collars=("deep_bound_v", "shallow_academic_v"), hems=("firm_rib_band", "soft_rib_band"), details=("paired_quiet_ribs", "single_broad_knit_band"), backs=("bound_armhole_knit_mass", "shallow_yoke_with_ribs"), palettes=("CREAM_ACADEMIC", "SPRING_ORCHARD", "EARTH_MOSS")),
    "OPEN_CARDIGAN": dict(category="cardigan", material="CARDIGAN", carrier="V5D_CARDIGAN", names=("Lilac Crossing Cardigan", "Seafoam Reading Cardigan", "Rosehush Open Knit"), silhouettes=("soft_relaxed_outer", "narrow_hanging_outer"), collars=("shallow_shawl_edge", "collarless_soft_band"), hems=("soft_rib_band", "straight_knit_hem"), details=("integrated_patch_pockets", "quiet_edge_ribbing"), backs=("unified_soft_knit_back", "shallow_rear_neck_and_yoke"), palettes=("LAVENDER_DAY", "SEA_GLASS", "ROSEWOOD_PASTEL")),
    "OPEN_CASUAL_SHIRT": dict(category="shirt_overshirt", material="WOVEN_SHIRT", carrier="V5B_STRUCTURED_SHIRT", names=("Coastlane Open Shirt", "Sunwash Camp Overshirt", "Birchwind Layer Shirt"), silhouettes=("relaxed_open_shell", "boxy_soft_overshirt"), collars=("wide_camp_collar", "folded_casual_collar"), hems=("rounded_split_shirttail", "relaxed_straight_split"), details=("one_integrated_chest_pocket", "asymmetric_small_flap"), backs=("broad_rear_yoke_and_pleat", "rear_yoke_and_clean_mass"), palettes=("COASTAL_MIST", "SUN_EMBER", "EVERYDAY_NEUTRAL")),
    "CREWNECK_SWEATSHIRT": dict(category="sweatshirt", material="SWEATSHIRT", carrier="V5B_SWEATER", names=("Berrycloud Crew", "Lakeglass Sweatshirt", "Apricot Track Crew"), silhouettes=("soft_boxy", "relaxed_rounded"), collars=("ribbed_crew", "high_ribbed_crew"), hems=("gathered_rib_band", "broad_soft_band"), details=("saddle_shoulder_plane", "single_horizontal_body_block"), backs=("quiet_rounded_mass", "curved_rear_saddle"), palettes=("ROSEWOOD_PASTEL", "SEA_GLASS", "BRIGHT_SPORT")),
    "WORK_JACKET": dict(category="structured_workwear", material="DENIM_WORKWEAR", carrier="V5D_WORK_SHELL", names=("Indigo Mill Work Jacket", "Ochre Yard Jacket", "Frostline Chore Jacket"), silhouettes=("boxy_heavy_shell", "regular_structured_shell"), collars=("firm_work_collar", "compact_spread_work_collar"), hems=("straight_heavy_hem", "reinforced_split_hem"), details=("paired_patch_pockets", "offset_utility_pockets"), backs=("broad_rear_yoke", "rear_yoke_with_center_seam"), palettes=("DENIM_BLUE", "HARVEST_WORKWEAR", "WINTER_FROST")),
    "FORMAL_WAISTCOAT": dict(category="formal_vest", material="BLAZER_FORMAL", carrier="V5D_WAISTCOAT", names=("Pearlwick Waistcoat", "Graphite Salon Waistcoat", "Creamhall Formal Vest"), silhouettes=("fitted_tapered_vest", "neat_tailored_vest"), collars=("deep_formal_v", "rounded_formal_v"), hems=("shaped_double_point", "soft_pointed_waist"), details=("paired_welt_pockets", "restrained_button_rhythm"), backs=("plain_tailored_back_adjuster", "rear_princess_seams_and_band"), palettes=("FORMAL_PEARL", "SOFT_CHARCOAL", "LUXURY_NEUTRAL")),
    "TRACK_JACKET": dict(category="sport_streetwear", material="SPORT_SHELL", carrier="V5D_FIELD_SHELL", names=("Citrus Relay Track Top", "Teal Current Track Shell", "Retroflare Zip Top"), silhouettes=("athletic_boxy_shell", "cropped_gathered_shell"), collars=("high_stand_collar", "low_funnel_collar"), hems=("gathered_sport_band", "cropped_elastic_band"), details=("shoulder_to_sleeve_block", "curved_saddle_and_slant_pockets"), backs=("curved_rear_saddle", "broad_contrast_yoke"), palettes=("BRIGHT_SPORT", "RETRO_TRACK", "HIGH_CONTRAST_STATEMENT")),
    "FITTED_BLAZER": dict(category="formal_piece", material="BLAZER_FORMAL", carrier="V5D_BLAZER", names=("Midnight Gallery Blazer", "Pearlline Fitted Blazer", "Silverleaf Salon Jacket"), silhouettes=("tailored_fitted", "softly_tapered_formal"), collars=("broad_notch_lapels", "slim_rounded_lapels"), hems=("shaped_tailored_hem", "single_button_curve"), details=("paired_welt_pockets", "one_pocket_square_plane"), backs=("rear_collar_center_seam_vent", "clean_back_with_shallow_vent"), palettes=("FORMAL_MIDNIGHT", "CEREMONIAL_IVORY", "GOTHIC_SILVER")),
    "SAILOR_TOP": dict(category="sailor_top", material="WOVEN_SHIRT", carrier="V5B_SAILOR", names=("Tidebell Sailor Top", "Pearlwake Deck Top", "Berryharbor Sailor Shirt"), silhouettes=("neat_wide_upper", "regular_soft_torso"), collars=("broad_sailor_v", "square_sailor_collar"), hems=("clean_straight", "lightly_tucked"), details=("double_collar_band", "contrast_v_inset"), backs=("large_tapered_rear_collar", "square_rear_sailor_panel"), palettes=("SAILOR_NAVY", "COASTAL_MIST", "SNOWBERRY")),
    "POLO_KNIT": dict(category="wildcard_everyday", material="WOVEN_SHIRT", carrier="V5B_STRUCTURED_SHIRT", names=("Seafig Polo Knit", "Creamgrove Collared Knit", "Coralfield Polo"), silhouettes=("neat_regular", "lightly_fitted"), collars=("small_polo_collar", "soft_spread_polo_collar"), hems=("clean_straight", "light_rib_hem"), details=("short_contained_placket", "single_chest_plane"), backs=("rear_collar_band", "small_rear_yoke"), palettes=("SEA_GLASS", "CREAM_ACADEMIC", "SPRING_ORCHARD")),
}

ORDER = tuple(FAMILIES)

def _choice(rng: random.Random, values: tuple[str, ...]) -> str:
    return values[rng.randrange(len(values))]

def _grammar_map() -> dict[str, dict[str, Any]]:
    data = json.loads(GRAMMARS.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["grammars"]}

def _palette_ids() -> set[str]:
    data = json.loads(PALETTES.read_text(encoding="utf-8"))
    return {item["id"] for item in data["stories"]}

def concept_for(family: str, attempt: int, *, seed: int = SEED) -> dict[str, Any]:
    cfg = FAMILIES[family]
    rng = random.Random(seed + ORDER.index(family) * 104729 + attempt * 7919)
    silhouette = _choice(rng, cfg["silhouettes"]); collar = _choice(rng, cfg["collars"])
    hem = _choice(rng, cfg["hems"]); detail = _choice(rng, cfg["details"]); back = _choice(rng, cfg["backs"])
    palette = _choice(rng, cfg["palettes"]); name = _choice(rng, cfg["names"])
    opening = {
        "OPEN_CARDIGAN":"broad_open_front", "OPEN_CASUAL_SHIRT":"two_open_woven_leaves",
        "WORK_JACKET":"firm_full_placket", "FORMAL_WAISTCOAT":"buttoned_deep_v",
        "TRACK_JACKET":"contained_half_zip", "FITTED_BLAZER":"overlapping_single_button",
        "POLO_KNIT":"short_partial_placket",
    }.get(family, "closed")
    layering = {
        "SWEATER_VEST":"woven_shirt_beneath", "OPEN_CARDIGAN":"broad_inner_shirt",
        "OPEN_CASUAL_SHIRT":"broad_inner_tee", "FORMAL_WAISTCOAT":"formal_shirt_beneath",
        "FITTED_BLAZER":"visible_formal_shirt", "SAILOR_TOP":"contrast_v_inset",
    }.get(family, "single_fabric_mass")
    sleeves = {
        "FITTED_TEE":"native_short_same_fabric", "SWEATER_VEST":"native_inner_shirt_sleeves",
        "FORMAL_WAISTCOAT":"native_formal_shirt_sleeves", "SAILOR_TOP":"native_short_banded",
        "POLO_KNIT":"native_short_bound",
    }.get(family, "native_long_coordinated")
    concept = {
        "id": f"AUTO_{family}_{attempt:02d}", "attempt": attempt, "family": family,
        "category": cfg["category"], "name": name, "carrier": cfg["carrier"],
        "material": cfg["material"], "paletteStory": palette,
        "structuralAxes": {"silhouetteVolume": silhouette, "fitProportion": silhouette, "collarNeckline": collar,
            "openingTopology": opening, "layeringTopology": layering, "hemWaist": hem,
            "pocketPanelArchitecture": detail, "sleeveRelationship": sleeves,
            "sideConstruction": f"compressed_{detail}_with_{hem}", "backConstruction": back,
            "majorColorBlockTopology": f"construction_following_{detail}"},
        "secondaryAxes": {"cuffBehavior":"native_cuff_matches_material", "seamYokeTreatment":back,
            "ribbing":"coherent_only_where_structural", "trimPlacement":"collar_or_termination_only",
            "surfacePattern":"none_or_one_supporting_system", "asymmetry":"restrained_if_pocket_driven",
            "closureDetail":opening},
        "directionalAuthorship": {
            "front": f"{collar}; {opening}; {detail}; {hem}",
            "right": f"one-side depth with {detail}; opening compresses; {hem} terminates naturally",
            "back": f"{back}; no front closure copied; coherent rear fabric field",
            "left": f"mirrored body attachment but independently compressed {detail}; {hem} remains readable"},
        "designHierarchy": {"dominant": f"{silhouette} with {collar}", "supporting": detail, "decorationBudget":"restrained"},
        "referenceArtworkRequired": False, "customSleeves": False,
    }
    return concept

def semantic_errors(concept: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    axes = concept["structuralAxes"]
    vague = {"normal", "standard", "simple", "default", "generic"}
    if any(value in vague for value in axes.values()): errors.append("under-specified structural axis")
    if concept["paletteStory"] not in _palette_ids(): errors.append("unknown palette story")
    if concept["family"] not in _grammar_map(): errors.append("family missing from reference grammar")
    if concept["customSleeves"]: errors.append("custom sleeves forbidden")
    if axes["openingTopology"] == "closed" and axes["layeringTopology"] in {"broad_inner_shirt", "broad_inner_tee"}: errors.append("closed opening conflicts with broad inner layer")
    return errors

def structural_difference(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    l, r = left["structuralAxes"], right["structuralAxes"]
    high_keys = ("silhouetteVolume", "collarNeckline", "openingTopology", "layeringTopology", "hemWaist")
    medium_keys = ("pocketPanelArchitecture", "sleeveRelationship", "sideConstruction", "backConstruction", "majorColorBlockTopology")
    high = [key for key in high_keys if l[key] != r[key]]; medium = [key for key in medium_keys if l[key] != r[key]]
    anchor = l["silhouetteVolume"] != r["silhouetteVolume"] or l["openingTopology"] != r["openingTopology"] or l["layeringTopology"] != r["layeringTopology"]
    return {"highDifferences": high, "mediumDifferences": medium, "meaningfulDifferenceCount": len(high)+len(medium), "hasRequiredAnchor": anchor, "pass": len(high)+len(medium) >= 3 and anchor}

def generate_recovery_concepts(*, seed: int = SEED) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []; rejected: list[dict[str, Any]] = []
    for family in ORDER:
        for attempt in range(1, 6):
            concept = concept_for(family, attempt, seed=seed)
            reasons = semantic_errors(concept)
            pair_failures = [other["id"] for other in accepted if not structural_difference(concept, other)["pass"]]
            if pair_failures: reasons.append("insufficient structural distance from " + ", ".join(pair_failures))
            if reasons:
                rejected.append({"concept": concept, "stage":"semantic", "reasons": reasons}); continue
            accepted.append(concept); break
        else:
            rejected.append({"family": family, "stage":"semantic", "reasons":["five attempts exhausted"]})
    return accepted, rejected
