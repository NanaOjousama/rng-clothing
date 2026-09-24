from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import onnxruntime as ort
ROOT=Path('/run/media/deck/USD00/RNG_clothing');sys.path.insert(0,str(ROOT))
from generator.source_respecting_hat_remix import source_frames,_parts,_validate_explicit_roles,_copy,_assert_locked_geometry,VIEWS
from v5.pngio import write_rgba_png,read_rgba_png
MODEL=Path('/home/deck/Downloads/PhotoTailor/models/marqo_fashion_siglip_vision_uint8.onnx')
LABELS=Path('/home/deck/Downloads/PhotoTailor/models/fashion_siglip_labels.json')
OUT=ROOT/'experiments/photo_tailor_bridge_02'
REFS=[
 ROOT/'mario hat/mariofront.jpg', ROOT/'mario hat/super-mario-bros-mario-cosplay-hat-5366136.jpg',
 ROOT/'mario hat/rightsidevew.webp', ROOT/'mario hat/marioback.jpg',
 ROOT/'slouch beanie motif/superslouuch_beanie.jpeg', ROOT/'slouch beanie motif/pattern_smalslouch.jpeg',
 ROOT/'slouch beanie motif/pattern+labelmotif.jpeg', ROOT/'slouch beanie motif/pom_motif.jpeg'
]

