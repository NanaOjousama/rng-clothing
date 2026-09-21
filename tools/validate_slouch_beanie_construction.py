#!/usr/bin/env python3
import json
from pathlib import Path
T=Path('generator/data/headwear/slouch_beanie_construction_template.json')
M=Path('generator/data/headwear/slouch_beanie_roll_matrix.json')
P=Path('experiments/slouch_beanie_generator_proof/proof.json')

def main():
    t=json.loads(T.read_text()); m=json.loads(M.read_text()); p=json.loads(P.read_text())
    assert t['referenceRole']=='CONSTRUCTION_ONLY'
    assert t['render']['sourceColourPolicy']=='IGNORE'
    assert t['render']['renderClass']=='head_20x20'
    assert t['render']['styleOwner']=='v5.ag'
    assert t['rollMatrix']==str(M)
    assert m['constructionTemplate']==str(T)
    assert m['motifLibrary']==t['motifLibrary'] if 'motifLibrary' in m else True
    for view,cfg in t['fitTargets'].items():
        assert 1 <= cfg['bbox'][0] <= 20 and 1 <= cfg['bbox'][1] <= 20
        assert 0 <= cfg['bottom'] < 20 and cfg['bandRows'] >= 1
    for path in t['referenceFrames'].values(): assert Path(path).exists(), path
    for view in ('front','right','left','back'):
        assert Path(f'experiments/slouch_beanie_generator_proof/slouch_v1_{view}.png').exists()
    assert p['sourceColourCopied'] is False
    assert p['styleRenderer']=='v5.ag/head_20x20'
    print('PASS slouch construction template + generator style proof')
    print('reference colour ignored; V5 owns outline/shading')

if __name__=='__main__': main()
