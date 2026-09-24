#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from generator.source_respecting_hat_remix import (
    source_frames,beret,beanie,straw,verify_patch_reconstruction,_parts
)
from v5.pngio import read_rgba_png

MAN=ROOT/'experiments/source_respecting_hat_pilot_01/manifest.json'

def alpha(rows):
    return {(x,y) for y,row in enumerate(rows) for x,p in enumerate(row) if p[3]}

def main():
    spec=json.loads((ROOT/'generator/data/source_respecting_remix_model.json').read_text())
    assert spec['schema']=='source-respecting-remix-model/v1'
    assert spec['pilot']['genericLineSynthesisEnabled'] is False
    assert spec['pilot']['generatedVariationLastResortEnabled'] is False
    parts=_parts()
    assert parts['genericProjectionAllowed'] is False
    assert parts['genericLineSynthesisAllowed'] is False
    assert parts['rules']['paletteRolesAreBoundToExactSourceRgb'] is True

    for cid in ('beret.dots_patch','beret.leaf_patch','beret.ribbon_patch','beret.white_ribbon_patch'):
        assert verify_patch_reconstruction(cid),cid

    m=json.loads(MAN.read_text())
    assert m['candidateCount']==27
    assert len(m['candidates'])==27
    assert all(not e['genericProjectionUsed'] and not e['genericLineUsed'] for e in m['candidates'])
    assert all(not e['lineFragmentErrors'] for e in m['candidates'])

    # Native variants are source-authoritative pixel-for-pixel.
    for state in ('Beret','Beret (Dotted)','Beret (Leaf)','Beret (Ribbon)','Beret (White Ribbon)'):
        r=beret(state=state,palette='source_native')
        src,_=source_frames('Cottagecore Set',state)
        assert r.frames==src,state
    for state in ('Beanie','Beanie (Floppy)','Beanie (Cat)'):
        r=beanie(construction=state,palette='source_native')
        src,_=source_frames('More Accessories and Stuff',state)
        assert r.frames==src,state
    for state in ('Straw Hat','Straw Hat (Messy)'):
        r=straw(construction=state,ribbon_palette='source_native')
        src,_=source_frames('More Accessories and Stuff',state)
        assert r.frames==src,state

    # Every recolour keeps its source construction alpha.
    for e in m['candidates']:
        for v,path in e['frames'].items():
            out=read_rgba_png(ROOT/path)
            fam=e['family']; state=e['sourceState']
            pack='Cottagecore Set' if fam=='beret' else 'More Accessories and Stuff'
            src,_=source_frames(pack,state)
            assert alpha(out)==alpha(src[v]),(e['label'],v)

    # Straw palette changes may touch only the stored built-in-ribbon mask.
    p=parts['families']['straw_hat']
    for state in ('Straw Hat','Straw Hat (Messy)'):
        roles=p['roleByConstructionRgb'][state]
        src,_=source_frames('More Accessories and Stuff',state)
        ribbon={v:{(x,y) for y,row in enumerate(src[v]) for x,pix in enumerate(row)
                   if pix[3] and roles[f'{pix[0]},{pix[1]},{pix[2]}'].startswith('ribbon_')}
                for v in src}
        for pal in ('cream','dusty_rose','sage'):
            r=straw(construction=state,ribbon_palette=pal)
            for v in r.frames:
                changed={(x,y) for y,row in enumerate(r.frames[v]) for x,pix in enumerate(row)
                         if pix!=src[v][y][x]}
                assert changed<=ribbon[v],(state,pal,v,changed-ribbon[v])

    print('PASS source-respecting remix model contract')
    print('PASS 4 exact beret source patches reconstruct author variants')
    print('PASS 27 pilot candidates; no generic projection or line synthesis')
    print('PASS native variants are pixel-identical to source render frames')
    print('PASS all recolours preserve source alpha')
    print('PASS straw recolours touch only built-in source ribbon mask')

if __name__=='__main__':main()
