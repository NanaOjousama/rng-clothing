#!/usr/bin/env python3
"""Generate the four fixed-seed V4 Vanilla-plus clothing proof cases."""
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
    PixelGrammarCompilerV4,V4_VANILLA_PLUS_LIBRARY_VERSION,V4_VANILLA_PLUS_PROFILE,
    V42_PROOF_PROFILE,V42_SAILOR_OUTLINE_PROFILE,V42_SHAPE_LIBRARY_VERSION,
)
from generator.png_utils import blank_image,blit,draw_rect,draw_text,nearest_scale,read_rgba_png,write_rgba_png
from tools.generate_controlled_grammar_hd_adapter_repair import FARMER,HAIR,_farmer_composite

OUT=ROOT/"output/v4-vanilla-plus"
DIRECTIONS=("front","right","back","left")
CASES=(
    {"slug":"polo","label":"POLO","family":"POLO_SHIRT","intent":"POLO_CLASSIC","fit":"MASC_TAILORED","seed":420201,"palette":"COASTAL_MIST"},
    {"slug":"vest","label":"SWEATER VEST","family":"SWEATER_VEST","intent":"VEST_ACADEMIC","fit":"MASC_TAILORED","seed":420203,"palette":"CREAM_ACADEMIC"},
    {"slug":"sailor","label":"SAILOR TOP","family":"SAILOR_TOP","intent":"SAILOR_DECK_CLASSIC","fit":"UNISEX_REGULAR","seed":420205,"palette":"SAILOR_NAVY","material":"WOVEN_SHIRT"},
    {"slug":"tee","label":"T-SHIRT","family":"T_SHIRT","intent":"TEE_CLEAN_ESSENTIAL","fit":"UNISEX_REGULAR","seed":420207,"palette":"SPRING_ORCHARD"},
)
CURRENT_VARIANTS={
    "POLO_SHIRT":{"FOLDED_POLO_COLLAR_FRONT_V1","FOLDED_POLO_COLLAR_SIDE_V1","FOLDED_POLO_COLLAR_BACK_V1","SHORT_POLO_PLACKET_FRONT_V1"},
    "SWEATER_VEST":{"V_BINDING_FRONT_V1","V_BINDING_SIDE_V1","V_BINDING_BACK_V1","CUTIN_ARMHOLE_SIDE_V1","INNER_SHIRT_EXPOSURE_SIDE_V1","KNIT_HEM_TERMINATION_V1"},
    "SAILOR_TOP":{"SAILOR_COLLAR_FRONT_TECHNICAL_V1","SAILOR_COLLAR_SIDE_TECHNICAL_V1","SAILOR_REAR_FLAP_TECHNICAL_V1","SAILOR_COLLAR_FLAP_OUTLINE_REFINED_V1","SAILOR_FRONT_BOW_TIE_OUTLINE_REFINED_V1"},
    "T_SHIRT":set(),
}
PLUS_VARIANTS={
    "POLO_SHIRT":{"POLO_COLLAR_VANILLA_A","POLO_PLACKET_VANILLA_A"},
    "SWEATER_VEST":{"VEST_V_BINDING_VANILLA_A","VEST_CUTIN_ARMHOLE_VANILLA_A","VEST_INNER_SHIRT_VANILLA_A","VEST_HEM_VANILLA_A"},
    "SAILOR_TOP":{"SAILOR_COLLAR_VANILLA_A","SAILOR_BOW_SMALL_A","SAILOR_REAR_FLAP_VANILLA_A"},
    "T_SHIRT":{"TEE_CREW_BINDING_VANILLA_A"},
}
TOPOLOGY={
    "POLO_SHIRT":{("ADD","right",12,1),("ADD","left",3,1)},
    "SWEATER_VEST":{("REMOVE","right",13,2),("REMOVE","right",13,3),("REMOVE","left",2,2),("REMOVE","left",2,3)},
    "SAILOR_TOP":{("ADD","right",12,1),("ADD","left",3,1)},
    "T_SHIRT":set(),
}
BG=(232,226,217,255); PANEL=(205,197,186,255); INK=(39,37,36,255); ACC=(46,116,125,255)


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def cells(render,system,direction): return {tuple(x) for x in render.semantic_regions["systems"][system][direction]}


