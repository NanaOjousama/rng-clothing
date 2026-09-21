#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from v5.source.template_transfer import load_contract, verify_contract, decision

LIB=ROOT/'source_catalog/SOURCE_TRANSFER_LIBRARY.json'
TPL=ROOT/'generator/data/templates/slouch_pl24.json'
MATRIX=ROOT/'generator/data/headwear/slouch_beanie_roll_matrix.json'

def main():
    lib=json.loads(LIB.read_text())
    assert lib['schema']=='source-transfer-library/v1'
    assert lib['sourceAppearanceCount']==319
    assert lib['sourceFamilyCount']==53
    scopes=lib['counts']['transferScopes']
    assert scopes['STYLE_DONOR']==53
    assert scopes['FAMILY_REUSABLE']==12
    assert scopes['SAME_BASE_ONLY']==43
    assert scopes['ALTERNATE_CONSTRUCTION']==108
    assert len(lib['parts'])==216
    tpl=load_contract(TPL)
    rep=verify_contract(tpl)
    assert set(rep['views'])=={'front','right','left','back'}
    matrix=json.loads(MATRIX.read_text())
    policy=matrix['renderPolicy']
    assert policy['status']=='SLOUCH_SPECIFIC_RENDERER_REQUIRED'
    assert 'BRIMLESS_HAT' in policy['forbidGenericNormalization']
    assert matrix['templateContract']=='generator/data/templates/slouch_pl24.json'
    assert matrix['sourceTransferLibrary']=='source_catalog/SOURCE_TRANSFER_LIBRARY.json'

    reusable=[p for p in lib['parts'] if p['transferScope']=='FAMILY_REUSABLE']
    assert all(p.get('requiresZone') for p in reusable)
    assert all(decision(p,tpl)['decision']=='ALLOW' for p in reusable)

    same=[p for p in lib['parts'] if p['transferScope']=='SAME_BASE_ONLY']
    alt=[p for p in lib['parts'] if p['transferScope']=='ALTERNATE_CONSTRUCTION']
    assert all(decision(p,tpl)['decision']=='DENY' for p in same)
    assert all(decision(p,tpl)['decision']=='DENY' for p in alt)
    assert tpl.geometry_lock['forbidResample'] is True
    assert tpl.geometry_lock['forbidGenericNormalization'] is True
    print('PASS source-backed template generator')
    print('source appearances=319 families=53')
    print('style donors=53 reusable=12 same-base-only=43 alternate-construction=108')
    print('template=slouch_pl24 views=4 geometry hashes locked')

if __name__=='__main__':
    main()
