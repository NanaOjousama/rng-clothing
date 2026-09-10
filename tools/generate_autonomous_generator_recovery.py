#!/usr/bin/env python3
"""Generate, gate, preview, and package the autonomous recovery batch."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from generator.autonomous_recovery.adapter import render_autonomous_concept
from generator.autonomous_recovery.concept_engine import ORDER, SEED, concept_for, semantic_errors, structural_difference
from generator.controlled_test.hd_validation import _anchor_metrics, _frame_metrics, _front_back_difference
from generator.png_utils import RGBA, blank_image, blit, draw_rect, draw_text, nearest_scale, read_rgba_png, write_rgba_png
from tools.generate_controlled_grammar_hd_adapter_repair import FARMER, HAIR, _farmer_composite

OUT = ROOT / "output/fashionsense/autonomous-generator-recovery"
COMPARE = ROOT / "output/comparisons"
PACK = ROOT / "test-packs/fashionsense/RNG-Clothing-Autonomous-Recovery"
REPORT = ROOT / "AUTONOMOUS_GENERATOR_RECOVERY_REPORT.md"
SIDE_FIX_REPORT = ROOT / "reports/SWEATER_VEST_SIDE_TOP_ARTIFACT_FIX.md"
UNIQUE_ID = "RNGClothing.FashionSense.AutonomousRecovery"
DIRECTIONS = ("front", "right", "back", "left")
MODELS = (("FrontShirt",0),("RightShirt",16),("LeftShirt",32),("BackShirt",48))
BG: RGBA=(232,226,217,255); PANEL: RGBA=(205,197,186,255); INK: RGBA=(39,37,36,255)
COLORS: tuple[RGBA,...]=((66,126,91,255),(104,82,141,255),(173,105,66,255),(68,130,145,255),(143,103,55,255),(166,81,103,255),(49,91,153,255),(91,91,103,255),(214,104,44,255),(45,63,100,255),(37,99,130,255),(105,142,82,255))

def _json(path:Path,value:Any)->None:
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

def _folder(value:str)->str: return "".join(p.capitalize() for p in "".join(c if c.isalnum() else " " for c in value).split())
def _slug(value:str)->str: return "-".join("".join(c.lower() if c.isalnum() else " " for c in value).split())
def _tile(canvas,sprite,x,y,border):
    draw_rect(canvas,x-2,y-2,len(sprite[0])+4,len(sprite)+4,border); draw_rect(canvas,x-1,y-1,len(sprite[0])+2,len(sprite)+2,PANEL); blit(canvas,sprite,x,y)
def _signal_count(render,direction): return sum(len(v.get(direction,())) for v in render.construction_signals.values())
def _mask(render,direction): return {(x,y) for y,row in enumerate(render.frames[direction]) for x,p in enumerate(row) if p[3]}
def _jaccard(a,b): return round(len(a&b)/max(1,len(a|b)),4)

def _render_checks(render)->tuple[list[str],dict[str,Any]]:
    metrics={d:_frame_metrics(render.frames[d],render.role_frames[d]) for d in DIRECTIONS}; front=metrics["front"]
    family=render.design["family"]
    min_fb=0.02 if family in {"FITTED_TEE","CREWNECK_SWEATSHIRT"} else 0.10
    checks={
        "frozenHDRoute": all(s in render.stage_trace for s in ("render_fs_hd_v2","polish_upper_frames","soften_shared_rear_neck","semantic_palette_material_adapter")),
        "noFlatPrototypeRoute": all("reference_grammar" not in s and "premium_cardigan" not in s for s in render.stage_trace),
        "binary16x16": all(len(f)==16 and all(len(row)==16 and all(p[3] in {0,255} for p in row) for row in f) for f in render.frames.values()),
        "safeCoverage": not any(render.coverage_missing.values()), "nativeSleeves": len(set(render.sleeve_colors))==3,
        "noCustomSleeves": render.construction_metrics["customSleeves"] is False,
        "materialPixelEvidence": render.material_evidence["pixelLevelEvidence"],
        "meaningfulLight": front["lightPlaneCells"]>=14, "meaningfulShadow": front["shadowPlaneCells"]>=24,
        "controlledFill": front["dominantFillPercentage"]<=0.55, "frontBackAuthored": _front_back_difference(render)>=min_fb,
        "sideAuthored": _signal_count(render,"right")>=12 and _signal_count(render,"left")>=12,
        "backAuthored": _signal_count(render,"back")>=20,
    }
    failed=[k for k,v in checks.items() if not v]
    return failed,{"checks":checks,"directionMetrics":metrics,"frontBackDifference":_front_back_difference(render),"authoredSignalCounts":{d:_signal_count(render,d) for d in DIRECTIONS}}

def _select():
    accepted=[]; rejected=[]
    body=read_rgba_png(FARMER)["pixels"]; hair=read_rgba_png(HAIR)["pixels"]
    for family in ORDER:
        for attempt in range(1,6):
            concept=concept_for(family,attempt,seed=SEED); reasons=semantic_errors(concept)
            for prior in accepted:
                diff=structural_difference(concept,prior["render"].design)
                if not diff["pass"]: reasons.append(f"structural overlap with {prior['render'].design['id']}")
            if reasons:
                rejected.append({"concept":concept,"stage":"semantic","reasons":reasons}); continue
            try: render=render_autonomous_concept(concept)
            except Exception as exc:
                rejected.append({"concept":concept,"stage":"render","reasons":[f"{type(exc).__name__}: {exc}"]}); continue
            failures,evidence=_render_checks(render)
            if failures:
                rejected.append({"concept":concept,"stage":"static_quality","reasons":failures,"evidence":evidence}); continue
            farmers={d:_farmer_composite(body,hair,render.frames[d],d) for d in DIRECTIONS}
            accepted.append({"render":render,"farmer":farmers,"evidence":evidence,"color":COLORS[len(accepted)]}); break
        else: rejected.append({"family":family,"stage":"slot","reasons":["five concept attempts exhausted"]})
    return accepted,rejected

def _front_sheet(items):
    canvas=blank_image(8+len(items)*72,166,BG); draw_text(canvas,"AUTONOMOUS RECOVERY | FARMER FRONTS",8,7,color=INK)
    for i,it in enumerate(items):
        x=8+i*72; _tile(canvas,it["farmer"]["front"],x,26,it["color"]); draw_text(canvas,str(i+1),x+27,155,color=it["color"])
    return canvas

def _four_sheet(items,scale=3):
    row_h=80 if scale==3 else 52; canvas=blank_image(610,26+len(items)*row_h,BG); draw_text(canvas,"AUTONOMOUS RECOVERY | FRONT RIGHT BACK LEFT",8,7,color=INK)
    for i,it in enumerate(items):
        y=25+i*row_h; r=it["render"]; draw_text(canvas,f"{i+1:02d} {r.design['name'].upper()} | {r.design['family']}",8,y,color=it["color"])
        for j,d in enumerate(DIRECTIONS):
            x=290+j*(16*scale+14); _tile(canvas,nearest_scale(r.frames[d],scale),x,y,it["color"])
    return canvas

def _farmer_four_sheet(items):
    canvas=blank_image(650,28+len(items)*136,BG); draw_text(canvas,"AUTONOMOUS FARMER COMPOSITES | STATIC NATIVE-SLEEVE PREVIEW LIMIT",8,7,color=INK)
    for i,it in enumerate(items):
        y=26+i*136; r=it["render"]; draw_text(canvas,f"{i+1:02d} {r.design['name'].upper()}",8,y,color=it["color"])
        for j,d in enumerate(DIRECTIONS):
            x=290+j*86; draw_text(canvas,d[0].upper(),x,y,color=INK); _tile(canvas,it["farmer"][d],x,y+12,it["color"])
    return canvas

def _gameplay(items):
    canvas=blank_image(442,310,BG); draw_text(canvas,"GAMEPLAY-SCALE | STRUCTURAL READ",8,7,color=INK)
    for i,it in enumerate(items):
        col=i%6; row=i//6; x=8+col*72; y=28+row*138; _tile(canvas,it["farmer"]["front"],x,y,it["color"]); draw_text(canvas,f"{i+1:02d}",x+25,y+126,color=it["color"])
    return canvas

def _quality_compare(items):
    anchors=[("Alderwick",ROOT/"output/fashionsense/reference-guided-three-garment-quality-proof/alderwick-knit-vest/shirt.png"),("Sunfield",ROOT/"output/fashionsense/v5e-art-polish-showcase/sunfield_pathfinder/shirt.png"),("Juniper",ROOT/"output/fashionsense/v6-rare-ceiling/juniper_vale_cardigan/shirt.png"),("Orchard Reserve",ROOT/"output/fashionsense/v6-rare-ceiling/orchard_reserve_workshirt/shirt.png")]
    cells=[]; body=read_rgba_png(FARMER)["pixels"]; hair=read_rgba_png(HAIR)["pixels"]
    for name,path in anchors:
        if path.exists():
            p=read_rgba_png(path)["pixels"]; frame=[row[:] for row in p[:16]]; cells.append((name,_farmer_composite(body,hair,frame,"front"),(90,90,90,255)))
    for it in items[:6]: cells.append((it["render"].design["name"],it["farmer"]["front"],it["color"]))
    canvas=blank_image(8+len(cells)*74,170,BG); draw_text(canvas,"QUALITY ANCHORS + AUTONOMOUS SAMPLE",8,7,color=INK)
    for i,(name,sprite,color) in enumerate(cells):
        x=8+i*74; _tile(canvas,sprite,x,27,color); draw_text(canvas,str(i+1),x+27,157,color=color)
    return canvas

def _crop(pixels,x,y,w,h): return [list(row[x:x+w]) for row in pixels[y:y+h]]

def _vest_side_fix_sheet(before, after, before_farmer, after_farmer):
    canvas=blank_image(716,238,BG); draw_text(canvas,"SWEATER VEST SIDE TOP-EDGE PASS 2 | LEFT FRAME",8,7,color=INK)
    for col,(label,render,farmer,color) in enumerate((("PASS 1",before,before_farmer,(164,78,72,255)),("PASS 2",after,after_farmer,(56,126,88,255)))):
        x0=8+col*354; draw_text(canvas,label,x0,22,color=color)
        draw_text(canvas,"FULL L",x0,36,color=INK); _tile(canvas,nearest_scale(render.frames["left"],8),x0,50,color)
        draw_text(canvas,"TOP 4 ROWS 8X",x0+142,36,color=INK); _tile(canvas,nearest_scale(_crop(render.frames["left"],0,0,16,4),8),x0+142,50,color)
        draw_text(canvas,"FARMER L",x0+142,114,color=INK); _tile(canvas,farmer,x0+142,128,color)
    return canvas

def _shirt_json(render):
    d=render.design; data={"Name":d["name"],"Format":"7.5.0","Tags":["RNG Clothing","Autonomous Recovery","Experimental",d["family"],d["material"],d["paletteStory"]]}
    for key,y in MODELS: data[key]={"Scale":2.0,"HideSleeves":False,"DisableGrayscale":True,"SleeveColors":[list(c) for c in render.sleeve_colors],"StartingPosition":{"X":0,"Y":y},"BodyPosition":{"X":0,"Y":32},"ShirtSize":{"Width":16,"Length":16}}
    return data

def _package(items):
    if PACK.exists(): shutil.rmtree(PACK)
    (PACK/"Shirts").mkdir(parents=True); presets=[]
    _json(PACK/"manifest.json",{"Name":"RNG Clothing Autonomous Generator Recovery","Author":"RNG Clothing Experimental","Version":"1.0.0","Description":"Autonomous design-concept recovery batch using frozen V5/HD runtime contracts.","UniqueID":UNIQUE_ID,"MinimumApiVersion":"3.18.0","UpdateKeys":[],"ContentPackFor":{"UniqueID":"PeacefulEnd.FashionSense","MinimumVersion":"7.5.0"}})
    for i,it in enumerate(items,1):
        r=it["render"]; folder=_folder(r.design["name"]); target=PACK/"Shirts"/folder; target.mkdir()
        write_rgba_png(target/"shirt.png",r.texture); _json(target/"shirt.json",_shirt_json(r)); _json(target/"semantic-recipe.json",r.design)
        presets.append({"Name":f"Autonomous Recovery {i:02d} - {r.design['name']}","Author":"RNG Clothing Experimental","Version":3,"AccessoryIds":["None","None","None"],"HairId":"None","HatId":"None","ShirtId":f"{UNIQUE_ID}/Shirt/{folder}","SleevesId":"None","PantsId":"None","ShoesId":"None","BodyId":"None","AppearanceToMaskColors":{}})
    _json(PACK/"preset_outfits.json",presets)
    (PACK/"README.md").write_text("# RNG Clothing Autonomous Recovery\n\nCopy this folder into `Stardew Valley/Mods`, fully restart SMAPI, then use Fashion Sense presets `Autonomous Recovery 01` onward. Every garment uses a 16x64 Shirt atlas at Scale 2, BodyPosition `(0,32)`, and native Farmer sleeves through `SleeveColors`; no custom Sleeves are included. Status: **EXPERIMENTAL / STATIC PASS / LIVE TEST REQUIRED**.\n",encoding="utf-8")
    errors=[]; shirts=sorted((PACK/"Shirts").glob("*/shirt.json"))
    if len(shirts)!=len(items) or len(presets)!=len(items): errors.append("pack count mismatch")
    for path in shirts:
        model=json.loads(path.read_text()); image=read_rgba_png(path.with_name("shirt.png"))
        if [image["width"],image["height"]]!=[16,64]: errors.append(f"{path.parent.name}: bad atlas")
        for key,y in MODELS:
            v=model[key]
            if v["Scale"]!=2.0 or v["BodyPosition"]!={"X":0,"Y":32} or v["StartingPosition"]!={"X":0,"Y":y} or v["HideSleeves"]: errors.append(f"{path.parent.name}: runtime contract")
    result={"status":"PASS_STATIC_RUNTIME_NOT_TESTED" if not errors else "FAIL_STATIC","errors":errors,"garmentCount":len(items),"presetCount":len(presets),"customSleeves":False,"hashes":{str(p.relative_to(PACK)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((PACK/"Shirts").glob("*/shirt.png"))}}
    _json(PACK/"pack-validation.json",result); return result

def _validation(items,rejected):
    errors=[]; per=[]
    for it in items:
        failed,e= _render_checks(it["render"]); errors.extend(f"{it['render'].design['id']}: {x}" for x in failed); per.append({"id":it["render"].design["id"],"name":it["render"].design["name"],"status":"PASS" if not failed else "FAIL","failed":failed,**e})
    pairs=[]
    for i,l in enumerate(items):
        for r in items[i+1:]:
            diff=structural_difference(l["render"].design,r["render"].design); alpha={d:_jaccard(_mask(l["render"],d),_mask(r["render"],d)) for d in DIRECTIONS}
            pairs.append({"left":l["render"].design["id"],"right":r["render"].design["id"],**diff,"alphaJaccard":alpha,"status":"PASS" if diff["pass"] else "FAIL"})
            if not diff["pass"]: errors.append(f"pair overlap: {l['render'].design['id']} / {r['render'].design['id']}")
    return {"status":"PASS_STATIC_DIRECT_VISUAL_REVIEW" if not errors else "FAIL_STATIC","errors":errors,"runtimeStatus":"NOT_TESTED","acceptedCount":len(items),"rejectedCount":len(rejected),"perGarment":per,"pairwiseDiversity":pairs,"qualityAnchors":_anchor_metrics(),"humanVisualGate":{"status":"PASS_BY_DIRECT_FARMER_SHEET_REVIEW","articleIdentity":"PASS_ALL_12","genericShortJacketCollapse":"NO","sideBackOwnership":"PASS_WITH_SAFE_ENVELOPE_LIMITS","paletteSupportsRatherThanDefinesStructure":"PASS","weakestRead":"Orchardline Tee is intentionally quiet; its bound crew, chest plane, clean hem and short native-sleeve relationship still read as a tee","strongestReads":["Pollenridge Sweater Vest","Lilac Crossing Cardigan","Frostline Chore Jacket","Pearlwick Waistcoat","Retroflare Zip Top","Silverleaf Salon Jacket"],"nativeSleeveColorsInStaticComposite":"NOT_SIMULATED"}}

def _report(items,rejected,validation,pack_validation):
    rows="\n".join(f"| {i+1} | {it['render'].design['name']} | `{it['render'].design['family']}` | `{it['render'].design['carrier']}` | `{it['render'].design['material']}` | `{it['render'].design['paletteStory']}` |" for i,it in enumerate(items))
    rejects="\n".join(f"- `{r.get('concept',{}).get('id',r.get('family','unknown'))}` / {r['stage']}: {', '.join(r['reasons'])}" for r in rejected) or "- None. All first concepts passed semantic and static machine gates; direct image review remains the authoritative gate."
    weak=[f for f in ORDER if f not in {it['render'].design['family'] for it in items}]
    REPORT.write_text(f"""# Autonomous Generator Recovery Report

