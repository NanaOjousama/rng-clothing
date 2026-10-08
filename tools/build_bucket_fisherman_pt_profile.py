#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from collections import Counter
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from generator.photo_tailor_port import bbox,build_shade_ramp,relative_luma,topology_boundary
from v5.source.template_transfer import load_contract,template_frames

TEMPLATE=ROOT/'generator/data/templates/bucket_fisherman_navy16.json'
OUT=ROOT/'authored/templates/bucket_fisherman_navy16/pt_profile.json'
VIEWS=('front','right','back','left')
DONORS={
 'cream':ROOT/'authored/approved/bucket_hat_v1/sources/design_flower_band_cream_front.png',
 'olive_canvas':ROOT/'authored/approved/bucket_hat_v1/sources/design_classic_olive_band_front.png',
 'rust':ROOT/'authored/approved/bucket_hat_v1/sources/pattern_patchwork_earth_front.png',
 'pastel_pink':ROOT/'authored/approved/bucket_hat_v1/sources/motif_daisy_pink_front.png',
 'rain_yellow':ROOT/'authored/approved/bucket_hat_v1/sources/material_rain_yellow_front.png',
}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def donor_colors(path):
 from v5.pngio import read_rgba_png
 fr=read_rgba_png(path)
 vals=[(relative_luma(p[:3]),p[:3]) for row in fr for p in row if p[3]]
 lum=sorted(v for v,c in vals)
 lo=lum[max(0,round((len(lum)-1)*.30))]
 hi=lum[max(0,round((len(lum)-1)*.92))]
 counts=Counter(c for v,c in vals if lo<=v<=hi)
 if not counts:counts=Counter(c for v,c in vals)
 base=tuple(counts.most_common(1)[0][0])
 boundary=[p[:3] for y,row in enumerate(fr) for x,p in enumerate(row)
           if p[3] and topology_boundary(fr,x,y)]
 if boundary:
  b_lum=sorted(relative_luma(c) for c in boundary)
  cutoff=b_lum[max(0,round((len(b_lum)-1)*.35))]
  dark=Counter(tuple(c) for c in boundary if relative_luma(c)<=cutoff)
  outline=tuple(dark.most_common(1)[0][0]) if dark else min(boundary,key=relative_luma)
 else:
  outline=build_shade_ramp(base)[0]
 return base,outline

def quantiles(vals):
 vals=sorted(vals)
 def q(t):
  return vals[round((len(vals)-1)*t)] if vals else 0
 return [q(.25),q(.50),q(.75)]

def role_for(luma,qs):
 if luma<=qs[0]:return 'shadow'
 if luma<=qs[1]:return 'mid'
 if luma<=qs[2]:return 'light'
 return 'highlight'

def main():
 frames=template_frames(load_contract(TEMPLATE))
 views={}
 for view in VIEWS:
  fr=frames[view];x0,y0,x1,y1=bbox(fr)
  boundary=[];interior=[]
  for y,row in enumerate(fr):
   for x,p in enumerate(row):
    if not p[3]:continue
    if topology_boundary(fr,x,y):boundary.append([x,y])
    else:interior.append((x,y,relative_luma(p[:3])))
  qs=quantiles([v for x,y,v in interior])
  roles={'outline':boundary,'shadow':[],'mid':[],'light':[],'highlight':[]}
  regions={'crown':[],'band':[],'brim':[]}
  h=max(1,y1-y0+1)
  for x,y,v in interior:
   roles[role_for(v,qs)].append([x,y])
  for y,row in enumerate(fr):
   for x,p in enumerate(row):
    if not p[3]:continue
    nv=(y-y0+.5)/h
    reg='crown' if nv<.64 else ('band' if nv<.82 else 'brim')
    regions[reg].append([x,y])
  views[view]={
   'bbox':[x0,y0,x1,y1],
   'opaqueCells':sum(1 for row in fr for p in row if p[3]),
   'boundaryCells':len(boundary),
   'sourceLumaQuantiles':[round(x,6) for x in qs],
   'shadeRoles':roles,
   'semanticRegions':regions,
  }
 palettes={
  'navy_source_native':{'mode':'SOURCE_NATIVE','source':'authored/templates/bucket_fisherman_navy16/*.png'},
 }
 for name,path in DONORS.items():
  base,outline=donor_colors(path)
  palettes[name]={
   'mode':'PHOTO_TAILOR_SHADE_RAMP_WITH_APPROVED_DONOR_OUTLINE',
   'donor':str(path.relative_to(ROOT)),
   'donorSha256':sha(path),
   'baseColor':list(base),
   'outlineColor':list(outline),
   'ptShadeRamp':[list(c) for c in build_shade_ramp(base)],
  }
 profile={
  'schema':'bucket-fisherman-photo-tailor-profile/v1',
  'template':'bucket_fisherman_navy16',
  'status':'PT_ANALYSIS_READY_FROZEN_RENDERER_CANDIDATE',
  'photoTailorAuthority':{
   'module':'generator/photo_tailor_port.py',
   'provenance':'permission-backed direct port of Photo Tailor mechanics',
   'mechanicsUsed':['relative_luma','topology_boundary','build_shade_ramp'],
   'role':'analyze source shading/topology and build candidate golden palette ramps; never owns construction geometry'
  },
  'constructionAuthority':'authored/templates/bucket_fisherman_navy16/{front,right,back,left}.png',
  'geometryPolicy':'EXACT_TEMPLATE_ALPHA_NO_RESAMPLE',
  'regionPolicy':{'crownEnd':.64,'bandEnd':.82,'brimStart':.82,'note':'semantic zones are construction metadata; PT supplies topology/luma shading evidence'},
  'views':views,
  'candidatePalettes':palettes,
 }
 OUT.write_text(json.dumps(profile,indent=2)+'\n')
 print('PASS wrote',OUT.relative_to(ROOT))
 print('palettes',', '.join(palettes))
if __name__=='__main__':main()
