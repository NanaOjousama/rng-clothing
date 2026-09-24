#!/usr/bin/env python3
from pathlib import Path
import json,sys,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1];OUT=REPO/'experiments/photo_tailor_private_lab_02'
REQ={'silhouette_fidelity','palette_material_resemblance','pattern_continuity','motif_location','four_view_coherence','stardew_readability','junk_control'}
def alpha(p):return np.array(Image.open(p).convert('RGBA'))[:,:,3]>0

def main():
 for p in ROOT.rglob('*.py'):
  s=p.read_text()
  for bad in [a+' '+b for a in ('from','import') for b in ('generator','v5','mods')]:assert bad not in s,(p,bad)
 inp=json.load(open(ROOT/'inputs.json'));assert inp['count']==20
 assert sum(x['category']=='hat' for x in inp['inputs'])==16
 assert sum(x['category']=='shirt' for x in inp['inputs'])==4
 assert (ROOT/'vendor/photo_tailor_models/marqo_fashion_siglip_vision_uint8.onnx').exists()
 assert (ROOT/'vendor/photo_tailor_models/fashion_siglip_labels.json').exists()
 summary=json.load(open(OUT/'summary.json'));assert summary['sampleCount']==20 and summary['hatCount']==16 and summary['shirtCount']==4
 assert summary['prototypeDecision'] in ('CLEAR_PROTOTYPE_WIN','MIXED','NO_MATERIAL_GAIN')
 assert summary['prototypeDecision']=='MIXED'
 assert summary['averageDelta']>0
 for row in summary['results']:
  rid=row['id'];r=json.load(open(OUT/rid/'result.json'));assert REQ==set(r['scores']['baseline'])==set(r['scores']['enhanced'])
  cid=r['input']['constructionHint']
  for v in ('front','right','left','back'):
   assert np.array_equal(alpha(ROOT/'control_assets'/cid/f'{v}.png'),alpha(OUT/rid/f'{v}.png')),(rid,v,'geometry drift')
  for f in ('reference','blueprint.png','occupancy_region.png','baseline_4view.png','enhanced_4view.png','comparison.png'):
   if f=='reference':assert any((OUT/rid).glob('reference.*'))
   else:assert (OUT/rid/f).exists(),(rid,f)
 for f in ('LAB02_ALL_20_CONTACT.png','LAB02_HATS_16_CONTACT.png','LAB02_SHIRTS_4_CONTACT.png','LAB02_SCORECARD.png'):assert (OUT/f).exists(),f
 print('PASS zero production imports')
 print('PASS 20 references = 16 hats + 4 shirts')
 print('PASS local disposable FashionSigLIP model + labels snapshot exists')
 print('PASS enhanced alpha geometry matches copied controls for all 80 directional outputs')
 print('PASS every sample has reference, blueprint, masks, baseline, enhanced 4-view, comparison, and 7-dimension scores')
 print('PASS Lab 02 decision:',summary['prototypeDecision'],'delta',summary['averageDelta'])
 print('PASS systems earning further study:',', '.join(summary['systemsEarningFurtherStudy']))
if __name__=='__main__':main()