def alpha(render,direction):
    return {(x,y) for y,row in enumerate(render.frames[direction]) for x,pixel in enumerate(row) if pixel[3]}


def topology(render):
    return {(op["op"],op["direction"],op["cell"][0],op["cell"][1]) for op in render.topology_map}


def identity_count(render,family):
    systems={
        "POLO_SHIRT":("collar","placket"),
        "SWEATER_VEST":("collar","armholes","inner_layer","hem","waistband","ribbing"),
        "SAILOR_TOP":("collar","collar_border","tie","inner_layer","rear_panel"),
        "T_SHIRT":("collar",),
    }[family]
    return sum(len(render.semantic_regions["systems"][system][d]) for system in systems for d in DIRECTIONS)


def selective_outline_ratio(render,direction):
    boundary=[]
    for y,row in enumerate(render.frames[direction]):
        for x,pixel in enumerate(row):
            if not pixel[3]: continue
            if any(nx<0 or nx>=16 or ny<0 or ny>=16 or not render.frames[direction][ny][nx][3]
                   for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))):
                boundary.append(render.role_frames[direction][y][x])
    darkest=sum(role=="PrimaryFabric.EXTERIOR_CONTOUR" for role in boundary)
    return 0 if not boundary else darkest/len(boundary)


def identity_checks(render,family):
    if family=="POLO_SHIRT":
        return {
            "frontFoldedCollar":len(cells(render,"collar","front"))>=6,
            "shortPlacket":len(cells(render,"placket","front"))==4,
            "sideCollarDepth":min(len(cells(render,"collar","right")),len(cells(render,"collar","left")))>=4,
            "placketFrontOnly":not any(cells(render,"placket",d) for d in ("right","back","left")),
        }
    if family=="SWEATER_VEST":
        runtime=render.semantic_regions["runtimeComponents"]
        return {
            "boundedFrontV":len(cells(render,"collar","front"))==6,
            "sleevelessCutin":min(len(cells(render,"armholes","right")),len(cells(render,"armholes","left")))>=4,
            "innerShirtHandoff":min(len(cells(render,"inner_layer","right")),len(cells(render,"inner_layer","left")))==3,
            "fourCellHemCues":all(len(cells(render,"hem",d))==4 for d in DIRECTIONS),
            "redundantRibSystemsCompressed":not any(cells(render,s,d) for s in ("waistband","ribbing") for d in DIRECTIONS),
            "architectureRuntimePreserved":all(d in runtime.get("waistband",{}) and d in runtime.get("ribbing",{}) for d in DIRECTIONS),
        }
    if family=="SAILOR_TOP":
        return {
            "broadFrontCollar":len(cells(render,"collar","front"))==10,
            "smallBowCluster":len(cells(render,"tie","front"))==4,
            "broadRearFlapCue":len(cells(render,"rear_panel","back"))==14,
            "sideContinuity":all(cells(render,"collar",d) and cells(render,"rear_panel",d) for d in ("right","left")),
            "noSeparateBorderCage":not any(cells(render,"collar_border",d) for d in DIRECTIONS),
        }
    return {"cleanCrewBinding":len(cells(render,"collar","front"))==6 and len(cells(render,"collar","back"))==4}


