#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw
import json, colorsys, math, shutil, hashlib
ROOT=Path(__file__).resolve().parents[1]
GAME=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer')
V7=ROOT/'experiments/vanilla_source_only_capability_audit_01'
V6=ROOT/'experiments/vanilla_source_only_motif_components_01'
V5=ROOT/'experiments/vanilla_source_only_region_styling_01'
V4=ROOT/'experiments/vanilla_source_only_material_regions_01'
V3=ROOT/'experiments/vanilla_source_only_random_batch_02_distinct'
OUT=ROOT/'experiments/vanilla_source_only_mixed_batch_v8_01'
VIEWS=('front','right','left','back')
HATS=Image.open(GAME/'hats.png').convert('RGBA')
SHIRTS=Image.open(GAME/'shirts.png').convert('RGBA')
PALETTES={p['id']:p for p in json.loads((ROOT/'authored/palettes.json').read_text())['palettes']}
HAT_DATA=json.loads((GAME.parent.parent/'Data/hats.json').read_text()) if (GAME.parent.parent/'Data/hats.json').exists() else {}
REVIEW=json.loads((V7/'vanilla_donor_vocabulary_reviewed.json').read_text())['categories']
CATALOG=json.loads((V7/'capability_catalog.json').read_text())['records']
CAP={(r['kind'],r['index']):r for r in CATALOG}

HAT_IDS=[52,66,79,98]
SHIRT_IDS=[225,228,239,572,584,535]

def extract_hat(idx):
 c,r=idx%12,idx//12;b=HATS.crop((c*20,r*80,c*20+20,r*80+80));return {v:b.crop((0,i*20,20,(i+1)*20)) for i,v in enumerate(VIEWS)}
def extract_shirt(idx):
 c,r=idx%32,idx//32;b=SHIRTS.crop((c*8,r*32,c*8+8,r*32+32));return {v:b.crop((0,i*8,8,(i+1)*8)) for i,v in enumerate(VIEWS)}
def load_frames(folder,prefix): return {v:Image.open(folder/f'{prefix}_{v}.png').convert('RGBA') for v in VIEWS}
def save_frames(folder,prefix,frames):
 folder.mkdir(parents=True,exist_ok=True)
 for v,im in frames.items():im.save(folder/f'{prefix}_{v}.png')
def alpha_hash(frames):
 h=hashlib.sha256()
 for v in VIEWS:
  for p in frames[v].getdata():h.update(bytes((p[3],)))
 return h.hexdigest()
def lum(p):return .299*p[0]+.587*p[1]+.114*p[2]
def tint_keep_luma(px,target,strength=.88):
 Y=lum(px); th,ts,tv=colorsys.rgb_to_hsv(*(c/255 for c in target)); rr,gg,bb=colorsys.hsv_to_rgb(th,max(.25,ts),max(.12,min(1,Y/255)))
 raw=[px[i]*(1-strength)+255*q*strength for i,q in enumerate((rr,gg,bb))];cur=.299*raw[0]+.587*raw[1]+.114*raw[2];d=Y-cur
 rgb=[max(0,min(255,round(q+d))) for q in raw];return (*rgb,px[3])
def accent(theme):
 h=PALETTES[theme]['ramps']['accent'][-2].lstrip('#');return tuple(int(h[i:i+2],16) for i in (0,2,4))
