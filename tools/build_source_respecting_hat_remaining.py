#!/usr/bin/env python3
from __future__ import annotations
import json,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from generator.source_respecting_hat_remix import source_family_state,VIEWS
from v5.pngio import write_rgba_png,read_rgba_png,blank_image,blit,nearest_scale,draw_text

OUT=ROOT/'experiments/source_respecting_hat_remaining_01'
CAND=OUT/'candidates'
REG=json.loads((ROOT/'generator/data/source_parts/hat_source_parts.json').read_text())

GROUPS={
 'B':['alt_beanie','alt_earmuffs','alt_headband','cc_headband','cc_headscarf','cc_hood'],
 'C':['mas_bows','mas_crown','mas_earmuffs','mas_garland','mas_hair_buns'],
 'D':['mas_headband','mas_hood'],
}
DISPLAY={
 'alt_beanie':'ALT Beanie','alt_earmuffs':'ALT Earmuffs','alt_headband':'ALT Headband',
 'cc_headband':'CC Headband','cc_headscarf':'CC Headscarf','cc_hood':'CC Hood',
 'mas_bows':'MAS Bows','mas_crown':'MAS Crown','mas_earmuffs':'MAS Earmuffs',
 'mas_garland':'MAS Garland','mas_hair_buns':'MAS Hair Buns',
 'mas_headband':'MAS Headband','mas_hood':'MAS Hood',
}

def cases_for(family):
    spec=REG['families'][family]
    out=[]
    for state in spec['alternateConstructionStates']:
        out.append((state,'source_native'))
    for state in spec['alternateConstructionStates']:
        if not spec.get('tintableState',{}).get(state,False): continue
        for pal in ('stone_blue','rose_cream','cocoa_gold'):
            if len(out)>=8: break
            out.append((state,pal))
        if len(out)>=8: break
    return out

def crop(fr):
    pts=[(x,y) for y,row in enumerate(fr) for x,p in enumerate(row) if p[3]]
    if not pts:return fr
    x0=min(x for x,y in pts);x1=max(x for x,y in pts)
    y0=min(y for x,y in pts);y1=max(y for x,y in pts)
    return [row[x0:x1+1] for row in fr[y0:y1+1]]

def save_candidate(family,state,palette,index):
    res=source_family_state(family,state,palette)
    d=CAND/f'{index:03d}_{family}'
    d.mkdir(parents=True,exist_ok=True)
    for v in VIEWS: write_rgba_png(d/f'{v}.png',res.frames[v])
    return {
      'index':index,'family':family,'label':DISPLAY[family],
      'sourceState':state,'palette':palette,
      'frames':{v:str((d/f'{v}.png').relative_to(ROOT)) for v in VIEWS},
      'trace':res.trace,'genericProjectionUsed':False,'genericLineUsed':False,
      'status':'HUMAN_ART_REVIEW_REQUIRED'
    }

def overview(group,rows):
    cols=max(len(x) for x in rows);cw,ch=190,140
    sheet=blank_image(cw*cols,ch*len(rows),(238,236,229,255))
    for ri,entries in enumerate(rows):
        for ci,e in enumerate(entries):
            fr=crop(read_rgba_png(ROOT/e['frames']['front']))
            sc=max(2,min(6,120//max(1,len(fr[0])),78//max(1,len(fr))))
            big=nearest_scale(fr,sc)
            blit(sheet,big,ci*cw+(cw-len(big[0]))//2,ri*ch+40+(78-len(big))//2)
            draw_text(sheet,e['label'][:22],ci*cw+4,ri*ch+5,scale=1)
            draw_text(sheet,e['sourceState'][:26],ci*cw+4,ri*ch+17,scale=1)
            draw_text(sheet,e['palette'][:20],ci*cw+4,ri*ch+29,scale=1)
    p=OUT/f'REMAINING_BATCH_{group}_OVERVIEW.png'
    write_rgba_png(p,sheet);return p

def directional(family,entries):
    cw,ch=170,130
    sheet=blank_image(cw*4,ch*len(entries),(238,236,229,255))
    for ri,e in enumerate(entries):
        for ci,v in enumerate(VIEWS):
            fr=crop(read_rgba_png(ROOT/e['frames'][v]))
            sc=max(2,min(6,118//max(1,len(fr[0])),76//max(1,len(fr))))
            big=nearest_scale(fr,sc)
            blit(sheet,big,ci*cw+(cw-len(big[0]))//2,ri*ch+34+(76-len(big))//2)
            if ri==0: draw_text(sheet,v.upper(),ci*cw+4,4,scale=1)
            if ci==0:
                draw_text(sheet,e['sourceState'][:22],4,ri*ch+18,scale=1)
                draw_text(sheet,e['palette'][:18],4,ri*ch+28,scale=1)
    p=OUT/f'{family.upper()}_DIRECTIONAL.png'
    write_rgba_png(p,sheet);return p

def main():
    if OUT.exists(): shutil.rmtree(OUT)
    CAND.mkdir(parents=True)
    manifest={
      'schema':'source-respecting-hat-remaining/v1',
      'families':[f for g in GROUPS.values() for f in g],
      'genericProjectionAllowed':False,
      'genericLineSynthesisAllowed':False,
      'generatedPaletteFallbackEnabled':False,
      'humanArtApproved':False,'candidates':[]
    }
    contacts=[];idx=0
    for group,fams in GROUPS.items():
        rows=[]
        for family in fams:
            entries=[]
            for state,palette in cases_for(family):
                idx+=1;e=save_candidate(family,state,palette,idx)
                entries.append(e);manifest['candidates'].append(e)
                print(f'{idx:03d} {family:18} {state:28} {palette}')
            rows.append(entries)
            contacts.append(directional(family,entries))
        contacts.append(overview(group,rows))
    manifest['candidateCount']=len(manifest['candidates'])
    manifest['contactSheets']=[str(p.relative_to(ROOT)) for p in contacts]
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('PASS remaining candidates',len(manifest['candidates']))
    print('PASS families',len(manifest['families']))
    print('PASS generic projection disabled')
    print('PASS generic line synthesis disabled')
    for p in contacts: print('CONTACT',p)

if __name__=='__main__': main()
