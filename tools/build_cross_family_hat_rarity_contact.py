#!/usr/bin/env python3
from __future__ import annotations
import itertools,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from generator.catalog_templates import evaluate_family_recipe, load_family
from v5.pngio import read_rgba_png, blank_image, nearest_scale, blit, draw_text, write_rgba_png

CAT=json.loads((ROOT/'source_catalog/catalog.json').read_text())
OUT=ROOT/'experiments/catalog_hat_rarity_test'
OUT.mkdir(parents=True,exist_ok=True)

SELECTIONS={
 "common":[
  {"capacity":"tiny","family":"catalog_hats_more_accessories_and_stuff_headband","pack":"More Accessories and Stuff","name":"Headband"},
  {"capacity":"small","family":"catalog_hats_more_accessories_and_stuff_hair_buns","pack":"More Accessories and Stuff","name":"Hair Buns"},
  {"capacity":"medium","family":"catalog_hats_more_accessories_and_stuff_beanie","pack":"More Accessories and Stuff","name":"Beanie"},
  {"capacity":"large","family":"catalog_hats_more_accessories_and_stuff_straw_hat","pack":"More Accessories and Stuff","name":"Straw Hat"},
 ],
 "uncommon":[
  {"capacity":"tiny","family":"catalog_hats_alt_fashion_set_headband_studded","pack":"Alt-Fashion Set","name":"Headband (Studded)"},
  {"capacity":"small","family":"catalog_hats_more_accessories_and_stuff_crown_diadem_1","pack":"More Accessories and Stuff","name":"Crown (Diadem 1)"},
  {"capacity":"medium","family":"catalog_hats_more_accessories_and_stuff_tulip_hat","pack":"More Accessories and Stuff","name":"Tulip Hat (Striped)"},
  {"capacity":"large","family":"catalog_hats_cottagecore_set_mushroom_hat","pack":"Cottagecore Set","name":"Mushroom Hat (Dotted)"},
 ],
 "rare":[
  {"capacity":"tiny","family":"catalog_hats_cottagecore_set_headband_daisies","pack":"Cottagecore Set","name":"Headband (Daisies)"},
  {"capacity":"small","family":"catalog_hats_more_accessories_and_stuff_garland_dried_1","pack":"More Accessories and Stuff","name":"Garland (Dried 1)"},
  {"capacity":"medium","family":"catalog_hats_cottagecore_set_beret","pack":"Cottagecore Set","name":"Beret (Leaf)"},
  {"capacity":"large","family":"catalog_hats_more_accessories_and_stuff_sun_hat","pack":"More Accessories and Stuff","name":"Sun Hat (Flowers)"},
 ],
 "epic":[
  {"capacity":"tiny","family":"catalog_hats_more_accessories_and_stuff_headband","pack":"More Accessories and Stuff","name":"Headband (Cat 2)"},
  {"capacity":"small","family":"catalog_hats_more_accessories_and_stuff_garland_dried_1","pack":"More Accessories and Stuff","name":"Garland (Dried 2)"},
  {"capacity":"medium","family":"catalog_hats_more_accessories_and_stuff_earmuffs","pack":"More Accessories and Stuff","name":"Earmuffs (Cat)"},
  {"capacity":"large","family":"catalog_hats_cottagecore_set_hood_mushroom","pack":"Cottagecore Set","name":"Hood (Pointy)"},
 ],
}

def read_jsonc(path):
    text=Path(path).read_text(encoding='utf-8-sig')
    out=[]; ins=False; esc=False; i=0
    while i<len(text):
        ch=text[i]
        if ins:
            out.append(ch)
            if ch=='"' and not esc: ins=False
            esc=(ch=='\\' and not esc)
            if ch!='\\': esc=False
        elif ch=='"':
            ins=True; esc=False; out.append(ch)
        elif text.startswith('//',i):
            while i<len(text) and text[i]!='\n': i+=1
            continue
        else: out.append(ch)
        i+=1
    return json.loads(re.sub(r',\s*([}\]])',r'\1',''.join(out)))

def appearance(pack,name):
    for a in CAT['appearances']:
        if a.get('category')=='Hats' and a.get('pack')==pack and a.get('name')==name:
            return a
    raise KeyError((pack,name))

