#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw
import json, colorsys, math, hashlib, shutil
ROOT=Path(__file__).resolve().parents[1]
V4=ROOT/'experiments/vanilla_source_only_material_regions_01'
V3=ROOT/'experiments/vanilla_source_only_random_batch_02_distinct'
OUT=ROOT/'experiments/vanilla_source_only_region_styling_01'
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
 xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
 return min(xs),min(ys),max(xs),max(ys)
def interior(im,x,y):
 if not im.getpixel((x,y))[3]: return False
 for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
  xx,yy=x+dx,y+dy
  if xx<0 or yy<0 or xx>=im.width or yy>=im.height or not im.getpixel((xx,yy))[3]: return False
 return True

def safe_cells(source):
 out={}
 for v,im in source.items():
  s=set()
  for y in range(im.height):
   for x in range(im.width):
    p=im.getpixel((x,y))
    if not interior(im,x,y) or lum(p)<=42: continue
    near=0
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
     if abs(lum(im.getpixel((x+dx,y+dy)))-lum(p))<36: near+=1
    if near>=2:s.add((x,y))
  out[v]=s
 return out

def derive_regions(kind,source,safe):
 """Return generic source-geometry zones, not guessed fashion semantics."""
 regs={'primary':{v:set() for v in VIEWS},'secondary':{v:set() for v in VIEWS}}
 per_view={}
 for v,im in source.items():
  x0,y0,x1,y1=bbox(im); w=max(1,x1-x0+1); h=max(1,y1-y0+1)
  if kind=='hat':
   # Upper surface vs lower construction zone. This is intentionally generic:
   # it can correspond to crown vs band/brim depending on the source.
   split=y0+max(1,round(h*.62))
   for p in safe[v]:
    (regs['primary'][v] if p[1]<split else regs['secondary'][v]).add(p)
  else:
   # Central torso/panel vs side treatment. At 8px scale this is more reliable
   # than claiming exact sleeve/collar semantics from pixels alone.
   lo=x0+w*.27; hi=x0+w*.73
   for p in safe[v]:
    (regs['primary'][v] if lo<=p[0]<=hi else regs['secondary'][v]).add(p)
  per_view[v]={'primary':len(regs['primary'][v]),'secondary':len(regs['secondary'][v])}
 totals={k:sum(len(regs[k][v]) for v in VIEWS) for k in regs}
 # Require enough cells globally and evidence in >=2 views for a styling zone.
 valid={k:(totals[k]>=10 and sum(bool(regs[k][v]) for v in VIEWS)>=2) for k in regs}
 return regs,totals,valid,per_view

