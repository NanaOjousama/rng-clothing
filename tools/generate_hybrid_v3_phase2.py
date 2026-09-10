#!/usr/bin/env python3
"""Generate the bounded eight-garment Hybrid V3 Phase 2 proof."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from generator.hybrid_v3.builder import CanonicalGarmentBuilder
from generator.hybrid_v3.compiler import PixelGrammarCompiler
from generator.hybrid_v3.compiler.stage_trace import verify_frozen_backend
from generator.hybrid_v3.config import HYBRID_GARMENT_COMPILER_V3_ENABLED
from generator.hybrid_v3.projector import DirectionalProjector
from generator.hybrid_v3.semantic_flat import emit_semantic_flat
from generator.png_utils import blank_image, blit, draw_rect, draw_text, nearest_scale, read_rgba_png, write_rgba_png
from tools.generate_controlled_grammar_hd_adapter_repair import _farmer_composite

OUT = ROOT / "output/hybrid-v3-phase2"
PACK = ROOT / "test-packs/fashionsense/RNG-Clothing-Hybrid-V3-Phase2"
COMPARE = ROOT / "output/comparisons"
UNIQUE_ID = "RNGClothing.FashionSense.HybridV3Phase2"
DIRECTIONS = ("front", "right", "back", "left")
MODEL_ORDER = (("FrontShirt",0),("RightShirt",16),("LeftShirt",32),("BackShirt",48))
FARMER = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/farmer_base.png")
HAIR = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/hairstyles.png")
BG=(232,226,217,255); PANEL=(205,197,186,255); INK=(39,37,36,255); BORDER=(67,61,57,255); ACC=(46,116,125,255); WHITE=(244,243,238,255)

CASES = (
    {"id":"01-orchard-essential-tee","name":"Orchard Essential Tee","family":"T_SHIRT","intent":"TEE_CLEAN_ESSENTIAL","fit":"UNISEX_REGULAR","seed":320201,"palette":"SPRING_ORCHARD"},
    {"id":"02-rosewater-weekend-tee","name":"Rosewater Weekend Tee","family":"T_SHIRT","intent":"TEE_RELAXED_WEEKEND","fit":"UNISEX_BOXY","seed":320202,"palette":"ROSEWOOD_PASTEL"},
    {"id":"03-coastal-knit-polo","name":"Coastal Knit Polo","family":"POLO_SHIRT","intent":"POLO_CLASSIC","fit":"MASC_TAILORED","seed":320203,"palette":"COASTAL_MIST"},
    {"id":"04-seaglass-sport-polo","name":"Sea Glass Sport Polo","family":"POLO_SHIRT","intent":"POLO_COASTAL_SPORT","fit":"UNISEX_BOXY","seed":320204,"palette":"SEA_GLASS"},
    {"id":"05-ivory-academic-vest","name":"Ivory Academic Vest","family":"SWEATER_VEST","intent":"VEST_ACADEMIC","fit":"MASC_TAILORED","seed":320205,"palette":"CREAM_ACADEMIC"},
    {"id":"06-lavender-relaxed-vest","name":"Lavender Relaxed Vest","family":"SWEATER_VEST","intent":"VEST_RELAXED_KNIT","fit":"FEM_RELAXED","seed":320206,"palette":"LAVENDER_DAY"},
    {"id":"07-harbor-deck-sailor","name":"Harbor Deck Sailor","family":"SAILOR_TOP","intent":"SAILOR_DECK_CLASSIC","fit":"UNISEX_REGULAR","seed":320207,"palette":"SAILOR_NAVY"},
    {"id":"08-snowberry-maritime-sailor","name":"Snowberry Maritime Sailor","family":"SAILOR_TOP","intent":"SAILOR_SOFT_MARITIME","fit":"FEM_RELAXED","seed":320208,"palette":"SNOWBERRY"},
)


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")


def tile(canvas, image, x, y, border=ACC):
    draw_rect(canvas,x-2,y-2,len(image[0])+4,len(image)+4,border); draw_rect(canvas,x-1,y-1,len(image[0])+2,len(image)+2,PANEL); blit(canvas,image,x,y)


def farmer_sheet(name, farmer):
    canvas=blank_image(300,166,BG); draw_text(canvas,name.upper(),8,7,color=INK)
    for i,d in enumerate(DIRECTIONS):
        x=8+i*72; draw_text(canvas,d.upper(),x,20,color=ACC); tile(canvas,farmer[d],x,34)
    return canvas


def isolated_sheet(name, frames):
    canvas=blank_image(548,166,BG); draw_text(canvas,name.upper(),8,7,color=INK)
    for i,d in enumerate(DIRECTIONS):
        x=8+i*134; draw_text(canvas,d.upper(),x,20,color=ACC); tile(canvas,nearest_scale(frames[d],8),x,34)
    return canvas


def alpha_image(frame, scale=8):
    logical=[[(25,25,25,255) if p[3] else (245,245,242,255) for p in row] for row in frame]
    return nearest_scale(logical,scale)


def all_fronts(items):
    canvas=blank_image(8*76+16,174,BG); draw_text(canvas,"HYBRID V3 PHASE 2 | ALL FARMER FRONTS",8,7,color=INK)
    for i,item in enumerate(items):
        x=8+i*76; tile(canvas,item["farmer"]["front"],x,28); draw_text(canvas,str(i+1),x+27,158,color=INK)
    return canvas


def all_directions(items):
    canvas=blank_image(4*72+220,8*142+28,BG); draw_text(canvas,"HYBRID V3 PHASE 2 | FARMER FRONT RIGHT BACK LEFT",8,7,color=INK)
    for row,item in enumerate(items):
        y=28+row*142; draw_text(canvas,item["case"]["name"][:27],8,y+55,color=INK)
        for col,d in enumerate(DIRECTIONS): tile(canvas,item["farmer"][d],220+col*72,y)
    return canvas


def isolated_all(items):
    canvas=blank_image(4*132+230,8*134+28,BG); draw_text(canvas,"HYBRID V3 PHASE 2 | ISOLATED LOGICAL ART 8X",8,7,color=INK)
    for row,item in enumerate(items):
        y=28+row*134; draw_text(canvas,item["case"]["name"][:28],8,y+55,color=INK)
        for col,d in enumerate(DIRECTIONS): tile(canvas,nearest_scale(item["render"].frames[d],8),230+col*132,y)
    return canvas


def family_qc(items, family, title):
    family_items=[x for x in items if x["case"]["family"]==family]
    canvas=blank_image(620,2*180+28,BG); draw_text(canvas,title,8,7,color=INK)
    for row,item in enumerate(family_items):
        y=28+row*180; draw_text(canvas,item["case"]["name"],8,y,color=INK)
        focus="right" if family=="SWEATER_VEST" else "front" if family=="POLO_SHIRT" else "back"
        draw_text(canvas,"RAW 16X16",8,y+15,color=ACC); tile(canvas,nearest_scale(item["render"].frames[focus],2),8,y+31)
        draw_text(canvas,"8X",64,y+15,color=ACC); tile(canvas,nearest_scale(item["render"].frames[focus],8),64,y+31)
        draw_text(canvas,"FARMER",204,y+15,color=ACC); tile(canvas,item["farmer"][focus],204,y+31)
        if family=="SWEATER_VEST":
            draw_text(canvas,"ALPHA",278,y+15,color=ACC); tile(canvas,alpha_image(item["render"].frames[focus]),278,y+31)
            summary=item["render"].validation
            draw_text(canvas,f"COMP {len(summary['connectedComponents'][focus])}",414,y+38,color=INK)
            draw_text(canvas,f"TOP {len(summary['topRows'][focus]['unsupportedRowZeroCells'])}",414,y+52,color=INK)
            cleared=item["render"].semantic_regions["clearedByCompiler"].get("body",{}).get(focus,[])
            draw_text(canvas,f"MAP CLEAR {len(cleared)}",414,y+66,color=INK)
        elif family=="POLO_SHIRT":
            draw_text(canvas,"PLACKET: FRONT ONLY",278,y+40,color=INK); draw_text(canvas,"BACK: FORBIDDEN",278,y+55,color=INK)
        else:
            draw_text(canvas,"REAR PANEL: FULL",278,y+40,color=INK); draw_text(canvas,"FRONT PANEL: HIDDEN",278,y+55,color=INK)
    return canvas


def shirt_json(case, render):
    models={}
    for key,y in MODEL_ORDER:
        models[key]={"Scale":2.0,"HideSleeves":False,"DisableGrayscale":True,"SleeveColors":[list(x) for x in render.sleeve_colors],"StartingPosition":{"X":0,"Y":y},"BodyPosition":{"X":0,"Y":32},"ShirtSize":{"Width":16,"Length":16}}
    return {"Name":case["name"],"Format":"7.5.0","Tags":["RNG Clothing","Hybrid V3 Phase 2",case["family"],case["intent"],"Experimental"],**models}


def main():
    frozen=verify_frozen_backend()
    if frozen["status"]!="PASS": raise SystemExit("Frozen backend hash mismatch; Phase 2 aborted")
    OUT.mkdir(parents=True,exist_ok=True); COMPARE.mkdir(parents=True,exist_ok=True)
    if PACK.exists(): shutil.rmtree(PACK)
    PACK.mkdir(parents=True)
    body=read_rgba_png(FARMER)["pixels"]; hair=read_rgba_png(HAIR)["pixels"]
    builder=CanonicalGarmentBuilder(); projector=DirectionalProjector(); compiler=PixelGrammarCompiler(); items=[]
    visual_path=OUT/"visual-review.json"; visual_reviews=json.loads(visual_path.read_text()) if visual_path.exists() else {}
    for case in CASES:
        canonical=builder.build(family=case["family"],design_intent=case["intent"],fit_profile=case["fit"],root_seed=case["seed"],rarity_budget="PHASE2_NEUTRAL_DEFAULT")
        projections=projector.project(canonical); render=compiler.compile(canonical,projections,palette_story=case["palette"])
        if case["id"] in visual_reviews:
            render.validation["farmerVisualReview"]=visual_reviews[case["id"]]
            if visual_reviews[case["id"]]["status"]!="PASS": render.validation["status"]="FAIL"; render.validation["issues"].append({"code":"FARMER_VISUAL_REVIEW_FAILED","detail":visual_reviews[case["id"]]})
        target=OUT/case["id"]; target.mkdir(parents=True,exist_ok=True)
        dump(target/"canonical-model.json",canonical); dump(target/"projections.json",projections)
        emit_semantic_flat(canonical,projections,target/"semantic-flat.png")
        dump(target/"pixel-grammar-map.json",render.pixel_grammar_map); dump(target/"semantic-pixel-regions.json",render.semantic_regions)
        write_rgba_png(target/"shirt.png",render.texture)
        farmer={d:_farmer_composite(body,hair,render.frames[d],d) for d in DIRECTIONS}
        write_rgba_png(target/"farmer-directions.png",farmer_sheet(case["name"],farmer)); write_rgba_png(target/"isolated-directions-8x.png",isolated_sheet(case["name"],render.frames))
        dump(target/"validation.json",render.validation); dump(target/"stage-trace.json",{"stages":render.stage_trace,"frozenBackend":frozen,"featureFlagDefault":HYBRID_GARMENT_COMPILER_V3_ENABLED})
        folder="".join(x.title() for x in case["name"].split()); shirt_dir=PACK/"Shirts"/folder; shirt_dir.mkdir(parents=True)
        write_rgba_png(shirt_dir/"shirt.png",render.texture); dump(shirt_dir/"shirt.json",shirt_json(case,render))
        items.append({"case":case,"render":render,"farmer":farmer,"folder":folder})
    write_rgba_png(COMPARE/"HYBRID_V3_PHASE2_ALL_FARMER_FRONTS.png",all_fronts(items))
    write_rgba_png(COMPARE/"HYBRID_V3_PHASE2_ALL_DIRECTIONS.png",all_directions(items))
    write_rgba_png(COMPARE/"HYBRID_V3_PHASE2_ISOLATED_8X.png",isolated_all(items))
    write_rgba_png(COMPARE/"HYBRID_V3_PHASE2_SWEATER_VEST_SIDE_QC.png",family_qc(items,"SWEATER_VEST","SWEATER VEST SIDE GOLDEN REGRESSION QC"))
    write_rgba_png(COMPARE/"HYBRID_V3_PHASE2_POLO_QC.png",family_qc(items,"POLO_SHIRT","POLO DIRECTIONAL QC"))
    write_rgba_png(COMPARE/"HYBRID_V3_PHASE2_SAILOR_QC.png",family_qc(items,"SAILOR_TOP","SAILOR REAR-PANEL QC"))
    manifest={"Name":"RNG Clothing Hybrid V3 Phase 2","Author":"RNG Clothing Experiment","Version":"0.2.0","Description":"Eight isolated Hybrid V3 compiler proof garments using frozen V5/HD carriers.","UniqueID":UNIQUE_ID,"UpdateKeys":[],"ContentPackFor":{"UniqueID":"PeacefulEnd.FashionSense","MinimumVersion":"7.5.0"}}
    dump(PACK/"manifest.json",manifest)
    presets=[]
    for i,item in enumerate(items,1):
        presets.append({"Name":f"Hybrid V3 P2 {i:02} - {item['case']['name']}","Author":"RNG Clothing Experiment","Version":3,"AccessoryIds":["None","None","None"],"HairId":"None","HatId":"None","ShirtId":f"{UNIQUE_ID}/Shirt/{item['case']['name']}","SleevesId":"None","PantsId":"None","ShoesId":"None","BodyId":"None","AppearanceToMaskColors":{}})
    dump(PACK/"preset_outfits.json",presets)
    summary={"status":"PASS" if all(x["render"].validation["status"]=="PASS" and x["render"].validation["farmerVisualReview"]["status"]=="PASS" for x in items) else "PENDING_OR_FAIL","garmentCount":len(items),"familyCounts":{f:sum(x["case"]["family"]==f for x in items) for f in ("T_SHIRT","POLO_SHIRT","SWEATER_VEST","SAILOR_TOP")},"frozenBackend":frozen,"featureFlagDefault":HYBRID_GARMENT_COMPILER_V3_ENABLED,"garments":[{"id":x["case"]["id"],"name":x["case"]["name"],"family":x["case"]["family"],"intent":x["case"]["intent"],"fit":x["case"]["fit"],"material":x["render"].canonical["material"]["id"],"palette":x["case"]["palette"],"carrier":x["render"].carrier["id"],"status":x["render"].validation["status"],"farmerVisualReview":x["render"].validation["farmerVisualReview"]} for x in items]}
    dump(OUT/"phase2-summary.json",summary); dump(PACK/"static-validation.json",summary)
    dump(PACK/"specimen-index.json",[{"index":i+1,**x["case"],"shirtId":f"{UNIQUE_ID}/Shirt/{x['case']['name']}"} for i,x in enumerate(items)])
    (PACK/"README.md").write_text("# Hybrid V3 Phase 2 experimental pack\n\nInstall this folder in `Stardew Valley/Mods`. Use the eight `Hybrid V3 P2` Fashion Sense presets. These use native Farmer sleeves; no custom Sleeves appearance is included.\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__": main()
