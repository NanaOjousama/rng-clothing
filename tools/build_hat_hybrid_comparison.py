#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from v5.pngio import read_rgba_png,write_rgba_png,blank_image,nearest_scale,blit,draw_text
G=json.load(open(ROOT/'experiments/hat_production_source_respecting_final_01/manifest.json'))
H=json.load(open(ROOT/'experiments/hat_production_hybrid_final_01/manifest.json'))
OUT=ROOT/'experiments/hat_production_hybrid_final_01/HYBRID_VS_GOLDEN_CONTACT.png'
def crop(fr):
 pts=[(x,y) for y,row in enumerate(fr) for x,p in enumerate(row) if p[3]]
 if not pts:return fr
 x0=min(x for x,y in pts);x1=max(x for x,y in pts);y0=min(y for x,y in pts);y1=max(y for x,y in pts)
 return [row[x0:x1+1] for row in fr[y0:y1+1]]
def main():
 gold={(c['family'],c['rarity']):c for c in G['candidates']};rows=[]
 for c in H['candidates']:rows.append((gold[(c['family'],c['rarity'])],c))
 cw,ch=165,145;labelw=260;s=blank_image(labelw+cw*8,ch*20,(238,236,229,255))
 fams=[]
 for c in H['candidates']:
  if c['family'] not in fams:fams.append(c['family'])
 for ri,fam in enumerate(fams):
  draw_text(s,fam.replace('catalog_hats_','')[:38],5,ri*ch+8,scale=1)
  fs=[c for c in H['candidates'] if c['family']==fam]
  for j,c in enumerate(fs):
   g=gold[(fam,c['rarity'])]
   for side,(tag,e) in enumerate((('G',g),('H',c))):
    fr=crop(read_rgba_png(ROOT/e['frames']['front']));sc=max(2,min(7,110//max(1,len(fr[0])),88//max(1,len(fr))))
    big=nearest_scale(fr,sc);x=labelw+(j*2+side)*cw+(cw-len(big[0]))//2;y=ri*ch+35+(90-len(big))//2;blit(s,big,x,y)
    draw_text(s,f'{tag} {c["rarity"][:3].upper()}',labelw+(j*2+side)*cw+4,ri*ch+8,scale=1)
   enh=c['hybridEnhancement'];draw_text(s,f'D{enh["changedPixels"]}',labelw+j*2*cw+4,ri*ch+126,scale=1)
 write_rgba_png(OUT,s);print(OUT)
if __name__=='__main__':main()
