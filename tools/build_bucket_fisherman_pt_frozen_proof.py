#!/usr/bin/env python3
from __future__ import annotations
import hashlib,itertools,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from generator.taste_policy import evaluate_recipe
from generator.hat_hybrid_enhancements import enhance_frames
from v5.source.template_transfer import load_contract,template_frames,alpha_cells
from v5.pngio import blank_image,blit,draw_text,nearest_scale,read_rgba_png,write_rgba_png

PROFILE=ROOT/'authored/templates/bucket_fisherman_navy16/pt_profile.json'
POLICY=ROOT/'generator/data/headwear/bucket_fisherman_hat_renderer_v1_policy.json'
CONTRACT=ROOT/'generator/data/templates/bucket_fisherman_navy16.json'
OUT=ROOT/'experiments/bucket_fisherman_pt_frozen_01'
VIEWS=('front','right','back','left')
RARITIES=('common','uncommon','rare','epic')
SEEDS={'common':[2101,2102,2103],'uncommon':[2201,2202,2203],'rare':[2301,2302,2303],'epic':[2401,2402,2403]}
PALETTE_BY_RARITY={
 'common':['navy_source_native','cream','olive_canvas'],
 'uncommon':['rain_yellow','rust','pastel_pink'],
 'rare':['olive_canvas','cream','rust'],
 'epic':['navy_source_native','pastel_pink','rain_yellow'],
}

def idx(key,n):return int(hashlib.sha256(key.encode()).hexdigest()[:12],16)%n

def legal_pool(policy,rarity):
 axes=list(policy['vocabulary'])
 rows=[]
 for vals in itertools.product(*(policy['vocabulary'][a] for a in axes)):
  rec=dict(zip(axes,vals));rep=evaluate_recipe(rec,rarity,policy)
  if rep.valid:rows.append((rec,rep))
 if not rows:raise RuntimeError(f'no legal recipe for {rarity}')
 high=max(rep.complexity for rec,rep in rows)
 return [(r,p) for r,p in rows if p.complexity>=max(0,high-1)]

def render_pt_golden(base,profile,palette_id):
 if palette_id=='navy_source_native':
  return {v:[list(row) for row in base[v]] for v in VIEWS}
 pinfo=profile['candidatePalettes'][palette_id]
 ramp=[tuple(x) for x in pinfo['ptShadeRamp']]
 outline=tuple(pinfo['outlineColor'])
 role_color={'outline':outline,'shadow':ramp[1],'mid':ramp[2],'light':ramp[3],'highlight':ramp[4]}
 out={v:[list(row) for row in base[v]] for v in VIEWS}
 for v in VIEWS:
  for role,cells in profile['views'][v]['shadeRoles'].items():
   rgb=role_color[role]
   for x,y in cells:
    a=out[v][y][x][3];out[v][y][x]=(*rgb,a)
 # Construction contract: left is exact mirror of right.
 out['left']=[list(reversed(row)) for row in out['right']]
 return out

def crop(fr):
 pts=[(x,y) for y,row in enumerate(fr) for x,p in enumerate(row) if p[3]]
 x0=min(x for x,y in pts);x1=max(x for x,y in pts);y0=min(y for x,y in pts);y1=max(y for x,y in pts)
 return [row[x0:x1+1] for row in fr[y0:y1+1]]

def alpha_equal(a,b):return alpha_cells(a)==alpha_cells(b)

