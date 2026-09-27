#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from v5.pngio import read_rgba_png
from v5.source.template_transfer import load_contract, verify_contract

def main():
    c=load_contract('generator/data/templates/trucker.json'); rep=verify_contract(c)
    assert c.id=='trucker' and c.frame_size==(26,26)
    assert set(c.frames)=={'front','right','left','back'}
    frames={v:read_rgba_png(ROOT/c.frames[v]['path']) for v in c.frames}
    assert frames['left']==[list(reversed(r)) for r in frames['right']], 'left must exact-mirror right'
    masks=json.loads((ROOT/'authored/templates/trucker_rd22_pl26/component_masks.json').read_text())
    assert masks['template']=='trucker'
    for v in ('front','right','left','back'):
        seen=set()
        for comp,cells in masks['views'][v].items():
            for x,y in cells:
                assert 0<=x<26 and 0<=y<26
                assert frames[v][y][x][3]>0, f'{v}/{comp} mask hits transparency at {(x,y)}'
                assert (x,y) not in seen, f'{v} mask overlap at {(x,y)}'
                seen.add((x,y))
    rm=json.loads((ROOT/'generator/data/headwear/trucker_roll_matrix.json').read_text())
    assert rm['templateContract']=='generator/data/templates/trucker.json'
    assert 'synthetic_mesh' in rm['renderPolicy']['forbid']
    wear=json.loads((ROOT/'generator/data/headwear/trucker_wear_contract.json').read_text())
    assert wear['template']=='trucker' and set(wear['directionDefaults'])=={'front','right','left','back'}
    print('PASS trucker source-backed generator template')
    print('views=4 frame=26x26 left=exact mirror masks=opaque/nonoverlap')
    print('roll-matrix=linked wear-contract=linked source-transfer=linked')
    print('opaque:', {v:rep['views'][v]['opaque'] for v in rep['views']})
if __name__=='__main__': main()
