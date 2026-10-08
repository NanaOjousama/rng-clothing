"""Native production hat enhancement layer.

This module is our own implementation of bounded, source-respecting feature
enhancements. It has no dependency on Photo Tailor, FashionSigLIP, ONNX, or any
prototype/vendor tree. Golden source-respecting pixels remain authoritative.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

VIEWS=("front","right","left","back")

# Conservative family regions. These are semantic *zones*, not replacement
# construction. They only decide where bounded color/pattern deltas may land.
REGIONS={
 "beret":((0.0,.76,"crown"),(.76,1.01,"band")),
 "beanie":((0.0,.72,"crown"),(.72,1.01,"band")),
 "straw_hat":((0.0,.53,"crown"),(.53,.66,"band"),(.66,1.01,"brim")),
 "boater_hat":((0.0,.52,"crown"),(.52,.66,"band"),(.66,1.01,"brim")),
 "mushroom_hat":((0.0,.72,"crown"),(.72,1.01,"lower")),
 "sun_hat":((0.0,.50,"crown"),(.50,.61,"band"),(.61,1.01,"brim")),
 "tulip_hat":((0.0,.84,"crown"),(.84,1.01,"hem")),
 "alt_beanie":((0.0,.72,"crown"),(.72,1.01,"band")),
 "alt_earmuffs":((0.0,.70,"crown"),(.70,1.01,"lower")),
 "alt_headband":((0.0,.82,"crown"),(.82,1.01,"band")),
 "cc_headband":((0.0,.82,"crown"),(.82,1.01,"band")),
 "cc_headscarf":((0.0,.72,"crown"),(.72,1.01,"hem")),
 "cc_hood":((0.0,.76,"crown"),(.76,1.01,"hem")),
 "mas_bows":((0.0,1.01,"whole"),),
 "mas_crown":((0.0,1.01,"whole"),),
 "mas_earmuffs":((0.0,.70,"crown"),(.70,1.01,"lower")),
 "mas_garland":((0.0,1.01,"whole"),),
 "mas_hair_buns":((0.0,1.01,"whole"),),
 "mas_headband":((0.0,.82,"crown"),(.82,1.01,"band")),
 "mas_hood":((0.0,.76,"crown"),(.76,1.01,"hem")),
 "trucker":((0.0,.70,"crown"),(.70,1.01,"brim")),
 "bucket_fisherman":((0.0,.64,"crown"),(.64,.82,"band"),(.82,1.01,"brim")),
}

TINY_SOURCE_FAMILIES={"alt_headband","cc_headband","mas_bows","mas_headband"}
SMALL_SOURCE_FAMILIES={"mas_crown","mas_garland","mas_hair_buns","bucket_fisherman"}

@dataclass(frozen=True)
class EnhancementReport:
 applied: bool
 fallback_reason: str|None
 changed_pixels: int
 changed_ratio: float
 outline_preserved: bool
 alpha_preserved: bool
 pattern: str
 motif: str
 motif_placement: str
 region_mode: str


def _copy(frames):
 return {v:[list(row) for row in frames[v]] for v in VIEWS}

def _bbox(frame):
 pts=[(x,y) for y,row in enumerate(frame) for x,p in enumerate(row) if p[3]]
 if not pts:return (0,0,max(0,len(frame[0])-1),max(0,len(frame)-1))
 xs=[p[0] for p in pts];ys=[p[1] for p in pts]
 return min(xs),min(ys),max(xs),max(ys)

def _edge_mask(frame):
 h=len(frame);w=len(frame[0]);m=[[False]*w for _ in range(h)]
 for y,row in enumerate(frame):
  for x,p in enumerate(row):
   if not p[3]:continue
   for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
    if nx<0 or ny<0 or nx>=w or ny>=h or not frame[ny][nx][3]:
     m[y][x]=True;break
 return m

def _uv(frame,view,x,y):
 x0,y0,x1,y1=_bbox(frame);w=max(1,x1-x0+1);h=max(1,y1-y0+1)
 u=(x-x0+.5)/w;v=(y-y0+.5)/h
 # Canonicalized u roughly maps one physical surface across facings.
 if view=="right":cu=.45+u*.55
 elif view=="left":cu=.55-u*.55
 elif view=="back":cu=1-u
 else:cu=u
 return cu,v

def _region(source_family,v):
 for lo,hi,name in REGIONS.get(source_family,((0,1.01,"whole"),)):
  if lo<=v<hi:return name
 return "whole"

def _luma(p):return .299*p[0]+.587*p[1]+.114*p[2]

def _scale_luma(p,f):
 if not p[3]:return p
 return (max(0,min(255,round(p[0]*f))),max(0,min(255,round(p[1]*f))),max(0,min(255,round(p[2]*f))),p[3])

def _mix(a,b,t):
 return tuple(max(0,min(255,round(a[i]*(1-t)+b[i]*t))) for i in range(3))+(a[3],)

def _accent_from(p,mode="light"):
 # Derive accent from the existing approved source pixel; no external palette.
 if mode=="dark":return _scale_luma(p,.58)
 if mode=="warm":
  r,g,b,a=p;target=(min(255,r+45),min(255,g+20),max(0,b-10),a);return _mix(p,target,.45)
 return _scale_luma(p,1.30)

def _pattern_hit(kind,u,v):
 if kind in ("solid","subtle"):return False
 if kind=="stripe":return int(v*14)%4==1
 if kind=="colorblock":return v>.54
 if kind=="dense":return (int(u*18)+int(v*17))%7 in (1,2)
 return False

def _scope_for(placement):
 if placement=="front_center" or placement=="front_offset":return {"front"}
 if placement=="side":return {"front","right","left"}
 if placement=="back_center":return {"back"}
 return set()

def _motif_anchor(frame,view,placement):
 x0,y0,x1,y1=_bbox(frame);w=max(1,x1-x0+1);h=max(1,y1-y0+1)
 if placement=="front_offset":u=.64
 elif placement=="side":u=.72 if view!="left" else .28
 else:u=.50
 v=.48
 return round(x0+u*(w-1)),round(y0+v*(h-1))

def _nearest_inside(frame,x,y,edge,r=4):
 h=len(frame);w=len(frame[0])
 if 0<=x<w and 0<=y<h and frame[y][x][3] and not edge[y][x]:return (x,y)
 for d in range(1,r+1):
  candidates=[]
  for yy in range(max(0,y-d),min(h,y+d+1)):
   for xx in range(max(0,x-d),min(w,x+d+1)):
    if frame[yy][xx][3] and not edge[yy][xx]:candidates.append((abs(xx-x)+abs(yy-y),xx,yy))
  if candidates:
   _,xx,yy=min(candidates);return (xx,yy)
 return None

def _motif_cells(kind):
 if kind=="emblem":return ((0,-1),(-1,0),(0,0),(1,0),(0,1))
 if kind=="small":return ((0,0),(1,0))
 return ()

def _count_opaque(frames):
 return sum(1 for v in VIEWS for row in frames[v] for p in row if p[3])

def _validate(base,out,source_family):
 changed=0
 for v in VIEWS:
  if len(base[v])!=len(out[v]) or len(base[v][0])!=len(out[v][0]):return False,"SIZE_DRIFT",0
  edge=_edge_mask(base[v])
  for y,row in enumerate(base[v]):
   for x,p in enumerate(row):
    q=out[v][y][x]
    if p[3]!=q[3]:return False,"ALPHA_DRIFT",0
    if edge[y][x] and p!=q:return False,"OUTLINE_DRIFT",0
    if p!=q:changed+=1
 total=max(1,_count_opaque(base));ratio=changed/total
 # Conservative density gates by physical capacity. Enhancement must remain a
 # detail layer, never a new renderer.
 max_ratio=.16 if source_family in TINY_SOURCE_FAMILIES else (.24 if source_family in SMALL_SOURCE_FAMILIES else .34)
 if ratio>max_ratio:return False,f"DELTA_TOO_LARGE:{ratio:.3f}>{max_ratio:.3f}",changed
 return True,None,changed

def enhance_frames(base_frames:dict[str,list],source_family:str,recipe:dict[str,Any],rarity:str)->tuple[dict[str,list],EnhancementReport]:
 base=_copy(base_frames);out=_copy(base_frames)
 pattern=recipe.get("pattern","solid")
 motif=recipe.get("motif","none")
 placement=recipe.get("motifPlacement","none")
 # Common stays essentially source-native. Uncommon gets only very subtle bounded deltas.
 rank={"common":0,"uncommon":1,"rare":2,"epic":3}[rarity]
 pattern_strength=(0.0,.06,.11,.14)[rank]
 colorblock_strength=(0.0,.05,.09,.12)[rank]
 motif_allowed=rank>=2 and motif in ("small","emblem") and placement!="none"
 # Tiny constructions do not get procedural patterns/motifs: their approved source states already carry rarity.
 if source_family in TINY_SOURCE_FAMILIES:
  pattern_strength=0.0;colorblock_strength=0.0;motif_allowed=False
 for view in VIEWS:
  frame=base[view];edge=_edge_mask(frame)
  for y,row in enumerate(frame):
   for x,p in enumerate(row):
    if not p[3] or edge[y][x]:continue
    u,v=_uv(frame,view,x,y);reg=_region(source_family,v)
    # Region-aware trim/band treatment is derived from existing source color.
    q=p
    if recipe.get("trim") in ("contrast","wrap") and reg in ("band","hem","brim") and rank>=1:
     q=_scale_luma(q,1.0+(.05 if rank==1 else .08))
    if pattern=="stripe" and pattern_strength and _pattern_hit("stripe",u,v):q=_scale_luma(q,1-pattern_strength)
    elif pattern=="dense" and pattern_strength and _pattern_hit("dense",u,v):q=_scale_luma(q,1-pattern_strength*.85)
    elif pattern=="colorblock" and colorblock_strength and _pattern_hit("colorblock",u,v):
     # Alternating luma treatment only; preserve source hue/shading structure.
     q=_scale_luma(q,1-colorblock_strength)
    elif pattern=="subtle" and rank>=1 and int(v*16)%7==2:
     q=_scale_luma(q,1-(.025+.01*rank))
    out[view][y][x]=q
  if motif_allowed and view in _scope_for(placement):
   ax,ay=_motif_anchor(frame,view,placement);hit=_nearest_inside(frame,ax,ay,edge,4)
   if hit:
    ax,ay=hit
    for dx,dy in _motif_cells(motif):
     xx,yy=ax+dx,ay+dy
     if 0<=yy<len(frame) and 0<=xx<len(frame[0]) and frame[yy][xx][3] and not edge[yy][xx]:
      mode="warm" if recipe.get("hardware")!="none" else "light"
      out[view][yy][xx]=_accent_from(out[view][yy][xx],mode)
 ok,reason,changed=_validate(base,out,source_family)
 if not ok:
  return base,EnhancementReport(False,reason,0,0.0,True,True,pattern,motif,placement,"SOURCE_DERIVED_BOUNDED")
 total=max(1,_count_opaque(base));ratio=changed/total
 return out,EnhancementReport(changed>0,None,changed,ratio,True,True,pattern,motif,placement,"SOURCE_DERIVED_BOUNDED")
