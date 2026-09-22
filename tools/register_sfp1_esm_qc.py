#!/usr/bin/env python3
from pathlib import Path
import json, sys

ROOT=Path('/run/media/deck/USD00/RNG_clothing')
sys.path.insert(0,str(ROOT))
from v5.pngio import read_rgba_png, write_rgba_png, blank_image, blit

PROOF=ROOT/'experiments/sfp1_proof'
MOD=ROOT/'mods/EnhancedSewingMachine'
TEX=MOD/'assets/qc/sfp1'
DEF=MOD/'assets/garments/qc/sfp1'
TEX.mkdir(parents=True,exist_ok=True)
DEF.mkdir(parents=True,exist_ok=True)

CONFIG={
 'wholehat':('WHOLE_HAT','wholehat_directions'),
 'wraparound':('WRAPAROUND_REGION','wraparound_directions'),
 'localized':('LOCALIZED','localized_directions'),
}
MAP={'Front':'S','Right':'E','Back':'N','Left':'W'}

def alpha_bbox_width(img):
    xs=[x for row in img for x,p in enumerate(row) if p[3]]
    return (max(xs)-min(xs)+1) if xs else 0

def pad24(img):
    h=len(img); w=len(img[0])
    if w>24 or h>24:
        raise ValueError(f'frame too large for SFP1 ESM QC: {w}x{h}')
    out=blank_image(24,24)
    x=(24-w)//2
    y=24-h
    blit(out,img,x,y)
    return out

entries=[]
for name,(consistency,folder) in CONFIG.items():
    outs=json.loads((PROOF/folder/'outputs.json').read_text())
    by={o['direction']:o for o in outs}
    frames={}
    widths=[]
    native_widths=[]
    for view,direction in MAP.items():
        img=read_rgba_png(ROOT/by[direction]['local_path'])
        frames[view]=pad24(img)
        widths.append(alpha_bbox_width(img))
        native_widths.append(len(img[0]))

    max_width=max(widths)
    max_native_width=max(native_widths)
    render_scale=20.0/max_native_width
    sheet=blank_image(24,96)
    for i,view in enumerate(['Front','Right','Back','Left']):
        blit(sheet,frames[view],0,i*24)

    tex_rel=f'assets/qc/sfp1/{name}.png'
    write_rgba_png(MOD/tex_rel,sheet)
    directions={
      'Front':{'SourceX':0,'SourceY':0,'AnchorX':12,'AnchorY':20,'OffsetX':0,'OffsetY':0},
      'Right':{'SourceX':0,'SourceY':24,'AnchorX':12,'AnchorY':20,'OffsetX':0,'OffsetY':0},
      'Back':{'SourceX':0,'SourceY':48,'AnchorX':12,'AnchorY':20,'OffsetX':0,'OffsetY':0},
      'Left':{'SourceX':0,'SourceY':72,'AnchorX':12,'AnchorY':20,'OffsetX':0,'OffsetY':0},
    }

    gid=f'qc.sfp1.{name}'
    definition={
      'Id':gid,'Category':'Hat','DefinitionVersion':1,
      'WornTexture':tex_rel,'FrameWidth':24,'FrameHeight':24,
      'RenderScale':render_scale,
      'VanillaReferenceAnchor':{'X':10,'Y':16},
      'Directions':directions,
      'Metadata':{
        'Family':'knit_cap','Construction':'slouch_beanie',
        'Material':'spritefusion_proof','Palette':'source',
        'Motif':'','GeneratorId':'SFP1','GeneratorVersion':1,
        'GeneratorSeed':1,'Style':'sf-pipeline-v2,qc',
        'QualityTier':'QC','Decals':'',
        'Classification':'QC_CANDIDATE',
        'Label':f'SFP1 {name.upper()}',
        'ConsistencyClass':consistency,
      }
    }

    rel=f'qc/sfp1/{name}.json'
    (MOD/'assets/garments'/rel).write_text(json.dumps(definition,indent=2)+'\n')
    entries.append(rel)
    print(name,'maxOpaqueWidth',max_width,'maxNativeWidth',max_native_width,'RenderScale',render_scale)

idxp=MOD/'assets/garments/index.json'
idx=json.loads(idxp.read_text())
idx['Garments']=[x for x in idx['Garments'] if not x.startswith('qc/sfp1/')]
idx['Garments'].extend(entries)
idxp.write_text(json.dumps(idx,indent=2)+'\n')
print('registered',len(entries),'SFP1 QC garments')
