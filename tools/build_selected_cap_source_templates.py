#!/usr/bin/env python3
from pathlib import Path
import json, hashlib, sys, shutil
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'experiments/cap_source_corpus_audit_01/selected_templates'
OUT.mkdir(parents=True,exist_ok=True)
PACK=ROOT/'test-packs/fashionsense/RNG-Cap-Source-Template-QC'
VIEWS=('front','right','left','back')

SOURCES={
 'BASEBALL':{
   'label':'Baseball — Ragnarok Boys Cap geometry',
   'source':'Ragnarok Online Hats / Seyph — Boys Cap',
   'path':Path('/home/deck/Downloads/[CP] Ragnarok Online Hats/assets/0_BoysCap.png'),
   'layout':'4x20',
   'constructionUse':'exact alpha shape donor',
   'identity':'baseball cap',
 },
 'DAD':{
   'label':'Dad — Jedone Vintage Cap geometry',
   'source':"Jedone's Casual Hat Pack — Vintage Cap_01",
   'path':Path("/home/deck/Downloads/[FS] Jedone's Casual Hat Pack/Hats/Vintage Cap/Vintage Cap_01/hat.png"),
   'layout':'4x20',
   'constructionUse':'exact alpha shape donor',
   'identity':'dad cap / low soft cap',
 },
 'TRUCKER':{
   'label':'Trucker — More Accessories Snapback geometry',
   'source':'More Accessories and Stuff / plurffle — Cap (Snapback)',
   'path':ROOT/'generator content/[FS] More Accessories and Stuff Pack/Hats/CapSnapback/hat.png',
   'layout':'3x20_mirror_left',
   'constructionUse':'structured cap alpha donor; trucker identity from panel/material contract',
   'identity':'trucker cap',
   'identityRefs':[
      '/home/deck/Downloads/front_view_trucker_h...-1938391056-0.png',
      'docs/headwear/KNOWLEDGE_BASE.md — vanilla #16 Trucker structural study',
   ],
 }
}

PALETTE={
 'outline':(36,42,50,255),
 'shadow':(66,78,90,255),
 'mid':(100,118,132,255),
 'light':(156,177,190,255),
 'accent':(191,202,203,255),
}
IDENTITY={
 'BASEBALL':{'body':(71,101,126,255),'light':(113,151,174,255),'accent':(216,176,92,255)},
 'DAD':{'body':(104,87,75,255),'light':(155,131,108,255),'accent':(206,183,143,255)},
 'TRUCKER':{'body':(58,75,89,255),'light':(107,131,143,255),'accent':(206,213,207,255)},
}

def source_frames(src):
    im=Image.open(src['path']).convert('RGBA')
    if src['layout']=='4x20':
        return {v:im.crop((0,i*20,20,(i+1)*20)) for i,v in enumerate(VIEWS)}
    if src['layout']=='3x20_mirror_left':
        f=im.crop((0,0,20,20)); r=im.crop((0,20,20,40)); b=im.crop((0,40,20,60))
        return {'front':f,'right':r,'left':r.transpose(Image.Transpose.FLIP_LEFT_RIGHT),'back':b}
    raise ValueError(src['layout'])

def mask(fr):
    return np.array(fr)[:,:,3]>0

def edge(m,x,y):
    if not m[y,x]: return False
    h,w=m.shape
    for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
        if nx<0 or ny<0 or nx>=w or ny>=h or not m[ny,nx]: return True
    return False

def neutral_from_alpha(fr):
    m=mask(fr); out=np.zeros((20,20,4),dtype=np.uint8)
    ys,xs=np.where(m)
    if not len(xs): return Image.fromarray(out,'RGBA')
    top,bottom=ys.min(),ys.max()
    left,right=xs.min(),xs.max()
    for y in range(20):
      for x in range(20):
        if not m[y,x]: continue
        if edge(m,x,y): c=PALETTE['outline']
        else:
          v=(y-top)/max(1,bottom-top)
          # completely new generic value model: top-left light, lower/right shadow
          relx=(x-left)/max(1,right-left)
          if v<.30 and relx<.72: c=PALETTE['light']
          elif v>.72 or relx>.78: c=PALETTE['shadow']
          else: c=PALETTE['mid']
        out[y,x]=c
    return Image.fromarray(out,'RGBA')

def identity_preview(kind, neutral):
    a=np.array(neutral).copy()
    m=a[:,:,3]>0
    ys,xs=np.where(m)
    if not len(xs): return neutral.copy()
    top,bottom=ys.min(),ys.max(); left,right=xs.min(),xs.max()
    body=IDENTITY[kind]['body']; light=IDENTITY[kind]['light']; accent=IDENTITY[kind]['accent']
    for y,x in zip(ys,xs):
        if edge(m,x,y):
            continue
        v=(y-top)/max(1,bottom-top); u=(x-left)/max(1,right-left)
        # Own design pass on borrowed geometry.
        if kind=='BASEBALL':
            c=light if (v<.42 and .25<u<.75) else body
            # subtle center seam/button cue
            if abs(u-.5)<.09 and v<.55: c=accent
        elif kind=='DAD':
            c=light if v<.34 else body
            # understated lower-band seam
            if .68<v<.82: c=accent
        else: # TRUCKER
            # foam/front panel + rear mesh cue. On front, centered panel;
            # on side/back this becomes alternating mesh cells in rear/lower crown.
            c=body
            if v<.58 and .28<u<.72: c=light
            if v>.38 and ((x+y)&1)==0: c=accent
        a[y,x]=c
    return Image.fromarray(a,'RGBA')

def stack(frames):
    out=Image.new('RGBA',(20,80),(0,0,0,0))
    for i,v in enumerate(VIEWS): out.alpha_composite(frames[v],(0,i*20))
    return out

