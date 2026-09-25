#!/usr/bin/env python3
from pathlib import Path
import importlib.util, json, shutil, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from v5 import authored
from generator.hat_hybrid_enhancements import enhance_frames

OUT=ROOT/'experiments/cap_source_final_generator_batch_01'
PACK=ROOT/'test-packs/fashionsense/RNG-Cap-Source-Final-Batch-QC'
VIEWS=('front','right','left','back')

# Reuse the audited extraction rules so this batch cannot silently use a
# different source frame than the source-corpus contact sheet.
spec=importlib.util.spec_from_file_location('cap_audit_builder',ROOT/'tools/build_cap_source_corpus_audit.py')
audit=importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
BY_ID={c['id']:c for c in audit.CANDS}

lib=authored.load()
PALETTES=[
 'STREET_TEAL_GRAPHITE','SAILOR_COBALT_CREAM','EVERYDAY_STONE_BLUE',
 'COASTAL_SEAFOAM_CORAL','DESERT_CLAY_TURQUOISE','EMBER_SUN_CHARCOAL',
]
PAL={p.id:p for p in lib.palettes if p.id in PALETTES}

# One polished Rare-style roll per complete unique construction.
ROWS=[
 ('MAS_CAP2','Baseball / Cap2','STREET_TEAL_GRAPHITE',dict(pattern='subtle',motif='small',motifPlacement='front_offset',trim='none',hardware='none')),
 ('MAS_SNAP','Snapback','SAILOR_COBALT_CREAM',dict(pattern='colorblock',motif='small',motifPlacement='front_center',trim='none',hardware='none')),
 ('RAGNAROK_BOYS','Boys Cap','EVERYDAY_STONE_BLUE',dict(pattern='subtle',motif='small',motifPlacement='front_center',trim='none',hardware='none')),
 ('JED_BACK','Backwards Cap','COASTAL_SEAFOAM_CORAL',dict(pattern='solid',motif='small',motifPlacement='back_center',trim='none',hardware='none')),
 ('JED_VINTAGE','Vintage / Dad-like','DESERT_CLAY_TURQUOISE',dict(pattern='subtle',motif='small',motifPlacement='side',trim='none',hardware='none')),
 ('JED_HEADPHONES','Cap + Headphones','STREET_TEAL_GRAPHITE',dict(pattern='solid',motif='small',motifPlacement='front_offset',trim='none',hardware='none')),
 ('JED_OFFICER','Officer Cap','EMBER_SUN_CHARCOAL',dict(pattern='stripe',motif='small',motifPlacement='front_center',trim='none',hardware='none')),
 ('MAS_PAPERBOY','Paperboy','EVERYDAY_STONE_BLUE',dict(pattern='dense',motif='small',motifPlacement='side',trim='none',hardware='none')),
 ('MAID_CAP','Maid Cap','COASTAL_SEAFOAM_CORAL',dict(pattern='subtle',motif='small',motifPlacement='front_center',trim='none',hardware='none')),
 ('OLD_DAD1','Old Dad V1','DESERT_CLAY_TURQUOISE',dict(pattern='subtle',motif='small',motifPlacement='front_offset',trim='none',hardware='none')),
 ('OLD_DAD2','Old Dad V2','SAILOR_COBALT_CREAM',dict(pattern='stripe',motif='small',motifPlacement='side',trim='none',hardware='none')),
]
def to_rows(im):
    a=np.array(im.convert('RGBA'),dtype=np.uint8)
    return [[tuple(map(int,a[y,x])) for x in range(a.shape[1])] for y in range(a.shape[0])]

def edge_mask(alpha):
    h,w=alpha.shape; out=np.zeros_like(alpha,dtype=bool)
    for y in range(h):
        for x in range(w):
            if not alpha[y,x]: continue
            for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if nx<0 or ny<0 or nx>=w or ny>=h or not alpha[ny,nx]:
                    out[y,x]=True; break
    return out

def luma(rgb):
    return .299*rgb[0]+.587*rgb[1]+.114*rgb[2]

