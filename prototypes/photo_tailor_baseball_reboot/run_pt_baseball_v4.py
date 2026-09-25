#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys,json,hashlib,math,tempfile
import numpy as np
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
LAB3=REPO/'prototypes/photo_tailor_private_lab_03'
sys.path.insert(0,str(LAB3/'src'))
from semantic_analyzer import Analyzer
from prototype_core import edge_mask

REFDIR=REPO/'cap reference'
OUT=REPO/'experiments/cap_reboot/baseball_cap_pt_04'
SIZE=20
FACINGS=('front','right','left','back')
REFERENCE_VIEWS={
    'front':(REFDIR/'Screenshot_20260924_223136.png',(65,120,337,365)),
    'right':(REFDIR/'Screenshot_20260924_223116.png',(314,135,523,255)),
    'back':(REFDIR/'Screenshot_20260924_223136.png',(341,118,624,365)),
}
ALT_VIEWS={
    'front_alt':(REFDIR/'Screenshot_20260924_223057.png',(45,40,336,278)),
    'side_alt':(REFDIR/'Screenshot_20260924_223057.png',(338,32,648,274)),
}

TARGETS={
 'PT5_PRIMARY_BALANCED':{
   'label':'PT5 PRIMARY / BALANCED',
   'front':(15,12),'right':(18,12),'back':(15,12),
 },
 'PT6_PRIMARY_COMPACT':{
   'label':'PT6 PRIMARY / COMPACT',
   'front':(14,11),'right':(17,11),'back':(14,11),
 },
}
RAMP={
 'outline':(43,49,57,255),
 'deep':(61,71,83,255),
 'shadow':(78,91,106,255),
 'mid':(102,118,135,255),
 'light':(133,149,165,255),
 'hi':(162,176,190,255),
}
REGION_COLORS={
 'crown':(210,85,85,255),
 'band':(80,135,225,255),
 'brim':(225,188,70,255),
 'rear_strap':(125,205,125,255),
}
def bg_color(im):
    a=np.array(im.convert('RGB'),dtype=float)
    h,w=a.shape[:2]
    pts=np.concatenate([
        a[:4,:,:].reshape(-1,3),
        a[-4:,:,:].reshape(-1,3),
        a[:, :4,:].reshape(-1,3),
        a[:, -4:,:].reshape(-1,3),
    ],axis=0)
    return np.median(pts,axis=0)

def largest_component(mask):
    h,w=mask.shape
    seen=np.zeros_like(mask,bool);best=[]
    for y in range(h):
        for x in range(w):
            if not mask[y,x] or seen[y,x]: continue
            stack=[(x,y)];seen[y,x]=1;comp=[]
            while stack:
                xx,yy=stack.pop();comp.append((xx,yy))
                for nx,ny in ((xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)):
                    if 0<=nx<w and 0<=ny<h and mask[ny,nx] and not seen[ny,nx]:
                        seen[ny,nx]=1;stack.append((nx,ny))
            if len(comp)>len(best): best=comp
    out=np.zeros_like(mask,bool)
    for x,y in best: out[y,x]=1
    return out
def extract_reference(im):
    im=im.convert('RGB')
    arr=np.array(im,dtype=np.int16)
    bg=bg_color(im)
    dist=np.sqrt(((arr-bg)**2).sum(axis=2))
    # Gray screenshot background is very stable; 14 catches antialiased edges
    # while preserving the true rear opening as background.
    mask=largest_component(dist>14)
    ys,xs=np.where(mask)
    bbox=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))
    return {'image':im,'array':arr,'mask':mask,'bbox':bbox,'background':bg.tolist()}

def resize_bool(mask,bbox,size,threshold=92):
    x0,y0,x1,y1=bbox
    src=Image.fromarray((mask[y0:y1,x0:x1]*255).astype(np.uint8),'L')
    return np.array(src.resize(size,Image.Resampling.LANCZOS))>=threshold

def resize_rgb(arr,bbox,size):
    x0,y0,x1,y1=bbox
    src=Image.fromarray(arr[y0:y1,x0:x1].astype(np.uint8),'RGB')
    return np.array(src.resize(size,Image.Resampling.LANCZOS),dtype=np.uint8)

def place(mask):
    h,w=mask.shape
    out=np.zeros((SIZE,SIZE),bool)
    x=(SIZE-w)//2
    y=3
    out[y:y+h,x:x+w]=mask
    return out,(x,y)
def region_map(mask,facing):
    ys,xs=np.where(mask)
    y0,y1=ys.min(),ys.max()
    out=np.full(mask.shape,'background',dtype=object)
    for y,x in zip(ys,xs):
        v=(y-y0+.5)/max(1,y1-y0+1)
        if facing=='back':
            out[y,x]='crown' if v<.82 else 'rear_strap'
        else:
            out[y,x]='crown' if v<.68 else ('band' if v<.82 else 'brim')
    return out

