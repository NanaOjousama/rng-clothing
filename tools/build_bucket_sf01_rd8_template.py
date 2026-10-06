#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from generator.png_utils import read_rgba_png, blank_image, blit, write_rgba_png, nearest_scale, draw_text

SRC = ROOT / 'authored/approved/bucket_hat_v1/rotations/01'
FRONT = ROOT / 'authored/approved/bucket_hat_v1/sources/construction_sf01_06_01_cream_split_droop.png'
OUT = ROOT / 'authored/templates/bucket_sf01_rd8'
OUT.mkdir(parents=True, exist_ok=True)
FS = 24

# RD rotate mapping follows the already-proven maroon RD8 orientation contract.
views = {
    'front': FRONT,
    'front_right': SRC / 'r0c2_snapped.png',
    'right': SRC / 'r1c0_snapped.png',
    'back_right': SRC / 'r2c2_snapped.png',
    'back': SRC / 'r2c1_snapped.png',
    'back_left': SRC / 'r2c0_snapped.png',
    'left': SRC / 'r1c2_snapped.png',
    'front_left': SRC / 'r0c0_snapped.png',
}

def tight(pix):
    ys=[]; xs=[]
    for y,row in enumerate(pix):
        for x,px in enumerate(row):
            if px[3]: xs.append(x); ys.append(y)
    if not xs: raise ValueError('empty image')
    x0,x1=min(xs),max(xs); y0,y1=min(ys),max(ys)
    return [row[x0:x1+1] for row in pix[y0:y1+1]], [x0,y0,x1+1,y1+1]

def seat(path):
    rec=read_rgba_png(path); crop,bbox=tight(rec['pixels'])
    h=len(crop); w=len(crop[0])
    if w>FS or h>FS: raise ValueError(f'{path}: tight {w}x{h} exceeds {FS}')
    canvas=blank_image(FS,FS)
    x=(FS-w)//2; y=FS-1-h
    blit(canvas,crop,x,y)
    return canvas,[w,h],[x,y],bbox

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def alpha_sha(pix):
    b=bytes(px[3] for row in pix for px in row)
    return hashlib.sha256(b).hexdigest()

frames={}
for name,path in views.items():
    pix,native,pos,bbox=seat(path)
    dst=OUT/f'{name}.png'; write_rgba_png(dst,pix)
    frames[name]={
        'path':str(dst.relative_to(ROOT)),
        'sourcePath':str(path.relative_to(ROOT)),
        'sourceSha256':sha(path),
        'sha256':sha(dst),
        'alphaSha256':alpha_sha(pix),
        'nativeTightSize':native,
        'seat':pos,
        'sourceOpaqueBBox':bbox,
    }

manifest={
    'schema':'rd8-construction-source/v1',
    'id':'bucket_sf01_rd8',
    'status':'HUMAN_ART_APPROVED_PENDING_WEAR_QC',
    'sourceRun':'authored/approved/bucket_hat_v1/rotations/01',
    'provenanceOrigin':'experiments/sf_approved_rotate/01',
    'frontAuthority':str(FRONT.relative_to(ROOT)),
    'runtimeAuthority':['front','right','back','left'],
    'evidenceOnly':['front_right','back_right','back_left','front_left'],
    'rdFrontEvidence':'authored/approved/bucket_hat_v1/rotations/01/r0c1_snapped.png',
    'notes':[
        'User supplied this folder as the completed Hat 01 rotation.',
        'Exact approved source front remains front authority; RD front is evidence only.',
        'No resampling. Native pixels are only cropped to alpha bounds and transparent-padded/bottom-seated on 24x24.',
        'Production remains disabled until ESM wear QC passes.'
    ],
    'frames':frames,
}
(OUT/'frame_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

# Cardinal review board, nearest-neighbor only.
order=['front','right','back','left']; labels=['FRONT exact','RIGHT','BACK','LEFT']
cellw,cellh=260,260
sheet=blank_image(cellw*4,cellh,(239,236,228,255))
for i,(v,label) in enumerate(zip(order,labels)):
    pix=read_rgba_png(OUT/f'{v}.png')['pixels']; up=nearest_scale(pix,8)
    x=i*cellw+(cellw-len(up[0]))//2; y=38
    blit(sheet,up,x,y)
    draw_text(sheet,label,i*cellw+8,8,scale=2,color=(55,50,45,255))
    n=frames[v]['nativeTightSize']; draw_text(sheet,f'{n[0]}X{n[1]}',i*cellw+8,225,scale=2,color=(80,73,65,255))
board=ROOT/'experiments/sf_approved_rotate/01/BUCKET01_FINAL_CARDINAL_X8.png'; write_rgba_png(board,sheet)
print('built', OUT.relative_to(ROOT))
print('review', board.relative_to(ROOT))
