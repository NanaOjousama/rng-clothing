#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from v5.pngio import read_rgba_png

CAT=json.loads((ROOT/'source_catalog/catalog.json').read_text())
OUT=ROOT/'generator/data/source_parts/hat_source_parts.json'

def read_jsonc(path):
    import re
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
        else:
            out.append(ch)
        i+=1
    return json.loads(re.sub(r',\s*([}\]])',r'\1',''.join(out)))

def appearance(pack,name):
    return next(a for a in CAT['appearances'] if a.get('pack')==pack and a.get('name')==name)

def frames(pack,name):
    a=appearance(pack,name); sheet=read_rgba_png(a['png_path']); out={}
    doc=read_jsonc(a['json_path'])
    if isinstance(doc,list):
        doc=next((x for x in doc if x.get('Name')==name),doc[0])
    for view,box in a['analysis']['boxes'].items():
        x,y,w,h=map(int,box); rows=[row[x:x+w] for row in sheet[y:y+h]]
        block=doc.get(f'{view}Hat') if isinstance(doc,dict) else None
        if isinstance(block,dict) and block.get('Flipped'):
            rows=[list(reversed(row)) for row in rows]
        out[view.lower()]=rows
    return a,out

def patch_component(pack,base_name,var_name,cid,semantic,kind='optional_addon',family='beret'):
    ba,b=frames(pack,base_name); va,v=frames(pack,var_name)
    if {k:(len(x[0]),len(x)) for k,x in b.items()} != {k:(len(x[0]),len(x)) for k,x in v.items()}:
        raise ValueError(f'{cid}: source variant changes frame size; use alternate construction')
    views={}
    for view in b:
        cells=[]
        for y,row in enumerate(b[view]):
            for x,p in enumerate(row):
                q=v[view][y][x]
                if p!=q:
                    cells.append({'x':x,'y':y,'before':list(p),'after':list(q)})
        views[view]=cells
        # exact reconstruction proof
        got=[[p for p in row] for row in b[view]]
        for c in cells: got[c['y']][c['x']]=tuple(c['after'])
        if got!=v[view]: raise AssertionError(f'{cid}/{view}: patch is not exact')
    return {
      'id':cid,'family':family,'kind':kind,'semantic':semantic,
      'sourcePack':pack,'sourceBase':base_name,'sourceVariant':var_name,
      'transferScope':'SAME_CONSTRUCTION_ONLY','coordinatePolicy':'EXACT_SOURCE_COORDINATES_NO_NORMALIZATION',
      'preservesUnchangedSourcePixels':True,'reconstructionExact':True,'views':views
    }

def explicit_gray_roles(pack,name):
    a,fr=frames(pack,name)
    vals=sorted({p[0] for rows in fr.values() for row in rows for p in row if p[3] and p[0]==p[1]==p[2]})
    labels=['outline','shadow','mid_dark','midtone','light','highlight','spec','spec2']
    if len(vals)==1: labels=['midtone']
    elif len(vals)==2: labels=['outline','light']
    elif len(vals)==3: labels=['outline','midtone','light']
    elif len(vals)==4: labels=['outline','shadow','midtone','light']
    elif len(vals)==5: labels=['outline','shadow','midtone','light','highlight']
    elif len(vals)==6: labels=['outline','shadow','midtone','light','highlight','spec']
    mapping={f'{v},{v},{v}':labels[min(i,len(labels)-1)] for i,v in enumerate(vals)}
    return mapping

def straw_roles(pack,name):
    a,fr=frames(pack,name)
    colors=sorted({tuple(p[:3]) for rows in fr.values() for row in rows for p in row if p[3]})
    warm=[c for c in colors if not (c[0]==c[1]==c[2])]
    gray=[c for c in colors if c[0]==c[1]==c[2]]
    warm=sorted(warm,key=lambda c:0.299*c[0]+0.587*c[1]+0.114*c[2])
    gray=sorted(gray,key=lambda c:c[0])
    body_labels=['body_outline','body_shadow','body_mid_dark','body_midtone','body_light','body_highlight','body_spec']
    band_labels=['ribbon_outline','ribbon_shadow','ribbon_midtone','ribbon_light','ribbon_highlight','ribbon_spec']
    out={}
    for i,c in enumerate(warm): out[','.join(map(str,c))]=body_labels[min(i,len(body_labels)-1)]
    for i,c in enumerate(gray): out[','.join(map(str,c))]=band_labels[min(i,len(band_labels)-1)]
    return out

