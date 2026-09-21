#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import replace
from pathlib import Path
import json, sys
sys.path.insert(0,'.')

from v5 import aa, ag
from v5.construction import Construction, Piece
from v5.contracts import ARCHITECTURE_LIBRARY, SLOT_LIBRARY
from v5.grammar import PLANE, VIEWS
from v5.pngio import read_rgba_png, write_rgba_png, blank_image, blit, flip_h
from v5.resolver import generate_spec
from v5.library import brimmed_hat, brimless_hat  # register HEAD contracts

ROOT=Path('.')
TPL_PATH=ROOT/'generator/data/headwear/slouch_beanie_construction_template.json'
OUT=ROOT/'experiments/slouch_beanie_generator_proof'
OUT.mkdir(parents=True, exist_ok=True)


def alpha_bbox(img):
    pts=[(x,y) for y,row in enumerate(img) for x,p in enumerate(row) if p[3]]
    if not pts: raise ValueError('empty reference')
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return min(xs),min(ys),max(xs),max(ys)


def crop_alpha(img):
    x0,y0,x1,y1=alpha_bbox(img)
    return [[img[y][x] for x in range(x0,x1+1)] for y in range(y0,y1+1)]


def scale_mask(src, tw, th):
    sh=len(src); sw=len(src[0])
    out=set()
    # nearest-neighbour geometry only; source RGB is intentionally discarded
    for y in range(th):
        sy=min(sh-1, int((y+0.5)*sh/th))
        for x in range(tw):
            sx=min(sw-1, int((x+0.5)*sw/tw))
            if src[sy][sx][3]: out.add((x,y))
    return out


def place_mask(mask, tw, th, bottom, canvas=(20,20)):
    cw,ch=canvas
    left=(cw-tw)//2
    top=bottom-th+1
    return {(left+x,top+y) for x,y in mask if 0<=left+x<cw and 0<=top+y<ch}


def build_construction(tpl):
    targets=tpl['fitTargets']; refs=tpl['referenceFrames']
    # V5 authors one profile-side view; right is the construction source and left mirrors at export.
    src_for={'front':'front','side':'right','back':'back'}
    silhouettes={}
    bands={}; crowns={}
    for view in VIEWS:
        k=src_for[view]; cfg=targets[k]
        img=read_rgba_png(ROOT/refs[k]); crop=crop_alpha(img)
        tw,th=cfg['bbox']; local=scale_mask(crop,tw,th)
        cells=place_mask(local,tw,th,cfg['bottom'])
        silhouettes[view]=cells
        occupied_rows=sorted({y for x,y in cells})
        br=cfg['bandRows']
        band_rows=set(occupied_rows[-br:])
        bands[view]={c for c in cells if c[1] in band_rows}
        crowns[view]=cells-bands[view]
    crown=Piece('crown','body',z=0,wrap=PLANE,surface_domain='crown',cells=crowns,identity=True)
    band=Piece('band','trim',z=1,wrap=PLANE,surface_domain='band',cells=bands,identity=True,form='mass')
    c=Construction(SLOT_LIBRARY['HEAD'].envelope,silhouettes,[crown,band],{'crown':('crown',),'band':('band',)})
    c.meta={'template':'slouch_beanie_construction_v1','reference_role':'CONSTRUCTION_ONLY'}
    c.validate()
    return c


def clean_spec(seed=0):
    # Borrow a wool headwear palette/material from the real resolver, then remove random shape/surface/ornament.
    base=None
    for candidate in range(seed, seed+512):
        probe=generate_spec(candidate,slot='HEAD',envelope=SLOT_LIBRARY['HEAD'].envelope)
        if probe.material == 'wool_melton':
            base=probe; break
    if base is None:
        raise RuntimeError('no wool_melton HEAD spec found in bounded search')
    return replace(base,architecture='BRIMLESS_HAT',parameters={},layers={},ornaments=(),surface={},
                   silhouette_ref='slouch_beanie_construction_v1',
                   construction_refs=('slouch_beanie_construction_v1',))


def rows_from_raster(raster, view):
    return ag.to_rows(raster[view], SLOT_LIBRARY['HEAD'].envelope)


def main():
    tpl=json.loads(TPL_PATH.read_text())
    con=build_construction(tpl)
    spec=clean_spec()
    arch=ARCHITECTURE_LIBRARY['BRIMLESS_HAT']
    art=aa.plan(spec,con,arch)
    raster=ag.rasterize(spec,con,art,'head_20x20')
    front=rows_from_raster(raster,'front'); side=rows_from_raster(raster,'side'); back=rows_from_raster(raster,'back')
    left=flip_h(side)
    for name,img in [('front',front),('right',side),('left',left),('back',back)]:
        write_rgba_png(OUT/f'slouch_v1_{name}.png',img)
    sheet=blank_image(80,20)
    for i,img in enumerate((front,side,left,back)): blit(sheet,img,i*20,0)
    write_rgba_png(OUT/'slouch_v1_sheet.png',sheet)
    # 8x visual-review sheet; not a runtime asset.
    from v5.pngio import nearest_scale
    write_rgba_png(OUT/'slouch_v1_sheet_x8.png',nearest_scale(sheet,8))
    meta={
      'constructionTemplate':str(TPL_PATH),
      'sourceColourCopied':False,
      'styleRenderer':'v5.ag/head_20x20',
      'paletteSeed':spec.seed,
      'material':spec.material,
      'views':['front','right','left','back'],
      'output':'experiments/slouch_beanie_generator_proof/slouch_v1_sheet.png'
    }
    (OUT/'proof.json').write_text(json.dumps(meta,indent=2)+'\n')
    print('PASS slouch generator proof')
    print('material',spec.material,'seed',spec.seed)
    for v in VIEWS: print(v,'cells',len(con.silhouette[v]))
    print(OUT/'slouch_v1_sheet_x8.png')

if __name__=='__main__': main()
