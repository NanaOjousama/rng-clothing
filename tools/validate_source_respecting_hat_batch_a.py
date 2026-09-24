#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from generator.source_respecting_hat_remix import (
    source_frames,boater,mushroom_hat,sun_hat,tulip_hat,
    verify_patch_reconstruction,_parts
)
from v5.pngio import read_rgba_png

MAN=ROOT/'experiments/source_respecting_hat_batch_a_01/manifest.json'

def alpha(rows):
    return {(x,y) for y,row in enumerate(rows) for x,p in enumerate(row) if p[3]}

def main():
    spec=json.loads((ROOT/'generator/data/source_respecting_remix_model.json').read_text())
    batch=spec['pilot']['batchA']
    assert batch['families']==['boater_hat','mushroom_hat','sun_hat','tulip_hat']
    assert batch['genericProjectionEnabled'] is False
    assert batch['genericLineSynthesisEnabled'] is False
    parts=_parts()
    assert parts['schema']=='source-respecting-hat-parts/v2'
    assert parts['genericProjectionAllowed'] is False
    assert parts['genericLineSynthesisAllowed'] is False
    assert parts['rules']['paletteRolesAreBoundToExactSourceRgb'] is True

    patch_ids=('boater.bow_patch','boater.ribbons_patch','mushroom.dotted_patch',
               'sun_hat.flowers_patch','sun_hat.ribbon_patch','tulip.striped_patch')
    for cid in patch_ids: assert verify_patch_reconstruction(cid),cid

    m=json.loads(MAN.read_text())
    assert m['candidateCount']==36 and len(m['candidates'])==36
    assert all(not e['genericProjectionUsed'] and not e['genericLineUsed'] for e in m['candidates'])
    assert all(not e['lineFragmentErrors'] for e in m['candidates'])

    native=[
      (boater,{'state':'Boater Hat','feature_palette':'source_native'},'Cottagecore Set','Boater Hat'),
      (boater,{'state':'Boater Hat (Bow)','feature_palette':'source_native'},'Cottagecore Set','Boater Hat (Bow)'),
      (boater,{'state':'Boater Hat (Ribbons)','feature_palette':'source_native'},'Cottagecore Set','Boater Hat (Ribbons)'),
      (mushroom_hat,{'state':'Mushroom Hat','body_palette':'source_native'},'Cottagecore Set','Mushroom Hat'),
      (mushroom_hat,{'state':'Mushroom Hat (Dotted)','body_palette':'source_native'},'Cottagecore Set','Mushroom Hat (Dotted)'),
      (sun_hat,{'state':'Sun Hat','body_palette':'source_native'},'More Accessories and Stuff','Sun Hat'),
      (sun_hat,{'state':'Sun Hat (Flowers)','body_palette':'source_native'},'More Accessories and Stuff','Sun Hat (Flowers)'),
      (sun_hat,{'state':'Sun Hat (Ribbon)','feature_palette':'source_native'},'More Accessories and Stuff','Sun Hat (Ribbon)'),
      (tulip_hat,{'state':'Tulip Hat','body_palette':'source_native'},'More Accessories and Stuff','Tulip Hat'),
      (tulip_hat,{'state':'Tulip Hat (Striped)','pattern_palette':'source_native'},'More Accessories and Stuff','Tulip Hat (Striped)'),
    ]
    for fn,kwargs,pack,state in native:
        r=fn(**kwargs);src,_=source_frames(pack,state);assert r.frames==src,state

    pack_of={'boater_hat':'Cottagecore Set','mushroom_hat':'Cottagecore Set',
             'sun_hat':'More Accessories and Stuff','tulip_hat':'More Accessories and Stuff'}
    for e in m['candidates']:
        src,_=source_frames(pack_of[e['family']],e['sourceState'])
        roles=parts['families'][e['family']]['roleByStateRgb'][e['sourceState']]
        prefix=('feature_' if e['family']=='boater_hat' else
                'body_' if e['family']=='mushroom_hat' else
                ('feature_' if e['family']=='sun_hat' and e['sourceState']=='Sun Hat (Ribbon)' else 'body_')
                if e['family']=='sun_hat' else
                ('pattern_' if e['sourceState']=='Tulip Hat (Striped)' else 'body_'))
        for v,path in e['frames'].items():
            out=read_rgba_png(ROOT/path)
            assert alpha(out)==alpha(src[v]),(e['label'],v)
            changed={(x,y) for y,row in enumerate(out) for x,pix in enumerate(row)
                     if pix!=src[v][y][x]}
            allowed={(x,y) for y,row in enumerate(src[v]) for x,pix in enumerate(row)
                     if pix[3] and roles[f'{pix[0]},{pix[1]},{pix[2]}'].startswith(prefix)}
            assert changed<=allowed,(e['label'],v,changed-allowed)

    print('PASS Batch A source-respecting remix contract')
    print('PASS 6 exact source patches reconstruct author variants')
    print('PASS 36 candidates; no generic projection or line synthesis')
    print('PASS 10 native source states are pixel-identical')
    print('PASS all recolours preserve source alpha')
    print('PASS every recolour stays inside its explicit source RGB role mask')

if __name__=='__main__':main()