def source_palette_map(frames,palette):
    # Preserve the source author's value/shading topology, but replace all RGB
    # with project curated ramps. This is the source-respecting colour step.
    vals=[]
    for im in frames.values():
        a=np.array(im.convert('RGBA'))
        alpha=a[:,:,3]>0; edge=edge_mask(alpha)
        for y,x in zip(*np.where(alpha & ~edge)):
            vals.append(luma(a[y,x,:3]))
    vals=sorted(vals)
    if vals:
        q=[vals[int((len(vals)-1)*f)] for f in (.12,.35,.58,.80)]
    else:
        q=[0,0,0,0]
    out={}
    for v,im in frames.items():
        a=np.array(im.convert('RGBA')); alpha=a[:,:,3]>0; edge=edge_mask(alpha)
        b=np.zeros_like(a)
        for y,x in zip(*np.where(alpha)):
            if edge[y,x]:
                col=palette.color('body',0)
            else:
                lv=luma(a[y,x,:3])
                step=1+sum(lv>qq for qq in q)
                # keep most cap interiors out of the palest endpoint
                step=min(step,5)
                col=palette.color('body',step)
            b[y,x]=col
        out[v]=[[tuple(map(int,b[y,x])) for x in range(b.shape[1])] for y in range(b.shape[0])]
    return out

def rgba_image(rows):
    a=np.array(rows,dtype=np.uint8)
    return Image.fromarray(a,'RGBA')

def stack(frames):
    out=Image.new('RGBA',(20,80),(0,0,0,0))
    for i,v in enumerate(VIEWS):
        out.alpha_composite(rgba_image(frames[v]),(0,i*20))
    return out

def add_palette_accent(frames,palette,mode):
    # Small semantic accents only; alpha and outline never change.
    out={v:[list(r) for r in frames[v]] for v in VIEWS}
    role='accent' if 'accent' in palette.ramps else 'trim'
    for v in VIEWS:
        a=np.array(out[v],dtype=np.uint8)
        alpha=a[:,:,3]>0; edge=edge_mask(alpha)
        ys,xs=np.where(alpha)
        if not len(xs): continue
        x0,x1=xs.min(),xs.max(); y0,y1=ys.min(),ys.max()
        if mode=='front_panel' and v=='front':
            cx=(x0+x1)//2
            pts=[(cx,y0+2),(cx,y0+3)]
        elif mode=='back_mark' and v=='back':
            cx=(x0+x1)//2
            pts=[(cx,max(y0,y1-2))]
        else:
            pts=[]
        for x,y in pts:
            if 0<=y<a.shape[0] and 0<=x<a.shape[1] and alpha[y,x] and not edge[y,x]:
                a[y,x]=palette.color(role,4)
        out[v]=[[tuple(map(int,a[y,x])) for x in range(a.shape[1])] for y in range(a.shape[0])]
    return out