def shade_role(mask,regions,facing):
    edge=edge_mask(mask)
    ys,xs=np.where(mask)
    x0,x1=xs.min(),xs.max()
    y0,y1=ys.min(),ys.max()
    out=np.full(mask.shape,'none',dtype=object)
    for y,x in zip(ys,xs):
        if edge[y,x]:
            out[y,x]='outline'
            continue
        u=(x-x0+.5)/max(1,x1-x0+1)
        v=(y-y0+.5)/max(1,y1-y0+1)
        role='mid'
        if u<.17 or u>.84:
            role='deep'
        elif .40<u<.62 and v<.62:
            role='light'
        elif .46<u<.56 and v<.34:
            role='hi'
        elif v>.78:
            role='shadow'
        if regions[y,x] in ('brim','rear_strap') and role not in ('outline','deep'):
            role='shadow' if role=='mid' else role
        out[y,x]=role
    return out
def apply_construction_lines(img,mask,regions,facing):
    px=img.load()
    ys,xs=np.where(mask)
    x0,x1=xs.min(),xs.max()
    y0,y1=ys.min(),ys.max()
    cx=round((x0+x1)/2)

    def put(x,y,role='shadow'):
        if 0<=x<SIZE and 0<=y<SIZE and mask[y,x] and not edge_mask(mask)[y,x]:
            px[x,y]=RAMP[role]

    # PT-style construction overlays: normalized, facing-scoped, not copied logos.
    if facing=='front':
        for y in range(y0+2,min(y0+5,y1)):
            put(cx,y,'shadow')
        # subtle crown-to-band construction line
        target=y0+round((y1-y0)*.67)
        for x in range(x0+2,x1-1):
            if regions[target,x] in ('crown','band'):
                put(x,target,'shadow')
    elif facing=='right':
        for dx,dy in ((0,2),(0,3),(1,4),(1,5)):
            put(cx+dx,y0+dy,'shadow')
    elif facing=='back':
        # center seam only above rear opening.
        for y in range(y0+2,y0+7):
            put(cx,y,'shadow')
    return img

def render(ev,size,facing):
    small=resize_bool(ev['mask'],ev['bbox'],size,92)
    canvas,origin=place(small)
    regions=region_map(canvas,facing)
    roles=shade_role(canvas,regions,facing)
    out=Image.new('RGBA',(SIZE,SIZE),(0,0,0,0))
    px=out.load()
    for y in range(SIZE):
        for x in range(SIZE):
            role=roles[y,x]
            if role!='none':
                px[x,y]=RAMP[role]
    apply_construction_lines(out,canvas,regions,facing)

    regdbg=Image.new('RGBA',(SIZE,SIZE),(0,0,0,0))
    rpx=regdbg.load()
    for y,x in zip(*np.where(canvas)):
        rpx[x,y]=REGION_COLORS[regions[y,x]]
    return out,regdbg,canvas
def mirror(im):
    return im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

def digest(im):
    return hashlib.sha256(im.tobytes()).hexdigest()

def mask_ascii(mask):
    return [''.join('#' if mask[y,x] else '.' for x in range(SIZE)) for y in range(SIZE)]

