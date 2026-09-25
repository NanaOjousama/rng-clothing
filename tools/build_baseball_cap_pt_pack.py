#!/usr/bin/env python3
from pathlib import Path
import json,shutil
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'experiments/cap_reboot/baseball_cap_pt_04'
PACK=ROOT/'test-packs/fashionsense/RNG-Cap-Reboot-Baseball-PT-04'
GAME=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley')
INSTALL=GAME/'Mods/[FS] RNG Cap Reboot Baseball PT 04'
OLD_INSTALLS=[
    GAME/'Mods/[FS] RNG Cap Reboot Baseball Cleanroom 04',
    GAME/'Mods/[FS] RNG Cap Reboot Baseball PT 03',
]
IDS=['PT5_PRIMARY_BALANCED','PT6_PRIMARY_COMPACT']
NAMES={
    'PT5_PRIMARY_BALANCED':'Baseball PT5 Balanced',
    'PT6_PRIMARY_COMPACT':'Baseball PT6 Compact',
}
def hat_json(name):
    out={'Name':name,'Tags':['RNG Clothing','CAP_REBOOT','BASEBALL','PHOTO_TAILOR','PT04']}
    for key,y in [('FrontHat',0),('RightHat',20),('LeftHat',40),('BackHat',60)]:
        out[key]={
            'DisableGrayscale':True,
            'HideHair':False,
            'HatSize':{'Width':20,'Length':20},
            'StartingPosition':{'X':0,'Y':y},
            'HeadPosition':{'X':0,'Y':-2},
        }
    return out

def main():
    if PACK.exists():
        shutil.rmtree(PACK)
    PACK.mkdir(parents=True)
    manifest={
        'Name':'RNG Cap Reboot Baseball PT 04',
        'Author':'RNG Clothing PT Prototype',
        'Version':'1.0.0',
        'Description':'PT-assisted Baseball candidates from new cap reference folder.',
        'UniqueID':'RNGClothing.FashionSense.CapRebootBaseballPT04',
        'UpdateKeys':[],
        'ContentPackFor':{'UniqueID':'PeacefulEnd.FashionSense','MinimumVersion':'7.5.0'},
    }
    (PACK/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    for cid in IDS:
        folder=PACK/'Hats'/cid
        folder.mkdir(parents=True)
        sheet=Image.new('RGBA',(20,80),(0,0,0,0))
        for i,v in enumerate(('front','right','left','back')):
            im=Image.open(SRC/cid/f'{v}.png').convert('RGBA')
            sheet.alpha_composite(im,(0,i*20))
        sheet.save(folder/'hat.png')
        (folder/'hat.json').write_text(json.dumps(hat_json(NAMES[cid]),indent=2)+'\n')

    trace={
        'schema':'cap-reboot-baseball-pt-pack/v2',
        'source':'baseball_cap_pt_04',
        'authoritativeReferenceFolder':'cap reference',
        'primaryCandidate':'PT5_PRIMARY_BALANCED',
        'candidates':IDS,
        'photoTailorUsed':True,
        'oldDadArtUsed':False,
        'oldTruckerArtUsed':False,
        'marioArtUsed':False,
        'oldVectorReferenceActive':False,
        'trueBackReferenceUsed':True,
        'backHasBrimSemantic':False,
        'rightReferenceAlreadyPointsRight':True,
        'HeadPosition':{'X':0,'Y':-2},
        'status':'CANDIDATE_WORN_QC',
    }
    (PACK/'TRACEABILITY.json').write_text(json.dumps(trace,indent=2)+'\n')
    for old in OLD_INSTALLS:
        if old.exists():
            shutil.rmtree(old)
    if INSTALL.exists():
        shutil.rmtree(INSTALL)
    shutil.copytree(PACK,INSTALL)
    print('built',PACK)
    print('installed',INSTALL)
    print('removed obsolete Baseball test packs if present')

if __name__=='__main__':
    main()
