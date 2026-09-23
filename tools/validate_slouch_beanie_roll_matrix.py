#!/usr/bin/env python3
import json
from pathlib import Path

PATH=Path('generator/data/headwear/slouch_beanie_roll_matrix.json')
required_axes=['presentationLean','slouchDepth','bandType','drapeDirection','crownShape','openingFit','knitStructure','pattern','trimAccent','microAccent','motif','carrierStyle','decorationStyle','motifPlacement','attachment','hardwareAccent']

def main():
    data=json.loads(PATH.read_text())
    assert data['id']=='slouch_beanie_v1'
    axes=data['axes']
    for name in required_axes:
        assert name in axes, f'missing axis {name}'
        vals=axes[name]
        assert vals and all(isinstance(v,int) and v>0 for v in vals.values()), f'bad weights in {name}'
    assert data['reference']['role']=='CONSTRUCTION_ONLY'
    assert data['reference']['cardinalFrames']=={'front':0,'right':2,'back':4,'left':6}
    assert 'constructionTemplate' not in data
    assert 'constructionProof' not in data
    policy=data.get('renderPolicy',{})
    assert policy.get('status')=='SLOUCH_SPECIFIC_RENDERER_REQUIRED'
    forbidden=set(policy.get('forbidGenericNormalization',[]))
    assert 'BRIMLESS_HAT' in forbidden
    assert any('generic V5' in x for x in forbidden)
    assert data['exclusions'], 'no exclusions defined'

    asset_path=Path(data['assetLibrary'])
    assert asset_path.exists(), f'missing asset library {asset_path}'
    lib=json.loads(asset_path.read_text())
    assets=lib['assets']
    for key,asset in assets.items():
        ap=Path(asset['path']); assert ap.exists(), f'missing asset {key}: {ap}'
    for roll_key,asset_key in data.get('assetBindings',{}).items():
        assert asset_key in assets, f'asset binding {roll_key} -> {asset_key} missing'
    assert {'pom_small','pom_large'}.issubset(assets), 'pom attachments missing'
    assert {'patch_rect','side_label','stitched_badge'}.issubset(assets), 'carrier assets missing'

    # Source-backed material/pattern library must exist and every binding must resolve.
    material_path=Path(data['materialPatternLibrary'])
    assert material_path.exists(), f'missing material library {material_path}'
    materials=json.loads(material_path.read_text())
    profiles=materials['profiles']
    assert materials['family']=='slouch_beanie'
    assert materials['status']=='CANDIDATE_APPROVED'
    assert {'rib_knit','cable_knit','heather_knit','stripe_colorblock','plaid_woven','fleece_wool'}.issubset(profiles)
    for name,binding in data['materialPatternBindings'].items():
        assert name in profiles, f'material binding missing profile {name}'
        assert binding==profiles[name]['rollBindings'], f'material binding drift: {name}'
        for axis,values in binding.items():
            assert axis in axes, f'unknown material axis {axis}'
            for value in values:
                assert value in axes[axis], f'{name}: {axis}.{value} not rollable'
    assert 'fleece_wool' in axes['knitStructure']
    assert 'plaid_woven' in axes['pattern']
    assert {'none','band_trim_line','crown_trim_line','double_trim_lines'}.issubset(axes['trimAccent'])
    assert {'none','cuff_patch_small','side_bow_small','diagonal_wrap_band','tiny_label_tag'}.issubset(axes['microAccent'])
    rr=data['rarityRules']
    assert rr['common']['forced']['motif']=='none'
    assert rr['uncommon']['forced']['motif']=='none'
    assert rr['minimumRarityByFeature']['motif_non_none']=='rare'
    assert rr['minimumRarityByFeature']['carrierStyle_non_none']=='rare'
    assert 'single_stripe' not in rr['common']['allowedPatterns']
    assert 'single_stripe' in rr['uncommon']['minimumPatterns']
    assert 'cable_plus_stripe' in rr['minimumRarityByFeature'] and rr['minimumRarityByFeature']['cable_plus_stripe']=='rare'
    tp=data['tastePolicy']
    assert set(tp['complexityBudgets'])=={'common','uncommon','rare','epic'}
    assert tp['complexityBudgets']['common']['max']==1
    assert tp['complexityBudgets']['epic']['max']==5
    assert set(tp['channels'])=={'SURFACE','PATTERN','REGION','GRAPHIC','ATTACHMENT','HARDWARE'}
    assert tp['roleRules']['rule'].startswith('Exactly zero or one PRIMARY')
    assert any(r['id']=='cable_vs_dense_pattern' for r in tp['strongConflictRules'])
    assert any(r['id']=='carrier_needs_placement' for r in tp['semanticRequirements'])
    vc=data['viewConsistencyPolicy']
    assert set(vc['classes'])=={'WHOLE_HAT','WRAPAROUND_REGION','LOCALIZED'}
    assert vc['axisDefaults']['pattern']=='WHOLE_HAT'
    assert vc['axisDefaults']['trimAccent']=='WRAPAROUND_REGION'
    assert vc['axisDefaults']['motif']=='LOCALIZED'
    assert vc['axisDefaults']['microAccent']=='LOCALIZED'
    assert vc['overrides']['trimAccent.band_trim_line']=='WRAPAROUND_REGION'
    assert vc['overrides']['pattern.contrast_cuff']=='WRAPAROUND_REGION'
    assert vc['overrides']['microAccent.tiny_label_tag']=='LOCALIZED'
    assert vc['overrides']['microAccent.diagonal_wrap_band']=='WRAPAROUND_REGION'
    assert set(vc['classes']['WHOLE_HAT']['requiredViews'])=={'front','right','back','left'}
    assert set(vc['classes']['WRAPAROUND_REGION']['requiredViews'])=={'front','right','back','left'}
    label=data['microAccentPlacementRules']['tiny_label_tag']
    assert label.get('edgeOnly') is True
    assert set(label['allowedPlacements'])=={'cuff_side_left','cuff_side_right','body_side_left','body_side_right'}
    label_rule=next(r for r in data['exclusions'] if r.get('when')=={'microAccent':'tiny_label_tag'})
    assert set(label_rule['allowOnly']['motifPlacement'])==set(label['allowedPlacements'])

    # Hard guard: no-band results may not use cuff-only placements.
    no_band=next(r for r in data['exclusions'] if r.get('when')=={'bandType':'none'})
    cuff_places={'cuff_front_center','cuff_front_offset_left','cuff_front_offset_right','cuff_side_left','cuff_side_right','cuff_back_center'}
    assert cuff_places.issubset(set(no_band['disallow']['motifPlacement']))

    # New complexity exclusions must remain explicit.
    plaid=next(r for r in data['exclusions'] if r.get('when')=={'pattern':'plaid_woven'})
    assert 'cable' in plaid['disallow']['knitStructure']
    cable_rules=[r for r in data['exclusions'] if r.get('when')=={'knitStructure':'cable'}]
    assert any('plaid_woven' in r.get('disallow',{}).get('pattern',[]) for r in cable_rules)
    fleece=next(r for r in data['exclusions'] if r.get('when')=={'knitStructure':'fleece_wool'})
    assert 'cable_plus_stripe' in fleece['disallow']['pattern']

    # AI-assisted production path is fail-closed and must remain wired.
    pipeline=Path(data['aiAssistedVisualPipeline'])
    assert pipeline.exists(), f'missing AI-assisted visual pipeline {pipeline}'
    promotion=data['productionPromotionPolicy']
    assert promotion['requiredStatus']=='PRODUCTION_APPROVED'
    assert promotion['candidateMechanicalQC'] is True
    assert promotion['directionMechanicalQC'] is True
    assert promotion['humanArtApproval'] is True
    assert promotion['esmWearApproval'] is True
    assert 'procedural redraw' in data['renderPolicy']['sfAssistedRule']

    # Presentation is a soft preference only, never a gender lock.
    assert all(v.get('avoidHardLocks') is True for v in data['presentationModifiers'].values())
    print('PASS slouch beanie roll matrix')
    print(f"axes={len(required_axes)} exclusions={len(data['exclusions'])} material_profiles={len(profiles)}")

if __name__=='__main__':
    main()
