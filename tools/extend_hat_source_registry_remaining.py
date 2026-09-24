#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from generator.source_respecting_hat_remix import source_frames

REG=ROOT/'generator/data/source_parts/hat_source_parts.json'
data=json.loads(REG.read_text())

FAMILIES={
 'alt_beanie':('Alt-Fashion Set','Beanie',['Beanie','Beanie (Bunny)','Beanie (Cat)','Beanie (Floppy)']),
 'alt_earmuffs':('Alt-Fashion Set','Earmuffs (Horns)',['Earmuffs (Angel Wings)','Earmuffs (Bat Wings)','Earmuffs (Horns)']),
 'alt_headband':('Alt-Fashion Set','Headband (Studded)',['Headband (Horns)','Headband (Studded)','Headband (Wide)','Headband (Wide, Studded)']),
 'cc_headband':('Cottagecore Set','Headband (Daisies)',['Headband (Daisies)','Headband (Ribbon)']),
 'cc_headscarf':('Cottagecore Set','Headscarf',['Headscarf','Headscarf (Dotted)','Headscarf (Small)','Headscarf (Small, Dotted)']),
 'cc_hood':('Cottagecore Set','Hood (Mushroom)',['Hood (Mushroom)','Hood (Pointy)']),
 'mas_bows':('More Accessories and Stuff','Bows (Double, Small 1)',['Bows (Double)','Bows (Double, Side)','Bows (Double, Small 1)','Bows (Double, Small 2)']),
 'mas_crown':('More Accessories and Stuff','Crown (Diadem 1)',['Crown (Coronet)','Crown (Diadem 1)','Crown (Diadem 2)']),
 'mas_earmuffs':('More Accessories and Stuff','Earmuffs',['Earmuffs','Earmuffs (Cat)']),
 'mas_garland':('More Accessories and Stuff','Garland (Dried 1)',['Garland 1','Garland 2','Garland (Dried 1)','Garland (Dried 2)','Garland (Flowers 1)','Garland (Flowers 2)']),
 'mas_hair_buns':('More Accessories and Stuff','Hair Buns',['Hair Buns','Hair Buns (Small)']),
 'mas_headband':('More Accessories and Stuff','Headband',['Headband','Headband (Cat 1)','Headband (Cat 2)','Headband (Frilly 1)','Headband (Frilly 2)','Headband (Puffs)','Headband (Small)','Headband (Tie 1)','Headband (Tie 2)']),
 'mas_hood':('More Accessories and Stuff','Hood',['Hood','Hood (Cat)','Hood (Frog)','Hood (Horns)','Hood (Rabbit)']),
}

def roles(pack,state):
    fr,_=source_frames(pack,state)
    colors=sorted({tuple(p[:3]) for rows in fr.values() for row in rows for p in row if p[3]})
    gray=[c for c in colors if c[0]==c[1]==c[2]]
    chrom=[c for c in colors if c[0]!=c[1] or c[1]!=c[2]]
    out={}
    labels=['body_outline','body_shadow','body_mid_dark','body_midtone','body_light','body_highlight','body_spec','body_spec2']
    for i,c in enumerate(sorted(gray,key=lambda c:c[0])):
        out[','.join(map(str,c))]=labels[min(i,len(labels)-1)]
    for c in chrom:
        out[','.join(map(str,c))]='locked_source_color'
    return out,not chrom

for key,(pack,base,states) in FAMILIES.items():
    role_maps={}; tintable={}
    for state in states:
        rm,ok=roles(pack,state);role_maps[state]=rm;tintable[state]=ok
    data['families'][key]={
      'pack':pack,'base':base,
      'lockedConstruction':['whole_source_geometry','defining_seams','source_shading_topology'],
      'mutableSourceFeatures':['body_color_if_fully_grayscale'],
      'optionalAddonParts':[],
      'alternateConstructionStates':states,
      'roleByStateRgb':role_maps,
      'tintableState':tintable,
      'statePolicy':'WHOLE_AUTHORED_SOURCE_STATE'
    }

data['schema']='source-respecting-hat-parts/v3'
data['rules']['remainingFamiliesUseWholeSourceStates']=True
REG.write_text(json.dumps(data,indent=2)+'\n')
print('PASS extended registry families',len(data['families']))
for key in FAMILIES:
    spec=data['families'][key]
    print(key,'states',len(spec['alternateConstructionStates']),
          'tintable',sum(spec['tintableState'].values()))
