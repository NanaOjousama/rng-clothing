#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from generator.photo_tailor_port import relative_luma,topology_boundary
from v5.pngio import read_rgba_png
from v5.source.template_transfer import alpha_cells

VIEWS=('front','right','back','left')
SRC={v:read_rgba_png(ROOT/f'authored/templates/bucket_fisherman_navy16/{v}.png') for v in VIEWS}
REG=json.load(open(ROOT/'generator/data/source_respecting_hat_goldens_fisherman_candidate.json'))
SMOKE=json.load(open(ROOT/'experiments/fisherman_frozen_source_smoke_01/manifest.json'))
PROD=json.load(open(ROOT/'generator/data/headwear/bucket_hat_production_registry.json'))

assert REG['status']=='HUMAN_VISUAL_APPROVAL_REQUIRED'
assert REG['sourceFamily']=='bucket_fisherman'
assert REG['sourceStateHumanApproved'] is True
assert len(REG['candidatePairs'])==4
assert {p['palette'] for p in REG['candidatePairs']}=={'source_native','cream','olive_canvas','rain_yellow'}

def assert_monotone(src,out,view):
 for boundary in (False,True):
  pairs=[]
  for y,row in enumerate(src):
   for x,p in enumerate(row):
    if not p[3] or topology_boundary(src,x,y)!=boundary:continue
    pairs.append((relative_luma(p[:3]),relative_luma(out[y][x][:3])))
  pairs.sort()
  # If source luminance increases, output luminance may stay equal due to RGB rounding,
  # but must never reverse materially.
  last=-1.0
  for sl,ol in pairs:
   if ol+1/255 < last:
    raise AssertionError((view,'boundary' if boundary else 'interior','luma topology reversed',sl,ol,last))
   last=max(last,ol)

for pair in REG['candidatePairs']:
 pal=pair['palette']
 frames={v:read_rgba_png(ROOT/pair['frames'][v]) for v in VIEWS}
 for v in VIEWS:
  assert alpha_cells(frames[v])==alpha_cells(SRC[v]),(pal,v,'alpha')
 assert frames['left']==[list(reversed(r)) for r in frames['right']],(pal,'mirror')
 if pal=='source_native':
  for v in VIEWS:assert frames[v]==SRC[v],(v,'source native drift')
 else:
  for v in VIEWS:assert_monotone(SRC[v],frames[v],v)
  # Explicitly reject the old 5-bucket PT failure mode on the front.
  assert len({p[:3] for row in frames['front'] for p in row if p[3]})>20,(pal,'front shade collapse')

assert SMOKE['renderer']=='HAT_RENDERER_V1'
assert SMOKE['productionCore']=='generator/hat_hybrid_enhancements.py::enhance_frames'
for row in SMOKE['rows']:
 for v in VIEWS:
  assert read_rgba_png(ROOT/row['common']['frames'][v])==read_rgba_png(ROOT/row['goldenFrames'][v]),(row['palette'],v,'common drift')
 assert row['rare']['alphaPreserved'] is True and row['rare']['outlinePreserved'] is True
 assert row['rare']['changedPixels']<=5,(row['palette'],'rare delta too large')

prod=PROD['constructions']['bucket_fisherman_navy16']
assert prod['weight']==0
assert prod['status']=='CONSTRUCTION_PRODUCTION_READY_SOURCE_GOLDEN_REVIEW_REQUIRED'
assert prod['candidateGoldenRegistry']=='generator/data/source_respecting_hat_goldens_fisherman_candidate.json'
assert 'approves' in prod['activationGate'].lower()

gold=json.load(open(ROOT/'generator/data/source_respecting_hat_goldens.json'))
assert 'bucket_fisherman_navy16' not in gold['families'],'candidate leaked into approved golden whitelist'

srcprod=(ROOT/'generator/source_respecting_hat_production.py').read_text()
assert "source=='bucket_fisherman'" in srcprod
print('PASS Fisherman is a source-respecting HAT_RENDERER_V1 extension with exact approved native pixels')
print('PASS 4 candidate goldens preserve alpha, mirror, and continuous source shading topology (no 5-bucket collapse)')
print('PASS frozen smoke keeps Common pixel-exact to each golden and bounds Rare to <=5 changed pixels')
print('PASS production remains weight 0 and candidate is not in the approved golden whitelist pending user review')