def prep(p):
 im=Image.open(p).convert('RGB');w,h=im.size;s=min(w,h);im=im.crop(((w-s)//2,(h-s)//2,(w+s)//2,(h+s)//2)).resize((224,224),Image.Resampling.BICUBIC)
 a=np.asarray(im,dtype=np.float32)/255.;a=(a-.5)/.5;return np.transpose(a,(2,0,1))[None]
def norm(v):
 n=np.linalg.norm(v);return v if n<1e-9 else v/n
class Analyzer:
 def __init__(self):
  self.s=ort.InferenceSession(str(MODEL),providers=['CPUExecutionProvider']);self.labels=json.load(open(LABELS))['labels']
 def run(self,p):
  e=norm(self.s.run(None,{'pixel_values':prep(p)})[0][0]);g={}
  for l in self.labels:
   sc=float(np.dot(e,norm(np.asarray(l['embedding'],dtype=np.float32))));g.setdefault(l['group'],[]).append((sc,l['value'],l.get('category','')))
  for k in g:g[k].sort(reverse=True)
  return {k:v[:5] for k,v in g.items()}

def extract_palette(p):
 im=Image.open(p).convert('RGB');w,h=im.size
 # Hat-focused crop: upper/central image, then discount background-like corner colors.
 crop=im.crop((int(w*.12),0,int(w*.88),int(h*.72)));crop.thumbnail((180,180))
 corners=[crop.getpixel((0,0)),crop.getpixel((crop.width-1,0)),crop.getpixel((0,crop.height-1)),crop.getpixel((crop.width-1,crop.height-1))]
 bg=tuple(round(sum(c[i] for c in corners)/4) for i in range(3))
 q=crop.quantize(colors=14,method=Image.Quantize.MEDIANCUT).convert('RGB');cnt={}
 for c in q.getdata():
  if min(c)>245 or max(c)<12:continue
  dist=sum((c[i]-bg[i])**2 for i in range(3))**.5
  if dist<24:continue
  sat=max(c)-min(c); weight=1.0+(sat/255)*1.8
  cnt[c]=cnt.get(c,0)+weight
 cols=sorted(cnt,key=cnt.get,reverse=True)
 return (cols[0] if cols else (150,150,150)),cols[:5]

def tint(px,c):
 if not px[3]:return px
 y=.299*px[0]+.587*px[1]+.114*px[2]
 return (round(c[0]*y/255),round(c[1]*y/255),round(c[2]*y/255),px[3])

def proto_cap_frames():
 base=ROOT/'experiments/dad_cap/production_20x20/inspect_x8'
 # inspect_x8 is enlarged; use production native if available, else downsample x8 safely
 native=ROOT/'experiments/dad_cap/production_20x20'
 out={}
 mapping={'front':'front_20.png','left':'left_20.png','right':'right_20.png','back':'back_20.png'}
 for v,n in mapping.items():
  candidates=[native/n,base/n]
  p=next((x for x in candidates if x.exists()),None)
  if p is None: raise FileNotFoundError(n)
  im=Image.open(p).convert('RGBA')
  if im.width>40:im=im.resize((im.width//8,im.height//8),Image.Resampling.NEAREST)
  out[v]=[[tuple(im.getpixel((x,y))) for x in range(im.width)] for y in range(im.height)]
 return out

def tint_all_source(frames,c):
 out=_copy(frames)
 for v in out:
  for y,row in enumerate(out[v]):
   for x,p in enumerate(row):
    if p[3]: out[v][y][x]=tint(p,c)
 return out

def choose(p,s):
 n=p.stem.lower();patterns=[x[1] for x in s['pattern'][:3]];sils=[x[1] for x in s['silhouette'] if x[2] in ('','hat')][:3]
 if 'mario' in n or 'cap' in n or (sils and sils[0]=='cap'):return 'proto_dad_cap','Dad Cap','reference+siglip cap'
 fam='beanie';state='Beanie (Floppy)' if ('slouch' in n or 'floppy' in n) else 'Beanie'
 if 'pattern' in n and 'horizontal_stripes' in patterns: state='Beanie (Floppy)'
 return fam,state,'reference+siglip beanie'

def render(fam,state,color,pattern='solid'):
 if fam=='proto_dad_cap':
  out=tint_all_source(proto_cap_frames(),color)
  return apply_pattern(out,pattern)
 spec=_parts()['families'][fam];raw,_=source_frames(spec['pack'],state);roles=_validate_explicit_roles(raw,fam,state);out=_copy(raw)
 for v in out:
  for y,row in enumerate(out[v]):
   for x,p in enumerate(row):
    if not p[3]:continue
    role=roles.get(f'{p[0]},{p[1]},{p[2]}','')
    if role.startswith(('body_','outline','shadow','mid','light','highlight','spec')):out[v][y][x]=tint(p,color)
 return apply_pattern(out,pattern)

def apply_pattern(out,pattern):
 if pattern not in ('horizontal_stripes','vertical_stripes','plaid','polka_dot'): return out
 for v in out:
  for y,row in enumerate(out[v]):
   for x,p in enumerate(row):
    if not p[3]: continue
    hit=(pattern=='horizontal_stripes' and y%3==1) or (pattern=='vertical_stripes' and x%4==1) or (pattern=='plaid' and (y%4==1 or x%5==1)) or (pattern=='polka_dot' and (x+y*2)%11==0)
    if hit: out[v][y][x]=(max(0,round(p[0]*.68)),max(0,round(p[1]*.68)),max(0,round(p[2]*.68)),p[3])
 return out

def main():
 if OUT.exists():
  import shutil;shutil.rmtree(OUT)
 OUT.mkdir(parents=True);an=Analyzer();rows=[]
 for i,p in enumerate(REFS,1):
  sc=an.run(p);fam,state,why=choose(p,sc);c,pal=extract_palette(p);pat=sc['pattern'][0][1];fr=render(fam,state,c,pat);d=OUT/f'{i:02d}_{fam}';d.mkdir()
  for v in VIEWS:write_rgba_png(d/f'{v}.png',fr[v])
  rows.append({'index':i,'reference':str(p.relative_to(ROOT)),'family':fam,'state':state,'reason':why,'rgb':c,'palette':pal,
   'category':[x[1:] for x in sc['category'][:3]],'silhouette':[x[1:] for x in sc['silhouette'][:3]],'pattern':[x[1:] for x in sc['pattern'][:3]]})
  print(i,p.name,'=>',fam,state,c,[x[1] for x in sc['pattern'][:3]],[x[1] for x in sc['silhouette'][:3]])
 (OUT/'manifest.json').write_text(json.dumps(rows,indent=2)+'\n');sheet(rows)

def sheet(rows):
 W=1600;H=270*len(rows);can=Image.new('RGB',(W,H),(238,236,229));dr=ImageDraw.Draw(can);font=ImageFont.load_default()
 for ri,e in enumerate(rows):
  y=ri*270;p=ROOT/e['reference'];im=Image.open(p).convert('RGB');im.thumbnail((350,220));can.paste(im,(10,y+38));dr.text((10,y+10),f"{e['index']:02d} {p.name[:48]}",fill=(15,15,15),font=font)
  dr.text((380,y+10),f"{e['family']} / {e['state']} / RGB {tuple(e['rgb'])}",fill=(15,15,15),font=font)
  dr.text((380,y+28),f"pattern: {', '.join(x[0] for x in e['pattern'])}",fill=(15,15,15),font=font)
  dr.text((380,y+46),f"silhouette: {', '.join(x[0] for x in e['silhouette'])}",fill=(15,15,15),font=font)
  for ci,v in enumerate(VIEWS):
   sp=Image.open(OUT/f"{e['index']:02d}_{e['family']}/{v}.png").convert('RGBA');bb=sp.getbbox();sp=sp.crop(bb) if bb else sp;scale=max(2,min(12,180//max(1,sp.width),160//max(1,sp.height)));sp=sp.resize((sp.width*scale,sp.height*scale),Image.Resampling.NEAREST)
   x=400+ci*270+(190-sp.width)//2;yy=y+80+(160-sp.height)//2;can.paste(sp,(x,yy),sp);dr.text((400+ci*270,y+64),v.upper(),fill=(15,15,15),font=font)
  for j,c in enumerate(e['palette']):dr.rectangle((1360+j*42,y+15,1394+j*42,y+47),fill=tuple(c),outline=(20,20,20))
 out=OUT/'PHOTO_TAILOR_BRIDGE_V2_CONTACT.png';can.save(out);print('CONTACT',out)
if __name__=='__main__':main()
