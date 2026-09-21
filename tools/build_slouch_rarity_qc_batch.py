#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from v5.pngio import read_rgba_png, write_rgba_png, blank_image, blit, nearest_scale, draw_text
from v5.source.template_transfer import load_contract, template_frames, alpha_cells, ContractError

OUT = ROOT / 'experiments/source_template_rarity_batch_01'
ASSETS = ROOT / 'authored/motifs/slouch_beanie_v1/assets'
VIEWS = ['front','right','left','back']

BATCH = [
    dict(id='C1_COCOA_SOLID', rarity='Common', palette='CUTE_COCOA_GOLD',
         pattern=None, motif=None, systems=['solid body']),
    dict(id='C2_STONE_FINE_RIB', rarity='Common', palette='EVERYDAY_STONE_BLUE',
         pattern='fine_rib', motif=None, systems=['fine rib']),
    dict(id='U1_SAGE_SEED_LEAF', rarity='Uncommon', palette='SPRING_SAGE_PETAL',
         pattern='seed_stitch', motif='leaf_sprig', systems=['seed texture','leaf focal']),
    dict(id='U2_INDIGO_TWIN_STAR', rarity='Uncommon', palette='CELESTIAL_INDIGO_STAR',
         pattern='twin_stripe', motif='star', systems=['twin stripe','star focal']),
    dict(id='R1_AUTUMN_JACQUARD_FLOWER', rarity='Rare', palette='AUTUMN_OCHRE_PLUM',
         pattern='simple_jacquard', motif='flower_cluster_small', systems=['jacquard','flower cluster']),
    dict(id='R2_WINE_CABLE_BADGE', rarity='Rare', palette='GOTHIC_WINE_ASH',
         pattern='cable_hint', motif='stitched_badge', systems=['cable texture','stitched badge']),
    dict(id='E1_ARCANE_CABLE_STRIPE_BOTANICAL', rarity='Epic', palette='ARCANE_VIOLET_COPPER',
         pattern='cable_hint', band_pattern='twin_stripe', motif='leaf_sprig', motif2='flower_tiny',
         systems=['cable','twin stripe','extended botanical']),
    dict(id='E2_JADE_JACQUARD_BOTANICAL', rarity='Epic', palette='LUXURY_JADE_BRONZE',
         pattern='simple_jacquard', band_pattern='contrast_stitch', motif='flower_cluster_small', motif2='leaf_sprig',
         systems=['jacquard','contrast finish','extended botanical']),
]


def hexrgb(s):
    s=s.lstrip('#')
    return tuple(int(s[i:i+2],16) for i in (0,2,4))


def luminance(p):
    return p[0]*0.299+p[1]*0.587+p[2]*0.114


def recolor_template(frame, ramp):
    vals=sorted({luminance(p) for row in frame for p in row if p[3]})
    out=[row[:] for row in frame]
    for y,row in enumerate(frame):
        for x,p in enumerate(row):
            if not p[3]: continue
            idx=min(range(len(vals)),key=lambda i:abs(vals[i]-luminance(p)))
            ri=round(idx*(len(ramp)-1)/max(1,len(vals)-1))
            out[y][x]=(*ramp[ri],p[3])
    return out


def asset_cells(name):
    img=read_rgba_png(ASSETS/f'{name}.png')
    pts=[(x,y,p) for y,row in enumerate(img) for x,p in enumerate(row) if p[3]]
    if not pts: raise ContractError(f'empty asset {name}')
    return pts, len(img[0]), len(img)


def apply_pattern(frame, name, ramp, *, band_only=False, crown_only=False):
    pts,w,h=asset_cells(name)
    mask={(x,y):p for x,y,p in pts}
    out=[row[:] for row in frame]
    ys=[y for y,row in enumerate(frame) for p in row if p[3]]
    maxy=max(ys)
    band_start=maxy-4
    for y,row in enumerate(frame):
        for x,p in enumerate(row):
            if not p[3]: continue
            if band_only and y < band_start: continue
            if crown_only and y >= band_start: continue
            src=mask.get((x%w,y%h))
            if not src: continue
            base_i=min(range(len(ramp)),key=lambda i:sum(abs(p[j]-ramp[i][j]) for j in range(3)))
            delta = -1 if luminance(src) < 140 else 1
            ni=max(0,min(len(ramp)-1,base_i+delta))
            out[y][x]=(*ramp[ni],p[3])
    return out


def motif_footprint(name):
    pts,w,h=asset_cells(name)
    # preserve authored silhouette, normalize only local origin.
    minx=min(x for x,_,_ in pts); miny=min(y for _,y,_ in pts)
    return [(x-minx,y-miny,p) for x,y,p in pts], max(x for x,_,_ in pts)-minx+1, max(y for _,y,_ in pts)-miny+1


