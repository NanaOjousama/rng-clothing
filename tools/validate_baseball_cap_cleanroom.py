#!/usr/bin/env python3
from pathlib import Path
import json
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'experiments/cap_reboot/baseball_cap_cleanroom_04'
PACK=ROOT/'test-packs/fashionsense/RNG-Cap-Reboot-Baseball-Cleanroom-04'
ACTIVE=[
    ROOT/'tools/cap_cleanroom_pixel_utils.py',
    ROOT/'tools/build_baseball_cap_cleanroom_v4.py',
    ROOT/'tools/build_baseball_cap_cleanroom_pack.py',
]
FORBIDDEN=(
    'experiments/dad_cap',
    'experiments/dad_cap_v2',
    'experiments/trucker_cap',
    'prototypes/mario_hat',
    'experiments/mario_hat',
)
IDS=('S1_STANDARD_ROUNDED','S2_LOW_ROUNDED')
VIEWS=('front','right','left','back')
def same(a,b):
    return ImageChops.difference(a,b).getbbox() is None

def main():
    for path in ACTIVE:
        source=path.read_text()
        for token in FORBIDDEN:
            assert token not in source, f'forbidden clean-room dependency: {token} in {path}'

    manifest=json.load(open(ART/'manifest.json'))
    assert manifest['cleanroom'] is True
    assert manifest['oldDadArtRead'] is False
    assert manifest['oldTruckerArtRead'] is False
    assert manifest['oldCapExperimentPixelsUsed'] is False
    assert manifest['sourceSpritePixelsUsed'] is False
    assert manifest['userReference'].endswith('.avif')
    assert tuple(x['id'] for x in manifest['candidates'])==IDS
    for cid in IDS:
        frames={}
        for view in VIEWS:
            p=ART/f'{cid.lower()}_{view}.png'
            im=Image.open(p).convert('RGBA')
            assert im.size==(20,20)
            assert set(px[3] for px in im.getdata()) <= {0,255}
            frames[view]=im
        assert same(frames['left'],frames['right'].transpose(Image.Transpose.FLIP_LEFT_RIGHT))

    trace=json.load(open(PACK/'TRACEABILITY.json'))
    assert trace['source']=='baseball_cap_cleanroom_04'
    assert trace['primaryCandidate']=='S1_STANDARD_ROUNDED'
    assert trace['candidates']==list(IDS)
    assert trace['oldDadArtUsed'] is False
    assert trace['oldTruckerArtUsed'] is False
    assert trace['sourceSpritePixelsUsed'] is False
    for cid in IDS:
        sheet=Image.open(PACK/'Hats'/cid/'hat.png').convert('RGBA')
        assert sheet.size==(20,80)
        data=json.load(open(PACK/'Hats'/cid/'hat.json'))
        assert data['FrontHat']['HeadPosition']=={'X':0,'Y':-2}
        assert data['BackHat']['StartingPosition']=={'X':0,'Y':60}

    print('PASS Baseball clean-room v4 has zero old Dad/Trucker/Mario dependencies')
    print('PASS user reference is study-only; no source-sprite pixels used')
    print('PASS S1/S2: 8 frames at 20x20, binary alpha, exact mirrored sides')
    print('PASS isolated Fashion Sense QC pack: 2 candidates x 4 directions')
    print('PASS S1 Standard/Rounded is primary worn-QC candidate')

if __name__=='__main__':
    main()
