#!/usr/bin/env python3
from pathlib import Path
import json, shutil, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from generator.catalog_templates import load_template_for_family, load_family
from generator.cap_photo_tailor_pipeline import render_cap_family
from generator import hat_hybrid_enhancements as hybrid
from generator.taste_policy import evaluate_recipe
from v5.source.template_transfer import template_frames
from v5.pngio import write_rgba_png, blank_image, blit, nearest_scale, draw_text

OUT=ROOT/'experiments/trucker_pt_hybrid_v2_01'
VIEWS=('front','right','left','back')
# Clean test: no generic stripes/colorblocks/full-width trim bands.
SPECS=[
 ('FOREST','common','FIELD_CANVAS_MOSS',(73,126,88),dict(materialTreatment='plain',pattern='solid',trim='none',motif='none',motifPlacement='none',attachment='none',hardware='none')),
 ('STONE','common','EVERYDAY_STONE_BLUE',(94,104,122),dict(materialTreatment='plain',pattern='solid',trim='none',motif='none',motifPlacement='none',attachment='none',hardware='none')),
 ('DENIM','uncommon','WORKWEAR_DENIM_RUST',(78,101,121),dict(materialTreatment='textured',pattern='solid',trim='none',motif='none',motifPlacement='none',attachment='none',hardware='none')),
 ('TEAL','uncommon','STREET_TEAL_GRAPHITE',(67,119,125),dict(materialTreatment='textured',pattern='solid',trim='none',motif='none',motifPlacement='none',attachment='none',hardware='none')),
 ('CRIMSON_PATCH','rare','CEREMONIAL_CRIMSON_IVORY',(151,67,70),dict(materialTreatment='textured',pattern='solid',trim='none',motif='small',motifPlacement='front_offset',attachment='none',hardware='none')),
 ('INDIGO_EMBLEM','epic','CELESTIAL_INDIGO_STAR',(74,76,143),dict(materialTreatment='textured',pattern='solid',trim='none',motif='emblem',motifPlacement='front_center',attachment='none',hardware='none')),
]

def alpha_bytes(rows): return bytes(p[3] for row in rows for p in row)

def main():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    contract=load_template_for_family('trucker'); policy=load_family('trucker'); base=template_frames(contract)
    built=[]
    for name,rarity,palette_id,base_color,recipe in SPECS:
        taste=evaluate_recipe(recipe,rarity,policy)
        if not taste.valid: raise RuntimeError(f'{name}: illegal recipe {taste.errors}')
        # Stage 1: direct Photo Tailor PreviewHat/Recolor port on locked vanilla geometry.
        pt,pt_report=render_cap_family(base,'trucker',[base_color],'solid')
        if not pt_report.valid or not pt_report.photo_tailor_port_used:
            raise RuntimeError(f'{name}: Photo Tailor port rejected {pt_report.errors}')
        # Stage 2: bounded hybrid feature layer. Outline/alpha safety gate remains authoritative.
        final,hrep=hybrid.enhance_frames(pt,'trucker',recipe,rarity)
        d=OUT/name; d.mkdir()
        for v in VIEWS:
            if alpha_bytes(final[v]) != alpha_bytes(base[v]): raise RuntimeError(f'{name}/{v}: alpha bytes drift')
            write_rgba_png(d/f'{v}.png',final[v])
        built.append({'name':name,'rarity':rarity,'palette':palette_id,'recipe':recipe,'pt':pt_report.__dict__,'hybrid':hrep.__dict__,'frames':final})

    scale=9; tile=180; gap=12; labelw=205; top=84; rowh=tile+42
    W=labelw+4*(tile+gap)+24; H=top+(len(built)+1)*rowh+10
    sheet=blank_image(W,H,(242,240,234,255))
    draw_text(sheet,'TRUCKER V2 - PHOTO TAILOR INTEGRATED HYBRID',8,8,scale=1)
    draw_text(sheet,'vanilla #16 geometry -> PT shading/projection -> bounded hybrid motifs',8,24,scale=1)
    draw_text(sheet,'no stripe/colorblock/full-width trim rules in this test',8,40,scale=1)
    for j,v in enumerate(VIEWS): draw_text(sheet,v.upper(),labelw+j*(tile+gap)+64,62,scale=1)
    y=top
    draw_text(sheet,'VANILLA #16',8,y+12,scale=1); draw_text(sheet,'GEOMETRY AUTHORITY',8,y+26,scale=1)
    for j,v in enumerate(VIEWS): blit(sheet,nearest_scale(base[v],scale),labelw+j*(tile+gap),y)
    y+=rowh
    for r in built:
        draw_text(sheet,f"{r['rarity'].upper()} {r['name']}",8,y+10,scale=1)
        draw_text(sheet,'PT + HYBRID',8,y+24,scale=1)
        draw_text(sheet,f"delta={r['hybrid']['changed_pixels']}",8,y+38,scale=1)
        for j,v in enumerate(VIEWS): blit(sheet,nearest_scale(r['frames'][v],scale),labelw+j*(tile+gap),y)
        y+=rowh
    contact=OUT/'TRUCKER_PT_HYBRID_V2_CONTACT.png'; write_rgba_png(contact,sheet)
    meta={'schema':'trucker-pt-hybrid/v2','family':'trucker','geometryAuthority':'Stardew Valley vanilla Trucker Hat #16','photoTailorIntegrated':True,'pipeline':['vanilla16 locked geometry','generator.cap_photo_tailor_pipeline / direct Photo Tailor port','generator.hat_hybrid_enhancements bounded layer'],'excludedForThisBatch':['stripe','colorblock','contrast/wrap trim'],'variants':[{k:r[k] for k in ('name','rarity','palette','recipe','pt','hybrid')} for r in built]}
    (OUT/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print('PASS',len(built),'Photo-Tailor-integrated hybrid truckers')
    print('all 24 frames preserve vanilla #16 alpha bytes')
    print(contact)
if __name__=='__main__': main()
