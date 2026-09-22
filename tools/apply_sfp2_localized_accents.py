#!/usr/bin/env python3
from pathlib import Path
import json, sys, shutil
ROOT=Path('/run/media/deck/USD00/RNG_clothing')
sys.path.insert(0,str(ROOT))
from v5.pngio import read_rgba_png, write_rgba_png, blank_image, nearest_scale, blit, draw_text

BATCH=ROOT/'experiments/sfp2_rarity_batch'
ASSETS=ROOT/'authored/motifs/slouch_beanie_v1/assets'
OUT=BATCH/'localized'

MOTIF_ASSET={
    'flower_tiny':'flower_tiny',
    'leaf':'leaf_sprig',
    'leaf_sprig':'leaf_sprig',
    'star':'star','moon':'moon','heart':'heart',
    'snowflake':'snowflake','mushroom_tiny':'mushroom_tiny',
    'animal_paw':'animal_paw','rune_mark':'rune_mark',
}
LEFT_VIS={'cuff_side_left','body_side_left'}
RIGHT_VIS={'cuff_side_right','body_side_right'}
FRONT_ONLY={
    'cuff_front_center','cuff_front_offset_left','cuff_front_offset_right',
    'body_front_center','body_front_offset_left','body_front_offset_right',
    'body_lower_front'
}
BACK_ONLY={'body_back_center','cuff_back_center'}

def alpha_cells(img):
    return {(x,y) for y,row in enumerate(img) for x,p in enumerate(row) if p[3]}

def flip_h(img):
    return [list(reversed(row)) for row in img]

def bbox(img):
    pts=alpha_cells(img)
    if not pts: raise ValueError('empty frame')
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return min(xs),min(ys),max(xs),max(ys)

def asset(name):
    img=read_rgba_png(ASSETS/f'{name}.png')
    pts=[(x,y,p) for y,row in enumerate(img) for x,p in enumerate(row) if p[3]]
    if not pts: raise ValueError('empty asset '+name)
    minx=min(x for x,y,p in pts); miny=min(y for x,y,p in pts)
    pts=[(x-minx,y-miny,p) for x,y,p in pts]
    w=max(x for x,y,p in pts)+1; h=max(y for x,y,p in pts)+1
    return pts,w,h

