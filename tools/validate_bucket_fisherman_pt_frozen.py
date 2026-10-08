#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from v5.pngio import read_rgba_png
from v5.source.template_transfer import alpha_cells

manifest=json.load(open(ROOT/'experiments/bucket_fisherman_pt_frozen_01/manifest.json'))
profile=json.load(open(ROOT/'authored/templates/bucket_fisherman_navy16/pt_profile.json'))
contract=json.load(open(ROOT/'generator/data/templates/bucket_fisherman_navy16.json'))
reg=json.load(open(ROOT/'generator/data/headwear/bucket_hat_production_registry.json'))
old=json.load(open(ROOT/'generator/data/headwear/bucket_fisherman_navy16_roll_matrix.json'))

assert manifest['status']=='CANDIDATE_REVIEW_REQUIRED'
assert manifest['photoTailor']['used'] is True
assert manifest['frozenRenderer']['used'] is True
assert manifest['frozenRenderer']['id']=='HAT_RENDERER_V1'
assert manifest['oldRejectedRendererImported'] is False
assert profile['photoTailorAuthority']['module']=='generator/photo_tailor_port.py'
assert 'build_shade_ramp' in profile['photoTailorAuthority']['mechanicsUsed']
assert contract['photoTailorProfile']=='authored/templates/bucket_fisherman_navy16/pt_profile.json'
assert contract['rendererContract']=='generator/data/hat_renderer_contract.json'
assert contract['rendererFamily']=='bucket_fisherman'
source={v:read_rgba_png(ROOT/f'authored/templates/bucket_fisherman_navy16/{v}.png') for v in ('front','right','back','left')}
for c in manifest['candidates']:
 for v,p in c['frames'].items():
  out=read_rgba_png(ROOT/p)
  assert alpha_cells(out)==alpha_cells(source[v]),(c['seed'],v,'alpha drift')
 assert read_rgba_png(ROOT/c['frames']['left'])==[list(reversed(r)) for r in read_rgba_png(ROOT/c['frames']['right'])],(c['seed'],'mirror drift')
 assert c['hybrid']['outlinePreserved'] is True and c['hybrid']['alphaPreserved'] is True
builder=(ROOT/'tools/build_bucket_fisherman_pt_frozen_proof.py').read_text()
assert 'from generator.hat_hybrid_enhancements import enhance_frames' in builder
assert 'bucket_fisherman_generator' not in builder
prod=reg['constructions']['bucket_fisherman_navy16']
assert prod['rendererId']=='HAT_RENDERER_V1'
assert prod['weight']==0
assert prod['status']=='CONSTRUCTION_PRODUCTION_READY_RENDERER_REVIEW_REQUIRED'
assert old['status']=='REJECTED_VISUAL_PROOF_DO_NOT_USE'
print('PASS Fisherman PT+frozen proof: actual permission-backed PT mechanics feed HAT_RENDERER_V1')
print('PASS 12 candidates preserve construction alpha and exact Right->Left mirror')
print('PASS rejected temporary mini-renderer is not imported or production-routed')
print('PASS construction remains approved; renderer activation is correctly gated on human visual review')
