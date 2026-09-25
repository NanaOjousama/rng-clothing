#!/usr/bin/env python3
from pathlib import Path
import json,shutil
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'experiments/cap_reboot/baseball_cap_cleanroom_04'
PACK=ROOT/'test-packs/fashionsense/RNG-Cap-Reboot-Baseball-Cleanroom-04'
GAME=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley')
INSTALL=GAME/'Mods/[FS] RNG Cap Reboot Baseball Cleanroom 04'
OLD_INSTALLS=[
 GAME/'Mods/[FS] RNG Cap Reboot Baseball Cleanroom 02',
 GAME/'Mods/[FS] RNG Cap Reboot Baseball Cleanroom 03',
]
IDS=['S1_STANDARD_ROUNDED','S2_LOW_ROUNDED']
NAMES={
 'S1_STANDARD_ROUNDED':'Baseball Cleanroom S1 Standard',
 'S2_LOW_ROUNDED':'Baseball Cleanroom S2 Lower',
}

def hat_json(name):
    out={'Name':name,'Tags':['RNG Clothing','CAP_REBOOT','BASEBALL','CLEANROOM_04']}
    for key,y in [('FrontHat',0),('RightHat',20),('LeftHat',40),('BackHat',60)]:
        out[key]={
          'DisableGrayscale':True,'HideHair':False,
          'HatSize':{'Width':20,'Length':20},
          'StartingPosition':{'X':0,'Y':y},
          'HeadPosition':{'X':0,'Y':-2}
        }
    return out

def main():
    if PACK.exists(): shutil.rmtree(PACK)
    PACK.mkdir(parents=True)
    manifest={
      'Name':'RNG Cap Reboot Baseball Cleanroom 04',
      'Author':'RNG Clothing Cleanroom','Version':'1.0.0',
      'Description':'Fresh reference-guided Baseball Cap candidates. Old Dad/Trucker art quarantined.',
      'UniqueID':'RNGClothing.FashionSense.CapRebootBaseballCleanroom04',
      'UpdateKeys':[],
      'ContentPackFor':{'UniqueID':'PeacefulEnd.FashionSense','MinimumVersion':'7.5.0'}
    }
    (PACK/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    for cid in IDS:
        folder=PACK/'Hats'/cid; folder.mkdir(parents=True)
        sheet=Image.new('RGBA',(20,80),(0,0,0,0))
        for i,v in enumerate(('front','right','left','back')):
            im=Image.open(SRC/f'{cid.lower()}_{v}.png').convert('RGBA')
            sheet.alpha_composite(im,(0,i*20))
        sheet.save(folder/'hat.png')
        (folder/'hat.json').write_text(json.dumps(hat_json(NAMES[cid]),indent=2)+'\n')
    trace={
      'schema':'cap-reboot-cleanroom-pack/v2',
      'source':'baseball_cap_cleanroom_04',
      'userReference':'baseball-cap-vector-template-set-uniform-fashion-blank-hat-design-sport-clothing_1284-44135.avif',
      'oldDadArtUsed':False,'oldTruckerArtUsed':False,'sourceSpritePixelsUsed':False,
      'candidates':IDS,'primaryCandidate':'S1_STANDARD_ROUNDED',
      'HeadPosition':{'X':0,'Y':-2},'status':'CANDIDATE_WORN_QC'
    }
    (PACK/'TRACEABILITY.json').write_text(json.dumps(trace,indent=2)+'\n')
    for old in OLD_INSTALLS:
        if old.exists(): shutil.rmtree(old)
    if INSTALL.exists(): shutil.rmtree(INSTALL)
    shutil.copytree(PACK,INSTALL)
    print('built',PACK)
    print('installed',INSTALL)
    print('removed obsolete installed clean-room packs if present')

if __name__=='__main__': main()
