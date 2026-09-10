"""Coordinate-free semantic recipes for V4.6B diagnostics."""

from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GRAMMAR = ROOT / "generator" / "data" / "fashionsense" / "v46b" / "lower_body_article_grammar.json"


def load_grammar() -> dict:
    return json.loads(GRAMMAR.read_text(encoding="utf-8"))


def generate_v46b_prototypes() -> list[dict]:
    recipes = [
        {"formatVersion":"4.6B","id":"v46b-pants-01","name":"Harborline Fitted Trousers","description":"Clean full-length fitted trousers with a readable inseam and paired ankle finish.","articleType":"PANTS","rarity":"Common","construction":{"fit":"fitted","length":"full","waist":"standard","construction":"plain"},"surface":{"primary":"two_leg_structure","support":"none","accent":"none"},"paletteStory":"denim_cream","runtimeStatus":"EXPERIMENTAL"},
        {"formatVersion":"4.6B","id":"v46b-pants-02","name":"Ridgeline Panel Trousers","description":"Tapered field trousers with reinforced knee panels, side seams, and controlled cuffs.","articleType":"PANTS","rarity":"Rare","construction":{"fit":"tapered","length":"ankle","waist":"contrast","construction":"paneled"},"surface":{"primary":"outer_leg_panels","support":"reinforced_knees","accent":"paired_cuffs"},"paletteStory":"forest_leather","runtimeStatus":"EXPERIMENTAL"},
        {"formatVersion":"4.6B","id":"v46b-shorts-01","name":"Cedar Day Shorts","description":"Simple fitted mid-length shorts with separated legs and clean paired hems.","articleType":"SHORTS","rarity":"Common","construction":{"fit":"fitted","length":"mid","hem":"clean","construction":"plain"},"surface":{"primary":"paired_short_legs","support":"none","accent":"none"},"paletteStory":"warm_neutral","runtimeStatus":"EXPERIMENTAL"},
        {"formatVersion":"4.6B","id":"v46b-shorts-02","name":"Bramble Cuff Shorts","description":"Relaxed utility shorts with shaped leg openings, rolled cuffs, and side panels.","articleType":"SHORTS","rarity":"Uncommon","construction":{"fit":"relaxed","length":"mid","hem":"rolled","construction":"utility"},"surface":{"primary":"rolled_pair_hems","support":"side_utility_panels","accent":"none"},"paletteStory":"rust_sage","runtimeStatus":"EXPERIMENTAL"},
        {"formatVersion":"4.6B","id":"v46b-skirt-01","name":"Willow A-Line Skirt","description":"A clean short A-line skirt with a unified flare and restrained waistband.","articleType":"SKIRT","rarity":"Common","construction":{"silhouette":"a_line","length":"short","waist":"standard","hem":"clean"},"surface":{"primary":"unified_a_line_mass","support":"none","accent":"none"},"paletteStory":"sage_tan","runtimeStatus":"EXPERIMENTAL"},
        {"formatVersion":"4.6B","id":"v46b-skirt-02","name":"Heather Pleat Skirt","description":"A medium pleated skirt with a contrast waist, controlled fold rhythm, and layered hem finish.","articleType":"SKIRT","rarity":"Rare","construction":{"silhouette":"pleated","length":"medium","waist":"contrast","hem":"layered"},"surface":{"primary":"pleat_rhythm","support":"contrast_waist","accent":"layered_hem"},"paletteStory":"burgundy_cream","runtimeStatus":"EXPERIMENTAL"}
    ]
    for recipe in recipes:
        errors = validate_v46b_recipe(recipe)
        if errors: raise ValueError(f"{recipe['id']}: {'; '.join(errors)}")
    return copy.deepcopy(recipes)


def validate_v46b_recipe(recipe: dict) -> tuple[str, ...]:
    grammar=load_grammar(); errors=[]
    if recipe.get("formatVersion")!="4.6B": errors.append("formatVersion must be 4.6B")
    article=recipe.get("articleType")
    if article not in grammar["articles"]: errors.append("unsupported lower-body article")
    else:
        fields=grammar["articles"][article]["fields"]
        construction=recipe.get("construction",{})
        if set(construction)!=set(fields): errors.append("article construction fields are incomplete")
        for key,values in fields.items():
            if construction.get(key) not in values: errors.append(f"invalid {article} {key}")
    rarity=recipe.get("rarity")
    if rarity not in grammar["rarity"]: errors.append("unsupported rarity")
    surface=recipe.get("surface",{})
    if set(surface)!={"primary","support","accent"}: errors.append("surface plan is incomplete")
    elif rarity=="Common" and (surface["support"]!="none" or surface["accent"]!="none"): errors.append("Common exceeds diagnostic surface budget")
    elif rarity=="Uncommon" and surface["support"]=="none": errors.append("Uncommon misses support construction")
    elif rarity=="Rare" and (surface["support"]=="none" or surface["accent"]=="none"): errors.append("Rare misses support/accent construction")
    if recipe.get("runtimeStatus")!="EXPERIMENTAL": errors.append("manual runtime evidence is required for promotion")
    raw=json.dumps(recipe)
    if any(token in raw for token in ('"x"','"y"','coordinate','pixelX','pixelY')): errors.append("recipe contains renderer coordinates")
    return tuple(errors)
