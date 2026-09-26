#!/usr/bin/env python3
from pathlib import Path
import json, shutil, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from generator.catalog_templates import load_template_for_family, load_family
from generator.taste_policy import evaluate_recipe
from generator.trucker_renderer import render_trucker
from v5.source.template_transfer import template_frames
from v5.pngio import write_rgba_png, blank_image, blit, nearest_scale, draw_text

OUT=ROOT/'experiments/trucker_vanilla16_production_01'
VIEWS=('front','right','left','back')
SPECS=[
 ('CLASSIC_MOSS','common','FIELD_CANVAS_MOSS',dict(materialTreatment='plain',pattern='solid',trim='none',motif='none',motifPlacement='none',attachment='none',hardware='none')),
 ('STONE_BLUE','common','EVERYDAY_STONE_BLUE',dict(materialTreatment='subtle',pattern='subtle',trim='subtle',motif='none',motifPlacement='none',attachment='none',hardware='none')),
 ('DENIM_RUST','uncommon','WORKWEAR_DENIM_RUST',dict(materialTreatment='subtle',pattern='colorblock',trim='contrast',motif='none',motifPlacement='none',attachment='none',hardware='none')),
 ('TEAL_STRIPE','uncommon','STREET_TEAL_GRAPHITE',dict(materialTreatment='textured',pattern='stripe',trim='none',motif='none',motifPlacement='none',attachment='none',hardware='none')),
 ('CRIMSON_PATCH','rare','CEREMONIAL_CRIMSON_IVORY',dict(materialTreatment='textured',pattern='solid',trim='subtle',motif='small',motifPlacement='front_center',attachment='none',hardware='none')),
 ('INDIGO_EMBLEM','epic','CELESTIAL_INDIGO_STAR',dict(materialTreatment='textured',pattern='subtle',trim='subtle',motif='emblem',motifPlacement='front_center',attachment='none',hardware='none')),
]

def hexrgb(s):
    s=s.lstrip('#'); return tuple(int(s[i:i+2],16) for i in (0,2,4))

def palettes():
    rows=json.loads((ROOT/'authored/palettes.json').read_text())['palettes']
    return {p['id']:p for p in rows}

def alpha_bytes(rows):
    return bytes(p[3] for row in rows for p in row)

def anchor(contract,view):
    a=contract.anchors.get(view,{})
    if view=='front' and 'motif_center' in a: return tuple(a['motif_center'])
    w,h=contract.size_for(view); return (w//2,h//3)

def main():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    contract=load_template_for_family('trucker'); policy=load_family('trucker'); base=template_frames(contract); pals=palettes()
    rows=[]
    for name,rarity,pid,recipe in SPECS:
        rep=evaluate_recipe(recipe,rarity,policy)
        if not rep.valid: raise RuntimeError(f'{name}: illegal recipe {rep.errors}')
        p=pals[pid]
        body=[hexrgb(x) for x in p['ramps']['body']]; mesh=[hexrgb(x) for x in p['ramps']['trim']]; accent=[hexrgb(x) for x in p['ramps']['accent']]
        anchors={v:anchor(contract,v) for v in VIEWS}
        rendered=render_trucker(base,recipe,body,mesh,accent,anchors,preserve_alpha=True)
        d=OUT/name; d.mkdir()
        for v in VIEWS:
            if alpha_bytes(rendered[v]) != alpha_bytes(base[v]):
                raise RuntimeError(f'{name}/{v}: vanilla alpha bytes changed')
            write_rgba_png(d/f'{v}.png',rendered[v])
        rows.append({'name':name,'rarity':rarity,'palette':pid,'recipe':recipe,'complexity':rep.complexity,'frames':rendered})

    scale=8; tile=20*scale; labelw=190; gap=12; top=76; rowh=tile+42
    W=labelw+4*(tile+gap)+20; H=top+(len(rows)+1)*rowh+12
    sheet=blank_image(W,H,(242,240,234,255))
    draw_text(sheet,'OFFICIAL TRUCKER - VANILLA #16 GEOMETRY',8,8,scale=1)
    draw_text(sheet,'vanilla geometry locked; generator changes styling only',8,24,scale=1)
    for j,v in enumerate(VIEWS): draw_text(sheet,v.upper(),labelw+j*(tile+gap)+50,52,scale=1)
    # authority row first
    y=top; draw_text(sheet,'VANILLA #16 BASE',8,y+12,scale=1); draw_text(sheet,'GEOMETRY AUTHORITY',8,y+26,scale=1)
    for j,v in enumerate(VIEWS):
        big=nearest_scale(base[v],scale); blit(sheet,big,labelw+j*(tile+gap),y)
    y+=rowh
    for row in rows:
        draw_text(sheet,f"{row['rarity'].upper()} {row['name']}",8,y+10,scale=1)
        draw_text(sheet,row['palette'][:27],8,y+24,scale=1)
        for j,v in enumerate(VIEWS):
            big=nearest_scale(row['frames'][v],scale); blit(sheet,big,labelw+j*(tile+gap),y)
        y+=rowh
    sheet_path=OUT/'TRUCKER_VANILLA16_PRODUCTION_CONTACT.png'; write_rgba_png(sheet_path,sheet)
    meta={'schema':'trucker-vanilla16-production/v1','family':'trucker','geometryAuthority':'Stardew Valley vanilla Trucker Hat #16','frameSize':[20,20],'photoTailorUsed':False,'variants':[{'name':r['name'],'rarity':r['rarity'],'palette':r['palette'],'recipe':r['recipe']} for r in rows]}
    (OUT/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print('PASS official trucker batch',len(rows),'variants')
    print('alpha bytes preserved for all 24 generated frames')
    print(sheet_path)
if __name__=='__main__': main()
