#!/usr/bin/env python3
"""Proof that VanillaOnly is routed through the unified production generator."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,shutil
from generator.production_router import pools,render
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'experiments/production_router_vanilla_only_01'
VIEWS=('front','right','left','back')
PALETTES=['COASTAL_SEAFOAM_CORAL','AUTUMN_OCHRE_PLUM','SAILOR_COBALT_CREAM','FIELD_CANVAS_MOSS','GOTHIC_WINE_ASH','SPRING_SAGE_PETAL','DESERT_CLAY_TURQUOISE','CUTE_ROSE_CREAM']

def save_frames(folder,prefix,frames):
    folder.mkdir(parents=True,exist_ok=True)
    for v,im in frames.items(): im.save(folder/f'{prefix}_{v}.png')
def sheet(rows,kind,path):
    frame=160 if kind=='hat' else 120; gap=12; group=4*frame+3*gap; sx=70; vx=sx+group+130; W=vx+group+70; rowh=250 if kind=='hat' else 210; H=62+len(rows)*rowh
    s=Image.new('RGBA',(W,H),(240,238,232,255));d=ImageDraw.Draw(s)
    d.text((14,10),f'PRODUCTION ROUTER — VANILLA ONLY — {kind.upper()}',fill=(20,20,20,255))
    d.text((14,29),'SOURCE | REAL-GENERATOR OUTPUT   provenance=VANILLA',fill=(55,55,55,255))
    for ri,r in enumerate(rows):
        y0=62+ri*rowh; f=OUT/r['dir']; d.text((14,y0),f"#{r['sourceIndex']} {r['sourceName']} | used={','.join(r['used'])} | capacity={r['capacity']}",fill=(30,30,30,255))
        for x0,label,prefix in ((sx,'SOURCE','source'),(vx,'OUTPUT','output')):
            d.text((x0,y0+18),label,fill=(65,65,65,255));x=x0
            for v in VIEWS:
                im=Image.open(f/f'{prefix}_{v}.png').convert('RGBA'); big=im.resize((frame,frame),Image.Resampling.NEAREST); s.alpha_composite(big,(x,y0+38)); d.text((x,y0+41+frame),v[0].upper(),fill=(70,70,70,255));x+=frame+gap
    s.save(path)

def main():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    pool=pools('VanillaOnly')
    if set(pool['allowedSources'])!={'VANILLA'}: raise RuntimeError(pool)
    records=[]
    for kind in ('hat','shirt'):
        for n,entry in enumerate(pool[kind]):
            result=render(entry,palette=PALETTES[n%len(PALETTES)])
            if result['provenance']!='VANILLA': raise RuntimeError('source leak')
            folder=OUT/f"{kind}_{result['sourceIndex']:03d}"; save_frames(folder,'source',result['sourceFrames']); save_frames(folder,'output',result['frames'])
            meta={k:v for k,v in result.items() if k not in ('sourceFrames','frames')}; meta['dir']=folder.name
            (folder/'production_trace.json').write_text(json.dumps(meta,indent=2)+'\n'); records.append(meta)
    hats=[r for r in records if r['kind']=='hat']; shirts=[r for r in records if r['kind']=='shirt']
    sheet(hats,'hat',OUT/'PRODUCTION_VANILLA_ONLY_HATS.png');sheet(shirts,'shirt',OUT/'PRODUCTION_VANILLA_ONLY_SHIRTS.png')
    audit={m:pools(m) for m in ('VanillaOnly','ModAuthorOnly','Everything')}
    # Assert no source leakage in restrictive modes.
    assert all(x['provenance']=='VANILLA' for k in ('hat','shirt') for x in audit['VanillaOnly'][k])
    assert all(x['provenance']=='MOD_AUTHOR' for k in ('hat','shirt') for x in audit['ModAuthorOnly'][k])
    (OUT/'source_mode_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    (OUT/'manifest.json').write_text(json.dumps({'schema':'production-router-vanilla-only-proof/v1','mode':'VanillaOnly','allowedSources':pool['allowedSources'],'records':records},indent=2)+'\n')
    print('PASS VanillaOnly production routing:',len(hats),'hats +',len(shirts),'shirts')
    print('ModAuthorOnly hats:',len(audit['ModAuthorOnly']['hat']),'shirts:',len(audit['ModAuthorOnly']['shirt']))
    print('Everything hats:',len(audit['Everything']['hat']),'shirts:',len(audit['Everything']['shirt']))
    print(OUT/'PRODUCTION_VANILLA_ONLY_HATS.png');print(OUT/'PRODUCTION_VANILLA_ONLY_SHIRTS.png')
if __name__=='__main__': main()
