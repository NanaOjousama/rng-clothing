#!/usr/bin/env python3
from __future__ import annotations
import json, shutil, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from v5.pngio import read_rgba_png, write_rgba_png, blank_image, blit
from v5.source.template_transfer import load_contract, template_frames, alpha_cells
import tools.build_slouch_rarity_qc_batch as rb

OUT=ROOT/'experiments/source_template_roundtrip_slb4'
PACK=ROOT/'test-packs/fashionsense/RNG-SLB4-RoundTrip-QC'
LIVE=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods/RNG-SLB4-RoundTrip-QC')
SLB3=ROOT/'experiments/source_template_rarity_batch_01'
VIEWS=['front','right','left','back']
FS_KEYS={'front':'FrontHat','right':'RightHat','left':'LeftHat','back':'BackHat'}
SELECT=['C2_STONE_FINE_RIB','U1_SAGE_SEED_LEAF','R1_AUTUMN_JACQUARD_FLOWER','E1_ARCANE_CABLE_STRIPE_BOTANICAL']
FS_SCALE=10/3

def interior(frame,x,y):
    if not frame[y][x][3]: return False
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            if not dx and not dy: continue
            xx,yy=x+dx,y+dy
            if yy<0 or yy>=len(frame) or xx<0 or xx>=len(frame[0]) or not frame[yy][xx][3]:
                return False
    return True

def safe_pattern(frame,name,ramp,*,band_only=False,crown_only=False):
    original=[row[:] for row in frame]
    painted=rb.apply_pattern(frame,name,ramp,band_only=band_only,crown_only=crown_only)
    for y,row in enumerate(painted):
        for x,p in enumerate(row):
            if p!=original[y][x] and not interior(original,x,y):
                painted[y][x]=original[y][x]
    return painted

def safe_motif(frame,name,accent,anchor,bias=(0,0)):
    # place normally, but reject any motif cell which would touch alpha boundary.
    pts,w,h=rb.motif_footprint(name)
    ax,ay=anchor
    px=ax-w//2+bias[0]; py=ay-h//2+bias[1]
    candidates=[]
    for radius in range(0,10):
        for dy in range(-radius,radius+1):
            for dx in range(-radius,radius+1):
                if max(abs(dx),abs(dy))!=radius: continue
                ox,oy=px+dx,py+dy
                if all(0<=ox+x<len(frame[0]) and 0<=oy+y<len(frame)
                       and interior(frame,ox+x,oy+y) for x,y,_ in pts):
                    candidates.append((ox,oy))
        if candidates: break
    if not candidates:
        return frame, {'asset':name,'skipped':'no interior-safe fit'}
    ox,oy=candidates[0]
    values=sorted({rb.luminance(p) for _,_,p in pts})
    out=[row[:] for row in frame]
    for x,y,p in pts:
        vi=min(range(len(values)),key=lambda i:abs(values[i]-rb.luminance(p)))
        ri=round(vi*(len(accent)-1)/max(1,len(values)-1))
        out[oy+y][ox+x]=(*accent[ri],frame[oy+y][ox+x][3])
    return out, {'asset':name,'offset':[ox,oy],'size':[w,h],'cells':len(pts)}

def render_fixed(spec,tpl,base,pal):
    p=pal[spec['palette']]
    body=[rb.hexrgb(x) for x in p['ramps']['body']]
    accent=[rb.hexrgb(x) for x in p['ramps']['accent']]
    trim=[rb.hexrgb(x) for x in p['ramps']['trim']]
    result={}; report={}
    for view in VIEWS:
        fr=rb.recolor_template(base[view],body)
        if spec.get('pattern'):
            fr=safe_pattern(fr,spec['pattern'],body,crown_only=True)
        if spec.get('band_pattern'):
            fr=safe_pattern(fr,spec['band_pattern'],trim,band_only=True)
        # Front-owned motif contract for this QC batch:
        # Front = visible; sides/back = no front emblem painted.
        if view=='front' and spec.get('motif'):
            fr,pl=safe_motif(fr,spec['motif'],accent,tpl.anchors[view]['crown_center'],bias=(-2,1) if spec.get('motif2') else (0,1))
            report.setdefault(view,[]).append(pl)
        if view=='front' and spec.get('motif2'):
            fr,pl=safe_motif(fr,spec['motif2'],accent,tpl.anchors[view]['crown_center'],bias=(3,0))
            report.setdefault(view,[]).append(pl)
        assert alpha_cells(fr)==alpha_cells(base[view])
        result[view]=fr
    return result,report

