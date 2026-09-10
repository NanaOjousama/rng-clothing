#!/usr/bin/env python3
"""Generate six V4.6B lower-body article-readability diagnostics."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from generator.png_utils import RGBA, blank_image, blit, draw_rect, draw_text, nearest_scale, read_rgba_png, write_rgba_png
from generator.renderers.fashionsense import appearance_json_v46b, render_v46b
from generator.v46b import generate_v46b_prototypes


OUT=ROOT/"output"/"fashionsense"/"v46b-lower-body-readability"
PACK=ROOT/"test-packs"/"fashionsense"/"RNG-Clothing-V46B-LowerBody-Readability"
COMPARE=ROOT/"output"/"comparisons"/"V46B_LOWER_BODY_ARTICLES.png"
GAMEPLAY=ROOT/"output"/"comparisons"/"V46B_LOWER_BODY_GAMEPLAY.png"
FARMER=Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/farmer_base.png")
BG:RGBA=(232,223,209,255); TILE:RGBA=(205,197,184,255); INK:RGBA=(48,44,41,255); BORDER:RGBA=(70,63,58,255)
# Fashion Sense 7.5 / Stardew Farmer idle contract:
# FacingDirection 2=down/front uses frame 0; 1=right uses frame 6;
# 0=up/back uses frame 12; 3=left reuses frame 6 with the left model.
DIRECTION_FRAMES=(("front",0),("right",6),("back",12),("left",6))


def _json(path,value): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def _slug(value): return "_".join(re.sub(r"[^a-z0-9]+"," ",value.lower()).split())
def _folder(value): return "".join(w.title() for w in _slug(value).split("_"))


def _default_map(recipe):
    defaults={
        "denim_cream":{54:(37,48,62,255),102:(55,73,94,255),154:(83,109,139,255),205:(132,156,181,255)},
        "forest_leather":{54:(35,43,31,255),102:(52,65,44,255),154:(76,93,64,255),205:(119,135,96,255)},
        "warm_neutral":{54:(72,52,36,255),102:(119,88,58,255),154:(174,139,99,255),205:(215,185,143,255)},
        "rust_sage":{54:(70,38,29,255),102:(111,56,39,255),154:(157,91,58,255),205:(199,135,91,255)},
        "sage_tan":{54:(48,60,42,255),102:(76,91,63,255),154:(112,132,94,255),205:(157,174,132,255)},
        "burgundy_cream":{54:(56,28,35,255),102:(88,36,46,255),154:(130,55,69,255),205:(176,93,104,255)}
    }
    return defaults[recipe["paletteStory"]]


def _colored(recipe,frame):
    mapping=_default_map(recipe)
    return [[mapping.get(p[0],p) if p[3] and p[0]==p[1]==p[2] else p for p in row] for row in frame]


def _farmer_frame(pixels,index):
    x0=(index%6)*16; y0=(index//6)*32
    return [list(row[x0:x0+16]) for row in pixels[y0:y0+32]]


def _hflip(pixels):
    return [list(reversed(row)) for row in pixels]


def _composite(recipe,render,direction,index,farmer):
    body_source=_farmer_frame(farmer,index)
    garment_source=_colored(recipe,render.frames[direction][index])
    # Stardew reuses horizontal frame 6 for both directions. FS 7.5 draws the
    # LeftPants model with Flipped=true; mirror both layers in previews too.
    if direction=="left":
        body_source=_hflip(body_source); garment_source=_hflip(garment_source)
    body=nearest_scale(body_source,4)
    garment=nearest_scale(garment_source,2)
    # Official Pants BodyPosition -1 at Scale 4 is four display pixels lower
    # than the base. Corrected Scale-2 BodyPosition 30 preserves that offset.
    blit(body,garment,0,4); return body


def _tile(canvas,image,x,y):
    draw_rect(canvas,x-2,y-2,len(image[0])+4,len(image)+4,BORDER); draw_rect(canvas,x-1,y-1,len(image[0])+2,len(image)+2,TILE); blit(canvas,image,x,y)


def _direction_sheet(recipe,render,farmer,diagnostic=False):
    scale=8 if diagnostic else 1
    if diagnostic:
        sw,sh=256,512; top=47; canvas=blank_image(20+4*(sw+17),top+sh+15,BG)
        draw_text(canvas,f"{recipe['name']} - {recipe['articleType']} - {recipe['rarity']}",7,7,color=INK); draw_text(canvas,"32X64 LOGICAL AT SCALE 2 - 8X NEAREST DIAGNOSTIC",7,21,color=INK)
        for i,(direction,index) in enumerate(DIRECTION_FRAMES):
            x=10+i*(sw+17); draw_text(canvas,direction,x,34,color=INK); _tile(canvas,nearest_scale(_colored(recipe,render.frames[direction][index]),scale),x,top)
    else:
        sw,sh=64,128; top=47; canvas=blank_image(25+4*(sw+28),top+sh+18,BG)
        draw_text(canvas,f"{recipe['name']} - GAMEPLAY FOOTPRINT - EXPERIMENTAL",7,7,color=INK); draw_text(canvas,"COMPOSITE PREVIEW FROM INSTALLED FARMER BASE",7,21,color=INK)
        for i,(direction,index) in enumerate(DIRECTION_FRAMES):
            x=12+i*(sw+28); draw_text(canvas,direction,x,34,color=INK); _tile(canvas,_composite(recipe,render,direction,index,farmer),x,top)
    return canvas


def _gameplay_collection(rendered,farmer):
    cell_w=112; cell_h=177; canvas=blank_image(6*cell_w,45+cell_h,BG)
    draw_text(canvas,"V4.6B LOWER-BODY ARTICLE READABILITY - GAMEPLAY FOOTPRINT",8,8,color=INK); draw_text(canvas,"PANTS | PANTS | SHORTS | SHORTS | SKIRT | SKIRT",8,22,color=INK)
    for i,(recipe,render) in enumerate(rendered):
        x=i*cell_w+23; y=74; draw_text(canvas,recipe["articleType"],x,43,color=INK); draw_text(canvas,recipe["rarity"],x,56,color=INK)
        _tile(canvas,_composite(recipe,render,"front",0,farmer),x,y); draw_text(canvas,"EXPERIMENTAL",i*cell_w+11,y+136,color=INK)
    return canvas


def _article_comparison(rendered,farmer):
    # Equal gameplay footprint, three construction views for every article.
    cell_w=105; cell_h=150; left=164; top=50
    canvas=blank_image(left+6*cell_w,top+3*cell_h+12,BG)
    draw_text(canvas,"V4.6B ARTICLE IDENTITY - FRONT / SIDE / BACK",8,8,color=INK); draw_text(canvas,"DIRECT 32X64 LOGICAL ART AT SCALE 2",8,22,color=INK)
    for col,(recipe,render) in enumerate(rendered):
        x=left+col*cell_w+18; draw_text(canvas,recipe["articleType"],x,36,color=INK)
        for row,(label,direction,index) in enumerate((("FRONT","front",0),("SIDE","right",6),("BACK","back",12))):
            y=top+row*cell_h; _tile(canvas,_composite(recipe,render,direction,index,farmer),x,y)
            if col==0: draw_text(canvas,label,10,y+57,color=INK)
    return canvas


def main():
    farmer=read_rgba_png(FARMER)["pixels"]; recipes=generate_v46b_prototypes(); rendered=[]
    _json(ROOT/"output"/"recipes"/"v46b_lower_body_readability.json",{"generatorVersion":"4.6B","count":6,"recipes":recipes})
    for recipe in recipes:
        render=render_v46b(recipe); rendered.append((recipe,render)); slug=_slug(recipe["name"]); target=OUT/slug
        write_rgba_png(target/f"{slug}.png",render.texture)
        write_rgba_png(target/f"{slug}-directions-8x.png",_direction_sheet(recipe,render,farmer,True))
        write_rgba_png(target/f"{slug}-gameplay-size.png",_direction_sheet(recipe,render,farmer,False))
        _json(target/f"{slug}-summary.json",{"recipe":recipe,"logicalFrame":{"width":32,"height":64,"scale":2},"identityValidation":render.identity,"staticErrors":list(render.static_errors),"runtimeStatus":"EXPERIMENTAL","runtimeEvidence":"NOT_TESTED"})
        dest=PACK/"Pants"/_folder(recipe["name"]); _json(dest/"pants.json",appearance_json_v46b(recipe,render)); write_rgba_png(dest/"pants.png",render.texture)
    comparison=_article_comparison(rendered,farmer); gameplay=_gameplay_collection(rendered,farmer)
    write_rgba_png(COMPARE,comparison); write_rgba_png(GAMEPLAY,gameplay); write_rgba_png(OUT/"V46B_LOWER_BODY_ARTICLES.png",comparison); write_rgba_png(OUT/"V46B_LOWER_BODY_GAMEPLAY.png",gameplay)
    _json(PACK/"manifest.json",{"Name":"RNG Clothing V4.6B Lower-Body Readability","Author":"RNG Clothing Experiment","Version":"0.1.1","Description":"Experimental Scale-2 diagnostic pack for two Pants, two Shorts, and two Skirts, with corrected full-frame BodyPosition. Shoes excluded.","UniqueID":"RNGClothing.FashionSense.V46BLowerBodyReadability","UpdateKeys":[],"ContentPackFor":{"UniqueID":"PeacefulEnd.FashionSense","MinimumVersion":"7.5.0"}})
    _json(PACK/"i18n"/"default.json",{key:value for r in recipes for key,value in ((f"appearance.{r['id']}.name",r["name"]),(f"appearance.{r['id']}.description",r["description"]))})
    (PACK/"README.md").write_text("""# RNG Clothing V4.6B Lower-Body Readability\n\nExperimental Fashion Sense 7.5.0 test pack. Contains exactly two Pants, two Shorts, and two Skirts; Fashion Sense exposes all six through its Pants category. Custom Shoes are deliberately absent.\n\nVersion 0.1.1 corrects the shared Scale-2 full-frame anchor from the invalid `(0,-2)` value to the Fashion Sense origin-equivalent `BodyPosition (0,30)`. Replace any earlier V4.6B copy before retesting.\n\nCopy this whole folder into `Stardew Valley/Mods`, restart through SMAPI, and use a Hand Mirror (`fs_add_mirror` if needed). If replacing assets during a running test, use `fs_reload RNGClothing.FashionSense.V46BLowerBodyReadability`.\n\nAll appearances are `EXPERIMENTAL`. Complete `reports/V46B_RUNTIME_TEST_CHECKLIST.md` before any runtime promotion. Because V4.6B uses direction-specific full-frame blocks, the native textures are intentionally larger than V4.6.\n""",encoding="utf-8")
    _json(OUT/"validation.json",{"status":"GENERATED_STATIC_VALIDATION_PENDING","count":6,"counts":{"PANTS":2,"SHORTS":2,"SKIRT":2},"shoesIncluded":False,"runtimeStatus":"EXPERIMENTAL","installedAutomatically":False})
    print("Generated six V4.6B EXPERIMENTAL lower-body readability prototypes")


if __name__=="__main__": main()
