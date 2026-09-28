#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw
import json, math, hashlib, shutil
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'experiments/vanilla_source_only_random_batch_02_distinct'
OUT=ROOT/'experiments/vanilla_source_only_material_regions_01'
VIEWS=('front','right','left','back')

def lum(p): return .299*p[0]+.587*p[1]+.114*p[2]
def load(d,prefix): return {v:Image.open(d/f'{prefix}_{v}.png').convert('RGBA') for v in VIEWS}
def save(d,prefix,frames):
 d.mkdir(parents=True,exist_ok=True)
 for v,im in frames.items(): im.save(d/f'{prefix}_{v}.png')
def alpha_hash(frames):
 h=hashlib.sha256()
 for v in VIEWS:
  for p in frames[v].getdata(): h.update(bytes((p[3],)))
 return h.hexdigest()
def interior(im,x,y):
 if not im.getpixel((x,y))[3]: return False
 for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
  xx,yy=x+dx,y+dy
  if xx<0 or yy<0 or xx>=im.width or yy>=im.height or not im.getpixel((xx,yy))[3]: return False
 return True

def safe_mask(source):
 # Source-owned capacity mask: interior only, excludes very dark construction pixels.
 out={}; total=0
 for v,im in source.items():
  cells=set()
  for y in range(im.height):
   for x in range(im.width):
    p=im.getpixel((x,y))
    if interior(im,x,y) and lum(p)>42:
     # require at least 2 same-ish luma neighbours so isolated motifs/details are excluded
     near=0
     for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
      q=im.getpixel((x+dx,y+dy))
      if abs(lum(q)-lum(p))<36: near+=1
     if near>=2: cells.add((x,y))
  out[v]=cells; total+=len(cells)
 return out,total

def select_sparse(mask,kind):
 chosen={v:set() for v in VIEWS}
 for vi,v in enumerate(VIEWS):
  cells=mask[v]
  for x,y in sorted(cells,key=lambda p:(p[1],p[0])):
   if kind=='knit': keep=((x+vi)%3==0 and y%2==0)
   elif kind=='wool': keep=((x*17+y*29+vi*7)%11==0)
   else: keep=((x+y+vi)%4==0 and (x%3==0 or y%3==0))
   if not keep: continue
   # no orthogonally adjacent treatment cells; avoids thick strokes/blobs
   if any((x+dx,y+dy) in chosen[v] for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))): continue
   chosen[v].add((x,y))
 return chosen

def shift(p,delta):
 if not p[3]: return p
 Y=lum(p); target=max(0,min(255,Y+delta)); scale=target/max(1,Y)
 rgb=tuple(max(0,min(255,round(c*scale))) for c in p[:3])
 return (*rgb,p[3])
def apply_material(base,mask,kind):
 chosen=select_sparse(mask,kind); out={}
 for v,im in base.items():
  dst=im.copy()
  for x,y in chosen[v]:
   d={'knit':-9,'wool':8,'plaid':-11}[kind]
   dst.putpixel((x,y),shift(dst.getpixel((x,y)),d))
  out[v]=dst
 return out,chosen

def mask_png(source,mask,chosen):
 w=next(iter(source.values())).width; h=next(iter(source.values())).height
 out=Image.new('RGBA',(w,h*4),(0,0,0,0))
 for i,v in enumerate(VIEWS):
  im=source[v]
  for y in range(h):
   for x in range(w):
    p=im.getpixel((x,y))
    if p[3]: out.putpixel((x,y+i*h),(205,205,205,255))
  for x,y in mask[v]: out.putpixel((x,y+i*h),(120,180,120,255))
  for x,y in chosen[v]: out.putpixel((x,y+i*h),(20,20,20,255))
 return out

def contact(records):
 W=1550; rowh=245; H=60+len(records)*rowh
 s=Image.new('RGBA',(W,H),(239,237,231,255)); d=ImageDraw.Draw(s)
 d.text((15,10),'STARDEW-ONLY V4 — SAFE MATERIAL REGION PROOF',fill=(20,20,20,255))
 d.text((15,30),'SOURCE | V3 COLORWAY | + MATERIAL   (green mask = eligible interior, black = changed treatment cells)',fill=(55,55,55,255))
 for ri,r in enumerate(records):
  y0=60+ri*rowh; f=OUT/r['dir']; sc=7 if r['kind']=='hat' else 12
  d.text((15,y0),f"{r['kind'].upper()} #{r['sourceIndex']} | {r['material']} | safe={r['safeCells']} changed={r['treatedCells']}",fill=(25,25,25,255))
  for ci,(lab,pref) in enumerate((('SOURCE','source'),('COLORWAY','base'),('MATERIAL','material'))):
   x0=90+ci*440; d.text((x0,y0+18),lab,fill=(65,65,65,255)); x=x0
   for v in VIEWS:
    im=Image.open(f/f'{pref}_{v}.png').convert('RGBA'); big=im.resize((im.width*sc,im.height*sc),Image.Resampling.NEAREST)
    s.alpha_composite(big,(x,y0+38)); x+=big.width+9
  m=Image.open(f/'mask.png').convert('RGBA'); big=m.resize((m.width*sc,m.height*sc),Image.Resampling.NEAREST)
  s.alpha_composite(big,(1360,y0+26)); d.text((1360,y0+12),'MASK',fill=(65,65,65,255))
 s.save(OUT/'STARDEW_ONLY_V4_MATERIAL_CONTACT.png')

if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)
manifest=json.load(open(SRC/'manifest.json')); records=[]
for i,r in enumerate(manifest['records']):
 f=SRC/r['dir']; source=load(f,'source'); base=load(f,'a'); mask,cap=safe_mask(source)
 # capacity-aware treatment; tiny garments may skip rather than force noise
 if cap>=34: material=('knit','plaid','wool')[i%3]
 elif cap>=14: material=('wool','knit')[i%2]
 else: material='none'
 if material=='none': out={v:im.copy() for v,im in base.items()}; chosen={v:set() for v in VIEWS}
 else: out,chosen=apply_material(base,mask,material)
 assert alpha_hash(source)==alpha_hash(out)
 treated=sum(len(x) for x in chosen.values())
 # If a nominal treatment found no legal cells, downgrade to none.
 if material!='none' and treated<2:
  material='none'; out={v:im.copy() for v,im in base.items()}; chosen={v:set() for v in VIEWS}; treated=0
 d=OUT/r['dir']; save(d,'source',source); save(d,'base',base); save(d,'material',out); mask_png(source,mask,chosen).save(d/'mask.png')
 rec={'dir':r['dir'],'kind':r['kind'],'sourceIndex':r['sourceIndex'],'material':material,'safeCells':cap,'treatedCells':treated,'theme':r['themeA']}
 (d/'material.json').write_text(json.dumps(rec,indent=2)+'\n'); records.append(rec)
contact(records)
(OUT/'manifest.json').write_text(json.dumps({'schema':'stardew-only-material-regions/v4','rules':['source alpha locked','eligible cells are source-derived interior only','very dark construction pixels excluded','isolated detail pixels excluded','treatment cells cannot be orthogonally adjacent','capacity-aware skip instead of forced decoration'],'records':records},indent=2)+'\n')
print('PASS',len(records),'items')
for r in records: print(r)
print(OUT/'STARDEW_ONLY_V4_MATERIAL_CONTACT.png')