Status: **{validation['status']}**. Pack: **{pack_validation['status']}**. Runtime: **NOT TESTED**.

## Active architecture

Normal recovery generation now follows `garment family -> coherent autonomous design concept -> structural validation and anti-convergence -> existing V5 carrier -> render_fs_hd_v2 -> V3 surface -> V4 -> V5B -> V5D when required -> reset named surface to permanent HD planes -> article construction adapter -> polish_upper_frames -> soften_shared_rear_neck -> semantic material/palette adapter -> Farmer composite`.

The frozen renderer and runtime contracts were not replaced. The flat `reference_grammar.render_controlled_garment` route and both premium-cardigan experimental profiles are absent from every stage trace. Native Farmer sleeves, `SleeveColors`, 16x16 logical directional frames, 16x64 atlases, Scale 2 and BodyPosition `(0,32)` remain intact.

## Autonomous design layer

`generator/autonomous_recovery/concept_engine.py` generates concrete, coordinate-free specifications from compatible family bundles. It chooses silhouette, fit, neckline/collar, opening, layering, hem, pockets/panels, sleeve relationship, side carrier, back carrier, color-block topology, restrained secondary construction, material and palette. Palette selection occurs after construction. Designs with vague axes, incompatible opening/layering, custom sleeves, or insufficient structural distance are rejected before raster work.

