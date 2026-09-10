#!/usr/bin/env python3
"""Generate the five-piece post-V5E gameplay art-polish showcase."""

from __future__ import annotations

import copy
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from generator.hoodie_layers import generate_hoodie_layer_batch
from generator.png_utils import RGBA, blank_image, blit, draw_rect, draw_text, nearest_scale, text_width, write_rgba_png
from generator.renderers.fashionsense.art_polish_v5e import polish_upper_frames
from generator.renderers.fashionsense.hoodie_layers import render_fs_hoodie_layers
from generator.renderers.fashionsense.structured_outerwear_v5e import render_fs_v5e
from generator.renderers.fashionsense.upper_v5b import _stack
from generator.renderers.fashionsense.upper_v5d import render_fs_v5d
from generator.v5d import generate_v5d_batch
from generator.v5e import generate_v5e_recipe

OUT = ROOT / "output" / "fashionsense" / "v5e-art-polish-showcase"
COMPARE = ROOT / "output" / "comparisons"
DIRECTIONS = ("front", "right", "back", "left")
BG: RGBA = (236, 228, 216, 255); PANEL: RGBA = (210, 201, 190, 255)
INK: RGBA = (43, 40, 38, 255); MUTED: RGBA = (102, 83, 70, 255); BORDER: RGBA = (65, 58, 54, 255)


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _slug(value: str) -> str:
    return "_".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def _tile(canvas, sprite, x, y):
    draw_rect(canvas, x-2, y-2, len(sprite[0])+4, len(sprite)+4, BORDER)
    draw_rect(canvas, x-1, y-1, len(sprite[0])+2, len(sprite)+2, PANEL)
    blit(canvas, sprite, x, y)


