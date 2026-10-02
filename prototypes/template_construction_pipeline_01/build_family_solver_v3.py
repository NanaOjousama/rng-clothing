#!/usr/bin/env python3
from pathlib import Path
import json, math
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
AI=HERE/'run_trucker_photo_zero123_01/semantic_trucker_01/template_frames'
OUT=HERE/'run_trucker_photo_zero123_01/family_solver_v3'
HEAD=ROOT/'experiments/pixellab/head_guides'
FIT=ROOT/'prototypes/photo_tailor_source_identity_01/trucker_wear_fit_proof_01/fit_contract.json'
OCC=ROOT/'generator/data/headwear/vanilla_hat_occupancy_rules.json'
TRACE=ROOT/'prototypes/photo_tailor_source_identity_01/trucker_reference_trace_26_02/trace_report.json'
VIEWS=('front','right','back','left')
PAL={'outline':(48,45,48,255),'panel':(190,187,180,255),'mesh':(151,156,153,255),
     'visor':(101,98,97,255),'strap':(91,87,90,255),'button':(73,69,71,255)}
def clamp(v,a,b): return max(a,min(b,v))
def cells(im): return {(x,y) for y in range(im.height) for x in range(im.width) if im.getpixel((x,y))[3]>15}
def bbox(ps):
    xs=[x for x,y in ps]; ys=[y for x,y in ps]
    return min(xs),min(ys),max(xs),max(ys)
def dims(ps):
    x0,y0,x1,y1=bbox(ps); return (x1-x0+1,y1-y0+1)
def border(ps):
    return {p for p in ps if any((p[0]+dx,p[1]+dy) not in ps for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))}

def vanilla_mask(rows):
    return {(x,y) for y,row in enumerate(rows) for x,ch in enumerate(row) if ch=='#'}

def resample_mask(mask,target_w,target_h,center_x=12.5,top=3):
    x0,y0,x1,y1=bbox(mask); sw=x1-x0+1; sh=y1-y0+1
    out=set()
    for ty in range(target_h):
        sy=y0+min(sh-1,int((ty+.5)*sh/target_h))
        for tx in range(target_w):
            sx=x0+min(sw-1,int((tx+.5)*sw/target_w))
            if (sx,sy) in mask:
                ox=round(center_x-(target_w-1)/2)+tx
                out.add((ox,top+ty))
    return out
def blended_targets(ai_dims, vanilla_dims, trace_dims):
    # Stardew occupancy is the strongest pixel-space prior; AI/reference only stretch it moderately.
    vw,vh=vanilla_dims; aw,ah=ai_dims; tw,th=trace_dims
    w=round(vw*.58 + aw*.22 + tw*.20)
    h=round(vh*.62 + ah*.18 + th*.20)
    return clamp(w,8,24), clamp(h,7,20)

def semantic_paint(shape,view):
    im=Image.new('RGBA',(26,26),(0,0,0,0))
    x0,y0,x1,y1=bbox(shape); w=x1-x0+1; h=y1-y0+1
    split=x0+round((w-1)*.52)
    visor_cut=y0+round((h-1)*.72)
    for x,y in shape:
        if view=='front':
            if y>=visor_cut: c=PAL['visor']
            elif x0+round(w*.19)<=x<=x1-round(w*.19): c=PAL['panel']
            else: c=PAL['mesh']
        elif view in ('right','left'):
            forward=(x>=split) if view=='right' else (x<=split)
            if y>=visor_cut and forward: c=PAL['visor']
            else: c=PAL['panel'] if forward else PAL['mesh']
        else:
            c=PAL['mesh']
        im.putpixel((x,y),c)
    if view=='back':
        # Smaller rounded family opening, based on vanilla back occupancy rather than the AI void.
        cx=(x0+x1)//2; oy0=y0+round(h*.55); oy1=y0+round(h*.78)
        half=max(2,round(w*.22))
        for y in range(oy0,oy1+1):
            inset=1 if y==oy0 else 0
            for x in range(cx-half+inset,cx+half-inset+1):
                if 0<=x<26: im.putpixel((x,y),(0,0,0,0))
        sy=min(y1,oy1+1)
        for x in range(cx-half,cx+half+1):
            if 0<=x<26 and (x,sy) in shape: im.putpixel((x,sy),PAL['strap'])
    return im
