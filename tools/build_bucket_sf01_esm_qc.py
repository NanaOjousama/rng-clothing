#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from v5.pngio import blank_image, blit, read_rgba_png, write_rgba_png
BASE=ROOT/'authored/templates/bucket_sf01_rd8'; MOD=ROOT/'mods/EnhancedSewingMachine'
TEX=MOD/'assets/qc/bucket_sf01_rd8'; DEF=MOD/'assets/garments/qc/bucket_sf01_rd8'; IDX=MOD/'assets/garments/index.json'
TEX.mkdir(parents=True,exist_ok=True); DEF.mkdir(parents=True,exist_ok=True)
order=['front','right','back','left']; fs=24; sheet=blank_image(fs,fs*4)
for i,v in enumerate(order): blit(sheet,read_rgba_png(BASE/f'{v}.png'),0,i*fs)
write_rgba_png(TEX/'base.png',sheet)
dirs={v.title():{'SourceX':0,'SourceY':i*fs,'AnchorX':12,'AnchorY':17,'OffsetX':0,'OffsetY':-2} for i,v in enumerate(order)}
d={'Id':'qc.bucket.sf01.rd8.base','Category':'Hat','DefinitionVersion':1,'WornTexture':'assets/qc/bucket_sf01_rd8/base.png','FrameWidth':24,'FrameHeight':24,'RenderScale':0.8333333333333334,'VanillaReferenceAnchor':{'X':10,'Y':16},'HairMode':'Obscured','Directions':dirs,'Metadata':{'Family':'bucket_hat','Construction':'bucket_sf01_rd8','Material':'source_backed','Palette':'cream_tan','Motif':'','GeneratorId':'BucketSF01RD8','GeneratorVersion':1,'GeneratorSeed':1,'Style':'approved-construction,wear-qc','QualityTier':'QC','Decals':'','Classification':'QC_CANDIDATE','Label':'BUCKET HAT 01 RD8'}}
rel='qc/bucket_sf01_rd8/base.json'; (MOD/'assets/garments'/rel).write_text(json.dumps(d,indent=2)+'\n')
idx=json.loads(IDX.read_text()); idx['Garments']=[x for x in idx['Garments'] if not str(x).startswith('qc/bucket_sf01_rd8/')]+[rel]; IDX.write_text(json.dumps(idx,indent=2)+'\n')
print('registered',rel)
