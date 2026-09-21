#!/usr/bin/env python3
from pathlib import Path
import json, sys
sys.path.insert(0,'.')
from v5.pngio import blank_image, write_rgba_png, nearest_scale, blit, draw_rect, draw_text

ROOT=Path('authored/motifs/slouch_beanie_v1')
ASSETS=ROOT/'assets'
ASSETS.mkdir(parents=True,exist_ok=True)
T=(0,0,0,0); O=(38,31,27,255); D=(91,67,48,255); M=(167,123,82,255); L=(224,188,139,255); A=(112,145,91,255); B=(154,84,78,255); C=(110,123,159,255)
PAL={'.':T,'O':O,'D':D,'M':M,'L':L,'A':A,'B':B,'C':C}

def art(rows):
    h=len(rows); w=max(len(r) for r in rows); img=blank_image(w,h)
    for y,r in enumerate(rows):
        for x,ch in enumerate(r):
            if ch!='.': img[y][x]=PAL[ch]
    return img

ASSET_SPECS={
# symbols
'flower_tiny':('SYMBOL',["..L..",".LBL.","LBABL",".LBL.","..L.."]),
'flower_cluster_small':('SYMBOL',[".L..L..","LBL.LBL",".A...A.","..A.A..","...A..."]),
'leaf_sprig':('SYMBOL',["....A.","..AA..",".ALA..","..A...",".ALA..","AA...."]),
'star':('SYMBOL',["..L..",".LLL.","LLLLL",".LLL.","L...L"]),
'moon':('SYMBOL',[".LLL.","LLLL.","LL...","LL...",".LLL."]),
'heart':('SYMBOL',[".B.B.","BBBBB","BBBBB",".BBB.","..B.."]),
'snowflake':('SYMBOL',["..L..","L.L.L",".LLL.","L.L.L","..L.."]),
'mushroom_tiny':('SYMBOL',[".BBB.","BBBBB","BODOB","..M..",".MMM."]),
'geom_diamond':('SYMBOL',["..C..",".CCC.","CCLCC",".CCC.","..C.."]),
'animal_paw':('SYMBOL',["L...L","..L..",".LLL.",".LLL.","..L.."]),
'rune_mark':('SYMBOL',["L...L",".L.L.","..L..",".L.L.","L...L"]),
# carriers / labels
'patch_rect':('CARRIER',["OOOOOOO","OMMMMLO","OMMMMLO","OOOOOOO"]),
'patch_square':('CARRIER',["OOOOO","OMMLO","OMMLO","OLLL O".replace(' ',''),"OOOOO"]),
'stitched_badge':('CARRIER',[".OOOOO.","OOMMMOO","OMLMLMO","OOMMMOO",".OOOOO."]),
'side_label':('CARRIER',["OOO","OML","OML","OOO"]),
'woven_tag':('CARRIER',["OOOO","OMLO","OMLO","OMLO","OOOO"]),
# hardware / silhouette attachments
'button_accent':('HARDWARE',["OOO","OMO","OOO"]),
'pom_small':('ATTACHMENT',[".OO.","OMMO","OMLO",".OO."]),
'pom_large':('ATTACHMENT',["..OO..",".OMMO.","OMLLMO","OMLLMO",".OMMO.","..OO.."]),
'contrast_stitch':('STITCH',["L.L.L.L"]),
# surface pattern swatches
'single_stripe':('PATTERN',["MMMMMMM","LLLLLLL","MMMMMMM","MMMMMMM"]),
'twin_stripe':('PATTERN',["MMMMMMM","LLLLLLL","MMMMMMM","LLLLLLL","MMMMMMM"]),
'contrast_cuff':('PATTERN',["MMMMMMM","MMMMMMM","DDDDDDD","LLLLLLL"]),
'two_tone_block':('PATTERN',["MMMMMMM","MMMMMMM","CCCCCCC","CCCCCCC"]),
'simple_jacquard':('PATTERN',["MMLMLMM","MLMMMLM","LMMMMML","MLMMMLM","MMLMLMM"]),
'heather_fleck':('PATTERN',["MMLMMMM","MMMMMLM","MLMMMMM","MMMMMML"]),
'fine_rib':('TEXTURE',["MDMDMDM","MLMLMLM","MDMDMDM","MLMLMLM"]),
'wide_rib':('TEXTURE',["MDDMDDM","MLLMLLM","MDDMDDM","MLLMLLM"]),
'seed_stitch':('TEXTURE',["MLMDMLM","DMLMDML","MLMDMLM","DMLMDML"]),
'cable_hint':('TEXTURE',["MDLLLDM","MMLDLMM","MMDLDMM","MMLDLMM","MDLLLDM"]),
'waffle_hint':('TEXTURE',["MDDMDDM","DLLDLLD","MDDMDDM","DLLDLLD"]),
}