def main():
 if OUT.exists():shutil.rmtree(OUT)
 OUT.mkdir(parents=True)
 profile=json.load(open(PROFILE));policy=json.load(open(POLICY))
 base=template_frames(load_contract(CONTRACT))
 manifest={
  'schema':'bucket-fisherman-pt-frozen-proof/v1',
  'status':'CANDIDATE_REVIEW_REQUIRED',
  'construction':'bucket_fisherman_navy16',
  'photoTailor':{
   'used':True,
   'authority':'generator/photo_tailor_port.py permission-backed mechanics',
   'profile':str(PROFILE.relative_to(ROOT)),
   'role':'candidate golden shading-role/topology analysis and PT HSL shade ramps; construction alpha untouched'
  },
  'frozenRenderer':{
   'used':True,
   'contract':'generator/data/hat_renderer_contract.json',
   'id':'HAT_RENDERER_V1',
   'hybridModule':'generator/hat_hybrid_enhancements.py',
   'sourceFamily':'bucket_fisherman',
   'tasteEvaluator':'generator/taste_policy.py',
   'policy':str(POLICY.relative_to(ROOT))
  },
  'oldRejectedRendererImported':False,
  'candidates':[]
 }
 rows=[]
 for rarity in RARITIES:
  pool=legal_pool(policy,rarity)
  for n,seed in enumerate(SEEDS[rarity]):
   recipe,rep=pool[idx(f'{rarity}|{seed}|recipe',len(pool))]
   palette_id=PALETTE_BY_RARITY[rarity][n]
   golden=render_pt_golden(base,profile,palette_id)
   final,enh=enhance_frames(golden,'bucket_fisherman',recipe,rarity)
   # Fisherman construction explicitly locks Left to mirrored Right.
   final['left']=[list(reversed(row)) for row in final['right']]
   golden['left']=[list(reversed(row)) for row in golden['right']]
   for v in VIEWS:
    if not alpha_equal(base[v],golden[v]):raise RuntimeError(f'{rarity}/{seed}/{v}: PT golden alpha drift')
    if not alpha_equal(base[v],final[v]):raise RuntimeError(f'{rarity}/{seed}/{v}: frozen hybrid alpha drift')
   if final['left']!=[list(reversed(row)) for row in final['right']]:raise RuntimeError('left mirror drift')
   d=OUT/f'{rarity}_{seed}';d.mkdir()
   for v in VIEWS:
    write_rgba_png(d/f'{v}.png',final[v])
    write_rgba_png(d/f'golden_{v}.png',golden[v])
   row={
    'rarity':rarity,'seed':seed,'palette':palette_id,'recipe':recipe,
    'taste':{'complexity':rep.complexity,'budget':[rep.budget_min,rep.budget_max],
             'channels':list(rep.active_channels),'primary':rep.primary,
             'secondary':list(rep.secondary),'accents':list(rep.accents)},
    'hybrid':{
      'applied':enh.applied,'fallbackReason':enh.fallback_reason,
      'changedPixels':enh.changed_pixels,'changedRatio':round(enh.changed_ratio,6),
      'outlinePreserved':enh.outline_preserved,'alphaPreserved':enh.alpha_preserved,
      'pattern':enh.pattern,'motif':enh.motif,'motifPlacement':enh.motif_placement,
      'regionMode':enh.region_mode,
    },
    'frames':{v:str((d/f'{v}.png').relative_to(ROOT)) for v in VIEWS},
    'goldenFrames':{v:str((d/f'golden_{v}.png').relative_to(ROOT)) for v in VIEWS},
   }
   (d/'recipe.json').write_text(json.dumps(row,indent=2)+'\n')
   manifest['candidates'].append(row);rows.append((row,final,golden))
 # front overview
 cw,ch=205,158;sheet=blank_image(cw*3,ch*4,(238,236,229,255))
 for i,(row,final,golden) in enumerate(rows):
  x=(i%3)*cw;y=(i//3)*ch
  fr=crop(final['front']);big=nearest_scale(fr,8)
  blit(sheet,big,x+(cw-len(big[0]))//2,y+28+(95-len(big))//2)
  draw_text(sheet,f"{row['rarity'].upper()} {row['seed']} {row['palette']}",x+4,y+4,scale=1)
  draw_text(sheet,f"{row['recipe']['pattern']} / {row['recipe']['trim']}",x+4,y+130,scale=1)
  draw_text(sheet,f"{row['recipe']['motif']} {row['recipe']['motifPlacement']}",x+4,y+142,scale=1)
 front=OUT/'PT_FROZEN_FRONT_12.png';write_rgba_png(front,sheet)
 # four-view sheet, one selected row per rarity (middle seed)
 cw,ch=190,160;sheet=blank_image(cw*4,ch*4,(238,236,229,255))
 chosen=[rows[1],rows[4],rows[7],rows[10]]
 for ry,(row,final,golden) in enumerate(chosen):
  for cx,v in enumerate(VIEWS):
   fr=crop(final[v]);big=nearest_scale(fr,8)
   blit(sheet,big,cx*cw+(cw-len(big[0]))//2,ry*ch+34+(95-len(big))//2)
   if ry==0:draw_text(sheet,v.upper(),cx*cw+4,4,scale=1)
  draw_text(sheet,f"{row['rarity'].upper()} {row['palette']}",4,ry*ch+18,scale=1)
  draw_text(sheet,f"{row['recipe']['pattern']} {row['recipe']['trim']} {row['recipe']['motif']}",4,ry*ch+142,scale=1)
 dirs=OUT/'PT_FROZEN_4VIEW_BY_RARITY.png';write_rgba_png(dirs,sheet)
 manifest['candidateCount']=len(rows);manifest['contactSheets']=[str(front.relative_to(ROOT)),str(dirs.relative_to(ROOT))]
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('PASS',len(rows),'Photo Tailor + HAT_RENDERER_V1 Fisherman candidates')
 print(front);print(dirs)
if __name__=='__main__':main()
