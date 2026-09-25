#!/usr/bin/env python3
from pathlib import Path
import importlib.util, json, shutil, sys
from collections import deque
from PIL import Image, ImageDraw
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
CONTRACTS=json.loads((ROOT/'generator/data/cap_family_production_contracts.json').read_text())
OUT=ROOT/'experiments/cap_real_pipeline_batch_01'
PACK=ROOT/'test-packs/fashionsense/RNG-Cap-Real-Pipeline-QC'
VIEWS=('front','right','left','back')

spec=importlib.util.spec_from_file_location('cap_audit',ROOT/'tools/build_cap_source_corpus_audit.py')
audit=importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
BY_ID={c['id']:c for c in audit.CANDS}

PALETTES={
 'baseball':((24,42,46),(54,93,98),(101,151,153),(169,207,202),(225,239,232)),
 'snapback':((30,35,46),(57,69,95),(92,114,153),(160,180,205),(235,231,208)),
 'boys_cap':((44,48,55),(75,87,102),(113,132,150),(166,184,198),(223,231,234)),
 'backwards':((40,52,48),(75,104,93),(119,153,136),(173,201,182),(230,239,229)),
 'dad':((55,43,39),(100,74,63),(149,110,88),(195,159,128),(235,215,181)),
 'headphones_cap':((28,36,41),(55,77,83),(91,121,126),(148,174,175),(218,230,226)),
 'officer':((18,20,24),(35,39,47),(58,65,78),(94,104,119),(224,226,231)),
 'paperboy':((42,45,50),(75,82,92),(111,123,136),(163,176,188),(222,229,234)),
 'trucker':((25,39,43),(49,79,83),(86,125,128),(145,177,176),(215,229,221)),
}

def copy_frames(frames):
    return {v:frames[v].convert('RGBA').copy() for v in VIEWS}

def bbox(im):
    return im.getchannel('A').getbbox()

def opaque_count(im):
    return int(np.count_nonzero(np.array(im)[:,:,3]))

def largest_component_share(im):
    a=np.array(im)[:,:,3]>0; h,w=a.shape; seen=np.zeros_like(a,bool); best=0; total=int(a.sum())
    for y in range(h):
        for x in range(w):
            if not a[y,x] or seen[y,x]: continue
            q=deque([(x,y)]); seen[y,x]=1; n=0
            while q:
                cx,cy=q.popleft(); n+=1
                for nx,ny in ((cx-1,cy),(cx+1,cy),(cx,cy-1),(cx,cy+1)):
                    if 0<=nx<w and 0<=ny<h and a[ny,nx] and not seen[ny,nx]:
                        seen[ny,nx]=1; q.append((nx,ny))
            best=max(best,n)
    return 1.0 if total==0 else best/total

def validate_source(family,frames):
    errs=[]; metrics={}
    if set(frames)!=set(VIEWS): errs.append('missing directional view')
    for v in VIEWS:
        if v not in frames: continue
        im=frames[v]
        if im.size!=(20,20): errs.append(f'{v}: native frame {im.size}, expected 20x20')
        b=bbox(im); n=opaque_count(im); share=largest_component_share(im)
        metrics[v]={'bbox':b,'opaque':n,'largestComponentShare':round(share,3)}
        if b==(0,0,20,20): errs.append(f'{v}: opaque content fills whole frame (contamination/rescale suspect)')
        if n<20: errs.append(f'{v}: too little hat content ({n}px)')
        if share<0.72 and family!='headphones_cap': errs.append(f'{v}: disconnected non-hat contamination suspect ({share:.2f})')
    return errs,metrics

def value_recolor(frames,ramp):
    vals=[]
    for im in frames.values():
        a=np.array(im)
        for p in a[a[:,:,3]>0,:3]:
            vals.append(float(.299*p[0]+.587*p[1]+.114*p[2]))
    cuts=np.quantile(vals,[.18,.4,.63,.84]) if vals else [0,0,0,0]
    out={}
    for v,im in frames.items():
        a=np.array(im).copy()
        for y,x in zip(*np.where(a[:,:,3]>0)):
            lum=.299*a[y,x,0]+.587*a[y,x,1]+.114*a[y,x,2]
            idx=sum(lum>c for c in cuts)
            a[y,x,:3]=ramp[idx]
        out[v]=Image.fromarray(a,'RGBA')
    return out

def paint_if_opaque(a,x,y,color):
    if 0<=y<a.shape[0] and 0<=x<a.shape[1] and a[y,x,3]:
        a[y,x,:3]=color

def apply_design(family,frames):
    out=copy_frames(frames); accent=(220,184,92)
    if family in ('baseball','snapback'):
        a=np.array(out['front']); b=bbox(out['front']); cx=(b[0]+b[2]-1)//2
        paint_if_opaque(a,cx,b[1]+2,accent); paint_if_opaque(a,cx,b[1]+3,accent)
        out['front']=Image.fromarray(a,'RGBA')
    elif family=='backwards':
        a=np.array(out['back']); b=bbox(out['back']); cx=(b[0]+b[2]-1)//2
        paint_if_opaque(a,cx,b[3]-3,accent); out['back']=Image.fromarray(a,'RGBA')
    elif family=='dad':
        a=np.array(out['right']); b=bbox(out['right'])
        paint_if_opaque(a,b[2]-4,b[1]+3,accent); out['right']=Image.fromarray(a,'RGBA')
        out['left']=out['right'].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    elif family=='officer':
        a=np.array(out['front']); b=bbox(out['front']); cx=(b[0]+b[2]-1)//2
        paint_if_opaque(a,cx,b[1]+2,accent); paint_if_opaque(a,cx+1,b[1]+2,accent)
        out['front']=Image.fromarray(a,'RGBA')
    elif family=='trucker':
        for v in ('right','left','back'):
            a=np.array(out[v]); b=bbox(out[v])
            for y in range(b[1]+2,b[3]-2):
                for x in range(b[0]+2,b[2]-2):
                    if (x+y)%2==0 and a[y,x,3]:
                        a[y,x,:3]=tuple(min(255,int(c*1.18)) for c in a[y,x,:3])
            out[v]=Image.fromarray(a,'RGBA')
    return out