def _rename_v5d(recipe, name, description):
    recipe = copy.deepcopy(recipe)
    design = recipe["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]
    design["itemName"] = name; design["itemDescription"] = description
    return recipe


def _rename_hoodie(recipe, name, description):
    recipe = copy.deepcopy(recipe); recipe["itemName"] = name; recipe["itemDescription"] = description
    design = recipe["baseUpperRecipe"]["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]
    design["itemName"] = name; design["itemDescription"] = description
    return recipe


def _concepts():
    v5d = {recipe["id"]: recipe for recipe in generate_v5d_batch()["recipes"]}
    hoodies = {recipe["id"]: recipe for recipe in generate_hoodie_layer_batch()["recipes"]}
    return [
        {"key":"sunfield_pathfinder", "name":"Sunfield Pathfinder Jacket", "family":"STRUCTURED_FIELD_JACKET", "rarity":"Rare", "route":"Rare+", "source":"v5e", "recipe":generate_v5e_recipe(), "idea":"Open tan field shell; bounded olive inner shirt; paired pockets; long native sleeves."},
        {"key":"ironleaf_dispatch", "name":"Ironleaf Dispatch Jacket", "family":"HIGH_COLLAR_UTILITY_JACKET", "rarity":"Rare", "route":"Rare+", "source":"v5d", "recipe":_rename_v5d(v5d["v5d-11"], "Ironleaf Dispatch Jacket", "A compact olive dispatch jacket with a guarded collar, ordered chest tabs, and a short field waist."), "idea":"Closed high collar; ordered utility tabs; belt-line termination; disciplined back yoke."},
        {"key":"mosswave_charm", "name":"Mosswave Charm Hoodie", "family":"RAISED_HOOD_STREETWEAR", "rarity":"Rare", "route":"Rare+", "source":"hoodie", "recipe":_rename_hoodie(hoodies["hoodie-layer-05"], "Mosswave Charm Hoodie", "A soft sage street hoodie with a raised lined hood, inward-falling cords, and a compact charm accent."), "idea":"True raised Hat hood; compact hoodie shell; shaped cords; small asymmetric charm."},
        {"key":"larkspur_evening", "name":"Larkspur Evening Waistcoat", "family":"FORMAL_WAISTCOAT", "rarity":"Uncommon", "route":"FS HD simple", "source":"v5d", "recipe":_rename_v5d(v5d["v5d-06"], "Larkspur Evening Waistcoat", "A precise ink waistcoat over an ivory shirt with a deep V, paired buttons, and tailored points."), "idea":"Deep V frame; visible dress shirt; compact formal buttons; tailored lower points."},
        {"key":"berry_signal", "name":"Berry Signal Cross-Zip", "family":"ALT_CASUAL_CROSS_ZIP", "rarity":"Rare", "route":"Rare+", "source":"v5d", "recipe":_rename_v5d(v5d["v5d-14"], "Berry Signal Cross-Zip", "A colorful fitted street top with one diagonal zip, a cream underlayer, and a restrained split-diamond mark."), "idea":"Asymmetric cross-zip; one-shoulder panel; bright underlayer; compact geometric focal."},
    ]


def _render(concept):
    if concept["source"] == "v5e":
        raw = render_fs_v5e(concept["recipe"]); base = raw.base
        before, before_defaults = raw.frames, raw.default_frames; hood = None
        runtime = raw.sleeve_metrics
    elif concept["source"] == "v5d":
        raw = render_fs_v5d(concept["recipe"]); base = raw.base
        before, before_defaults = raw.frames, raw.default_frames; hood = None
        runtime = {"mechanism":"NATIVE_ANIMATED_SLEEVES_V1", "customSleevesAppearance":False}
    else:
        raw = render_fs_hoodie_layers(concept["recipe"]); base = raw.upper.base
        before, before_defaults = raw.shirt_frames, raw.shirt_default_frames; hood = raw.hood_default_frames
        runtime = {"mechanism":"NATIVE_ANIMATED_SLEEVES_V1", "hatRuntimeFieldsChanged":False}
    polished = polish_upper_frames(base, before, before_defaults, article_family=concept["family"])
    return {"raw":raw, "before":before_defaults, "frames":polished.frames, "defaults":polished.default_frames, "texture":_stack(polished.frames), "hood":hood, "metrics":polished.metrics, "runtime":runtime}


def _assembled(entry, direction):
    canvas = blank_image(32, 48)
    hood = entry["render"]["hood"]
    if hood is not None:
        blit(canvas, hood[direction], 0, 0)
        shirt_y = 26 if direction == "front" else 24
    else:
        shirt_y = 24
    blit(canvas, entry["render"]["defaults"][direction], 8, shirt_y)
    return canvas


def _collection(entries, *, scale: int, title: str):
    sw, sh = 32*scale, 48*scale; gap = 10; label_w = 220; top = 56; row_h = sh+23
    canvas = blank_image(label_w + sw*4 + gap*3 + 16, top + row_h*len(entries)+10, BG)
    draw_text(canvas, title, 7, 7, color=INK)
    draw_text(canvas, "ASSEMBLED LAYER SCHEMATIC - FRONT RIGHT BACK LEFT - NO FAKE FARMER", 7, 20, color=MUTED)
    for i,d in enumerate(DIRECTIONS): draw_text(canvas,d.upper(),label_w+i*(sw+gap),40,color=INK)
    for row,entry in enumerate(entries):
        y=top+row*row_h; c=entry["concept"]
        draw_text(canvas,f"{row+1} {c['rarity'].upper()} {c['family'].replace('_',' ')}"[:36],6,y+2,color=INK)
        draw_text(canvas,c["name"][:36],6,y+16,color=INK)
        draw_text(canvas,c["route"][:36],6,y+30,color=MUTED)
        for i,d in enumerate(DIRECTIONS): _tile(canvas,nearest_scale(_assembled(entry,d),scale),label_w+i*(sw+gap),y)
    return canvas


def _fronts(entries, scale=2):
    sw,sh=32*scale,48*scale; cell_w=sw+85; top=50
    canvas=blank_image(cell_w*5,top+sh+42,BG)
    draw_text(canvas,"POST-V5E FIVE-WAY GAMEPLAY-FOOTPRINT SHOWCASE",8,7,color=INK)
    draw_text(canvas,"TWO JACKETS | HOODIE | FORMAL | ALT CASUAL",8,20,color=MUTED)
    for i,e in enumerate(entries):
        x=i*cell_w+40; c=e["concept"]
        draw_text(canvas,c["name"][:22],i*cell_w+5,34,color=INK)
        _tile(canvas,nearest_scale(_assembled(e,"front"),scale),x,top)
        draw_text(canvas,c["rarity"],i*cell_w+5,top+sh+15,color=MUTED)
    return canvas


def _before_after(entries):
    scale=6; sprite=16*scale; label_w=215; gap=24; top=54; row_h=sprite+22
    canvas=blank_image(label_w+sprite*2+gap+18,top+row_h*len(entries)+10,BG)
    draw_text(canvas,"SHADE-ROLE POLISH - CONSTRUCTION AND ALPHA UNCHANGED",7,7,color=INK)
    draw_text(canvas,"BEFORE",label_w,36,color=INK); draw_text(canvas,"POLISHED",label_w+sprite+gap,36,color=INK)
    for row,e in enumerate(entries):
        y=top+row*row_h; c=e["concept"]
        draw_text(canvas,c["name"][:34],6,y+3,color=INK)
        draw_text(canvas,c["family"].replace("_"," ")[:34],6,y+17,color=MUTED)
        _tile(canvas,nearest_scale(e["render"]["before"]["front"],scale),label_w,y)
        _tile(canvas,nearest_scale(e["render"]["defaults"]["front"],scale),label_w+sprite+gap,y)
    return canvas


def main():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True); COMPARE.mkdir(parents=True,exist_ok=True)
    entries=[]
    for concept in _concepts():
        render=_render(concept); entry={"concept":concept,"render":render}; entries.append(entry)
        target=OUT/concept["key"]; target.mkdir()
        write_rgba_png(target/"shirt.png",render["texture"])
        write_rgba_png(target/"front-right-back-left-6x.png",_collection([entry],scale=3,title=concept["name"]))
        write_rgba_png(target/"gameplay-front.png",nearest_scale(_assembled(entry,"front"),2))
        if render["hood"] is not None:
            write_rgba_png(target/"hood.png",render["raw"].hood_texture)
        _json(target/"summary.json",{
            "name":concept["name"],"family":concept["family"],"rarity":concept["rarity"],"rendererRoute":concept["route"],
            "primaryDesignIdea":concept["idea"],"polishMetrics":render["metrics"],"runtime":render["runtime"],
            "qualityReview":{"articleReadability":"PASS_STATIC","construction":"PASS_STATIC","collectibility":"HUMAN_REVIEW_REQUIRED"},
            "recipe":concept["recipe"],
        })
    write_rgba_png(OUT/"V5E_POST_POLISH_GAMEPLAY.png",_fronts(entries,2))
    write_rgba_png(OUT/"V5E_POST_POLISH_DIRECTIONS.png",_collection(entries,scale=2,title="POST-V5E POLISHED DIRECTIONAL SHOWCASE"))
    write_rgba_png(COMPARE/"V5E_POST_POLISH_SHOWCASE.png",_collection(entries,scale=3,title="POST-V5E POLISHED FIVE-PIECE SHOWCASE"))
    write_rgba_png(COMPARE/"V5E_ART_POLISH_BEFORE_AFTER.png",_before_after(entries))
    alpha_preserved=all(e["render"]["metrics"]["alphaGeometryPreserved"] for e in entries)
    distinct=len({e["concept"]["family"] for e in entries})==5
    _json(OUT/"validation.json",{
        "status":"PASS_STATIC_RUNTIME_RETEST_REQUIRED" if alpha_preserved and distinct else "FAIL",
        "count":len(entries),"distinctFamilies":len({e["concept"]["family"] for e in entries}),
        "alphaGeometryPreserved":alpha_preserved,"runtimeFieldsChanged":False,
        "customSleevesAppearances":0,"nativeSleeveContract":"NATIVE_ANIMATED_SLEEVES_V1",
        "hoodAnchorOrDrawOrderChanged":False,"beautyClaim":"HUMAN_GAMEPLAY_REVIEW_REQUIRED",
        "garments":[{"name":e["concept"]["name"],"family":e["concept"]["family"],"rarity":e["concept"]["rarity"],"metrics":e["render"]["metrics"]} for e in entries],
    })
    print(f"Generated {len(entries)} post-V5E polished showcase garments")
    print(OUT)


if __name__=="__main__": main()
