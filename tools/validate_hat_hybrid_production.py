#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from generator.source_respecting_hat_production import RARITIES,roll_and_render
from v5.pngio import read_rgba_png
BATCH=ROOT/'experiments/hat_production_hybrid_final_01/manifest.json'
GOLD=ROOT/'experiments/hat_production_source_respecting_final_01/manifest.json'
VIEWS=('front','right','left','back')

def edge_mask(fr):
 h=len(fr);w=len(fr[0]);m=[[False]*w for _ in range(h)]
 for y,row in enumerate(fr):
  for x,p in enumerate(row):
   if not p[3]:continue
   if any(nx<0 or ny<0 or nx>=w or ny>=h or not fr[ny][nx][3] for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))):m[y][x]=True
 return m

def main():
 policy=json.load(open(ROOT/'generator/data/hat_hybrid_production_policy.json'))
 assert policy['goldenBaseline']=='HAT_PRODUCTION_GOLDEN_V1'
 assert policy['productionDependencyOnPhotoTailor'] is False
 assert policy['productionDependencyOnFashionSigLIP'] is False
 assert policy['prototypeImportsAllowed'] is False
 for rel in ('generator/hat_hybrid_enhancements.py','generator/source_respecting_hat_production.py','tools/build_hat_production_batch.py'):
  s=(ROOT/rel).read_text()
  for bad in ('from prototypes','import prototypes','onnxruntime','fashion_siglip_vision','photo_tailor_private_lab'):
   assert bad not in s,(rel,bad)
 m=json.load(open(BATCH));g=json.load(open(GOLD))
 assert m['schema']=='hat-production-source-respecting-hybrid/v1'
 assert m['candidateCount']==80 and m['familyCount']==20
 assert m['rarityCounts']=={r:20 for r in RARITIES}
 assert m['goldenBaseline']=='HAT_PRODUCTION_GOLDEN_V1'
 assert m['productionAuthority']=='GOLDEN_SOURCE_RESPECTING_HYBRID_V1'
 assert m['photoTailorDependency'] is False and m['prototypeImportsAllowed'] is False
 assert m['hybridAppliedCount']>0
 assert m['hybridFallbackCount']>=1 # proves hard-fallback gate is exercised in this batch
 gold={(c['family'],c['rarity']):c for c in g['candidates']}
 for c in m['candidates']:
  key=(c['family'],c['rarity']);gc=gold[key]
  assert c['approvedPair']['state']==gc['sourceState'] and c['approvedPair']['palette']==gc['palette'],(key,'golden pair drift')
  fresh=roll_and_render(c['family'],c['rarity'],m['presentationLeanMode']);res=fresh['renderResult']
  assert fresh['approvedPair']==c['approvedPair']
  assert fresh['hybridEnhancement']==c['hybridEnhancement']
  for v in VIEWS:
   saved=read_rgba_png(ROOT/c['frames'][v]);assert saved==res.frames[v],(key,v,'saved render drift')
   gf=read_rgba_png(ROOT/gc['frames'][v]);assert len(gf)==len(saved) and len(gf[0])==len(saved[0])
   em=edge_mask(gf)
   for y,row in enumerate(gf):
    for x,p in enumerate(row):
     q=saved[y][x];assert p[3]==q[3],(key,v,'alpha drift')
     if em[y][x]:assert p==q,(key,v,'outline drift')
  if c['hybridEnhancement']['fallbackReason']:
   assert all(read_rgba_png(ROOT/c['frames'][v])==read_rgba_png(ROOT/gc['frames'][v]) for v in VIEWS),(key,'fallback not exact golden')
 print('PASS native production has zero prototype/ONNX/FashionSigLIP imports')
 print('PASS 80 candidates = 20 families x 4 rarities')
 print('PASS all candidates retain the exact HAT_PRODUCTION_GOLDEN_V1 approved state/palette pair')
 print('PASS all 320 hybrid frames preserve golden alpha + exact outline pixels')
 print('PASS every saved frame pixel-matches a fresh native production render')
 print('PASS hard fallback exercised:',m['hybridFallbackCount'],'candidate(s) returned exact golden pixels')
 print('PASS hybrid applied:',m['hybridAppliedCount'],'of 80; changed pixels:',m['hybridChangedPixels'],'max ratio:',m['hybridMaxChangedRatio'])
if __name__=='__main__':main()
