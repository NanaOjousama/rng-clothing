from __future__ import annotations
from pathlib import Path
from collections import deque,Counter
import json,math
import numpy as np
from PIL import Image
from prototype_core import FACINGS,SCOPES,uv_maps,region_map,edge_mask,pattern_hit,cleanup_pattern,draw_overlay,REGION_COLORS

def rgba(path:Path)->np.ndarray:return np.array(Image.open(path).convert('RGBA'),dtype=np.uint8)
def save(arr,path):Image.fromarray(arr.astype(np.uint8),'RGBA').save(path)
def bbox(alpha):
 ys,xs=np.where(alpha>0)
 if len(xs)==0:return (0,0,alpha.shape[1]-1,alpha.shape[0]-1)
 return (int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max()))
def hx(s):
 s=s.lstrip('#');return tuple(int(s[i:i+2],16) for i in (0,2,4))
def lum(c):return .299*c[0]+.587*c[1]+.114*c[2]
def preserve_luma(target,source):
 sl=max(10.0,lum(source));tl=max(10.0,lum(target));f=sl/tl
 return tuple(max(0,min(255,round(x*f))) for x in target)
def blend(a,b,t):return tuple(max(0,min(255,round(a[i]*(1-t)+b[i]*t))) for i in range(3))
def region_target(plan,reg):
 pal=plan['region_palettes'].get(reg,plan['region_palettes'].get('whole',['#808080','#b0b0b0']))
 return hx(pal[0]),hx(pal[min(1,len(pal)-1)]),hx(pal[min(2,len(pal)-1)])
def in_band(plan,reg,v):
 for b in plan.get('color_bands',[]):
  if b.get('region') not in (None,reg):continue
  if b['top']<=v<=b['bottom']:return hx(b['color'])
 return None

def cleanup_overlay(arr,min_component=2):
 a=arr[:,:,3]>0;h,w=a.shape;seen=np.zeros_like(a,bool)
 for y in range(h):
  for x in range(w):
   if not a[y,x] or seen[y,x]:continue
   q=deque([(x,y)]);seen[y,x]=1;comp=[]
   while q:
    xx,yy=q.popleft();comp.append((xx,yy))
    for nx,ny in ((xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)):
     if 0<=nx<w and 0<=ny<h and a[ny,nx] and not seen[ny,nx]:seen[ny,nx]=1;q.append((nx,ny))
   if len(comp)<min_component:
    for xx,yy in comp:arr[yy,xx]=(0,0,0,0)
 return arr

def render_hybrid_view(src,control_id,plan,facing):
 alpha=src[:,:,3];u,v=uv_maps(alpha,facing);regions=region_map(control_id,alpha,v,u);edge=edge_mask(alpha)
 out=src.copy();base=src.copy();kind=plan['semantic_pattern'];pm=np.zeros(alpha.shape,bool);changed=np.zeros(alpha.shape,bool)
 for y in range(src.shape[0]):
  for x in range(src.shape[1]):
   if not alpha[y,x] or edge[y,x]:continue
   reg=regions[y,x];source=tuple(int(z) for z in src[y,x,:3]);primary,secondary,accent=region_target(plan,reg)
   band=in_band(plan,reg,float(v[y,x]));target=band or primary
   t=plan.get('palette_strength',.34)+(0.14 if band else 0)
   tinted=preserve_luma(target,source);new=blend(source,tinted,t)
   if pattern_hit(kind,float(u[y,x]),float(v[y,x]),x,y):pm[y,x]=True
   base[y,x]=(*new,src[y,x,3]);out[y,x]=base[y,x]
 pm=cleanup_pattern(pm,alpha,edge,kind)
 for y,x in zip(*np.where(pm)):
  reg=regions[y,x];source=tuple(int(z) for z in base[y,x,:3]);_,secondary,accent=region_target(plan,reg)
  target=preserve_luma(secondary,source);new=blend(source,target,plan.get('pattern_strength',.42));out[y,x]=(*new,255);changed[y,x]=True
 # PT motif/facing-scope system, but constrained by our occupancy and cleaned.
 overlay=np.zeros_like(src);draw_overlay(overlay,alpha,regions,plan,facing);overlay=cleanup_overlay(overlay,2)
 om=overlay[:,:,3]>0
 for y,x in zip(*np.where(om)):
  if edge[y,x]:continue
  source=tuple(int(z) for z in out[y,x,:3]);target=tuple(int(z) for z in overlay[y,x,:3]);new=blend(source,target,plan.get('overlay_strength',.76));out[y,x]=(*new,255);changed[y,x]=True
 # Track all non-edge color deltas, but preserve alpha and exact outline pixels.
 changed |= np.any(out[:,:,:3]!=src[:,:,:3],axis=2)&(alpha>0)
 out[edge]=src[edge]
 # Debug layers.
 occ=np.zeros_like(src);occ[alpha>0]=(245,245,245,255);occ[edge]=(40,40,40,255)
 regdbg=np.zeros_like(src)
 for reg,c in REGION_COLORS.items():regdbg[(regions==reg)&(alpha>0)]=(*c,255)
 delta=np.zeros_like(src);delta[changed]=(245,80,80,255);delta[edge]=(40,40,40,255)
 return out,base,overlay,occ,regdbg,delta,int(pm.sum()),int(changed.sum()),int((alpha>0).sum())

def compile_hybrid(control_root:Path,control_id:str,plan:dict,outdir:Path):
 outdir.mkdir(parents=True,exist_ok=True);views=[];pattern_cells={};changed={};ratios={}
 for facing in FACINGS:
  src=rgba(control_root/control_id/f'{facing}.png');final,base,overlay,occ,reg,delta,npat,nchg,nopaque=render_hybrid_view(src,control_id,plan,facing)
  save(final,outdir/f'{facing}.png');save(base,outdir/f'{facing}_base.png');save(overlay,outdir/f'{facing}_overlay.png');save(occ,outdir/f'{facing}_occupancy.png');save(reg,outdir/f'{facing}_regions.png');save(delta,outdir/f'{facing}_delta.png')
  pattern_cells[facing]=npat;changed[facing]=nchg;ratios[facing]=round(nchg/max(1,nopaque),4)
  views.append({'facing':facing,'size':[int(src.shape[1]),int(src.shape[0])],'opaque':nopaque,'changed':nchg,'changeRatio':ratios[facing]})
 payload={'schema':'pt-private-lab03-hybrid-draft/v1','control':control_id,'plan':plan,'views':views,'patternCellsAfterCleanup':pattern_cells,'changedPixels':changed,'changeRatioByView':ratios,'outlinePreservedExactly':True,'sourcePixelsAreBaseAuthority':True}
 (outdir/'hybrid_draft.json').write_text(json.dumps(payload,indent=2)+'\n');return payload
