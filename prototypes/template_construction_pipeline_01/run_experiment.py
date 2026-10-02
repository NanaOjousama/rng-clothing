#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, subprocess, sys
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
TRACE=ROOT/'prototypes/photo_tailor_source_identity_01/trucker_reference_trace_26_02'
HEAD=ROOT/'experiments/pixellab/head_guides'
FIT=ROOT/'prototypes/photo_tailor_source_identity_01/trucker_wear_fit_proof_01/fit_contract.json'
OUT=HERE/'run_trucker_benchmark_01'
VIEWS=('front','right','back','left')
sys.path.insert(0,str(ROOT))
from generator.photo_tailor_port import recolor_four_facing

PALETTE=[(145,151,158),(166,173,180),(188,195,201),(211,216,221),(232,235,238)]

def rows(im):
 a=im.convert('RGBA'); return [[a.getpixel((x,y)) for x in range(a.width)] for y in range(a.height)]
def image(rs):
 h=len(rs); w=len(rs[0]); im=Image.new('RGBA',(w,h)); im.putdata([p for r in rs for p in r]); return im

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def largest_share(im):
 a=im.getchannel('A'); pts={(x,y) for y in range(im.height) for x in range(im.width) if a.getpixel((x,y))>15}
 if not pts:return 0.0
 unseen=set(pts); best=0
 while unseen:
  q=[unseen.pop()]; n=0
  while q:
   x,y=q.pop(); n+=1
   for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
    if p in unseen: unseen.remove(p); q.append(p)
  best=max(best,n)
 return best/len(pts)

def contact(frames,path,title):
 scale=9; tile=26*scale; pad=12; W=pad+4*(tile+pad); H=tile+70
 out=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(out); d.text((10,8),title,fill='black')
 for i,v in enumerate(VIEWS):
  x=pad+i*(tile+pad); d.text((x+88,30),v.upper(),fill='black')
  src=frames[v].resize((tile,tile),Image.Resampling.NEAREST); out.paste(src,(x,50),src)
 out.save(path)

def paint_scaled(canvas,sprite,sx,sy,ox,oy):
 for y in range(sprite.height):
  for x in range(sprite.width):
   p=sprite.getpixel((x,y))
   if p[3]==0: continue
   block=Image.new('RGBA',(sx,sy),p); canvas.alpha_composite(block,(ox+x*sx,oy+y*sy))

def wear_sheet(frames,path):
 fit=json.loads(FIT.read_text())['after']; base=12; head_origin=(60,144)
 cell=(312,360); pad=8; sheet=Image.new('RGB',(4*cell[0]+5*pad,cell[1]+60),(239,238,233)); d=ImageDraw.Draw(sheet)
 d.text((8,8),'TEMPLATE PIPELINE - STARDew FARMER FIT PREVIEW',fill='black')
 for i,v in enumerate(VIEWS):
  x0=pad+i*(cell[0]+pad); d.text((x0+135,28),v.upper(),fill='black')
  c=Image.new('RGBA',cell,(0,0,0,0)); head=Image.open(HEAD/f'farmer_head_{v}_hair.png').convert('RGBA')
  paint_scaled(c,head,base,base,*head_origin)
  t=fit[v]; paint_scaled(c,frames[v],t['scaleX'],t['scaleY'],t['offsetX'],t['offsetY'])
  flat=Image.new('RGB',cell,(239,238,233)); flat.paste(c,(0,0),c); sheet.paste(flat,(x0,50))
 sheet.save(path)

def main():
 OUT.mkdir(parents=True,exist_ok=True); (OUT/'template_frames').mkdir(exist_ok=True)
 subprocess.run([sys.executable,str(TRACE/'build_trace.py')],check=True)
 src={v:Image.open(TRACE/'generated'/f'{v}.png').convert('RGBA') for v in VIEWS}
 styled_rows=recolor_four_facing({v:rows(src[v]) for v in VIEWS},pattern='solid',palette=PALETTE)
 styled={v:image(styled_rows[v]) for v in VIEWS}
 for v in VIEWS: styled[v].save(OUT/'template_frames'/f'{v}.png')
 contact(src,OUT/'01_source_geometry.png','STAGE 1 - SOURCE-DERIVED CONSTRUCTION GEOMETRY')
 contact(styled,OUT/'02_photo_tailor_normalized.png','STAGE 2 - PHOTO TAILOR NORMALIZED / GEOMETRY LOCKED')
 wear_sheet(styled,OUT/'03_stardew_fit_preview.png')

 qc={}
 for v in VIEWS:
  im=styled[v]; a=im.getchannel('A'); box=a.getbbox(); opaque=sum(1 for p in a.getdata() if p>15)
  qc[v]={'size':list(im.size),'bbox':list(box) if box else None,'opaquePixels':opaque,'largestComponentShare':round(largest_share(im),4)}
 qc['leftMirrorsRight']=list(styled['left'].getdata())==[styled['right'].getpixel((25-x,y)) for y in range(26) for x in range(26)]
 qc['technicalPass']=all(qc[v]['size']==[26,26] and qc[v]['opaquePixels']>=40 and qc[v]['largestComponentShare']>=0.90 for v in VIEWS) and qc['leftMirrorsRight']
 contract={'schema':'experimental-construction-template/v1','id':'trucker_multistage_benchmark_01','family':'trucker_cap','status':'EXPERIMENTAL_CANDIDATE','frameSize':[26,26],
  'pipeline':['reference-view segmentation','source-derived silhouette reduction','semantic component mapping','Photo Tailor four-facing normalization','Stardew farmer wear-space fit'],
  'viewProvider':{'kind':'KNOWN_REFERENCE_BENCHMARK','note':'Front/right/back are known references; left mirrors right. Replaceable by multiview AI provider when available.'},
  'geometryAuthority':'source-derived frames; Photo Tailor is forbidden from changing alpha',
  'frames':{v:{'path':f'template_frames/{v}.png','sha256':sha(OUT/'template_frames'/f'{v}.png')} for v in VIEWS},
  'wearContract':json.loads(FIT.read_text())['after'],'qc':qc,
  'promotionRule':'Do not promote automatically. Requires visual approval in Stardew/in-game QC.'}
 (OUT/'construction_template.json').write_text(json.dumps(contract,indent=2)+'\n')
 (OUT/'RESULT.txt').write_text(('TECHNICAL PASS\n' if qc['technicalPass'] else 'TECHNICAL FAIL\n')+'See 03_stardew_fit_preview.png and construction_template.json\n')
 print(json.dumps(qc,indent=2)); print('OUTPUT',OUT)

if __name__=='__main__': main()
