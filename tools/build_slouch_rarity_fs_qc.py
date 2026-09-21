#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, shutil, sys
sys.path.insert(0,'.')
from v5.pngio import read_rgba_png, write_rgba_png, blank_image, blit, nearest_scale

ROOT=Path('.')
PACK=ROOT/'test-packs/fashionsense/RNG-Slouch-Rarity-QC-260920'
MODS=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods')
TAG='ZZ_SLOUCH_RARITY_QC_260920'
BASE=ROOT/'experiments/slouch_beanie_generator_proof'
MOTIFS=ROOT/'authored/motifs/slouch_beanie_v1/assets'
DIRS=('front','right','left','back')

PALETTES={
 'earth':[(37,29,24,255),(64,47,36,255),(92,66,48,255),(130,92,64,255),(170,126,86,255),(215,176,124,255)],
 'sage':[(31,34,28,255),(52,62,47,255),(75,88,66,255),(105,120,89,255),(143,155,116,255),(194,202,157,255)],
 'navy':[(24,28,39,255),(36,48,69,255),(52,69,96,255),(76,98,129,255),(111,135,164,255),(167,185,202,255)],
 'berry':[(42,24,31,255),(73,38,51,255),(105,52,69,255),(145,73,93,255),(184,106,125,255),(224,165,177,255)],
 'gold':[(48,35,19,255),(82,57,25,255),(118,82,31,255),(160,113,41,255),(203,153,66,255),(237,204,126,255)],
 'teal':[(20,38,37,255),(27,64,61,255),(38,90,84,255),(57,122,111,255),(90,158,141,255),(153,204,184,255)],
 'plum':[(38,26,42,255),(63,39,68,255),(90,54,95,255),(123,74,127,255),(161,105,159,255),(209,164,205,255)],
 'frost':[(29,34,43,255),(48,60,76,255),(70,85,105,255),(101,120,142,255),(144,164,184,255),(202,216,228,255)]
}

VARIANTS=[
 ('C01','Common','earth','solid',None,None),
 ('C02','Common','sage','fine_rib',None,None),
 ('U01','Uncommon','navy','twin_stripe','side_label',None),
 ('U02','Uncommon','berry','contrast_cuff','star',None),
 ('R01','Rare','gold','cable_hint','leaf_sprig','pom_small'),
 ('R02','Rare','teal','simple_jacquard','mushroom_tiny',None),
 ('E01','Epic','plum','two_tone_block','flower_cluster_small','pom_large'),
 ('E02','Epic','frost','simple_jacquard','moon','pom_small'),
]

def luminance(p): return .2126*p[0]+.7152*p[1]+.0722*p[2]

def recolor(img,pal):
    vals=sorted({round(luminance(p),2) for row in img for p in row if p[3]})
    if not vals: return img
    lo,hi=min(vals),max(vals); out=blank_image(len(img[0]),len(img))
    for y,row in enumerate(img):
        for x,p in enumerate(row):
            if not p[3]: continue
            t=0 if hi==lo else (luminance(p)-lo)/(hi-lo)
            idx=max(0,min(5,round(t*5)))
            out[y][x]=pal[idx]
    return out

def bbox(img):
    pts=[(x,y) for y,row in enumerate(img) for x,p in enumerate(row) if p[3]]
    xs=[x for x,y in pts]; ys=[y for x,y in pts]
    return min(xs),min(ys),max(xs),max(ys)

