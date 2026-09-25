"""Cap renderer using the directly ported Photo Tailor compiler mechanics."""
from __future__ import annotations

from dataclasses import dataclass
from collections import deque
from typing import Any

from generator.photo_tailor_port import (
    ALL_FACINGS, FRONT_ONLY, ColorBand, bbox, copy_frames, edge_mask,
    normalized_uv, render_source_locked, resolve_field_color, resolve_shade_step,
    shade,
)

VIEWS=("front","right","left","back")

@dataclass(frozen=True)
class CapRenderReport:
    family: str
    valid: bool
    errors: tuple[str,...]
    alpha_preserved: bool
    photo_tailor_port_used: bool

def _opaque(frame):
    return {(x,y) for y,row in enumerate(frame) for x,p in enumerate(row) if p[3]}

def _component_share(frame):
    pts=_opaque(frame)
    if not pts:return 0.0
    unseen=set(pts);best=0
    while unseen:
        start=next(iter(unseen));q=deque([start]);unseen.remove(start);n=0
        while q:
            x,y=q.popleft();n+=1
            for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if p in unseen:
                    unseen.remove(p);q.append(p)
        best=max(best,n)
    return best/len(pts)

def validate_frames(frames):
    errors=[]
    if set(frames)!=set(VIEWS):
        errors.append("FOUR_VIEWS_REQUIRED")
    for v in VIEWS:
        if v not in frames:continue
        f=frames[v]
        if len(f)!=20 or len(f[0])!=20:errors.append(f"{v}:NATIVE_20_REQUIRED")
        if bbox(f)==(0,0,19,19):errors.append(f"{v}:FULL_FRAME_CONTAMINATION")
        if len(_opaque(f))<20:errors.append(f"{v}:TOO_LITTLE_CONTENT")
        if _component_share(f)<0.72:errors.append(f"{v}:DISCONNECTED_CONTAMINATION")
    return errors

def _alpha_signature(frames):
    return {v:tuple(tuple(1 if p[3] else 0 for p in row) for row in frames[v]) for v in VIEWS}

def _motifs_for(family,accent):
    if family in ("baseball","snapback"):
        return ({"scope":FRONT_ONLY,"x":0.50,"y":0.42,"color":accent},)
    if family=="officer":
        return ({"scope":FRONT_ONLY,"x":0.50,"y":0.34,"color":accent},)
    return ()

def render_cap_family(frames,family,palette,pattern="solid",accent=(224,190,104)):
    errors=validate_frames(frames)
    if errors:
        return copy_frames(frames),CapRenderReport(family,False,tuple(errors),True,False)
    before=_alpha_signature(frames)
    bands=()
    motifs=_motifs_for(family,accent)
    out=render_source_locked(frames,pattern=pattern,palette=palette,bands=bands,motifs=motifs)
    after=_alpha_signature(out)
    alpha_ok=before==after
    if not alpha_ok:
        errors.append("ALPHA_DRIFT")
        return copy_frames(frames),CapRenderReport(family,False,tuple(errors),False,True)
    return out,CapRenderReport(family,True,(),True,True)
