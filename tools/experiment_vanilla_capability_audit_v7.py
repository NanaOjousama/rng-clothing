#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw
from collections import Counter,deque
import json, math, shutil
ROOT=Path(__file__).resolve().parents[1]
GAME=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer')
OUT=ROOT/'experiments/vanilla_source_only_capability_audit_01'
VIEWS=('front','right','left','back')
HATS=Image.open(GAME/'hats.png').convert('RGBA')
SHIRTS=Image.open(GAME/'shirts.png').convert('RGBA')

def extract_hat(idx):
 c,r=idx%12,idx//12;b=HATS.crop((c*20,r*80,c*20+20,r*80+80));return {v:b.crop((0,i*20,20,(i+1)*20)) for i,v in enumerate(VIEWS)}
def extract_shirt(idx):
 c,r=idx%32,idx//32;b=SHIRTS.crop((c*8,r*32,c*8+8,r*32+32));return {v:b.crop((0,i*8,8,(i+1)*8)) for i,v in enumerate(VIEWS)}
def opaque(im):return [(x,y,im.getpixel((x,y))) for y in range(im.height) for x in range(im.width) if im.getpixel((x,y))[3]]
def bbox(im):
 pts=[(x,y) for x,y,p in opaque(im)]
 if not pts:return None
 xs=[x for x,y in pts];ys=[y for x,y in pts];return min(xs),min(ys),max(xs),max(ys)
def interior(im,x,y):
 if not im.getpixel((x,y))[3]:return False
 for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
  xx,yy=x+dx,y+dy
  if xx<0 or yy<0 or xx>=im.width or yy>=im.height or not im.getpixel((xx,yy))[3]:return False
 return True
def lum(p):return .299*p[0]+.587*p[1]+.114*p[2]
def color_dist(a,b):return math.dist(a[:3],b[:3])
def modal_color(im):
 c=Counter(p[:3] for _,_,p in opaque(im));return c.most_common(1)[0][0] if c else (0,0,0)
def components(cells):
 rem=set(cells);out=[]
 while rem:
  s=rem.pop();q=[s];comp={s}
  while q:
   x,y=q.pop()
   for d in ((1,0),(-1,0),(0,1),(0,-1)):
    n=(x+d[0],y+d[1])
    if n in rem:rem.remove(n);comp.add(n);q.append(n)
  out.append(comp)
 return sorted(out,key=len,reverse=True)
def minority_cells(im):
 if not opaque(im):return set()
 mode=modal_color(im); b=bbox(im);x0,y0,x1,y1=b
 vals=[]
 for x,y,p in opaque(im):
  if interior(im,x,y) and color_dist(p,(*mode,255))>=38 and lum(p)>28:
   vals.append((x,y))
 return set(vals)
def row_runs(cells):
 rows={}
 for x,y in cells:rows.setdefault(y,[]).append(x)
 return {y:sorted(xs) for y,xs in rows.items()}
def col_runs(cells):
 cols={}
 for x,y in cells:cols.setdefault(x,[]).append(y)
 return {x:sorted(ys) for x,ys in cols.items()}
