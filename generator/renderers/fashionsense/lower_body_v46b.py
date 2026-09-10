"""Scale-2, 2x-density article grammars for V4.6B lower bodies."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from generator.png_utils import RGBA, blank_image
from generator.v46b.engine import validate_v46b_recipe


ROOT=Path(__file__).resolve().parents[3]
CONTRACT=ROOT/"generator"/"data"/"fashionsense"/"v46b"/"article_frame_contracts.json"
DIRECTIONS=("front","back","right","left")
MASK={"deep":(54,54,54,255),"shadow":(102,102,102,255),"base":(154,154,154,255),"light":(205,205,205,255)}
FIXED={"outline":(38,32,31,255),"denim":(63,86,111,255),"forest":(67,82,57,255),"leather":(91,57,39,255),"rust":(142,77,48,255),"sage":(104,121,84,255),"burgundy":(112,48,60,255),"cream":(222,204,166,255)}


@dataclass(frozen=True)
class V46BRender:
    recipe: dict
    contract: dict
    texture: list[list[RGBA]]
    frames: dict[str, dict[int, list[list[RGBA]]]]
    regions: dict[str, dict[int, dict[tuple[int,int],str]]]
    identity: dict[str, dict]
    static_errors: tuple[str,...]
    runtime_status: str="EXPERIMENTAL"


def load_contract(): return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _cells(rows): return {(x,row["y"]) for row in rows for a,b in row["spans"] for x in range(a,b+1)}
def _bounds(cells):
    xs=[x for x,_ in cells]; ys=[y for _,y in cells]; return min(xs),min(ys),max(xs),max(ys)
def _neighbors(cell):
    x,y=cell; return ((x-1,y),(x+1,y),(x,y-1),(x,y+1))


def _row_bounds(cells,y):
    xs=[x for x,yy in cells if yy==y]
    return (min(xs),max(xs)) if xs else None


def _paint_base(cells,center,direction):
    regions={}
    side=direction in {"right","left"}
    for x,y in cells:
        if side: regions[(x,y)]="sideMass"
        elif x<center: regions[(x,y)]="leftLeg"
        else: regions[(x,y)]="rightLeg"
    return regions


def _pants_regions(recipe,direction,entry):
    env=_cells(entry["highDensityEnvelope"])
    if not env: return {}
    top=entry["top"]; bottom=entry["bottom"]; center=entry["centerX2"]
    length=recipe["construction"]["length"]
    reserve={"full":4,"ankle":6,"cropped":10}[length]
    end=max(top+10,bottom-reserve)
    cells={(x,y) for x,y in env if top<=y<=end}
    # Fitted/straight/tapered geometry follows the motion envelope; relaxed adds
    # only one HD cell at lower outer edges, never a 2x copied contour.
    if recipe["construction"]["fit"]=="relaxed":
        for y in range(top+5,end+1):
            row=_row_bounds(cells,y)
            if row:
                cells.add((max(0,row[0]-1),y)); cells.add((min(31,row[1]+1),y))
    regions=_paint_base(cells,center,direction)
    for x,y in list(cells):
        if y<=top+1: regions[(x,y)]="waistband"
    if direction in {"front","back"}:
        seam="centerFront" if direction=="front" else "centerBack"
        for y in range(top+4,end+1):
            row=_row_bounds(cells,y)
            if not row: continue
            for x in (center-1,center):
                if (x,y) in cells: regions[(x,y)]=seam
        # Paired cuff identities and a tiny termination notch stop the pants
        # reading as one horizontal skirt slab.
        for x,y in list(cells):
            if y>=end-1: regions[(x,y)]="leftCuff" if x<center else "rightCuff"
        for x in (center-1,center):
            cells.discard((x,end)); regions.pop((x,end),None)
    else:
        edge_from_left=direction=="right"
        for y in range(top+4,end-2):
            row=_row_bounds(cells,y)
            if row:
                x=row[0]+1 if edge_from_left else row[1]-1
                if (x,y) in cells: regions[(x,y)]="outerLegSeam"
        for x,y in list(cells):
            if y>=end-1: regions[(x,y)]="sideCuff"
    if recipe["construction"]["construction"] in {"paneled","reinforced"}:
        knee=top+round((end-top)*.58)
        for x,y in list(cells):
            if knee-1<=y<=knee+1 and abs(x-center)>=2: regions[(x,y)]="kneePanel"
            elif (x<=min(xx for xx,_ in cells)+2 or x>=max(xx for xx,_ in cells)-2) and top+4<y<end-2: regions[(x,y)]="outerPanel"
    return {cell:regions[cell] for cell in cells}


def _shorts_regions(recipe,direction,entry):
    env=_cells(entry["highDensityEnvelope"])
    if not env: return {}
    top=entry["top"]; bottom=entry["bottom"]; center=entry["centerX2"]
    length={"short":7,"mid":9,"knee":12}[recipe["construction"]["length"]]
    end=min(top+length,bottom-7)
    cells={(x,y) for x,y in env if top<=y<=end}
    if recipe["construction"]["fit"] in {"relaxed","wide"}:
        for y in range(top+3,end+1):
            row=_row_bounds(cells,y)
            if row:
                cells.add((max(0,row[0]-1),y)); cells.add((min(31,row[1]+1),y))
    regions=_paint_base(cells,center,direction)
    for x,y in list(cells):
        if y<=top+1: regions[(x,y)]="waistband"
    if direction in {"front","back"}:
        for y in range(top+3,end+1):
            for x in (center-1,center):
                if (x,y) in cells: regions[(x,y)]="inseam"
        # Two high leg openings: separate only below the crotch, leaving no
        # accidental skin hole at the waistband/hip.
        for y in range(end-2,end+1):
            for x in (center-1,center): cells.discard((x,y)); regions.pop((x,y),None)
        for x,y in list(cells):
            if y>=end-1: regions[(x,y)]="leftHem" if x<center else "rightHem"
    else:
        for y in range(top+3,end-1):
            row=_row_bounds(cells,y)
            if row:
                x=row[0]+1 if direction=="right" else row[1]-1
                if (x,y) in cells: regions[(x,y)]="sideSeam"
        for x,y in list(cells):
            if y>=end-1: regions[(x,y)]="sideHem"
    if recipe["construction"]["construction"]=="utility":
        for x,y in list(cells):
            if top+3<=y<=top+6 and (x<=center-4 or x>=center+3): regions[(x,y)]="utilityPanel"
    return {cell:regions[cell] for cell in cells}


def _skirt_regions(recipe,direction,entry):
    seed=_cells(entry["pantsSeed"])
    if not seed: return {}
    seed={(x*2+dx,y*2+dy) for x,y in seed for dx in (0,1) for dy in (0,1)}
    top=min(y for _,y in seed); center=entry["centerX2"]
    sx0=min(x for x,_ in seed); sx1=max(x for x,_ in seed)
    length=9 if recipe["construction"]["length"]=="short" else 13
    end=min(61,top+length)
    silhouette=recipe["construction"]["silhouette"]; side=direction in {"right","left"}
    cells=set(); regions={}
    for y in range(top,end+1):
        t=(y-top)/max(1,end-top)
        if silhouette=="straight": spread=0
        elif silhouette in {"a_line","pleated"}: spread=round(t*(1 if side else 3))
        else: spread=round(t*(2 if side else 4))
        left=max(0,sx0-spread+(1 if side else 0)); right=min(31,sx1+spread-(1 if side else 0))
        for x in range(left,right+1):
            cells.add((x,y)); regions[(x,y)]="skirtMass"
    for x,y in cells:
        if y<=top+1: regions[(x,y)]="waistband"
        elif y>=end-1: regions[(x,y)]="skirtHem"
        elif x==min(xx for xx,yy in cells if yy==y): regions[(x,y)]="skirtLeftEdge"
        elif x==max(xx for xx,yy in cells if yy==y): regions[(x,y)]="skirtRightEdge"
    if silhouette in {"pleated","soft_flare"}:
        offsets=(-4,0,4) if not side else (-2,2)
        for off in offsets:
            for y in range(top+3,end-1):
                x=center+off+(1 if off>0 and (y-top)%4==0 else 0)
                if (x,y) in cells: regions[(x,y)]="skirtFold"
    return regions


def _build_regions(recipe,direction,entry):
    if recipe["articleType"]=="PANTS": return _pants_regions(recipe,direction,entry)
    if recipe["articleType"]=="SHORTS": return _shorts_regions(recipe,direction,entry)
    return _skirt_regions(recipe,direction,entry)


def _region_color(recipe,region,cell,regions,direction):
    x,y=cell; cells=set(regions); exterior=any(n not in cells for n in _neighbors(cell))
    if exterior: return FIXED["outline"]
    if region in {"centerFront","centerBack","inseam","outerLegSeam","sideSeam","skirtFold"}: return MASK["deep"]
    if region in {"leftCuff","rightCuff","sideCuff","leftHem","rightHem","sideHem","skirtHem"}: return MASK["shadow"]
    if region=="waistband":
        return FIXED["leather"] if recipe["construction"].get("waist")=="contrast" else MASK["deep"]
    if region in {"outerPanel","kneePanel","utilityPanel"}:
        return FIXED["forest"] if recipe["articleType"]=="PANTS" else FIXED["rust"]
    # Coherent upper-left light bias, restrained to connected planes.
    return MASK["light"] if x<14 and y%5 in {0,1} else MASK["base"] if x<18 else MASK["shadow"]


def _render_frame(recipe,direction,regions):
    frame=blank_image(32,64)
    for cell,region in regions.items():
        x,y=cell; frame[y][x]=_region_color(recipe,region,cell,regions,direction)
    return frame


def _place(texture,frame,index,block_y):
    x0=(index%6)*32; y0=block_y+(index//6)*64
    for y,row in enumerate(frame): texture[y0+y][x0:x0+32]=list(row)


def _components(cells):
    unseen=set(cells); count=0
    while unseen:
        count+=1; stack=[unseen.pop()]
        while stack:
            cell=stack.pop()
            for n in _neighbors(cell):
                if n in unseen: unseen.remove(n); stack.append(n)
    return count


def _identity(recipe,all_regions):
    # Authoritative representative idle sources from the installed FS 7.5
    # SimplePantsTemplate: down/front 0, right 6, up/back 12, left 6.
    metrics={}; reps={"front":0,"right":6,"back":12,"left":6}
    for direction,index in reps.items():
        regions=all_regions[direction][index]; cells=set(regions); names=set(regions.values())
        if not cells: metrics[direction]={"passes":False,"errors":["empty representative frame"]}; continue
        x0,y0,x1,y1=_bounds(cells); errors=[]; article=recipe["articleType"]
        if article=="PANTS":
            if y1-y0+1<12: errors.append("pants lack long hip-to-termination continuation")
            if direction in {"front","back"} and not ({"leftCuff","rightCuff"} <= names): errors.append("paired cuffs/leg channels missing")
            if direction in {"front","back"} and not ({"centerFront","centerBack"}&names): errors.append("inseam/center construction missing")
            if direction in {"right","left"} and "outerLegSeam" not in names: errors.append("side trouser seam missing")
        elif article=="SHORTS":
            if y1-y0+1>13: errors.append("shorts extend into pants-length range")
            if direction in {"front","back"} and not ({"leftHem","rightHem"}<=names): errors.append("paired short hems missing")
            if direction in {"front","back"} and not any((x,y1) not in cells for x in range(14,18)): errors.append("shorts termination lacks center split")
        else:
            if _components(cells)!=1: errors.append("skirt mass is not connected")
            if "inseam" in names or "leftCuff" in names: errors.append("skirt contains false pant construction")
            if "skirtHem" not in names: errors.append("skirt hem missing")
            if direction in {"front","back"} and not any((x,y1) in cells for x in range(14,18)): errors.append("skirt hem is unintentionally split")
        metrics[direction]={"passes":not errors,"errors":errors,"bounds":[x0,y0,x1,y1],"components":_components(cells),"regions":sorted(names),"opaqueCells":len(cells)}
    return metrics


def render_v46b(recipe):
    errors=list(validate_v46b_recipe(recipe)); contract=load_contract(); info=contract["frame"]
    texture=blank_image(info["textureWidth"],info["textureHeight"]); frames={}; regions={}
    for direction in DIRECTIONS:
        frames[direction]={}; regions[direction]={}; block=contract["directionBlocks"][direction]
        for index in range(126):
            region_map=_build_regions(recipe,direction,contract["frames"][str(index)])
            frame=_render_frame(recipe,direction,region_map); regions[direction][index]=region_map; frames[direction][index]=frame; _place(texture,frame,index,block)
    identity=_identity(recipe,regions)
    for direction,result in identity.items():
        errors.extend(f"{direction}: {e}" for e in result["errors"])
    alpha={p[3] for row in texture for p in row}
    if alpha-{0,255}: errors.append("alpha is not binary")
    return V46BRender(recipe,contract,texture,frames,regions,identity,tuple(errors))


def color_mask_layers(recipe):
    defaults={"denim_cream":[83,109,139],"forest_leather":[76,93,64],"warm_neutral":[174,139,99],"rust_sage":[157,91,58],"sage_tan":[112,132,94],"burgundy_cream":[130,55,69]}
    return [{"Name":"Primary fabric","DefaultColor":defaults[recipe["paletteStory"]],"Values":[[v,v,v] for v in (54,102,154,205)]}]


def appearance_json_v46b(recipe,render):
    root={"Name":recipe["name"],"Format":"7.5.0","Tags":["RNG Clothing","V4.6B","Readability Diagnostic",recipe["articleType"].title(),recipe["rarity"]]}
    for direction in DIRECTIONS:
        root[direction.title()+"Pants"]={"Scale":2.0,"DisableNativeOffset":True,"DisableGrayscale":False,"ColorMaskLayers":color_mask_layers(recipe),"StartingPosition":{"X":0,"Y":render.contract["directionBlocks"][direction]},"BodyPosition":render.contract["bodyPosition"],"PantsSize":{"Width":32,"Length":64},"Flipped":render.contract["directionFlips"][direction],"HideWhileSwimming":True,"HideWhileWearingBathingSuit":True,"HideLegs":False,"HideShadow":False,"UniformAnimation":render.contract["uniformAnimation"][direction]}
    return root
