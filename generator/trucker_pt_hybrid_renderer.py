"""Trucker-specific Photo Tailor integrated renderer.

Vanilla Stardew Trucker Hat #16 owns all geometry. Photo Tailor's renderer
shading math is used per semantic region; trucker-specific masks prevent
front-mesh and generic horizontal-band artifacts.
"""
from __future__ import annotations
from generator.photo_tailor_port import relative_luma, renderer_shade_factor, shade_factor, topology_boundary

VIEWS=('front','right','left','back')
PINK={(68,53,53),(179,161,155),(247,232,232)}
GREEN={(21,61,8),(53,91,41),(91,145,66)}
OUTLINE={(10,17,9)}
PARTIAL={(43,16,0),(33,9,19)}

def _scale(rgb,f):
    return tuple(max(0,min(255,round(c*f))) for c in rgb)

def _mix(a,b,t):
    return tuple(max(0,min(255,round(a[i]*(1-t)+b[i]*t))) for i in range(3))

def _region(frame,view,x,y):
    p=frame[y][x]; rgb=tuple(p[:3])
    if not p[3]: return 'empty'
    if rgb in OUTLINE: return 'outline'
    # Physical visor/closure zones from vanilla #16 construction, not normalized y bands.
    if view=='front' and y>=10: return 'brim'
    if view in ('right','left') and y>=10: return 'brim'
    if view=='back' and y>=12: return 'closure'
    if view=='front': return 'front_panel'  # never mesh on front-facing crown
    if view in ('right','left'):
        if rgb in PINK: return 'front_panel'
        if rgb in GREEN: return 'rear_mesh'
        return 'front_panel'
    if view=='back':
        if rgb in GREEN: return 'rear_mesh'
        return 'crown_detail'
    return 'front_panel'

def _pt_shaded(target, source_pixel, frame,x,y):
    sl=relative_luma(source_pixel[:3])
    factor=renderer_shade_factor(target,sl,topology_boundary(frame,x,y))
    return shade_factor(target,factor)

def _mesh_treatment(rgb,x,y,strength):
    if strength<=0:return rgb
    # Opaque weave/value texture only; geometry and alpha never change.
    return _scale(rgb,1.0+strength) if (x+y)%2==0 else _scale(rgb,1.0-strength*.72)

def _front_pattern(rgb,kind,x,y,strength):
    if strength<=0:return rgb
    if kind=='stripe' and x%3==0:return _scale(rgb,1.0-strength)
    if kind=='pinstripe' and x%4==1:return _scale(rgb,1.0-strength*.65)
    if kind=='check' and ((x//2+y//2)%2==0):return _scale(rgb,1.0-strength*.55)
    return rgb

def render(frames, *, body, rear, brim, accent, pattern='solid', mesh_strength=.08,
           pattern_strength=.10, motif='none', motif_offset=0):
    out={v:[list(r) for r in frames[v]] for v in VIEWS}
    for view in VIEWS:
        frame=frames[view]
        for y,row in enumerate(frame):
            for x,p in enumerate(row):
                if not p[3]: continue
                reg=_region(frame,view,x,y)
                if reg=='outline':
                    out[view][y][x]=p; continue
                if reg=='front_panel': target=body
                elif reg=='rear_mesh': target=rear
                elif reg in ('brim','closure'): target=brim
                else: target=_mix(body,rear,.35)
                rgb=_pt_shaded(target,p,frame,x,y)
                if reg=='rear_mesh': rgb=_mesh_treatment(rgb,x,y,mesh_strength)
                if reg=='front_panel': rgb=_front_pattern(rgb,pattern,x,y,pattern_strength)
                out[view][y][x]=(*rgb,p[3])

    # Explicit front-panel motif. Never touches brim/mesh/outline.
    if motif!='none':
        frame=frames['front']; candidates=[]
        for y in range(len(frame)):
            for x in range(len(frame[0])):
                if _region(frame,'front',x,y)=='front_panel' and not topology_boundary(frame,x,y):
                    candidates.append((x,y))
        if candidates:
            cx=round(sum(x for x,y in candidates)/len(candidates))+motif_offset
            cy=round(sum(y for x,y in candidates)/len(candidates))
            cells=[(0,0),(1,0)] if motif=='small' else [(0,-1),(-1,0),(0,0),(1,0),(0,1)]
            for dx,dy in cells:
                x,y=cx+dx,cy+dy
                if 0<=y<len(frame) and 0<=x<len(frame[0]) and _region(frame,'front',x,y)=='front_panel' and not topology_boundary(frame,x,y):
                    src=out['front'][y][x]
                    out['front'][y][x]=(*_pt_shaded(accent,src,frame,x,y),src[3])
    return out
