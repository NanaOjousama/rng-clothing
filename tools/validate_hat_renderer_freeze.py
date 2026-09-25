#!/usr/bin/env python3
from pathlib import Path
import json,re

ROOT=Path(__file__).resolve().parents[1]

def main():
    contract=json.load(open(ROOT/'generator/data/hat_renderer_contract.json'))
    policy=json.load(open(ROOT/'generator/data/hat_hybrid_production_policy.json'))
    audit=json.load(open(ROOT/'generator/data/hat_type_gap_audit.json'))

    assert contract['id']=='HAT_RENDERER_V1'
    assert contract['status']=='FROZEN'
    assert contract['goldenBaseline']=='HAT_PRODUCTION_GOLDEN_V1'
    assert contract['catalogFrozen'] is False
    assert contract['catalogExpansionAllowed'] is True
    assert contract['rendererRedesignRequiredForNewFamilies'] is False

    assert policy['rendererContract']=='HAT_RENDERER_V1'
    assert policy['rendererFrozen'] is True
    assert policy['catalogFrozen'] is False
    assert policy['catalogExpansionAllowed'] is True

    prod=(ROOT/'generator/source_respecting_hat_production.py').read_text()
    builder=(ROOT/'tools/build_hat_production_batch.py').read_text()
    assert "g.get('familyCount')!=20" not in prod
    assert "'familyCount':20" not in builder
    assert "'familyCount':len(hats)" in builder

    assert audit['rendererFrozen'] is True
    assert audit['catalogFrozen'] is False
    assert audit['productionFamilyCount']==20
    assert audit['sourceCatalogHatSlotAppearances']==116
    assert audit['sourceAppearancesCoveredByProductionContracts']==70
    assert audit['sourceAppearancesNotCoveredByProductionContracts']==46

    gaps={x['type']:x for x in audit['stillMissingFromProduction']}
    assert gaps['Cowboy hat']['status']=='SOURCE_PRESENT_UNPROMOTED'
    assert gaps['Baseball cap']['status']=='PHOTO_TAILOR_REBOOT_IN_PROGRESS'
    assert gaps['Dad cap']['status']=='CLEANROOM_REBOOT_PLANNED'
    assert gaps['Trucker cap']['status']=='CLEANROOM_REBOOT_PLANNED'
    assert gaps['Snapback cap']['status']=='DEFERRED_NOT_REQUIRED'
    assert gaps['Mario-style reference cap']['status']=='DEFERRED_EASTER_EGG'
    assert gaps['Paperboy / newsboy cap']['status']=='SOURCE_PRESENT_BUT_REJECTED'

    disp=audit['oldMaterialDisposition']
    assert 'experiments/dad_cap/' in disp['QUARANTINED_CAP_HISTORY']
    assert 'experiments/dad_cap_v2/' in disp['QUARANTINED_CAP_HISTORY']
    assert 'experiments/trucker_cap/' in disp['QUARANTINED_CAP_HISTORY']
    assert not any('dad_cap' in x or 'trucker_cap' in x for x in disp['KEEP_REFERENCE_OR_PROMOTION_INPUT'])

    print('PASS HAT_RENDERER_V1 is frozen while catalog remains expandable')
    print('PASS production loader/builder no longer hardcode exactly 20 families')
    print('PASS gap audit: 116 hat-slot sources, 70 covered, 46 uncovered')
    print('PASS cap reboot statuses: Baseball active; Dad/Trucker planned; Snapback/Mario deferred')
    print('PASS old Dad/Trucker visual history is quarantined, not used as active construction input')

if __name__=='__main__':
    main()