def classify(kind,frames):
 f=frames['front'];b=bbox(f)
 if not b:return {'empty':True,'capabilities':[],'donors':[],'metrics':{}}
 x0,y0,x1,y1=b; w=x1-x0+1;h=y1-y0+1; total=len(opaque(f)); uniq=len(set(p[:3] for _,_,p in opaque(f)))
 minor=minority_cells(f); comps=components(minor); rows=row_runs(minor); cols=col_runs(minor)
 caps=[];don=[]
 # generic pattern density
 density=len(minor)/max(1,total)
 if density<.08: caps.append('plain_or_low_detail')
 # horizontal band / stripe evidence
 wide_rows=[(y,xs) for y,xs in rows.items() if len(xs)>=max(2,round(w*.45))]
 if wide_rows: caps.append('horizontal_band_or_stripe')
 # central vertical placket/button evidence
 cx=(x0+x1)/2
 center_cells=[(x,y) for x,y in minor if abs(x-cx)<=1]
 if len(center_cells)>=2 and len({y for x,y in center_cells})>=2: caps.append('central_placket_or_buttons')
 # compact motif candidate: interior minority component small and bounded
 motif=[]
 for comp in comps:
  if 2<=len(comp)<= (10 if kind=='hat' else 6):
   xs=[x for x,y in comp];ys=[y for x,y in comp]
   if min(xs)>x0 and max(xs)<x1 and min(ys)>y0 and max(ys)<y1:
    motif.append(comp)
 if motif:
  caps.append('compact_graphic_candidate')
  comp=motif[0];don.append({'type':'compact_graphic','view':'front','cells':sorted([list(p) for p in comp]),'bbox':[min(x for x,y in comp),min(y for x,y in comp),max(x for x,y in comp),max(y for x,y in comp)]})
 # dense pattern candidate
 if density>=.28 and len(comps)>=3: caps.append('dense_pattern_candidate')
 # contrast panel candidate: minority occupies sizeable connected region
 if comps and len(comps[0])>=max(3,round(total*.12)): caps.append('contrast_panel_candidate')
 if kind=='hat':
  lower=[(x,y) for x,y in minor if y>=y0+h*.58]
  if len(lower)>=max(3,round(w*.25)): caps.append('hat_lower_band_detail_candidate')
  upper=[(x,y) for x,y in minor if y<=y0+h*.58]
  if 2<=len(upper)<=12: caps.append('hat_front_detail_candidate')
 else:
  # side/collar treatment proxy
  edge=[(x,y) for x,y in minor if x<=x0+1 or x>=x1-1]
  if len(edge)>=3:caps.append('side_or_sleeve_contrast_candidate')
 return {'empty':False,'capabilities':sorted(set(caps)),'donors':don,'metrics':{'opaque':total,'uniqueColors':uniq,'minorityPixels':len(minor),'minorityDensity':round(density,3),'components':[len(c) for c in comps[:6]],'bbox':[x0,y0,x1,y1]}}
def make_sheet(records,kind,cap,path):
 picked=[r for r in records if r['kind']==kind and cap in r['capabilities']][:80]
 if not picked:return
 size=20 if kind=='hat' else 8;scale=7 if kind=='hat' else 12;cols=10 if kind=='hat' else 16
 rows=(len(picked)+cols-1)//cols;W=cols*(size*scale+28)+20;H=50+rows*(size*scale+25)
 s=Image.new('RGBA',(W,H),(242,240,234,255));d=ImageDraw.Draw(s);d.text((10,10),f'{kind.upper()} CAPABILITY: {cap}  n={len([r for r in records if r["kind"]==kind and cap in r["capabilities"]])}',fill=(20,20,20,255))
 for i,r in enumerate(picked):
  im=(extract_hat(r['index']) if kind=='hat' else extract_shirt(r['index']))['front'];x=10+(i%cols)*(size*scale+28);y=38+(i//cols)*(size*scale+25)
  s.alpha_composite(im.resize((size*scale,size*scale),Image.Resampling.NEAREST),(x,y));d.text((x,y+size*scale+2),str(r['index']),fill=(40,40,40,255))
 s.save(path)

if OUT.exists():shutil.rmtree(OUT)
OUT.mkdir(parents=True)
records=[]
for kind,count,extract in [('hat',132,extract_hat),('shirt',608,extract_shirt)]:
 for idx in range(count):
  frames=extract(idx);c=classify(kind,frames);records.append({'kind':kind,'index':idx,**c})
summary={}
for kind in ('hat','shirt'):
 rr=[r for r in records if r['kind']==kind and not r['empty']];counts=Counter(c for r in rr for c in r['capabilities'])
 summary[kind]={'nonEmpty':len(rr),'capabilityCounts':dict(sorted(counts.items())),'withDonorCandidates':sum(bool(r['donors']) for r in rr)}
 for cap in counts:
  make_sheet(records,kind,cap,OUT/f'{kind}_{cap}.png')
# donor vocabulary: exact source-backed candidate cells only
vocab=[]
for r in records:
 for n,d in enumerate(r['donors']):vocab.append({'id':f"vanilla.{r['kind']}.{r['index']}.{d['type']}.{n}",'sourceKind':r['kind'],'sourceIndex':r['index'],**d})
(OUT/'capability_catalog.json').write_text(json.dumps({'schema':'stardew-only-capability-audit/v7','records':records},indent=2)+'\n')
(OUT/'vanilla_donor_vocabulary.json').write_text(json.dumps({'schema':'stardew-only-donor-vocabulary/v1','boundary':'candidate source pixels only; no production transfer approval','donors':vocab},indent=2)+'\n')
(OUT/'summary.json').write_text(json.dumps({'schema':'stardew-only-capability-summary/v7','summary':summary,'donorCandidates':len(vocab)},indent=2)+'\n')
print(json.dumps({'summary':summary,'donorCandidates':len(vocab)},indent=2))
