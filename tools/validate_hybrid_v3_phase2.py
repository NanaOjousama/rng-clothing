#!/usr/bin/env python3
"""Static validation for the isolated Hybrid V3 Phase 2 proof."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from generator.hybrid_v3.builder import CanonicalGarmentBuilder
from generator.hybrid_v3.compiler import PixelGrammarCompiler
from generator.hybrid_v3.compiler.stage_trace import verify_frozen_backend
from generator.hybrid_v3.config import HYBRID_GARMENT_COMPILER_V3_ENABLED, is_enabled
from generator.hybrid_v3.data_validation import validate_repository
from generator.hybrid_v3.projector import DirectionalProjector
from generator.png_utils import read_rgba_png
from tools.generate_hybrid_v3_phase2 import CASES, MODEL_ORDER, OUT, PACK


def load(path): return json.loads(path.read_text(encoding="utf-8"))
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def main():
    errors=[]; checks={}
    frozen=verify_frozen_backend(); checks["frozenBackend"]=frozen
    if frozen["status"]!="PASS": errors.append("frozen backend hash mismatch")
    repo=validate_repository(); checks["v3DataRepository"]=repo
    if repo["status"]!="PASS": errors.extend(repo["errors"])
    checks["featureFlag"]={"constant":HYBRID_GARMENT_COMPILER_V3_ENABLED,"defaultEvaluation":is_enabled({})}
    if HYBRID_GARMENT_COMPILER_V3_ENABLED or is_enabled({}): errors.append("V3 feature flag is not false by default")
    shirts=list((PACK/"Shirts").glob("*/shirt.json")); presets=load(PACK/"preset_outfits.json")
    checks["counts"]={"cases":len(CASES),"shirtAppearances":len(shirts),"presets":len(presets)}
    if checks["counts"]!={"cases":8,"shirtAppearances":8,"presets":8}: errors.append(f"wrong bounded output counts {checks['counts']}")

    artifacts=("canonical-model.json","projections.json","semantic-flat.png","pixel-grammar-map.json","semantic-pixel-regions.json","shirt.png","farmer-directions.png","validation.json","stage-trace.json")
    builder=CanonicalGarmentBuilder(); projector=DirectionalProjector(); compiler=PixelGrammarCompiler(); garments=[]
    for case in CASES:
        target=OUT/case["id"]; missing=[name for name in artifacts if not (target/name).exists()]
        if missing: errors.append(f"{case['id']}: missing artifacts {missing}"); continue
        canonical=load(target/"canonical-model.json"); projections=load(target/"projections.json"); validation=load(target/"validation.json"); pixel_map=load(target/"pixel-grammar-map.json"); regions=load(target/"semantic-pixel-regions.json")
        if validation["status"]!="PASS" or validation["farmerVisualReview"]["status"]!="PASS": errors.append(f"{case['id']}: final QC not PASS")
        if any(len(v)!=1 for v in validation["connectedComponents"].values()): errors.append(f"{case['id']}: alpha component count")
        if any(v["unsupportedRowZeroCells"] for v in validation["topRows"].values()): errors.append(f"{case['id']}: top-edge contamination")
        if not validation["binaryAlpha"]: errors.append(f"{case['id']}: non-binary alpha")
        atlas=read_rgba_png(target/"shirt.png")
        if (atlas["width"],atlas["height"])!=(16,64): errors.append(f"{case['id']}: atlas is not 16x64")
        family=case["family"]
        if family=="POLO_SHIRT":
            if canonical["material"]["id"]!="KNIT": errors.append(f"{case['id']}: polo material not KNIT")
            for d in ("right","back","left"):
                p=next(x for x in projections[d] if x["componentInstance"]=="placket")
                expected="FORBIDDEN" if d=="back" else "HIDDEN"
                if p["visibility"]!=expected: errors.append(f"{case['id']}: placket {d} {p['visibility']}")
                if regions["components"].get("placket",{}).get(d): errors.append(f"{case['id']}: placket pixels in {d}")
            if pixel_map["inheritedCarrierPlacketCellsReset"]<=0: errors.append(f"{case['id']}: inherited placket was not reset")
        if family=="SWEATER_VEST":
            if any(x["componentType"]=="SLEEVE" for x in canonical["components"]): errors.append(f"{case['id']}: vest has sleeve component")
            for d in ("right","left"):
                if not regions["components"].get("armholes",{}).get(d): errors.append(f"{case['id']}: missing side armhole")
                if len(regions["clearedByCompiler"].get("body",{}).get(d,[]))!=6: errors.append(f"{case['id']}: vest carrier mapping did not exclude six invalid cells on {d}")
        if family=="SAILOR_TOP":
            rear={d:next(x for x in projections[d] if x["componentInstance"]=="rear")["visibility"] for d in ("front","right","back","left")}
            if rear!={"front":"HIDDEN","right":"COMPRESSED","back":"FULL","left":"COMPRESSED"}: errors.append(f"{case['id']}: rear panel projection drift {rear}")
            if not regions["components"].get("rear",{}).get("back"): errors.append(f"{case['id']}: no compiled rear panel")
        rebuilt=builder.build(family=case["family"],design_intent=case["intent"],fit_profile=case["fit"],root_seed=case["seed"],rarity_budget="PHASE2_NEUTRAL_DEFAULT")
        reproj=projector.project(rebuilt); rerender=compiler.compile(rebuilt,reproj,palette_story=case["palette"])
        determinism={"canonical":digest(canonical)==digest(rebuilt),"projections":digest(projections)==digest(reproj),"texture":digest(atlas["pixels"])==digest(rerender.texture)}
        if not all(determinism.values()): errors.append(f"{case['id']}: nondeterministic {determinism}")
        garments.append({"id":case["id"],"family":family,"status":validation["status"],"farmer":validation["farmerVisualReview"]["status"],"connectedComponents":validation["connectedComponents"],"determinism":determinism,"carrier":pixel_map["carrierId"]})

    for shirt in shirts:
        model=load(shirt)
        for key,y in MODEL_ORDER:
            data=model[key]
            if data["Scale"]!=2.0 or data["BodyPosition"]!={"X":0,"Y":32} or data["StartingPosition"]!={"X":0,"Y":y} or data["ShirtSize"]!={"Width":16,"Length":16} or data["HideSleeves"] is not False:
                errors.append(f"{shirt}: runtime contract mismatch in {key}")
    compiler_text="\n".join(path.read_text(encoding="utf-8") for path in (ROOT/"generator/hybrid_v3/compiler").glob("*.py"))
    forbidden=[name for name in ("reference_grammar.render_controlled_garment","PREMIUM_CARDIGAN_V1","PREMIUM_CONSTRUCTION_CARDIGAN_V1") if name in compiler_text]
    if forbidden: errors.append(f"forbidden renderer route references {forbidden}")
    result={"status":"PASS" if not errors else "FAIL","errors":errors,"checks":checks,"garments":garments,"forbiddenRoutesFound":forbidden}
    (OUT/"phase2-validation.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    (PACK/"pack-validation.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if not errors else 1)

if __name__=="__main__": main()
