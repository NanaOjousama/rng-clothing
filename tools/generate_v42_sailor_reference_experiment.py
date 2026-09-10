#!/usr/bin/env python3
"""One fixed-seed current-vs-technical Sailor architecture experiment."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from generator.hybrid_v3.builder import CanonicalGarmentBuilder
from generator.hybrid_v3.projector import DirectionalProjector
from generator.hybrid_v3.compiler.pixel_grammar_v4 import (
    PixelGrammarCompilerV4,V42_PROOF_PROFILE,V42_SAILOR_TECHNICAL_PROFILE,V42_SHAPE_LIBRARY_VERSION,
)
from generator.png_utils import blank_image,blit,draw_rect,draw_text,nearest_scale,read_rgba_png,write_rgba_png
from tools.generate_controlled_grammar_hd_adapter_repair import FARMER,HAIR,_farmer_composite

OUT=ROOT/"output/v4-sailor-reference-experiment"
DIRECTIONS=("front","right","back","left")
CASE={"family":"SAILOR_TOP","intent":"SAILOR_DECK_CLASSIC","fit":"UNISEX_REGULAR","seed":420205,"palette":"SAILOR_NAVY","material":"WOVEN_SHIRT"}
CURRENT_VARIANTS={"SAILOR_COLLAR_FRONT_V1","SAILOR_COLLAR_SIDE_V1","SAILOR_REAR_PANEL_V1","SAILOR_FRONT_OPENING_OR_INSERT_V1"}
TECHNICAL_VARIANTS={"SAILOR_COLLAR_FRONT_TECHNICAL_V1","SAILOR_COLLAR_SIDE_TECHNICAL_V1","SAILOR_REAR_FLAP_TECHNICAL_V1","SAILOR_COLLAR_BORDER_TECHNICAL_V1","SAILOR_FRONT_OPENING_OR_INSERT_V1"}
CURRENT_TOPOLOGY={("ADD","right",14,2),("ADD","left",1,2)}
TECHNICAL_TOPOLOGY={("ADD","right",12,1),("ADD","left",3,1)}
BG=(232,226,217,255); PANEL=(205,197,186,255); INK=(39,37,36,255); ACC=(46,116,125,255)


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def tile(canvas,image,x,y,border=ACC):
    draw_rect(canvas,x-2,y-2,len(image[0])+4,len(image)+4,border)
    draw_rect(canvas,x-1,y-1,len(image[0])+2,len(image)+2,PANEL)
    blit(canvas,image,x,y)


def comparison_sheet(title,current,technical,*,farmer=False):
    scale=2 if farmer else 8; sprite_w=(64 if farmer else 16)*scale; sprite_h=(128 if farmer else 16)*scale
    label=175; gap=18; top=35; row_h=sprite_h+35
    canvas=blank_image(label+4*(sprite_w+gap),top+2*row_h+8,BG); draw_text(canvas,title,8,7,color=INK)
    for row,(name,frames) in enumerate((("CURRENT V4.2 SAILOR",current),("TECHNICAL REFERENCE",technical))):
        y=top+row*row_h; draw_text(canvas,name,8,y+sprite_h//2,color=INK if row==0 else ACC)
        for col,direction in enumerate(DIRECTIONS):
            x=label+col*(sprite_w+gap); draw_text(canvas,direction.upper(),x,y,color=ACC)
            tile(canvas,nearest_scale(frames[direction],scale),x,y+16,INK if row==0 else ACC)
    return canvas


def architecture_overlay(render):
    colors={"body":(108,108,108,110),"collar":(66,137,201,255),"rear_panel":(64,158,108,255),"collar_border":(229,174,55,255),"inner_layer":(188,76,103,255)}
    overlays={}
    for direction in DIRECTIONS:
        frame=[[(0,0,0,0) for _ in range(16)] for _ in range(16)]
        for y,row in enumerate(render.frames[direction]):
            for x,pixel in enumerate(row):
                if pixel[3]: frame[y][x]=colors["body"]
        for system in ("collar","rear_panel","collar_border","inner_layer"):
            for x,y in render.semantic_regions["systems"][system][direction]: frame[y][x]=colors[system]
        overlays[direction]=frame
    anchors={"front":(8,1),"right":(12,1),"back":(8,1),"left":(3,1)}
    labels={
        "front":("COLLAR + BORDER","NECK + INSERT"),
        "right":("COLLAR DEPTH","REAR HANDOFF"),
        "back":("NECK + FLAP","BORDER + LOWER EDGE"),
        "left":("COLLAR DEPTH","REAR HANDOFF"),
    }
    scale=8; size=128; gap=18; canvas=blank_image(4*(size+gap)+12,214,BG)
    draw_text(canvas,"SAILOR TECHNICAL ARCHITECTURE OVERLAY",8,7,color=INK)
    draw_text(canvas,"BLUE COLLAR  GREEN REAR FLAP  GOLD BORDER  RED INSERT  PINK ANCHOR",8,19,color=INK)
    for col,direction in enumerate(DIRECTIONS):
        x=8+col*(size+gap); draw_text(canvas,direction.upper(),x,33,color=ACC)
        scaled=nearest_scale(overlays[direction],scale); tile(canvas,scaled,x,47)
        ax,ay=anchors[direction]; draw_rect(canvas,x+ax*scale+2,47+ay*scale+2,4,4,(242,74,180,255))
        draw_text(canvas,labels[direction][0],x,181,color=INK)
        draw_text(canvas,labels[direction][1],x,193,color=INK)
    return canvas


def topology_signature(render):
    return {(op["op"],op["direction"],op["cell"][0],op["cell"][1]) for op in render.topology_map}


def assert_route(name,render,expected_variants,expected_topology,profile):
    if render.validation["status"]!="PASS": raise RuntimeError(f"{name} validation failed: {render.validation['issues']}")
    if render.metrics["executionProfile"]!=profile or render.metrics["shapeLibraryVersion"]!=V42_SHAPE_LIBRARY_VERSION:
        raise RuntimeError(f"{name} compiler routing mismatch: {render.metrics['routing']}")
    if set(render.metrics["shapeVariants"])!=expected_variants or set(render.metrics["expectedShapeVariants"])!=expected_variants:
        raise RuntimeError(f"{name} variant mismatch: {render.metrics['shapeVariants']}")
    if topology_signature(render)!=expected_topology: raise RuntimeError(f"{name} topology mismatch: {render.topology_map}")


def save_render(folder,render,comparison):
    target=OUT/folder
    dump(target/"topology-map.json",{"operations":render.topology_map,"visualChangeContract":render.validation["visualChangeContract"]})
    dump(target/"ownership-ledger.json",render.semantic_regions["ownership"])
    dump(target/"semantic-regions.json",{k:v for k,v in render.semantic_regions.items() if k!="ownership"})
    dump(target/"metrics.json",{**render.metrics,"controlledExperiment":comparison})
    dump(target/"validation.json",render.validation)
    dump(target/"stage-trace.json",{"stages":render.stage_trace,"rejectedMutations":render.semantic_regions["ownership"]["rejectedMutations"],"automatedQC":render.validation["automatedQC"],"humanVisualQC":"PENDING"})
    write_rgba_png(target/"final-logical-atlas.png",render.texture)


def main():
    if not FARMER.exists() or not HAIR.exists(): raise FileNotFoundError("unpacked Farmer fixtures are required")
    OUT.mkdir(parents=True,exist_ok=True)
    canonical=CanonicalGarmentBuilder().build(family=CASE["family"],design_intent=CASE["intent"],fit_profile=CASE["fit"],root_seed=CASE["seed"],rarity_budget="V4_2_SAILOR_REFERENCE_EXPERIMENT",material=CASE["material"])
    projections=DirectionalProjector().project(canonical)
    current=PixelGrammarCompilerV4(execution_profile=V42_PROOF_PROFILE).compile(canonical,projections,palette_story=CASE["palette"],required_shape_library_version=V42_SHAPE_LIBRARY_VERSION,expected_shape_variants=CURRENT_VARIANTS)
    technical=PixelGrammarCompilerV4(execution_profile=V42_SAILOR_TECHNICAL_PROFILE).compile(canonical,projections,palette_story=CASE["palette"],required_shape_library_version=V42_SHAPE_LIBRARY_VERSION,expected_shape_variants=TECHNICAL_VARIANTS)
    assert_route("current",current,CURRENT_VARIANTS,CURRENT_TOPOLOGY,V42_PROOF_PROFILE)
    assert_route("technical",technical,TECHNICAL_VARIANTS,TECHNICAL_TOPOLOGY,V42_SAILOR_TECHNICAL_PROFILE)
    body=read_rgba_png(FARMER)["pixels"]; hair=read_rgba_png(HAIR)["pixels"]
    current_farmer={d:_farmer_composite(body,hair,current.frames[d],d) for d in DIRECTIONS}
    technical_farmer={d:_farmer_composite(body,hair,technical.frames[d],d) for d in DIRECTIONS}
    comparison={"sameCanonicalDigest":digest(current.canonical)==digest(technical.canonical),"sameProjectionDigest":digest(current.projections)==digest(technical.projections),"sameSeed":CASE["seed"],"sameFit":CASE["fit"],"sameMaterial":canonical["material"]["id"],"samePaletteStory":CASE["palette"],"sameSleeveColors":current.sleeve_colors==technical.sleeve_colors,"onlyExecutionProfileDiffers":True,"humanVisualQC":"PENDING"}
    dump(OUT/"canonical-model.json",canonical); dump(OUT/"projections.json",projections); dump(OUT/"experiment-contract.json",comparison)
    architecture=json.loads((ROOT/"specs/garment_grammar_v4/architecture_grammar_v4.json").read_text())["familyArchitectures"]["SAILOR_TOP"]
    dump(OUT/"sailor-architecture.json",architecture)
    save_render("current-v4.2",current,comparison); save_render("technical-refined",technical,comparison)
    write_rgba_png(OUT/"SAILOR_REFERENCE_BEFORE_AFTER_FARMER.png",comparison_sheet("SAILOR REFERENCE EXPERIMENT | SAME SEED / FIT / MATERIAL / PALETTE | HUMAN QC PENDING",current_farmer,technical_farmer,farmer=True))
    write_rgba_png(OUT/"SAILOR_REFERENCE_BEFORE_AFTER_ISOLATED_8X.png",comparison_sheet("SAILOR REFERENCE EXPERIMENT | CURRENT V4.2 VS TECHNICAL GRAMMAR | 8X",current.frames,technical.frames))
    write_rgba_png(OUT/"SAILOR_REFERENCE_ARCHITECTURE_OVERLAY.png",architecture_overlay(technical))
    dump(OUT/"experiment-summary.json",{"case":CASE,"current":{"variants":current.metrics["shapeVariants"],"topology":current.topology_map,"automatedQC":current.validation["automatedQC"]},"technical":{"variants":technical.metrics["shapeVariants"],"topology":technical.topology_map,"automatedQC":technical.validation["automatedQC"]},"humanVisualQC":"PENDING"})
    print(json.dumps({"currentAutomatedQC":current.validation["automatedQC"],"technicalAutomatedQC":technical.validation["automatedQC"],"humanVisualQC":"PENDING"},indent=2))


if __name__=="__main__": main()
