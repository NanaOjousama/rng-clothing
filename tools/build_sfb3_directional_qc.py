#!/usr/bin/env python3
from pathlib import Path
import json, shutil, sys
ROOT=Path('/run/media/deck/USD00/RNG_clothing')
sys.path.insert(0,str(ROOT))
from v5.pngio import read_rgba_png, write_rgba_png, blank_image, blit, nearest_scale, draw_text

SRC=ROOT/'experiments/sfb3_spritefusion_directions'
OUT=ROOT/'experiments/sfb3_directional_qc'
PACK=ROOT/'test-packs/fashionsense/RNG-SFB3-Directional-QC'
LIVE=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods/RNG-SFB3-Directional-QC')
VIEWS=['front','right','left','back']
DIRMAP={'front':'S','right':'E','left':'W','back':'N'}
FS_KEYS={'front':'FrontHat','right':'RightHat','left':'LeftHat','back':'BackHat'}
RARITIES=['Common','Common','Uncommon','Uncommon','Rare','Rare','Epic','Epic']
def pad24(img):
    h=len(img); w=len(img[0])
    if w>24 or h>24:
        raise ValueError(f'oversize cardinal frame {w}x{h}')
    out=blank_image(24,24)
    x=(24-w)//2
    y=24-h
    blit(out,img,x,y)
    return out,{'sourceSize':[w,h],'offset':[x,y]}

def make_contact(records):
    scale=5; cw=150; ch=155; cols=4
    sheet=blank_image(cw*cols,ch*len(records),(242,240,234,255))
    for r,rec in enumerate(records):
        draw_text(sheet,f"SFB3 {rec['rarity']} {rec['id']}",4,r*ch+4,scale=1)
        for c,view in enumerate(VIEWS):
            img=read_rgba_png(Path(rec['frames'][view]))
            big=nearest_scale(img,scale)
            x=c*cw+(cw-len(big[0]))//2
            y=r*ch+22
            blit(sheet,big,x,y)
            draw_text(sheet,view,c*cw+4,r*ch+140,scale=1)
    return sheet
def main():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    records=[]
    for i in range(8):
        sid=f'SF{i+1:02d}'
        sdir=SRC/sid
        vdir=OUT/sid
        vdir.mkdir()
        frames={}; sourceMeta={}
        for view in VIEWS:
            src=read_rgba_png(sdir/f"{DIRMAP[view]}.png")
            padded,meta=pad24(src)
            p=vdir/f'{view}.png'
            write_rgba_png(p,padded)
            frames[view]=str(p)
            sourceMeta[view]={**meta,'spriteFusionDirection':DIRMAP[view]}
        records.append({
            'id':sid,'rarity':RARITIES[i],
            'frames':frames,'sourceMeta':sourceMeta,
            'geometry':'SPRITE_FUSION_DIRECTIONAL_SOURCE_PADDED_ONLY'
        })
    (OUT/'batch_manifest.json').write_text(json.dumps({
        'schema':'sfb3-directional-qc/v1','tag':'SFB3',
        'cardinalMap':DIRMAP,'variants':records
    },indent=2)+'\n')
    write_rgba_png(OUT/'SFB3_cardinal_contact.png',make_contact(records))
    if PACK.exists(): shutil.rmtree(PACK)
    PACK.mkdir(parents=True)
    (PACK/'manifest.json').write_text(json.dumps({
        'Name':'SFB3 Directional QC','Author':'RNG Clothing','Version':'0.1.0',
        'Description':'SFB3 true Sprite Fusion cardinal direction QC.',
        'UniqueID':'RNGClothing.FashionSense.SFB3DirectionalQC',
        'UpdateKeys':[],
        'ContentPackFor':{'UniqueID':'PeacefulEnd.FashionSense','MinimumVersion':'7.5.0'}
    },indent=2)+'\n')
    head_x={'front':-2,'right':-1,'left':-3,'back':-2}
    for rec in records:
        folder=PACK/'Hats'/rec['id']
        folder.mkdir(parents=True)
        sheet=blank_image(24,96)
        for vi,view in enumerate(VIEWS):
            blit(sheet,read_rgba_png(Path(rec['frames'][view])),0,vi*24)
        write_rgba_png(folder/'hat.png',sheet)
        dirs={}
        for vi,view in enumerate(VIEWS):
            dirs[FS_KEYS[view]]={
                'DisableGrayscale':True,'HideHair':False,
                'StartingPosition':{'X':0,'Y':vi*24},
                'HeadPosition':{'X':head_x[view],'Y':-3},
                'HatSize':{'Width':24,'Length':24}
            }
        name=f"SFB3 {rec['rarity']} {rec['id']}"
        tags=['SFB3','RNG Clothing','Sprite Fusion directions',
              'directional qc',rec['rarity'],rec['id']]
        (folder/'hat.json').write_text(json.dumps({
            'Name':name,'Tags':tags,**dirs
        },indent=2)+'\n')

    (PACK/'TRACEABILITY.json').write_text(json.dumps({
        'tag':'SFB3',
        'source':'Sprite Fusion direction-set API',
        'cardinalMap':DIRMAP,
        'count':len(records),
        'rarities':{'Common':2,'Uncommon':2,'Rare':2,'Epic':2},
        'transform':'transparent pad to 24x24 only; no scale, no silhouette rewrite'
    },indent=2)+'\n')
    if LIVE.exists():
        shutil.rmtree(LIVE)
    shutil.copytree(PACK,LIVE)
    print('PASS SFB3',len(records),'hats')
    print('LIVE',LIVE)
    for rarity in ('Common','Uncommon','Rare','Epic'):
        print(rarity,sum(1 for r in records if r['rarity']==rarity))
    print('CONTACT',OUT/'SFB3_cardinal_contact.png')

if __name__=='__main__':
    main()