def qc_case(case,current,plus):
    family=case["family"]
    same_alpha={d:alpha(current,d)==alpha(plus,d) for d in DIRECTIONS}
    owned={d:{tuple(item["cell"]) for item in plus.semantic_regions["fabrics"][d]} for d in DIRECTIONS}
    outline_ratios={d:selective_outline_ratio(plus,d) for d in DIRECTIONS}
    rejected=plus.semantic_regions["ownership"]["rejectedMutations"]
    rejected_survive=all(
        plus.pre_polish_frames[item["direction"]][item["cell"][1]][item["cell"][0]]
        == plus.post_polish_frames[item["direction"]][item["cell"][1]][item["cell"][0]]
        for item in rejected
    )
    anchors=identity_checks(plus,family)
    checks={
        "compilerValidationPass":plus.validation["status"]=="PASS",
        "approvedMicroShapesExact":set(plus.metrics["shapeVariants"])==PLUS_VARIANTS[family],
        "architectureTopologyPreserved":topology(current)==topology(plus)==TOPOLOGY[family],
        "bodySilhouetteUnchanged":all(same_alpha.values()),
        "oneConnectedAlphaComponent":all(len(plus.validation["connectedComponents"][d])==1 for d in DIRECTIONS),
        "noUnsupportedTopPixels":all(not plus.validation["topRows"][d]["unsupportedRowZeroCells"] for d in DIRECTIONS),
        "noUnownedAlphaFringe":all(alpha(plus,d)<=owned[d] for d in DIRECTIONS),
        "noAccidentalDarkBands":all(not plus.validation["darkBandScan"][d]["vertical"] and not plus.validation["darkBandScan"][d]["horizontal"] for d in DIRECTIONS),
        "selectiveRatherThanUniformDarkOutline":all(ratio<0.60 for ratio in outline_ratios.values()),
        "identityAnchorsSurvive":all(anchors.values()),
        "ownershipConflictFree":plus.metrics["ownershipConflictCount"]==0,
        "protectedStructuralCellsSurvive":plus.validation["protectedStructuralSurvival"]["status"]=="PASS",
        "legacyPolishRejectionsPreserved":rejected_survive and plus.metrics["ownershipRejectedMutationCount"]==len(rejected),
        "identityDetailNotIncreased":identity_count(plus,family)<=identity_count(current,family),
    }
    return {
        "status":"PASS" if all(checks.values()) else "FAIL",
        "checks":checks,"identityAnchorChecks":anchors,"sameAlphaByDirection":same_alpha,
        "selectiveOutlineDarkestBoundaryRatio":outline_ratios,
        "identityCellCount":{"current":identity_count(current,family),"vanillaPlus":identity_count(plus,family)},
        "unownedAlphaCells":{d:[list(c) for c in sorted(alpha(plus,d)-owned[d])] for d in DIRECTIONS},
    }


def tile(canvas,image,x,y,border):
    draw_rect(canvas,x-2,y-2,len(image[0])+4,len(image)+4,border)
    draw_rect(canvas,x-1,y-1,len(image[0])+2,len(image)+2,PANEL)
    blit(canvas,image,x,y)


