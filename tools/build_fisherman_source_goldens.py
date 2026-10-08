#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from generator.fisherman_source_family import render,load_spec
from v5.pngio import blank_image,blit,draw_text,nearest_scale,write_rgba_png
OUT=ROOT/'experiments/fisherman_source_goldens_candidate_02'
REG=ROOT/'generator/data/source_respecting_hat_goldens_fisherman_candidate.json'
PALETTES=('source_native','cream','olive_canvas','rain_yellow')
VIEWS=('front','right','back','left')

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def crop(fr):
 pts=[(x,y) for y,row in enumerate(fr) for x,p in enumerate(row) if p[3]]
 x0=min(x for x,y in pts);x1=max(x for x,y in pts);y0=min(y for x,y in pts);y1=max(y for x,y in pts)
 return [row[x0:x1+1] for row in fr[y0:y1+1]]

def main():
 if OUT.exists(): shutil.rmtree(OUT)
 OUT.mkdir(parents=True)
 spec=load_spec(); rows=[]
 for pal in PALETTES:
  res=render(palette=pal); d=OUT/pal; d.mkdir()
  for v in VIEWS: write_rgba_png(d/f'{v}.png',res.frames[v])
  row={
   'state':res.source_state,'palette':pal,
   'status':'SOURCE_STATE_ALREADY_APPROVED' if pal=='source_native' else 'CANDIDATE_REVIEW_REQUIRED',
   'sourceShadingTopologyPreserved':True,
   'trace':res.trace,
   'frames':{v:str((d/f'{v}.png').relative_to(ROOT)) for v in VIEWS},
   'hashes':{v:sha(d/f'{v}.png') for v in VIEWS},
  }
  (d/'candidate.json').write_text(json.dumps(row,indent=2)+'\n')
  rows.append(row)

 cw,ch=190,150
 sheet=blank_image(cw*4,ch*4,(238,236,229,255))
 for ry,row in enumerate(rows):
  for cx,v in enumerate(VIEWS):
   fr=crop(__import__('v5.pngio',fromlist=['read_rgba_png']).read_rgba_png(ROOT/row['frames'][v]))
   big=nearest_scale(fr,8)
   blit(sheet,big,cx*cw+(cw-len(big[0]))//2,ry*ch+38+(90-len(big))//2)
   if ry==0: draw_text(sheet,v.upper(),cx*cw+5,4,scale=1)
  draw_text(sheet,row['palette'].upper(),5,ry*ch+20,scale=1)
  draw_text(sheet,'EXACT SOURCE' if row['palette']=='source_native' else 'CONTINUOUS SOURCE SHADING',5,ry*ch+134,scale=1)
 contact=OUT/'FISHERMAN_SOURCE_GOLDENS_4X4.png';write_rgba_png(contact,sheet)

 registry={
  'schema':'source-respecting-hat-golden-candidates/v1',
  'templateFamily':'bucket_fisherman_navy16',
  'sourceFamily':'bucket_fisherman',
  'status':'HUMAN_VISUAL_APPROVAL_REQUIRED',
  'sourceState':spec['base'],
  'sourceStateHumanApproved':True,
  'sourceStateAuthority':'authored/templates/bucket_fisherman_navy16/{front,right,back,left}.png',
  'goldenBaselineAfterApproval':'HAT_PRODUCTION_GOLDEN_V1',
  'productionAuthorityAfterApproval':'GOLDEN_SOURCE_RESPECTING_HYBRID_V1',
  'candidatePairs':[{k:r[k] for k in ('state','palette','status','frames','hashes')} for r in rows],
  'rules':{
   'sourceShadingTopologyAuthority':'CONTINUOUS_SOURCE_LUMA_NO_BUCKETS',
   'photoTailorRole':'approved donor palette evidence only',
   'genericProjectionAllowed':False,
   'genericLineSynthesisAllowed':False,
   'alphaGeometryLocked':True,
   'rightLeftMirrorLocked':True,
  },
  'contactSheet':str(contact.relative_to(ROOT)),
  'activationGate':'User visually approves candidate palette goldens before any non-native pair enters production whitelist.',
 }
 REG.write_text(json.dumps(registry,indent=2)+'\n')
 manifest={'schema':'fisherman-source-golden-proof/v1','candidateCount':len(rows),'registry':str(REG.relative_to(ROOT)),
           'contactSheet':str(contact.relative_to(ROOT)),'candidates':rows}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('PASS built',len(rows),'Fisherman source-golden candidates')
 print('CONTACT',contact)
 print('REGISTRY',REG)
if __name__=='__main__':main()
