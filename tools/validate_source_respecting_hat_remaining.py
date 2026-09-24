#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from generator.source_respecting_hat_remix import source_frames,source_family_state,_parts
from v5.pngio import read_rgba_png

MAN=ROOT/'experiments/source_respecting_hat_remaining_01/manifest.json'

def alpha(rows):
    return {(x,y) for y,row in enumerate(rows) for x,p in enumerate(row) if p[3]}

def main():
    model=json.loads((ROOT/'generator/data/source_respecting_remix_model.json').read_text())
    rem=model['pilot']['remaining13']
    parts=_parts()
    assert parts['schema']=='source-respecting-hat-parts/v3'
    assert len(rem['families'])==13
    assert rem['genericProjectionEnabled'] is False
    assert rem['genericLineSynthesisEnabled'] is False

    m=json.loads(MAN.read_text())
    assert m['candidateCount']==84 and len(m['candidates'])==84
    assert set(m['families'])==set(rem['families'])
    assert all(not e['genericProjectionUsed'] and not e['genericLineUsed'] for e in m['candidates'])

    # Every authored native state must be reproduced pixel-for-pixel.
    for family in rem['families']:
        spec=parts['families'][family]
        for state in spec['alternateConstructionStates']:
            r=source_family_state(family,state,'source_native')
            src,_=source_frames(spec['pack'],state)
            assert r.frames==src,(family,state)

    # Any tint must preserve geometry and only touch explicit body-role pixels.
    for e in m['candidates']:
        spec=parts['families'][e['family']]
        src,_=source_frames(spec['pack'],e['sourceState'])
        roles=spec['roleByStateRgb'][e['sourceState']]
        for v,path in e['frames'].items():
            out=read_rgba_png(ROOT/path)
            assert alpha(out)==alpha(src[v]),(e['family'],e['sourceState'],v)
            changed={(x,y) for y,row in enumerate(out) for x,p in enumerate(row)
                     if p!=src[v][y][x]}
            allowed={(x,y) for y,row in enumerate(src[v]) for x,p in enumerate(row)
                     if p[3] and roles[f'{p[0]},{p[1]},{p[2]}'].startswith('body_')}
            assert changed<=allowed,(e['family'],e['sourceState'],v,changed-allowed)

    print('PASS remaining 13 source-respecting families')
    print('PASS 84 candidates; no generic projection or line synthesis')
    print('PASS every authored native state is pixel-identical')
    print('PASS all tint variants preserve source alpha')
    print('PASS all tint changes stay inside explicit source body-role masks')

if __name__=='__main__':
    main()