results={}
for kind,src in SOURCES.items():
    sf=source_frames(src)
    nf={v:neutral_from_alpha(sf[v]) for v in VIEWS}
    pf={v:identity_preview(kind,nf[v]) for v in VIEWS}
    d=OUT/kind.lower(); d.mkdir(parents=True,exist_ok=True)
    stack(nf).save(d/'template_shape_20x80.png')
    stack(pf).save(d/'identity_preview_20x80.png')
    for v in VIEWS:
        nf[v].save(d/f'{v}.png')
    # prove geometry copied, colour/design not copied
    source_alpha=hashlib.md5(b''.join(bytes(mask(sf[v]).flatten()) for v in VIEWS)).hexdigest()
    template_alpha=hashlib.md5(b''.join(bytes(mask(nf[v]).flatten()) for v in VIEWS)).hexdigest()
    trace={
      'type':kind,'source':src['source'],'sourcePath':str(src['path']),
      'constructionUse':src['constructionUse'],'identity':src['identity'],
      'identityRefs':src.get('identityRefs',[]),
      'sourceAlphaHash':source_alpha,'templateAlphaHash':template_alpha,
      'alphaExact':source_alpha==template_alpha,
      'copiedSourceRGB':False,
      'colorPolicy':'new project neutral shading + project identity preview; source RGB not reused',
      'status':'EXPERIMENTAL_SOURCE_DERIVED_TEMPLATE_NEEDS_HUMAN_APPROVAL'
    }
    (d/'trace.json').write_text(json.dumps(trace,indent=2)+'\n')
    results[kind]={'source':sf,'template':nf,'preview':pf,'trace':trace}

# Contact: 3 types x source/template/identity-preview, all four directions
scale=10; tile=200; gap=12; labelw=345; rowh=220
rows=[]
for kind in ('BASEBALL','DAD','TRUCKER'):
    rows.extend([(kind,'SOURCE'),(kind,'SHAPE TEMPLATE'),(kind,'IDENTITY PREVIEW')])
W=labelw+4*(tile+gap)+25; H=68+len(rows)*rowh
sheet=Image.new('RGB',(W,H),'white'); dr=ImageDraw.Draw(sheet)
dr.text((10,8),'SELECTED CAP SOURCE CONSTRUCTIONS — source -> borrowed alpha -> project preview',fill='black')
dr.text((10,28),'Source RGB/design is NOT copied into the shape template. Alpha geometry is exact.',fill='black')
for i,v in enumerate(('FRONT','RIGHT','LEFT','BACK')):
    dr.text((labelw+i*(tile+gap)+74,48),v,fill='black')
y=68
for kind,stage in rows:
    src=SOURCES[kind]; data=results[kind]
    dr.text((10,y+38),f'{kind} — {stage}',fill='black')
    if stage=='SOURCE':
        dr.text((10,y+60),src['source'][:48],fill='black'); frames=data['source']
    elif stage=='SHAPE TEMPLATE':
        dr.text((10,y+60),'borrowed alpha only; new neutral shading',fill='black'); frames=data['template']
    else:
        extra='mesh/panel contract' if kind=='TRUCKER' else 'project-owned style preview'
        dr.text((10,y+60),extra,fill='black'); frames=data['preview']
    dr.text((10,y+82),f"alpha exact: {data['trace']['alphaExact']}",fill='black')
    for i,v in enumerate(VIEWS):
        big=frames[v].resize((tile,tile),Image.Resampling.NEAREST)
        sheet.paste(big,(labelw+i*(tile+gap),y),big)
    y+=rowh
contact=OUT/'SELECTED_CAP_TEMPLATES_CONTACT_X10.png'; sheet.save(contact)
chat=sheet.copy(); chat.thumbnail((1500,1800),Image.Resampling.LANCZOS); chat.save(OUT/'SELECTED_CAP_TEMPLATES_CONTACT_CHAT.png')

# Build QC pack but do not promote these into production catalog.
if PACK.exists(): shutil.rmtree(PACK)
(PACK/'Hats').mkdir(parents=True)
manifest={
 'Name':'RNG Cap Source Template QC','Author':'RNG Clothing project',
 'Version':'0.1.0','Description':'QC-only source-derived cap construction candidates. Not production.',
 'UniqueID':'RNGClothing.CapSourceTemplateQC','ContentPackFor':{'UniqueID':'PeacefulEnd.FashionSense'}
}
(PACK/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for kind in ('BASEBALL','DAD','TRUCKER'):
    d=PACK/'Hats'/kind; d.mkdir()
    stack(results[kind]['preview']).save(d/'hat.png')
    h={
      'Name':f'CAPAUDIT {kind}',
      'Tags':['CAP_SOURCE_AUDIT','QC ONLY',kind],
    }
    for i,(v,key) in enumerate(zip(VIEWS,('FrontHat','RightHat','LeftHat','BackHat'))):
      h[key]={
        'DisableGrayscale':True,'HideHair':False,
        'StartingPosition':{'X':0,'Y':i*20},
        'HeadPosition':{'X':0,'Y':0},
        'HatSize':{'Width':20,'Length':20},
      }
    (d/'hat.json').write_text(json.dumps(h,indent=2)+'\n')
(PACK/'TRACEABILITY.json').write_text(json.dumps({k:v['trace'] for k,v in results.items()},indent=2)+'\n')

print(contact)
print(OUT/'SELECTED_CAP_TEMPLATES_CONTACT_CHAT.png')
print('QC pack',PACK)
for k in results: print(k,results[k]['trace']['alphaExact'],results[k]['trace']['sourceAlphaHash'])
