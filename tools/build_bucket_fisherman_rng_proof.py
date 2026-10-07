#!/usr/bin/env python3
from pathlib import Path
import json, shutil, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from generator.bucket_fisherman_generator import RARITIES,roll_recipe,render_recipe,pixel_sha
from v5.pngio import blank_image,blit,nearest_scale,write_rgba_png,draw_text
OUT=ROOT/'experiments/bucket_fisherman_rng_proof_01'; VIEWS=('front','right','back','left')
SEEDS={'Common':[1101,1102,1103,1104],'Uncommon':[1201,1202,1203,1204],'Rare':[1301,1302,1303,1304],'Epic':[1401,1402,1403,1404]}

def crop(fr):
 pts=[(x,y) for y,row in enumerate(fr) for x,p in enumerate(row) if p[3]]
 x0=min(x for x,y in pts);x1=max(x for x,y in pts);y0=min(y for x,y in pts);y1=max(y for x,y in pts)
 return [r[x0:x1+1] for r in fr[y0:y1+1]]

def main():
 if OUT.exists():shutil.rmtree(OUT)
 OUT.mkdir(parents=True)
 manifest={'schema':'bucket-fisherman-rng-proof/v1','status':'GENERATED_REVIEW_REQUIRED','construction':'bucket_fisherman_navy16','candidateCount':0,'candidates':[]}
 for rarity in RARITIES:
  rows=[]
  for seed in SEEDS[rarity]:
   rec=roll_recipe(seed,rarity); frames,report=render_recipe(rec); d=OUT/f'{rarity.lower()}_{seed}';d.mkdir()
   for v in VIEWS:write_rgba_png(d/f'{v}.png',frames[v])
   rec['frames']={v:str((d/f'{v}.png').relative_to(ROOT)) for v in VIEWS};rec['hashes']={v:pixel_sha(frames[v]) for v in VIEWS};rec['audit']=report
   (d/'recipe.json').write_text(json.dumps(rec,indent=2)+'\n');manifest['candidates'].append(rec);rows.append((rec,frames))
  # 4 rolls x 4 directions
  cw,ch=170,145; sheet=blank_image(cw*4,ch*4,(238,236,229,255))
  for ry,(rec,frames) in enumerate(rows):
   for cx,v in enumerate(VIEWS):
    fr=crop(frames[v]);big=nearest_scale(fr,7);blit(sheet,big,cx*cw+(cw-len(big[0]))//2,ry*ch+35+(85-len(big))//2)
    if ry==0:draw_text(sheet,v.upper(),cx*cw+4,4,scale=1)
   draw_text(sheet,f'{rarity.upper()} {rec["seed"]}',4,ry*ch+18,scale=1)
   draw_text(sheet,f'{rec["material"]} {rec["pattern"]}',4,ry*ch+122,scale=1)
   draw_text(sheet,f'{rec["wraparound"]} {rec["motif"]} {rec["palette"]}',4,ry*ch+133,scale=1)
  write_rgba_png(OUT/f'{rarity.upper()}_4VIEW.png',sheet)
 # front overview
 cw,ch=190,150; sheet=blank_image(cw*4,ch*4,(238,236,229,255))
 for i,rec in enumerate(manifest['candidates']):
  fr=__import__('v5.pngio',fromlist=['read_rgba_png']).read_rgba_png(ROOT/rec['frames']['front'])
  fr=crop(fr);big=nearest_scale(fr,8);x=(i%4)*cw;y=(i//4)*ch
  blit(sheet,big,x+(cw-len(big[0]))//2,y+28+(90-len(big))//2)
  draw_text(sheet,f'{rec["rarity"][0]} {rec["seed"]} {rec["palette"]}',x+4,y+4,scale=1)
  draw_text(sheet,f'{rec["pattern"]}/{rec["motif"]}',x+4,y+130,scale=1)
 write_rgba_png(OUT/'OVERVIEW_FRONT_16.png',sheet)
 manifest['candidateCount']=len(manifest['candidates']);manifest['contactSheets']=[str((OUT/'OVERVIEW_FRONT_16.png').relative_to(ROOT))]+[str((OUT/f'{r.upper()}_4VIEW.png').relative_to(ROOT)) for r in RARITIES]
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('PASS generated',manifest['candidateCount'],'Fisherman RNG proof rolls')
 print('OVERVIEW',OUT/'OVERVIEW_FRONT_16.png')
if __name__=='__main__':main()
