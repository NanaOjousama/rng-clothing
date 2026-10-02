#!/usr/bin/env python3
from pathlib import Path
import json, sys
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SRC = HERE / "run_trucker_photo_zero123_01/construction_from_zero123_5321/template_frames"
OUT = HERE / "run_trucker_photo_zero123_01/semantic_trucker_01"
HEAD = ROOT / "experiments/pixellab/head_guides"
FIT = ROOT / "prototypes/photo_tailor_source_identity_01/trucker_wear_fit_proof_01/fit_contract.json"
VIEWS = ("front","right","back","left")
COLORS = {"outline":(52,50,53,255), "front_panel":(183,181,175,255),
          "rear_mesh":(137,145,144,255), "visor":(93,91,93,255),
          "strap":(112,105,104,255), "button":(75,71,73,255)}


def alpha_cells(im):
    return {(x,y) for y in range(im.height) for x in range(im.width) if im.getpixel((x,y))[3] > 15}


def bbox(cells):
    xs=[p[0] for p in cells]; ys=[p[1] for p in cells]
    return min(xs),min(ys),max(xs),max(ys)


def border(cells):
    return {p for p in cells if any((p[0]+dx,p[1]+dy) not in cells for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))}


def partition(view, cells):
    x0,y0,x1,y1=bbox(cells); w=x1-x0+1; h=y1-y0+1
    parts={k:set() for k in ("front_panel","rear_mesh","visor","strap","button","opening")}
    if view == "front":
        visor_y = y0 + round(h*0.76)
        cx0=x0+round(w*.20); cx1=x0+round(w*.80)
        for x,y in cells:
            if y >= visor_y: parts["visor"].add((x,y))
            elif cx0 <= x <= cx1: parts["front_panel"].add((x,y))
            else: parts["rear_mesh"].add((x,y))
    elif view in ("right","left"):
        forward_right = view == "right"
        split=x0+round(w*.52); visor_y=y0+round(h*.63)
        for x,y in cells:
            forward = x >= split if forward_right else x <= split
            if forward and y >= visor_y: parts["visor"].add((x,y))
            elif forward: parts["front_panel"].add((x,y))
            else: parts["rear_mesh"].add((x,y))
    else:
        parts["rear_mesh"] = set(cells)
        open_x0=x0+round(w*.31); open_x1=x0+round(w*.69)
        open_y0=y0+round(h*.58); open_y1=y0+round(h*.80)
        opening={(x,y) for x,y in cells if open_x0<=x<=open_x1 and open_y0<=y<=open_y1}
        parts["opening"] = opening
        parts["rear_mesh"] -= opening
        strap_y=min(y1,open_y1+1)
        parts["strap"]={(x,strap_y) for x in range(open_x0,open_x1+1) if (x,strap_y) in cells}
        parts["rear_mesh"] -= parts["strap"]
    top=min(y for x,y in cells); xs=[x for x,y in cells if y==top]
    if xs: parts["button"].add((round(sum(xs)/len(xs)),top))
    return parts

def render(parts_by_view):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'template_frames').mkdir(exist_ok=True)
    frames={}
    masks_doc={}
    for view in VIEWS:
        parts=parts_by_view[view]
        cells=set().union(*(parts[k] for k in ('front_panel','rear_mesh','visor','strap','button')))
        im=Image.new('RGBA',(26,26),(0,0,0,0))
        for name in ('rear_mesh','front_panel','visor','strap','button'):
            for x,y in parts[name]: im.putpixel((x,y),COLORS[name])
        for x,y in border(cells): im.putpixel((x,y),COLORS['outline'])
        frames[view]=im
        masks_doc[view]={k:sorted([list(p) for p in v]) for k,v in parts.items()}
        im.save(OUT/'template_frames'/f'{view}.png')
    return frames,masks_doc

def contact(frames,path,title):
    scale=9; tile=26*scale; pad=12
    out=Image.new('RGB',(pad+4*(tile+pad),tile+70),'white'); d=ImageDraw.Draw(out)
    d.text((10,8),title,fill='black')
    for i,v in enumerate(VIEWS):
        x=pad+i*(tile+pad); d.text((x+88,30),v.upper(),fill='black')
        src=frames[v].resize((tile,tile),Image.Resampling.NEAREST); out.paste(src,(x,50),src)
    out.save(path)

def paint_scaled(canvas,sprite,sx,sy,ox,oy):
    for y in range(sprite.height):
        for x in range(sprite.width):
            p=sprite.getpixel((x,y))
            if not p[3]: continue
            canvas.alpha_composite(Image.new('RGBA',(sx,sy),p),(ox+x*sx,oy+y*sy))

def wear_sheet(frames,path):
    fit=json.loads(FIT.read_text())['after']; base=12; cell=(312,360); pad=8
    sheet=Image.new('RGB',(4*cell[0]+5*pad,cell[1]+60),(239,238,233)); d=ImageDraw.Draw(sheet)
    d.text((8,8),'SEMANTIC TRUCKER TEMPLATE - STARDew FIT',fill='black')
    for i,v in enumerate(VIEWS):
        x0=pad+i*(cell[0]+pad); d.text((x0+135,28),v.upper(),fill='black')
        c=Image.new('RGBA',cell,(0,0,0,0))
        head=Image.open(HEAD/f'farmer_head_{v}_hair.png').convert('RGBA')
        paint_scaled(c,head,base,base,60,144)
        t=fit[v]; paint_scaled(c,frames[v],t['scaleX'],t['scaleY'],t['offsetX'],t['offsetY'])
        flat=Image.new('RGB',cell,(239,238,233)); flat.paste(c,(0,0),c); sheet.paste(flat,(x0,50))
    sheet.save(path)

def main():
    source={v:Image.open(SRC/f'{v}.png').convert('RGBA') for v in VIEWS}
    parts={v:partition(v,alpha_cells(source[v])) for v in VIEWS}
    frames,masks=render(parts)
    contact(frames,OUT/'01_semantic_construction.png','AI MULTIVIEW -> SEMANTIC TRUCKER CONSTRUCTION')
    wear_sheet(frames,OUT/'02_stardew_fit_preview.png')

    contract={
        'schema':'experimental-semantic-trucker-template/v1','status':'EXPERIMENTAL_REVIEW_REQUIRED',
        'family':'trucker_cap','frameSize':[26,26],
        'upstream':'Zero123++ single-photo multiview -> calibrated cardinal geometry',
        'semantics':['front_panel','rear_mesh','visor','button','opening','strap'],
        'inferred':['back opening/strap placement from trucker family rules'],
        'geometryPolicy':'outer alpha from AI candidate; semantic partition may remove inferred opening only',
        'parts':masks,
        'promotionRule':'Never auto-promote. Requires visual and in-game approval.'
    }
    (OUT/'construction_template_semantic.json').write_text(json.dumps(contract,indent=2)+'\n')
    print('OUTPUT',OUT)

if __name__=='__main__': main()
