#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
pairs={
 'catalog_hats_alt_fashion_set_beanie':'alt_beanie',
 'catalog_hats_alt_fashion_set_earmuffs_horns':'alt_earmuffs',
 'catalog_hats_alt_fashion_set_headband_studded':'alt_headband',
 'catalog_hats_cottagecore_set_headband_daisies':'cc_headband',
 'catalog_hats_cottagecore_set_headscarf':'cc_headscarf',
 'catalog_hats_cottagecore_set_hood_mushroom':'cc_hood',
 'catalog_hats_more_accessories_and_stuff_bows_double_small_1':'mas_bows',
 'catalog_hats_more_accessories_and_stuff_crown_diadem_1':'mas_crown',
 'catalog_hats_more_accessories_and_stuff_earmuffs':'mas_earmuffs',
 'catalog_hats_more_accessories_and_stuff_garland_dried_1':'mas_garland',
 'catalog_hats_more_accessories_and_stuff_hair_buns':'mas_hair_buns',
 'catalog_hats_more_accessories_and_stuff_headband':'mas_headband',
 'catalog_hats_more_accessories_and_stuff_hood':'mas_hood',
}
modelp=ROOT/'generator/data/source_respecting_remix_model.json'
model=json.loads(modelp.read_text())
all_keys=list(model['pilot']['families'])+[v for v in pairs.values() if v not in model['pilot']['families']]
model['pilot']['families']=all_keys
model['pilot']['remaining13']={
 'families':list(pairs.values()),
 'status':'HUMAN_ART_REVIEW_REQUIRED',
 'genericProjectionEnabled':False,
 'genericLineSynthesisEnabled':False,
 'wholeAuthoredSourceStateDefault':True
}
model['pilot']['sourceParts']='generator/data/source_parts/hat_source_parts.json'
modelp.write_text(json.dumps(model,indent=2)+'\n')

vp=ROOT/'generator/data/hat_visual_contracts.json'
vis=json.loads(vp.read_text())
for template,key in pairs.items():
    line=vis['families'][template]['linePlacement']
    line['lineAllowed']=False
    line['replacementAuthority']='SOURCE_RESPECTING_REMIX_ONLY'
vp.write_text(json.dumps(vis,indent=2)+'\n')
print('PASS activated remaining 13')
print('source-respecting families',len(model['pilot']['families']))
