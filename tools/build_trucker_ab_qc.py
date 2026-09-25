#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw
import json, math, shutil

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'authored/source_bases/cap/cap_trucker'
OUT=ROOT/'experiments/trucker_ab_resolution_qc_01'
VIEWS=('front','right','left','back')

VARIANTS=[
 ('01_source_green', None, None),
 ('02_forest_cream', '#315B47', '#C8D8B8'),
 ('03_navy_cream', '#314861', '#D8D2B5'),
 ('04_red_blue', '#A63A3E', '#48617E'),
 ('05_rust_tan', '#98533E', '#D0B286'),
 ('06_charcoal_sage', '#42484B', '#9EAF9C'),
]

def rgb(h):
 h=h.lstrip('#'); return tuple(int(h[i:i+2],16) for i in (0,2,4))

def luma(p):
 return (0.2126*p[0]+0.7152*p[1]+0.0722*p[2])/255.0

def sat(p):
 mx=max(p[:3]); mn=min(p[:3])
 return 0 if mx==0 else (mx-mn)/mx

def recolor(frame, solid_hex, mesh_hex):
 if solid_hex is None:
  return frame.copy()
 solid=rgb(solid_hex); mesh=rgb(mesh_hex)
 out=Image.new('RGBA',frame.size,(0,0,0,0))
 for y in range(frame.height):
  for x in range(frame.width):
   p=frame.getpixel((x,y))
   if p[3]<16:
    continue
   # Pale/low-saturation source pixels are the mesh/highlight treatment.
   is_mesh=(luma(p)>0.52 and sat(p)<0.42)
   base=mesh if is_mesh else solid
   factor=0.60+0.72*luma(p)
   q=tuple(max(0,min(255,round(c*factor))) for c in base)
   out.putpixel((x,y),(*q,p[3]))
 return out

def add_front_patch(frame, color=(232,225,196,255)):
 out=frame.copy()
 b=out.getbbox()
 if not b: return out
 x0,y0,x1,y1=b
 cx=(x0+x1)//2
 y=max(y0+2, y0+(y1-y0)//4)
 pts=[(cx-1,y),(cx,y),(cx+1,y),(cx-1,y+1),(cx,y+1),(cx+1,y+1)]
 for x,yy in pts:
  if 0<=x<out.width and 0<=yy<out.height and out.getpixel((x,yy))[3]>=16:
   out.putpixel((x,yy),color)
 return out

def stack(frames,size):
 sheet=Image.new('RGBA',(size,size*4),(0,0,0,0))
 for i,v in enumerate(VIEWS):
  sheet.alpha_composite(frames[v],(0,i*size))
 return sheet

def render_candidate(label,size):
 srcdir=BASE/f'production_{size}'
 result=[]
 for idx,(name,solid,mesh) in enumerate(VARIANTS):
  frames={}
  for v in VIEWS:
   fr=Image.open(srcdir/f'{v}.png').convert('RGBA')
   fr=recolor(fr,solid,mesh)
   if v=='front' and idx in (2,3,4):
    fr=add_front_patch(fr)
   frames[v]=fr
  d=OUT/label/name
  d.mkdir(parents=True,exist_ok=True)
  for v in VIEWS: frames[v].save(d/f'{v}.png')
  stack(frames,size).save(d/'hat.png')
  result.append((name,frames))
 return result

def main():
 if OUT.exists(): shutil.rmtree(OUT)
 OUT.mkdir(parents=True)
 A=render_candidate('A32',32)
 B=render_candidate('B24',24)

 # Like-for-like A/B: each row is one design; A32 and B24 both show all 4 views.
 tile=144; gap=8; labelw=190; split=28
 W=labelw+8*(tile+gap)+split+20
 rowh=tile+34; H=70+len(VARIANTS)*rowh
 sheet=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(sheet)
 d.text((10,8),'TRUCKER A/B RESOLUTION QC — SAME 6 DESIGNS',fill='black')
 d.text((labelw+250,28),'A = 32x32',fill='black')
 d.text((labelw+4*(tile+gap)+split+250,28),'B = 24x24',fill='black')
 for j,v in enumerate(VIEWS):
  d.text((labelw+j*(tile+gap)+45,48),v.upper(),fill='black')
  bx=labelw+4*(tile+gap)+split+j*(tile+gap)
  d.text((bx+45,48),v.upper(),fill='black')
 y=70

 for i,(name,_) in enumerate(zip(VARIANTS,A)):
  d.text((10,y+20),VARIANTS[i][0],fill='black')
  for j,v in enumerate(VIEWS):
   fr=A[i][1][v].resize((tile,tile),Image.Resampling.NEAREST)
   x=labelw+j*(tile+gap)
   sheet.paste(fr,(x,y),fr)
   fr2=B[i][1][v].resize((tile,tile),Image.Resampling.NEAREST)
   bx=labelw+4*(tile+gap)+split+j*(tile+gap)
   sheet.paste(fr2,(bx,y),fr2)
  y+=rowh
 sheet.save(OUT/'TRUCKER_AB_32_VS_24_CONTACT.png')
 meta={
  'source':str(BASE/'source/trucker_4view_master_80.png'),
  'A':'32x32 normalized production candidate',
  'B':'24x24 normalized production candidate',
  'variants':[v[0] for v in VARIANTS],
  'decision':'pending human visual QC'
 }
 (OUT/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
 print(OUT/'TRUCKER_AB_32_VS_24_CONTACT.png')

if __name__=='__main__':
 main()