def fs_doc(name,tag,rarity,scale=None):
    doc={'Name':name,'Tags':['SLB4','Round Trip QC',tag,rarity,'RNG Clothing','slouch beanie']}
    headx={'front':-2,'right':-1,'left':-3,'back':-2}
    for i,v in enumerate(VIEWS):
        doc[FS_KEYS[v]]={
            'DisableGrayscale':True,'HideHair':False,
            'StartingPosition':{'X':0,'Y':i*24},
            'HeadPosition':{'X':headx[v],'Y':-3},
            'HatSize':{'Width':24,'Length':24}
        }
    if scale is not None: doc['Scale']=scale
    return doc

def write_hat(folder,frames,doc):
    folder.mkdir(parents=True,exist_ok=True)
    atlas=blank_image(24,96)
    for i,v in enumerate(VIEWS): blit(atlas,frames[v],0,i*24)
    write_rgba_png(folder/'hat.png',atlas)
    (folder/'hat.json').write_text(json.dumps(doc,indent=2)+'\n')

def main():
    tpl=load_contract(ROOT/'generator/data/templates/slouch_pl24.json')
    base=template_frames(tpl)
    pals={p['id']:p for p in json.loads((ROOT/'authored/palettes.json').read_text())['palettes']}
    specs={s['id']:s for s in rb.BATCH}
    for p in (OUT,PACK):
        if p.exists(): shutil.rmtree(p)
    OUT.mkdir(parents=True); (PACK/'Hats').mkdir(parents=True)
    records=[]
    for vid in SELECT:
        spec=specs[vid]
        direct={v:read_rgba_png(SLB3/vid/f'{v}.png') for v in VIEWS}
        fixed,placements=render_fixed(spec,tpl,base,pals)
        od=OUT/vid; od.mkdir()
        for v in VIEWS:
            write_rgba_png(od/f'A_direct_{v}.png',direct[v])
            write_rgba_png(od/f'B_fixed_{v}.png',fixed[v])
        short=vid.split('_',1)[0]
        write_hat(PACK/'Hats'/f'{short}_A_DIRECT',direct,
                  fs_doc(f'SLB4 {short} A DIRECT', 'A direct SLB3', spec['rarity'], None))
        write_hat(PACK/'Hats'/f'{short}_B_ROUNDTRIP',fixed,
                  fs_doc(f'SLB4 {short} B ROUNDTRIP FIXED', 'B roundtrip fixed', spec['rarity'], FS_SCALE))
        records.append({'id':vid,'rarity':spec['rarity'],'A':'direct SLB3 export','B':'roundtrip fixed',
                        'B_scale':FS_SCALE,'motif_contract':'front-owned; absent on side/back',
                        'surface_contract':'pattern/motif interior-safe; outline alpha cells untouched',
                        'placements':placements})
    manifest={
      'Name':'SLB4 Round Trip QC','Author':'RNG Clothing','Version':'0.1.0',
      'Description':'A/B slouch round-trip QC: direct SLB3 export vs corrected fidelity/export contract.',
      'UniqueID':'RNGClothing.FashionSense.SLB4RoundTripQC','UpdateKeys':[],
      'ContentPackFor':{'UniqueID':'PeacefulEnd.FashionSense','MinimumVersion':'7.5.0'}}
    (PACK/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    report={'tag':'SLB4','pairs':records,'fsScale':FS_SCALE,
            'whyScale':'24px PL24 construction matched to ESM 0.833333 presentation: Fashion Sense base scale 4 x 0.833333 = 3.333333',
            'directions':VIEWS}
    (PACK/'TRACEABILITY.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    if LIVE.exists(): shutil.rmtree(LIVE)
    shutil.copytree(PACK,LIVE)
    print('PASS SLB4 pairs',len(records))
    print('PASS live hats',len(list((LIVE/'Hats').glob('*/hat.json'))))
    print('LIVE',LIVE)

if __name__=='__main__': main()