def target_rgb(palette,lane):
 ramp=palette['ramps'][lane]; h=ramp[len(ramp)//2].lstrip('#'); return tuple(int(h[i:i+2],16) for i in (0,2,4))
def recolor_keep_luma(px,target,amount=.85):
 if not px[3]:return px
 Y=lum(px); r,g,b=[q/255 for q in target]; hh,ss,vv=colorsys.rgb_to_hsv(r,g,b)
 # Build target hue at source luminance, then blend chroma only.
 rr,gg,bb=colorsys.hsv_to_rgb(hh,max(.20,ss),max(.10,min(1,Y/255)))
 tr,tg,tb=[q*255 for q in (rr,gg,bb)]
 raw=[px[0]*(1-amount)+tr*amount,px[1]*(1-amount)+tg*amount,px[2]*(1-amount)+tb*amount]
 cur=.299*raw[0]+.587*raw[1]+.114*raw[2]; shift=Y-cur
 out=[max(0,min(255,q+shift)) for q in raw]
 # final tiny correction to keep luminance tightly source-relative
 cur=.299*out[0]+.587*out[1]+.114*out[2]; d=Y-cur
 out=[max(0,min(255,round(q+d))) for q in out]
 return (*out,px[3])
def apply_region(base,regions,valid,palette,mode):
 out={v:base[v].copy() for v in VIEWS}; changed={v:set() for v in VIEWS}
 # Variant A accents secondary; B accents primary with a quieter amount.
 zone='secondary' if mode=='A' else 'primary'; amount=.90 if mode=='A' else .72
 if not valid.get(zone): return out,changed,zone,False
 lane='accent' if mode=='A' else 'trim'; tgt=target_rgb(palette,lane)
 for v in VIEWS:
  for x,y in regions[zone][v]:
   p=out[v].getpixel((x,y)); q=recolor_keep_luma(p,tgt,amount)
   if q!=p: out[v].putpixel((x,y),q); changed[v].add((x,y))
 return out,changed,zone,True

def diff_stats(a,b):
 total=changed=0; delta=0
 for v in VIEWS:
  for p,q in zip(a[v].getdata(),b[v].getdata()):
   if not p[3]:continue
   total+=1
   if p!=q:changed+=1;delta+=math.dist(p[:3],q[:3])
 return {'changedOpaqueRatio':round(changed/max(1,total),4),'avgRgbDeltaChanged':round(delta/max(1,changed),2)}
def region_mask_png(source,regions,valid):
 w=next(iter(source.values())).width; h=next(iter(source.values())).height
 out=Image.new('RGBA',(w,h*4),(0,0,0,0))
 for i,v in enumerate(VIEWS):
  im=source[v]
  for y in range(h):
   for x in range(w):
    if im.getpixel((x,y))[3]:out.putpixel((x,y+i*h),(205,205,205,255))
  for x,y in regions['primary'][v]:out.putpixel((x,y+i*h),(105,160,215,255))
  for x,y in regions['secondary'][v]:out.putpixel((x,y+i*h),(225,155,95,255))
 return out

def contact(records,kind):
 rows=[r for r in records if r['kind']==kind]; W=1760; rowh=270 if kind=='hat' else 250; H=66+rowh*len(rows)
 s=Image.new('RGBA',(W,H),(239,237,231,255)); d=ImageDraw.Draw(s)
 d.text((15,10),f'STARDEW-ONLY V5 {kind.upper()} — SOURCE-BACKED REGION STYLING',fill=(20,20,20,255))
 d.text((15,30),'SOURCE | V4 MATERIAL | REGION A | REGION B | MASK   blue=primary geometry zone, orange=secondary',fill=(55,55,55,255))
 for ri,r in enumerate(rows):
  y0=66+ri*rowh; f=OUT/r['dir']; sc=8 if kind=='hat' else 13
  d.text((15,y0),f"{kind.upper()} #{r['sourceIndex']} | A:{r['zoneA']} {'ON' if r['appliedA'] else 'SKIP'} | B:{r['zoneB']} {'ON' if r['appliedB'] else 'SKIP'} | zones {r['regionTotals']}",fill=(30,30,30,255))
  for ci,(lab,pref) in enumerate((('SOURCE','source'),('V4 MATERIAL','material'),('REGION A','a'),('REGION B','b'))):
   x0=75+ci*400; d.text((x0,y0+20),lab,fill=(65,65,65,255)); x=x0
   for v in VIEWS:
    im=Image.open(f/f'{pref}_{v}.png').convert('RGBA'); big=im.resize((im.width*sc,im.height*sc),Image.Resampling.NEAREST)
    s.alpha_composite(big,(x,y0+42)); x+=big.width+8
  m=Image.open(f/'region_mask.png').convert('RGBA'); big=m.resize((m.width*sc,m.height*sc),Image.Resampling.NEAREST)
  s.alpha_composite(big,(1610,y0+30)); d.text((1610,y0+15),'MASK',fill=(65,65,65,255))
 out=OUT/f'STARDEW_ONLY_V5_{kind.upper()}_REGION_CONTACT.png';s.save(out);print(out)

if OUT.exists():shutil.rmtree(OUT)
OUT.mkdir(parents=True)
v4=json.load(open(V4/'manifest.json')); records=[]
for r in v4['records']:
 d4=V4/r['dir']; d3=V3/r['dir']; source=load(d4,'source'); material=load(d4,'material')
 remix=json.load(open(d3/'remix.json')); alt_theme=remix['themeB']; pal=PALETTES[alt_theme]
 safe=safe_cells(source); regs,totals,valid,per_view=derive_regions(r['kind'],source,safe)
 a,chA,zA,onA=apply_region(material,regs,valid,pal,'A'); b,chB,zB,onB=apply_region(material,regs,valid,pal,'B')
 assert alpha_hash(source)==alpha_hash(a)==alpha_hash(b)
 d=OUT/r['dir'];save(d,'source',source);save(d,'material',material);save(d,'a',a);save(d,'b',b);region_mask_png(source,regs,valid).save(d/'region_mask.png')
 rec={'dir':r['dir'],'kind':r['kind'],'sourceIndex':r['sourceIndex'],'material':r['material'],'alternateTheme':alt_theme,'regionTotals':totals,'regionValid':valid,'perView':per_view,'zoneA':zA,'zoneB':zB,'appliedA':onA,'appliedB':onB,'statsA':diff_stats(material,a),'statsB':diff_stats(material,b)}
 (d/'region.json').write_text(json.dumps(rec,indent=2)+'\n');records.append(rec)
for kind in ('hat','shirt'):contact(records,kind)
(OUT/'manifest.json').write_text(json.dumps({'schema':'stardew-only-region-styling/v5','principle':'generic source-geometry regions first; semantic names only after human/source-backed confirmation','rules':['exact alpha/geometry locked','region masks derive from source occupied geometry + safe interior','no brightness/color semantic guessing','region must have >=10 cells and appear in >=2 views','dark structural pixels and silhouette edges excluded','capacity-aware skip','region recolor preserves local luminance'],'records':records},indent=2)+'\n')
print('PASS',len(records),'items')
for r in records:print(r['kind'],r['sourceIndex'],r['regionTotals'],r['regionValid'],r['statsA'],r['statsB'])
