from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from collections import deque,Counter
import json,math
import numpy as np
from PIL import Image

FACINGS=('front','right','left','back')
SCOPES={
 'ALL_FACINGS':set(FACINGS),'FRONT_ONLY':{'front'},'FRONT_SIDES':{'front','right','left'},
 'SIDES_ONLY':{'right','left'},'BACK_ONLY':{'back'},'FRONT_BACK':{'front','back'}
}
REGION_COLORS={'crown':(220,80,80),'band':(80,130,230),'brim':(225,185,70),'hem':(120,210,120),'lower':(170,110,210),'whole':(180,180,180)}
FAMILY_RULES={
 'beret':[(0,.76,'crown'),(.76,1.01,'band')],
 'beanie':[(0,.72,'crown'),(.72,1.01,'band')],
 'straw_hat':[(0,.53,'crown'),(.53,.66,'band'),(.66,1.01,'brim')],
 'boater_hat':[(0,.52,'crown'),(.52,.66,'band'),(.66,1.01,'brim')],
 'mushroom_hat':[(0,.72,'crown'),(.72,1.01,'lower')],
 'sun_hat':[(0,.50,'crown'),(.50,.61,'band'),(.61,1.01,'brim')],
 'tulip_hat':[(0,.84,'crown'),(.84,1.01,'hem')],
 'hood':[(0,.76,'crown'),(.76,1.01,'hem')],
}
SHADE_FACTORS={-2:.43,-1:.68,0:.92,1:1.10}

@dataclass
class ViewDraft:
 facing:str; width:int; height:int; bbox:tuple[int,int,int,int]
 opaque:int; regions:dict[str,int]; shade_steps:dict[str,int]

@dataclass
class ConstructionDraft:
 control_id:str; canvas_width:int; canvas_height:int; views:list[ViewDraft]
 regions:list[str]; semantic_pattern:str; color_bands:list; motifs:list; overlays:list
 region_palettes:dict; normalized_pattern_coordinates:bool=True
 base_overlay_separation:bool=True; shading_topology_preserved:bool=True
 texture_cleanup:bool=True; coherent_four_view_projection:bool=True


def rgba(path:Path)->np.ndarray:return np.array(Image.open(path).convert('RGBA'),dtype=np.uint8)
def save(arr,path):Image.fromarray(arr.astype(np.uint8),'RGBA').save(path)
def bbox(alpha):
 ys,xs=np.where(alpha>0)
 if len(xs)==0:return (0,0,alpha.shape[1]-1,alpha.shape[0]-1)
 return (int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max()))
def edge_mask(alpha):
 h,w=alpha.shape;out=np.zeros_like(alpha,dtype=bool)
 for y in range(h):
  for x in range(w):
   if not alpha[y,x]:continue
   if any(nx<0 or ny<0 or nx>=w or ny>=h or not alpha[ny,nx] for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))):out[y,x]=True
 return out

def uv_maps(alpha,facing):
 x0,y0,x1,y1=bbox(alpha);h,w=alpha.shape
 u=np.zeros((h,w),float);v=np.zeros((h,w),float)
 for y in range(y0,y1+1):
  for x in range(x0,x1+1):
   uu=(x-x0+.5)/max(1,x1-x0+1);vv=(y-y0+.5)/max(1,y1-y0+1)
   # Photo Tailor-inspired normalized canonical sampling.
   if facing=='right':cu=.45+uu*.55
   elif facing=='left':cu=.55-uu*.55
   elif facing=='back':cu=1-uu
   else:cu=uu
   u[y,x]=cu;v[y,x]=vv
 return u,v

def region_map(control_id,alpha,v):
 rules=FAMILY_RULES[control_id];out=np.full(alpha.shape,'background',dtype=object)
 for lo,hi,name in rules:out[(alpha>0)&(v>=lo)&(v<hi)]=name
 return out

def shade_topology(src,alpha,regions):
 lum=src[:,:,:3].astype(float)@np.array([.299,.587,.114]);edge=edge_mask(alpha);steps=np.zeros(alpha.shape,dtype=np.int8)
 for reg in set(regions[alpha>0]):
  mask=(regions==reg)&(alpha>0)&(~edge);vals=lum[mask]
  if len(vals):
   q1,q2,q3=np.quantile(vals,[.22,.55,.82])
   steps[mask&(lum<=q1)]=-1;steps[mask&(lum>q1)&(lum<=q3)]=0;steps[mask&(lum>q3)]=1
 steps[edge]=-2;return steps

