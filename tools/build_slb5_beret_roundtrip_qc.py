#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, shutil, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from v5 import authored
from v5 import source_backed as sbm
from v5.pngio import write_rgba_png, read_rgba_png
from v5.source import roundtrip

PACK=ROOT/'test-packs/fashionsense/RNG-SLB5-Beret-RoundTrip-QC'
LIVE=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods/RNG-SLB5-Beret-RoundTrip-QC')
WORK=ROOT/'experiments/source_template_roundtrip_slb5'
FS_ORDER=['Front','Right','Left','Back']
CASES=[
 ('P0_PLAIN',None,None),
 ('M1_LEAF','CUTE_ROSE_CREAM','leaf_sprig'),
 ('M2_DOTS','CUTE_COCOA_GOLD','beret_dots_small'),
 ('M3_BOW','PASTEL_PEACH_LILAC','bow_knot'),
]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]

def app_for(name,jpath,ppath,w,h):
    return {
      'name':name,'pack':'SLB5 Direct','pack_author':'RNG Clothing','category':'Hats',
      'json_path':str(jpath),'png_path':str(ppath),
      'analysis':{'boxes':{
        'Front':[0,0,w,h],'Right':[0,h,w,h],
        'Left':[0,h*2,w,h],'Back':[0,h*3,w,h]
      }}
    }

def main():
    for p in (PACK,WORK):
        if p.exists(): shutil.rmtree(p)
    (PACK/'Hats').mkdir(parents=True)
    WORK.mkdir(parents=True)

    lib=authored.load()
    base=sbm.load_one('beret_02')
    w,h=base.size
    report={
      'tag':'SLB5',
      'template':'beret_02',
      'size':[w,h],
      'size_policy':'source-derived/default; no forced 20px export rule',
      'pairs':[]
    }

    for cid,pid,decal_name in CASES:
        palette=next((p for p in lib.palettes if p.id==pid),None) if pid else None
        decals=()
        if decal_name:
            decals=(next(d for d in lib.decals if d.name==decal_name),)
        direct=sbm.render(base,palette=palette,decals=decals,lib=lib)

        adir=PACK/'Hats'/f'{cid}_A_DIRECT'
        adir.mkdir(parents=True)
        aname=f'SLB5 {cid} A DIRECT'
        atags=['SLB5','A direct','beret_02','source-backed',decal_name or 'plain']
        adoc=sbm.hat_json(direct,aname,atags)
        write_rgba_png(adir/'hat.png',sbm.sheet(direct))
        (adir/'hat.json').write_text(json.dumps(adoc,indent=2)+'\n')

        # True round-trip: re-ingest A's FS model+atlas, then re-export.
        app=app_for(aname,adir/'hat.json',adir/'hat.png',w,h)
        bdoc,batlas,brep=roundtrip.export(app,name=f'SLB5 {cid} B ROUNDTRIP')
        bdoc['Tags']=['SLB5','B roundtrip','beret_02','roundtrip',decal_name or 'plain']
        bdir=PACK/'Hats'/f'{cid}_B_ROUNDTRIP'
        bdir.mkdir(parents=True)
        write_rgba_png(bdir/'hat.png',batlas)
        (bdir/'hat.json').write_text(json.dumps(bdoc,indent=2)+'\n')

        cmp=roundtrip.compare(app,bdoc)
        report['pairs'].append({
          'id':cid,'palette':pid,'decal':decal_name,
          'A_png_sha':sha(adir/'hat.png'),'B_png_sha':sha(bdir/'hat.png'),
          'property_compare':cmp,
          'roundtrip':brep,
          'expected_visibility': (
             'plain/no motif' if not decal_name else
             'front+right+left; absent on back' if decal_name=='leaf_sprig' else
             'declared on all views; independently seated per view'
          )
        })

    (PACK/'manifest.json').write_text(json.dumps({
      'Name':'SLB5 Beret Round Trip QC',
      'Author':'RNG Clothing','Version':'0.1.0',
      'Description':'Different-template A/B fidelity test using source-backed beret_02.',
      'UniqueID':'RNGClothing.FashionSense.SLB5BeretRoundTripQC',
      'UpdateKeys':[],
      'ContentPackFor':{'UniqueID':'PeacefulEnd.FashionSense','MinimumVersion':'7.5.0'}
    },indent=2)+'\n')
    (PACK/'TRACEABILITY.json').write_text(json.dumps(report,indent=2)+'\n')
    (WORK/'report.json').write_text(json.dumps(report,indent=2)+'\n')

    if LIVE.exists(): shutil.rmtree(LIVE)
    shutil.copytree(PACK,LIVE)

    print('PASS source-derived size',w,h)
    print('PASS pairs',len(report['pairs']))
    print('PASS live hats',len(list((LIVE/'Hats').glob('*/hat.json'))))
    print('LIVE',LIVE)

if __name__=='__main__':
    main()