def anchor_for(img, placement, *, cuff=False):
    x0,y0,x1,y1=bbox(img)
    w=x1-x0+1; h=y1-y0+1
    # semantic center points, then fit search keeps the authored footprint in alpha.
    if 'left' in placement:
        ax=x0+max(2,w//4)
    elif 'right' in placement:
        ax=x1-max(2,w//4)
    else:
        ax=(x0+x1)//2
    if cuff or placement.startswith('cuff_'):
        ay=y1-max(1,min(2,h//5))
    elif 'lower' in placement:
        ay=y0+max(2,(h*2)//3)
    elif 'back' in placement:
        ay=y0+h//2
    else:
        ay=y0+h//2
    return ax,ay

def find_fit(img, pts, w, h, anchor, radius_max=10):
    ax,ay=anchor
    px=ax-w//2; py=ay-h//2
    for r in range(radius_max+1):
        for dy in range(-r,r+1):
            for dx in range(-r,r+1):
                if max(abs(dx),abs(dy))!=r: continue
                ox,oy=px+dx,py+dy
                if all(0<=ox+x<len(img[0]) and 0<=oy+y<len(img) and img[oy+y][ox+x][3]
                       for x,y,p in pts):
                    return ox,oy
    raise ValueError(f'cannot fit asset near {anchor}')

def apply_asset(img, name, anchor):
    pts,w,h=asset(name)
    ox,oy=find_fit(img,pts,w,h,anchor)
    out=[row[:] for row in img]
    for x,y,p in pts:
        # source-backed RGB, but preserve the existing alpha exactly.
        a=out[oy+y][ox+x][3]
        out[oy+y][ox+x]=(p[0],p[1],p[2],a)
    if alpha_cells(out)!=alpha_cells(img):
        raise AssertionError('alpha changed')
    return out, {'asset':name,'offset':[ox,oy],'size':[w,h],'cells':len(pts)}

def visible_views(placement):
    if placement in LEFT_VIS: return {'front','left'}
    if placement in RIGHT_VIS: return {'front','right'}
    if placement in BACK_ONLY: return {'back'}
    if placement in FRONT_ONLY or placement=='none': return {'front'}
    return {'front'}

def read_outputs(rid, view):
    p=BATCH/f'{rid}_{view}'/'outputs.json'
    return json.loads(p.read_text()) if p.exists() else []

def make_base_views(rid, selected, directional):
    views={'front':read_rgba_png(Path(selected[rid]['local_path']))}
    e=directional.get(rid,{})
    for view in ('right','back'):
        x=e.get(view)
        if x:
            views[view]=read_rgba_png(Path(x['local_path']))
    if 'right' in views:
        views['left']=flip_h(views['right'])
    return views

def main():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    plan=json.loads((BATCH/'batch_plan.json').read_text())
    selected=json.loads((BATCH/'selected_fronts.json').read_text())
    directional=json.loads((BATCH/'selected_directional.json').read_text())
    records=[]
    for item in plan['recipes']:
        if item['consistencyClass']!='LOCALIZED':
            continue
        rid=item['id']; rec=item['recipe']
        views=make_base_views(rid,selected,directional)
        vis=visible_views(rec.get('motifPlacement','none'))
        outdir=OUT/rid; outdir.mkdir(parents=True)
        paths={}; placements={}
        for view,img0 in views.items():
            img=[row[:] for row in img0]
            placements[view]=[]
            if view in vis:
                placement=rec.get('motifPlacement','none')
                # carrier/backing first when recipe calls for one.
                carrier=rec.get('carrierStyle','none')
                if carrier=='none' and rec.get('decorationStyle')=='woven_patch':
                    carrier='patch_rect'
                if carrier!='none' and (ASSETS/f'{carrier}.png').exists():
                    img,pl=apply_asset(img,carrier,anchor_for(img,placement))
                    placements[view].append({'role':'carrier',**pl})
                motif=MOTIF_ASSET.get(rec.get('motif','none'))
                if motif and (ASSETS/f'{motif}.png').exists():
                    img,pl=apply_asset(img,motif,anchor_for(img,placement))
                    placements[view].append({'role':'motif',**pl})
                micro=rec.get('microAccent','none')
                if micro!='none' and (ASSETS/f'{micro}.png').exists():
                    # micro accent retains its semantic identity (cuff patch stays on cuff).
                    img,pl=apply_asset(img,micro,anchor_for(img,placement,cuff=True))
                    placements[view].append({'role':'microAccent',**pl})
            if alpha_cells(img)!=alpha_cells(img0):
                raise AssertionError(f'{rid}/{view}: silhouette changed')
            path=outdir/f'{view}.png'; write_rgba_png(path,img); paths[view]=str(path)
        records.append({
            'id':rid,'rarity':item['rarity'],'recipe':rec,
            'visibleViews':sorted(vis),'availableViews':sorted(views),
            'frames':paths,'placements':placements,
            'geometry':'SOURCE_ALPHA_PRESERVED',
            'humanArtApproved':False,
        })
    (OUT/'localized_manifest.json').write_text(json.dumps({'schema':'sfp2-localized/v1','variants':records},indent=2)+'\n')

    # Contact: one row per localized recipe, all available cardinals.
    order=['front','right','back','left']; cw=210; ch=205; labelw=260
    sheet=blank_image(labelw+4*cw,len(records)*ch,(242,240,234,255))
    for rr,row in enumerate(records):
        y0=rr*ch
        draw_text(sheet,row['id'],8,y0+8,scale=1)
        r=row['recipe']
        draw_text(sheet,(r['motif']+' / '+r['decorationStyle'])[:34],8,y0+20,scale=1)
        draw_text(sheet,r['motifPlacement'][:34],8,y0+32,scale=1)
        for cc,view in enumerate(order):
            x0=labelw+cc*cw
            draw_text(sheet,view.upper(),x0+6,y0+7,scale=1)
            p=row['frames'].get(view)
            if not p:
                draw_text(sheet,'BASE VIEW PENDING',x0+30,y0+90,scale=1); continue
            img=read_rgba_png(Path(p))
            scale=max(1,min(7,185//len(img[0]),155//len(img)))
            big=nearest_scale(img,scale)
            blit(sheet,big,x0+(cw-len(big[0]))//2,y0+35+(155-len(big))//2)
            mark='DECORATED' if row['placements'].get(view) else 'BASE ONLY'
            draw_text(sheet,mark,x0+6,y0+190,scale=1)
    write_rgba_png(OUT/'SFP2_LOCALIZED_CONTACT.png',sheet)
    print('PASS localized compositor',len(records),'recipes')
    for r in records:
        print(r['id'],'visible=',r['visibleViews'],'available=',r['availableViews'])
        for v,p in r['placements'].items():
            if p: print(' ',v,p)
    print(OUT/'SFP2_LOCALIZED_CONTACT.png')

if __name__=='__main__':
    main()
