#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw
import json, colorsys, math, hashlib, shutil
ROOT=Path(__file__).resolve().parents[1]
V5=ROOT/'experiments/vanilla_source_only_region_styling_01'
V3=ROOT/'experiments/vanilla_source_only_random_batch_02_distinct'
OUT=ROOT/'experiments/vanilla_source_only_motif_components_01'
PALETTES={p['id']:p for p in json.loads((ROOT/'authored/palettes.json').read_text())['palettes']}
VIEWS=('front','right','left','back')

def load(d,prefix): return {v:Image.open(d/f'{prefix}_{v}.png').convert('RGBA') for v in VIEWS}
def save(d,prefix,frames):
 d.mkdir(parents=True,exist_ok=True)
 for v,im in frames.items(): im.save(d/f'{prefix}_{v}.png')
def lum(p): return .299*p[0]+.587*p[1]+.114*p[2]
def alpha_hash(frames):
 h=hashlib.sha256()
 for v in VIEWS:
  for p in frames[v].getdata(): h.update(bytes((p[3],)))
 return h.hexdigest()
def bbox(im):
 pts=[(x,y) for y in range(im.height) for x in range(im.width) if im.getpixel((x,y))[3]]
 if not pts:return (0,0,im.width-1,im.height-1)
 xs=[p[0] for p in pts];ys=[p[1] for p in pts]
 return min(xs),min(ys),max(xs),max(ys)
def interior(im,x,y):
 if not im.getpixel((x,y))[3]:return False
 for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
  xx,yy=x+dx,y+dy
  if xx<0 or yy<0 or xx>=im.width or yy>=im.height or not im.getpixel((xx,yy))[3]:return False
 return True

def safe_cells(source):
 out={}
 for v,im in source.items():
  s=set()
  for y in range(im.height):
   for x in range(im.width):
    p=im.getpixel((x,y))
    if not interior(im,x,y) or lum(p)<=48:continue
    near=sum(abs(lum(im.getpixel((x+dx,y+dy)))-lum(p))<38 for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))
    if near>=2:s.add((x,y))
  out[v]=s
 return out

def accent_rgb(theme):
 ramp=PALETTES[theme]['ramps']['accent']; h=ramp[-2].lstrip('#')
 return tuple(int(h[i:i+2],16) for i in (0,2,4))