manifest={'schema':'slouch_beanie_motif/v1','nativePixelArt':True,'assets':{}}
for name,(category,rows) in ASSET_SPECS.items():
    img=art(rows); path=ASSETS/f'{name}.png'; write_rgba_png(path,img)
    manifest['assets'][name]={'category':category,'path':str(path),'size':[len(img[0]),len(img)]}

# Contact sheet: native asset shown at 10x; labels at 2x using built-in pixel font.
sections=[
 ('SYMBOLS',[k for k,v in ASSET_SPECS.items() if v[0]=='SYMBOL']),
 ('CARRIERS',[k for k,v in ASSET_SPECS.items() if v[0]=='CARRIER']),
 ('HARDWARE + ATTACH',[k for k,v in ASSET_SPECS.items() if v[0] in ('HARDWARE','ATTACHMENT','STITCH')]),
 ('PATTERNS',[k for k,v in ASSET_SPECS.items() if v[0]=='PATTERN']),
 ('KNIT TEXTURES',[k for k,v in ASSET_SPECS.items() if v[0]=='TEXTURE']),
]
W=900; rowh=118; header=48; H=30+sum(header+((len(items)+5)//6)*rowh for _,items in sections)
sheet=blank_image(W,H,(238,232,220,255)); y=18
draw_text(sheet,'SLOUCH BEANIE MOTIF LIBRARY V1',18,y,scale=2,color=O); y+=34
for title,items in sections:
    draw_text(sheet,title,18,y,scale=2,color=D); y+=header
    for i,name in enumerate(items):
        col=i%6; row=i//6; x=18+col*146; yy=y+row*rowh
        img=art(ASSET_SPECS[name][1]); big=nearest_scale(img,10)
        # checker-ish pale card
        draw_rect(sheet,x,yy,128,76,(248,245,238,255));
        bx=x+(128-len(big[0]))//2; by=yy+(62-len(big))//2
        blit(sheet,big,bx,by)
        draw_text(sheet,name.replace('_',' ')[:19],x,yy+82,scale=1,color=O)
    y+=((len(items)+5)//6)*rowh
write_rgba_png(ROOT/'slouch_beanie_motif_sheet.png',sheet)
# 2x review sheet for compact viewing
write_rgba_png(ROOT/'slouch_beanie_motif_sheet_x2.png',nearest_scale(sheet,2))
manifest['sheet']=str(ROOT/'slouch_beanie_motif_sheet.png')
manifest['notes']={
 'symbols':'Recolourable icon primitives; may be direct stitch, knit-in, or placed on carriers.',
 'carriers':'Patch/label shapes are independent of symbols so combinations multiply without duplicate art.',
 'attachments':'Pom assets are silhouette attachments, not motifs; roll separately.',
 'patterns':'Surface swatches are references/primitives, not placed motif sprites.',
 'sourcePolicy':'User photos and online research are reference-only; no photo pixels were copied.'
}
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('WROTE',len(ASSET_SPECS),'native assets')
print(ROOT/'slouch_beanie_motif_sheet.png')