def make_contact(rows):
    scale=10; cell=SIZE*scale; left=175; gap=18; top=155
    w=left+4*cell+3*gap+30
    h=top+len(rows)*(cell+58)+30
    sheet=Image.new('RGB',(w,h),(240,239,235))
    d=ImageDraw.Draw(sheet)
    d.text((12,12),'PHOTO TAILOR BASEBALL 04 — NEW CAP REFERENCE FOLDER',fill=(20,20,20))
    d.text((12,29),'PT semantics + reference-derived occupancy + normalized cap regions/construction',fill=(50,50,50))
    d.text((12,46),'True BackHat reference: rear crown/opening/strap only; no visor behind player.',fill=(80,30,30))
    d.text((12,68),'Reference images stay local in cap reference/ and are not copied into this artifact.',fill=(45,45,45))
    for i,c in enumerate(FACINGS):
        d.text((left+i*(cell+gap)+70,137),c.upper(),fill=(25,25,25))
    y=top
    for label,frames in rows:
        d.text((12,y+78),label,fill=(20,20,20))
        for i,c in enumerate(FACINGS):
            im=frames[c].resize((cell,cell),Image.Resampling.NEAREST)
            sheet.paste(im,(left+i*(cell+gap),y),im)
        y+=cell+58
    sheet.save(OUT/'PT_BASEBALL_04_CONTACT_X10.png')
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    refs={name:Image.open(path).convert('RGB').crop(box) for name,(path,box) in REFERENCE_VIEWS.items()}
    alts={name:Image.open(path).convert('RGB').crop(box) for name,(path,box) in ALT_VIEWS.items()}

    evidence={facing:extract_reference(im) for facing,im in refs.items()}
    alt_evidence={name:extract_reference(im) for name,im in alts.items()}

    analyzer=Analyzer()
    semantics={}
    with tempfile.TemporaryDirectory(prefix='pt-baseball-ref-') as td:
        td=Path(td)
        for facing in ('front','right','back'):
            temp=td/f'{facing}.png'
            refs[facing].save(temp)
            semantics[facing]=analyzer.analyze(temp,'hat')
    semantics['folder_overview']=analyzer.analyze(REFDIR/'caprefimages.jpeg','hat')
    (OUT/'pt_semantics.json').write_text(json.dumps(semantics,indent=2)+'\n')
    rows=[]; candidates=[]
    for cid,spec in TARGETS.items():
        cdir=OUT/cid;cdir.mkdir(exist_ok=True)
        frames={};regions={};masks={}
        for facing in ('front','right','back'):
            frames[facing],regions[facing],masks[facing]=render(evidence[facing],spec[facing],facing)
        frames['left']=mirror(frames['right'])
        regions['left']=mirror(regions['right'])
        masks['left']=np.fliplr(masks['right'])

        for facing in FACINGS:
            frames[facing].save(cdir/f'{facing}.png')
            regions[facing].save(cdir/f'{facing}_regions.png')

        rows.append((spec['label'],frames))
        candidates.append({
            'id':cid,'label':spec['label'],
            'bboxByView':{f:list(frames[f].getbbox()) for f in FACINGS},
            'sha256ByView':{f:digest(frames[f]) for f in FACINGS},
            'leftIsExactMirrorOfRight':digest(frames['left'])==digest(mirror(frames['right'])),
            'maskAscii':{f:mask_ascii(masks[f]) for f in FACINGS},
        })

    make_contact(rows)
    def aspect(ev):
        x0,y0,x1,y1=ev['bbox']
        return round((x1-x0)/max(1,y1-y0),4)

    manifest={
      'schema':'photo-tailor-baseball-reboot/v4',
      'prototype':'PT_BASEBALL_04',
      'status':'PRIVATE_PROTOTYPE_CANDIDATE_QC',
      'authoritativeReferenceFolder':'cap reference',
      'authoritativeViews':{
        'front':'Screenshot_20260924_223136.png / front',
        'right':'Screenshot_20260924_223116.png / side',
        'back':'Screenshot_20260924_223136.png / true back',
      },
      'secondaryProportionChecks':[
        'Screenshot_20260924_223057.png / front',
        'Screenshot_20260924_223057.png / side',
        'caprefimages.jpeg',
        'capefernece.jpeg',
      ],
      'photoTailorSemantics':{
        k:{
          'topCategory':v['categoryCandidates'][0]['value'] if v['categoryCandidates'] else None,
          'topSilhouette':v['silhouetteCandidates'][0]['value'] if v['silhouetteCandidates'] else None,
          'coverage':v['coverageCandidates'][0]['value'] if v['coverageCandidates'] else None,
        } for k,v in semantics.items()
      },
      'referenceAspectRatios':{
        'front':aspect(evidence['front']),
        'right':aspect(evidence['right']),
        'back':aspect(evidence['back']),
        'front_alt':aspect(alt_evidence['front_alt']),
        'side_alt':aspect(alt_evidence['side_alt']),
      },
      'projection':{
        'normalizedCoordinates':True,
        'capRegionModel':{'crown':[0,.68],'band':[.68,.82],'brim':[.82,1.0]},
        'backRegionModel':{'crown':[0,.82],'rear_strap':[.82,1.0]},
        'referenceLogosMotifsIgnored':True,
        'ptConstructionOverlaysUsed':True,
        'trueBackHasNoBrimSemantic':True,
        'rightReferenceAlreadyPointsRight':True,
        'leftExactMirrorOfRight':True,
      },
      'cleanroom':{
        'oldDadV1Read':False,'oldDadV2Read':False,'oldTruckerRead':False,
        'oldCapControlUsed':False,'marioArtUsed':False,
        'oldVectorReferenceActive':False,
      },
      'candidates':candidates,
    }
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('PT semantics:',manifest['photoTailorSemantics'])
    print('aspects:',manifest['referenceAspectRatios'])
    print('wrote',OUT/'PT_BASEBALL_04_CONTACT_X10.png')
    for c in candidates:
        print(c['id'],c['bboxByView'])
        print('BACK MASK')
        print('\n'.join(c['maskAscii']['back']))

if __name__=='__main__':
    main()
