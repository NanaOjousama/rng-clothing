#!/usr/bin/env python3
from __future__ import annotations
import json, sys, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from v5.pngio import read_rgba_png, write_rgba_png, blank_image, blit, nearest_scale, draw_text
from v5.source.template_transfer import load_contract, template_frames, alpha_cells, ContractError
from generator.catalog_templates import load_family
from generator.taste_policy import evaluate_recipe

OUT=ROOT/'experiments/trucker_generator_batch_v1'
VIEWS=('front','right','left','back')
MOTIFS=ROOT/'authored/motifs/slouch_beanie_v1/assets'

SPECS=[
 ('C1_FIELD_MOSS','common','FIELD_CANVAS_MOSS',dict(materialTreatment='plain',pattern='solid',trim='none',motif='none',motifPlacement='none',attachment='none',hardware='none'),dict(panel='body',mesh='trim',brim='body',button='hardware',closure='trim')),
 ('C2_STONE_BLUE','common','EVERYDAY_STONE_BLUE',dict(materialTreatment='subtle',pattern='subtle',trim='subtle',motif='none',motifPlacement='none',attachment='none',hardware='none'),dict(panel='body',mesh='trim',brim='trim',button='hardware',closure='hardware')),
 ('U1_DENIM_RUST','uncommon','WORKWEAR_DENIM_RUST',dict(materialTreatment='subtle',pattern='colorblock',trim='contrast',motif='none',motifPlacement='none',attachment='none',hardware='none'),dict(panel='trim',mesh='body',brim='accent',button='hardware',closure='accent')),
 ('U2_TEAL_GRAPHITE','uncommon','STREET_TEAL_GRAPHITE',dict(materialTreatment='textured',pattern='stripe',trim='none',motif='none',motifPlacement='none',attachment='none',hardware='none'),dict(panel='body',mesh='trim',brim='accent',button='hardware',closure='hardware')),
 ('R1_CRIMSON_PATCH','rare','CEREMONIAL_CRIMSON_IVORY',dict(materialTreatment='textured',pattern='solid',trim='subtle',motif='small',motifPlacement='front_center',attachment='none',hardware='none'),dict(panel='body',mesh='trim',brim='accent',button='hardware',closure='hardware',motif_asset='tiny_label_tag')),
 ('E1_INDIGO_STAR','epic','CELESTIAL_INDIGO_STAR',dict(materialTreatment='textured',pattern='subtle',trim='subtle',motif='emblem',motifPlacement='front_offset',attachment='none',hardware='none'),dict(panel='body',mesh='trim',brim='accent',button='hardware',closure='hardware',motif_asset='star')),
]

def hexrgb(s):
 s=s.lstrip('#'); return tuple(int(s[i:i+2],16) for i in (0,2,4))

def lum(p): return p[0]*299+p[1]*587+p[2]*114

def load_masks():
 d=json.loads((ROOT/'authored/templates/trucker_rd22_pl26/component_masks.json').read_text())
 return {v:{c:{tuple(p) for p in cells} for c,cells in d['views'][v].items()} for v in VIEWS}

def rank_map(frame,cells,ramp):
 vals=sorted({lum(frame[y][x]) for x,y in cells if frame[y][x][3]})
 out=[row[:] for row in frame]
 for x,y in cells:
  p=frame[y][x]
  if not p[3]: continue
  i=min(range(len(vals)),key=lambda j:abs(vals[j]-lum(p)))
  ri=round(i*(len(ramp)-1)/max(1,len(vals)-1))
  out[y][x]=(*ramp[ri],p[3])
 return out

def shade_front_brim_like_side(frame,cells,ramp):
    """Front visor treatment modeled on vanilla Stardew hat #16.

    Preserve this trucker's alpha/silhouette, but use the vanilla front-brim
    value grammar: chromatic dark edge, lighter upper/front plane, darker
    underside, and darkest tiny lower tips.
    """
    out=[row[:] for row in frame]
    by_row={}
    for x,y in cells:
        by_row.setdefault(y,[]).append(x)
    if not by_row:
        return out
    ys=sorted(by_row)
    top=ys[0]
    bottom=ys[-1]
    n=len(ramp)
    def ri(i): return max(0,min(n-1,i))
    for y in ys:
        xs=sorted(by_row[y]); lo,hi=min(xs),max(xs); span=max(1,hi-lo)
        for x in xs:
            edge=min(x-lo,hi-x)
            # Vanilla #16 front brim: brighter front plane with darker chromatic
            # rim, then a substantially darker underside.
            if y==top:
                idx = 1 if edge==0 else (2 if edge==1 else (4 if edge<=3 else 5))
            elif y==top+1:
                idx = 0 if edge==0 else (1 if edge==1 else (3 if edge<=3 else 4))
            elif y==top+2:
                idx = 0 if edge<=1 else (1 if edge<=3 else 2)
            elif y==bottom:
                idx = 0
            else:
                idx = 0 if edge<=1 else 1
            out[y][x]=(*ramp[ri(idx)],frame[y][x][3])
    return out

