#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path('/run/media/deck/USD00/RNG_clothing')
sys.path.insert(0,str(ROOT))
from v5.pngio import blank_image, write_rgba_png
ASSETS=ROOT/'authored/motifs/slouch_beanie_v1/assets'
MAN=ROOT/'authored/motifs/slouch_beanie_v1/manifest.json'
MATRIX=ROOT/'generator/data/headwear/slouch_beanie_roll_matrix.json'
T=(0,0,0,0); O=(38,31,27,255); M=(167,123,82,255); L=(224,188,139,255); A=(154,84,78,255)
PAL={'.':T,'O':O,'M':M,'L':L,'A':A}
def art(rows):
    img=blank_image(max(map(len,rows)),len(rows))
    for y,row in enumerate(rows):
        for x,ch in enumerate(row):
            if ch!='.': img[y][x]=PAL[ch]
    return img
SPECS={
 'cuff_patch_small':('MICRO_ACCENT',["OOO","OMO"]),
 'side_bow_small':('MICRO_ACCENT',["O.O.O",".OMO.","..O.."]),
 'diagonal_wrap_band':('MICRO_ACCENT',["L......",".L.....","..L...."]),
 'tiny_label_tag':('MICRO_ACCENT',["OO","OL","OO"]),
}
man=json.loads(MAN.read_text())
for name,(cat,rows) in SPECS.items():
    img=art(rows); path=ASSETS/f'{name}.png'; write_rgba_png(path,img)
    man['assets'][name]={'category':cat,'path':str(path.relative_to(ROOT)),'size':[len(img[0]),len(img)]}
man.setdefault('notes',{})['microAccents']='Low-complexity beanie accents inspired by approved visual examples; fit inside locked alpha unless explicitly promoted to an attachment.'
MAN.write_text(json.dumps(man,indent=2)+'\n')

m=json.loads(MATRIX.read_text())
order=m['rollOrder']
if 'trimAccent' not in order: order.insert(order.index('motif'),'trimAccent')
if 'microAccent' not in order: order.insert(order.index('motif'),'microAccent')
m['axes']['trimAccent']={'none':52,'band_trim_line':20,'crown_trim_line':14,'double_trim_lines':8}
m['axes']['microAccent']={'none':60,'cuff_patch_small':14,'side_bow_small':8,'diagonal_wrap_band':7,'tiny_label_tag':11}
m.setdefault('microAccentPlacementRules',{})
m['microAccentPlacementRules'].update({
 'cuff_patch_small':{
   'allowedZones':['band'],
   'allowedPlacements':['cuff_front_center','cuff_front_offset_left','cuff_front_offset_right']
 },
 'side_bow_small':{
   'allowedZones':['band','crown'],
   'allowedPlacements':['cuff_side_left','cuff_side_right','body_side_left','body_side_right']
 },
 'diagonal_wrap_band':{
   'allowedZones':['band','crown'],
   'allowedPlacements':['body_front_offset_left','body_front_offset_right']
 },
 'tiny_label_tag':{
   'edgeOnly':True,
   'allowedZones':['band','crown'],
   'allowedPlacements':['cuff_side_left','cuff_side_right','body_side_left','body_side_right'],
   'forbidPlacements':['cuff_front_center','body_lower_front','crown_front','body_front_offset_left','body_front_offset_right'],
   'reason':'Label/tag motifs are edge-attached design accents and may not float in the middle of the beanie.'
 }
})

rules=m['exclusions']
def add(rule):
    if rule not in rules: rules.append(rule)

add({
 'when':{'trimAccent':'double_trim_lines'},
 'disallow':{
   'pattern':['plaid_woven','simple_jacquard','cable_plus_stripe'],
   'microAccent':['diagonal_wrap_band']
 },
 'reduce':['motif_complexity'],
 'reason':'Two trim lines already create medium visual complexity.'
})
add({
 'when':{'microAccent':'side_bow_small'},
 'disallow':{
   'pattern':['plaid_woven'],
   'knitStructure':['cable','chunky']
 },
 'reduce':['large_front_motif'],
 'reason':'Small side bow needs a quieter surface to remain readable.'
})
add({
 'when':{'microAccent':'diagonal_wrap_band'},
 'disallow':{
   'pattern':['plaid_woven','single_stripe','twin_stripe','two_tone_block'],
   'trimAccent':['double_trim_lines','crown_trim_line']
 },
 'reason':'Diagonal wrap is itself a strong line treatment.'
})
add({
 'when':{'microAccent':'tiny_label_tag'},
 'allowOnly':{
   'motifPlacement':['cuff_side_left','cuff_side_right','body_side_left','body_side_right']
 },
 'reason':'Label/tag motifs are edge-only and may not float on crown or center front.'
})

m.setdefault('rollSemantics',{})['trimAccent']='low-complexity line accents on band/cuff and/or crown'
m['rollSemantics']['microAccent']='small wearable beanie accents such as patch, side bow, wrap band, or edge label'
m.setdefault('assetBindings',{}).update({
 'microAccent.cuff_patch_small':'cuff_patch_small',
 'microAccent.side_bow_small':'side_bow_small',
 'microAccent.diagonal_wrap_band':'diagonal_wrap_band',
 'microAccent.tiny_label_tag':'tiny_label_tag'
})
MATRIX.write_text(json.dumps(m,indent=2)+'\n')
print('UPDATED accents + edge-only label rule')
