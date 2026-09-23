#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from generator.catalog_templates import load_template_for_family, load_family, evaluate_family_recipe, list_families, compatible_donors

REPORT=ROOT/'generator/data/templates/catalog_promotion_report.json'
TIDX=ROOT/'generator/data/templates/index.json'
TREG=ROOT/'generator/data/taste_policy_registry.json'

def main():
    report=json.loads(REPORT.read_text())
    tidx=json.loads(TIDX.read_text())
    treg=json.loads(TREG.read_text())
    assert report['familyBaseCount']==report['promotedCount']+report['deferredCount']
    assert report['familyBaseCount']==53
    assert report['promotedCount']>0
    promoted_ids={row['family'] for row in report['promoted']}
    deferred_ids={row['family'] for row in report['deferred']}
    assert len(promoted_ids)==report['promotedCount']
    assert len(deferred_ids)==report['deferredCount']
    assert not (promoted_ids & deferred_ids)
    assert len(promoted_ids | deferred_ids)==report['familyBaseCount']
    assert {x['family'] for x in tidx.get('deferredCatalogFamilies',[])}==deferred_ids
    assert {x['family'] for x in treg.get('deferredCatalogFamilies',[])}==deferred_ids
    for row in report['promoted']:
        fam=row['family']; tid=row['template']
        assert tid in tidx['templates']
        te=tidx['templates'][tid]
        assert te['family']==fam and te['status']=='CANDIDATE_READY'
        assert te.get('humanArtApprovalRequired') is True
        assert fam in treg['families'] and treg['families'][fam]['status']=='ACTIVE'
        contract=load_template_for_family(fam)
        assert contract.family==fam
        policy=load_family(fam)
        rr=evaluate_family_recipe(fam,'common',policy['defaultRecipe'])
        assert rr.valid,(fam,rr.errors)
    # Third-party source art is referenced from generator content; promoter only writes JSON contracts/policies.
    catalog_dir=ROOT/'generator/data/templates/catalog'
    assert not list(catalog_dir.glob('*.png'))
    belt=next(x['family'] for x in list_families(include_manual=False) if x.get('sourceName')=='Belt')
    donors=compatible_donors(belt)
    assert any(x['part'].get('transferScope')=='SAME_BASE_ONLY' for x in donors['allowed'])
    assert not any(x['part'].get('transferScope')=='ALTERNATE_CONSTRUCTION' for x in donors['allowed'])
    print('PASS catalog template promotions')
    print('promoted',report['promotedCount'],'deferred',report['deferredCount'])
    cats={}
    for r in report['promoted']: cats[r['category']]=cats.get(r['category'],0)+1
    print('promoted_by_category',cats)

if __name__=='__main__': main()