def stack(frames):
    im=Image.new('RGBA',(20,80),(0,0,0,0))
    for i,v in enumerate(VIEWS): im.alpha_composite(frames[v],(0,i*20))
    return im

def hat_json(name):
    d={'Name':name,'Tags':['RNG Clothing','CAP REAL PIPELINE','QC ONLY']}
    for i,(v,key) in enumerate(zip(VIEWS,('FrontHat','RightHat','LeftHat','BackHat'))):
        d[key]={'DisableGrayscale':True,'HideHair':False,'StartingPosition':{'X':0,'Y':i*20},
                'HeadPosition':{'X':0,'Y':0},'HatSize':{'Width':20,'Length':20}}
    return d

def main():
    if OUT.exists(): shutil.rmtree(OUT)
    if PACK.exists(): shutil.rmtree(PACK)
    OUT.mkdir(parents=True); (PACK/'Hats').mkdir(parents=True)
    rows=[]; rejected=[]
    for family,cfg in CONTRACTS['families'].items():
        c=BY_ID[cfg['source']]
        frames=copy_frames(c['frames'])
        errs,metrics=validate_source(family,frames)
        if errs:
            rejected.append({'family':family,'source':cfg['source'],'errors':errs,'metrics':metrics})
            print('REJECT',family,errs); continue
        alpha_before={v:np.array(frames[v])[:,:,3].copy() for v in VIEWS}
        colored=value_recolor(frames,PALETTES[family])
        final=apply_design(family,colored)
        alpha_ok=all(np.array_equal(alpha_before[v],np.array(final[v])[:,:,3]) for v in VIEWS)
        if not alpha_ok: raise RuntimeError(f'{family}: alpha changed')
        d=OUT/family; d.mkdir()
        stack(final).save(d/'hat.png')
        for v in VIEWS: final[v].save(d/f'{v}.png')
        trace={'family':family,'sourceId':cfg['source'],'capacity':cfg['capacity'],
               'identity':cfg['identity'],'design':cfg['design'],'validation':metrics,
               'alphaPreserved':alpha_ok,'sourceFrameResizeUsed':False,
               'frontOnlyReferencePixelsUsed':False}
        (d/'trace.json').write_text(json.dumps(trace,indent=2)+'\n')
        q=PACK/'Hats'/family; q.mkdir()
        stack(final).save(q/'hat.png'); (q/'hat.json').write_text(json.dumps(hat_json(f'CAP REAL {family}'),indent=2)+'\n')
        rows.append((family,cfg,final,trace))
    (OUT/'rejected.json').write_text(json.dumps(rejected,indent=2)+'\n')
    manifest={'Name':'RNG Cap Real Pipeline QC','Author':'RNG Clothing','Version':'0.1.0',
              'Description':'Strict source-backed cap family-contract QC batch.',
              'UniqueID':'RNGClothing.CapRealPipelineQC',
              'ContentPackFor':{'UniqueID':'PeacefulEnd.FashionSense'}}
    (PACK/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

    scale=10; tile=200; labelw=330; gap=12; rowh=230
    W=labelw+4*(tile+gap)+20; H=70+len(rows)*rowh
    sheet=Image.new('RGB',(W,H),'white'); dr=ImageDraw.Draw(sheet)
    dr.text((10,8),'CAP REAL PIPELINE — STRICT VALIDATED FINAL ROLLS',fill='black')
    dr.text((10,28),'NO RESIZE • 4 VIEWS • ALPHA LOCK • FAMILY IDENTITY • NO FRONT-ONLY TRUCKER PIXELS',fill='black')
    for i,v in enumerate(('FRONT','RIGHT','LEFT','BACK')): dr.text((labelw+i*(tile+gap)+72,50),v,fill='black')
    y=70
    for family,cfg,frames,trace in rows:
        dr.text((10,y+12),family.upper(),fill='black')
        dr.text((10,y+34),cfg['identity'][:48],fill='black')
        dr.text((10,y+54),f"design={cfg['design']}  capacity={cfg['capacity']}",fill='black')
        for i,v in enumerate(VIEWS):
            big=frames[v].resize((tile,tile),Image.Resampling.NEAREST)
            sheet.paste(big,(labelw+i*(tile+gap),y),big)
        y+=rowh
    sheet.save(OUT/'CAP_REAL_PIPELINE_CONTACT_X10.png')
    share=sheet.copy(); share.thumbnail((1450,2100),Image.Resampling.LANCZOS)
    share.save(OUT/'CAP_REAL_PIPELINE_CONTACT_SHARE.jpg',quality=78,optimize=True)
    print('PASS',len(rows),'accepted',len(rejected),'rejected')
    print(OUT/'CAP_REAL_PIPELINE_CONTACT_X10.png')
    print(OUT/'CAP_REAL_PIPELINE_CONTACT_SHARE.jpg')

if __name__=='__main__': main()
