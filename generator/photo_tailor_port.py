"""Direct Python port of selected Photo Tailor garment-art compiler mechanics.

Source: Photo Tailor 0.15.1 decompile snapshot under
prototypes/photo_tailor_private_lab/vendor/photo_tailor_decompiled/.
The Photo Tailor author explicitly granted this project permission to adapt/reuse
the code. This module intentionally preserves the original algorithms where useful
rather than approximating them.
"""
from __future__ import annotations

from dataclasses import dataclass
import colorsys
import math
from typing import Iterable, Sequence

VIEWS=("front","right","left","back")
BASE_FIELD="base"
DISPLAY_ONLY="display"
FRONT_ONLY="front"
ALL_FACINGS="all"

@dataclass(frozen=True)
class ColorBand:
    top: float
    bottom: float
    color: tuple[int,int,int]

def clamp(v,lo,hi):
    return lo if v<lo else hi if v>hi else v

def canonical_u(view:str,u:float)->float:
    u=clamp(u,0.0,1.0)
    if view=="right": return 0.45+u*0.55
    if view=="left": return 0.55-u*0.55
    if view=="back": return 1.0-u
    return u

def view_u_from_canonical(view:str,canonical_x:float):
    c=clamp(canonical_x,0.0,1.0)
    if view=="front": return c
    if view=="back": return 1.0-c
    if view=="right":
        return None if c<0.45 else (c-0.45)/0.55
    if view=="left":
        return None if c>0.55 else (0.55-c)/0.55
    raise ValueError(view)

def scope_visible(scope:str,view:str)->bool:
    if scope==ALL_FACINGS: return True
    if scope==FRONT_ONLY: return view=="front"
    if scope==DISPLAY_ONLY: return False
    return False

def mix_rgb(left,right,amount:float):
    t=clamp(amount,0.0,1.0)
    return tuple(int(clamp(round(left[i]+(right[i]-left[i])*t),0,255)) for i in range(3))

def build_shade_ramp(color):
    r,g,b=(c/255.0 for c in color)
    h,l,s=colorsys.rgb_to_hls(r,g,b)
    floor=0.38 if l>=0.68 else 0.26 if l>=0.5 else min(0.18,l*0.72)
    levels=[
        max(floor,l*0.62),
        max(floor+0.04,l*0.82),
        l,
        l+(1.0-l)*0.2,
        l+(1.0-l)*0.38,
    ]
    out=[]
    for lv in levels:
        rr,gg,bb=colorsys.hls_to_rgb(h,clamp(lv,0.0,1.0),s)
        out.append(tuple(int(clamp(round(v*255),0,255)) for v in (rr,gg,bb)))
    return out

def shade(color,shade_step:int):
    ramp=build_shade_ramp(color)
    return ramp[int(clamp(2+shade_step,0,len(ramp)-1))]

def resolve_field_color(source_pattern:str,compiled_pattern:str,palette:Sequence[tuple[int,int,int]],
                        bands:Sequence[ColorBand],base_color,u:float,v:float,x:int,y:int):
    color=next((b.color for b in bands if v>=b.top and v<=b.bottom),base_color)
    if not palette: return color
    result=palette[0]
    sp=(source_pattern or "").lower()
    if "horizontal" in sp or (compiled_pattern=="striped" and "vertical" not in sp):
        idx=int(clamp(math.floor(v*10.0),0,9))
        return palette[idx%min(len(palette),5)]
    if "vertical" in sp:
        idx=int(clamp(math.floor(u*9.0),0,8))
        return palette[idx%min(len(palette),5)]
    if "plaid" in sp or "check" in sp:
        if abs(x)%10<=1 and len(palette)>1: return palette[1]
        if abs(y)%10<=1 and len(palette)>2: return palette[2]
    if "colorblock" in sp or "colourblock" in sp:
        idx=0 if v<0.36 else 1 if v<0.68 else 2
        return palette[min(idx,len(palette)-1)]
    if "gradient" in sp and len(palette)>1:
        return mix_rgb(palette[0],palette[1],v)
    return result

def bbox(frame):
    pts=[(x,y) for y,row in enumerate(frame) for x,p in enumerate(row) if p[3]]
    if not pts: return (0,0,max(0,len(frame[0])-1),max(0,len(frame)-1))
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return min(xs),min(ys),max(xs),max(ys)

def edge_mask(frame):
    h=len(frame); w=len(frame[0]); out=[[False]*w for _ in range(h)]
    for y,row in enumerate(frame):
        for x,p in enumerate(row):
            if not p[3]: continue
            for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if nx<0 or ny<0 or nx>=w or ny>=h or not frame[ny][nx][3]:
                    out[y][x]=True
                    break
    return out

def normalized_uv(frame,view,x:int,y:int):
    x0,y0,x1,y1=bbox(frame)
    w=max(1,x1-x0+1); h=max(1,y1-y0+1)
    u=(x-x0+0.5)/w
    v=(y-y0+0.5)/h
    return canonical_u(view,u),clamp(v,0.0,1.0)

