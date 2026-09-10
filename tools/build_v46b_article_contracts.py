#!/usr/bin/env python3
"""Build high-density lower-body envelopes from installed Farmer/FS data."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from generator.png_utils import read_rgba_png


V46=ROOT/"generator"/"data"/"fashionsense"/"v46"/"lower_body_frame_contracts.json"
OUT=ROOT/"generator"/"data"/"fashionsense"/"v46b"/"article_frame_contracts.json"
FARMER=Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer")
MALE=FARMER/"farmer_base.png"; FEMALE=FARMER/"farmer_girl_base.png"


def cells_from_rows(rows):
    return {(x,row["y"]) for row in rows for a,b in row["spans"] for x in range(a,b+1)}


def rows_from_cells(cells):
    result=[]
    for y in sorted({y for _,y in cells}):
        xs=sorted(x for x,yy in cells if yy==y); spans=[]; start=last=xs[0]
        for x in xs[1:]:
            if x==last+1: last=x
            else: spans.append([start,last]); start=last=x
        spans.append([start,last]); result.append({"y":y,"spans":spans})
    return result


def frame_alpha(pixels,frame):
    x0=(frame%6)*16; y0=(frame//6)*32
    return {(x,y) for y in range(32) for x in range(16) if pixels[y0+y][x0+x][3]}


def upscale_coverage(cells):
    return {(x*2+dx,y*2+dy) for x,y in cells for dx in (0,1) for dy in (0,1)}


def main():
    source=json.loads(V46.read_text(encoding="utf-8"))["contracts"]["FITTED_PANTS"]
    male=read_rgba_png(MALE)["pixels"]; female=read_rgba_png(FEMALE)["pixels"]
    # Fashion Sense draws appearances at position+origin with draw origin
    # origin+BodyPosition. The normal Farmer world origin is (0,32). Preserve
    # the official Scale-4 Pants position (BodyPosition 0,-1) at Scale 2:
    #   (origin + targetBody) * 2 == (origin + sourceBody) * 4
    # so targetBody = (0,30), not the naive (0,-2).
    native_origin={"X":0,"Y":32}; source_scale=4; target_scale=2
    source_body=source["models"]["front"]["bodyPosition"]
    target_body={axis:int((native_origin[axis]+source_body[axis])*source_scale/target_scale-native_origin[axis]) for axis in ("X","Y")}
    frames={}
    for frame in range(126):
        seed=cells_from_rows(source["coverage"][str(frame)]["rowSpans"])
        if not seed:
            frames[str(frame)]={"pantsSeed":[],"lowerBodyEnvelope":[],"highDensityEnvelope":[],"top":None,"bottom":None,"centerX2":15,"intentionallyEmpty":True}
            continue
        body=frame_alpha(male,frame)|frame_alpha(female,frame)
        top=min(y for _,y in seed); sx0=min(x for x,_ in seed); sx1=max(x for x,_ in seed)
        # Central lower-body window excludes most hand/tool fragments but allows stride.
        lower={(x,y) for x,y in body if y>=top and sx0-2<=x<=sx1+2}
        # Always preserve the framework's authoritative pants coverage seed.
        lower|=seed
        hd=upscale_coverage(lower)
        frames[str(frame)]={
            "pantsSeed":rows_from_cells(seed),
            "lowerBodyEnvelope":rows_from_cells(lower),
            "highDensityEnvelope":rows_from_cells(hd),
            "top":min(y for _,y in hd),"bottom":max(y for _,y in hd),
            "centerX2":int(round(((sx0+sx1+1)/2)*2)),
            "intentionallyEmpty":False,
        }
    block_height=source["texture"]["height"]*2
    data={
        "formatVersion":"4.6B",
        "fashionSenseVersion":"7.5.0",
        "stardewVersion":"1.6.15.24356",
        "source":{"v46Contract":str(V46.relative_to(ROOT)),"v46Sha256":hashlib.sha256(V46.read_bytes()).hexdigest(),"maleBase":str(MALE),"maleBaseSha256":hashlib.sha256(MALE.read_bytes()).hexdigest(),"femaleBase":str(FEMALE),"femaleBaseSha256":hashlib.sha256(FEMALE.read_bytes()).hexdigest()},
        "frame":{"width":32,"height":64,"scale":2,"columns":6,"capacityPerDirection":126,"blockWidth":192,"blockHeight":block_height,"textureWidth":192,"textureHeight":block_height*4},
        "bodyPosition":target_body,
        "anchorContract":{"nativeFarmerOrigin":native_origin,"sourceScale":source_scale,"sourceBodyPosition":source_body,"targetScale":target_scale,"worldDisplayDeltaFromVanilla":{"X":0,"Y":4},"formula":"(origin + targetBody) * targetScale == (origin + sourceBody) * sourceScale"},
        "directionBlocks":{"front":0,"back":block_height,"right":block_height*2,"left":block_height*3},
        # The official FS 7.5 SimplePantsTemplate reuses horizontal Farmer
        # frame 6 and flips only the LeftPants model at draw time.
        "directionFlips":{"front":False,"back":False,"right":False,"left":True},
        "uniformAnimation":{direction:model["uniformAnimation"] for direction,model in source["models"].items()},
        "frames":frames,
        "method":"2x coverage envelope only; finished geometry is re-resolved by article grammar",
        "runtimeStatus":"EXPERIMENTAL"
    }
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    visible=sum(not f["intentionallyEmpty"] for f in frames.values())
    print(f"Wrote V4.6B high-density contracts for {visible}/126 visible source frames")


if __name__=="__main__": main()
