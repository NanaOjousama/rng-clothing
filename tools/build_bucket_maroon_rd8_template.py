#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import hashlib,json
ROOT=Path('/run/media/deck/USD00/RNG_clothing'); SRC=ROOT/'experiments/rd_bucket_rotate_02_maroon'; OUT=ROOT/'authored/templates/bucket_maroon_rd8'; ATT=OUT/'attachments/chin_strap'
OUT.mkdir(parents=True,exist_ok=True); ATT.mkdir(parents=True,exist_ok=True)
views={'front':SRC/'source_17x17.png','front_right':SRC/'cell_r0c2.png','right':SRC/'cell_r1c0.png','back_right':SRC/'cell_r2c2.png','back':SRC/'cell_r2c1.png','back_left':SRC/'cell_r2c0.png','left':SRC/'cell_r1c2.png','front_left':SRC/'cell_r0c0.png'}
cuts={'front':17,'right':18,'back':21,'left':18}; runtime=set(cuts)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def asha(im): return hashlib.sha256(im.getchannel('A').tobytes()).hexdigest()
def seat(src):
 im=Image.open(src).convert('RGBA'); bb=im.getbbox(); crop=im.crop(bb); c=Image.new('RGBA',(24,24)); x=(24-crop.width)//2; y=23-crop.height; c.alpha_composite(crop,(x,y)); return c,[crop.width,crop.height],[x,y]
meta={}; att={'schema':'rng-directional-attachment/v1','id':'chin_strap','family':'bucket_maroon_rd8','views':{},'rule':'Optional overlay reconstructed from approved full cardinal source.'}
for name,src in views.items():
 full,native,pos=seat(src); final=full
 if name in runtime:
  fullp=OUT/f'{name}_with_strap_source.png'; full.save(fullp)
  base=full.copy(); ov=Image.new('RGBA',(24,24)); cut=cuts[name]
  for y in range(cut,24):
   for x in range(24):
    px=full.getpixel((x,y))
    if px[3]: ov.putpixel((x,y),px); base.putpixel((x,y),(0,0,0,0))
  final=base; op=ATT/f'{name}.png'; ov.save(op)
  att['views'][name]={'baseCutY':cut,'overlayPath':str(op.relative_to(ROOT)),'sourceFullPath':str(fullp.relative_to(ROOT)),'overlayOpaqueCells':sum(1 for px in ov.getdata() if px[3])}
 dst=OUT/f'{name}.png'; final.save(dst); a=final.getchannel('A'); p=a.load(); opaque={(x,y) for y in range(24) for x in range(24) if p[x,y]>0}; boundary=[]; interior=[]
 for x,y in sorted(opaque): (boundary if any((x+dx,y+dy) not in opaque for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))) else interior).append([x,y])
 meta[name]={'path':str(dst.relative_to(ROOT)),'sha256':sha(dst),'alphaSha256':asha(final),'nativeTightSize':native,'seat':pos,'boundaryCells':boundary,'interiorCells':interior}
(ATT/'manifest.json').write_text(json.dumps(att,indent=2)+'\n')
(OUT/'frame_manifest.json').write_text(json.dumps({'schema':'rd8-construction-source/v2','id':'bucket_maroon_rd8','status':'HUMAN_ART_APPROVED_PENDING_WEAR_QC','sourceRun':'experiments/rd_bucket_rotate_02_maroon','runtimeAuthority':['front','right','back','left'],'evidenceOnly':['front_right','back_right','back_left','front_left'],'optionalAttachments':['chin_strap'],'notes':['Runtime cardinal base excludes chin strap.','chin_strap is an optional directional overlay roll.','Full approved source views are retained as *_with_strap_source.png.','No resampling; sprites are transparent-padded/bottom-centered only.'],'frames':meta},indent=2)+'\n')
print('built bucket_maroon_rd8 base + optional chin_strap')