def motif_cells(name):
 im=read_rgba_png(MOTIFS/f'{name}.png')
 pts=[(x,y,p) for y,row in enumerate(im) for x,p in enumerate(row) if p[3]]
 minx=min(x for x,_,_ in pts); miny=min(y for _,y,_ in pts)
 pts=[(x-minx,y-miny,p) for x,y,p in pts]
 w=max(x for x,_,_ in pts)+1; h=max(y for _,y,_ in pts)+1
 return pts,w,h

def apply_front_motif(frame,panel_cells,name,ramp,anchor):
 pts,w,h=motif_cells(name); ax,ay=anchor
 preferred=(ax-w//2,ay-h//2)
 pos=None
 for radius in range(0,8):
  for dy in range(-radius,radius+1):
   for dx in range(-radius,radius+1):
    if max(abs(dx),abs(dy))!=radius: continue
    ox,oy=preferred[0]+dx,preferred[1]+dy
    if all((ox+x,oy+y) in panel_cells for x,y,_ in pts): pos=(ox,oy); break
   if pos: break
  if pos: break
 if not pos: raise ContractError(f'motif {name} cannot fit front panel')
 out=[row[:] for row in frame]; values=sorted({lum(p) for _,_,p in pts})
 for x,y,p in pts:
  idx=min(range(len(values)),key=lambda j:abs(values[j]-lum(p)))
  ri=round(idx*(len(ramp)-1)/max(1,len(values)-1))
  tx,ty=pos[0]+x,pos[1]+y; out[ty][tx]=(*ramp[ri],frame[ty][tx][3])
 return out

def render_variant(base,masks,pal,spec):
 ramps={k:[hexrgb(x) for x in v] for k,v in pal['ramps'].items()}
 frames={}
 cmap={'front_panel':spec['panel'],'rear_mesh':spec['mesh'],'brim':spec['brim'],'top_button':spec['button'],'back_closure':spec['closure']}
 for v in VIEWS:
  fr=[row[:] for row in base[v]]
  for comp,ramp_name in cmap.items():
   if v=='front' and comp=='brim':
    fr=shade_front_brim_like_side(fr,masks[v][comp],ramps[ramp_name])
   else:
    fr=rank_map(fr,masks[v][comp],ramps[ramp_name])
  if v=='front' and spec.get('motif_asset'):
   fr=apply_front_motif(fr,masks[v]['front_panel'],spec['motif_asset'],ramps['accent'],tuple(TPL.anchors['front']['motif_center']))
  if alpha_cells(fr)!=alpha_cells(base[v]): raise ContractError(f'{v}: alpha changed')
  frames[v]=fr
 return frames

def contact(rows):
 scale=5; fw=26*scale; labelw=210; top=48; rowh=fw+28
 W=labelw+4*fw+36; H=top+len(rows)*rowh
 out=blank_image(W,H,(240,238,232,255)); draw_text(out,'TRUCKER GENERATOR BATCH V1',8,8,scale=1)
 for i,v in enumerate(VIEWS): draw_text(out,v.upper(),labelw+i*fw+46,28,scale=1)
 for r,row in enumerate(rows):
  y=top+r*rowh; draw_text(out,f"{row['rarity'].upper()} {row['id']}",8,y+9,scale=1); draw_text(out,row['palette'],8,y+22,scale=1)
  for i,v in enumerate(VIEWS): blit(out,nearest_scale(row['frames'][v],scale),labelw+i*fw,y)
 return out

TPL=load_contract(ROOT/'generator/data/templates/trucker.json')
POL=load_family('trucker'); BASE=template_frames(TPL); MASKS=load_masks(); PALS={p['id']:p for p in json.loads((ROOT/'authored/palettes.json').read_text())['palettes']}

def main():
 if OUT.exists(): shutil.rmtree(OUT)
 OUT.mkdir(parents=True)
 rows=[]; manifest=[]
 for ident,rarity,pid,recipe,spec in SPECS:
  rep=evaluate_recipe(recipe,rarity,POL)
  if not rep.valid: raise RuntimeError(f'{ident} rejected: {rep.errors}')
  frames=render_variant(BASE,MASKS,PALS[pid],spec); d=OUT/ident; d.mkdir()
  for v in VIEWS: write_rgba_png(d/f'{v}.png',frames[v])
  rows.append({'id':ident,'rarity':rarity,'palette':pid,'frames':frames})
  manifest.append({'id':ident,'rarity':rarity,'palette':pid,'recipe':recipe,'componentRampMap':spec})
 write_rgba_png(OUT/'TRUCKER_GENERATOR_BATCH_V1.png',contact(rows))
 (OUT/'batch_manifest.json').write_text(json.dumps({'schema':'trucker-generator-batch/v1','template':'trucker','count':len(rows),'variants':manifest},indent=2)+'\n')
 print('PASS trucker generator batch',len(rows),'variants',len(rows)*4,'frames')
 print(OUT/'TRUCKER_GENERATOR_BATCH_V1.png')
if __name__=='__main__': main()
