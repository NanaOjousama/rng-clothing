#!/usr/bin/env python3
"""Render compact worn-image contact sheets for HPQC comparisons."""
from __future__ import annotations
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SAMPLE=(('01 Propeller Cap','01 Propeller Cap'),('05 Messy Straw','05 Messy Straw'),('10 Blue Straw','10 Blue Straw'))
DIRECTIONS=('front','right','back','left')
HEADBOX=(82, 23, 174, 155)
BG='#e9e5dc'
FONTFILE='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def sheet(root:Path, hair:int, dst:Path):
    w,h=1120,1650
    canvas=Image.new('RGB',(w,h),'#dedbd4')
    draw=ImageDraw.Draw(canvas)
    titlefont=ImageFont.truetype(FONTFILE,23)
    font=ImageFont.truetype(FONTFILE,17)
    small=ImageFont.truetype(FONTFILE,14)
    draw.text((20,12),f'Hair visibility A/B | Hairstyle #{hair} | Actual game-rendered farmer',fill='#212121',font=titlefont)
    draw.text((22,44),'Each row is the same hat sprite and identical offsets. HAIR ON / OFF is the only difference.',fill='#424242',font=small)
    names={'front':'FRONT','right':'RIGHT','back':'BACK','left':'LEFT'}
    for j,dir in enumerate(DIRECTIONS):
        draw.text((205+j*224,79),names[dir],fill='#3f4247',font=font)
    for i,(short,folderpart) in enumerate(SAMPLE):
      for k,mode in enumerate(('HAIR ON','HAIR OFF')):
        y=111+(i*2+k)*254
        label=f'{short}\n{mode}'
        draw.multiline_text((16,y+40),label,fill='#242424',font=font,spacing=8)
        for j,dir in enumerate(DIRECTIONS):
          path=root/f'hair{hair:03d}_HPQC {folderpart} - {mode}'/f'{dir}_worn.png'
          if not path.exists():
            draw.text((200+j*224,y+60),'MISSING',fill='#a10000',font=font)
            continue
          img=Image.open(path).convert('RGBA').crop(HEADBOX)
          tile=Image.new('RGBA',img.size,BG)
          tile.alpha_composite(img)
          tile=tile.convert('RGB').resize((184,264),Image.Resampling.NEAREST)
          x=198+j*224
          canvas.paste(tile,(x,y))
          draw.rectangle((x,y,x+183,y+263),outline='#a3a4a0',width=1)
    dst.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(dst)
    print(dst)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('captures',type=Path)
    ap.add_argument('output',type=Path)
    ap.add_argument('--hair',nargs='+',type=int,default=[0,16,38])
    a=ap.parse_args()
    for hair in a.hair:sheet(a.captures,hair,a.output/f'hair_policy_{hair:03d}.png')
