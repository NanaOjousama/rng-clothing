#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys,json,hashlib
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import cap_cleanroom_pixel_utils as pxu

OUT=ROOT/'experiments/cap_reboot/baseball_cap_cleanroom_04'
SIZE=20; SCALE=8; P=pxu.PALETTE

SPECS={
 'S1_STANDARD_ROUNDED':{
  'label':'S1 STANDARD / ROUNDED',
  'front_crown':{3:(8,11),4:(6,13),5:(5,14),6:(4,15),7:(4,15),8:(4,15),9:(4,15)},
  'front_brim':{9:(5,14),10:(2,17),11:(3,16),12:(5,14),13:(7,12)},
  'side_crown':{3:(9,11),4:(7,13),5:(6,14),6:(5,15),7:(5,15),8:(5,15),9:(5,15)},
  'side_brim':{9:(13,17),10:(12,18),11:(12,18),12:(13,17)},
  'back_crown':{3:(8,11),4:(6,13),5:(5,14),6:(4,15),7:(4,15),8:(4,15),9:(4,15),10:(4,15),11:(5,14)}
 },
 'S2_LOW_ROUNDED':{
  'label':'S2 LOWER / ROUNDED',
  'front_crown':{4:(7,12),5:(5,14),6:(4,15),7:(4,15),8:(4,15),9:(4,15)},
  'front_brim':{9:(5,14),10:(2,17),11:(3,16),12:(5,14),13:(7,12)},
  'side_crown':{4:(8,12),5:(6,14),6:(5,15),7:(5,15),8:(5,15),9:(5,15)},
  'side_brim':{9:(13,17),10:(12,18),11:(12,18),12:(13,17)},
  'back_crown':{4:(7,12),5:(5,14),6:(4,15),7:(4,15),8:(4,15),9:(4,15),10:(4,15),11:(5,14)}
 }
}

def layer(spans,facing):
    return pxu.shade(pxu.mask_from_spans(spans),facing)

def overlay(bottom,top):
    out=bottom.copy(); out.alpha_composite(top); return out

def add_button(img,top_y):
    y=max(1,top_y-1)
    img.putpixel((9,y),P['outline']); img.putpixel((10,y),P['outline'])

def front(spec):
    brim=layer(spec['front_brim'],'front')
    crown=layer(spec['front_crown'],'front')
    # small curved-panel hints only; no full center stripe
    for x,y in ((7,5),(12,5),(6,6),(13,6),(6,7),(13,7)):
        if crown.getpixel((x,y))[3]:
            crown.putpixel((x,y),P['shadow'])
    # tiny center top stitch, deliberately not full-height
    for x,y in ((9,4),(10,4)):
        if crown.getpixel((x,y))[3]:
            crown.putpixel((x,y),P['shadow'])
    img=overlay(brim,crown)
    add_button(img,min(spec['front_crown']))
    return img

def side(spec):
    brim=layer(spec['side_brim'],'right')
    crown=layer(spec['side_crown'],'right')
    for x,y in ((10,4),(10,5),(11,6),(11,7)):
        if crown.getpixel((x,y))[3]:
            crown.putpixel((x,y),P['shadow'])
    img=overlay(brim,crown)
    add_button(img,min(spec['side_crown']))
    return img

def back(spec):
    crown=layer(spec['back_crown'],'back')
    # subtle center seam above opening
    for y in range(min(spec['back_crown'])+2,9):
        if crown.getpixel((9,y))[3]:
            crown.putpixel((9,y),P['shadow'])
    px=crown.load()
    # compact 4x2 opening
    for y in (9,10):
        for x in range(8,12):
            px[x,y]=(0,0,0,0)
    # compact border + strap
    for x,y in ((8,8),(9,8),(10,8),(11,8),(7,9),(12,9)):
        px[x,y]=P['outline']
    for x in range(8,12):
        px[x,11]=P['shadow']
    px[8,11]=P['outline']; px[11,11]=P['outline']
    px[9,11]=P['light']
    add_button(crown,min(spec['back_crown']))
    return crown

def digest(im): return hashlib.sha256(im.tobytes()).hexdigest()

def sheet(results):
    cell=SIZE*SCALE; left=168; gap=16; top=55
    W=left+4*cell+3*gap+24; H=top+len(results)*(cell+44)+20
    out=Image.new('RGB',(W,H),(238,238,238)); d=ImageDraw.Draw(out)
    d.text((12,12),'BASEBALL CLEAN-ROOM 04 — USER REFERENCE REFINED',fill=(20,20,20))
    d.text((12,29),'rounded crown / reduced seams / compact rear opening',fill=(50,50,50))
    for i,t in enumerate(('FRONT','RIGHT','LEFT','BACK')):
        d.text((left+i*(cell+gap)+44,36),t,fill=(25,25,25))
    y=top
    for cid,(label,frames) in results.items():
        d.text((12,y+60),label,fill=(20,20,20))
        for i,v in enumerate(('front','right','left','back')):
            big=frames[v].resize((cell,cell),Image.Resampling.NEAREST)
            out.paste(big,(left+i*(cell+gap),y),big)
        y+=cell+44
    out.save(OUT/'BASEBALL_CLEANROOM_04_CONTACT_X8.png')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    results={}; items=[]
    for cid,s in SPECS.items():
        frames={'front':front(s),'right':side(s),'back':back(s)}
        frames['left']=pxu.mirror(frames['right'])
        for v,im in frames.items():
            pxu.validate_frame(im); im.save(OUT/f'{cid.lower()}_{v}.png')
        results[cid]=(s['label'],frames)
        items.append({'id':cid,'label':s['label'],
          'bboxByView':{v:list(im.getbbox()) for v,im in frames.items()},
          'sha256ByView':{v:digest(im) for v,im in frames.items()},
          'leftIsExactMirrorOfRight':digest(frames['left'])==digest(pxu.mirror(frames['right']))})
    sheet(results)
    manifest={'schema':'cap-cleanroom-baseball/v4','batch':'baseball_cap_cleanroom_04',
      'cleanroom':True,'construction':'BASEBALL_CAP','rendererTarget':'HAT_RENDERER_V1',
      'userReference':'baseball-cap-vector-template-set-uniform-fashion-blank-hat-design-sport-clothing_1284-44135.avif',
      'referenceUse':'SILHOUETTE_AND_CONSTRUCTION_STUDY_ONLY',
      'oldDadArtRead':False,'oldTruckerArtRead':False,
      'oldCapExperimentPixelsUsed':False,'sourceSpritePixelsUsed':False,
      'method':'FRESH_AUTHORED_GEOMETRY_REFERENCE_REFINED','candidates':items}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('wrote',OUT/'BASEBALL_CLEANROOM_04_CONTACT_X8.png')
    for i in items: print(i['id'],i['bboxByView'])

if __name__=='__main__': main()
