#!/usr/bin/env python3
"""Generate the fixed-seed V4.2 three-family directional shape proof."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from generator.hybrid_v3.builder import CanonicalGarmentBuilder
from generator.hybrid_v3.projector import DirectionalProjector
from generator.hybrid_v3.compiler.pixel_grammar_v4 import PixelGrammarCompilerV4,V42_PROOF_PROFILE,V42_SHAPE_LIBRARY_VERSION
from generator.png_utils import blank_image,blit,draw_rect,draw_text,nearest_scale,read_rgba_png,write_rgba_png
from generator.renderers.fashionsense.upper_v5b import _stack
from tools.generate_controlled_grammar_hd_adapter_repair import FARMER,HAIR,_farmer_composite

OUT=ROOT/"output/v4-shape-proof"
DIRECTIONS=("front","right","back","left")
CASES=(
    {"label":"Polo","family":"POLO_SHIRT","intent":"POLO_CLASSIC","fit":"MASC_TAILORED","seed":420201,"palette":"COASTAL_MIST"},
    {"label":"Sweater Vest","family":"SWEATER_VEST","intent":"VEST_ACADEMIC","fit":"MASC_TAILORED","seed":420203,"palette":"CREAM_ACADEMIC"},
    {"label":"Sailor Top","family":"SAILOR_TOP","intent":"SAILOR_DECK_CLASSIC","fit":"UNISEX_REGULAR","seed":420205,"palette":"SAILOR_NAVY"},
)
EXPECTED_VARIANTS={
    "POLO_SHIRT":{"FOLDED_POLO_COLLAR_FRONT_V1","FOLDED_POLO_COLLAR_SIDE_V1","FOLDED_POLO_COLLAR_BACK_V1","SHORT_POLO_PLACKET_FRONT_V1"},
    "SWEATER_VEST":{"V_BINDING_FRONT_V1","V_BINDING_SIDE_V1","V_BINDING_BACK_V1","CUTIN_ARMHOLE_SIDE_V1","INNER_SHIRT_EXPOSURE_SIDE_V1","KNIT_HEM_TERMINATION_V1"},
    "SAILOR_TOP":{"SAILOR_COLLAR_FRONT_V1","SAILOR_COLLAR_SIDE_V1","SAILOR_REAR_PANEL_V1","SAILOR_FRONT_OPENING_OR_INSERT_V1"},
}
EXPECTED_TOPOLOGY={
    "POLO_SHIRT":{("ADD","right",12,1),("ADD","left",3,1)},
    "SWEATER_VEST":{("REMOVE","right",13,2),("REMOVE","right",13,3),("REMOVE","left",2,2),("REMOVE","left",2,3)},
    "SAILOR_TOP":{("ADD","right",14,2),("ADD","left",1,2)},
}
BG=(232,226,217,255); PANEL=(205,197,186,255); INK=(39,37,36,255); ACC=(46,116,125,255); RED=(190,67,57,255); GREEN=(55,146,89,255)


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


def slug(value): return "-".join(re.sub(r"[^a-z0-9]+"," ",value.lower()).split())


def tile(canvas,image,x,y,border=ACC):
    draw_rect(canvas,x-2,y-2,len(image[0])+4,len(image)+4,border)
    draw_rect(canvas,x-1,y-1,len(image[0])+2,len(image)+2,PANEL)
    blit(canvas,image,x,y)


def isolated_sheet(items):
    canvas=blank_image(760,32+3*160,BG); draw_text(canvas,"V4.2 ROUTING FIXED | ACTUAL SHAPE GRAMMAR | ISOLATED 8X",8,7,color=INK)
    for row,item in enumerate(items):
        y=32+row*160; draw_text(canvas,item["case"]["label"].upper(),8,y+52,color=INK)
        for col,direction in enumerate(DIRECTIONS):
            x=220+col*134; draw_text(canvas,direction.upper(),x,y,color=ACC)
            tile(canvas,nearest_scale(item["render"].frames[direction],8),x,y+20)
    return canvas


def farmer_sheet(items):
    scale=2; card_w=4*138+12; card_h=294
    canvas=blank_image(card_w,32+3*card_h,BG); draw_text(canvas,"V4.2 ROUTING FIXED | FARMER FRONT / RIGHT / BACK / LEFT | HUMAN VISUAL QC PENDING",8,7,color=INK)
    for row,item in enumerate(items):
        y0=32+row*card_h; draw_text(canvas,item["case"]["label"].upper(),8,y0,color=INK)
        for col,direction in enumerate(DIRECTIONS):
            x=8+col*138; draw_text(canvas,direction.upper(),x,y0+13,color=ACC)
            tile(canvas,nearest_scale(item["farmers"][direction],scale),x,y0+30)
    return canvas


def before_after_sheet(items):
    size=96; gap=18; label=180; row_h=124
    canvas=blank_image(label+4*(size+gap)+8,28+6*row_h,BG)
    draw_text(canvas,"CURRENT V4.1  ->  NEW V4.2 | FIXED SEEDS | FRONT RIGHT BACK LEFT",8,7,color=INK)
    for index,item in enumerate(items):
        for phase,render in (("V4.1",item["baseline"]),("V4.2",item["render"])):
            row=index*2+(0 if phase=="V4.1" else 1); y=28+row*row_h
            draw_text(canvas,f"{item['case']['label'].upper()} {phase}",8,y+47,color=INK if phase=="V4.1" else ACC)
            for col,direction in enumerate(DIRECTIONS):
                x=label+col*(size+gap); draw_text(canvas,direction.upper(),x,y,color=ACC)
                tile(canvas,nearest_scale(render.frames[direction],6),x,y+16,INK if phase=="V4.1" else ACC)
    return canvas


def topology_frame(render,direction):
    frame=[[(0,0,0,0) for _ in range(16)] for _ in range(16)]
    for y,row in enumerate(render.frames[direction]):
        for x,pixel in enumerate(row):
            if pixel[3]: frame[y][x]=(112,112,112,110)
    for op in render.topology_map:
        if op["direction"]!=direction: continue
        x,y=op["cell"]; frame[y][x]=GREEN if op["op"]=="ADD" else RED
    return frame


def direction_sheet(title,frames,scale=8):
    canvas=blank_image(4*134+16,164,BG); draw_text(canvas,title,8,7,color=INK)
    for col,direction in enumerate(DIRECTIONS):
        x=8+col*134; draw_text(canvas,direction.upper(),x,20,color=ACC); tile(canvas,nearest_scale(frames[direction],scale),x,34)
    return canvas


def save_item(item):
    case=item["case"]; render=item["render"]; target=OUT/slug(case["label"]); target.mkdir(parents=True,exist_ok=True)
    dump(target/"canonical-model.json",render.canonical)
    dump(target/"projections.json",render.projections)
    dump(target/"topology-map.json",{"schemaVersion":"4.2.0","operations":render.topology_map,"visualChangeContract":render.validation["visualChangeContract"]})
    dump(target/"ownership-ledger.json",render.semantic_regions["ownership"])
    dump(target/"semantic-regions.json",{k:v for k,v in render.semantic_regions.items() if k!="ownership"})
    dump(target/"pre-polish-frame.json",render.pre_polish_frames)
    dump(target/"post-polish-merge-result.json",render.post_polish_frames)
    dump(target/"final-logical-frames.json",render.frames)
    dump(target/"validation.json",render.validation)
    dump(target/"metrics.json",render.metrics)
    dump(target/"routing-trace.json",render.metrics["routing"])
    dump(target/"stage-trace.json",{"stages":render.stage_trace,"ownershipConflicts":render.semantic_regions["ownership"]["conflicts"],"rejectedMutations":render.semantic_regions["ownership"]["rejectedMutations"],"automatedQC":render.validation["automatedQC"],"humanVisualQC":"PENDING"})
    write_rgba_png(target/"pre-polish-frame.png",_stack(render.pre_polish_frames))
    write_rgba_png(target/"post-polish-merge-result.png",_stack(render.post_polish_frames))
    write_rgba_png(target/"final-logical-atlas.png",render.texture)
    write_rgba_png(target/"topology-map.png",direction_sheet(case["label"].upper()+" | GREEN ADD / RED REMOVE",{d:topology_frame(render,d) for d in DIRECTIONS}))
    write_rgba_png(target/"farmer-composites.png",direction_sheet(case["label"].upper()+" | FARMER COMPOSITES",item["farmers"],scale=1))
    for direction,image in item["farmers"].items(): write_rgba_png(target/f"farmer-{direction}.png",image)


def main():
    if not FARMER.exists() or not HAIR.exists(): raise FileNotFoundError("unpacked Farmer and hairstyles fixtures are required")
    OUT.mkdir(parents=True,exist_ok=True); body=read_rgba_png(FARMER)["pixels"]; hair=read_rgba_png(HAIR)["pixels"]
    builder=CanonicalGarmentBuilder(); projector=DirectionalProjector(); compiler=PixelGrammarCompilerV4(execution_profile=V42_PROOF_PROFILE)
    items=[]
    for case in CASES:
        canonical=builder.build(family=case["family"],design_intent=case["intent"],fit_profile=case["fit"],root_seed=case["seed"],rarity_budget="V4_2_SHAPE_PROOF")
        projections=projector.project(canonical)
        render=compiler.compile(canonical,projections,palette_story=case["palette"],required_shape_library_version=V42_SHAPE_LIBRARY_VERSION)
        farmers={d:_farmer_composite(body,hair,render.frames[d],d) for d in DIRECTIONS}
        items.append({"case":case,"render":render,"farmers":farmers})
    # Fail closed before writing any claimed routing-fixed artifacts.
    for item in items:
        case=item["case"]; render=item["render"]; family=case["family"]
        actual_variants=set(render.metrics["shapeVariants"])
        actual_topology={(op["op"],op["direction"],op["cell"][0],op["cell"][1]) for op in render.topology_map}
        if render.metrics["shapeLibraryVersion"] != V42_SHAPE_LIBRARY_VERSION:
            raise RuntimeError(f"{family}: V4.2 routing failed: {render.metrics['shapeLibraryVersion']}")
        if set(render.metrics["expectedShapeVariants"]) != EXPECTED_VARIANTS[family] or actual_variants != EXPECTED_VARIANTS[family]:
            raise RuntimeError(f"{family}: V4.2 variant routing failed: expected={sorted(EXPECTED_VARIANTS[family])} actual={sorted(actual_variants)}")
        if actual_topology != EXPECTED_TOPOLOGY[family]:
            raise RuntimeError(f"{family}: V4.2 topology routing failed: expected={sorted(EXPECTED_TOPOLOGY[family])} actual={sorted(actual_topology)}")
        if render.validation["status"] != "PASS":
            raise RuntimeError(f"{family}: V4.2 validation failed: {render.validation['issues']}")
    for item in items: save_item(item)
    write_rgba_png(OUT/"V4_2_ROUTING_FIXED_FARMER.png",farmer_sheet(items))
    write_rgba_png(OUT/"V4_2_ROUTING_FIXED_ISOLATED_8X.png",isolated_sheet(items))
    summary={"schemaVersion":"4.2.0-shape-proof","fixedCases":list(CASES),"garments":[{"family":x["case"]["family"],"seed":x["case"]["seed"],"automatedQC":x["render"].validation["automatedQC"],"humanVisualQC":"PENDING","topologyOperations":x["render"].topology_map,"shapeVariants":x["render"].metrics["shapeVariants"]} for x in items],"status":{"automatedQC":"PASS" if all(x["render"].validation["status"]=="PASS" for x in items) else "FAIL","humanVisualQC":"PENDING"}}
    dump(OUT/"proof-summary.json",summary)
    print(json.dumps(summary["status"],indent=2))


if __name__=="__main__": main()
