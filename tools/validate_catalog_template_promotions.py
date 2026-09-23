#!/usr/bin/env python3
from __future__ import annotations
import itertools, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from generator.catalog_templates import load_template_for_family, load_family, evaluate_family_recipe, list_families, compatible_donors, source_family_entry
from v5.source.template_transfer import compile_recipe

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
        assert all('opaqueCells' in spec for spec in contract.frames.values())
        assert max(int(spec['opaqueCells']) for spec in contract.frames.values())>0
        policy=load_family(fam)
        cap=policy['familyCapacity']
        assert cap['surfaceAreaClass'] in {'tiny','small','medium','large'}
        assert 2 <= int(cap['maxComplexity']) <= 5
        assert cap['rarityCeilingStrategy']=='COMPRESS_BUDGET_NOT_DISABLE_TIER'
        rr=evaluate_family_recipe(fam,'common',policy['defaultRecipe'])
        assert rr.valid,(fam,rr.errors)

        # Every promoted family must map back to its source family and compile
        # at least one real source-backed recipe through the shared transfer planner.
        assert source_family_entry(fam) is not None
        donor_plan=compatible_donors(fam)
        styles=[x['part'] for x in donor_plan['allowed'] if x['part'].get('partKind')=='STYLE_PROFILE']
        assert styles, f'{fam}: no allowed style donor'
        reusable=[x['part'] for x in donor_plan['allowed']
                  if x['part'].get('partKind') in {'MATERIAL_PATTERN','MOTIF','ATTACHMENT','HARDWARE','PALETTE_TONE'}]
        compiled=compile_recipe(contract,styles[0],reusable[:2])
        assert compiled['template']==tid and compiled['geometryPolicy']=='LOCKED_TEMPLATE_ALPHA'

        # Systematic usability means each family has at least one valid recipe
        # in every active rarity tier, not merely a valid default Common.
        vocab=policy['vocabulary']
        axes=list(vocab)
        for rarity in ('common','uncommon','rare','epic'):
            found=False
            for values in itertools.product(*(vocab[a] for a in axes)):
                candidate=dict(zip(axes,values))
                if evaluate_family_recipe(fam,rarity,candidate).valid:
                    found=True
                    break
            assert found, f'{fam}: no valid {rarity} recipe'
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
