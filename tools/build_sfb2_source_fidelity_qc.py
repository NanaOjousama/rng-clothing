#!/usr/bin/env python3
from pathlib import Path
import json, shutil, sys
ROOT=Path('/run/media/deck/USD00/RNG_clothing')
sys.path.insert(0,str(ROOT))
from v5.pngio import read_rgba_png, write_rgba_png, blank_image, blit, nearest_scale, draw_text
from v5.source.template_transfer import load_contract, template_frames, alpha_cells, ContractError

SRC=ROOT/'experiments/spritefusion_beanie_material_rescale_test_01/accepted_32_and_under'
OUT=ROOT/'experiments/sfb2_source_fidelity_qc'
PACK=ROOT/'test-packs/fashionsense/RNG-SFB2-Source-Fidelity-QC'
LIVE=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods/RNG-SFB2-Source-Fidelity-QC')
VIEWS=['front','right','left','back']
FS_KEYS={'front':'FrontHat','right':'RightHat','left':'LeftHat','back':'BackHat'}
RARITIES=['Common','Common','Uncommon','Uncommon','Rare','Rare','Epic','Epic']
def opaque_rows(img):
    return [y for y,row in enumerate(img) if any(p[3] for p in row)]

def row_span(img,y):
    xs=[x for x,p in enumerate(img[y]) if p[3]]
    return (min(xs),max(xs)) if xs else None

def nearest_opaque_in_row(img,y,x):
    if img[y][x][3]: return img[y][x]
    xs=[xx for xx,p in enumerate(img[y]) if p[3]]
    if not xs: return (0,0,0,0)
    xx=min(xs,key=lambda q:abs(q-x))
    return img[y][xx]

def transfer_rgb(donor,target):
    drows=opaque_rows(donor); trows=opaque_rows(target)
    out=[row[:] for row in target]
    for ti,ty in enumerate(trows):
        dy=drows[round(ti*(len(drows)-1)/max(1,len(trows)-1))]
        ds=row_span(donor,dy); ts=row_span(target,ty)
        if not ds or not ts: continue
        dx0,dx1=ds; tx0,tx1=ts
        for tx in range(tx0,tx1+1):
            if not target[ty][tx][3]: continue
            u=(tx-tx0)/max(1,tx1-tx0)
            dx=round(dx0+u*(dx1-dx0))
            q=nearest_opaque_in_row(donor,dy,dx)
            out[ty][tx]=(q[0],q[1],q[2],target[ty][tx][3])
    return out

def build_contact(records):
    scale=6; cw=290; ch=190; cols=2
    rows=(len(records)+cols-1)//cols
    sheet=blank_image(cw*cols,ch*rows,(242,240,234,255))
    for i,r in enumerate(records):
        c=i%cols; rr=i//cols; x0=c*cw; y0=rr*ch
        donor=read_rgba_png(Path(r['donor']))
        front=read_rgba_png(Path(r['frames']['front']))
        blit(sheet,nearest_scale(donor,6),x0+10,y0+35)
        blit(sheet,nearest_scale(front,6),x0+145,y0+20)
        draw_text(sheet,f"SFB2 {r['rarity']} {i+1}",x0+8,y0+5,scale=1)
        draw_text(sheet,'SF SOURCE',x0+10,y0+150,scale=1)
        draw_text(sheet,'PL24 DIRECT',x0+145,y0+170,scale=1)
    return sheet
def main():
    tpl=load_contract(ROOT/'generator/data/templates/slouch_pl24.json')
    base=template_frames(tpl)
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    records=[]
    for i in range(8):
        donor_path=SRC/f'material_{i:02d}.png'
        donor=read_rgba_png(donor_path)
        vdir=OUT/f'SF{i+1:02d}'; vdir.mkdir()
        frames={}
        for view in VIEWS:
            fr=transfer_rgb(donor,base[view])
            if alpha_cells(fr)!=alpha_cells(base[view]):
                raise ContractError(f'SF{i+1:02d}/{view}: alpha changed')
            p=vdir/f'{view}.png'; write_rgba_png(p,fr); frames[view]=str(p)
        records.append({
          'id':f'SF{i+1:02d}','rarity':RARITIES[i],
          'donor':str(donor_path),'frames':frames,
          'transfer':'DIRECT_SOURCE_RGB_ROW_MAP',
          'geometry':'LOCKED_TEMPLATE_ALPHA'
        })
    (OUT/'batch_manifest.json').write_text(json.dumps({
      'schema':'sfb2-source-fidelity-qc/v1','tag':'SFB2',
      'template':'slouch_pl24','variants':records
    },indent=2)+'\n')
    write_rgba_png(OUT/'SFB2_source_vs_transfer_contact.png',build_contact(records))
    if PACK.exists(): shutil.rmtree(PACK)
    PACK.mkdir(parents=True)
    (PACK/'manifest.json').write_text(json.dumps({
      'Name':'SFB2 Source Fidelity QC','Author':'RNG Clothing','Version':'0.1.0',
      'Description':'SFB2 direct Sprite Fusion source-structure transfer QC.',
      'UniqueID':'RNGClothing.FashionSense.SFB2SourceFidelityQC','UpdateKeys':[],
      'ContentPackFor':{'UniqueID':'PeacefulEnd.FashionSense','MinimumVersion':'7.5.0'}
    },indent=2)+'\n')
    head_x={'front':-2,'right':-1,'left':-3,'back':-2}
    for r in records:
        folder=PACK/'Hats'/r['id']; folder.mkdir(parents=True)
        sheet=blank_image(24,96)
        for vi,view in enumerate(VIEWS):
            blit(sheet,read_rgba_png(Path(r['frames'][view])),0,vi*24)
        write_rgba_png(folder/'hat.png',sheet)
        dirs={}
        for vi,view in enumerate(VIEWS):
            dirs[FS_KEYS[view]]={
              'DisableGrayscale':True,'HideHair':False,
              'StartingPosition':{'X':0,'Y':vi*24},
              'HeadPosition':{'X':head_x[view],'Y':-3},
              'HatSize':{'Width':24,'Length':24}
            }
        tags=['SFB2','RNG Clothing','source fidelity','Sprite Fusion',r['rarity'],r['id']]
        name=f"SFB2 {r['rarity']} {r['id']}"
        (folder/'hat.json').write_text(json.dumps({'Name':name,'Tags':tags,**dirs},indent=2)+'\n')
    (PACK/'TRACEABILITY.json').write_text(json.dumps({
      'tag':'SFB2','sourceBatch':'experiments/sfb2_source_fidelity_qc',
      'template':'slouch_pl24','count':len(records),
      'rarities':{'Common':2,'Uncommon':2,'Rare':2,'Epic':2},
      'policy':'Actual approved Sprite Fusion donor RGB/value structure is row-mapped onto locked PL24 alpha. No procedural texture/trim/micro-accent synthesis.'
    },indent=2)+'\n')
    if LIVE.exists(): shutil.rmtree(LIVE)
    shutil.copytree(PACK,LIVE)
    print('PASS SFB2',len(records),'hats')
    print('LIVE',LIVE)
    for rarity in ('Common','Uncommon','Rare','Epic'):
        print(rarity,sum(1 for r in records if r['rarity']==rarity))
    print('CONTACT',OUT/'SFB2_source_vs_transfer_contact.png')

if __name__=='__main__':
    main()