def _lum(c):
    return 0.299*c[0]+0.587*c[1]+0.114*c[2]

def _stepped(colors,prefix):
    labels=[f'{prefix}_outline',f'{prefix}_shadow',f'{prefix}_mid_dark',
            f'{prefix}_midtone',f'{prefix}_light',f'{prefix}_highlight',
            f'{prefix}_spec',f'{prefix}_spec2']
    cols=sorted(colors,key=_lum)
    return {','.join(map(str,c)):labels[min(i,len(labels)-1)] for i,c in enumerate(cols)}

def source_roles(pack,name,mode):
    _,fr=frames(pack,name)
    colors={tuple(p[:3]) for rows in fr.values() for row in rows for p in row if p[3]}
    gray={c for c in colors if c[0]==c[1]==c[2]}
    chrom=colors-gray
    if mode=='gray_body':
        out=_stepped(gray,'body')
        out.update({','.join(map(str,c)):'locked_source_color' for c in chrom})
        return out
    if mode=='warm_body_gray_feature':
        out=_stepped(gray,'feature')
        out.update({','.join(map(str,c)):'body_locked_source_color' for c in chrom})
        return out
    if mode=='gray_body_chromatic_pattern':
        out=_stepped(gray,'body');out.update(_stepped(chrom,'pattern'));return out
    raise ValueError(mode)

