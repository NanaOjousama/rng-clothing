#!/usr/bin/env python3
from pathlib import Path
import json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
OUT=REPO/'experiments/photo_tailor_private_lab_03'

def arr(p): return np.array(Image.open(p).convert('RGBA'))
def edge(alpha):
    h,w=alpha.shape
    out=np.zeros_like(alpha,bool)
    for y in range(h):
        for x in range(w):
            if not alpha[y,x]: continue
            for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if nx<0 or ny<0 or nx>=w or ny>=h or not alpha[ny,nx]:
                    out[y,x]=1
                    break
    return out

def main():
    for p in ROOT.rglob('*.py'):
        s=p.read_text()
        for bad in [a+' '+b for a in ('from','import') for b in ('generator','v5','mods')]:
            assert bad not in s,(p,bad)
    inp=json.load(open(ROOT/'inputs.json'))
    assert inp['count']==20
    summary=json.load(open(OUT/'summary.json'))
    assert summary['sampleCount']==20
    assert summary['prototypeDecision']=='PROMISING_HYBRID'
    for row in inp['inputs']:
        rid=row['id']; cid=row['constructionHint']
        res=json.load(open(OUT/rid/'result.json'))
        assert res['plan']['authority']=='SOURCE_PIXELS_FIRST_PT_FEATURE_DELTAS_ONLY'
        for v in ('front','right','left','back'):
            a=arr(ROOT/'control_assets'/cid/f'{v}.png')
            b=arr(OUT/rid/f'{v}.png')
            assert np.array_equal(a[:,:,3],b[:,:,3]),(rid,v,'alpha')
            em=edge(a[:,:,3]>0)
            assert np.array_equal(a[em],b[em]),(rid,v,'outline drift')
            assert (OUT/rid/f'{v}_delta.png').exists()
    for f in ('LAB03_ALL_20_CONTACT.png','LAB03_HATS_16_CONTACT.png','LAB03_SHIRTS_4_CONTACT.png','LAB03_SCORECARD.png'):
        assert (OUT/f).exists(),f
    assert summary['dimensionAverages']['junk_control']['hybrid']>=9.8
    assert summary['dimensionAverages']['four_view_coherence']['hybrid']>=9.7
    print('PASS Lab03 zero production imports')
    print('PASS 20 same challenge references')
    print('PASS alpha geometry preserved across all 80 hybrid outputs')
    print('PASS source outline pixels preserved exactly across all 80 outputs')
    print('PASS bounded PT feature-delta authority on every sample')
    print('PASS hybrid cleanliness recovered:',summary['dimensionAverages']['four_view_coherence']['hybrid'],summary['dimensionAverages']['junk_control']['hybrid'])
    print('PASS decision',summary['prototypeDecision'],'overall',summary['averageHybridOverall'])

if __name__=='__main__':
    main()
