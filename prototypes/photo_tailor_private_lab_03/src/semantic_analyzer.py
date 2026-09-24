from __future__ import annotations
from pathlib import Path
from collections import defaultdict
import json,math
import numpy as np
from PIL import Image
import onnxruntime as ort

HERE=Path(__file__).resolve().parents[1]
MODEL=HERE/'vendor/photo_tailor_models/marqo_fashion_siglip_vision_uint8.onnx'
LABELS=HERE/'vendor/photo_tailor_models/fashion_siglip_labels.json'

def norm(v):
 n=float(np.linalg.norm(v));return v if n<1e-9 else v/n

def preprocess(path:Path):
 im=Image.open(path).convert('RGB');w,h=im.size;s=min(w,h);x=(w-s)//2;y=(h-s)//2
 im=im.crop((x,y,x+s,y+s)).resize((224,224),Image.Resampling.BICUBIC)
 a=np.asarray(im,dtype=np.float32)/255.0;a=(a-.5)/.5
 return np.transpose(a,(2,0,1))[None]

def palette(path:Path,category:str):
 im=Image.open(path).convert('RGB');w,h=im.size
 if category=='hat':im=im.crop((int(w*.08),0,int(w*.92),int(h*.78)))
 else:im=im.crop((int(w*.08),int(h*.03),int(w*.92),int(h*.97)))
 im.thumbnail((180,180));corners=[im.getpixel((0,0)),im.getpixel((im.width-1,0)),im.getpixel((0,im.height-1)),im.getpixel((im.width-1,im.height-1))]
 bg=tuple(round(sum(c[i] for c in corners)/4) for i in range(3));q=im.quantize(colors=16,method=Image.Quantize.MEDIANCUT).convert('RGB');cnt={}
 for c in q.getdata():
  if min(c)>248 or max(c)<8:continue
  dist=sum((c[i]-bg[i])**2 for i in range(3))**.5
  if dist<20:continue
  sat=max(c)-min(c);cnt[c]=cnt.get(c,0)+1.0+(sat/255.0)*1.6
 cols=sorted(cnt,key=cnt.get,reverse=True)[:6]
 if not cols:cols=[(120,120,120),(175,175,175)]
 return cols

def hx(c):return '#%02x%02x%02x'%tuple(int(x) for x in c)

class Analyzer:
 def __init__(self):
  self.session=ort.InferenceSession(str(MODEL),providers=['CPUExecutionProvider'])
  self.labels=json.load(open(LABELS))['labels']
 def analyze(self,path:Path,category_hint:str):
  emb=norm(self.session.run(None,{'pixel_values':preprocess(path)})[0][0]);groups=defaultdict(list)
  for lab in self.labels:
   cat=lab.get('category','')
   if cat and cat not in (category_hint,''):continue
   score=float(np.dot(emb,norm(np.asarray(lab['embedding'],dtype=np.float32))))
   groups[lab['group']].append({'value':lab['value'],'score':score,'category':cat})
  for g in groups:groups[g]=sorted(groups[g],key=lambda x:x['score'],reverse=True)[:5]
  cols=palette(path,category_hint)
  top=lambda g,default: groups.get(g,[{'value':default}])[0]['value'] if groups.get(g) else default
  patt=top('pattern','solid');canonical={'stripes':'horizontal_stripes','color_block':'colorblock'}.get(patt,patt)
  return {
   'categoryHint':category_hint,'categoryCandidates':groups.get('category',[])[:3],
   'silhouetteCandidates':groups.get('silhouette',[])[:4],
   'patternCandidates':groups.get('pattern',[])[:4],
   'coverageCandidates':groups.get('coverage',[])[:3],
   'necklineCandidates':groups.get('neckline',[])[:3],
   'detailCandidates':groups.get('detail',[])[:3],
   'semanticPattern':canonical,'paletteRgb':[list(x) for x in cols],'paletteHex':[hx(x) for x in cols],
   'primaryColor':hx(cols[0]),'secondaryColor':hx(cols[min(1,len(cols)-1)]),'accentColor':hx(cols[min(2,len(cols)-1)]),
  }
