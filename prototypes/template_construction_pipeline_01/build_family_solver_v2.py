#!/usr/bin/env python3
from pathlib import Path
import json, math
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
SEM=HERE/'run_trucker_photo_zero123_01/semantic_trucker_01'
OUT=HERE/'run_trucker_photo_zero123_01/family_solver_v2'
HEAD=ROOT/'experiments/pixellab/head_guides'
FIT=ROOT/'prototypes/photo_tailor_source_identity_01/trucker_wear_fit_proof_01/fit_contract.json'
VIEWS=('front','right','back','left')
PAL={'outline':(48,45,48,255),'panel':(190,187,180,255),'mesh':(151,156,153,255),
     'visor':(101,98,97,255),'strap':(91,87,90,255),'button':(73,69,71,255)}

def cells(im): return {(x,y) for y in range(26) for x in range(26) if im.getpixel((x,y))[3]>15}
def bbox(ps):
 xs=[x for x,y in ps]; ys=[y for x,y in ps]; return min(xs),min(ys),max(xs),max(ys)
def border(ps): return {p for p in ps if any((p[0]+dx,p[1]+dy) not in ps for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))}
def clamp(v,a,b): return max(a,min(b,v))
def measure(source):
 out={}
 for v,im in source.items():
  ps=cells(im); x0,y0,x1,y1=bbox(ps)
  out[v]={'bbox':[x0,y0,x1,y1],'w':x1-x0+1,'h':y1-y0+1,'opaque':len(ps)}
 return out

def span_rows(cx, top, widths):
 ps=set()
 for i,w in enumerate(widths):
  x0=round(cx-(w-1)/2); y=top+i
  ps.update((x,y) for x in range(x0,x0+w))
 return ps

def solve_front(m):
 crown_w=clamp(round(m['w']*.78),14,18); crown_h=clamp(round(m['h']*.68),10,13)
 widths=[]
 for r in range(crown_h):
  t=r/max(1,crown_h-1); widths.append(max(4,round(crown_w*(0.52+0.48*math.sin(min(1,t+0.15)*math.pi/2)))))
 crown=span_rows(12.5,3,widths); visor_y=3+crown_h-2
 visor={(x,y) for y in range(visor_y,visor_y+3) for x in range(4,22) if (y<visor_y+2 or 6<=x<=19)}
 return crown|visor, visor

def solve_side(m):
 crown_h=clamp(round(m['h']*.78),9,12); crown_w=clamp(round(m['w']*.66),13,16)
 crown=set(); x0=4
 for r in range(crown_h):
  t=r/max(1,crown_h-1); left=x0+round((1-t)*3); right=x0+crown_w-1
  crown.update((x,3+r) for x in range(left,right+1))
 visor_y=3+crown_h-3; visor={(x,y) for y in range(visor_y,visor_y+3) for x in range(x0+crown_w-5,25) if y<visor_y+2 or x<23}
 return crown|visor, visor

def solve_back(m):
 w=clamp(round(m['w']*.82),13,17); h=clamp(round(m['h']*.78),11,14)
 widths=[]
 for r in range(h):
  t=r/max(1,h-1); widths.append(max(4,round(w*(0.55+0.45*math.sin(min(1,t+0.12)*math.pi/2)))))
 ps=span_rows(12.5,3,widths)
 return ps
def paint(shape, visor=None, view='front'):
 im=Image.new('RGBA',(26,26),(0,0,0,0)); visor=visor or set()
 x0,y0,x1,y1=bbox(shape)
 split=x0+round((x1-x0+1)*.52)
 for x,y in shape:
  if (x,y) in visor: c=PAL['visor']
  elif view=='front': c=PAL['panel'] if 7<=x<=18 else PAL['mesh']
  elif view in ('right','left'):
   front=(x>=split) if view=='right' else (x<=split); c=PAL['panel'] if front else PAL['mesh']
  else: c=PAL['mesh']
  im.putpixel((x,y),c)
 if view=='back':
  ox0,ox1=9,16; oy0,oy1=10,14
  for y in range(oy0,oy1+1):
   for x in range(ox0,ox1+1): im.putpixel((x,y),(0,0,0,0))
  for x in range(ox0,ox1+1): im.putpixel((x,15),PAL['strap'])
 if view in ('front','back'):
  im.putpixel((12,3),PAL['button']); im.putpixel((13,3),PAL['button'])
 for x,y in border({(x,y) for y in range(26) for x in range(26) if im.getpixel((x,y))[3]}): im.putpixel((x,y),PAL['outline'])
 return im