def find_fit(frame, pts, w, h, anchor, bias=(0,0)):
    ax,ay=anchor
    px=ax-w//2+bias[0]; py=ay-h//2+bias[1]
    for radius in range(0,10):
        for dy in range(-radius,radius+1):
            for dx in range(-radius,radius+1):
                if max(abs(dx),abs(dy))!=radius: continue
                ox,oy=px+dx,py+dy
                if all(0<=ox+x<len(frame[0]) and 0<=oy+y<len(frame) and frame[oy+y][ox+x][3]
                       for x,y,_ in pts):
                    return ox,oy
    raise ContractError(f'cannot fit motif near {anchor}')


def apply_motif(frame, name, accent_ramp, anchor, bias=(0,0)):
    pts,w,h=motif_footprint(name)
    ox,oy=find_fit(frame,pts,w,h,anchor,bias)
    values=sorted({luminance(p) for _,_,p in pts})
    out=[row[:] for row in frame]
    for x,y,p in pts:
        vi=min(range(len(values)),key=lambda i:abs(values[i]-luminance(p)))
        ri=round(vi*(len(accent_ramp)-1)/max(1,len(values)-1))
        out[oy+y][ox+x]=(*accent_ramp[ri],frame[oy+y][ox+x][3])
    return out,dict(asset=name,offset=[ox,oy],size=[w,h],cells=len(pts))


def make_contact(rows):
    scale=4; label_w=220; cell=24*scale; row_h=cell+18
    canvas=blank_image(label_w+4*cell, row_h*len(rows),(238,235,229,255))
    for r,row in enumerate(rows):
        y0=r*row_h
        draw_text(canvas,f"{row['rarity']} {row['id']}",6,y0+5,scale=1)
        draw_text(canvas,' / '.join(row['systems'])[:34],6,y0+15,scale=1)
        for c,v in enumerate(VIEWS):
            big=nearest_scale(read_rgba_png(Path(row['frames'][v])),scale)
            blit(canvas,big,label_w+c*cell,y0)
            draw_text(canvas,v,label_w+c*cell+3,y0+cell+3,scale=1)
    return canvas


def main():
    tpl=load_contract(ROOT/'generator/data/templates/slouch_pl24.json')
    base=template_frames(tpl)
    palettes=json.loads((ROOT/'authored/palettes.json').read_text())['palettes']
    pal={p['id']:p for p in palettes}
    OUT.mkdir(parents=True,exist_ok=True)
    records=[]
    for spec in BATCH:
        p=pal[spec['palette']]
        body=[hexrgb(x) for x in p['ramps']['body']]
        accent=[hexrgb(x) for x in p['ramps']['accent']]
        trim=[hexrgb(x) for x in p['ramps']['trim']]
        vdir=OUT/spec['id']; vdir.mkdir(parents=True,exist_ok=True)
        placements={}
        paths={}
        for view in VIEWS:
            fr=recolor_template(base[view],body)
            if spec.get('pattern'):
                fr=apply_pattern(fr,spec['pattern'],body,crown_only=True)
            if spec.get('band_pattern'):
                fr=apply_pattern(fr,spec['band_pattern'],trim,band_only=True)
            anchor=tpl.anchors[view]['crown_center']
            if spec.get('motif'):
                fr,pl=apply_motif(fr,spec['motif'],accent,anchor,bias=(-2,1) if spec.get('motif2') else (0,1))
                placements.setdefault(view,[]).append(pl)
            if spec.get('motif2'):
                fr,pl=apply_motif(fr,spec['motif2'],accent,anchor,bias=(3,0))
                placements.setdefault(view,[]).append(pl)
            if alpha_cells(fr)!=alpha_cells(base[view]):
                raise ContractError(f"{spec['id']}/{view}: locked alpha changed")
            path=vdir/f'{view}.png'; write_rgba_png(path,fr)
            paths[view]=str(path)
        records.append({**spec,'frames':paths,'placements':placements,'geometry':'LOCKED_TEMPLATE_ALPHA'})
    (OUT/'batch_manifest.json').write_text(json.dumps({'schema':'slouch-rarity-qc/v1','template':'slouch_pl24','count':len(records),'variants':records},indent=2)+'\n')
    sheet=make_contact(records)
    write_rgba_png(OUT/'rarity_contact_sheet.png',sheet)
    print(f'PASS rarity QC batch: {len(records)} variants / {len(records)*4} frames')
    for rarity in ['Common','Uncommon','Rare','Epic']:
        print(rarity, sum(1 for r in records if r['rarity']==rarity))
    print(OUT/'rarity_contact_sheet.png')

if __name__=='__main__':
    main()