def finalize_outline(im):
    ps=cells(im)
    for x,y in border(ps): im.putpixel((x,y),PAL['outline'])
    return im

def contact(frames,path,title):
    scale=9; tile=26*scale; pad=12
    out=Image.new('RGB',(pad+4*(tile+pad),tile+70),'white'); d=ImageDraw.Draw(out)
    d.text((10,8),title,fill='black')
    for i,v in enumerate(VIEWS):
        x=pad+i*(tile+pad); d.text((x+88,30),v.upper(),fill='black')
        src=frames[v].resize((tile,tile),Image.Resampling.NEAREST)
        out.paste(src,(x,50),src)
    out.save(path)

def paint_scaled(canvas,sprite,sx,sy,ox,oy):
    for y in range(sprite.height):
        for x in range(sprite.width):
            p=sprite.getpixel((x,y))
            if p[3]: canvas.alpha_composite(Image.new('RGBA',(sx,sy),p),(ox+x*sx,oy+y*sy))

def wear_sheet(frames,path):
    fit=json.loads(FIT.read_text())['after']; base=12; cell=(312,360); pad=8
    sheet=Image.new('RGB',(4*cell[0]+5*pad,cell[1]+60),(239,238,233)); d=ImageDraw.Draw(sheet)
    d.text((8,8),'FAMILY SOLVER V3 - VANILLA-PRIOR STARDew FIT',fill='black')
    for i,v in enumerate(VIEWS):
        x0=pad+i*(cell[0]+pad); d.text((x0+135,28),v.upper(),fill='black')
        c=Image.new('RGBA',cell,(0,0,0,0)); head=Image.open(HEAD/f'farmer_head_{v}_hair.png').convert('RGBA')
        paint_scaled(c,head,base,base,60,144)
        t=fit[v]; paint_scaled(c,frames[v],t['scaleX'],t['scaleY'],t['offsetX'],t['offsetY'])
        flat=Image.new('RGB',cell,(239,238,233)); flat.paste(c,(0,0),c); sheet.paste(flat,(x0,50))
    sheet.save(path)
def main():
    occ=json.loads(OCC.read_text())['families']['trucker']['views']
    trace=json.loads(TRACE.read_text())['traceMeta']
    ai={v:Image.open(AI/f'{v}.png').convert('RGBA') for v in VIEWS}
    frames={}; report={}
    for v in ('front','right','back'):
        ai_d=dims(cells(ai[v]))
        vm=vanilla_mask(occ[v]['alphaRows'])
        vd=dims(vm)
        td=tuple(trace[v]['targetSize'])
        target=blended_targets(ai_d,vd,td)
        shape=resample_mask(vm,target[0],target[1],center_x=12.5,top=3)
        frames[v]=finalize_outline(semantic_paint(shape,v))
        report[v]={'aiSize':list(ai_d),'vanillaSize':list(vd),'referenceTraceSize':list(td),'solvedSize':list(target)}
    frames['left']=frames['right'].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    report['left']={'mirrorOf':'right','solvedSize':report['right']['solvedSize']}

    OUT.mkdir(parents=True,exist_ok=True); (OUT/'template_frames').mkdir(exist_ok=True)
    for v in VIEWS: frames[v].save(OUT/'template_frames'/f'{v}.png')
    contact(frames,OUT/'01_family_solver_v3.png','AI + REAL REFERENCE + VANILLA OCCUPANCY -> TRUCKER SOLVER V3')
    wear_sheet(frames,OUT/'02_stardew_fit_preview.png')
    contract={'schema':'experimental-trucker-family-solver/v3','status':'EXPERIMENTAL_REVIEW_REQUIRED','family':'trucker_cap',
              'authorities':{'ai':'proportion evidence only','referenceTrace':'family envelope evidence','vanillaHat16':'pixel-space occupancy prior'},
              'measurements':report,'rules':['vanilla occupancy strongest prior','AI cannot directly author final pixels','real trace moderates dimensions','left is exact mirror of right','back opening reconstructed from family grammar'],
              'promotionRule':'Visual + in-game approval required before template registration.'}
    (OUT/'construction_template_solver_v3.json').write_text(json.dumps(contract,indent=2)+'\n')
    print(json.dumps(report,indent=2)); print('OUTPUT',OUT)

if __name__=='__main__': main()
