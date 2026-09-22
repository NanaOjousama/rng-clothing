#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path('/run/media/deck/USD00/RNG_clothing')
sys.path.insert(0,str(ROOT))
from v5.pngio import read_rgba_png, write_rgba_png, blank_image, blit
SRC=ROOT/'experiments/sfb3_directional_qc'
MOD=ROOT/'mods/EnhancedSewingMachine'
TEX=MOD/'assets/qc/sfb3'
DEF=MOD/'assets/garments/qc/sfb3'
TEX.mkdir(parents=True,exist_ok=True)
DEF.mkdir(parents=True,exist_ok=True)
rarities=['Common','Common','Uncommon','Uncommon','Rare','Rare','Epic','Epic']
entries=[]
for i in range(1,9):
    sid=f'SF{i:02d}'
    sheet=blank_image(24,96)
    for j,view in enumerate(['front','right','back','left']):
        blit(sheet,read_rgba_png(SRC/sid/f'{view}.png'),0,j*24)
    tex_rel=f'assets/qc/sfb3/{sid.lower()}.png'
    write_rgba_png(MOD/tex_rel,sheet)
    gid=f'qc.sfb3.{sid.lower()}'
    directions={
      'Front':{'SourceX':0,'SourceY':0,'AnchorX':12,'AnchorY':20,'OffsetX':0,'OffsetY':0},
      'Right':{'SourceX':0,'SourceY':24,'AnchorX':12,'AnchorY':20,'OffsetX':0,'OffsetY':0},
      'Back':{'SourceX':0,'SourceY':48,'AnchorX':12,'AnchorY':20,'OffsetX':0,'OffsetY':0},
      'Left':{'SourceX':0,'SourceY':72,'AnchorX':12,'AnchorY':20,'OffsetX':0,'OffsetY':0}
    }
    definition={
      'Id':gid,'Category':'Hat','DefinitionVersion':1,
      'WornTexture':tex_rel,'FrameWidth':24,'FrameHeight':24,
      'RenderScale':0.8333333333333334,
      'VanillaReferenceAnchor':{'X':10,'Y':16},
      'Directions':directions,
      'Metadata':{
        'Family':'knit_cap','Construction':'slouch_beanie',
        'Material':'spritefusion_directional','Palette':'source',
        'Motif':'','GeneratorId':'SFB3','GeneratorVersion':1,
        'GeneratorSeed':i,'Style':'source-fidelity,directional,qc',
        'QualityTier':'QC','Decals':'',
        'Classification':'QC_CANDIDATE',
        'Label':f'SFB3 {rarities[i-1]} {sid}'
      }
    }
    rel=f'qc/sfb3/{sid.lower()}.json'
    (MOD/'assets/garments'/rel).write_text(json.dumps(definition,indent=2)+'\n')
    entries.append(rel)

idxp=MOD/'assets/garments/index.json'
idx=json.loads(idxp.read_text())
idx['Garments']=[x for x in idx['Garments'] if not x.startswith('qc/sfb3/')]
idx['Garments'].extend(entries)
idxp.write_text(json.dumps(idx,indent=2)+'\n')
print('registered',len(entries),'SFB3 QC garments')
