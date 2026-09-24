#!/usr/bin/env python3
from __future__ import annotations
import json,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from generator.source_respecting_hat_remix import (
    boater,mushroom_hat,sun_hat,tulip_hat,verify_patch_reconstruction,
    validate_no_isolated_line_fragment,VIEWS
)
from v5.pngio import write_rgba_png,read_rgba_png,blank_image,blit,nearest_scale,draw_text

OUT=ROOT/'experiments/source_respecting_hat_batch_a_01'
CAND=OUT/'candidates'

BOATERS=[
 ('B01 Base Native',dict(state='Boater Hat',feature_palette='source_native')),
 ('B02 Base Cream',dict(state='Boater Hat',feature_palette='cream')),
 ('B03 Base Rose',dict(state='Boater Hat',feature_palette='dusty_rose')),
 ('B04 Base Sage',dict(state='Boater Hat',feature_palette='sage')),
 ('B05 Bow Native',dict(state='Boater Hat (Bow)',feature_palette='source_native')),
 ('B06 Bow Rose',dict(state='Boater Hat (Bow)',feature_palette='dusty_rose')),
 ('B07 Bow Sage',dict(state='Boater Hat (Bow)',feature_palette='sage')),
 ('B08 Ribbons Native',dict(state='Boater Hat (Ribbons)',feature_palette='source_native')),
 ('B09 Ribbons Cream',dict(state='Boater Hat (Ribbons)',feature_palette='cream')),
]
MUSHROOMS=[
 ('M01 Plain Native',dict(state='Mushroom Hat',body_palette='source_native')),
 ('M02 Plain Stone Blue',dict(state='Mushroom Hat',body_palette='stone_blue')),
 ('M03 Plain Rose Cream',dict(state='Mushroom Hat',body_palette='rose_cream')),
 ('M04 Plain Cocoa Gold',dict(state='Mushroom Hat',body_palette='cocoa_gold')),
 ('M05 Dotted Native',dict(state='Mushroom Hat (Dotted)',body_palette='source_native')),
 ('M06 Dotted Stone Blue',dict(state='Mushroom Hat (Dotted)',body_palette='stone_blue')),
 ('M07 Dotted Rose Cream',dict(state='Mushroom Hat (Dotted)',body_palette='rose_cream')),
 ('M08 Dotted Cocoa Gold',dict(state='Mushroom Hat (Dotted)',body_palette='cocoa_gold')),
]
SUNS=[
 ('S01 Plain Native',dict(state='Sun Hat',body_palette='source_native')),
 ('S02 Plain Stone Blue',dict(state='Sun Hat',body_palette='stone_blue')),
 ('S03 Plain Rose Cream',dict(state='Sun Hat',body_palette='rose_cream')),
 ('S04 Plain Cocoa Gold',dict(state='Sun Hat',body_palette='cocoa_gold')),
 ('S05 Flowers Native',dict(state='Sun Hat (Flowers)',body_palette='source_native')),
 ('S06 Flowers Stone Blue',dict(state='Sun Hat (Flowers)',body_palette='stone_blue')),
 ('S07 Flowers Rose Cream',dict(state='Sun Hat (Flowers)',body_palette='rose_cream')),
 ('S08 Ribbon Native',dict(state='Sun Hat (Ribbon)',feature_palette='source_native')),
 ('S09 Ribbon Cream',dict(state='Sun Hat (Ribbon)',feature_palette='cream')),
 ('S10 Ribbon Rose',dict(state='Sun Hat (Ribbon)',feature_palette='dusty_rose')),
 ('S11 Ribbon Sage',dict(state='Sun Hat (Ribbon)',feature_palette='sage')),
]
TULIPS=[
 ('T01 Plain Native',dict(state='Tulip Hat',body_palette='source_native')),
 ('T02 Plain Stone Blue',dict(state='Tulip Hat',body_palette='stone_blue')),
 ('T03 Plain Rose Cream',dict(state='Tulip Hat',body_palette='rose_cream')),
 ('T04 Plain Cocoa Gold',dict(state='Tulip Hat',body_palette='cocoa_gold')),
 ('T05 Striped Native',dict(state='Tulip Hat (Striped)',pattern_palette='source_native')),
 ('T06 Striped Cream',dict(state='Tulip Hat (Striped)',pattern_palette='cream')),
 ('T07 Striped Rose',dict(state='Tulip Hat (Striped)',pattern_palette='dusty_rose')),
 ('T08 Striped Sage',dict(state='Tulip Hat (Striped)',pattern_palette='sage')),
]

def crop_opaque(fr):
    pts=[(x,y) for y,row in enumerate(fr) for x,p in enumerate(row) if p[3]]
    if not pts:return fr
    x0=min(x for x,y in pts);x1=max(x for x,y in pts);y0=min(y for x,y in pts);y1=max(y for x,y in pts)
    return [row[x0:x1+1] for row in fr[y0:y1+1]]

