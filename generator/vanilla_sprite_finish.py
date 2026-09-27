"""Measured Stardew-vanilla RGB finishing helpers for locked pixel templates.

This module never changes alpha. It chromatically integrates outer outlines and
internal dark seams with the neighboring semantic component instead of applying
one global black border.
"""
from __future__ import annotations

def luminance(rgb):
    r,g,b=rgb
    return r*.299 + g*.587 + b*.114

def opaque_cells(frame):
    return {(x,y) for y,row in enumerate(frame) for x,p in enumerate(row) if p[3]}

def outer_boundary(frame):
    op=opaque_cells(frame); out=set(); h=len(frame); w=len(frame[0])
    for x,y in op:
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if nx<0 or nx>=w or ny<0 or ny>=h or (nx,ny) not in op:
                out.add((x,y)); break
    return out

def owner_map(component_masks):
    own={}
    for comp,cells in component_masks.items():
        for p in cells: own[tuple(p)]=comp
    return own

def nearest_component(x,y,owners,max_radius=3):
    if (x,y) in owners: return owners[(x,y)]
    for r in range(1,max_radius+1):
        candidates=[]
        for dy in range(-r,r+1):
            for dx in range(-r,r+1):
                if abs(dx)+abs(dy)!=r: continue
                comp=owners.get((x+dx,y+dy))
                if comp: candidates.append(comp)
        if candidates:
            # deterministic majority, then lexical tie-break
            return sorted(set(candidates), key=lambda c:(-candidates.count(c),c))[0]
    return None

def apply_chromatic_outline(frame, component_masks, ramps, *, preserve=None):
    """Recolor only outer boundary RGB using local semantic ramps.

    `ramps` maps component -> ordered darkest..lightest RGB tuples.
    Deep structural pixels can be kept untouched through `preserve`.
    """
    preserve=set(preserve or ())
    out=[row[:] for row in frame]; boundary=outer_boundary(frame)
    owners=owner_map(component_masks)
    for x,y in boundary:
        if (x,y) in preserve: continue
        comp=nearest_component(x,y,owners)
        ramp=ramps.get(comp) if comp else None
        if not ramp: continue
        rgb=tuple(ramp[0])
        out[y][x]=(*rgb,frame[y][x][3])
    return out
