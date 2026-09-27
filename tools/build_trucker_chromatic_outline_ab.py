#!/usr/bin/env python3
from pathlib import Path
import json, sys, shutil
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from v5.pngio import read_rgba_png, write_rgba_png, blank_image, blit, nearest_scale, draw_text
from generator.vanilla_sprite_finish import apply_chromatic_outline

SRC=ROOT/'experiments/trucker_generator_batch_v1'; OUT=ROOT/'experiments/trucker_chromatic_outline_ab_01'
MASK=json.loads((ROOT/'authored/templates/trucker_rd22_pl26/component_masks.json').read_text())['views']
PAL={p['id']:p for p in json.loads((ROOT/'authored/palettes.json').read_text())['palettes']}
MAN=json.loads((SRC/'batch_manifest.json').read_text())['variants']; VIEWS=('front','right','left','back')
def hexrgb(s): s=s.lstrip('#'); return tuple(int(s[i:i+2],16) for i in (0,2,4))
rows=[]
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)
for spec in MAN:
    pid=spec['palette']; ramps0=PAL[pid]['ramps']; cmap=spec['componentRampMap']
    ramps={
      'front_panel':[hexrgb(x) for x in ramps0[cmap['panel']]],
      'rear_mesh':[hexrgb(x) for x in ramps0[cmap['mesh']]],
      'brim':[hexrgb(x) for x in ramps0[cmap['brim']]],
      'top_button':[hexrgb(x) for x in ramps0[cmap['button']]],
      'back_closure':[hexrgb(x) for x in ramps0[cmap['closure']]],
    }
    d=OUT/spec['id']; d.mkdir(); before={}; after={}
    for v in VIEWS:
        fr=read_rgba_png(SRC/spec['id']/f'{v}.png'); before[v]=fr
        # keep very dark pixels bordering the back opening/strong structural gaps untouched
        preserve=[]
        if v=='back':
            for y,row in enumerate(fr):
                for x,p in enumerate(row):
                    if p[3] and max(p[:3])<40 and 10<=x<=16 and 14<=y<=22: preserve.append((x,y))
        af=apply_chromatic_outline(fr,MASK[v],ramps,preserve=preserve); after[v]=af
        write_rgba_png(d/f'{v}.png',af)
    rows.append((spec,before,after))
scale=4; cell=26*scale; labelw=220; pairgap=16; top=54; rowh=cell+26
W=labelw+8*cell+pairgap+20; H=top+len(rows)*rowh
sheet=blank_image(W,H,(240,238,232,255)); draw_text(sheet,'TRUCKER OUTLINE A/B - CURRENT vs MEASURED VANILLA CHROMATIC',8,8,scale=1)
draw_text(sheet,'CURRENT',labelw+150,26,scale=1); draw_text(sheet,'CHROMATIC OUTLINE',labelw+4*cell+pairgap+130,26,scale=1)
for r,(spec,bef,aft) in enumerate(rows):
    y=top+r*rowh; draw_text(sheet,f"{spec['rarity'].upper()} {spec['id']}",8,y+8,scale=1)
    for i,v in enumerate(VIEWS):
        blit(sheet,nearest_scale(bef[v],scale),labelw+i*cell,y)
        blit(sheet,nearest_scale(aft[v],scale),labelw+4*cell+pairgap+i*cell,y)
write_rgba_png(OUT/'TRUCKER_CHROMATIC_OUTLINE_AB.png',sheet)
print(OUT/'TRUCKER_CHROMATIC_OUTLINE_AB.png')