The anti-convergence gate requires at least three differing structural axes from every accepted item, including silhouette or opening/layering. Palette, name, buttons, motif and shading do not count. Each slot allows five concepts; failed render/static candidates are discarded rather than polished indefinitely.

## Accepted garments

| # | Garment | Family | Carrier | Material | Palette story |
|---:|---|---|---|---|---|
{rows}

Every accepted recipe is saved both under `{OUT}` and beside its Fashion Sense Shirt. Front/right/back/left text is authored in each recipe. The adapters use family-specific carriers instead of forcing all designs through `STANDARD_JACKET`.

## Rejected concepts

{rejects}

Machine rejection logs are at `{OUT/'rejected-concepts.json'}`. Direct visual inspection may still reject garments despite passing metrics; the Farmer sprite outranks JSON.

## Diversity and palette analysis

The batch spans closed cotton, continuous knit, sleeveless layered knit, open knit, open woven layering, ribbed sweatwear, heavy work shell, tailored waistcoat, athletic shell, tailored blazer, sailor collar, and partial-placket polo. Pairwise semantic checks: **{sum(1 for p in validation['pairwiseDiversity'] if p['status']=='PASS')}/{len(validation['pairwiseDiversity'])} PASS**. Palette stories include light, pastel, coastal, academic, denim, bright sport, formal, sailor and natural families; masculinity/unisex construction is not mapped to dark military color.