def normalize20(im):
    im=im.convert('RGBA')
    if im.size==(20,20): return im
    if im.width>20 or im.height>20:
        cp=im.copy(); cp.thumbnail((20,20),Image.Resampling.NEAREST); im=cp
    out=Image.new('RGBA',(20,20),(0,0,0,0))
    out.alpha_composite(im,((20-im.width)//2,(20-im.height)//2))
    return out

def source_frames(cid):
    c=BY_ID[cid]
    return {v:normalize20(c['frames'][v]) for v in VIEWS}

def finish_one(cid,label,pid,recipe):
    src=source_frames(cid); pal=PAL[pid]
    mapped=source_palette_map(src,pal)
    # tiny accent only on true casual cap fronts; hybrid then handles bounded design.
    if cid in ('MAS_CAP2','MAS_SNAP','RAGNAROK_BOYS','JED_VINTAGE','OLD_DAD2'):
        mapped=add_palette_accent(mapped,pal,'front_panel')
    final,rep=enhance_frames(mapped,'cap',recipe,'rare')
    return src,mapped,final,rep

def save_hat_json(folder,name):
    h={'Name':name,'Tags':['CAP_SOURCE_FINAL_BATCH','QC ONLY','rare']}
    for i,key in enumerate(('FrontHat','RightHat','LeftHat','BackHat')):
        h[key]={'DisableGrayscale':True,'HideHair':False,
                'StartingPosition':{'X':0,'Y':i*20},
                'HeadPosition':{'X':0,'Y':0},
                'HatSize':{'Width':20,'Length':20}}
    (folder/'hat.json').write_text(json.dumps(h,indent=2)+'\n')
def main():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    if PACK.exists(): shutil.rmtree(PACK)
    (PACK/'Hats').mkdir(parents=True)
    records=[]
    batch_rows=list(ROWS)
    batch_rows.append(('MAS_SNAP','Trucker (derived)','STREET_TEAL_GRAPHITE',
                       dict(pattern='dense',motif='small',motifPlacement='front_center',trim='none',hardware='none')))
    for idx,(cid,label,pid,recipe) in enumerate(batch_rows,1):
        src,mapped,final,rep=finish_one(cid,label,pid,recipe)
        d=OUT/f'{idx:02d}_{cid.lower()}'; d.mkdir()
        stack(final).save(d/'hat.png')
        for v in VIEWS: rgba_image(final[v]).save(d/f'{v}.png')
        src_alpha=sum(px[3]>0 for v in VIEWS for row in to_rows(src[v]) for px in row)
        fin_alpha=sum(px[3]>0 for v in VIEWS for row in final[v] for px in row)
        rec={'id':cid,'label':label,'palette':pid,'recipe':recipe,
             'hybridApplied':rep.applied,'fallbackReason':rep.fallback_reason,
             'changedPixels':rep.changed_pixels,'changedRatio':round(rep.changed_ratio,6),
             'alphaPreserved':src_alpha==fin_alpha,'outlinePreserved':rep.outline_preserved,
             'sourcePack':BY_ID[cid]['pack'] if cid in BY_ID else 'derived'}
        (d/'trace.json').write_text(json.dumps(rec,indent=2)+'\n')
        records.append((rec,final))
        q=PACK/'Hats'/f'{idx:02d}_{cid}'; q.mkdir()
        stack(final).save(q/'hat.png'); save_hat_json(q,f'FINAL CAP {idx:02d} {label}')
    manifest={'Name':'RNG Cap Source Final Batch QC','Author':'RNG Clothing project',
              'Version':'0.1.0','Description':'Final-looking source-derived cap batch for visual QC.',
              'UniqueID':'RNGClothing.CapSourceFinalBatchQC',
              'ContentPackFor':{'UniqueID':'PeacefulEnd.FashionSense'}}
    (PACK/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (OUT/'manifest.json').write_text(json.dumps({'schema':'cap-source-final-batch/v1',
        'rarity':'rare','candidateCount':len(records),'candidates':[r for r,_ in records]},indent=2)+'\n')

    scale=9; tile=20*scale; gap=20; labelw=360; rowh=tile+58
    W=labelw+4*(tile+gap)+20; H=62+len(records)*rowh
    sheet=Image.new('RGB',(W,H),'white'); dr=ImageDraw.Draw(sheet)
    dr.text((10,8),'ALL CAP SOURCES — FINISHED GENERATOR ROLLS (RARE)',fill='black')
    dr.text((10,27),'source shape + source shading topology + curated palette + bounded HAT_RENDERER_V1 treatment',fill='black')
    for i,v in enumerate(('FRONT','RIGHT','LEFT','BACK')):
        dr.text((labelw+i*(tile+gap)+65,45),v,fill='black')
    y=62
    for n,(rec,frames) in enumerate(records,1):
        dr.text((10,y+18),f'{n:02d}. {rec["label"]}',fill='black')
        dr.text((10,y+38),rec['sourcePack'][:48],fill='black')
        dr.text((10,y+58),rec['palette'],fill='black')
        rr='APPLIED' if rec['hybridApplied'] else ('FALLBACK '+str(rec['fallbackReason']))
        dr.text((10,y+78),f'HAT_RENDERER_V1: {rr}',fill='black')
        for i,v in enumerate(VIEWS):
            im=rgba_image(frames[v]).resize((tile,tile),Image.Resampling.NEAREST)
            sheet.paste(im,(labelw+i*(tile+gap),y),im)
        y+=rowh
    full=OUT/'ALL_CAPS_FINISHED_CONTACT_X9.png'; sheet.save(full)
    share=sheet.copy(); share.thumbnail((1450,2100),Image.Resampling.LANCZOS)
    share.save(OUT/'ALL_CAPS_FINISHED_CONTACT_SHARE.jpg',quality=72,optimize=True)
    print('PASS final rows',len(records))
    for rec,_ in records:
        print(rec['label'],'|',rec['palette'],'| applied',rec['hybridApplied'],
              '| alpha',rec['alphaPreserved'],'| ratio',rec['changedRatio'])
    print(full)
    print(OUT/'ALL_CAPS_FINISHED_CONTACT_SHARE.jpg')
    print(PACK)

if __name__=='__main__':
    main()
