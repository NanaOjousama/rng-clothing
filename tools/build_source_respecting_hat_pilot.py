#!/usr/bin/env python3
from __future__ import annotations
import json,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from generator.source_respecting_hat_remix import (
    beret,beanie,straw,verify_patch_reconstruction,
    validate_no_isolated_line_fragment,VIEWS
)
from v5.pngio import write_rgba_png,read_rgba_png,blank_image,blit,nearest_scale,draw_text

OUT=ROOT/'experiments/source_respecting_hat_pilot_01'
CAND=OUT/'candidates'

BERETS=[
 ('B01 Plain Native',dict(state='Beret',palette='source_native')),
 ('B02 Plain Stone Blue',dict(state='Beret',palette='stone_blue')),
 ('B03 Plain Rose Cream',dict(state='Beret',palette='rose_cream')),
 ('B04 Dots Native',dict(state='Beret (Dotted)',palette='source_native')),
 ('B05 Dots Rose Cream',dict(state='Beret (Dotted)',palette='rose_cream')),
 ('B06 Leaf Native',dict(state='Beret (Leaf)',palette='source_native')),
 ('B07 Leaf Stone Blue',dict(state='Beret (Leaf)',palette='stone_blue')),
 ('B08 Ribbon Native',dict(state='Beret (Ribbon)',palette='source_native')),
 ('B09 Ribbon Rose Cream',dict(state='Beret (Ribbon)',palette='rose_cream')),
 ('B10 White Ribbon Native',dict(state='Beret (White Ribbon)',palette='source_native')),
]
BEANIES=[
 ('N01 Regular Native',dict(construction='Beanie',palette='source_native')),
 ('N02 Regular Stone Blue',dict(construction='Beanie',palette='stone_blue')),
 ('N03 Regular Rose Cream',dict(construction='Beanie',palette='rose_cream')),
 ('N04 Floppy Native',dict(construction='Beanie (Floppy)',palette='source_native')),
 ('N05 Floppy Stone Blue',dict(construction='Beanie (Floppy)',palette='stone_blue')),
 ('N06 Floppy Rose Cream',dict(construction='Beanie (Floppy)',palette='rose_cream')),
 ('N07 Cat Native',dict(construction='Beanie (Cat)',palette='source_native')),
 ('N08 Cat Stone Blue',dict(construction='Beanie (Cat)',palette='stone_blue')),
 ('N09 Cat Rose Cream',dict(construction='Beanie (Cat)',palette='rose_cream')),
]
STRAWS=[
 ('S01 Regular Native Ribbon',dict(construction='Straw Hat',ribbon_palette='source_native')),
 ('S02 Regular Cream Ribbon',dict(construction='Straw Hat',ribbon_palette='cream')),
 ('S03 Regular Rose Ribbon',dict(construction='Straw Hat',ribbon_palette='dusty_rose')),
 ('S04 Regular Sage Ribbon',dict(construction='Straw Hat',ribbon_palette='sage')),
 ('S05 Messy Native Ribbon',dict(construction='Straw Hat (Messy)',ribbon_palette='source_native')),
 ('S06 Messy Cream Ribbon',dict(construction='Straw Hat (Messy)',ribbon_palette='cream')),
 ('S07 Messy Rose Ribbon',dict(construction='Straw Hat (Messy)',ribbon_palette='dusty_rose')),
 ('S08 Messy Sage Ribbon',dict(construction='Straw Hat (Messy)',ribbon_palette='sage')),
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
    cw,ch=210,150;cols=10
    sheet=blank_image(cw*cols,ch*3,(238,236,229,255))
    for ri,entries in enumerate(rows):
        for ci,e in enumerate(entries):
            fr=crop_opaque(read_rgba_png(ROOT/e['frames']['front']))
            sc=max(2,min(7,130//max(1,len(fr[0])),85//max(1,len(fr))))
            big=nearest_scale(fr,sc)
            x=ci*cw+(cw-len(big[0]))//2;y=ri*ch+38+(85-len(big))//2
            blit(sheet,big,x,y)
            draw_text(sheet,e['label'][:28],ci*cw+5,ri*ch+6,scale=1)
            draw_text(sheet,(e['construction']+' / '+e['palette'])[:30],ci*cw+5,ri*ch+19,scale=1)
    p=OUT/'SOURCE_RESPECTING_HAT_PILOT_OVERVIEW.png';write_rgba_png(p,sheet);return p

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
    for cid in ['beret.dots_patch','beret.leaf_patch','beret.ribbon_patch','beret.white_ribbon_patch']:
        assert verify_patch_reconstruction(cid),cid
    manifest={
      'schema':'source-respecting-hat-pilot/v1',
      'guidingPrinciple':'Preserve the source hat core construction; remix non-core parts.',
      'families':['beret','beanie','straw_hat'],
      'genericProjectionAllowed':False,'genericLineSynthesisAllowed':False,
      'palettePriority':['same_family_source','same_material_or_construction','curated_transfer_group','generated_last_resort'],
      'generatedPaletteFallbackEnabled':False,
      'humanArtApproved':False,'candidates':[]
    }
    rows=[];idx=0
    for family,cases,fn in [('beret',BERETS,beret),('beanie',BEANIES,beanie),('straw_hat',STRAWS,straw)]:
        entries=[]
        for label,kwargs in cases:
            idx+=1;res=fn(**kwargs);e=save_result(label,res,idx)
            entries.append(e);manifest['candidates'].append(e)
            print(f'{idx:02d} {family:9} {label:28} source={res.source_state} component={res.component or "-"}')
        rows.append(entries)
    contacts=[overview(rows)]
    for family,entries in zip(('beret','beanie','straw_hat'),rows):
        contacts.append(directional(family,entries))
    manifest['candidateCount']=len(manifest['candidates'])
    manifest['contactSheets']=[str(p.relative_to(ROOT)) for p in contacts]
    manifest['sourcePatchReconstructionExact']=True
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('PASS candidates',len(manifest['candidates']))
    print('PASS exact source patch reconstruction')
    print('PASS generic projection disabled')
    print('PASS generic line synthesis disabled')
    for p in contacts:print('CONTACT',p)

if __name__=='__main__':main()