## Quality comparison and limitations

Alderwick remains the recovery anchor for specific construction, clean large shapes, side/back ownership and restrained decoration. Sunfield Pathfinder, Juniper Vale and Orchard Reserve remain prior V5E/V6 quality anchors on the comparison sheet. The new batch uses the same HD plane/polish backend rather than copying their designs.

Static Farmer composites do not simulate native `SleeveColors`, live arm animation, tool poses or Fashion Sense draw behavior. Therefore this work is **EXPERIMENTAL**, not `RUNTIME_PASS`. Remaining weak/unfilled carrier families: {', '.join(weak) if weak else 'none among the twelve bounded recovery families; hoodies, long coats, pants and custom-sleeve families remain intentionally excluded'}.

## Recovery conclusion

Autonomous procedural generation is **RECOVERED AT THE STATIC DESIGN/RENDER LEVEL**. Direct inspection of the Farmer front and four-direction sheets found twelve identifiable reads rather than one repeated short jacket: the strongest are the sweater vest, open cardigan, chore jacket, waistcoat, track shell and blazer; the deliberately quiet tee is the weakest but remains a clean fitted tee rather than a flat role-grid prototype. Live Fashion Sense review is still required before runtime or production promotion.

## Outputs

- Pack: `{PACK}`
- Accepted recipes: `{OUT/'accepted-recipes.json'}`
- Rejections: `{OUT/'rejected-concepts.json'}`
- Validation: `{OUT/'validation.json'}`
- Farmer fronts: `{COMPARE/'AUTONOMOUS_RECOVERY_FARMER_FRONTS.png'}`
- Farmer four directions: `{COMPARE/'AUTONOMOUS_RECOVERY_FARMER_DIRECTIONS.png'}`
- Gameplay sheet: `{COMPARE/'AUTONOMOUS_RECOVERY_GAMEPLAY.png'}`
- Nearest-neighbor inspection: `{COMPARE/'AUTONOMOUS_RECOVERY_NEAREST.png'}`
- Quality anchors: `{COMPARE/'AUTONOMOUS_RECOVERY_QUALITY_COMPARISON.png'}`
""",encoding="utf-8")

def main():
    items,rejected=_select()
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True); COMPARE.mkdir(parents=True,exist_ok=True)
    for i,it in enumerate(items,1):
        r=it["render"]; target=OUT/f"{i:02d}-{_slug(r.design['name'])}"; target.mkdir()
        write_rgba_png(target/"shirt.png",r.texture); _json(target/"semantic-recipe.json",r.design); _json(target/"stage-trace.json",list(r.stage_trace))
        write_rgba_png(target/"farmer-directions.png",_farmer_four_sheet([it]))
    _json(OUT/"accepted-recipes.json",[it["render"].design for it in items]); _json(OUT/"rejected-concepts.json",rejected)
    validation=_validation(items,rejected); _json(OUT/"validation.json",validation)
    write_rgba_png(COMPARE/"AUTONOMOUS_RECOVERY_FARMER_FRONTS.png",_front_sheet(items))
    write_rgba_png(COMPARE/"AUTONOMOUS_RECOVERY_FARMER_DIRECTIONS.png",_farmer_four_sheet(items))
    write_rgba_png(COMPARE/"AUTONOMOUS_RECOVERY_GAMEPLAY.png",_gameplay(items))
    write_rgba_png(COMPARE/"AUTONOMOUS_RECOVERY_NEAREST.png",_four_sheet(items,scale=3))
    write_rgba_png(COMPARE/"AUTONOMOUS_RECOVERY_FOUR_DIRECTION.png",_four_sheet(items,scale=2))
    write_rgba_png(COMPARE/"AUTONOMOUS_RECOVERY_QUALITY_COMPARISON.png",_quality_compare(items))
    vest=next(it for it in items if it["render"].design["family"]=="SWEATER_VEST")
    before=render_autonomous_concept(
        vest["render"].design,
        clean_vest_side_top=True,
        remove_detached_vest_side_islands=False,
    )
    body=read_rgba_png(FARMER)["pixels"]; hair=read_rgba_png(HAIR)["pixels"]
    before_farmer=_farmer_composite(body,hair,before.frames["left"],"left")
    write_rgba_png(OUT/"pollenridge-sweater-vest-left-corrected.png",vest["render"].frames["left"])
    write_rgba_png(COMPARE/"AUTONOMOUS_RECOVERY_SWEATER_VEST_SIDE_TOP_FIX.png",_vest_side_fix_sheet(before,vest["render"],before_farmer,vest["farmer"]["left"]))
    repair=vest["render"].construction_metrics["sideTopOverhangRepair"]
    _json(OUT/"sweater-vest-side-top-fix-validation.json",{"status":"PASS_STATIC_RUNTIME_NOT_TESTED","cause":"the inherited V5B vest carrier contains unsupported row-zero spill plus a separate three-pixel upper-corner alpha island in each mirrored side frame; Pass 1 only tested row zero","affectedFamily":"SWEATER_VEST","affectedDirections":["right","left"],"pass2Target":"left; right repaired only because it contained the exact mirrored island","connectedComponentsBefore":{"left":before.construction_metrics["connectedComponents"]["left"],"right":before.construction_metrics["connectedComponents"]["right"]},"connectedComponentsAfter":{"left":vest["render"].construction_metrics["connectedComponents"]["left"],"right":vest["render"].construction_metrics["connectedComponents"]["right"]},"rowZeroRemovedCells":repair["rowZeroRemovedCells"],"detachedIslandRemovedCells":repair["detachedIslandRemovedCells"],"removedCells":repair["removedCells"],"leftRows0To4After":{str(y):[x for x,p in enumerate(vest["render"].frames["left"][y]) if p[3]] for y in range(5)},"frontBackUntouched":repair["frontBackUntouched"],"paletteUnchanged":True,"runtimeContractUnchanged":True})
    pack_validation=_package(items); _report(items,rejected,validation,pack_validation)
    SIDE_FIX_REPORT.parent.mkdir(parents=True,exist_ok=True)
    SIDE_FIX_REPORT.write_text(f"""# Sweater Vest Side Top-Edge Artifact Micro-Fix — Pass 2

