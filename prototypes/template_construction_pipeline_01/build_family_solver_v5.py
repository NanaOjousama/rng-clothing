#!/usr/bin/env python3
from pathlib import Path
import json, math
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
V3=HERE/'run_trucker_photo_zero123_01/family_solver_v4/template_frames'
OUT=HERE/'run_trucker_photo_zero123_01/family_solver_v5'
HEAD=ROOT/'experiments/pixellab/head_guides'
FIT=ROOT/'prototypes/photo_tailor_source_identity_01/trucker_wear_fit_proof_01/fit_contract.json'
VIEWS=('front','right','back','left')
PAL={'outline':(48,45,48,255),'panel':(190,187,180,255),'mesh':(151,156,153,255),
     'visor':(101,98,97,255),'strap':(91,87,90,255),'button':(73,69,71,255)}

def cells(im): return {(x,y) for y in range(26) for x in range(26) if im.getpixel((x,y))[3]>15}
def bbox(ps):
    xs=[x for x,y in ps]; ys=[y for x,y in ps]; return min(xs),min(ys),max(xs),max(ys)
def border(ps): return {p for p in ps if any((p[0]+dx,p[1]+dy) not in ps for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))}
def refine_side(src):
    ps=cells(src); x0,y0,x1,y1=bbox(ps)
    # Rebuild crown from V3 silhouette but replace blunt visor with a taper.
    visor_cut=y0+round((y1-y0+1)*.70)
    crown={(x,y) for x,y in ps if y<visor_cut}
    base_y=max(y for x,y in crown)
    # V5: shorter visor, thicker root, cleaner crown-to-visor transition.
    wedge=set()
    rows=[(base_y-1, x1-5, x1+2),(base_y, x1-4, x1+4),(base_y+1, x1-2, x1+4)]
    for y,a,b in rows:
        for x in range(a,min(25,b)+1): wedge.add((x,y))
    shape=crown|wedge
    im=Image.new('RGBA',(26,26),(0,0,0,0)); split=x0+round((x1-x0+1)*.52)
    for x,y in shape:
        if (x,y) in wedge: c=PAL['visor']
        else: c=PAL['mesh'] if x<split else PAL['panel']
        im.putpixel((x,y),c)
    for x,y in border(cells(im)): im.putpixel((x,y),PAL['outline'])
    return im

def refine_back(src):
    ps=cells(src); x0,y0,x1,y1=bbox(ps)
    im=Image.new('RGBA',(26,26),(0,0,0,0))
    for x,y in ps: im.putpixel((x,y),PAL['mesh'])
    cx=round((x0+x1)/2); h=y1-y0+1; w=x1-x0+1
    oy0=y0+round(h*.56); oy1=y0+round(h*.80); half=max(2,round(w*.20))
    # Rounded/trapezoid opening: narrow top and bottom, widest middle.
    for y in range(oy0,oy1+1):
        rel=(y-oy0)/max(1,oy1-oy0)
        inset=1 if rel<.28 or rel>.78 else 0
        for x in range(cx-half+inset,cx+half-inset+1):
            im.putpixel((x,y),(0,0,0,0))
    strap_y=min(y1,oy1+1)
    for x in range(cx-half+1,cx+half):
        if (x,strap_y) in ps: im.putpixel((x,strap_y),PAL['strap'])
    for x,y in border(cells(im)): im.putpixel((x,y),PAL['outline'])
    return im
def contact(frames,path,title):
    scale=9; tile=26*scale; pad=12
    out=Image.new('RGB',(pad+4*(tile+pad),tile+70),'white'); d=ImageDraw.Draw(out)
    d.text((10,8),title,fill='black')
    for i,v in enumerate(VIEWS):
        x=pad+i*(tile+pad); d.text((x+88,30),v.upper(),fill='black')
        s=frames[v].resize((tile,tile),Image.Resampling.NEAREST); out.paste(s,(x,50),s)
    out.save(path)

def paint_scaled(canvas,sprite,sx,sy,ox,oy):
    for y in range(sprite.height):
        for x in range(sprite.width):
            p=sprite.getpixel((x,y))
            if p[3]: canvas.alpha_composite(Image.new('RGBA',(sx,sy),p),(ox+x*sx,oy+y*sy))

def wear_sheet(frames,path):
    fit=json.loads(FIT.read_text())['after']; base=12; cell=(312,360); pad=8
    sheet=Image.new('RGB',(4*cell[0]+5*pad,cell[1]+60),(239,238,233)); d=ImageDraw.Draw(sheet)
    d.text((8,8),'FAMILY SOLVER V5 - SHORTER VISOR + THICKER ROOT',fill='black')
    for i,v in enumerate(VIEWS):
        x0=pad+i*(cell[0]+pad); d.text((x0+135,28),v.upper(),fill='black')
        c=Image.new('RGBA',cell,(0,0,0,0)); head=Image.open(HEAD/f'farmer_head_{v}_hair.png').convert('RGBA')
        paint_scaled(c,head,base,base,60,144); t=fit[v]
        paint_scaled(c,frames[v],t['scaleX'],t['scaleY'],t['offsetX'],t['offsetY'])
        flat=Image.new('RGB',cell,(239,238,233)); flat.paste(c,(0,0),c); sheet.paste(flat,(x0,50))
    sheet.save(path)
def main():
    src={v:Image.open(V3/f'{v}.png').convert('RGBA') for v in VIEWS}
    frames={'front':src['front'].copy(),'right':refine_side(src['right']),'back':refine_back(src['back'])}
    frames['left']=frames['right'].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    OUT.mkdir(parents=True,exist_ok=True); (OUT/'template_frames').mkdir(exist_ok=True)
    for v in VIEWS: frames[v].save(OUT/'template_frames'/f'{v}.png')
    contact(frames,OUT/'01_family_solver_v4.png','TRUCKER SOLVER V5 - SHORTER VISOR / THICKER ROOT')
    wear_sheet(frames,OUT/'02_stardew_fit_preview.png')
    report={v:{'bbox':list(bbox(cells(frames[v]))),'opaque':len(cells(frames[v]))} for v in VIEWS}
    report['leftExactMirror']=list(frames['left'].getdata())==[frames['right'].getpixel((25-x,y)) for y in range(26) for x in range(26)]
    contract={'schema':'experimental-trucker-family-solver/v5','status':'EXPERIMENTAL_REVIEW_REQUIRED',
              'family':'trucker_cap','base':'solver_v4','changes':['shorten side visor by about 2 px','thicken visor root into crown','smooth crown-to-visor transition','retain v4 rounded back opening','left exact mirror of right'],
              'qc':report,'promotionRule':'Visual + in-game approval required.'}
    (OUT/'construction_template_solver_v4.json').write_text(json.dumps(contract,indent=2)+'\n')
    print(json.dumps(report,indent=2)); print('OUTPUT',OUT)

if __name__=='__main__': main()