def hexrgb(s):s=s.lstrip('#');return tuple(int(s[i:i+2],16) for i in (0,2,4))
def shade(c,step):f=SHADE_FACTORS[int(step)];return tuple(max(0,min(255,round(x*f))) for x in c)
def palette_color(pal,idx=0):return hexrgb(pal[min(idx,len(pal)-1)])

def band_color(design,reg,v,default):
 for b in design.get('color_bands',[]):
  if b.get('region') not in (None,reg):continue
  if b['top']<=v<=b['bottom']:return hexrgb(b['color'])
 return default

def pattern_hit(kind,u,v,x,y):
 if kind in ('solid','none'):return False
 if kind=='horizontal_stripes':return int(v*14)%4==1
 if kind=='vertical_stripes':return int(u*16)%5==1
 if kind=='plaid':return int(u*18)%6==1 or int(v*16)%5==1
 if kind=='polka_dot':return (int(u*15)+2*int(v*15))%11 in (0,1)
 if kind=='diagonal':return (int(u*18)+int(v*18))%7 in (1,2)
 return False

def cleanup_pattern(mask,alpha,edge,kind):
 m=mask.copy();m[edge]=False;m[~(alpha>0)]=False
 h,w=m.shape;seen=np.zeros_like(m,bool)
 for y in range(h):
  for x in range(w):
   if not m[y,x] or seen[y,x]:continue
   q=deque([(x,y)]);seen[y,x]=True;comp=[]
   while q:
    a,b=q.popleft();comp.append((a,b))
    for nx,ny in ((a-1,b),(a+1,b),(a,b-1),(a,b+1)):
     if 0<=nx<w and 0<=ny<h and m[ny,nx] and not seen[ny,nx]:seen[ny,nx]=True;q.append((nx,ny))
   minimum=2 if kind!='polka_dot' else 1
   if len(comp)<minimum:
    for a,b in comp:m[b,a]=False
 return m

def motif_shape(kind):
 return {
  'flower':[(0,0),(0,-1),(0,1),(-1,0),(1,0)],
  'diamond':[(0,-1),(-1,0),(0,0),(1,0),(0,1)],
  'leaf':[(0,-1),(0,0),(1,0),(1,1)],
  'badge':[(-1,-1),(0,-1),(1,-1),(-1,0),(0,0),(1,0),(0,1)],
  'spark':[(0,-2),(0,-1),(0,0),(0,1),(0,2),(-2,0),(-1,0),(1,0),(2,0)],
 }.get(kind,[(0,0)])

def facing_u(canonical_x,facing):
 if facing=='front':return canonical_x
 if facing=='back':return 1-canonical_x
 if facing=='right':
  return None if canonical_x<.45 else (canonical_x-.45)/.55
 if facing=='left':
  return None if canonical_x>.55 else (.55-canonical_x)/.55

def nearest_opaque(alpha,x,y,r=4):
 h,w=alpha.shape
 if 0<=x<w and 0<=y<h and alpha[y,x]:return x,y
 for d in range(1,r+1):
  cand=[]
  for yy in range(max(0,y-d),min(h,y+d+1)):
   for xx in range(max(0,x-d),min(w,x+d+1)):
    if alpha[yy,xx]:cand.append((abs(xx-x)+abs(yy-y),xx,yy))
  if cand:
   _,xx,yy=min(cand);return xx,yy
 return None

def draw_overlay(overlay,alpha,regions,design,facing):
 x0,y0,x1,y1=bbox(alpha);w=max(1,x1-x0+1);h=max(1,y1-y0+1)
 for item in design.get('motifs',[]):
  if facing not in SCOPES[item['scope']]:continue
  fu=facing_u(item['x'],facing)
  if fu is None:continue
  cx=x0+round(fu*(w-1));cy=y0+round(item['y']*(h-1));hit=nearest_opaque(alpha,cx,cy,5)
  if not hit:continue
  cx,cy=hit;color=hexrgb(item['color']);scale=item.get('scale',1)
  for dx,dy in motif_shape(item['type']):
   for sy in range(scale):
    for sx in range(scale):
     xx=cx+dx*scale+sx;yy=cy+dy*scale+sy
     if 0<=yy<alpha.shape[0] and 0<=xx<alpha.shape[1] and alpha[yy,xx]:overlay[yy,xx]=(*color,255)
 for item in design.get('overlays',[]):
  if facing not in SCOPES[item['scope']]:continue
  color=hexrgb(item['color']);kind=item['type']
  if kind=='horizontal_seam':
   yy=y0+round(item['y']*(h-1))
   for xx in range(x0,x1+1):
    if alpha[yy,xx] and not edge_mask(alpha)[yy,xx]:overlay[yy,xx]=(*color,255)
  elif kind=='vertical_seam':
   xx=x0+round(item.get('x',.5)*(w-1))
   for yy in range(y0,y1+1):
    if alpha[yy,xx] and not edge_mask(alpha)[yy,xx]:overlay[yy,xx]=(*color,255)

