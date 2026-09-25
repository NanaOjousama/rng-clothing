#!/usr/bin/env python3
from pathlib import Path
import json, shutil, sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from generator.catalog_templates import load_template_for_family, load_family
from generator.taste_policy import evaluate_recipe
from generator.trucker_renderer import render_trucker
from v5.source.template_transfer import template_frames, alpha_cells
from v5.pngio import write_rgba_png, blank_image, blit, nearest_scale, draw_text

OUT=ROOT/'experiments/trucker_final_generator_ab_01'
VIEWS=('front','right','left','back')

SPECS=[
 ('C1_CLASSIC','common','FIELD_CANVAS_MOSS',
  dict(materialTreatment='plain',pattern='solid',trim='none',motif='none',motifPlacement='none',attachment='none',hardware='none')),
 ('C2_SUBTLE','common','EVERYDAY_STONE_BLUE',
  dict(materialTreatment='subtle',pattern='subtle',trim='subtle',motif='none',motifPlacement='none',attachment='none',hardware='none')),
 ('U1_TWOTONE','uncommon','WORKWEAR_DENIM_RUST',
  dict(materialTreatment='subtle',pattern='colorblock',trim='contrast',motif='none',motifPlacement='none',attachment='none',hardware='none')),

 ('U2_STRIPE','uncommon','STREET_TEAL_GRAPHITE',
  dict(materialTreatment='textured',pattern='stripe',trim='none',motif='none',motifPlacement='none',attachment='none',hardware='none')),
 ('R1_PATCH','rare','CEREMONIAL_CRIMSON_IVORY',
  dict(materialTreatment='textured',pattern='solid',trim='subtle',motif='small',motifPlacement='front_center',attachment='none',hardware='none')),
 ('E1_EMBLEM','epic','CELESTIAL_INDIGO_STAR',
  dict(materialTreatment='textured',pattern='subtle',trim='subtle',motif='emblem',motifPlacement='front_offset',attachment='none',hardware='none')),
]

def hexrgb(s):
    s=s.lstrip('#')
    return tuple(int(s[i:i+2],16) for i in (0,2,4))

def load_palettes():
    rows=json.loads((ROOT/'authored/palettes.json').read_text())['palettes']
    return {p['id']:p for p in rows}

def anchor_for(contract,view):
    a=contract.anchors.get(view,{})
    if view=='front' and 'motif_center' in a:
        return tuple(a['motif_center'])
    w,h=contract.size_for(view)
    return (w//2,h//3)

def render_family(family,label):
    contract=load_template_for_family(family)
    policy=load_family(family)
    base=template_frames(contract)
    pals=load_palettes()
    rows=[]
    family_dir=OUT/label
    family_dir.mkdir(parents=True,exist_ok=True)
    for name,rarity,pid,recipe in SPECS:
        rep=evaluate_recipe(recipe,rarity,policy)
        if not rep.valid:
            raise RuntimeError(f'{family}/{name}: illegal generator recipe {rep.errors}')
        p=pals[pid]
        body=[hexrgb(x) for x in p['ramps']['body']]
        mesh=[hexrgb(x) for x in p['ramps']['trim']]
        accent=[hexrgb(x) for x in p['ramps']['accent']]
        anchors={v:anchor_for(contract,v) for v in VIEWS}
        rendered=render_trucker(base,recipe,body,mesh,accent,anchors)
        d=family_dir/name
        d.mkdir()
        for v in VIEWS:
            if alpha_cells(rendered[v]) != alpha_cells(base[v]):
                raise RuntimeError(f'{family}/{name}/{v}: silhouette cell drift')
            write_rgba_png(d/f'{v}.png',rendered[v])
        rows.append({'name':name,'rarity':rarity,'palette':pid,'recipe':recipe,'tasteComplexity':rep.complexity,'frames':rendered})
    return contract,rows

def make_sheet(a_contract,a_rows,b_contract,b_rows):
    tile=152; gap=8; labelw=190; split=30
    W=labelw+8*(tile+gap)+split+20
    rowh=tile+38; H=78+len(a_rows)*rowh
    sheet=blank_image(W,H,(242,240,234,255))
    draw_text(sheet,'TRUCKER FINAL-LOOK GENERATOR A/B',8,8,scale=1)
    draw_text(sheet,'A32 FINAL',labelw+260,26,scale=1)
    draw_text(sheet,'B24 FINAL',labelw+4*(tile+gap)+split+260,26,scale=1)
    for j,v in enumerate(VIEWS):
        draw_text(sheet,v.upper(),labelw+j*(tile+gap)+50,48,scale=1)
        bx=labelw+4*(tile+gap)+split+j*(tile+gap)
        draw_text(sheet,v.upper(),bx+50,48,scale=1)
    y=72
    for i,row in enumerate(a_rows):
        draw_text(sheet,f"{row['rarity'].upper()} {row['name']}",8,y+12,scale=1)
        draw_text(sheet,row['palette'][:26],8,y+25,scale=1)
        for j,v in enumerate(VIEWS):
            a=nearest_scale(row['frames'][v],max(1,tile//len(row['frames'][v])))
            ax=labelw+j*(tile+gap)+(tile-len(a[0]))//2
            ay=y+(tile-len(a))//2
            blit(sheet,a,ax,ay)
            b=b_rows[i]['frames'][v]
            bb=nearest_scale(b,max(1,tile//len(b)))
            bx=labelw+4*(tile+gap)+split+j*(tile+gap)+(tile-len(bb[0]))//2
            by=y+(tile-len(bb))//2
            blit(sheet,bb,bx,by)
        y+=rowh
    p=OUT/'TRUCKER_FINAL_GENERATOR_A32_VS_B24.png'
    write_rgba_png(p,sheet)
    return p

def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    ac,ar=render_family('trucker_a32_qc','A32_FINAL')
    bc,br=render_family('trucker_b24_qc','B24_FINAL')
    sheet=make_sheet(ac,ar,bc,br)
    meta={
      'schema':'trucker-final-generator-ab/v1',
      'A':{'family':'trucker_a32_qc','size':list(ac.frame_size)},
      'B':{'family':'trucker_b24_qc','size':list(bc.frame_size)},
      'variants':[{'name':r['name'],'rarity':r['rarity'],'palette':r['palette'],'recipe':r['recipe']} for r in ar],
      'finishRules':['opaque production mesh','mesh value weave','solid front','strong border','front-only motif','back opening preserved'],
      'decision':'pending user visual choice'
    }
    (OUT/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print('PASS final-look generator A/B',len(ar),'variants each')
    print(sheet)

if __name__=='__main__':
    main()
