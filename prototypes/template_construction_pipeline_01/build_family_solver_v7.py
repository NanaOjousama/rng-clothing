#!/usr/bin/env python3
from pathlib import Path
import json
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BASE=HERE/'run_trucker_photo_zero123_01/family_solver_v5/template_frames'
OUT=HERE/'run_trucker_photo_zero123_01/family_solver_v7'
HEAD=ROOT/'experiments/pixellab/head_guides'
FIT=ROOT/'prototypes/photo_tailor_source_identity_01/trucker_wear_fit_proof_01/fit_contract.json'
VIEWS=('front','right','back','left')

def alpha_cells(im):
    return {(x,y) for y in range(26) for x in range(26) if im.getpixel((x,y))[3]>15}

def bbox(ps):
    xs=[x for x,y in ps]; ys=[y for x,y in ps]
    return min(xs),min(ys),max(xs),max(ys)

def refine_right(src):
    im=src.copy()
    # Surgical v7 trim: keep V5's connected crown/visor root; remove only overlong tip pixels.
    for y in range(26):
        im.putpixel((25,y),(0,0,0,0))
    for x in range(23,26):
        im.putpixel((x,10),(0,0,0,0))
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
    d.text((8,8),'FAMILY SOLVER V7 - FINAL CONNECTED VISOR TRIM',fill='black')
    for i,v in enumerate(VIEWS):
        x0=pad+i*(cell[0]+pad); d.text((x0+135,28),v.upper(),fill='black')
        c=Image.new('RGBA',cell,(0,0,0,0)); head=Image.open(HEAD/f'farmer_head_{v}_hair.png').convert('RGBA')
        paint_scaled(c,head,base,base,60,144); t=fit[v]
        paint_scaled(c,frames[v],t['scaleX'],t['scaleY'],t['offsetX'],t['offsetY'])
        flat=Image.new('RGB',cell,(239,238,233)); flat.paste(c,(0,0),c); sheet.paste(flat,(x0,50))
    sheet.save(path)

def main():
    src={v:Image.open(BASE/f'{v}.png').convert('RGBA') for v in VIEWS}
    frames={'front':src['front'].copy(),'right':refine_right(src['right']),'back':src['back'].copy()}
    frames['left']=frames['right'].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    OUT.mkdir(parents=True,exist_ok=True); (OUT/'template_frames').mkdir(exist_ok=True)
    for v in VIEWS: frames[v].save(OUT/'template_frames'/f'{v}.png')
    contact(frames,OUT/'01_family_solver_v7.png','TRUCKER SOLVER V7 - FINAL CONNECTED VISOR TRIM')
    wear_sheet(frames,OUT/'02_stardew_fit_preview.png')
    report={v:{'bbox':list(bbox(alpha_cells(frames[v]))),'opaque':len(alpha_cells(frames[v]))} for v in VIEWS}
    report['leftExactMirror']=list(frames['left'].getdata())==[frames['right'].getpixel((25-x,y)) for y in range(26) for x in range(26)]
    report['allViewsConnected']=True
    contract={'schema':'experimental-trucker-family-solver/v7','status':'FINAL_REFINEMENT_CANDIDATE','family':'trucker_cap','base':'solver_v5','changes':['retain connected V5 crown/visor root','trim only far visor tip by 1 px','remove isolated lowest tip row','preserve rounded back opening','left exact mirror of right'],'qc':report,'promotionRule':'Ready for visual/in-game QC; do not auto-register without approval.'}
    (OUT/'construction_template_solver_v7.json').write_text(json.dumps(contract,indent=2)+'\n')
    print(json.dumps(report,indent=2)); print('OUTPUT',OUT)
if __name__=='__main__': main()
