#!/usr/bin/env python3
from pathlib import Path
import json
from PIL import Image,ImageChops

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'experiments/cap_reboot/baseball_cap_pt_04'
PACK=ROOT/'test-packs/fashionsense/RNG-Cap-Reboot-Baseball-PT-04'
PROTO=ROOT/'prototypes/photo_tailor_baseball_reboot/run_pt_baseball_v4.py'
FORBIDDEN=(
    'experiments/dad_cap',
    'experiments/dad_cap_v2',
    'experiments/trucker_cap',
    'prototypes/mario_hat',
    'experiments/mario_hat',
)
IDS=('PT5_PRIMARY_BALANCED','PT6_PRIMARY_COMPACT')
VIEWS=('front','right','left','back')

def same(a,b):
    return ImageChops.difference(a,b).getbbox() is None
def main():
    source=PROTO.read_text()
    for token in FORBIDDEN:
        assert token not in source, f'forbidden cap dependency: {token}'

    manifest=json.load(open(ART/'manifest.json'))
    assert manifest['prototype']=='PT_BASEBALL_04'
    assert manifest['authoritativeReferenceFolder']=='cap reference'
    assert manifest['cleanroom']['oldDadV1Read'] is False
    assert manifest['cleanroom']['oldDadV2Read'] is False
    assert manifest['cleanroom']['oldTruckerRead'] is False
    assert manifest['cleanroom']['oldCapControlUsed'] is False
    assert manifest['cleanroom']['marioArtUsed'] is False
    assert manifest['cleanroom']['oldVectorReferenceActive'] is False
    for k,v in manifest['photoTailorSemantics'].items():
        assert v['topCategory']=='hat', (k,v)
        assert v['topSilhouette']=='cap', (k,v)
    assert manifest['projection']['trueBackHasNoBrimSemantic'] is True
    assert manifest['projection']['rightReferenceAlreadyPointsRight'] is True
    assert manifest['projection']['leftExactMirrorOfRight'] is True
    assert manifest['projection']['referenceLogosMotifsIgnored'] is True

    for cid in IDS:
        frames={}
        for view in VIEWS:
            im=Image.open(ART/cid/f'{view}.png').convert('RGBA')
            assert im.size==(20,20)
            assert set(px[3] for px in im.getdata()) <= {0,255}
            frames[view]=im
        assert same(frames['left'],frames['right'].transpose(Image.Transpose.FLIP_LEFT_RIGHT))
        # Back opening must remain transparent inside the occupied bbox.
        b=frames['back'].getbbox()
        x0,y0,x1,y1=b
        internal=[frames['back'].getpixel((x,y))[3]==0
                  for y in range(y0+2,y1-1) for x in range(x0+2,x1-2)]
        assert any(internal), f'{cid}: back opening disappeared'
    trace=json.load(open(PACK/'TRACEABILITY.json'))
    assert trace['source']=='baseball_cap_pt_04'
    assert trace['primaryCandidate']=='PT5_PRIMARY_BALANCED'
    assert trace['photoTailorUsed'] is True
    assert trace['authoritativeReferenceFolder']=='cap reference'
    assert trace['oldDadArtUsed'] is False
    assert trace['oldTruckerArtUsed'] is False
    assert trace['marioArtUsed'] is False
    assert trace['oldVectorReferenceActive'] is False
    assert trace['trueBackReferenceUsed'] is True
    assert trace['backHasBrimSemantic'] is False

    for cid in IDS:
        sheet=Image.open(PACK/'Hats'/cid/'hat.png').convert('RGBA')
        assert sheet.size==(20,80)
        data=json.load(open(PACK/'Hats'/cid/'hat.json'))
        assert data['FrontHat']['HeadPosition']=={'X':0,'Y':-2}
        assert data['BackHat']['StartingPosition']=={'X':0,'Y':60}
    print('PASS PT04 uses cap reference folder as authoritative Baseball source')
    print('PASS Photo Tailor semantics identify front/right/back/overview as hat -> cap')
    print('PASS no old Dad/Trucker/Mario or old cap-control dependency')
    print('PASS true BackHat has preserved opening and no brim semantic')
    print('PASS PT5/PT6 are 20x20, binary alpha, exact mirrored left/right')
    print('PASS isolated Fashion Sense PT04 pack is ready for worn QC')

if __name__=='__main__':
    main()
