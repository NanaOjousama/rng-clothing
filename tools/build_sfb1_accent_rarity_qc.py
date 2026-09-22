#!/usr/bin/env python3
from pathlib import Path
import json, shutil, sys
ROOT=Path('/run/media/deck/USD00/RNG_clothing')
sys.path.insert(0,str(ROOT))
from v5.pngio import read_rgba_png, write_rgba_png, blank_image, blit
from v5.source.template_transfer import load_contract, template_frames, alpha_cells, ContractError
OUT=ROOT/'experiments/sfb1_accent_rarity_qc'
PACK=ROOT/'test-packs/fashionsense/RNG-SFB1-Accent-Rarity-QC'
LIVE=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods/RNG-SFB1-Accent-Rarity-QC')
ASSETS=ROOT/'authored/motifs/slouch_beanie_v1/assets'
VIEWS=['front','right','left','back']
FS_KEYS={'front':'FrontHat','right':'RightHat','left':'LeftHat','back':'BackHat'}
BATCH=[
 {'id':'C1_BAND_TRIM','rarity':'Common','palette':'EVERYDAY_STONE_BLUE','texture':None,'pattern':None,'trim':'band_trim_line','micro':'none'},
 {'id':'C2_CROWN_TRIM','rarity':'Common','palette':'CUTE_COCOA_GOLD','texture':'fine_rib','pattern':None,'trim':'crown_trim_line','micro':'none'},
 {'id':'U1_PATCH_RIB','rarity':'Uncommon','palette':'SPRING_SAGE_PETAL','texture':'fine_rib','pattern':None,'trim':'band_trim_line','micro':'cuff_patch_small'},
 {'id':'U2_EDGE_TAG_HEATHER','rarity':'Uncommon','palette':'EVERYDAY_STONE_BLUE','texture':None,'pattern':'heather_fleck','trim':'none','micro':'tiny_label_tag'},
 {'id':'R1_BOW_CABLE','rarity':'Rare','palette':'GOTHIC_WINE_ASH','texture':'cable_hint','pattern':None,'trim':'band_trim_line','micro':'side_bow_small'},
 {'id':'R2_WRAP_FLEECE','rarity':'Rare','palette':'AUTUMN_OCHRE_PLUM','texture':None,'pattern':None,'trim':'none','micro':'diagonal_wrap_band'},
 {'id':'E1_DOUBLE_PATCH','rarity':'Epic','palette':'ARCANE_VIOLET_COPPER','texture':'fine_rib','pattern':'heather_fleck','trim':'double_trim_lines','micro':'cuff_patch_small'},
 {'id':'E2_TAG_COLORBLOCK','rarity':'Epic','palette':'LUXURY_JADE_BRONZE','texture':None,'pattern':'two_tone_block','trim':'band_trim_line','micro':'tiny_label_tag'},
]

def hexrgb(s):
    s=s.lstrip('#')
    return tuple(int(s[i:i+2],16) for i in (0,2,4))

def lum(p): return p[0]*0.299+p[1]*0.587+p[2]*0.114
def recolor(frame,ramp):
    vals=sorted({lum(p) for row in frame for p in row if p[3]})
    out=[row[:] for row in frame]
    for y,row in enumerate(frame):
        for x,p in enumerate(row):
            if not p[3]: continue
            i=min(range(len(vals)),key=lambda k:abs(vals[k]-lum(p)))
            ri=round(i*(len(ramp)-1)/max(1,len(vals)-1))
            out[y][x]=(*ramp[ri],p[3])
    return out

def apply_tile(frame,name,ramp):
    src=read_rgba_png(ASSETS/f'{name}.png')
    h,w=len(src),len(src[0]); out=[row[:] for row in frame]
    for y,row in enumerate(frame):
        for x,p in enumerate(row):
            if not p[3]: continue
            q=src[y%h][x%w]
            if not q[3]: continue
            base=min(range(len(ramp)),key=lambda i:sum(abs(p[j]-ramp[i][j]) for j in range(3)))
            step=-1 if lum(q)<130 else 1
            ni=max(0,min(len(ramp)-1,base+step))
            out[y][x]=(*ramp[ni],p[3])
    return out

def opaque_rows(frame):
    ys=[y for y,row in enumerate(frame) if any(p[3] for p in row)]
    return min(ys),max(ys)
