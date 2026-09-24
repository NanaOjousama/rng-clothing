#!/usr/bin/env python3
"""Final hat production batch: source-respecting goldens only."""
from __future__ import annotations
import json,os,re,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from generator.catalog_templates import list_families,load_family
from generator.source_respecting_hat_production import RARITIES,load_goldens,roll_and_render
from v5.pngio import read_rgba_png,write_rgba_png,blank_image,blit,nearest_scale,draw_text
BATCH=os.environ.get('RNG_HAT_BATCH','hat_production_source_respecting_final_01')
LEAN=os.environ.get('RNG_HAT_PRESENTATION_LEAN','mixed')
OUT=ROOT/'experiments'/BATCH;CAND=OUT/'candidates';SHEETS=OUT/'family_sheets'
VIEWS=('front','right','left','back')

def label(f):
 return f.replace('catalog_hats_','').replace('more_accessories_and_stuff_','MAS ').replace('cottagecore_set_','CC ').replace('alt_fashion_set_','ALT ').replace('_',' ')
def slug(s):return re.sub(r'[^a-z0-9]+','_',s.lower()).strip('_')
def crop(fr):
 pts=[(x,y) for y,row in enumerate(fr) for x,p in enumerate(row) if p[3]]
 if not pts:return fr
 x0=min(x for x,y in pts);x1=max(x for x,y in pts);y0=min(y for x,y in pts);y1=max(y for x,y in pts)
 return [row[x0:x1+1] for row in fr[y0:y1+1]]

def save_candidate(row,n):
 res=row.pop('renderResult');d=CAND/f'{n:03d}_{row["rarity"]}_{slug(row["family"])}';d.mkdir(parents=True,exist_ok=True)
 for v in VIEWS:write_rgba_png(d/f'{v}.png',res.frames[v])
 row['sourceState']=res.source_state;row['palette']=res.palette;row['component']=res.component
 row['renderTrace']=res.trace;row['frames']={v:str((d/f'{v}.png').relative_to(ROOT)) for v in VIEWS}
 row['status']='CANDIDATE_REVIEW_REQUIRED'
 return row

def cross_sheet(grid,name):
 cw,ch=310,185;s=blank_image(cw*4,ch*len(grid),(238,236,229,255))
 for y,row in enumerate(grid):
  for x,e in enumerate(row):
   fr=crop(read_rgba_png(ROOT/e['frames']['front']));sc=max(2,min(7,190//max(1,len(fr[0])),105//max(1,len(fr))))
   big=nearest_scale(fr,sc);blit(s,big,x*cw+(cw-len(big[0]))//2,y*ch+54+(105-len(big))//2)
   draw_text(s,f'{e["rarity"].upper()}  {e["capacity"].upper()}  C{e["taste"]["complexity"]}',x*cw+7,y*ch+6,scale=1)
   if x==0:draw_text(s,label(e['family'])[:46],x*cw+7,y*ch+19,scale=1)
   draw_text(s,e['presentationLean'].replace('_leaning','')[:18],x*cw+7,y*ch+32,scale=1)
   draw_text(s,e['sourceState'][:43],x*cw+7,y*ch+160,scale=1)
   draw_text(s,e['palette'][:24],x*cw+7,y*ch+172,scale=1)
 p=OUT/name;write_rgba_png(p,s);return p

def family_sheet(family,entries):
 cw,ch=215,145;s=blank_image(cw*4,ch*4,(238,236,229,255))
 for ri,e in enumerate(entries):
  for ci,v in enumerate(VIEWS):
   fr=crop(read_rgba_png(ROOT/e['frames'][v]));sc=max(2,min(7,145//max(1,len(fr[0])),88//max(1,len(fr))))
   big=nearest_scale(fr,sc);blit(s,big,ci*cw+(cw-len(big[0]))//2,ri*ch+42+(88-len(big))//2)
   if ri==0:draw_text(s,v.upper(),ci*cw+5,4,scale=1)
   if ci==0:
    draw_text(s,f'{e["rarity"].upper()} C{e["taste"]["complexity"]} {e["presentationLean"].split("_")[0]}',5,ri*ch+17,scale=1)
    draw_text(s,e['sourceState'][:32],5,ri*ch+29,scale=1)
 p=SHEETS/f'{slug(family)}_DIRECTIONAL.png';write_rgba_png(p,s);return p

def main():
 if OUT.exists():shutil.rmtree(OUT)
 CAND.mkdir(parents=True);SHEETS.mkdir(parents=True)
 reg=load_goldens();hats=sorted(e['family'] for e in list_families(include_manual=False) if load_family(e['family']).get('category')=='Hats')
 if set(hats)!=set(reg['families']):raise RuntimeError('promoted hat set does not match golden registry')
 manifest={'schema':'hat-production-source-respecting/v1','batch':BATCH,'familyCount':20,
  'rarities':list(RARITIES),'presentationLeanMode':LEAN,'humanArtApproved':False,
  'goldenRegistry':'generator/data/source_respecting_hat_goldens.json','productionAuthority':'GOLDEN_SOURCE_RESPECTING_V1',
  'approvedPairWhitelistRequired':True,'genericProjectionAllowed':False,'genericLineSynthesisAllowed':False,
  'legacyStyleProfileFallbackAllowed':False,'candidates':[]}
 grid=[];n=0;family_contacts=[]
 for fam in hats:
  row=[]
  for rar in RARITIES:
   n+=1;e=save_candidate(roll_and_render(fam,rar,LEAN),n);manifest['candidates'].append(e);row.append(e)
   print(f'{n:02d}/80 {rar:8} {e["capacity"]:6} {label(fam):42} C{e["taste"]["complexity"]} {e["sourceState"]} / {e["palette"]}')
  grid.append(row);family_contacts.append(family_sheet(fam,row))
 all_sheet=cross_sheet(grid,'FINAL_HAT_PRODUCTION_ALL.png')
 a_sheet=cross_sheet(grid[:10],'FINAL_HAT_PRODUCTION_OVERVIEW_A.png')
 b_sheet=cross_sheet(grid[10:],'FINAL_HAT_PRODUCTION_OVERVIEW_B.png')
 manifest['candidateCount']=len(manifest['candidates'])
 manifest['rarityCounts']={r:sum(1 for c in manifest['candidates'] if c['rarity']==r) for r in RARITIES}
 manifest['capacityCounts']={k:sum(1 for c in manifest['candidates'] if c['capacity']==k) for k in ('tiny','small','medium','large')}
 manifest['presentationLeanCounts']={k:sum(1 for c in manifest['candidates'] if c['presentationLean']==k) for k in ('neutral','male_leaning','female_leaning')}
 manifest['contactSheets']=[str(x.relative_to(ROOT)) for x in [all_sheet,a_sheet,b_sheet,*family_contacts]]
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('PASS candidates',len(manifest['candidates']),'rarities',manifest['rarityCounts'])
 print('CONTACT',all_sheet);print('CONTACT',a_sheet);print('CONTACT',b_sheet)
if __name__=='__main__':main()