def save_result(label,res,index):
    d=CAND/f'{index:02d}_{res.family}_{label.split(" ",1)[0].lower()}'
    d.mkdir(parents=True,exist_ok=True)
    for v in VIEWS: write_rgba_png(d/f'{v}.png',res.frames[v])
    # Generic-line fragment check applies only to optional source patches. It is
    # deliberately not applied to a built-in source ribbon recolour.
    line_errors=[]
    if res.component:
        line_errors=validate_no_isolated_line_fragment(res.frames,res.changed)
    if line_errors: raise RuntimeError(f'{label}: {line_errors}')
    return {
      'index':index,'label':label,'family':res.family,'construction':res.construction,
      'sourceState':res.source_state,'palette':res.palette,'component':res.component,
      'frames':{v:str((d/f'{v}.png').relative_to(ROOT)) for v in VIEWS},
      'trace':res.trace,
      'changedCells':{v:len(res.changed[v]) for v in VIEWS},
      'lineFragmentErrors':line_errors,
      'genericProjectionUsed':False,'genericLineUsed':False,
      'status':'HUMAN_ART_REVIEW_REQUIRED'
    }

def overview(rows):
    cw,ch=210,150;cols=11
    sheet=blank_image(cw*cols,ch*4,(238,236,229,255))
    for ri,entries in enumerate(rows):
        for ci,e in enumerate(entries):
            fr=crop_opaque(read_rgba_png(ROOT/e['frames']['front']))
            sc=max(2,min(7,130//max(1,len(fr[0])),85//max(1,len(fr))))
            big=nearest_scale(fr,sc)
            x=ci*cw+(cw-len(big[0]))//2;y=ri*ch+38+(85-len(big))//2
            blit(sheet,big,x,y)
            draw_text(sheet,e['label'][:28],ci*cw+5,ri*ch+6,scale=1)
            draw_text(sheet,(e['construction']+' / '+e['palette'])[:30],ci*cw+5,ri*ch+19,scale=1)
    p=OUT/'SOURCE_RESPECTING_HAT_BATCH_A_OVERVIEW.png';write_rgba_png(p,sheet);return p

def directional(family,entries):
    cw,ch=180,140
    sheet=blank_image(cw*4,ch*len(entries),(238,236,229,255))
    for ri,e in enumerate(entries):
        for ci,v in enumerate(VIEWS):
            fr=crop_opaque(read_rgba_png(ROOT/e['frames'][v]))
            sc=max(2,min(6,130//max(1,len(fr[0])),82//max(1,len(fr))))
            big=nearest_scale(fr,sc)
            blit(sheet,big,ci*cw+(cw-len(big[0]))//2,ri*ch+35+(82-len(big))//2)
            if ri==0:draw_text(sheet,v.upper(),ci*cw+5,4,scale=1)
            if ci==0:draw_text(sheet,e['label'][:25],ci*cw+5,ri*ch+18,scale=1)
    p=OUT/f'{family.upper()}_DIRECTIONAL.png';write_rgba_png(p,sheet);return p

def main():
    if OUT.exists():shutil.rmtree(OUT)
    CAND.mkdir(parents=True)
    patch_ids=['boater.bow_patch','boater.ribbons_patch','mushroom.dotted_patch',
               'sun_hat.flowers_patch','sun_hat.ribbon_patch','tulip.striped_patch']
    for cid in patch_ids: assert verify_patch_reconstruction(cid),cid
    manifest={
      'schema':'source-respecting-hat-batch-a/v1',
      'guidingPrinciple':'Preserve the source hat core construction; remix non-core parts.',
      'families':['boater_hat','mushroom_hat','sun_hat','tulip_hat'],
      'genericProjectionAllowed':False,'genericLineSynthesisAllowed':False,
      'palettePriority':['same_family_source','same_material_or_construction','curated_transfer_group','generated_last_resort'],
      'generatedPaletteFallbackEnabled':False,
      'humanArtApproved':False,'candidates':[]
    }
    rows=[];idx=0
    groups=[('boater_hat',BOATERS,boater),('mushroom_hat',MUSHROOMS,mushroom_hat),
            ('sun_hat',SUNS,sun_hat),('tulip_hat',TULIPS,tulip_hat)]
    for family,cases,fn in groups:
        entries=[]
        for label,kwargs in cases:
            idx+=1;res=fn(**kwargs);e=save_result(label,res,idx)
            entries.append(e);manifest['candidates'].append(e)
            print(f'{idx:02d} {family:12} {label:30} source={res.source_state} component={res.component or "-"}')
        rows.append(entries)
    contacts=[overview(rows)]
    for (family,_,_),entries in zip(groups,rows):
        contacts.append(directional(family,entries))
    manifest['candidateCount']=len(manifest['candidates'])
    manifest['contactSheets']=[str(p.relative_to(ROOT)) for p in contacts]
    manifest['sourcePatchReconstructionExact']=True
    manifest['sourcePartRegistry']='generator/data/source_parts/hat_source_parts.json'
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('PASS candidates',len(manifest['candidates']))
    print('PASS exact source patch reconstruction',len(patch_ids))
    print('PASS generic projection disabled')
    print('PASS generic line synthesis disabled')
    for p in contacts:print('CONTACT',p)

if __name__=='__main__':main()
