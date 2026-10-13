#!/usr/bin/env python3
"""Actual in-game ESM Full / Obscured contact sheets, 3 hats x 4 directions."""
import argparse
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

HATS=(('01','Propeller Cap'),('05','Messy Straw'),('10','Blue Straw'))
DIRS=('front','right','back','left')
F='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def build(root:Path,out:Path,hair:int):
    cw,ch=1120,1680
    canvas=Image.new('RGB',(cw,ch),'#dedbd6');p=ImageDraw.Draw(canvas)
    ft=ImageFont.truetype(F,22);label=ImageFont.truetype(F,16);small=ImageFont.truetype(F,13)
    p.text((15,10),f'Full vs Obscured — ESM / Stardew vanilla covered-hair policy — hairstyle #{hair}',font=ft,fill='#202020')
    p.text((15,43),'Actual in-game worn sprites. Same hat pixels and exact FS-calibrated placement; hair policy only.',font=small,fill='#444')
    for j,direction in enumerate(DIRS):
        p.text((204+j*225,77),direction.upper(),font=label,fill='#333')
    for i,(code,name) in enumerate(HATS):
      for j,mode in enumerate(('full','obscured')):
        y=110+256*(i*2+j)
        p.multiline_text((13,y+60),f'{code} {name}\n{mode.upper()}',font=label,fill='#1a1a1a',spacing=7)
        for k,direction in enumerate(DIRS):
            path=root/f'esm2_hair{hair:03d}_QC2_{code}_{mode}'/f'{direction}_worn.png'
            x=198+k*225
            if path.exists():
                im=Image.open(path).convert('RGBA').crop((82,23,174,155))
                back=Image.new('RGBA',im.size,'#e9e5dc');back.alpha_composite(im)
                tile=back.convert('RGB').resize((184,264),Image.Resampling.NEAREST)
                canvas.paste(tile,(x,y))
                p.rectangle((x,y,x+183,y+263),outline='#a5a2a0',width=1)
            else:
                p.text((x+15,y+80),'NOT CAPTURED',font=small,fill='#b40000')
    out.mkdir(parents=True,exist_ok=True)
    dest=out/f'esm_obscured_hair{hair:03d}_corrected.png'
    canvas.save(dest);print(dest)

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('captures',type=Path);a.add_argument('output',type=Path)
    a.add_argument('--hair',nargs='+',type=int,default=[0,16,38])
    args=a.parse_args()
    for h in args.hair:build(args.captures,args.output,h)
