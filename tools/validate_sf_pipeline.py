#!/usr/bin/env python3
from pathlib import Path
import json, sys

ROOT=Path('/run/media/deck/USD00/RNG_clothing')
sys.path.insert(0,str(ROOT))

from sf_pipeline.model import CandidateOutput, DirectionAsset, DirectionMethod, DirectionSetManifest, PromotionStatus
from sf_pipeline.qc import candidate_qc, direction_qc, promotion_allowed

POLICY=ROOT/'sf_pipeline/policy.json'
WORKFLOW=ROOT/'docs/SPRITE_FUSION_WORKFLOW.md'
LEGACY=ROOT/'sf_pipeline/deprecated_visual_paths.json'
SMOKE=ROOT/'experiments/sf_pipeline_smoke_01'


def main():
    assert POLICY.exists()
    assert WORKFLOW.exists()
    assert LEGACY.exists()
    policy=json.loads(POLICY.read_text())
    assert policy['requestedSize']==16
    assert policy['maximumCandidateDimension']==32
    assert policy['pixelSnapperNativeSpriteFusionDefault'] is False
    assert policy['headwearDirectionalPolicy']['productionMethod']=='edit-cardinal'
    assert policy['headwearDirectionalPolicy']['legacyDirectionSet'].startswith('research/evidence only')
    candidate=json.loads((SMOKE/'candidate_manifest.json').read_text())
    out=candidate['output']
    candidate_obj=CandidateOutput(
        index=out['index'],
        asset_id=out['asset_id'],
        local_path=str(ROOT/out['local_path']),
        width=out['width'],
        height=out['height'],
        request_id=candidate.get('requestId',''),
    )
    candidate_report=candidate_qc(candidate_obj)
    assert candidate_report['passMechanical'] is True
    assert candidate_report['semanticHumanReviewRequired'] is True

    raw=json.loads((SMOKE/'direction_manifest.json').read_text())
    directions={}
    for name,item in raw['directions'].items():
        directions[name]=DirectionAsset(
            direction=name,
            asset_id=item['asset_id'],
            local_path=str(ROOT/item['path']),
            width=item['width'],
            height=item['height'],
        )
    manifest=DirectionSetManifest(
        id=raw['id'],
        source_candidate_id=raw['sourceCandidateId'],
        source_asset_id=raw['sourceAssetId'],
        requested_size=raw['requestedSize'],
        directions=directions,
        consistency_classes=raw.get('consistencyClasses',{}),
    )
    direction_report=direction_qc(manifest)
    assert direction_report['passMechanical'] is True
    assert direction_report['semanticHumanReviewRequired'] is True

    proof=ROOT/'experiments/sfp1_edit_direction_test_v2'
    edit_assets={
        'front': DirectionAsset('front','front',str(ROOT/'experiments/sfp1_proof/whole_hat/output_04.png'),22,22),
        'right': DirectionAsset('right','right',str(proof/'right_edit/output_00.png'),21,21),
        'back': DirectionAsset('back','back',str(proof/'back_edit/output_00.png'),21,21),
        'left': DirectionAsset('left','mirror:right',str(proof/'left_mirror.png'),21,21),
    }
    edit_manifest=DirectionSetManifest(
        id='edit-cardinal-proof', source_candidate_id='sfp1.wholehat',
        source_asset_id='front', requested_size=16, directions=edit_assets,
        method=DirectionMethod.EDIT_CARDINAL, garment_category='hat',
    )
    edit_report=direction_qc(edit_manifest)
    assert edit_report['passMechanical'] is True
    assert edit_report['method']=='edit-cardinal'

    assert not promotion_allowed(
        PromotionStatus.PRODUCTION_APPROVED,
        candidate_ok=True,
        direction_ok=True,
        human_art_approved=False,
        esm_wear_approved=False,
    )
    assert promotion_allowed(
        PromotionStatus.PRODUCTION_APPROVED,
        candidate_ok=True,
        direction_ok=True,
        human_art_approved=True,
        esm_wear_approved=True,
    )
    print('PASS SF pipeline policy')
    print('PASS candidate mechanical gate')
    print('PASS legacy 8-direction evidence gate')
    print('PASS headwear edit-cardinal production gate')
    print('PASS production fail-closed gate')


if __name__=='__main__':
    main()
