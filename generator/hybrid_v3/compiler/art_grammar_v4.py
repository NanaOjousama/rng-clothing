"""Experimental V4 art-grammar normalization for Hybrid garments.

This module deliberately separates BODY FORM from COMPONENT IDENTITY.
It runs after the legacy V5E optical polish and before V3 component painting,
so legacy polish cannot erase component-owned collar/armhole/placket roles.
"""
from __future__ import annotations

from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER
from generator.renderers.fashionsense.upper_v5b import _default_value, _mask_value


def _copy(frames):
    return {d:[list(r) for r in frames[d]] for d in DIRECTION_ORDER}


def _bounds(frame, y):
    xs=[x for x,p in enumerate(frame[y]) if p[3]]
    return None if not xs else (min(xs),max(xs))


def normalize_body_form(base, source_frames, source_defaults, *, family: str, break_dark_rails: bool = True):
    """Rebuild readable form planes without changing alpha geometry.

    Rules are intentionally conservative at 16x16:
    - exterior boundary owns darkest contour;
    - dominant interior remains BASE;
    - upper-left gets a compact connected LIGHT plane;
    - right/lower interior gets sparse SHADOW, never a central dark stripe;
    - collar/component identity is authored later and therefore cannot be
      overwritten by this pass.
    """
    frames=_copy(source_frames); defaults=_copy(source_defaults)
    changed={d:set() for d in DIRECTION_ORDER}

    def put(d,x,y,role):
        if not (0<=x<16 and 0<=y<16 and frames[d][y][x][3]):
            return
        v=_mask_value(base,role); dv=_default_value(base,role)
        if frames[d][y][x]!=v or defaults[d][y][x]!=dv:
            frames[d][y][x]=v; defaults[d][y][x]=dv; changed[d].add((x,y))

    for d in DIRECTION_ORDER:
        frame=frames[d]
        for y in range(16):
            b=_bounds(frame,y)
            if not b: continue
            lo,hi=b
            width=hi-lo+1
            for x in range(lo,hi+1):
                if not frame[y][x][3]: continue
                # Preserve a clear exterior silhouette, but avoid turning every
                # upper neckline pixel into a black sticker border.
                exterior = x==lo or x==hi or y==15 or not all(
                    0<=nx<16 and 0<=ny<16 and frame[ny][nx][3]
                    for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))
                )
                if exterior:
                    if y <= 2 and 5 <= x <= 10:
                        role='SHADOW'
                    else:
                        role='EXTERIOR_CONTOUR'
                    put(d,x,y,role)
                    continue

                # Calm dominant fabric mass first.
                role='BASE'
                # Small connected upper-left light plane. Side views get a
                # narrow vertical highlight rather than front-like noise.
                if d in {'front','back'}:
                    if 3<=y<=7 and x<=lo+2: role='LIGHT'
                    elif y in {8,9} and x==lo+2: role='LIGHT'
                elif d=='right':
                    if 2<=y<=7 and x<=lo+2: role='LIGHT'
                else:  # mirrored illumination still reads from world upper-left
                    if 2<=y<=7 and x<=lo+2: role='LIGHT'

                # Sparse form shadow hugs the shadow-facing side. Never paint
                # the middle of a side torso dark merely because carrier did.
                # Broken shadow beats describe turn of form without creating
                # the old full-height dark side rail.
                if x>=hi-1 and (y in {4,5,8,11,12} if break_dark_rails else y>=4): role='SHADOW'
                if y>=12 and x>=lo+2: role='SHADOW'
                put(d,x,y,role)

    return frames, defaults, {d:len(c) for d,c in changed.items()}


def normalize_vanilla_plus_body_form(base, source_frames, source_defaults, *, protected_cells=None):
    """Compress body rendering to vanilla-like local-color shorthand.

    The pass never changes alpha and skips every component-owned structural
    cell. It leaves one calm base mass, a small connected light plane, sparse
    turn-of-form shadow, and darkest pixels only at silhouette turns and the
    underside. This is an art abstraction layer, not garment architecture.
    """
    frames=_copy(source_frames); defaults=_copy(source_defaults)
    protected_cells=protected_cells or {d:set() for d in DIRECTION_ORDER}
    changed={d:set() for d in DIRECTION_ORDER}

    def put(d,x,y,role):
        if (x,y) in protected_cells.get(d,set()) or not frames[d][y][x][3]:
            return
        value=_mask_value(base,role); default=_default_value(base,role)
        if frames[d][y][x] != value or defaults[d][y][x] != default:
            frames[d][y][x]=value; defaults[d][y][x]=default; changed[d].add((x,y))

    before={d:{(x,y) for y,row in enumerate(frames[d]) for x,p in enumerate(row) if p[3]} for d in DIRECTION_ORDER}
    for d in DIRECTION_ORDER:
        for y in range(16):
            bounds=_bounds(frames[d],y)
            if not bounds: continue
            lo,hi=bounds
            for x in range(lo,hi+1):
                if not frames[d][y][x][3] or (x,y) in protected_cells.get(d,set()): continue
                exterior=any(
                    nx<0 or nx>=16 or ny<0 or ny>=16 or not frames[d][ny][nx][3]
                    for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))
                )
                if exterior:
                    # Darkest local color belongs to corners, underarms, and
                    # the hem. Long side runs use the softer fabric shadow.
                    structural_turn = y in {0,1,7,14,15} or x not in {lo,hi}
                    put(d,x,y,"EXTERIOR_CONTOUR" if structural_turn else "SHADOW")
                    continue
                role="BASE"
                if d in {"front","back"} and 3<=y<=7 and x in {lo+1,lo+2}:
                    role="LIGHT"
                elif d in {"right","left"} and 2<=y<=6 and x==lo+1:
                    role="LIGHT"
                elif x==hi-1 and y in {5,9,12}:
                    role="SHADOW"
                put(d,x,y,role)
    after={d:{(x,y) for y,row in enumerate(frames[d]) for x,p in enumerate(row) if p[3]} for d in DIRECTION_ORDER}
    if before != after:
        raise ValueError("vanilla-plus body abstraction changed alpha geometry")
    return frames, defaults, {d:len(c) for d,c in changed.items()}
