#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'experiments/photo_tailor_final_comparison'

def main():
    j=json.load(open(OUT/'FINAL_COMPARISON.json'))
    b=j['sameReferenceBenchmark']
    assert b['sampleCount']==20
    assert b['overall']['A']==8.73
    assert b['overall']['B']==9.18
    assert b['overall']['C']==9.29
    assert b['overall']['C_minus_B']==0.11
    assert j['threeLabHistory']['Lab01']['same20ReferenceBenchmark'] is False
    assert j['threeLabHistory']['Lab02']['samples']==20
    assert j['threeLabHistory']['Lab03']['samples']==20
    for f in ('FINAL_A_B_C_20_REFERENCE_CONTACT.png','FINAL_A_B_C_SCORECARD.png',
              'FINAL_LAB_01_02_03_OVERVIEW.png','FINAL_COMPARISON.md'):
        assert (OUT/f).exists(),f
    print('PASS final three-lab comparison package')
    print('PASS A/B/C 20-reference result: 8.73 / 9.18 / 9.29')
    print('PASS Hybrid C beats Full PT B by +0.11 proxy points')
    print('PASS Lab01 is represented architecturally, not with a fake benchmark')

if __name__=='__main__':
    main()
