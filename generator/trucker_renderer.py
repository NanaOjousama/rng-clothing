"""Finished trucker renderer for the A/B base comparison.

Uses locked construction alpha cells, but converts non-zero source alpha to opaque
production pixels so the mesh reads as fabric instead of a fading template.
"""
from __future__ import annotations

def _lum(p):
    return p[0]*0.299+p[1]*0.587+p[2]*0.114

def _sat(p):
    mx=max(p[:3]); mn=min(p[:3])
    return 0.0 if mx==0 else (mx-mn)/mx

def _edge(frame,x,y):
    h=len(frame); w=len(frame[0])
    for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
        if nx<0 or ny<0 or nx>=w or ny>=h or not frame[ny][nx][3]:
            return True
    return False

def _opaque_bbox(frame):
    pts=[(x,y) for y,row in enumerate(frame) for x,p in enumerate(row) if p[3]]
    if not pts:return (0,0,len(frame[0])-1,len(frame)-1)
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return min(xs),min(ys),max(xs),max(ys)

def _mesh_cell(p):
    # Source mesh is pale/low-saturation; source outline/shadows are not.
    return p[3] and _lum(p) >= 135 and _sat(p) <= 0.50

def _rank_color(p,ramp):
    if not ramp:return p[:3]
    vals=list(range(len(ramp)))
    src=max(0,min(255,_lum(p)))
    # Use source luma as the local shading topology.
    idx=round((src/255)*(len(ramp)-1))
    return tuple(ramp[idx])

def _darken(rgb,amount=0.72):
    return tuple(max(0,min(255,round(c*amount))) for c in rgb)

def _lighten(rgb,amount=1.18):
    return tuple(max(0,min(255,round(c*amount))) for c in rgb)

def _solid_region_pattern(rgb,x,y,recipe):
    patt=recipe.get('pattern','solid')
    if patt=='subtle' and (x+y)%5==0:return _lighten(rgb,1.08)
    if patt=='stripe' and x%4==0:return _darken(rgb,0.82)
    if patt=='dense' and (x+2*y)%4==0:return _darken(rgb,0.84)
    return rgb

def render_frame(frame,view,body_ramp,mesh_ramp,accent_ramp,recipe,anchor):
    x0,y0,x1,y1=_opaque_bbox(frame)
    out=[row[:] for row in frame]
    for y,row in enumerate(frame):
        for x,p in enumerate(row):
            if not p[3]:
                out[y][x]=(0,0,0,0); continue
            is_mesh=_mesh_cell(p)
            rgb=_rank_color(p,mesh_ramp if is_mesh else body_ramp)
            if is_mesh:
                # Visible woven mesh: alternating value, but never semi-transparent.
                rgb=_lighten(rgb,1.10) if (x+y)%2==0 else _darken(rgb,0.82)
            else:
                rgb=_solid_region_pattern(rgb,x,y,recipe)
            # Preserve a strong Stardew-style border.
            if _edge(frame,x,y):
                rgb=_darken(rgb,0.56)
            out[y][x]=(*rgb,255)

    # Colorblock/contrast treatments apply to the lower brim/band area.
    trim=recipe.get('trim','none')
    patt=recipe.get('pattern','solid')
    brim_y=y0+round((y1-y0)*0.70)
    for y in range(brim_y,y1+1):
        for x in range(x0,x1+1):
            if not out[y][x][3]: continue
            if patt=='colorblock' or trim in ('contrast','wrap'):
                base=accent_ramp[-2 if len(accent_ramp)>1 else -1]
                rgb=_darken(base,0.60) if _edge(frame,x,y) else base
                out[y][x]=(*rgb,255)
            elif trim=='subtle' and y==brim_y:
                rgb=accent_ramp[0]
                out[y][x]=(*rgb,255)

    motif=recipe.get('motif','none')
    if view=='front' and motif!='none':
        ax,ay=anchor
        pts=[(0,0),(-1,0),(1,0),(0,1)]
        if motif=='emblem':
            pts += [(-1,1),(1,1),(0,-1)]
        color=accent_ramp[-1]
        for dx,dy in pts:
            x,y=ax+dx,ay+dy
            if 0<=y<len(out) and 0<=x<len(out[0]) and out[y][x][3] and not _mesh_cell(frame[y][x]):
                out[y][x]=(*color,255)
    return out

def render_trucker(frames,recipe,body_ramp,mesh_ramp,accent_ramp,anchors):
    return {
        view:render_frame(frames[view],view,body_ramp,mesh_ramp,accent_ramp,recipe,anchors[view])
        for view in ('front','right','left','back')
    }