def trim_rgb(theme):
 ramp=PALETTES[theme]['ramps']['trim']; h=ramp[len(ramp)//2].lstrip('#')
 return tuple(int(h[i:i+2],16) for i in (0,2,4))
def tint_keep_luma(px,target,strength=.9):
 Y=lum(px); th,ts,tv=colorsys.rgb_to_hsv(*(q/255 for q in target)); rr,gg,bb=colorsys.hsv_to_rgb(th,max(.25,ts),max(.12,min(1,Y/255)))
 raw=[px[i]*(1-strength)+255*q*strength for i,q in enumerate((rr,gg,bb))]
 cur=.299*raw[0]+.587*raw[1]+.114*raw[2]; d=Y-cur
 rgb=[max(0,min(255,round(q+d))) for q in raw]
 return (*rgb,px[3])

def localized_candidates(kind,source,safe):
 im=source['front']; x0,y0,x1,y1=bbox(im); cx=(x0+x1)/2; h=max(1,y1-y0+1)
 # Stay in upper/middle face, away from lower hems/brims and silhouette.
 ylo=y0+1; yhi=y0+max(1,round(h*.62))
 cand=[p for p in safe['front'] if ylo<=p[1]<=yhi]
 if kind=='hat':
  cand.sort(key=lambda p:(abs(p[0]-cx)+abs(p[1]-(ylo+yhi)/2)*.6,p[1],p[0]))
 else:
  # Slightly offset chest mark reads better than dead-centre at 8px.
  targetx=cx-0.8; targety=y0+h*.38
  cand.sort(key=lambda p:(abs(p[0]-targetx)+abs(p[1]-targety)*.7,p[1],p[0]))
 return cand

def choose_localized(kind,source,safe):
 cand=localized_candidates(kind,source,safe)
 need=3 if kind=='hat' else 1
 if len(cand)<need:return set()
 first=cand[0]; chosen=[first]
 # Hats can carry a tiny 2-3 cell mark; shirts default to one cell unless a safe horizontal mate exists.
 if kind=='hat':
  for q in cand[1:]:
   if abs(q[0]-first[0])<=1 and abs(q[1]-first[1])<=1 and q not in chosen:
    chosen.append(q)
    if len(chosen)==3:break
  if len(chosen)<2:return set()
 else:
  for q in cand[1:]:
   if q[1]==first[1] and abs(q[0]-first[0])==1:
    chosen.append(q);break
 return set(chosen[:3 if kind=='hat' else 2])

def choose_wrap(source,safe):
 chosen={v:set() for v in VIEWS}
 # Find one low interior row per view with >=3 safe cells (>=2 on 8px shirts), use sparse cells only.
 for v,im in source.items():
  x0,y0,x1,y1=bbox(im); rows={}
  for x,y in safe[v]: rows.setdefault(y,[]).append(x)
  viable=[(y,sorted(xs)) for y,xs in rows.items() if len(xs)>=2]
  if not viable:continue
  y,xs=max(viable,key=lambda t:t[0])
  # 1px-spaced trim marks; no solid thick bands.
  for i,x in enumerate(xs):
   if i%2==0:chosen[v].add((x,y))
 return chosen

def apply_localized(base,cells,target):
 out={v:base[v].copy() for v in VIEWS}; changed={v:set() for v in VIEWS}
 for x,y in cells:
  p=out['front'].getpixel((x,y)); q=tint_keep_luma(p,target,.95); out['front'].putpixel((x,y),q);changed['front'].add((x,y))
 return out,changed

def apply_wrap(base,cells,target):
 out={v:base[v].copy() for v in VIEWS};changed={v:set() for v in VIEWS}
 for v in VIEWS:
  for x,y in cells[v]:
   p=out[v].getpixel((x,y));q=tint_keep_luma(p,target,.86);out[v].putpixel((x,y),q);changed[v].add((x,y))
 return out,changed

def stats(a,b):
 total=changed=0;delta=0
 for v in VIEWS:
  for p,q in zip(a[v].getdata(),b[v].getdata()):
   if not p[3]:continue
   total+=1
   if p!=q:changed+=1;delta+=math.dist(p[:3],q[:3])
 return {'changedOpaqueRatio':round(changed/max(1,total),4),'avgRgbDeltaChanged':round(delta/max(1,changed),2),'changedPixels':changed}
def mask_image(source,safe,local,wrap):
 w=next(iter(source.values())).width;h=next(iter(source.values())).height
 out=Image.new('RGBA',(w,h*4),(0,0,0,0))
 for i,v in enumerate(VIEWS):
  im=source[v]
  for y in range(h):
   for x in range(w):
    if im.getpixel((x,y))[3]:out.putpixel((x,y+i*h),(205,205,205,255))
  for x,y in safe[v]:out.putpixel((x,y+i*h),(165,205,165,255))
  if v=='front':
   for x,y in local:out.putpixel((x,y+i*h),(210,60,70,255))
  for x,y in wrap[v]:out.putpixel((x,y+i*h),(65,110,220,255))
 return out

def contact(records,kind):
 rows=[r for r in records if r['kind']==kind];W=1760;rowh=270 if kind=='hat' else 250;H=68+len(rows)*rowh
 s=Image.new('RGBA',(W,H),(239,237,231,255));d=ImageDraw.Draw(s)
 d.text((15,10),f'STARDEW-ONLY V6 {kind.upper()} — SAFE MOTIF / COMPONENT PROOF',fill=(20,20,20,255))
 d.text((15,30),'SOURCE | V5 BASE | LOCALIZED ACCENT | WRAP TRIM | MASK   red=localized, blue=wrap, green=safe interior',fill=(55,55,55,255))
 for ri,r in enumerate(rows):
  y0=68+ri*rowh;f=OUT/r['dir'];sc=8 if kind=='hat' else 13
  d.text((15,y0),f"{kind.upper()} #{r['sourceIndex']} | local {r['localizedPixels']} px {'ON' if r['localizedApplied'] else 'SKIP'} | wrap {r['wrapPixels']} px {'ON' if r['wrapApplied'] else 'SKIP'}",fill=(28,28,28,255))
  for ci,(lab,pref) in enumerate((('SOURCE','source'),('V5 BASE','base'),('LOCAL','localized'),('WRAP','wrap'))):
   x0=72+ci*400;d.text((x0,y0+20),lab,fill=(65,65,65,255));x=x0
   for v in VIEWS:
    im=Image.open(f/f'{pref}_{v}.png').convert('RGBA');big=im.resize((im.width*sc,im.height*sc),Image.Resampling.NEAREST)
    s.alpha_composite(big,(x,y0+42));x+=big.width+8
  m=Image.open(f/'motif_mask.png').convert('RGBA');big=m.resize((m.width*sc,m.height*sc),Image.Resampling.NEAREST)
  s.alpha_composite(big,(1610,y0+30));d.text((1610,y0+15),'MASK',fill=(65,65,65,255))
 out=OUT/f'STARDEW_ONLY_V6_{kind.upper()}_MOTIF_COMPONENT_CONTACT.png';s.save(out);print(out)

if OUT.exists():shutil.rmtree(OUT)
OUT.mkdir(parents=True)
v5=json.load(open(V5/'manifest.json'));records=[]
for r in v5['records']:
 f5=V5/r['dir'];f3=V3/r['dir'];source=load(f5,'source');base=load(f5,'a')
 remix=json.load(open(f3/'remix.json'));theme=remix['themeB'];safe=safe_cells(source)
 local=choose_localized(r['kind'],source,safe);wrapcells=choose_wrap(source,safe)
 wrap_count=sum(len(x) for x in wrapcells.values())
 # capacity gates: local minimum 2 px for hats, 1 for shirts. Wrap must touch >=3 views and enough pixels.
 local_ok=len(local)>=(2 if r['kind']=='hat' else 1)
 wrap_views=sum(bool(wrapcells[v]) for v in VIEWS);wrap_ok=wrap_views>=3 and wrap_count>=(8 if r['kind']=='hat' else 4)
 if local_ok:localized,chL=apply_localized(base,local,accent_rgb(theme))
 else:localized={v:base[v].copy() for v in VIEWS};chL={v:set() for v in VIEWS}
 if wrap_ok:wrap,chW=apply_wrap(base,wrapcells,trim_rgb(theme))
 else:wrap={v:base[v].copy() for v in VIEWS};chW={v:set() for v in VIEWS}
 assert alpha_hash(source)==alpha_hash(localized)==alpha_hash(wrap)
 d=OUT/r['dir'];save(d,'source',source);save(d,'base',base);save(d,'localized',localized);save(d,'wrap',wrap);mask_image(source,safe,local if local_ok else set(),wrapcells if wrap_ok else {v:set() for v in VIEWS}).save(d/'motif_mask.png')
 rec={'dir':r['dir'],'kind':r['kind'],'sourceIndex':r['sourceIndex'],'theme':theme,'localizedApplied':local_ok,'localizedPixels':len(local) if local_ok else 0,'localizedViews':['front'] if local_ok else [],'wrapApplied':wrap_ok,'wrapPixels':wrap_count if wrap_ok else 0,'wrapViews':[v for v in VIEWS if wrap_ok and wrapcells[v]],'localizedStats':stats(base,localized),'wrapStats':stats(base,wrap)}
 (d/'motif_component.json').write_text(json.dumps(rec,indent=2)+'\n');records.append(rec)
for k in ('hat','shirt'):contact(records,k)
(OUT/'manifest.json').write_text(json.dumps({'schema':'stardew-only-safe-motif-components/v6','principles':['localized motifs stay localized; no automatic copying to every view','wrap trim must have coherent safe cells in >=3 views','no alpha additions or generated silhouette geometry','motifs/components recolor existing source-safe pixels only','capacity-aware skip is preferred to forced decoration'],'records':records},indent=2)+'\n')
print('PASS',len(records),'items')
for r in records:print(r['kind'],r['sourceIndex'],'local',r['localizedApplied'],r['localizedPixels'],'wrap',r['wrapApplied'],r['wrapPixels'],r['wrapViews'])
