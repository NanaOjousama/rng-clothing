#!/usr/bin/env python3
import json, shutil, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from v5.pngio import read_rgba_png, write_rgba_png, blank_image, blit

SRC=ROOT/'experiments/source_template_rarity_batch_01'
PACK=ROOT/'test-packs/fashionsense/RNG-SLB3-Rarity-QC'
LIVE=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods/RNG-SLB3-Rarity-QC')
VIEWS=['front','right','left','back']
FS_KEYS={'front':'FrontHat','right':'RightHat','left':'LeftHat','back':'BackHat'}
LABELS={
'C1_COCOA_SOLID':'C1 Cocoa Solid',
'C2_STONE_FINE_RIB':'C2 Stone Fine Rib',
'U1_SAGE_SEED_LEAF':'U1 Sage Seed Leaf',
'U2_INDIGO_TWIN_STAR':'U2 Indigo Twin Star',
'R1_AUTUMN_JACQUARD_FLOWER':'R1 Autumn Jacquard Flower',
'R2_WINE_CABLE_BADGE':'R2 Wine Cable Badge',
'E1_ARCANE_CABLE_STRIPE_BOTANICAL':'E1 Arcane Cable Stripe Botanical',
'E2_JADE_JACQUARD_BOTANICAL':'E2 Jade Jacquard Botanical',
}

man=json.loads((SRC/'batch_manifest.json').read_text())
if PACK.exists():
    shutil.rmtree(PACK)
PACK.mkdir(parents=True)
(PACK/'manifest.json').write_text(json.dumps({
    'Name':'SLB3 Rarity QC',
    'Author':'RNG Clothing',
    'Version':'0.1.0',
    'Description':'SLB3 controlled slouch beanie rarity QC: Common through Epic.',
    'UniqueID':'RNGClothing.FashionSense.SLB3RarityQC',
    'UpdateKeys':[],
    'ContentPackFor':{'UniqueID':'PeacefulEnd.FashionSense','MinimumVersion':'7.5.0'}
},indent=2)+'\n')

for v in man['variants']:
    vid=v['id']
    folder=PACK/'Hats'/vid
    folder.mkdir(parents=True)
    sheet=blank_image(24,96)
    for i,view in enumerate(VIEWS):
        frame=read_rgba_png(Path(v['frames'][view]))
        blit(sheet,frame,0,i*24)
    write_rgba_png(folder/'hat.png',sheet)

    name=f"SLB3 {LABELS[vid]}"
    tags=['SLB3','RNG Clothing','slouch beanie','rarity qc',v['rarity'],vid]
    directions={}
    # Start with the proven slouch head-position family convention.
    head_x={'front':-2,'right':-1,'left':-3,'back':-2}
    for i,view in enumerate(VIEWS):
        directions[FS_KEYS[view]]={
            'DisableGrayscale':True,
            'HideHair':False,
            'StartingPosition':{'X':0,'Y':i*24},
            'HeadPosition':{'X':head_x[view],'Y':-3},
            'HatSize':{'Width':24,'Length':24}
        }
    data={'Name':name,'Tags':tags,**directions}
    (folder/'hat.json').write_text(json.dumps(data,indent=2)+'\n')

(PACK/'TRACEABILITY.json').write_text(json.dumps({
    'tag':'SLB3',
    'sourceBatch':'experiments/source_template_rarity_batch_01',
    'template':'slouch_pl24',
    'count':len(man['variants']),
    'rarities':{'Common':2,'Uncommon':2,'Rare':2,'Epic':2},
    'qcNote':'Search Fashion Sense for SLB3. All art preserves locked PL24 alpha. Head positions are initial QC fit based on prior slouch family convention.'
},indent=2)+'\n')

if LIVE.exists():
    shutil.rmtree(LIVE)
shutil.copytree(PACK,LIVE)
print('PACK',PACK)
print('LIVE',LIVE)
print('HATS',len(list((LIVE/'Hats').glob('*/hat.json'))))