def proof_sheet(title,items,*,farmer):
    scale=2 if farmer else 8; source_w=64 if farmer else 16; source_h=128 if farmer else 16
    w=source_w*scale; h=source_h*scale; label=142; gap=18; top=38; row_h=h+31
    canvas=blank_image(label+4*(w+gap),top+len(items)*row_h+8,BG); draw_text(canvas,title,8,7,color=INK)
    for row,item in enumerate(items):
        y=top+row*row_h; draw_text(canvas,item["case"]["label"],8,y+h//2,color=INK)
        for col,direction in enumerate(DIRECTIONS):
            x=label+col*(w+gap); draw_text(canvas,direction.upper(),x,y,color=ACC)
            image=item["plus_farmer"][direction] if farmer else item["plus"].frames[direction]
            tile(canvas,nearest_scale(image,scale),x,y+15,ACC)
    return canvas


def comparison_sheet(items):
    scale=6; size=16*scale; gap=12; group_gap=28; label=128; top=51; row_h=size+29
    width=label+8*(size+gap)+group_gap
    canvas=blank_image(width,top+len(items)*row_h+8,BG)
    draw_text(canvas,"V4.2 CURRENT VS V4 VANILLA-PLUS | SAME CANONICAL / SEED / FIT / MATERIAL / PALETTE",8,7,color=INK)
    draw_text(canvas,"CURRENT V4.2",label,21,color=INK); draw_text(canvas,"VANILLA-PLUS",label+4*(size+gap)+group_gap,21,color=ACC)
    for group in range(2):
        start=label+group*(4*(size+gap)+group_gap)
        for col,d in enumerate(DIRECTIONS): draw_text(canvas,d.upper(),start+col*(size+gap),34,color=ACC)
    for row,item in enumerate(items):
        y=top+row*row_h; draw_text(canvas,item["case"]["label"],8,y+size//2,color=INK)
        for group,key in enumerate(("current","plus")):
            start=label+group*(4*(size+gap)+group_gap)
            for col,d in enumerate(DIRECTIONS):
                x=start+col*(size+gap); tile(canvas,nearest_scale(item[key].frames[d],scale),x,y,INK if group==0 else ACC)
    return canvas


def compile_current(case,canonical,projections):
    family=case["family"]
    profile=V42_SAILOR_OUTLINE_PROFILE if family=="SAILOR_TOP" else V42_PROOF_PROFILE
    compiler=PixelGrammarCompilerV4(execution_profile=profile)
    kwargs={}
    if CURRENT_VARIANTS[family]:
        kwargs={"required_shape_library_version":V42_SHAPE_LIBRARY_VERSION,"expected_shape_variants":CURRENT_VARIANTS[family]}
    return compiler.compile(canonical,projections,palette_story=case["palette"],**kwargs)


def main():
    if not FARMER.exists() or not HAIR.exists(): raise FileNotFoundError("unpacked Farmer fixtures are required")
    OUT.mkdir(parents=True,exist_ok=True)
    builder=CanonicalGarmentBuilder(); projector=DirectionalProjector()
    farmer=read_rgba_png(FARMER)["pixels"]; hair=read_rgba_png(HAIR)["pixels"]
    items=[]
    for case in CASES:
        canonical=builder.build(family=case["family"],design_intent=case["intent"],fit_profile=case["fit"],root_seed=case["seed"],rarity_budget="V4_VANILLA_PLUS_PROOF",material=case.get("material"))
        projections=projector.project(canonical)
        current=compile_current(case,canonical,projections)
        plus=PixelGrammarCompilerV4(execution_profile=V4_VANILLA_PLUS_PROFILE).compile(
            canonical,projections,palette_story=case["palette"],required_shape_library_version=V4_VANILLA_PLUS_LIBRARY_VERSION,
            expected_shape_variants=PLUS_VARIANTS[case["family"]],
        )
        qc=qc_case(case,current,plus)
        plus_farmer={d:_farmer_composite(farmer,hair,plus.frames[d],d) for d in DIRECTIONS}
        current_farmer={d:_farmer_composite(farmer,hair,current.frames[d],d) for d in DIRECTIONS}
        items.append({"case":case,"canonical":canonical,"projections":projections,"current":current,"plus":plus,"qc":qc,"plus_farmer":plus_farmer,"current_farmer":current_farmer})
        folder=OUT/case["slug"]
        dump(folder/"canonical-model.json",canonical); dump(folder/"projections.json",projections)
        dump(folder/"current-metrics.json",current.metrics); dump(folder/"current-validation.json",current.validation)
        dump(folder/"metrics.json",{**plus.metrics,"vanillaPlusQC":qc}); dump(folder/"validation.json",{**plus.validation,"vanillaPlusQC":qc,"humanVisualQC":{"status":"PENDING"}})
        dump(folder/"ownership-ledger.json",plus.semantic_regions["ownership"])
        write_rgba_png(folder/"final-logical-atlas.png",plus.texture)
    automated="PASS" if all(item["qc"]["status"]=="PASS" for item in items) else "FAIL"
    contract={
        "profile":V4_VANILLA_PLUS_PROFILE,"microShapeLibraryVersion":V4_VANILLA_PLUS_LIBRARY_VERSION,
        "cases":[{"family":x["case"]["family"],"seed":x["case"]["seed"],"palette":x["case"]["palette"],"sameCanonicalDigest":digest(x["current"].canonical)==digest(x["plus"].canonical),"sameProjectionDigest":digest(x["current"].projections)==digest(x["plus"].projections),"automatedQC":x["qc"]["status"]} for x in items],
        "automatedQC":automated,"humanVisualQC":"PENDING",
    }
    dump(OUT/"proof-contract.json",contract)
    write_rgba_png(OUT/"V4_VANILLA_PLUS_FARMER.png",proof_sheet("V4 VANILLA-PLUS | FARMER SCALE | HUMAN VISUAL QC PENDING",items,farmer=True))
    write_rgba_png(OUT/"V4_VANILLA_PLUS_ISOLATED_8X.png",proof_sheet("V4 VANILLA-PLUS | ISOLATED LOGICAL FRAMES | 8X",items,farmer=False))
    write_rgba_png(OUT/"V4_VANILLA_PLUS_VS_CURRENT.png",comparison_sheet(items))
    print(json.dumps({"automatedQC":automated,"humanVisualQC":"PENDING","cases":{x["case"]["family"]:x["qc"] for x in items}},indent=2))
    if automated!="PASS": raise RuntimeError("Vanilla-plus proof QC failed; inspect per-case validation")


if __name__=="__main__": main()
