#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path('/run/media/deck/USD00/RNG_clothing')
sys.path.insert(0,str(ROOT))
from v5.pngio import read_rgba_png, write_rgba_png, blank_image, blit, nearest_scale, draw_text
from v5.source.template_transfer import load_contract, template_frames, alpha_cells

SRCROOT=ROOT/'experiments/spritefusion_beanie_material_rescale_test_01/accepted_32_and_under'
OUT=ROOT/'experiments/sf_structural_transfer_test_01'
OUT.mkdir(parents=True,exist_ok=True)
TPL=load_contract(ROOT/'generator/data/templates/slouch_pl24.json')
BASE=template_frames(TPL)
PALS={p['id']:p for p in json.loads((ROOT/'authored/palettes.json').read_text())['palettes']}
def hexrgb(s):
    s=s.lstrip('#')
    return tuple(int(s[i:i+2],16) for i in (0,2,4))
def lum(p): return p[0]*0.299+p[1]*0.587+p[2]*0.114

def opaque_rows(img):
    return [y for y,row in enumerate(img) if any(p[3] for p in row)]

def row_span(img,y):
    xs=[x for x,p in enumerate(img[y]) if p[3]]
    return (min(xs),max(xs)) if xs else None

def is_boundary(img,x,y):
    if not img[y][x][3]: return False
    h,w=len(img),len(img[0])
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
        xx,yy=x+dx,y+dy
        if xx<0 or yy<0 or xx>=w or yy>=h or not img[yy][xx][3]:
            return True
    return False
def transfer(donor,target,ramp):
    drows=opaque_rows(donor); trows=opaque_rows(target)
    dlums=sorted(lum(p) for row in donor for p in row if p[3])
    if not dlums: return [row[:] for row in target]
    def role(v):
        # 6-level source-value role, independent of donor RGB/hue.
        q=sum(1 for z in dlums if z<=v)/len(dlums)
        return min(len(ramp)-1,max(0,round(q*(len(ramp)-1))))
    out=[row[:] for row in target]
    for ti,ty in enumerate(trows):
        dy=drows[round(ti*(len(drows)-1)/max(1,len(trows)-1))]
        ds=row_span(donor,dy); ts=row_span(target,ty)
        if not ds or not ts: continue
        dx0,dx1=ds; tx0,tx1=ts
        for tx in range(tx0,tx1+1):
            if not target[ty][tx][3]: continue
            u=(tx-tx0)/max(1,tx1-tx0)
            dx=round(dx0+u*(dx1-dx0))
            dp=donor[dy][dx]
            if not dp[3]: continue
            ri=role(lum(dp))
            # Protect the authored target outline/contact edge.
            if is_boundary(target,tx,ty):
                ri=min(ri,1)
            out[ty][tx]=(*ramp[ri],target[ty][tx][3])
    return out

PALETTE_IDS=[
 'EVERYDAY_STONE_BLUE','CUTE_COCOA_GOLD','SPRING_SAGE_PETAL',
 'CELESTIAL_INDIGO_STAR','GOTHIC_WINE_ASH','AUTUMN_OCHRE_PLUM',
 'ARCANE_VIOLET_COPPER','LUXURY_JADE_BRONZE','EVERYDAY_STONE_BLUE'
]
records=[]
for i in range(9):
    donor_path=SRCROOT/f'material_{i:02d}.png'
    donor=read_rgba_png(donor_path)
    pal=PALS[PALETTE_IDS[i]]
    ramp=[hexrgb(x) for x in pal['ramps']['body']]
    frames={}
    for view,base in BASE.items():
        out=transfer(donor,base,ramp)
        assert alpha_cells(out)==alpha_cells(base)
        p=OUT/f'material_{i:02d}_{view}.png'
        write_rgba_png(p,out); frames[view]=str(p)
    records.append({'index':i,'donor':str(donor_path),'palette':PALETTE_IDS[i],'frames':frames})

(OUT/'manifest.json').write_text(json.dumps({'schema':'sf-structural-transfer-test/v1','records':records},indent=2)+'\n')

cw,ch=330,230
sheet=blank_image(cw*3,ch*3,(242,240,234,255))
for i,r in enumerate(records):
    donor=read_rgba_png(Path(r['donor']))
    front=read_rgba_png(Path(r['frames']['front']))
    c=i%3; rr=i//3; x0=c*cw; y0=rr*ch
    blit(sheet,nearest_scale(donor,8),x0+12,y0+38)
    blit(sheet,nearest_scale(front,8),x0+160,y0+22)
    draw_text(sheet,f'SF{i+1} SOURCE',x0+10,y0+8,scale=1)
    draw_text(sheet,'-> PL24 TRANSFER',x0+160,y0+8,scale=1)
write_rgba_png(OUT/'contact_source_vs_pl24_x8.png',sheet)
print('PASS structural transfer',len(records),'donors')
print(OUT/'contact_source_vs_pl24_x8.png')