def contact(frames,path,title):
 scale=9; tile=26*scale; pad=12
 out=Image.new('RGB',(pad+4*(tile+pad),tile+70),'white'); d=ImageDraw.Draw(out); d.text((10,8),title,fill='black')
 for i,v in enumerate(VIEWS):
  x=pad+i*(tile+pad); d.text((x+88,30),v.upper(),fill='black'); src=frames[v].resize((tile,tile),Image.Resampling.NEAREST); out.paste(src,(x,50),src)
 out.save(path)

def paint_scaled(canvas,sprite,sx,sy,ox,oy):
 for y in range(sprite.height):
  for x in range(sprite.width):
   p=sprite.getpixel((x,y))
   if p[3]: canvas.alpha_composite(Image.new('RGBA',(sx,sy),p),(ox+x*sx,oy+y*sy))
def wear_sheet(frames,path):
 fit=json.loads(FIT.read_text())['after']; base=12; cell=(312,360); pad=8
 sheet=Image.new('RGB',(4*cell[0]+5*pad,cell[1]+60),(239,238,233)); d=ImageDraw.Draw(sheet); d.text((8,8),'FAMILY SOLVER V2 - STARDew FIT',fill='black')
 for i,v in enumerate(VIEWS):
  x0=pad+i*(cell[0]+pad); d.text((x0+135,28),v.upper(),fill='black'); c=Image.new('RGBA',cell,(0,0,0,0))
  head=Image.open(HEAD/f'farmer_head_{v}_hair.png').convert('RGBA'); paint_scaled(c,head,base,base,60,144)
  t=fit[v]; paint_scaled(c,frames[v],t['scaleX'],t['scaleY'],t['offsetX'],t['offsetY'])
  flat=Image.new('RGB',cell,(239,238,233)); flat.paste(c,(0,0),c); sheet.paste(flat,(x0,50))
 sheet.save(path)

def main():
 source={v:Image.open(SEM/'template_frames'/f'{v}.png').convert('RGBA') for v in VIEWS}; m=measure(source)
 front,fvisor=solve_front(m['front']); side,svisor=solve_side(m['right']); back=solve_back(m['back'])
 frames={'front':paint(front,fvisor,'front'),'right':paint(side,svisor,'right'),'back':paint(back,set(),'back')}
 frames['left']=frames['right'].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 OUT.mkdir(parents=True,exist_ok=True); (OUT/'template_frames').mkdir(exist_ok=True)
 for v in VIEWS: frames[v].save(OUT/'template_frames'/f'{v}.png')
 contact(frames,OUT/'01_family_solver_template.png','AI MEASUREMENTS -> TRUCKER FAMILY CONSTRUCTION SOLVER V2')
 wear_sheet(frames,OUT/'02_stardew_fit_preview.png')
 contract={'schema':'experimental-trucker-family-solver/v2','status':'EXPERIMENTAL_REVIEW_REQUIRED','family':'trucker_cap',
  'input':'Zero123++ semantic cardinal candidate','measurements':m,'rules':['AI supplies proportions, not final pixels','front/back symmetry enforced','left exact mirror of solved right','Stardew occupancy clamps crown/visor proportions','back opening inferred from family grammar'],
  'promotionRule':'Never auto-promote; compare against AI views and in-game QC.'}
 (OUT/'construction_template_solver_v2.json').write_text(json.dumps(contract,indent=2)+'\n')
 print(json.dumps(m,indent=2)); print('OUTPUT',OUT)

if __name__=='__main__': main()
