#!/usr/bin/env python3
"""Source-faithful Full-vs-Obscured hat test using ESM's existing hair modes.

No FS models or source sprites are edited. Outputs definitions and sprite paths
for a local ESM QC folder only; no dependency, patch or runtime code changes.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import hashlib
import shutil

SAMPLES={"01": "propeller_cap", "05": "messy_straw", "10": "blue_straw"}

def build(source: Path, installed: Path):
    art_dst = installed / 'assets/qc/hair_policy_ab'
    def_dst = installed / 'assets/garments/qc/hair_policy_ab'
    if not (source / 'manifest.json').is_file():
        raise RuntimeError(f'Cannot find source FS pack at {source}')
    for d in (art_dst,def_dst):
        d.mkdir(parents=True, exist_ok=True)
    records=[]
    for i,short in SAMPLES.items():
        matches=list(source.glob(f'Hats/PSQC2 {i} */hat.json'))
        if len(matches)!=1:
            raise RuntimeError(f'Expected 1 QC2 {i} hat; found {len(matches)}')
        j=matches[0]; model=json.loads(j.read_text())
        src=j.with_suffix('.png'); art=art_dst/f'psqc2_{i}.png'
        if art.exists() and art.read_bytes()!=src.read_bytes():
            raise RuntimeError(f'Refusing to overwrite different sprite: {art}')
        shutil.copy2(src,art)
        assert src.read_bytes()==art.read_bytes()
        fw=model['FrontHat']['HatSize']['Width']; fh=model['FrontHat']['HatSize']['Length']
        dirs={}
        for name in ('Front','Right','Back','Left'):
            view=model[name+'Hat']; start=view['StartingPosition']; size=view['HatSize']; shift=view.get('HeadPosition',{'X':0,'Y':0})
            assert size['Width']==fw and size['Length']==fh
            # ESM reference pivot and model frame center: this base placement is
            # shared identically across both policies. Hair comparisons valid
            # even if FS & ESM engines have different placement conventions.
            dirs[name]={
                'SourceX':start['X'],'SourceY':start['Y'],
                'AnchorX':fw//2,'AnchorY':16,
                'OffsetX': -int(shift['X']), 'OffsetY': -int(shift['Y']),
                'FlipX':bool(view.get('Flipped',False)),
            }
        for mode in ('Full','Obscured'):
            id=f'qc.hairpolicy.psqc2.{i}.{mode.lower()}'
            definition={
                'Id':id,'Category':'Hat','DefinitionVersion':1,
                'WornTexture':f'assets/qc/hair_policy_ab/psqc2_{i}.png',
                'FrameWidth':fw,'FrameHeight':fh,'RenderScale':1.0,
                'VanillaReferenceAnchor':{'X':10,'Y':16},
                'HairMode':mode,'Directions':dirs,
                'Metadata':{'Family':'hair_policy_qc','Construction':short,'Material':'source_backed',
                            'Palette':'original','Motif':'', 'GeneratorId':'PackStudyHairPolicyQC',
                            'GeneratorVersion':1,'GeneratorSeed':0,'Style':'hair-policy-a-b',
                            'QualityTier':'QC','Decals':'','Classification':'QC_ONLY',
                            'Label':f'HPQC {i} {short} {mode}'}}
            target=def_dst/f'psqc2_{i}_{mode.lower()}.json'
            if target.exists():
                existing=json.loads(target.read_text())
                if existing!=definition:
                    raise RuntimeError(f'Refusing to overwrite changed definition: {target}')
            target.write_text(json.dumps(definition,indent=2)+'\n')
            records.append((id,mode))
    print('Built',len(records),'ESM QC definitions, 3 byte-identical source sprites')
    for rid, mode in records:print(rid,mode)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',required=True,type=Path)
    ap.add_argument('--esm',required=True,type=Path)
    a=ap.parse_args()
    build(a.source,a.esm)
