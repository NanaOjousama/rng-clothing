#!/usr/bin/env python3
from __future__ import annotations
import sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from generator.hybrid_v3.builder import CanonicalGarmentBuilder
from generator.hybrid_v3.projector import DirectionalProjector
from generator.hybrid_v3.compiler.pixel_grammar_v4 import PixelGrammarCompilerV4,V41_BASELINE_PROFILE
from generator.png_utils import blank_image, draw_text, draw_rect, blit, nearest_scale, read_rgba_png, write_rgba_png
from tools.generate_controlled_grammar_hd_adapter_repair import _farmer_composite

OUT=ROOT/'output/v4-art-grammar-pass2'; OUT.mkdir(parents=True,exist_ok=True)
D=('front','right','back','left')
CASES=(
 ('Orchard Essential Tee','T_SHIRT','TEE_CLEAN_ESSENTIAL','UNISEX_REGULAR',320201,'SPRING_ORCHARD'),
 ('Coastal Knit Polo','POLO_SHIRT','POLO_CLASSIC','MASC_TAILORED',320203,'COASTAL_MIST'),
 ('Ivory Academic Vest','SWEATER_VEST','VEST_ACADEMIC','MASC_TAILORED',320205,'CREAM_ACADEMIC'),
 ('Harbor Deck Sailor','SAILOR_TOP','SAILOR_DECK_CLASSIC','UNISEX_REGULAR',320207,'SAILOR_NAVY'),
)
FARMER=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/farmer_base.png')
HAIR=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/hairstyles.png')
BG=(232,226,217,255); PANEL=(205,197,186,255); INK=(39,37,36,255); ACC=(46,116,125,255)
def tile(c,img,x,y):
 draw_rect(c,x-2,y-2,len(img[0])+4,len(img)+4,ACC); draw_rect(c,x-1,y-1,len(img[0])+2,len(img)+2,PANEL); blit(c,img,x,y)
def main():
 # This generator remains the frozen V4.1 comparison fixture. V4.2 proof
 # generation lives in generate_v42_shape_library_proof.py.
 b=CanonicalGarmentBuilder(); p=DirectionalProjector(); comp=PixelGrammarCompilerV4(execution_profile=V41_BASELINE_PROFILE); items=[]
 for name,fam,intent,fit,seed,pal in CASES:
  can=b.build(family=fam,design_intent=intent,fit_profile=fit,root_seed=seed,rarity_budget='PHASE2_NEUTRAL_DEFAULT')
  proj=p.project(can); r=comp.compile(can,proj,palette_story=pal)
  farmers={}
  items.append((name,r,farmers))
  ddir=OUT/name.lower().replace(' ','-'); ddir.mkdir(exist_ok=True)
  write_rgba_png(ddir/'shirt.png',r.texture)
  (ddir/'validation.json').write_text(json.dumps(r.validation,indent=2)+'\n')
  (ddir/'metrics.json').write_text(json.dumps(r.metrics,indent=2)+'\n')
 # isolated sheet
 c=blank_image(760,4*160+32,BG); draw_text(c,'V4 PASS 2 | CONSTRUCTION GRAMMAR PROOF | 8X',8,7,color=INK)
 for row,(name,r,farmers) in enumerate(items):
  y=32+row*160; draw_text(c,name.upper(),8,y+50,color=INK)
  for col,d in enumerate(D):
   x=220+col*134; draw_text(c,d.upper(),x,y,color=ACC); tile(c,nearest_scale(r.frames[d],8),x,y+20)
 write_rgba_png(OUT/'V4_PASS2_ISOLATED_8X.png',c)
 print(json.dumps({name:r.validation['status'] for name,r,_ in items},indent=2))
if __name__=='__main__': main()
