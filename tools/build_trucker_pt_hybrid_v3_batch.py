#!/usr/bin/env python3
from pathlib import Path
import json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from generator.catalog_templates import load_template_for_family
from generator.trucker_pt_hybrid_renderer import render
from v5.source.template_transfer import template_frames
from v5.pngio import write_rgba_png,blank_image,blit,nearest_scale,draw_text

OUT=ROOT/'experiments/trucker_pt_hybrid_v3_01'; VIEWS=('front','right','left','back')

def hx(s):
 s=s.lstrip('#');return tuple(int(s[i:i+2],16) for i in (0,2,4))

def pals():return {p['id']:p for p in json.load(open(ROOT/'authored/palettes.json'))['palettes']}

def pick(p,ramp,idx):return hx(p['ramps'][ramp][idx])

# Richer styling is intentionally restored. Pattern/contrast is bound to physical zones.
SPECS=[
 ('CLASSIC_MOSS','common','FIELD_CANVAS_MOSS','solid',0.05,0.00,'none',0),
 ('STONE_BLUE','common','EVERYDAY_STONE_BLUE','solid',0.06,0.00,'none',0),
 ('DENIM_RUST','uncommon','WORKWEAR_DENIM_RUST','solid',0.09,0.00,'none',0),
 ('TEAL_PINSTRIPE','uncommon','STREET_TEAL_GRAPHITE','pinstripe',0.08,0.11,'none',0),
 ('COASTAL_TWOTONE','rare','COASTAL_SEAFOAM_CORAL','solid',0.11,0.00,'small',1),
 ('CRIMSON_PATCH','rare','CEREMONIAL_CRIMSON_IVORY','check',0.10,0.10,'small',0),
 ('INDIGO_EMBLEM','epic','CELESTIAL_INDIGO_STAR','pinstripe',0.13,0.13,'emblem',0),
 ('AUTUMN_CHECK','epic','AUTUMN_OCHRE_PLUM','check',0.12,0.14,'emblem',1),
]

def alpha_bytes(fr):return bytes(p[3] for row in fr for p in row)

def main():
 if OUT.exists():shutil.rmtree(OUT)
 OUT.mkdir(parents=True)
 c=load_template_for_family('trucker');base=template_frames(c);P=pals();built=[]
 for name,rarity,pid,pattern,mesh_s,pat_s,motif,moff in SPECS:
  p=P[pid]
  body=pick(p,'body',3); rear=pick(p,'trim',3); brim=pick(p,'accent',2); accent=pick(p,'accent',5)
  # Common keeps brim quieter; higher rarities get stronger physical contrast.
  if rarity=='common': brim=pick(p,'body',1)
  elif rarity=='uncommon': brim=pick(p,'accent',1)
  final=render(base,body=body,rear=rear,brim=brim,accent=accent,pattern=pattern,
               mesh_strength=mesh_s,pattern_strength=pat_s,motif=motif,motif_offset=moff)
  d=OUT/name;d.mkdir()
  for v in VIEWS:
   if alpha_bytes(final[v])!=alpha_bytes(base[v]):raise RuntimeError(f'{name}/{v}: vanilla alpha drift')
   write_rgba_png(d/f'{v}.png',final[v])
  built.append(dict(name=name,rarity=rarity,palette=pid,pattern=pattern,meshStrength=mesh_s,patternStrength=pat_s,motif=motif,frames=final))

 scale=9;tile=180;gap=12;labelw=215;top=86;rowh=tile+44
 W=labelw+4*(tile+gap)+20;H=top+(len(built)+1)*rowh+12
 sheet=blank_image(W,H,(242,240,234,255))
 draw_text(sheet,'TRUCKER V3 - RICH PHOTO TAILOR HYBRID',8,8,scale=1)
 draw_text(sheet,'vanilla #16 geometry + PT shading math + physical-region styling',8,24,scale=1)
 draw_text(sheet,'contrast/pattern/mesh restored; no generic full-width band heuristic',8,40,scale=1)
 for j,v in enumerate(VIEWS):draw_text(sheet,v.upper(),labelw+j*(tile+gap)+62,64,scale=1)
 y=top;draw_text(sheet,'VANILLA #16',8,y+10,scale=1);draw_text(sheet,'GEOMETRY AUTHORITY',8,y+24,scale=1)
 for j,v in enumerate(VIEWS):blit(sheet,nearest_scale(base[v],scale),labelw+j*(tile+gap),y)
 y+=rowh
 for r in built:
  draw_text(sheet,f"{r['rarity'].upper()} {r['name']}",8,y+8,scale=1)
  draw_text(sheet,r['palette'][:28],8,y+22,scale=1);draw_text(sheet,f"{r['pattern']} / {r['motif']}",8,y+36,scale=1)
  for j,v in enumerate(VIEWS):blit(sheet,nearest_scale(r['frames'][v],scale),labelw+j*(tile+gap),y)
  y+=rowh
 contact=OUT/'TRUCKER_PT_HYBRID_V3_CONTACT.png';write_rgba_png(contact,sheet)
 meta={'schema':'trucker-pt-hybrid/v3','family':'trucker','geometryAuthority':'Stardew Valley vanilla Trucker Hat #16','photoTailorIntegrated':True,
       'photoTailorRole':'renderer shading/value projection math per physical semantic region','regionRules':{'front':'solid crown only; no mesh','sides':'solid front panel + rear mesh + explicit visor','back':'rear mesh + explicit lower closure'},
       'variants':[{k:r[k] for k in ('name','rarity','palette','pattern','meshStrength','patternStrength','motif')} for r in built]}
 (OUT/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
 print('PASS',len(built),'rich PT-hybrid truckers');print('all 32 frames preserve vanilla #16 alpha bytes');print(contact)
if __name__=='__main__':main()
