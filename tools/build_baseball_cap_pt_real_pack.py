#!/usr/bin/env python3
from pathlib import Path
import json, shutil
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
PTGEN=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods/PhotoTailor/generated')
OUT=ROOT/'experiments/cap_reboot/baseball_cap_pt_real_01'
PACK=ROOT/'test-packs/fashionsense/RNG-Cap-Reboot-Baseball-PT-REAL-01'
GAME=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley')
INSTALL=GAME/'Mods/[FS] RNG Cap Reboot Baseball PT REAL 01'

CANDS=[
 ('PLAIN_FRONT','Baseball PT Real - Plain', 'Robin.PhotoTailor_personal_20260925032118_00_hat.png'),
 ('COLORED_FRONT','Baseball PT Real - Colored Front', 'Robin.PhotoTailor_personal_20260925032204_00_hat.png'),
 ('COLORED_SIDE','Baseball PT Real - Colored Side', 'Robin.PhotoTailor_personal_20260925032207_00_hat.png'),
]
def hat_json(name):
    out={'Name':name,'Tags':['RNG Clothing','CAP_REBOOT','BASEBALL','PHOTO_TAILOR','REAL_PT']}
    for key,y in [('FrontHat',0),('RightHat',20),('LeftHat',40),('BackHat',60)]:
        out[key]={
          'DisableGrayscale':True,
          'HideHair':False,
          'HatSize':{'Width':20,'Length':20},
          'StartingPosition':{'X':0,'Y':y},
          'HeadPosition':{'X':0,'Y':-2},
        }
    return out

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if PACK.exists(): shutil.rmtree(PACK)
    PACK.mkdir(parents=True)
    for old in [
      GAME/'Mods/[FS] RNG Cap Reboot Baseball PT 04',
      GAME/'Mods/[FS] RNG Cap Reboot Baseball Cleanroom 04',
    ]:
      if old.exists(): shutil.rmtree(old)
    manifest={
      'Name':'RNG Cap Reboot Baseball PT REAL 01',
      'Author':'RNG Clothing / actual Photo Tailor output',
      'Version':'1.0.0',
      'Description':'Raw Photo Tailor 0.15.1 cap outputs copied unchanged for worn QC.',
      'UniqueID':'RNGClothing.FashionSense.BaseballPTReal01',
      'UpdateKeys':[],
      'ContentPackFor':{'UniqueID':'PeacefulEnd.FashionSense','MinimumVersion':'7.5.0'},
    }
    (PACK/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

    rows=[]
    summaries={}
    for cid,name,srcname in CANDS:
      src=PTGEN/srcname
      im=Image.open(src).convert('RGBA')
      assert im.size==(20,80)
      cdir=PACK/'Hats'/cid
      cdir.mkdir(parents=True)
      shutil.copy2(src,cdir/'hat.png')
      (cdir/'hat.json').write_text(json.dumps(hat_json(name),indent=2)+'\n')
      shutil.copy2(src,OUT/f'{cid.lower()}_raw_pt.png')
      spec_path=PTGEN/srcname.replace('.png','.spec.json')
      spec=json.loads(spec_path.read_text())
      summaries[cid]={k:spec.get(k) for k in ('name','category','semantic_description','primary_color','secondary_color','accent_color','pattern','silhouette','coverage','confidence')}
      rows.append((name,im))
    scale=12; left=250; gap=36
    w=left+20*scale+30
    h=20+sum(80*scale+gap for _ in rows)
    sheet=Image.new('RGB',(w,h),'white'); d=ImageDraw.Draw(sheet); y=10
    for name,im in rows:
      d.text((10,y+20),name,fill='black')
      big=im.resize((20*scale,80*scale),Image.Resampling.NEAREST)
      sheet.paste(big,(left,y),big)
      y+=80*scale+gap
    sheet.save(OUT/'PT_REAL_CAP_CONTACT_X12.png')

    (OUT/'pt_spec_summary.json').write_text(json.dumps(summaries,indent=2)+'\n')

    trace={
      'schema':'baseball-cap-pt-real/v1',
      'photoTailorVersion':'0.15.1',
      'actualPhotoTailorRendererUsed':True,
      'customRendererUsed':False,
      'silhouetteForcedToCap':True,
      'pixelsModifiedAfterPhotoTailor':False,
      'candidates':[{'id':cid,'source':src} for cid,_,src in CANDS],
      'status':'CANDIDATE_WORN_QC',
    }
    (OUT/'manifest.json').write_text(json.dumps(trace,indent=2)+'\n')
    (PACK/'TRACEABILITY.json').write_text(json.dumps(trace,indent=2)+'\n')
    if INSTALL.exists(): shutil.rmtree(INSTALL)
    shutil.copytree(PACK,INSTALL)
    print('built',PACK)
    print('installed',INSTALL)
    print('contact',OUT/'PT_REAL_CAP_CONTACT_X12.png')

if __name__=='__main__':
    main()
