#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from generator.hat_visual_rules import (load_contracts,contract_for,palette_roles,harmony_tag,
    render_proportional_line,validate_line,validate_palette_frame,recipe_visual_precheck)

def frame(w=16,h=16):
    z=(0,0,0,0); out=[[z for _ in range(w)] for _ in range(h)]
    for y in range(3,12):
        inset=abs(7-y)//3
        for x in range(3+inset,13-inset): out[y][x]=(120,120,120,255)
    return out

def main():
    reg=load_contracts(); assert reg['schema']=='hat-visual-contract-registry/v1'
    assert len(reg['families'])==20
    required={'lineAllowed','lineSemanticType','lineZone','lineCenterYRatio','lineThicknessPxMax',
              'lineWidthRatioRange','lineMayTouchOutline','lineMayOverlapBrimBand',
              'lineContrastMaxStep','lineCountMax','lineForbiddenRowsRelativeToBottom'}
    for fam,c in reg['families'].items():
        assert required<=set(c['linePlacement']),fam
        q=c['paletteSanity']
        assert q['explicitRoles']==['outline','shadow','midtone','light','accent']
        assert 0<q['accentPixelBudgetMax']<=0.18
        assert q['accentPixelBudgetMinPixels']>=2

    vc=contract_for('catalog_hats_cottagecore_set_boater_hat')
    roles=palette_roles([(35,35,35),(85,85,85),(145,145,145),(210,210,210)])
    fr=frame(); out,meta=render_proportional_line(fr,vc['linePlacement'],roles,'contrast')
    assert meta['applied'] and meta['thicknessPx']==1
    assert not validate_line(meta,vc['linePlacement'])
    x=dict(meta);x['thicknessPx']=2
    assert 'line:too_thick' in validate_line(x,vc['linePlacement'])
    x=dict(meta);x['centerYRatio']=0.90
    assert 'line:too_low_or_high' in validate_line(x,vc['linePlacement'])
    x=dict(meta);x['widthRatio']=0.99
    assert 'line:too_wide_or_narrow' in validate_line(x,vc['linePlacement'])


    for pilot_family in (
        'catalog_hats_cottagecore_set_beret',
        'catalog_hats_more_accessories_and_stuff_beanie',
        'catalog_hats_more_accessories_and_stuff_straw_hat',
    ):
        pc=contract_for(pilot_family)
        assert pc['linePlacement']['lineAllowed'] is False
        assert pc['linePlacement'].get('replacementAuthority')=='SOURCE_RESPECTING_REMIX_ONLY'

    frag=dict(meta)
    row=frag['row']; x0,y0,x1,y1=frag['bbox']
    cx=(x0+x1)//2
    frag['cells']=[(cx-1,row),(cx,row),(cx+1,row)]
    frag['widthPx']=3
    frag['widthBasisPx']=max(10,frag.get('widthBasisPx',10))
    frag['widthRatio']=3/frag['widthBasisPx']
    ferr=validate_line(frag,vc['linePlacement'])
    assert 'line:isolated_center_fragment' in ferr

    hood=contract_for('catalog_hats_more_accessories_and_stuff_hood')
    assert recipe_visual_precheck({'trim':'contrast'},hood)==['line:family_disallows_line']
    assert harmony_tag([(40,40,40),(110,110,110),(215,215,215)]) in ('soft_neutral','alt_monochrome')
    masks={'MOTIF':{(x,y) for y in (5,6,7) for x in range(3,13)}}
    errors,metrics=validate_palette_frame(out,roles,vc,masks,'soft_neutral',reference_frame=fr)
    assert 'palette:accent_budget' in errors

    print('PASS 20 per-family visual contracts')
    print('PASS proportional line placement and thickness/width/height rejection')
    print('PASS family line prohibition, pilot opt-out, and isolated-fragment rejection')
    print('PASS explicit palette roles and harmony tagging')
    print('PASS accent budget rejection and discrete pixel floors')

if __name__=='__main__':
    main()
