#!/usr/bin/env python3
from pathlib import Path
import json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from generator.fisherman_source_family import render
from generator.hat_hybrid_enhancements import enhance_frames
from generator.taste_policy import evaluate_recipe
from v5.pngio import blank_image,blit,draw_text,nearest_scale,read_rgba_png,write_rgba_png
OUT=ROOT/'experiments/fisherman_frozen_source_smoke_01'
POLICY=json.load(open(ROOT/'generator/data/headwear/bucket_fisherman_hat_renderer_v1_policy.json'))
REG=json.load(open(ROOT/'generator/data/source_respecting_hat_goldens_fisherman_candidate.json'))
VIEWS=('front','right','back','left')
COMMON={'materialTreatment':'plain','pattern':'solid','trim':'none','motif':'none','motifPlacement':'none','attachment':'none','hardware':'none'}
RARE={'materialTreatment':'textured','pattern':'solid','trim':'none','motif':'small','motifPlacement':'front_center','attachment':'none','hardware':'none'}

def crop(fr):
 pts=[(x,y) for y,row in enumerate(fr) for x,p in enumerate(row) if p[3]]
 x0=min(x for x,y in pts);x1=max(x for x,y in pts);y0=min(y for x,y in pts);y1=max(y for x,y in pts)
 return [row[x0:x1+1] for row in fr[y0:y1+1]]

def main():
 if OUT.exists():shutil.rmtree(OUT)
 OUT.mkdir(parents=True)
 assert evaluate_recipe(COMMON,'common',POLICY).valid
 assert evaluate_recipe(RARE,'rare',POLICY).valid
 rows=[]
 for pair in REG['candidatePairs']:
  pal=pair['palette']; golden=render(state=pair['state'],palette=pal)
  common,crep=enhance_frames(golden.frames,'bucket_fisherman',COMMON,'common')
  rare,rrep=enhance_frames(golden.frames,'bucket_fisherman',RARE,'rare')
  d=OUT/pal;d.mkdir()
  for v in VIEWS:
   write_rgba_png(d/f'golden_{v}.png',golden.frames[v])
   write_rgba_png(d/f'common_{v}.png',common[v])
   write_rgba_png(d/f'rare_{v}.png',rare[v])
  rows.append({
   'palette':pal,'goldenStatus':pair['status'],
   'common':{'recipe':COMMON,'changedPixels':crep.changed_pixels,'fallbackReason':crep.fallback_reason,
             'frames':{v:str((d/f'common_{v}.png').relative_to(ROOT)) for v in VIEWS}},
   'rare':{'recipe':RARE,'changedPixels':rrep.changed_pixels,'changedRatio':round(rrep.changed_ratio,6),
           'fallbackReason':rrep.fallback_reason,'outlinePreserved':rrep.outline_preserved,
           'alphaPreserved':rrep.alpha_preserved,'frames':{v:str((d/f'rare_{v}.png').relative_to(ROOT)) for v in VIEWS}},
   'goldenFrames':{v:str((d/f'golden_{v}.png').relative_to(ROOT)) for v in VIEWS},
  })

 # Show the actual source golden and the bounded rare output side-by-side per palette.
 cw,ch=190,150
 sheet=blank_image(cw*5,ch*4,(238,236,229,255))
 for ry,row in enumerate(rows):
  golden=read_rgba_png(ROOT/row['goldenFrames']['front'])
  g=crop(golden);gb=nearest_scale(g,8)
  blit(sheet,gb,(cw-len(gb[0]))//2,ry*ch+38+(90-len(gb))//2)
  if ry==0:draw_text(sheet,'GOLDEN FRONT',5,4,scale=1)
  for cx,v in enumerate(VIEWS,1):
   fr=crop(read_rgba_png(ROOT/row['rare']['frames'][v]));big=nearest_scale(fr,8)
   blit(sheet,big,cx*cw+(cw-len(big[0]))//2,ry*ch+38+(90-len(big))//2)
   if ry==0:draw_text(sheet,f'RARE {v.upper()}',cx*cw+5,4,scale=1)
  draw_text(sheet,row['palette'].upper(),5,ry*ch+20,scale=1)
  draw_text(sheet,f"HAT_RENDERER_V1 DELTA {row['rare']['changedPixels']} PX",5,ry*ch+134,scale=1)
 contact=OUT/'FISHERMAN_GOLDEN_TO_FROZEN_SMOKE.png';write_rgba_png(contact,sheet)
 manifest={'schema':'fisherman-candidate-frozen-smoke/v1','renderer':'HAT_RENDERER_V1',
  'productionCore':'generator/hat_hybrid_enhancements.py::enhance_frames',
  'sourceFamilyRenderer':'generator/fisherman_source_family.py',
  'candidateRegistry':'generator/data/source_respecting_hat_goldens_fisherman_candidate.json',
  'status':'CANDIDATE_REVIEW_REQUIRED_NOT_PRODUCTION_WHITELISTED',
  'contactSheet':str(contact.relative_to(ROOT)),'rows':rows}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('PASS Fisherman candidate family routed through frozen HAT_RENDERER_V1 smoke')
 print('CONTACT',contact)
 for r in rows:print(r['palette'],'common delta',r['common']['changedPixels'],'rare delta',r['rare']['changedPixels'])
if __name__=='__main__':main()