def trim(theme):
 ramp=PALETTES[theme]['ramps']['trim'];h=ramp[len(ramp)//2].lstrip('#');return tuple(int(h[i:i+2],16) for i in (0,2,4))
def frame_changed(a,b):
 n=d=0;tot=0
 for v in VIEWS:
  for p,q in zip(a[v].getdata(),b[v].getdata()):
   if not p[3]:continue
   tot+=1
   if p!=q:n+=1;d+=math.dist(p[:3],q[:3])
 return {'ratio':round(n/max(1,tot),4),'avgDelta':round(d/max(1,n),2),'pixels':n}

def apply_shirt_grammar(frames,idx,category,theme):
 out={v:frames[v].copy() for v in VIEWS}; changed=[]; front=out['front']; w,h=front.size; tgt=accent(theme)
 # grammar references are about placement/scale only; no literal donor pixels are copied.
 if category=='horizontal_stripe_or_band':
  y=max(2,min(h-3,round(h*.55)))
  for x in range(1,w-1):
   p=front.getpixel((x,y))
   if p[3]:front.putpixel((x,y),tint_keep_luma(p,tgt,.92));changed.append((x,y))
 elif category=='placket_or_buttons':
  x=w//2
  for y in range(2,h-1,2):
   p=front.getpixel((x,y))
   if p[3]:front.putpixel((x,y),tint_keep_luma(p,tgt,.96));changed.append((x,y))
 elif category=='checker_or_plaid':
  for y in range(2,h-1):
   for x in range(1,w-1):
    if (x+y)%2==0:
     p=front.getpixel((x,y))
     if p[3]:front.putpixel((x,y),tint_keep_luma(p,trim(theme),.70));changed.append((x,y))
 elif category=='compact_graphic':
  cx=w//2; pts=[(cx,3),(cx-1,4),(cx,4),(cx+1,4)]
  for x,y in pts:
   if 0<=x<w and 0<=y<h:
    p=front.getpixel((x,y))
    if p[3]:front.putpixel((x,y),tint_keep_luma(p,tgt,.98));changed.append((x,y))
 return out,changed

def choose_shirt_cap(idx):
 caps=CAP.get(('shirt',idx),{}).get('capabilities',[])
 # Deliberately cover different reviewed vanilla grammars in the proof batch.
 preferred={225:'horizontal_stripe_or_band',228:'placket_or_buttons',239:'compact_graphic',572:'checker_or_plaid'}
 cat=preferred.get(idx)
 if idx==535:return None,'low_capacity_fallback'
 if idx==584:return None,'region_material_only_control'
 support={
  'horizontal_stripe_or_band':'horizontal_band_or_stripe',
  'placket_or_buttons':'central_placket_or_buttons',
  'compact_graphic':'compact_graphic_candidate',
  'checker_or_plaid':'dense_pattern_candidate'}
 if cat and idx in REVIEW.get(cat,[]) and support[cat] in caps:return cat,'reviewed_seed_and_target_supported'
 return None,'no_reviewed_grammar_support'

def fallback_colorway(source,theme):
 out={v:source[v].copy() for v in VIEWS}; tgt=trim(theme)
 for v,im in out.items():
  for y in range(im.height):
   for x in range(im.width):
    p=im.getpixel((x,y))
    if p[3] and lum(p)>38:
     im.putpixel((x,y),tint_keep_luma(p,tgt,.76))
 return out

def hat_name(idx):
 raw=HAT_DATA.get(str(idx),'')
 return raw.split('/')[0] if raw else ''

def contact(records,kind,path):
 rows=[r for r in records if r['kind']==kind];sc=8 if kind=='hat' else 14; size=20 if kind=='hat' else 8
 framew=size*sc; gap=12
 groupw=4*framew+3*gap
 source_x=70
 variant_x=source_x+groupw+(120 if kind=='hat' else 110)
 W=variant_x+groupw+80
 rowh=255 if kind=='hat' else 230;H=64+len(rows)*rowh
 s=Image.new('RGBA',(W,H),(240,238,232,255));d=ImageDraw.Draw(s)
 d.text((14,10),f'STARDEW-ONLY V8 {kind.upper()} MIXED BATCH',fill=(20,20,20,255))
 d.text((14,29),'SOURCE | GENERATED VARIANT | capabilities used/skipped (no rarity)',fill=(55,55,55,255))
 for ri,r in enumerate(rows):
  y0=64+ri*rowh;f=OUT/r['dir']
  nm=f" ({hat_name(r['sourceIndex'])})" if kind=='hat' and hat_name(r['sourceIndex']) else ''
  d.text((14,y0),f"{kind.upper()} #{r['sourceIndex']}{nm}  used={','.join(r['used']) or 'none'}  skipped={','.join(r['skipped']) or 'none'}",fill=(30,30,30,255))
  for x0,lab,pref in ((source_x,'SOURCE','source'),(variant_x,'VARIANT','variant')):
   d.text((x0,y0+20),lab,fill=(65,65,65,255));x=x0
   for v in VIEWS:
    im=Image.open(f/f'{pref}_{v}.png').convert('RGBA');big=im.resize((framew,framew),Image.Resampling.NEAREST);s.alpha_composite(big,(x,y0+42));d.text((x,y0+45+framew),v[0].upper(),fill=(70,70,70,255));x+=framew+gap
  d.text((14,y0+rowh-28),f"{r['notes']}  | delta {r['difference']}",fill=(65,65,65,255))
 s.save(path)

if OUT.exists():shutil.rmtree(OUT)
OUT.mkdir(parents=True)
records=[]
# Hats: use existing proven color/material/region/band treatment only; no generic motifs.
for idx in HAT_IDS:
 source=extract_hat(idx); d5=V5/f'hat_{idx:03d}'; d4=V4/f'hat_{idx:03d}'; d6=V6/f'hat_{idx:03d}'
 used=[];skipped=['generic_motif'];notes=[]
 if d5.exists(): variant=load_frames(d5,'a');used+=['colorway','region_style'];notes.append('v5 region-style base')
 elif d4.exists(): variant=load_frames(d4,'material');used+=['colorway','material'];notes.append('v4 material base')
 else: variant={v:source[v].copy() for v in VIEWS};notes.append('source fallback')
 if d6.exists():
  meta=json.loads((d6/'motif_component.json').read_text())
  if meta.get('wrapApplied'):
   variant=load_frames(d6,'wrap');used.append('wrap_trim');notes.append('source-safe wrap trim')
  else:skipped.append('wrap_trim')
 assert alpha_hash(source)==alpha_hash(variant)
 folder=OUT/f'hat_{idx:03d}';save_frames(folder,'source',source);save_frames(folder,'variant',variant)
 rec={'dir':folder.name,'kind':'hat','sourceIndex':idx,'detected':CAP.get(('hat',idx),{}).get('capabilities',[]),'used':used,'skipped':skipped,'notes':'; '.join(notes),'difference':frame_changed(source,variant)}
 (folder/'manifest.json').write_text(json.dumps(rec,indent=2)+'\n');records.append(rec)
# Shirts: use reviewed grammar only when target classifier supports it; otherwise safe fallback.
for idx in SHIRT_IDS:
 source=extract_shirt(idx); d5=V5/f'shirt_{idx:03d}'; d4=V4/f'shirt_{idx:03d}'; d3=V3/f'shirt_{idx:03d}'
 used=[];skipped=[];notes=[]
 theme=json.loads((d3/'remix.json').read_text())['themeB'] if d3.exists() else ('COASTAL_SEAFOAM_CORAL' if idx%2 else 'AUTUMN_OCHRE_PLUM')
 if d5.exists(): base=load_frames(d5,'a');used+=['colorway','region_style'];notes.append('v5 base')
 elif d4.exists(): base=load_frames(d4,'material');used+=['colorway','material'];notes.append('v4 base')
 elif d3.exists(): base=load_frames(d3,'a');used+=['colorway'];notes.append('v3 base')
 else: base=fallback_colorway(source,theme);used+=['colorway'];notes.append('v8 source-safe colorway base')
 cat,reason=choose_shirt_cap(idx)
 if cat:
  variant,cells=apply_shirt_grammar(base,idx,cat,theme);used.append(cat);notes.append(f'{cat} grammar applied ({len(cells)} px)')
 else:
  variant=base;skipped.append('shirt_graphic_grammar');notes.append(reason)
 assert alpha_hash(source)==alpha_hash(variant)
 folder=OUT/f'shirt_{idx:03d}';save_frames(folder,'source',source);save_frames(folder,'variant',variant)
 rec={'dir':folder.name,'kind':'shirt','sourceIndex':idx,'detected':CAP.get(('shirt',idx),{}).get('capabilities',[]),'used':used,'skipped':skipped,'notes':'; '.join(notes),'difference':frame_changed(source,variant)}
 (folder/'manifest.json').write_text(json.dumps(rec,indent=2)+'\n');records.append(rec)
contact(records,'hat',OUT/'STARDEW_ONLY_V8_HAT_MIXED_CONTACT.png')
contact(records,'shirt',OUT/'STARDEW_ONLY_V8_SHIRT_MIXED_CONTACT.png')
(OUT/'manifest.json').write_text(json.dumps({'schema':'stardew-only-mixed-batch/v8','boundary':'isolated experiment; reviewed vanilla grammar only; no rarity; no production promotion','records':records},indent=2)+'\n')
print('PASS',len(records),'items')
for r in records:print(r['kind'],r['sourceIndex'],'used=',r['used'],'skipped=',r['skipped'],r['difference'])