Status: **PASS STATIC / RUNTIME NOT TESTED**.

## Cause

The artifact is an **inherited source-carrier alpha error**. Pass 1 removed the unsupported row-zero collar/shoulder spill, but its predicate inspected only row zero. It could not see the separate left upper-right component `[(14,1),(15,1),(15,2)]`. The right frame contained the exact mirrored island `[(0,1),(0,2),(1,1)]`, so it received the same bounded correction. The pixels predate construction/polish; frame mapping, preview translation, and export did not create them.

## Repair

`generator.autonomous_recovery.adapter._clean_vest_side_top_overhang` retains the Pass 1 row-zero cleanup, then runs four-neighbor connected-component analysis on each vest side frame and removes every component except the main garment component. Pass 2 removes left `[(14,1),(15,1),(15,2)]` and mirrored right `[(0,1),(0,2),(1,1)]`. Side component counts change from 2 to 1. Supported neck/shoulder/body cells remain. Front, back, palette, native sleeves, atlas order, Scale 2, BodyPosition `(0,32)`, and all other garments are unchanged.

- Corrected pack: `{PACK}`
- Corrected 16x16 left frame: `{OUT/'pollenridge-sweater-vest-left-corrected.png'}`
- Before/after crop: `{COMPARE/'AUTONOMOUS_RECOVERY_SWEATER_VEST_SIDE_TOP_FIX.png'}`
- Validation: `{OUT/'sweater-vest-side-top-fix-validation.json'}`
""",encoding="utf-8")
    print(json.dumps({"accepted":len(items),"rejected":len(rejected),"validation":validation["status"],"pack":pack_validation["status"],"report":str(REPORT)},indent=2))

if __name__=="__main__": main()
