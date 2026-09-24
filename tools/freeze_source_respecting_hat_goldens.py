#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BATCHES=[
 ('pilot','experiments/source_respecting_hat_pilot_01/manifest.json'),
 ('batch_a','experiments/source_respecting_hat_batch_a_01/manifest.json'),
 ('remaining','experiments/source_respecting_hat_remaining_01/manifest.json'),
]
MAP={
 'catalog_hats_alt_fashion_set_beanie':'alt_beanie',
 'catalog_hats_alt_fashion_set_earmuffs_horns':'alt_earmuffs',
 'catalog_hats_alt_fashion_set_headband_studded':'alt_headband',
 'catalog_hats_cottagecore_set_beret':'beret',
 'catalog_hats_cottagecore_set_boater_hat':'boater_hat',
 'catalog_hats_cottagecore_set_headband_daisies':'cc_headband',
 'catalog_hats_cottagecore_set_headscarf':'cc_headscarf',
 'catalog_hats_cottagecore_set_hood_mushroom':'cc_hood',
 'catalog_hats_cottagecore_set_mushroom_hat':'mushroom_hat',
 'catalog_hats_more_accessories_and_stuff_beanie':'beanie',
 'catalog_hats_more_accessories_and_stuff_bows_double_small_1':'mas_bows',
 'catalog_hats_more_accessories_and_stuff_crown_diadem_1':'mas_crown',
 'catalog_hats_more_accessories_and_stuff_earmuffs':'mas_earmuffs',
 'catalog_hats_more_accessories_and_stuff_garland_dried_1':'mas_garland',
 'catalog_hats_more_accessories_and_stuff_hair_buns':'mas_hair_buns',
 'catalog_hats_more_accessories_and_stuff_headband':'mas_headband',
 'catalog_hats_more_accessories_and_stuff_hood':'mas_hood',
 'catalog_hats_more_accessories_and_stuff_straw_hat':'straw_hat',
 'catalog_hats_more_accessories_and_stuff_sun_hat':'sun_hat',
 'catalog_hats_more_accessories_and_stuff_tulip_hat':'tulip_hat',
}

def sha(path):
 return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
 by_family={}; batch_meta=[]
 for batch_id,rel in BATCHES:
  p=ROOT/rel;j=json.loads(p.read_text())
  j['humanArtApproved']=True;j['humanApprovalStatus']='HUMAN_ART_APPROVED'
  for c in j.get('candidates',[]): c['status']='HUMAN_ART_APPROVED'
  p.write_text(json.dumps(j,indent=2)+'\n')
  batch_meta.append({'id':batch_id,'manifest':rel,'candidateCount':j['candidateCount']})
  for c in j['candidates']:
   pair={'state':c['sourceState'],'palette':c['palette'],'batch':batch_id}
   arr=by_family.setdefault(c['family'],[])
   if not any(x['state']==pair['state'] and x['palette']==pair['palette'] for x in arr):arr.append(pair)
 parts_path=ROOT/'generator/data/source_parts/hat_source_parts.json'
 parts=json.loads(parts_path.read_text())
 for k,s in parts['families'].items():
  s['humanArtApproved']=True;s['productionAuthority']='GOLDEN_SOURCE_RESPECTING_V1'
 parts_path.write_text(json.dumps(parts,indent=2)+'\n')
 model_path=ROOT/'generator/data/source_respecting_remix_model.json'
 model=json.loads(model_path.read_text())
 model['pilot']['status']='HUMAN_ART_APPROVED'
 model['pilot']['batchA']['status']='HUMAN_ART_APPROVED'
 model['pilot']['remaining13']['status']='HUMAN_ART_APPROVED'
 model['production']={
  'status':'AUTHORITATIVE','authority':'GOLDEN_SOURCE_RESPECTING_V1',
  'familyCount':20,'genericProjectionEnabled':False,'genericLineSynthesisEnabled':False,
  'legacyStyleProfileFallbackEnabled':False,'approvedPairWhitelistRequired':True,
  'goldenRegistry':'generator/data/source_respecting_hat_goldens.json'}
 model_path.write_text(json.dumps(model,indent=2)+'\n')
 families={}
 for template,source in MAP.items():
  if source not in by_family: raise RuntimeError(f'missing approved candidates for {source}')
  spec=parts['families'][source]
  payload={'templateFamily':template,'sourceFamily':source,
   'approvedPairs':by_family[source],
   'lockedConstruction':spec.get('lockedConstruction',[]),
   'mutableSourceFeatures':spec.get('mutableSourceFeatures',[]),
   'optionalAddonParts':spec.get('optionalAddonParts',[]),
   'alternateConstructionStates':spec.get('alternateConstructionStates',[]),
   'humanArtApproved':True,'productionAuthority':'GOLDEN_SOURCE_RESPECTING_V1'}
  payload['contractDigest']=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
  families[template]=payload
 registry={'schema':'source-respecting-hat-goldens/v1','humanArtApproved':True,
  'approvedOn':'2026-09-24','familyCount':len(families),
  'authority':'GOLDEN_SOURCE_RESPECTING_V1',
  'rules':{'approvedPairWhitelistRequired':True,'genericProjectionAllowed':False,
   'genericLineSynthesisAllowed':False,'legacyStyleProfileFallbackAllowed':False,
   'sourceConstructionRulesAuthoritative':True,
   'rarityMaySelectOnlyApprovedStatePalettePairs':True,
   'presentationLeanValues':['neutral','male_leaning','female_leaning'],
   'presentationLeanIsBiasNotHardLock':True},
  'approvedBatches':batch_meta,'families':families}
 out=ROOT/'generator/data/source_respecting_hat_goldens.json'
 out.write_text(json.dumps(registry,indent=2)+'\n')
 # Record final hashes after approval mutation.
 registry=json.loads(out.read_text())
 for row in registry['approvedBatches']:row['manifestSha256']=sha(ROOT/row['manifest'])
 registry['sourcePartsSha256']=sha(parts_path)
 out.write_text(json.dumps(registry,indent=2)+'\n')
 print('PASS froze',len(families),'golden hat families')
 print('PASS approved pairs',sum(len(v['approvedPairs']) for v in families.values()))
 for row in registry['approvedBatches']: print('APPROVED',row['id'],row['candidateCount'])
if __name__=='__main__':main()