def nearest_opaque(frame,x:int,y:int,max_radius:int=12,avoid_edge:bool=False):
    h=len(frame); w=len(frame[0]); edges=edge_mask(frame) if avoid_edge else None
    def valid(xx,yy):
        return 0<=xx<w and 0<=yy<h and frame[yy][xx][3] and (not avoid_edge or not edges[yy][xx])
    if valid(x,y): return (x,y)
    for radius in range(1,max_radius+1):
        for dx in range(-radius,radius+1):
            for yy in (y-radius,y+radius):
                xx=x+dx
                if valid(xx,yy): return (xx,yy)
        for dy in range(-radius+1,radius):
            for xx in (x-radius,x+radius):
                yy=y+dy
                if valid(xx,yy): return (xx,yy)
    return None

def canonical_anchor(frame,view,canonical_x:float,canonical_y:float,avoid_edge=True):
    u=view_u_from_canonical(view,canonical_x)
    if u is None: return None
    x0,y0,x1,y1=bbox(frame)
    x=x0+round(clamp(u,0.0,1.0)*max(0,x1-x0))
    y=y0+round(clamp(canonical_y,0.0,1.0)*max(0,y1-y0))
    return nearest_opaque(frame,x,y,12,avoid_edge=avoid_edge)

def pattern_color(pattern,palette,bands,base_color,frame,view,x,y):
    u,v=normalized_uv(frame,view,x,y)
    return resolve_field_color(pattern,pattern,palette,bands,base_color,u,v,x,y)

def resolve_shade_step(frame,x:int,y:int):
    edges=edge_mask(frame)
    if edges[y][x]: return -2
    x0,_,x1,_=bbox(frame)
    u=((x-x0)+0.5)/max(1.0,x1-x0+1)
    if u<0.18 or u>0.82: return -1
    if 0.42<u<0.60: return 1
    return 0

def source_palette(frame,limit=5):
    counts={}
    for row in frame:
        for p in row:
            if p[3]:
                rgb=tuple(p[:3]); counts[rgb]=counts.get(rgb,0)+1
    colors=sorted(counts,key=lambda c:(.299*c[0]+.587*c[1]+.114*c[2],-counts[c]))
    if not colors: return [(96,104,116)]
    if len(colors)<=limit: return colors
    picks=[]
    for i in range(limit):
        picks.append(colors[round(i*(len(colors)-1)/(limit-1))])
    return picks

def copy_frames(frames):
    return {v:[list(row) for row in frames[v]] for v in VIEWS}

def render_source_locked(frames,pattern="solid",palette=None,bands=(),motifs=()):
    """Apply Photo Tailor PreviewHat/Recolor projection to a locked 4-view silhouette."""
    out=recolor_four_facing(frames,pattern=pattern,palette=palette,bands=bands)
    for view in VIEWS:
        frame=frames[view]
        for motif in motifs:
            scope=motif.get("scope",FRONT_ONLY)
            if not scope_visible(scope,view): continue
            hit=canonical_anchor(frame,view,motif.get("x",0.5),motif.get("y",0.45),avoid_edge=True)
            if hit is None: continue
            x,y=hit
            color=tuple(motif.get("color",(230,210,140)))
            out[view][y][x]=(color[0],color[1],color[2],out[view][y][x][3])
    return out

def relative_luma(rgb):
    return (0.2126*rgb[0]+0.7152*rgb[1]+0.0722*rgb[2])/255.0

def shade_factor(rgb,factor:float):
    return tuple(int(clamp(round(c*factor),0,255)) for c in rgb)

def topology_boundary(frame,x:int,y:int):
    h=len(frame);w=len(frame[0])
    if x==0 or y==0 or x==w-1 or y==h-1:return True
    for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
        if nx<0 or nx>=w or ny<0 or ny>=h or frame[ny][nx][3]<16:return True
    return False

def renderer_shade_factor(target,source_luma:float,boundary:bool):
    if boundary:
        return 0.96 if relative_luma(target)<0.25 else clamp(0.78+0.18*source_luma,0.8,0.96)
    return round((0.88+0.24*source_luma)*8.0)/8.0

def recolor_four_facing(frames,pattern="solid",palette=None,bands=()):
    """Direct port of SpriteRenderer.PreviewHat -> Recolor for four-facing hats."""
    out=copy_frames(frames)
    for view in VIEWS:
        frame=frames[view]
        pal=list(palette or source_palette(frame))
        base=pal[min(2,len(pal)-1)]
        for y,row in enumerate(frame):
            for x,p in enumerate(row):
                if p[3]<16:
                    out[view][y][x]=(0,0,0,0); continue
                source_luma=relative_luma(p[:3])
                u=(x+0.5)/max(1.0,len(row)); v=(y+0.5)/max(1.0,len(frame))
                target=resolve_field_color(pattern,pattern,pal,bands,base,canonical_u(view,u),v,x,y)
                factor=renderer_shade_factor(target,source_luma,topology_boundary(frame,x,y))
                rgb=shade_factor(target,factor)
                out[view][y][x]=(rgb[0],rgb[1],rgb[2],p[3])
    return out
