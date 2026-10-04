#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import hashlib, json
ROOT=Path('/run/media/deck/USD00/RNG_clothing')
SRC=ROOT/'experiments/rd_bucket_rotate_02_maroon'
OUT=ROOT/'authored/templates/bucket_maroon_rd8'
OUT.mkdir(parents=True, exist_ok=True)
views={
 'front':SRC/'source_17x17.png',
 'front_right':SRC/'cell_r0c2.png',
 'right':SRC/'cell_r1c0.png',
 'back_right':SRC/'cell_r2c2.png',
 'back':SRC/'cell_r2c1.png',
 'back_left':SRC/'cell_r2c0.png',
 'left':SRC/'cell_r1c2.png',
 'front_left':SRC/'cell_r0c0.png',
}
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def alpha_digest(im): return hashlib.sha256(im.getchannel('A').tobytes()).hexdigest()
meta={}
for name,src in views.items():
 im=Image.open(src).convert('RGBA'); bb=im.getbbox()
 if not bb: raise RuntimeError(f'empty: {src}')
 crop=im.crop(bb)
 canvas=Image.new('RGBA',(24,24),(0,0,0,0))
 x=(24-crop.width)//2; y=24-crop.height-1
 canvas.alpha_composite(crop,(x,y))
 dst=OUT/f'{name}.png'; canvas.save(dst)
 alpha=canvas.getchannel('A'); ap=alpha.load(); opaque={(xx,yy) for yy in range(24) for xx in range(24) if ap[xx,yy]>0}
 boundary=[]; interior=[]
 for xx,yy in sorted(opaque):
  if any((xx+dx,yy+dy) not in opaque for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))): boundary.append([xx,yy])
  else: interior.append([xx,yy])
 meta[name]={'path':str(dst.relative_to(ROOT)),'sha256':digest(dst),'alphaSha256':alpha_digest(canvas),'nativeTightSize':[crop.width,crop.height],'seat':[x,y],'boundaryCells':boundary,'interiorCells':interior}
(OUT/'frame_manifest.json').write_text(json.dumps({'schema':'rd8-construction-source/v1','id':'bucket_maroon_rd8','status':'CANDIDATE_PENDING_HUMAN_ART_APPROVAL','sourceRun':'experiments/rd_bucket_rotate_02_maroon','runtimeAuthority':['front','right','back','left'],'evidenceOnly':['front_right','back_right','back_left','front_left'],'notes':['No resampling; tight native sprites are only transparent-padded/bottom-centered to 24x24.','Front authority is the original user-supplied maroon source_17x17.png.','RD diagonal views are retained as rotation evidence/reference only.'],'frames':meta},indent=2))
print(OUT)
for k,v in meta.items(): print(k,v['nativeTightSize'],v['seat'])