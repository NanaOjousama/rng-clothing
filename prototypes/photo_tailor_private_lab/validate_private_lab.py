#!/usr/bin/env python3
from pathlib import Path
import json,re,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1];OUT=REPO/'experiments/photo_tailor_private_lab_01'
REQ={'4_view_projection','construction_template_drafting','normalized_motif_placement','facing_scopes','base_overlay_layers','occupancy_region_masks','normalized_pattern_coordinates','color_bands','semantic_pattern_fields','separate_region_palettes','shading_topology','texture_pattern_cleanup','coherent_detail_propagation'}

def arr(p):return np.array(Image.open(p).convert('RGBA'))
def alpha(p):return arr(p)[:,:,3]>0

def main():
 # Isolation: executable prototype code must not import the production generator/render stack.
 for p in list(ROOT.rglob('*.py')):
  if p.name=='validate_private_lab.py':continue
  s=p.read_text()
  forbidden=[a+' '+b for a in ('from','import') for b in ('generator','v5','mods')]
  for bad in forbidden:assert bad not in s,(p,bad)
 m=json.load(open(OUT/'manifest.json'));assert m['privateDisposablePrototype'] is True
 assert m['productionImports'] is False and m['productionGeneratorModified'] is False
 assert REQ<=set(m['featureCoverage']);assert len(m['designs'])==8
 controls=json.load(open(ROOT/'control_assets/controls.json'));assert len(controls['controls'])==8
 byid={c['id']:c for c in controls['controls']}
 for d in m['designs']:
  did=d['design_id'];cid=d['control_id'];od=OUT/did
  assert d['normalized_pattern_coordinates'] and d['base_overlay_separation'] and d['shading_topology_preserved'] and d['texture_cleanup'] and d['coherent_four_view_projection']
  for v in ('front','right','left','back'):
   ctrl=ROOT/byid[cid]['frames'][v]
   final=od/f'{v}.png';base=od/f'{v}_base.png';overlay=od/f'{v}_overlay.png';occ=od/f'{v}_occupancy.png';reg=od/f'{v}_regions.png'
   for p in (final,base,overlay,occ,reg):assert p.exists(),p
   assert np.array_equal(alpha(ctrl),alpha(final)),(did,v,'alpha geometry drift')
   assert np.array_equal(alpha(ctrl),alpha(base)),(did,v,'base geometry drift')
   a,b,o=arr(final),arr(base),arr(overlay);mask=o[:,:,3]>0
   assert np.array_equal(a[~mask],b[~mask]),(did,v,'base/overlay leak')
 # Concrete facing-scope proofs.
 def counts(design):return {v:int((arr(OUT/design/f'{v}_overlay.png')[:,:,3]>0).sum()) for v in ('front','right','left','back')}
 assert counts('beanie_knit_badge')['front']>0 and all(counts('beanie_knit_badge')[v]==0 for v in ('right','left','back'))
 hc=counts('hood_two_tone_seams');assert hc['front']>0 and hc['back']>0 and hc['right']==0 and hc['left']==0
 sc=counts('sun_floral_brim');assert all(sc[v]>0 for v in sc),sc
 # Pattern cleanup still leaves meaningful evidence on all intended stress cases.
 for did in ('beret_plaid_flower','beanie_knit_badge','mushroom_spotted','sun_floral_brim','tulip_vertical'):
  d=next(x for x in m['designs'] if x['design_id']==did);assert sum(d['pattern_cells_after_cleanup'].values())>0,did
 for p in ('PHOTO_TAILOR_PRIVATE_LAB_CONTACT.png','PHOTO_TAILOR_PRIVATE_LAB_BASE_OVERLAY.png','PHOTO_TAILOR_PRIVATE_LAB_MASKS.png'):assert (OUT/p).exists()
 print('PASS private prototype imports no production generator/render modules')
 print('PASS 8 copied controls preserve alpha geometry across all 32 final views')
 print('PASS base/overlay layers are separated with no leakage')
 print('PASS FrontOnly, Front+Back, and AllFacings scope behaviors')
 print('PASS normalized pattern cleanup retains meaningful detail on 5 patterned stress cases')
 print('PASS all 13 requested Photo Tailor-style systems covered')
 print('PASS disposable outputs: 1 main contact + base/overlay + occupancy/region mask sheet')
if __name__=='__main__':main()
