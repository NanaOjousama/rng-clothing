#!/usr/bin/env python3
from pathlib import Path
import json, shutil, sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
SRC=ROOT/'experiments/beanie_template_compare_16'
PACK=ROOT/'test-packs/fashionsense/RNG-B16QC'
LIVE=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods/RNG-B16QC')
VIEWS=['front','right','left','back']
FSKEY={'front':'FrontHat','right':'RightHat','left':'LeftHat','back':'BackHat'}
SETS=[('PL16','B16PL',SRC/'pl16'),('RT16','B16RT',SRC/'roundtrip16')]

def main():
    if PACK.exists(): shutil.rmtree(PACK)
    (PACK/'Hats').mkdir(parents=True)
    manifest={
      'Name':'B16QC - 16px Beanie Template Compare',
      'Author':'RNG Clothing','Version':'0.1.0',
      'Description':'In-game QC: matched 16px PixelLab vs round-trip source beanie batches.',
      'UniqueID':'RNGClothing.FashionSense.B16QC',
      'UpdateKeys':[],
      'ContentPackFor':{'UniqueID':'PeacefulEnd.FashionSense','MinimumVersion':'7.5.0'}
    }
    (PACK/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

    trace=[]
    for label,subtag,src in SETS:
      m=json.loads((src/'manifest.json').read_text())
      for v in m['variants']:
        vid=v['id']
        folder=PACK/'Hats'/f'{subtag}_{vid}'
        folder.mkdir(parents=True)
        # Compose 16x64 sheet from explicit directional frames.
        from v5.pngio import read_rgba_png, blank_image, blit, write_rgba_png
        sheet=blank_image(16,64)
        for i,view in enumerate(VIEWS):
          fr=read_rgba_png(src/vid/f'{view}.png')
          blit(sheet,fr,0,i*16)
        write_rgba_png(folder/'hat.png',sheet)

        name=f'B16QC {label} {vid}'
        doc={'Name':name,'Format':'7.5.0',
             'Tags':['B16QC',subtag,label,'16px','RNG Clothing',v['rarity'],vid]}
        for i,view in enumerate(VIEWS):
          block={
            'DisableGrayscale':True,
            'HideHair':False,
            'StartingPosition':{'X':0,'Y':i*16},
            'HeadPosition':{'X':-2,'Y':-3},
            'HatSize':{'Width':16,'Length':16},
            'UniformAnimation':[{'Frame':0,'Duration':5000}],
          }
          if view in ('front','right','left'):
            block['DrawOrderOverride']={'Preposition':'Before','AppearanceType':'Sleeves'}
          doc[FSKEY[view]]=block
        (folder/'hat.json').write_text(json.dumps(doc,indent=2)+'\n')
        trace.append({'template':label,'tag':subtag,'id':vid,'rarity':v['rarity'],
                      'size':[16,16],'headPosition':[-2,-3]})

    (PACK/'TRACEABILITY.json').write_text(json.dumps({
      'tag':'B16QC','subtags':['B16PL','B16RT'],
      'comparison':'same 8 variants on PL16 and RoundTrip16',
      'wearContract':{'HatSize':[16,16],'HeadPosition':[-2,-3],
                      'note':'shared round-trip source beanie anchor for apples-to-apples QC'},
      'entries':trace
    },indent=2)+'\n')

    if LIVE.exists(): shutil.rmtree(LIVE)
    shutil.copytree(PACK,LIVE)
    print('PASS built',len(trace),'hats')
    print('PASS PL16',sum(x['template']=='PL16' for x in trace))
    print('PASS RT16',sum(x['template']=='RT16' for x in trace))
    print('LIVE',LIVE)

if __name__=='__main__':
    main()
