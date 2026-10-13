#!/usr/bin/env python3
"""Live 4-dir Full vs Obscured ESM worn capture at fixed hairstyles.

Only operates when no unrelated hat is equipped; clears newly generated QC
carrier between captures to avoid polluting player inventory. Restores hair.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import qc

PREF='qc.hairpolicy.psqc2'

def main(hairs):
    init=qc.require('get_render_state')['state']
    farmer=init['farmer']
    oldhair=farmer['hairstyle']
    facing=farmer['facing_name']
    oldhat=init.get('hat') or {}
    fsid=oldhat.get('fashion_sense_id') or ''
    vanilla=oldhat.get('vanilla_hat') or ''
    if fsid not in ('','None') or vanilla not in ('','(H)RNGClothing.ESM.GeneratedHat'):
        raise RuntimeError('Refusing to clear an unrelated worn hat')
    target=Path(qc.CAPTURES)/qc.current_session()/'esm_obscured_capture_index_v2.json'
    index=json.loads(target.read_text()).get('samples',[]) if target.exists() else []
    index=[item for item in index if item['hairstyle'] not in hairs]
    try:
        for hair in hairs:
            print('=== Hair',hair,'===',flush=True)
            qc.require('set_scene',hairstyle=hair,direction='front',freeze='true')
            for number in ('01','05','10'):
                for mode in ('full','obscured'):
                    id=f'{PREF}.{number}.{mode}'
                    label=f'esm2_hair{hair:03d}_QC2_{number}_{mode}'
                    qc.require('clear_hat')
                    qc.require('equip_garment',id=id)
                    state=qc.require('get_render_state')['state']
                    if state['hat'].get('vanilla_hat') != '(H)RNGClothing.ESM.GeneratedHat':
                        raise RuntimeError(f'Expected ESM carrier after equip {id}')
                    print(label,flush=True)
                    out=qc.require('capture_all_directions',label=label)
                    index.append({'hairstyle':hair,'number':number,'policy':mode,'id':id,'dir':out.get('directory')})
        target.write_text(json.dumps({'samples':index,'original_hair':oldhair},indent=2)+'\n')
        print('COMPLETE',len(index),'capture sets',target,flush=True)
    finally:
        qc.require('clear_hat')
        qc.require('set_scene',hairstyle=oldhair,direction=facing,freeze='false')
        print('Restored no hat, hairstyle',oldhair,'direction',facing,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--hair',nargs='+',type=int,default=[0,16,38])
    a=p.parse_args()
    main(a.hair)
