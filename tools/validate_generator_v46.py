#!/usr/bin/env python3
"""Static guardrails for V4.6. Never promotes runtime status."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from generator.png_utils import encode_rgba_png, read_rgba_png
from generator.renderers.fashionsense import appearance_json_v46, render_v46
from generator.v46 import generate_v46_prototypes, validate_v46_recipe


def check(value, message, errors):
    if not value: errors.append(message)


def main():
    errors=[]; warnings=[]
    recipes_a=generate_v46_prototypes(); recipes_b=generate_v46_prototypes()
    check(recipes_a==recipes_b,"semantic generation is nondeterministic",errors)
    check(len(recipes_a)==4,"expected exactly four prototypes",errors)
    counts={a:sum(r["articleType"]==a for r in recipes_a) for a in ("FITTED_PANTS","FOOTWEAR")}
    check(counts=={"FITTED_PANTS":2,"FOOTWEAR":2},f"wrong article mix: {counts}",errors)
    hashes={}; summaries=[]
    contracts=json.loads((ROOT/"generator"/"data"/"fashionsense"/"v46"/"lower_body_frame_contracts.json").read_text())
    for article, contract in contracts["contracts"].items():
        for key in ("json","png"):
            source=ROOT/contract["source"][key]; expected=contract["source"][key+"Sha256"]
            check(source.exists(),f"{article}: missing authoritative {key} source",errors)
            if source.exists(): check(hashlib.sha256(source.read_bytes()).hexdigest()==expected,f"{article}: authoritative {key} source hash changed; rebuild/audit contracts",errors)
        check(all("anatomy" in contract["coverage"][str(i)] for i in range(contract["texture"]["capacity"])),f"{article}: frame anatomy map incomplete",errors)
    for recipe in recipes_a:
        errors.extend(f"{recipe['id']}: {e}" for e in validate_v46_recipe(recipe))
        one=render_v46(recipe); two=render_v46(recipe)
        check(one.texture==two.texture,f"{recipe['id']}: nondeterministic pixels",errors)
        check(not one.static_errors,f"{recipe['id']}: {'; '.join(one.static_errors)}",errors)
        check(one.runtime_status=="EXPERIMENTAL" and recipe["runtimeStatus"]=="EXPERIMENTAL",f"{recipe['id']}: illegal runtime promotion",errors)
        slug="_".join(re.sub(r"[^a-z0-9]+"," ",recipe["name"].lower()).split())
        path=ROOT/"output"/"fashionsense"/"v46-lower-body-runtime"/slug/f"{slug}.png"
        check(path.exists(),f"{recipe['id']}: missing native output",errors)
        if path.exists():
            png=read_rgba_png(path); info=one.contract["texture"]
            check((png["width"],png["height"])==(info["width"],info["height"]),f"{recipe['id']}: wrong atlas dimensions",errors)
            check(set(png["filters"])=={0},f"{recipe['id']}: PNG encoder used nonzero filter",errors)
            check({p[3] for row in png["pixels"] for p in row}<={0,255},f"{recipe['id']}: semitransparent pixels",errors)
            digest=hashlib.sha256(encode_rgba_png(one.texture)).hexdigest(); check(png["sha256"]==digest,f"{recipe['id']}: output differs from renderer",errors); hashes[recipe["id"]]=digest
        model=appearance_json_v46(recipe,one); suffix="Pants" if recipe["articleType"]=="FITTED_PANTS" else "Shoes"
        check(model["Format"]=="7.5.0",f"{recipe['id']}: wrong FS format",errors)
        for direction in ("Front","Back","Right","Left"):
            m=model[direction+suffix]; size=m[suffix+"Size"]; capacity=one.contract["texture"]["capacity"]
            check(size=={"Width":16,"Length":32},f"{recipe['id']}/{direction}: wrong logical frame",errors)
            check(m["Scale"]==4.0 and m["DisableNativeOffset"] is True,f"{recipe['id']}/{direction}: scale/native offset contract changed",errors)
            check(m["HideWhileSwimming"] is True and m["HideWhileWearingBathingSuit"] is True,f"{recipe['id']}/{direction}: unsafe water visibility",errors)
            check(all(0<=a["Frame"]<capacity for a in m["UniformAnimation"]),f"{recipe['id']}/{direction}: animation source out of bounds",errors)
            check(len(m["ColorMaskLayers"])==1 and m["DisableGrayscale"] is False,f"{recipe['id']}/{direction}: recolor contract missing",errors)
        summaries.append({"id":recipe["id"],"article":recipe["articleType"],"rarity":recipe["rarity"],"static":"PASS","runtime":"NOT_TESTED","promotionState":"EXPERIMENTAL"})
    check(len(set(hashes.values()))==4,"prototype textures are not unique",errors)
    pack=ROOT/"test-packs"/"fashionsense"/"RNG-Clothing-V46-LowerBody-Runtime"
    manifest=json.loads((pack/"manifest.json").read_text())
    check(manifest["ContentPackFor"]=={"UniqueID":"PeacefulEnd.FashionSense","MinimumVersion":"7.5.0"},"pack dependency changed",errors)
    pants=sorted((pack/"Pants").glob("*/pants.json")); shoes=sorted((pack/"Shoes").glob("*/shoes.json"))
    check(len(pants)==2 and len(shoes)==2,"pack must contain exactly two pants and two shoes",errors)
    forbidden=("Skirts","Accessories","Shirts","CoatTails","Mantles")
    check(not any((pack/x).exists() for x in forbidden),"unsupported article leaked into pack",errors)
    for path in pants+shoes:
        data=json.loads(path.read_text()); stem="Pants" if path.name=="pants.json" else "Shoes"; texture=read_rgba_png(path.with_suffix(".png"))
        for direction in ("Front","Back","Right","Left"):
            m=data[direction+stem]; size=m[stem+"Size"]; max_frame=max(a["Frame"] for a in m["UniformAnimation"])
            columns=texture["width"]//size["Width"]; rows=texture["height"]//size["Length"]
            check(max_frame<columns*rows,f"{path}/{direction}: source frame outside atlas",errors)
    warnings += [
        "Static PASS is not a motion PASS; all four appearances remain EXPERIMENTAL.",
        "Rare boot shaft extension is frame-relative and must be checked during sitting, horse, tools, and special poses.",
        "Swimming/bathing success means a clean framework-driven hide/transition, not persistent garment visibility.",
        "Multiplayer equip/color synchronization remains NOT TESTED.",
    ]
    report={"status":"PASS_STATIC_CONTRACTS_RUNTIME_NOT_TESTED" if not errors else "FAIL","errors":errors,"warnings":warnings,"fashionSense":"7.5.0","stardew":"1.6.15.24356","counts":counts,"textures":hashes,"prototypes":summaries,"claims":{"static":not errors,"idle":False,"walk":False,"run":False,"tools":False,"sitting":False,"horse":False,"swimmingTransitions":False,"multiplayer":False,"recolor":False}}
    target=ROOT/"output"/"fashionsense"/"v46-lower-body-runtime"/"full_validation.json"; target.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"errors":errors,"warnings":warnings},indent=2)); raise SystemExit(1 if errors else 0)


if __name__=="__main__": main()
