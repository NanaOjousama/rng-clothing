#!/usr/bin/env python3
"""Vanilla-only wardrobe remix v3: different piece, same Stardew construction.

Unlike v2, this NEVER guesses body/trim/accent from brightness or coverage.
The source's exact alpha, pixel clusters, unique color identities, and luminance
relationships remain authority.  We only rotate each SOURCE COLOR FAMILY toward
a curated generator palette lane using an injective, luminance-preserving map.

A generated output must also pass a novelty gate: it may not be identical or a
near-duplicate of its vanilla source.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import colorsys, hashlib, json, math, shutil

ROOT=Path(__file__).resolve().parents[1]
GAME=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer')
OUT=ROOT/'experiments/vanilla_source_only_random_batch_02_distinct'
HATS=Image.open(GAME/'hats.png').convert('RGBA')
SHIRTS=Image.open(GAME/'shirts.png').convert('RGBA')
PALETTES={p['id']:p for p in json.loads((ROOT/'authored/palettes.json').read_text())['palettes']}
VIEWS=('front','right','left','back')
# Same items as v2: intentional regression set, not cherry-picked.
HAT_IDS=[52,66,79,98,33,82]
SHIRT_IDS=[527,481,225,584,535,424]
# Two visibly different but restrained colorways per source.
THEMES=[
 ('COASTAL_SEAFOAM_CORAL','AUTUMN_OCHRE_PLUM'),
 ('GOTHIC_WINE_ASH','SPRING_SAGE_PETAL'),
 ('SAILOR_COBALT_CREAM','DESERT_CLAY_TURQUOISE'),
 ('FIELD_CANVAS_MOSS','PASTEL_PEACH_LILAC'),
 ('FORMAL_PEARL_MIDNIGHT','EMBER_SUN_CHARCOAL'),
 ('CUTE_OLIVE_GOLD','CUTE_ROSE_CREAM'),
 ('CYBER_CYAN_MAGENTA','WORKWEAR_DENIM_RUST'),
 ('FIELD_CANVAS_MOSS','COASTAL_SEAFOAM_CORAL'),
 ('EMBER_SUN_CHARCOAL','CELESTIAL_INDIGO_STAR'),
 ('SAILOR_COBALT_CREAM','AUTUMN_OCHRE_PLUM'),
 ('DESERT_CLAY_TURQUOISE','GOTHIC_WINE_ASH'),
 ('COASTAL_SEAFOAM_CORAL','CUTE_COCOA_GOLD'),
]


def extract_hat(idx):
 c,r=idx%12,idx//12; b=HATS.crop((c*20,r*80,c*20+20,r*80+80)); return {v:b.crop((0,i*20,20,(i+1)*20)) for i,v in enumerate(VIEWS)}
def extract_shirt(idx):
 c,r=idx%32,idx//32; b=SHIRTS.crop((c*8,r*32,c*8+8,r*32+32)); return {v:b.crop((0,i*8,8,(i+1)*8)) for i,v in enumerate(VIEWS)}
def y(rgb): return .299*rgb[0]+.587*rgb[1]+.114*rgb[2]
def chroma(rgb):
 Y=y(rgb); return math.hypot(rgb[2]-Y, rgb[0]-Y)
def alpha_digest(frames):
 h=hashlib.sha256()
 for v in VIEWS:
  h.update(v.encode()); im=frames[v]
  for p in im.getdata(): h.update(bytes((p[3],)))
 return h.hexdigest()
def pixel_digest(frames):
 h=hashlib.sha256()
 for v in VIEWS: h.update(v.encode()+frames[v].tobytes())
 return h.hexdigest()
def counts(frames):
 d={}
 for im in frames.values():
  for p in im.getdata():
   if p[3]: d[p[:3]]=d.get(p[:3],0)+1
 return d

def hue_point(rgb):
 r,g,b=[c/255 for c in rgb]; h,s,v=colorsys.rgb_to_hsv(r,g,b)
 # circular hue with saturation as radius; grayscale falls near origin
 return (math.cos(2*math.pi*h)*s, math.sin(2*math.pi*h)*s)
def dist2(a,b): return (a[0]-b[0])**2+(a[1]-b[1])**2

def color_families(frames,max_k=3):
 c=counts(frames); colors=list(c)
 # Keep extremely dark construction colors as protected outline family.
 protected={rgb for rgb in colors if y(rgb)<=28}
 work=[rgb for rgb in colors if rgb not in protected]
 if not work: return {},protected,[]
 # Estimate useful family count from chromatic diversity; 1..3 only.
 chromatic=[rgb for rgb in work if colorsys.rgb_to_hsv(*(q/255 for q in rgb))[1]>.12]
 k=min(max_k,max(1,len({round(math.atan2(hue_point(q)[1],hue_point(q)[0]),1) for q in chromatic})))
 # weighted farthest-first in hue/chroma space
 pts={q:hue_point(q) for q in work}
 first=max(work,key=lambda q:c[q]); centers=[pts[first]]
 while len(centers)<k:
  q=max(work,key=lambda q:min(dist2(pts[q],z) for z in centers)*max(1,c[q])**.25)
  centers.append(pts[q])
 for _ in range(10):
  bins=[[] for _ in centers]
  for q in work: bins[min(range(k),key=lambda i:dist2(pts[q],centers[i]))].append(q)
  new=[]
  for old,b in zip(centers,bins):
   if not b: new.append(old); continue
   total=sum(c[q] for q in b); new.append((sum(pts[q][0]*c[q] for q in b)/total,sum(pts[q][1]*c[q] for q in b)/total))
  if all(dist2(a,b)<1e-9 for a,b in zip(new,centers)): break
  centers=new
 assign={q:min(range(k),key=lambda i:dist2(pts[q],centers[i])) for q in work}
 coverage=[sum(c[q] for q in work if assign[q]==i) for i in range(k)]
 order=sorted(range(k),key=lambda i:-coverage[i])
 # Largest source family -> body, then trim, then accent. This labels source hue families,
 # not physical regions, and never changes pixel membership or shade topology.
 lane_names=['body','trim','accent']; lane_for={cluster:lane_names[pos] for pos,cluster in enumerate(order)}
 return {q:lane_for[assign[q]] for q in work},protected,coverage

def target_chroma(rgb):
 Y=y(rgb); cb=rgb[2]-Y; cr=rgb[0]-Y; mag=math.hypot(cb,cr)
 if mag<1e-6: return (0,0)
 return cb/mag,cr/mag

def recolor_same_luma(src,target_rgb,minimum_chroma=24):
 """Move chroma toward target hue while retaining source luminance."""
 Y=y(src); srcmag=chroma(src); unit=target_chroma(target_rgb)
 # Keep source chroma personality, but colorize gray mids enough to be visibly different.
 mag=max(srcmag*1.00, (minimum_chroma+8) if 38<Y<225 else 12)
 # RGB from Y + Cr/Cb direction using our simple opponent representation.
 cb,cr=unit[0]*mag,unit[1]*mag
 # We define cr=R-Y and cb=B-Y, solve G from the luma equation.
 for scale in (1,.9,.8,.7,.6,.5,.4,.3,.2,.1,0):
  R=Y+cr*scale; B=Y+cb*scale; G=(Y-.299*R-.114*B)/.587
  if min(R,G,B)>=0 and max(R,G,B)<=255:
   return tuple(round(v) for v in (R,G,B))
 return tuple(round(Y) for _ in range(3))

def lane_target(palette,lane):
 ramp=palette['ramps'][lane]; h=ramp[len(ramp)//2].lstrip('#'); return tuple(int(h[i:i+2],16) for i in (0,2,4))
def build_mapping(frames,palette):
 fam,protected,coverage=color_families(frames)
 mapping={}; used=set(protected)
 # Deterministic per-RGB mapping. Same source RGB maps identically in all 4 views.
 for rgb,lane in sorted(fam.items(),key=lambda kv:(y(kv[0]),kv[0])):
  tgt=recolor_same_luma(rgb,lane_target(palette,lane))
  # Enforce injectivity without flattening shade ordering. Tiny chroma nudge only.
  if tgt in used:
   base=tgt
   found=None
   for d in range(1,7):
    for cand in ((min(255,base[0]+d),base[1],base[2]),(base[0],min(255,base[1]+d),base[2]),(base[0],base[1],min(255,base[2]+d)),(max(0,base[0]-d),base[1],base[2])):
     if cand not in used and abs(y(cand)-y(rgb))<=2.25: found=cand; break
    if found: break
   tgt=found or rgb
  mapping[rgb]=tgt; used.add(tgt)
 return mapping,protected,coverage

def apply(frames,mapping):
 out={}
 for v,im in frames.items():
  dst=Image.new('RGBA',im.size,(0,0,0,0)); data=[]
  for p in im.getdata():
   if p[3] and p[:3] in mapping: data.append((*mapping[p[:3]],p[3]))
   else: data.append(p)
  dst.putdata(data); out[v]=dst
 return out

def measure_variant(source,out,mapping):
 assert alpha_digest(source)==alpha_digest(out),'alpha drift'
 total=changed=0; delta=0
 for v in VIEWS:
  for a,b in zip(source[v].getdata(),out[v].getdata()):
   if not a[3]: continue
   total+=1
   if a!=b:
    changed+=1; delta+=math.dist(a[:3],b[:3])
    assert a[:3] in mapping and b[:3]==mapping[a[:3]]
 vals=[mapping[k] for k in mapping]
 assert len(vals)==len(set(vals)),'shade/color merge'
 ratio=changed/total; avg=delta/max(1,changed)
 max_dy=max((abs(y(k)-y(v)) for k,v in mapping.items()),default=0)
 assert max_dy<=2.25, f'luma drift {max_dy}'
 return {'changedOpaqueRatio':round(ratio,4),'avgRgbDeltaChanged':round(avg,2),'maxLumaDrift':round(max_dy,3),'uniqueSourceColorsMapped':len(mapping)}

def passes_novelty(m):
 return m['changedOpaqueRatio']>=.40 and m['avgRgbDeltaChanged']>=18

def frame_distance(a,b):
 total=changed=0; delta=0
 for v in VIEWS:
  for p,q in zip(a[v].getdata(),b[v].getdata()):
   if not p[3]: continue
   total+=1
   if p!=q:
    changed+=1; delta+=math.dist(p[:3],q[:3])
 return changed/max(1,total), delta/max(1,changed)

def choose_variants(source):
 candidates=[]
 for name,pal in PALETTES.items():
  mapping,_,_=build_mapping(source,pal); out=apply(source,mapping); met=measure_variant(source,out,mapping)
  if passes_novelty(met):
   candidates.append((met['avgRgbDeltaChanged']*met['changedOpaqueRatio'],name,mapping,out,met))
 if len(candidates)<2: raise AssertionError(f'fewer than 2 non-duplicate palette variants ({len(candidates)})')
 candidates.sort(reverse=True,key=lambda x:x[0])
 first=candidates[0]
 viable=[]
 for cand in candidates[1:]:
  ratio,avg=frame_distance(first[3],cand[3])
  if ratio>=.35 and avg>=16: viable.append((ratio*avg,cand))
 second=max(viable,key=lambda x:x[0])[1] if viable else candidates[1]
 return first,second

def save_frames(d,prefix,frames):
 d.mkdir(parents=True,exist_ok=True)
 for v in VIEWS: frames[v].save(d/f'{prefix}_{v}.png')

def make_contact(records):
 # source + variant A + variant B; all four views displayed at nearest-neighbor scale.
 W=1500; rowh=230; H=58+len(records)*rowh
 sheet=Image.new('RGBA',(W,H),(239,237,231,255)); dr=ImageDraw.Draw(sheet)
 dr.text((15,10),'STARDEW-ONLY REMIX V3 — DIFFERENT PIECE, SAME VANILLA CONSTRUCTION',fill=(20,20,20,255))
 dr.text((15,30),'SOURCE | VARIANT A | VARIANT B   • exact alpha/geometry • source shading preserved • near-duplicates rejected',fill=(50,50,50,255))
 for ri,rec in enumerate(records):
  y0=58+ri*rowh; d=OUT/rec['dir']; sc=7 if rec['kind']=='hat' else 12
  dr.text((15,y0),f"{rec['kind'].upper()} #{rec['sourceIndex']}  | A {rec['themeA']} | B {rec['themeB']}",fill=(25,25,25,255))
  for ci,(label,prefix) in enumerate((('SOURCE','source'),('VARIANT A','a'),('VARIANT B','b'))):
   x0=95+ci*465; dr.text((x0,y0+18),label,fill=(65,65,65,255)); x=x0
   for v in VIEWS:
    im=Image.open(d/f'{prefix}_{v}.png').convert('RGBA'); big=im.resize((im.width*sc,im.height*sc),Image.Resampling.NEAREST)
    sheet.alpha_composite(big,(x,y0+38)); dr.text((x,y0+40+big.height),v[0].upper(),fill=(70,70,70,255)); x+=big.width+10
  dr.text((15,y0+198),f"A Δ {rec['metricsA']['changedOpaqueRatio']:.0%} / {rec['metricsA']['avgRgbDeltaChanged']:.1f}   B Δ {rec['metricsB']['changedOpaqueRatio']:.0%} / {rec['metricsB']['avgRgbDeltaChanged']:.1f}",fill=(65,65,65,255))
 sheet.save(OUT/'STARDEW_ONLY_REMIX_V3_CONTACT.png')

if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)
records=[]; items=[('hat',i,extract_hat) for i in HAT_IDS]+[('shirt',i,extract_shirt) for i in SHIRT_IDS]
for n,(kind,idx,extract) in enumerate(items):
 source=extract(idx); d=OUT/f'{kind}_{idx:03d}'
 A,B=choose_variants(source)
 _,tA,mA,a,metA=A; _,tB,mB,b,metB=B
 print('SELECTED',kind,idx,tA,metA,'|',tB,metB,flush=True)
 save_frames(d,'source',source); save_frames(d,'a',a); save_frames(d,'b',b)
 meta={'kind':kind,'sourceIndex':idx,'themeA':tA,'themeB':tB,'sourcePixelSha256':pixel_digest(source),'sourceAlphaSha256':alpha_digest(source),
       'rules':['exact source alpha/coordinates locked','same source RGB maps identically across all views','extreme dark construction colors protected','no source shade quantization','no procedural texture/pattern','injective source-color mapping','max luminance drift <= 2.25','near-duplicate rejection: changed opaque >= 40% and avg changed RGB delta >= 18','variant-to-variant diversity preferred: >=35% pixels and avg RGB delta >=16'],
       'metricsA':metA,'metricsB':metB,'mappingA':{','.join(map(str,k)):list(v) for k,v in mA.items()},'mappingB':{','.join(map(str,k)):list(v) for k,v in mB.items()}}
 (d/'remix.json').write_text(json.dumps(meta,indent=2)+'\n')
 records.append({'dir':d.name,**{k:meta[k] for k in ('kind','sourceIndex','themeA','themeB','metricsA','metricsB')}})
make_contact(records)
manifest={'schema':'stardew-only-remix/v3','purpose':'meaningfully different vanilla-derived wardrobe variants without generated geometry','regressionSet':{'hats':HAT_IDS,'shirts':SHIRT_IDS},'records':records}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('PASS',len(records),'vanilla sources ->',len(records)*2,'distinct variants')
for r in records: print(r['kind'],r['sourceIndex'],'A',r['metricsA'],'B',r['metricsB'])
print(OUT/'STARDEW_ONLY_REMIX_V3_CONTACT.png')