def front_frame(a):
    data=read_jsonc(a['json_path'])
    block=data.get('FrontHat')
    if not block: raise ValueError(f"{a['pack']}/{a['name']}: no FrontHat")
    sz=block['HatSize']; st=block['StartingPosition']
    w,h=int(sz['Width']),int(sz['Length']); x,y=int(st['X']),int(st['Y'])
    sheet=read_rgba_png(Path(a['png_path']))
    rows=[row[x:x+w] for row in sheet[y:y+h]]
    if block.get('Flipped'): rows=[list(reversed(row)) for row in rows]
    return rows

def crop_opaque(img):
    pts=[(x,y) for y,row in enumerate(img) for x,p in enumerate(row) if p[3]]
    if not pts: return img
    xs=[x for x,y in pts]; ys=[y for x,y in pts]
    x0,x1=max(0,min(xs)-1),min(len(img[0])-1,max(xs)+1)
    y0,y1=max(0,min(ys)-1),min(len(img)-1,max(ys)+1)
    return [row[x0:x1+1] for row in img[y0:y1+1]]

def strongest_valid_recipe(family, rarity):
    policy=load_family(family)
    axes=list(policy['vocabulary'])
    best=None
    for values in itertools.product(*(policy['vocabulary'][a] for a in axes)):
        recipe=dict(zip(axes,values))
        report=evaluate_family_recipe(family,rarity,recipe)
        if not report.valid:
            continue
        key=(report.complexity,len(report.active_channels),len(report.secondary),len(report.accents))
        if best is None or key>best[0]:
            best=(key,recipe,report)
    if best is None:
        raise RuntimeError(f'{family}: no valid {rarity} recipe')
    return policy,best[1],best[2]

manifest={'schema':'cross-family-hat-rarity-contact/v2','sourceBacked':True,'capacityAware':True,'humanArtApproved':False,'rarities':{}}
planned={}
for rarity,items in SELECTIONS.items():
    manifest['rarities'][rarity]=[]
    planned[rarity]=[]
    for item in items:
        a=appearance(item['pack'],item['name'])
        policy,recipe,report=strongest_valid_recipe(item['family'],rarity)
        cap=policy['familyCapacity']
        if cap['surfaceAreaClass']!=item['capacity']:
            raise AssertionError((item['family'],cap['surfaceAreaClass'],item['capacity']))
        row={
            **item,'png':a['png_path'],'json':a['json_path'],'generatorRole':a.get('generator_role'),
            'familyCapacity':cap,'policyValidRecipe':recipe,
            'tasteReport':{'complexity':report.complexity,'budget':[report.budget_min,report.budget_max],
                           'activeChannels':list(report.active_channels),'primary':report.primary,
                           'secondary':list(report.secondary),'accents':list(report.accents)}
        }
        manifest['rarities'][rarity].append(row)
        planned[rarity].append((item,a,report,cap))
(OUT/'selection_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

rarities=('common','uncommon','rare','epic')
cw,ch=270,235
sheet=blank_image(cw*4,ch*4,(240,238,232,255))
for rr,rarity in enumerate(rarities):
    for cc,(item,a,report,cap) in enumerate(planned[rarity]):
        img=crop_opaque(front_frame(a))
        maxw,maxh=195,138
        scale=max(1,min(12,maxw//max(1,len(img[0])),maxh//max(1,len(img))))
        big=nearest_scale(img,scale)
        x0=cc*cw; y0=rr*ch
        cid=f"{rarity[0].upper()}{cc+1}"
        draw_text(sheet,f"{cid} {rarity.upper()} / {cap['surfaceAreaClass'].upper()}",x0+8,y0+7,scale=1)
        draw_text(sheet,item['name'][:40],x0+8,y0+20,scale=1)
        draw_text(sheet,item['pack'][:40],x0+8,y0+32,scale=1)
        draw_text(sheet,f"CAP {cap['maxComplexity']}  RECIPE {report.complexity}  CH {len(report.active_channels)}",x0+8,y0+44,scale=1)
        bx=x0+(cw-len(big[0]))//2
        by=y0+62+(138-len(big))//2
        blit(sheet,big,bx,by)
        draw_text(sheet,'CAPACITY-AWARE / SOURCE-BACKED FRONT',x0+8,y0+219,scale=1)
out=OUT/'CROSS_FAMILY_HAT_ALL_RARITIES_CONTACT.png'
write_rgba_png(out,sheet)
print(out)
for rarity in rarities:
    print('\n'+rarity.upper())
    for item,a,report,cap in planned[rarity]:
        print(item['capacity'],item['name'],'family=',item['family'],'complexity=',report.complexity,'budget=',(report.budget_min,report.budget_max),'channels=',report.active_channels)
