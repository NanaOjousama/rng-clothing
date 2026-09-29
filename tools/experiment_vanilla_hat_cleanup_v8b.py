#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw
import json, colorsys, math, shutil
ROOT=Path(__file__).resolve().parents[1]
GAME=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer')
OUT=ROOT/'experiments/vanilla_source_only_hat_cleanup_v8b_01'
HATS=Image.open(GAME/'hats.png').convert('RGBA')
HAT_DATA=json.loads((GAME.parent.parent/'Data/hats.json').read_text())
VIEWS=('front','right','left','back')
PALETTES={p['id']:p for p in json.loads((ROOT/'authored/palettes.json').read_text())['palettes']}

def extract(idx):
 c,r=idx%12,idx//12;b=HATS.crop((c*20,r*80,c*20+20,r*80+80));return {v:b.crop((0,i*20,20,(i+1)*20)) for i,v in enumerate(VIEWS)}
def lum(p):return .299*p[0]+.587*p[1]+.114*p[2]
def tint_keep_luma(px,target,strength=.82):
 if not px[3]: return px
 Y=lum(px); th,ts,tv=colorsys.rgb_to_hsv(*(c/255 for c in target)); rr,gg,bb=colorsys.hsv_to_rgb(th,max(.22,ts),max(.10,min(1,Y/255)))
 raw=[px[i]*(1-strength)+255*q*strength for i,q in enumerate((rr,gg,bb))];cur=.299*raw[0]+.587*raw[1]+.114*raw[2];d=Y-cur
 rgb=[max(0,min(255,round(q+d))) for q in raw];return (*rgb,px[3])
def target(theme,lane='body'):
 ramp=PALETTES[theme]['ramps'][lane];h=ramp[len(ramp)//2].lstrip('#');return tuple(int(h[i:i+2],16) for i in (0,2,4))
def recolor(source,theme):
 tgt=target(theme,'body');out={}
 for v,im in source.items():
  dst=im.copy()
  for y in range(20):
   for x in range(20):
    p=dst.getpixel((x,y))
    if p[3] and lum(p)>35:dst.putpixel((x,y),tint_keep_luma(p,tgt,.84))
  out[v]=dst
 return out
def bbox(im):
 pts=[(x,y) for y in range(20) for x in range(20) if im.getpixel((x,y))[3]]
 if not pts:return None
 return min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)
def crown_band(out,theme):
 tgt=target(theme,'trim'); changed={v:[] for v in VIEWS}
 for v,im in out.items():
  b=bbox(im)
  if not b:continue
  x0,y0,x1,y1=b;h=y1-y0+1
  # lower crown, but still above the brim zone: ~45% down the occupied height.
  y=y0+max(2,round(h*.45))
  xs=[x for x in range(x0,x1+1) if im.getpixel((x,y))[3]]
  if len(xs)<5:continue
  # inset 1 px from both ends so it reads as a crown band, not an outline/brim repaint.
  xs=xs[1:-1]
  for x in xs:
   p=im.getpixel((x,y))
   if p[3] and lum(p)>35:
    im.putpixel((x,y),tint_keep_luma(p,tgt,.94));changed[v].append((x,y))
 return out,changed

def save(folder,prefix,frames):
 folder.mkdir(parents=True,exist_ok=True)
 for v,im in frames.items():im.save(folder/f'{prefix}_{v}.png')
def name(idx):
 raw=HAT_DATA.get(str(idx),'')
 return raw.split('/')[0] if raw else f'Vanilla Hat {idx}'
def contact(rows,path,title):
 sc=8;frame=160;gap=12;group=4*frame+3*gap; sx=70; vx=sx+group+120; W=vx+group+70; rowh=250;H=60+rowh*len(rows)
 s=Image.new('RGBA',(W,H),(240,238,232,255));d=ImageDraw.Draw(s);d.text((14,10),title,fill=(20,20,20,255));d.text((14,29),'SOURCE | VARIANT',fill=(55,55,55,255))
 for ri,r in enumerate(rows):
  y0=60+ri*rowh;f=OUT/r['dir'];d.text((14,y0),f"#{r['idx']} {r['name']} — {r['rule']}",fill=(30,30,30,255))
  for x0,lab,pref in ((sx,'SOURCE','source'),(vx,'VARIANT','variant')):
   d.text((x0,y0+20),lab,fill=(65,65,65,255));x=x0
   for v in VIEWS:
    im=Image.open(f/f'{pref}_{v}.png').convert('RGBA').resize((frame,frame),Image.Resampling.NEAREST);s.alpha_composite(im,(x,y0+42));d.text((x,y0+205),v[0].upper(),fill=(70,70,70,255));x+=frame+gap
 s.save(path)

if OUT.exists():shutil.rmtree(OUT)
OUT.mkdir(parents=True)
rows=[]
# Fix set
for idx,theme,mode in [(79,'SAILOR_COBALT_CREAM','recolor_only'),(98,'COASTAL_SEAFOAM_CORAL','crown_band')]:
 src=extract(idx);var=recolor(src,theme);changed={v:[] for v in VIEWS}
 if mode=='crown_band':var,changed=crown_band(var,theme)
 d=OUT/f'fix_{idx:03d}';save(d,'source',src);save(d,'variant',var)
 rec={'dir':d.name,'idx':idx,'name':name(idx),'rule':'recolor only; no added line' if mode=='recolor_only' else 'recolor + small crown band; brim untouched','bandCells':changed};(d/'manifest.json').write_text(json.dumps(rec,indent=2)+'\n');rows.append(rec)
contact(rows,OUT/'V8B_FIX_CONTACT.png','V8B HAT CLEANUP — USER-FLAGGED FIXES')
# New batch: use different hats, mostly recolor-only; only clear-brim Fishing Hat gets crown band.
rows2=[]
new=[(15,'Hunter\'s Cap','AUTUMN_OCHRE_PLUM','recolor_only'),(16,'Trucker Hat','COASTAL_SEAFOAM_CORAL','recolor_only'),(17,'Sailor\'s Cap','SAILOR_COBALT_CREAM','recolor_only'),(55,'Fishing Hat','FIELD_CANVAS_MOSS','crown_band')]
for idx,nm,theme,mode in new:
 src=extract(idx);var=recolor(src,theme);changed={v:[] for v in VIEWS}
 if mode=='crown_band':var,changed=crown_band(var,theme)
 d=OUT/f'new_{idx:03d}';save(d,'source',src);save(d,'variant',var)
 rec={'dir':d.name,'idx':idx,'name':name(idx),'rule':'recolor only; capacity too limited/ambiguous for extra detail' if mode=='recolor_only' else 'recolor + small crown band; brim untouched','bandCells':changed};(d/'manifest.json').write_text(json.dumps(rec,indent=2)+'\n');rows2.append(rec)
contact(rows2,OUT/'V8B_NEW_BATCH_CONTACT.png','V8B NEW VANILLA HAT BATCH — STRICT CAPACITY RULES')
(OUT/'manifest.json').write_text(json.dumps({'fixes':rows,'newBatch':rows2},indent=2)+'\n')
print('done')
for r in rows+rows2:print(r['idx'],r['name'],r['rule'],{k:len(v) for k,v in r['bandCells'].items()})
