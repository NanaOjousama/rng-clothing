#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from v5.pngio import blank_image, blit, read_rgba_png, write_rgba_png
BASE=ROOT/'authored/templates/bucket_maroon_rd8'
ATT=BASE/'attachments/chin_strap'
MOD=ROOT/'mods/EnhancedSewingMachine'
TEXDIR=MOD/'assets/qc/bucket_maroon_rd8'; DEFDIR=MOD/'assets/garments/qc/bucket_maroon_rd8'; INDEX=MOD/'assets/garments/index.json'
ORDER=['front','right','back','left']; FS=24; RS=0.8333333333333334
TEXDIR.mkdir(parents=True,exist_ok=True); DEFDIR.mkdir(parents=True,exist_ok=True)

def compose(view,strap):
    base=read_rgba_png(BASE/f'{view}.png')
    if not strap: return base
    out=[row[:] for row in base]
    ov=read_rgba_png(ATT/f'{view}.png')
    for y in range(FS):
        for x in range(FS):
            if ov[y][x][3]: out[y][x]=ov[y][x]
    return out

def make(slug,strap,label):
    sheet=blank_image(FS,FS*4)
    for i,v in enumerate(ORDER): blit(sheet,compose(v,strap),0,i*FS)
    texrel=f'assets/qc/bucket_maroon_rd8/{slug}.png'; write_rgba_png(MOD/texrel,sheet)
    dirs={}
    for i,v in enumerate(ORDER):
        dirs[v.title()]={'SourceX':0,'SourceY':i*FS,'AnchorX':12,'AnchorY':17,'OffsetX':0,'OffsetY':-2}
    d={'Id':f'qc.bucket.maroon.rd8.{slug}','Category':'Hat','DefinitionVersion':1,'WornTexture':texrel,'FrameWidth':FS,'FrameHeight':FS,'RenderScale':RS,'VanillaReferenceAnchor':{'X':10,'Y':16},'Directions':dirs,'Metadata':{'Family':'bucket_hat','Construction':'bucket_maroon_rd8','Material':'source_backed','Palette':'maroon','Motif':'','GeneratorId':'BucketMaroonRD8','GeneratorVersion':1,'GeneratorSeed':1 if strap else 0,'Style':'approved-construction,wear-qc','QualityTier':'QC','Decals':'chin_strap' if strap else '','Classification':'QC_CANDIDATE','Label':label}}
    rel=f'qc/bucket_maroon_rd8/{slug}.json'; (MOD/'assets/garments'/rel).write_text(json.dumps(d,indent=2)+'\n'); return rel
entries=[make('base_off',False,'BUCKET MAROON RD8 - STRAP OFF'),make('strap_on',True,'BUCKET MAROON RD8 - STRAP ON')]
idx=json.loads(INDEX.read_text()); idx['Garments']=[x for x in idx['Garments'] if not str(x).startswith('qc/bucket_maroon_rd8/')]+entries; INDEX.write_text(json.dumps(idx,indent=2)+'\n')
print('registered',entries)
