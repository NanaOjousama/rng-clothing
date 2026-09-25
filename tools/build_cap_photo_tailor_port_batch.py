#!/usr/bin/env python3
from pathlib import Path
import importlib.util,json,shutil,sys
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from generator.cap_photo_tailor_pipeline import render_cap_family

OUT=ROOT/'experiments/cap_photo_tailor_port_batch_01'
PACK=ROOT/'test-packs/fashionsense/RNG-Cap-PhotoTailor-Port-QC'
VIEWS=('front','right','left','back')
spec=importlib.util.spec_from_file_location('audit',ROOT/'tools/build_cap_source_corpus_audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
BY_ID={c['id']:c for c in audit.CANDS}

ROWS=[
 ('baseball','MAS_CAP2',[(32,58,62),(61,103,108),(102,151,153),(168,205,200),(224,238,232)],'solid'),
 ('snapback','MAS_SNAP',[(30,35,46),(57,69,95),(92,114,153),(160,180,205),(235,231,208)],'colorblock'),
 ('boys_cap','RAGNAROK_BOYS',[(44,48,55),(75,87,102),(113,132,150),(166,184,198),(223,231,234)],'solid'),
 ('backwards','JED_BACK',[(40,52,48),(75,104,93),(119,153,136),(173,201,182),(230,239,229)],'solid'),
 ('dad','JED_VINTAGE',[(55,43,39),(100,74,63),(149,110,88),(195,159,128),(235,215,181)],'solid'),
 ('headphones_cap','JED_HEADPHONES',[(28,36,41),(55,77,83),(91,121,126),(148,174,175),(218,230,226)],'solid'),
 ('officer','JED_OFFICER',[(18,20,24),(35,39,47),(58,65,78),(94,104,119),(224,226,231)],'solid'),
 ('paperboy','MAS_PAPERBOY',[(42,45,50),(75,82,92),(111,123,136),(163,176,188),(222,229,234)],'plaid'),
]

def rows_of(im):
 a=np.array(im.convert('RGBA'),dtype=np.uint8)
 return [[tuple(map(int,a[y,x])) for x in range(a.shape[1])] for y in range(a.shape[0])]

def image_of(rows):
 return Image.fromarray(np.array(rows,dtype=np.uint8),'RGBA')

def stack(frames):
 out=Image.new('RGBA',(20,80),(0,0,0,0))
 for i,v in enumerate(VIEWS):out.alpha_composite(image_of(frames[v]),(0,i*20))
 return out

def hat_json(name):
 d={'Name':name,'Tags':['RNG Clothing','PHOTO TAILOR PORT','QC ONLY']}
 for i,key in enumerate(('FrontHat','RightHat','LeftHat','BackHat')):
  d[key]={'DisableGrayscale':True,'HideHair':False,
          'StartingPosition':{'X':0,'Y':i*20},
          'HeadPosition':{'X':0,'Y':0},
          'HatSize':{'Width':20,'Length':20}}
 return d

def main():
 if OUT.exists():shutil.rmtree(OUT)
 if PACK.exists():shutil.rmtree(PACK)
 OUT.mkdir(parents=True);(PACK/'Hats').mkdir(parents=True)
 rendered=[];rejected=[]
 for family,cid,palette,pattern in ROWS:
  src={v:rows_of(BY_ID[cid]['frames'][v]) for v in VIEWS}
  out,report=render_cap_family(src,family,palette,pattern)
  if not report.valid:
   rejected.append({'family':family,'source':cid,'errors':report.errors});continue

  d=OUT/family;d.mkdir()
  stack(out).save(d/'hat.png')
  for v in VIEWS:image_of(out[v]).save(d/f'{v}.png')
  trace={'family':family,'sourceId':cid,'pattern':pattern,
         'photoTailorPortUsed':report.photo_tailor_port_used,
         'alphaPreserved':report.alpha_preserved,
         'geometryAuthority':'source four-view construction',
         'renderAuthority':'Photo Tailor PreviewHat/Recolor direct Python port'}
  (d/'trace.json').write_text(json.dumps(trace,indent=2)+'\n')
  q=PACK/'Hats'/family;q.mkdir()
  stack(out).save(q/'hat.png')
  (q/'hat.json').write_text(json.dumps(hat_json('PT PORT '+family),indent=2)+'\n')
  rendered.append((family,cid,pattern,out))
 (OUT/'rejected.json').write_text(json.dumps(rejected,indent=2)+'\n')
 manifest={'Name':'RNG Cap Photo Tailor Port QC','Author':'RNG Clothing',
           'Version':'0.1.0','Description':'Direct Photo Tailor code-port cap rendering QC.',
           'UniqueID':'RNGClothing.CapPhotoTailorPortQC',
           'ContentPackFor':{'UniqueID':'PeacefulEnd.FashionSense'}}
 (PACK/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

 scale=10;tile=200;labelw=300;gap=12;rowh=225
 W=labelw+4*(tile+gap)+20;H=70+len(rendered)*rowh
 sheet=Image.new('RGB',(W,H),'white');dr=ImageDraw.Draw(sheet)
 dr.text((10,8),'CAPS — DIRECT PHOTO TAILOR CODE PORT',fill='black')
 dr.text((10,28),'PreviewHat/Recolor + FourFacing projection; source alpha locked',fill='black')
 for i,v in enumerate(('FRONT','RIGHT','LEFT','BACK')):
  dr.text((labelw+i*(tile+gap)+70,50),v,fill='black')
 y=70
 for family,cid,pattern,frames in rendered:
  dr.text((10,y+15),family.upper(),fill='black')
  dr.text((10,y+37),f'{cid}  pattern={pattern}',fill='black')
  for i,v in enumerate(VIEWS):
   im=image_of(frames[v]).resize((tile,tile),Image.Resampling.NEAREST)
   sheet.paste(im,(labelw+i*(tile+gap),y),im)
  y+=rowh
 sheet.save(OUT/'CAP_PT_PORT_CONTACT_X10.png')
 share=sheet.copy();share.thumbnail((1450,2100),Image.Resampling.LANCZOS)
 share.save(OUT/'CAP_PT_PORT_CONTACT_SHARE.jpg',quality=80,optimize=True)
 print('PASS',len(rendered),'rendered',len(rejected),'rejected')
 print(OUT/'CAP_PT_PORT_CONTACT_X10.png')

if __name__=='__main__':main()