def apply_pattern(img,name,pal):
    if name=='solid': return img
    x0,y0,x1,y1=bbox(img)
    for y in range(y0,y1+1):
        for x in range(x0,x1+1):
            if not img[y][x][3]: continue
            # preserve dark silhouette border by touching only brighter interior pixels
            if luminance(img[y][x]) < luminance(pal[1]): continue
            if name=='fine_rib' and x%2==0: img[y][x]=pal[2]
            elif name=='twin_stripe' and y in (y1-6,y1-4): img[y][x]=pal[4]
            elif name=='contrast_cuff' and y>=y1-2: img[y][x]=pal[1]
            elif name=='cable_hint' and x in ((x0+x1)//2-1,(x0+x1)//2+1) and y%2==0: img[y][x]=pal[4]
            elif name=='simple_jacquard' and ((x+y)%4==0 or (x-y)%5==0) and y<y1-2: img[y][x]=pal[4]
            elif name=='two_tone_block' and y<=(y0+y1)//2: img[y][x]=pal[3]
    return img

def paste_motif(img,name,view,pal):
    if not name: return
    m=read_rgba_png(MOTIFS/f'{name}.png')
    # recolour motif to a bright/dark two-step accent while preserving alpha
    mh,mw=len(m),len(m[0]); x0,y0,x1,y1=bbox(img)
    if name=='side_label':
        tx=(x1-mw+1 if view in ('front','right') else x0); ty=y1-mh-1
    else:
        tx=(x0+x1-mw+1)//2; ty=max(y0+2,y1-mh-2)
    for yy,row in enumerate(m):
        for xx,p in enumerate(row):
            if not p[3]: continue
            x,y=tx+xx,ty+yy
            if 0<=y<len(img) and 0<=x<len(img[0]) and img[y][x][3]:
                img[y][x]=pal[5] if luminance(p)>100 else pal[1]

def paste_attachment(img,name,pal):
    if not name: return
    m=read_rgba_png(MOTIFS/f'{name}.png'); mh,mw=len(m),len(m[0]); x0,y0,x1,y1=bbox(img)
    tx=(x0+x1-mw+1)//2; ty=max(0,y0-mh+1)
    for yy,row in enumerate(m):
        for xx,p in enumerate(row):
            if not p[3]: continue
            x,y=tx+xx,ty+yy
            if 0<=y<len(img) and 0<=x<len(img[0]): img[y][x]=pal[4] if luminance(p)>90 else pal[1]

def fs_block(y):
    return {'DisableGrayscale':True,'HideHair':False,'HatSize':{'Width':20,'Length':20},'StartingPosition':{'X':0,'Y':y},'HeadPosition':{'X':0,'Y':-2}}

def main():
    if PACK.exists(): shutil.rmtree(PACK)
    (PACK/'Hats').mkdir(parents=True)
    (PACK/'manifest.json').write_text(json.dumps({
      'Name':'ZZ Slouch Rarity QC 260920','Author':'RNG Clothing QC','Version':'1.0.0',
      'Description':'Temporary rarity-scope QC for generator-styled slouch beanies.',
      'UniqueID':'RNGClothing.FashionSense.SlouchRarityQC260920','UpdateKeys':[],
      'ContentPackFor':{'UniqueID':'PeacefulEnd.FashionSense','MinimumVersion':'7.5.0'}},indent=2)+'\n')
    trace=[]; contact=blank_image(4*20,8*20)
    for i,(code,tier,pkey,pattern,motif,attach) in enumerate(VARIANTS):
        pal=PALETTES[pkey]; frames=[]
        for view in DIRS:
            img=recolor(read_rgba_png(BASE/f'slouch_v1_{view}.png'),pal)
            apply_pattern(img,pattern,pal)
            # front motif, labels also visible on side; attachments all views
            if motif and (view=='front' or motif=='side_label' and view in ('right','left')):
                paste_motif(img,motif,view,pal)
            paste_attachment(img,attach,pal)
            frames.append(img)
        sh=blank_image(20,80)
        for j,img in enumerate(frames): blit(sh,img,0,j*20)
        app=f'ZZ SLOUCH QC {tier.upper()} {code}'
        out=PACK/'Hats'/app; out.mkdir(parents=True)
        write_rgba_png(out/'hat.png',sh)
        doc={'Name':app,'Tags':[TAG,'SLOUCH','RARITY QC',tier,pattern,pkey],
             'FrontHat':fs_block(0),'RightHat':fs_block(20),'LeftHat':fs_block(40),'BackHat':fs_block(60)}
        if motif: doc['Tags'].append(motif)
        if attach: doc['Tags'].append(attach)
        (out/'hat.json').write_text(json.dumps(doc,indent=2)+'\n')
        for j,img in enumerate(frames): blit(contact,img,j*20,i*20)
        trace.append({'appearance':app,'tier':tier,'palette':pkey,'pattern':pattern,'motif':motif,'attachment':attach,'tag':TAG})
    write_rgba_png(PACK/'rarity_contact_sheet.png',contact)
    write_rgba_png(PACK/'rarity_contact_sheet_x8.png',nearest_scale(contact,8))
    (PACK/'TRACEABILITY.json').write_text(json.dumps(trace,indent=2)+'\n')
    dest=MODS/PACK.name
    if dest.exists(): shutil.rmtree(dest)
    shutil.copytree(PACK,dest)
    print('PASS built+installed',len(VARIANTS),'appearances')
    for x in trace: print(x['tier'],x['appearance'],x['pattern'],x['motif'] or '-',x['attachment'] or '-')
    print('TAG',TAG)
    print('INSTALLED',dest)

if __name__=='__main__': main()