def render_view(src,control_id,design,facing):
 alpha=src[:,:,3];u,v=uv_maps(alpha,facing);regions=region_map(control_id,alpha,v);steps=shade_topology(src,alpha,regions);edge=edge_mask(alpha)
 base=np.zeros_like(src);kind=design['semantic_pattern'];pm=np.zeros(alpha.shape,bool)
 for y in range(src.shape[0]):
  for x in range(src.shape[1]):
   if not alpha[y,x]:continue
   reg=regions[y,x];pal=design['region_palettes'].get(reg,design['region_palettes'].get('whole',['#808080','#b0b0b0']))
   base_idx=1 if kind=='colorblock' and len(pal)>1 and ((v[y,x]>.52) if facing in ('front','back') else (u[y,x]>.52)) else 0
   c=band_color(design,reg,v[y,x],palette_color(pal,base_idx))
   if pattern_hit(kind,u[y,x],v[y,x],x,y):pm[y,x]=True
   base[y,x]=(*shade(c,steps[y,x]),255)
 pm=cleanup_pattern(pm,alpha,edge,kind)
 for y,x in zip(*np.where(pm)):
  reg=regions[y,x];pal=design['region_palettes'].get(reg,design['region_palettes'].get('whole',['#808080','#b0b0b0']))
  c=palette_color(pal,1 if len(pal)>1 else 0);base[y,x]=(*shade(c,steps[y,x]),255)
 overlay=np.zeros_like(src);draw_overlay(overlay,alpha,regions,design,facing)
 final=base.copy();sel=overlay[:,:,3]>0;final[sel]=overlay[sel]
 region_dbg=np.zeros_like(src)
 for reg,c in REGION_COLORS.items():region_dbg[(regions==reg)&(alpha>0)]=(*c,255)
 occ=np.zeros_like(src);occ[alpha>0]=(245,245,245,255);occ[edge]=(40,40,40,255)
 return final,base,overlay,occ,region_dbg,regions,steps,int(pm.sum())

def compile_design(control_root:Path,control_id:str,design:dict,outdir:Path):
 outdir.mkdir(parents=True,exist_ok=True);views=[];pattern_cells={}
 for facing in FACINGS:
  src=rgba(control_root/control_id/f'{facing}.png')
  final,base,overlay,occ,region_dbg,regions,steps,npat=render_view(src,control_id,design,facing)
  save(final,outdir/f'{facing}.png');save(base,outdir/f'{facing}_base.png');save(overlay,outdir/f'{facing}_overlay.png');save(occ,outdir/f'{facing}_occupancy.png');save(region_dbg,outdir/f'{facing}_regions.png')
  alpha=src[:,:,3];x0,y0,x1,y1=bbox(alpha);rc=Counter(regions[alpha>0]);sc=Counter(map(int,steps[alpha>0]))
  views.append(ViewDraft(facing,src.shape[1],src.shape[0],(x0,y0,x1,y1),int((alpha>0).sum()),dict(rc),{str(k):v for k,v in sc.items()}));pattern_cells[facing]=npat
 draft=ConstructionDraft(control_id,64,96,views,sorted(set(k for v in views for k in v.regions)),design['semantic_pattern'],design.get('color_bands',[]),design.get('motifs',[]),design.get('overlays',[]),design['region_palettes'])
 payload=asdict(draft);payload['pattern_cells_after_cleanup']=pattern_cells;payload['design_id']=design['id'];payload['description']=design['description']
 (outdir/'draft.json').write_text(json.dumps(payload,indent=2)+'\n')
 return payload
