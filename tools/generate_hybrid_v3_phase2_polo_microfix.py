#!/usr/bin/env python3
"""Focused Coastal Knit Polo directional cleanup; no batch regeneration."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from generator.hybrid_v3.builder import CanonicalGarmentBuilder
from generator.hybrid_v3.compiler import PixelGrammarCompiler
from generator.hybrid_v3.compiler.stage_trace import verify_frozen_backend
from generator.hybrid_v3.projector import DirectionalProjector
from generator.png_utils import blank_image, blit, draw_rect, draw_text, nearest_scale, read_rgba_png, write_rgba_png
from tools.generate_controlled_grammar_hd_adapter_repair import _farmer_composite

TARGET=ROOT/'output/hybrid-v3-phase2/03-coastal-knit-polo'
MICRO=ROOT/'output/hybrid-v3-phase2/polo-microfix'
PACK_SHIRT=ROOT/'test-packs/fashionsense/RNG-Clothing-Hybrid-V3-Phase2/Shirts/CoastalKnitPolo/shirt.png'
COMPARE=ROOT/'output/comparisons/HYBRID_V3_PHASE2_COASTAL_POLO_MICROFIX_QC.png'
FARMER=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/farmer_base.png')
HAIR=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/hairstyles.png')
DIRECTIONS=('front','right','back','left'); OFFSETS={'front':0,'right':16,'left':32,'back':48}
BG=(232,226,217,255); PANEL=(205,197,186,255); INK=(39,37,36,255); BORDER=(67,61,57,255); ACC=(46,116,125,255)


def dump(path,value): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,indent=2)+"\n",encoding='utf-8')
def frames(atlas): return {d:[list(row) for row in atlas[OFFSETS[d]:OFFSETS[d]+16]] for d in DIRECTIONS}
def crop(frame,x,y,w,h): return [list(row[x:x+w]) for row in frame[y:y+h]]
def tile(canvas,image,x,y,border=ACC):
    draw_rect(canvas,x-2,y-2,len(image[0])+4,len(image)+4,border); draw_rect(canvas,x-1,y-1,len(image[0])+2,len(image)+2,PANEL); blit(canvas,image,x,y)


def farmer_sheet(title, farmer):
    canvas=blank_image(300,166,BG); draw_text(canvas,title,8,7,color=INK)
    for i,d in enumerate(DIRECTIONS):
        x=8+i*72; draw_text(canvas,d.upper(),x,20,color=ACC); tile(canvas,farmer[d],x,34)
    return canvas


def isolated_sheet(title, garment_frames):
    canvas=blank_image(548,166,BG); draw_text(canvas,title,8,7,color=INK)
    for i,d in enumerate(DIRECTIONS):
        x=8+i*134; draw_text(canvas,d.upper(),x,20,color=ACC); tile(canvas,nearest_scale(garment_frames[d],8),x,34)
    return canvas


def qc_sheet(before,after,before_farmer,after_farmer):
    checks=(
        ('BACK COLLAR', 'back', (3,0,10,5)),
        ('RIGHT COLLAR', 'right', (4,0,9,6)),
        ('RIGHT TORSO MIDDLE', 'right', (4,2,9,8)),
    )
    canvas=blank_image(720,500,BG); draw_text(canvas,'COASTAL KNIT POLO MICRO-FIX | BEFORE / AFTER | 8X',8,7,color=INK)
    for row,(label,d,(x,y,w,h)) in enumerate(checks):
        y0=32+row*145; draw_text(canvas,label,8,y0,color=INK); draw_text(canvas,'BEFORE',120,y0,color=BORDER); draw_text(canvas,'AFTER',300,y0,color=ACC)
        tile(canvas,nearest_scale(crop(before[d],x,y,w,h),8),120,y0+18,BORDER)
        tile(canvas,nearest_scale(crop(after[d],x,y,w,h),8),300,y0+18,ACC)
        tile(canvas,before_farmer[d],490,y0+8,BORDER); tile(canvas,after_farmer[d],560,y0+8,ACC)
    return canvas


def main():
    if verify_frozen_backend()['status']!='PASS': raise SystemExit('frozen backend mismatch')
    MICRO.mkdir(parents=True,exist_ok=True)
    before_path=MICRO/'before-shirt.png'
    if before_path.exists(): before_atlas=read_rgba_png(before_path)['pixels']
    else:
        before_atlas=read_rgba_png(TARGET/'shirt.png')['pixels']; write_rgba_png(before_path,before_atlas)
    before=frames(before_atlas)
    model=CanonicalGarmentBuilder().build(family='POLO_SHIRT',design_intent='POLO_CLASSIC',fit_profile='MASC_TAILORED',root_seed=320203,rarity_budget='PHASE2_NEUTRAL_DEFAULT')
    projections=DirectionalProjector().project(model)
    render=PixelGrammarCompiler().compile(model,projections,palette_story='COASTAL_MIST')
    after=render.frames
    if before['front']!=after['front']: raise SystemExit('front frame changed; micro-fix aborted')
    changes={d:[[x,y] for y in range(16) for x in range(16) if before[d][y][x]!=after[d][y][x]] for d in DIRECTIONS}
    expected={'front':0,'right':10,'back':12,'left':10}
    if {d:len(v) for d,v in changes.items()}!=expected: raise SystemExit(f'unexpected change scope {changes}')
    body=read_rgba_png(FARMER)['pixels']; hair=read_rgba_png(HAIR)['pixels']
    before_farmer={d:_farmer_composite(body,hair,before[d],d) for d in DIRECTIONS}
    after_farmer={d:_farmer_composite(body,hair,after[d],d) for d in DIRECTIONS}
    review_path=MICRO/'visual-review.json'
    review=json.loads(review_path.read_text(encoding='utf-8')) if review_path.exists() else {'status':'PENDING_MICROFIX_REVIEW','authority':'focused Farmer composite'}
    write_rgba_png(MICRO/'after-shirt.png',render.texture); write_rgba_png(TARGET/'shirt.png',render.texture); write_rgba_png(PACK_SHIRT,render.texture)
    write_rgba_png(MICRO/'farmer-before.png',farmer_sheet('COASTAL KNIT POLO | BEFORE',before_farmer))
    write_rgba_png(MICRO/'farmer-after.png',farmer_sheet('COASTAL KNIT POLO | AFTER',after_farmer))
    write_rgba_png(TARGET/'farmer-directions.png',farmer_sheet('COASTAL KNIT POLO | MICRO-FIXED',after_farmer))
    write_rgba_png(MICRO/'isolated-after-8x.png',isolated_sheet('COASTAL KNIT POLO | AFTER 8X',after))
    write_rgba_png(TARGET/'isolated-directions-8x.png',isolated_sheet('COASTAL KNIT POLO | MICRO-FIXED 8X',after))
    qc=qc_sheet(before,after,before_farmer,after_farmer); write_rgba_png(MICRO/'before-after-8x-qc.png',qc); write_rgba_png(COMPARE,qc)
    dump(TARGET/'pixel-grammar-map.json',render.pixel_grammar_map); dump(TARGET/'semantic-pixel-regions.json',render.semantic_regions)
    validation=render.validation; validation['farmerVisualReview']=review
    if review['status']!='PASS': validation['status']='PENDING_OR_FAIL'
    dump(TARGET/'validation.json',validation)
    dump(TARGET/'stage-trace.json',{'stages':render.stage_trace+['polo_medium_collar_directional_microfix'],'scope':'Coastal Knit Polo only','frontFramePreserved':True})
    note={
        'status':review['status'],'garment':'Coastal Knit Polo','frontFrameBytePreserved':True,
        'changedCellCounts':{d:len(v) for d,v in changes.items()},'changedCoordinates':changes,
        'regions':{
            'backCollar':'Moved explicit folded band from logical y=1 to y=0 at x=5..10; y=1 x=5..10 restored to a quiet primary-knit light/base/shadow plane.',
            'sideCollar':'Replaced the two-cell signal over inherited carrier chatter with compact five-cell folded wedges in each side direction.',
            'sideTorso':'Normalized the local upper-middle side knit plane in logical rows 1..5; only ten resulting pixels per side changed after polish.'
        },
        'validation':render.validation,'nativeSleeves':True,'customSleeves':False
    }
    dump(MICRO/'microfix-note.json',note); print(json.dumps(note,indent=2))

if __name__=='__main__': main()