parts=[
 patch_component('Cottagecore Set','Beret','Beret (Dotted)','beret.dots_patch','dot_cluster'),
 patch_component('Cottagecore Set','Beret','Beret (Leaf)','beret.leaf_patch','leaf'),
 patch_component('Cottagecore Set','Beret','Beret (Ribbon)','beret.ribbon_patch','ribbon','alternate_construction_patch'),
 patch_component('Cottagecore Set','Beret','Beret (White Ribbon)','beret.white_ribbon_patch','ribbon','alternate_construction_patch'),
 patch_component('Cottagecore Set','Boater Hat','Boater Hat (Bow)','boater.bow_patch','bow','optional_addon','boater_hat'),
 patch_component('Cottagecore Set','Boater Hat','Boater Hat (Ribbons)','boater.ribbons_patch','ribbons','optional_addon','boater_hat'),
 patch_component('Cottagecore Set','Mushroom Hat','Mushroom Hat (Dotted)','mushroom.dotted_patch','dot_pattern','mutable_source_feature','mushroom_hat'),
 patch_component('More Accessories and Stuff','Sun Hat','Sun Hat (Flowers)','sun_hat.flowers_patch','flowers','optional_addon','sun_hat'),
 patch_component('More Accessories and Stuff','Sun Hat','Sun Hat (Ribbon)','sun_hat.ribbon_patch','ribbon','alternate_construction_patch','sun_hat'),
 patch_component('More Accessories and Stuff','Tulip Hat','Tulip Hat (Striped)','tulip.striped_patch','striped_pattern','mutable_source_feature','tulip_hat'),
]
payload={
 'schema':'source-respecting-hat-parts/v2',
 'principle':'Preserve source construction; remix only explicitly mutable or optional source-backed features.',
 'genericProjectionAllowed':False,'genericLineSynthesisAllowed':False,'parts':parts,
 'families':{
   'beret':{
     'pack':'Cottagecore Set','base':'Beret',
     'lockedConstruction':['base_alpha','crown','defining_seams','source_shading_topology'],
     'mutableSourceFeatures':['source_palette_tint'],
     'optionalAddonParts':['beret.dots_patch','beret.leaf_patch'],
     'alternateConstructionStates':['Beret (Ribbon)','Beret (White Ribbon)'],
     'roleByStateRgb':{n:explicit_gray_roles('Cottagecore Set',n) for n in ['Beret','Beret (Dotted)','Beret (Leaf)','Beret (Ribbon)','Beret (White Ribbon)']}
   },
   'beanie':{
     'pack':'More Accessories and Stuff','base':'Beanie',
     'lockedConstruction':['base_alpha','crown','default_knit_band','defining_seams','source_shading_topology'],
     'mutableSourceFeatures':['source_palette_tint'],'optionalAddonParts':[],
     'alternateConstructionStates':['Beanie','Beanie (Floppy)','Beanie (Cat)'],
     'roleByConstructionRgb':{n:explicit_gray_roles('More Accessories and Stuff',n) for n in ['Beanie','Beanie (Floppy)','Beanie (Cat)']}
   },
   'straw_hat':{
     'pack':'More Accessories and Stuff','base':'Straw Hat',
     'lockedConstruction':['base_alpha','crown','brim','built_in_ribbon_geometry','defining_seams','source_shading_topology'],
     'mutableSourceFeatures':['built_in_ribbon_color'],'optionalAddonParts':[],
     'alternateConstructionStates':['Straw Hat','Straw Hat (Messy)'],
     'roleByConstructionRgb':{n:straw_roles('More Accessories and Stuff',n) for n in ['Straw Hat','Straw Hat (Messy)']}
   },
   'boater_hat':{
     'pack':'Cottagecore Set','base':'Boater Hat',
     'lockedConstruction':['base_alpha','crown','brim','built_in_band_geometry','source_shading_topology'],
     'mutableSourceFeatures':['built_in_band_color'],
     'optionalAddonParts':['boater.bow_patch','boater.ribbons_patch'],'alternateConstructionStates':[],
     'roleByStateRgb':{n:source_roles('Cottagecore Set',n,'warm_body_gray_feature') for n in ['Boater Hat','Boater Hat (Bow)','Boater Hat (Ribbons)']}
   },
   'mushroom_hat':{
     'pack':'Cottagecore Set','base':'Mushroom Hat',
     'lockedConstruction':['base_alpha','cap','stem','defining_seams','source_shading_topology'],
     'mutableSourceFeatures':['cap_color','source_authored_dot_pattern'],'optionalAddonParts':[],
     'alternateConstructionStates':[],
     'roleByStateRgb':{n:source_roles('Cottagecore Set',n,'gray_body') for n in ['Mushroom Hat','Mushroom Hat (Dotted)']}
   },
   'sun_hat':{
     'pack':'More Accessories and Stuff','base':'Sun Hat',
     'lockedConstruction':['base_alpha','crown','brim','defining_seams','source_shading_topology'],
     'mutableSourceFeatures':['body_color','source_ribbon_color'],'optionalAddonParts':['sun_hat.flowers_patch'],
     'alternateConstructionStates':['Sun Hat (Ribbon)'],
     'roleByStateRgb':{
       'Sun Hat':source_roles('More Accessories and Stuff','Sun Hat','gray_body'),
       'Sun Hat (Flowers)':source_roles('More Accessories and Stuff','Sun Hat (Flowers)','gray_body'),
       'Sun Hat (Ribbon)':source_roles('More Accessories and Stuff','Sun Hat (Ribbon)','warm_body_gray_feature')
     }
   },
   'tulip_hat':{
     'pack':'More Accessories and Stuff','base':'Tulip Hat',
     'lockedConstruction':['base_alpha','petal_silhouette','defining_folds','source_shading_topology'],
     'mutableSourceFeatures':['body_color','source_authored_stripe_pattern'],'optionalAddonParts':[],
     'alternateConstructionStates':[],
     'roleByStateRgb':{
       'Tulip Hat':source_roles('More Accessories and Stuff','Tulip Hat','gray_body'),
       'Tulip Hat (Striped)':source_roles('More Accessories and Stuff','Tulip Hat (Striped)','gray_body_chromatic_pattern')
     }
   }
 },
 'rules':{
   'lockedConstructionMayBeRemoved':False,'optionalPatchMustBeSameConstruction':True,
   'optionalPatchMustReconstructSourceVariantExactly':True,'alternateConstructionUsesWholeSourceFrame':True,
   'paletteRolesAreBoundToExactSourceRgb':True,
   'palettePriority':['same_family_source','same_material_or_construction','curated_transfer_group','generated_last_resort'],
   'generatedLastResortEnabledInPilot':False
 }
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(payload,indent=2)+'\n')
print('PASS wrote',OUT,'families',len(payload['families']),'parts',len(parts))
for p in parts[4:]:
    print(p['id'],p['kind'],sum(len(v) for v in p['views'].values()),'changed cells')