def apply_trim(frame,kind,accent):
    if kind=='none': return [row[:] for row in frame]
    out=[row[:] for row in frame]
    ymin,ymax=opaque_rows(frame)
    band_y=max(ymin,ymax-3)
    crown_y=max(ymin+2, ymin+(ymax-ymin)//2)
    rows=[]
    if kind in ('band_trim_line','double_trim_lines'): rows.append(band_y)
    if kind in ('crown_trim_line','double_trim_lines'): rows.append(crown_y)
    for y in rows:
        xs=[x for x,p in enumerate(frame[y]) if p[3]]
        if len(xs)<4: continue
        for x in range(min(xs)+1,max(xs)):
            if frame[y][x][3]:
                out[y][x]=(*accent[-1],frame[y][x][3])
    return out

def place_micro(frame,kind,accent,view):
    if kind=='none': return [row[:] for row in frame]
    out=[row[:] for row in frame]
    ymin,ymax=opaque_rows(frame)
    rows=[(y,[x for x,p in enumerate(row) if p[3]]) for y,row in enumerate(frame)]
    rows=[(y,xs) for y,xs in rows if xs]
    if kind=='cuff_patch_small':
        y=max(ymin,ymax-2); xs=dict(rows)[y]; cx=(min(xs)+max(xs))//2
        for dx in (-1,0,1):
            x=cx+dx
            if 0<=x<len(frame[0]) and frame[y][x][3]: out[y][x]=(*accent[-1],frame[y][x][3])
        if y-1>=0 and frame[y-1][cx][3]: out[y-1][cx]=(*accent[-2],frame[y-1][cx][3])
    elif kind=='tiny_label_tag':
        y=max(ymin,ymax-2); xs=dict(rows)[y]
        # edge-only: right edge on front/right/back, left edge on left view
        x=min(xs) if view=='left' else max(xs)
        inward=1 if x==min(xs) else -1
        for yy in (y-1,y):
            xx=x
            if 0<=yy<len(frame) and frame[yy][xx][3]: out[yy][xx]=(*accent[-1],frame[yy][xx][3])
            xx=x+inward
            if 0<=yy<len(frame) and 0<=xx<len(frame[0]) and frame[yy][xx][3]: out[yy][xx]=(*accent[-2],frame[yy][xx][3])
    elif kind=='side_bow_small':
        y=max(ymin,ymax-3); xs=dict(rows)[y]
        x=min(xs)+1 if view in ('front','left') else max(xs)-1
        pts=[(0,0),(-1,-1),(1,-1),(0,1)]
        for dx,dy in pts:
            xx,yy=x+dx,y+dy
            if 0<=yy<len(frame) and 0<=xx<len(frame[0]) and frame[yy][xx][3]:
                out[yy][xx]=(*accent[-1 if dx else -2],frame[yy][xx][3])
    elif kind=='diagonal_wrap_band':
        for k in range(5):
            y=max(ymin,ymax-5)+k
            xs=dict(rows).get(y,[])
            if not xs: continue
            x=min(xs)+2+k
            if x>max(xs)-1: x=max(xs)-1
            if frame[y][x][3]: out[y][x]=(*accent[-1],frame[y][x][3])
    return out
def main():
    tpl=load_contract(ROOT/'generator/data/templates/slouch_pl24.json')
    base=template_frames(tpl)
    pals={p['id']:p for p in json.loads((ROOT/'authored/palettes.json').read_text())['palettes']}
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    records=[]
    for spec in BATCH:
        pal=pals[spec['palette']]
        body=[hexrgb(x) for x in pal['ramps']['body']]
        accent=[hexrgb(x) for x in pal['ramps']['accent']]
        vdir=OUT/spec['id']; vdir.mkdir()
        frames={}
        for view in VIEWS:
            fr=recolor(base[view],body)
            if spec['texture']: fr=apply_tile(fr,spec['texture'],body)
            if spec['pattern']: fr=apply_tile(fr,spec['pattern'],body)
            fr=apply_trim(fr,spec['trim'],accent)
            fr=place_micro(fr,spec['micro'],accent,view)
            if alpha_cells(fr)!=alpha_cells(base[view]):
                raise ContractError(f"{spec['id']}/{view}: locked alpha changed")
            path=vdir/f'{view}.png'; write_rgba_png(path,fr); frames[view]=str(path)
        records.append({**spec,'frames':frames,'geometry':'LOCKED_TEMPLATE_ALPHA'})
    (OUT/'batch_manifest.json').write_text(json.dumps({'schema':'sfb1-accent-rarity-qc/v1','tag':'SFB1','template':'slouch_pl24','variants':records},indent=2)+'\n')

    if PACK.exists(): shutil.rmtree(PACK)
    PACK.mkdir(parents=True)
    (PACK/'manifest.json').write_text(json.dumps({
      'Name':'SFB1 Slouch Accent Rarity QC','Author':'RNG Clothing','Version':'0.1.0',
      'Description':'SFB1 slouch-beanie accent/motif rarity QC.',
      'UniqueID':'RNGClothing.FashionSense.SFB1AccentRarityQC','UpdateKeys':[],
      'ContentPackFor':{'UniqueID':'PeacefulEnd.FashionSense','MinimumVersion':'7.5.0'}
    },indent=2)+'\n')
    head_x={'front':-2,'right':-1,'left':-3,'back':-2}
    for spec in records:
        folder=PACK/'Hats'/spec['id']; folder.mkdir(parents=True)
        sheet=blank_image(24,96)
        for i,view in enumerate(VIEWS):
            blit(sheet,read_rgba_png(Path(spec['frames'][view])),0,i*24)
        write_rgba_png(folder/'hat.png',sheet)
        directions={}
        for i,view in enumerate(VIEWS):
            directions[FS_KEYS[view]]={
              'DisableGrayscale':True,'HideHair':False,
              'StartingPosition':{'X':0,'Y':i*24},
              'HeadPosition':{'X':head_x[view],'Y':-3},
              'HatSize':{'Width':24,'Length':24}
            }
        name=f"SFB1 {spec['rarity']} {spec['id']}"
        tags=['SFB1','RNG Clothing','slouch beanie','accent qc','rarity qc',spec['rarity'],spec['id']]
        (folder/'hat.json').write_text(json.dumps({'Name':name,'Tags':tags,**directions},indent=2)+'\n')
    (PACK/'TRACEABILITY.json').write_text(json.dumps({
      'tag':'SFB1','sourceBatch':'experiments/sfb1_accent_rarity_qc','template':'slouch_pl24',
      'count':len(records),'rarities':{'Common':2,'Uncommon':2,'Rare':2,'Epic':2},
      'labelRule':'tiny_label_tag is rendered at the beanie edge only; never floating at center/crown.'
    },indent=2)+'\n')
    if LIVE.exists(): shutil.rmtree(LIVE)
    shutil.copytree(PACK,LIVE)
    print('PASS SFB1',len(records),'hats')
    print('LIVE',LIVE)
    for rarity in ('Common','Uncommon','Rare','Epic'):
        print(rarity,sum(1 for r in records if r['rarity']==rarity))
if __name__=='__main__': main()
