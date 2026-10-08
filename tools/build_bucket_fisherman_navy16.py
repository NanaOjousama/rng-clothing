#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import hashlib, json, sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from v5.pngio import blank_image, blit, read_rgba_png, write_rgba_png

SEL_DIR=ROOT/'authored/approved/bucket_hat_v1/rotations/fisherman_navy/selected'
SELECTION=ROOT/'authored/approved/bucket_hat_v1/rotations/fisherman_navy/selection.json'
TD=ROOT/'authored/templates/bucket_fisherman_navy16'
CONTRACT=ROOT/'generator/data/templates/bucket_fisherman_navy16.json'
WEAR=ROOT/'generator/data/headwear/bucket_fisherman_navy16_wear_contract.json'
TINDEX=ROOT/'generator/data/templates/index.json'
LIB=ROOT/'generator/data/headwear/bucket_hat_approved_library.json'
MOD=ROOT/'mods/EnhancedSewingMachine'
TEX=MOD/'assets/qc/bucket_fisherman_navy16/base.png'
DEF=MOD/'assets/garments/qc/bucket_fisherman_navy16/base.json'
GINDEX=MOD/'assets/garments/index.json'

ID='bucket_fisherman_navy16'
FRAME=16
BOTTOM=12
RUNTIME=('front','right','back','left')
SOURCES={v:SEL_DIR/f'{v}_sprite.png' for v in RUNTIME}

def sha(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def alpha_sha(pixels)->str:
    payload=bytes(1 if px[3] else 0 for row in pixels for px in row)
    return hashlib.sha256(payload).hexdigest()

def bbox(pixels):
    pts=[(x,y) for y,row in enumerate(pixels) for x,p in enumerate(row) if p[3]]
    if not pts: return [0,0,0,0]
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return [min(xs),min(ys),max(xs)+1,max(ys)+1]

sel=json.loads(SELECTION.read_text())
for v,p in SOURCES.items():
    if not p.exists(): raise FileNotFoundError(p)
    expected=sel['sha256'][f'selected/{v}_sprite.png']
    if sha(p)!=expected: raise ValueError(f'{v}: selected source hash drift')

TD.mkdir(parents=True,exist_ok=True)
frames={}
for v,p in SOURCES.items():
    src=read_rgba_png(p)
    h=len(src); w=len(src[0])
    if w>FRAME or h>FRAME: raise ValueError(f'{v}: {w}x{h} exceeds {FRAME}x{FRAME}')
    # For odd-width side art on an even canvas, seat Left as the exact
    # canvas mirror of Right instead of independently floor-centering it.
    if v=='left':
        x=FRAME-w-frames['right']['seat'][0]
    else:
        x=(FRAME-w)//2
    y=BOTTOM-h+1
    canvas=blank_image(FRAME,FRAME)
    blit(canvas,src,x,y)
    out=TD/f'{v}.png'
    write_rgba_png(out,canvas)
    frames[v]={
        'path':str(out.relative_to(ROOT)),
        'sourcePath':str(p.relative_to(ROOT)),
        'sourceSha256':sha(p),
        'sha256':sha(out),
        'alphaSha256':alpha_sha(canvas),
        'nativeTightSize':[w,h],
        'seat':[x,y],
        'sourceOpaqueBBox':bbox(src),
    }

manifest={
 'schema':'cardinal-construction-source/v1',
 'id':ID,
 'status':'PRODUCTION_CONSTRUCTION_APPROVED',
 'sourceSelection':str(SELECTION.relative_to(ROOT)),
 'reviewSheet':'authored/approved/bucket_hat_v1/rotations/fisherman_navy/VIEWS_FISHERMAN_ALL.png',
 'runtimeAuthority':list(RUNTIME),
 'notes':[
   'User explicitly chose this four-view fisherman/bucket set as the first finished construction.',
   'Front is the exact approved navy fisherman source; Right is RD run1 r0c0; Back is RD run1 r2c1; Left is an exact horizontal mirror of Right.',
   'No source-art resampling or recoloring. Cardinal art is only transparent-padded and bottom-seated on a 16x16 presentation canvas.',
   'Production roll weight remains zero until live ESM wear QC is accepted.'
 ],
 'frames':frames
}
(TD/'frame_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

contract={
 'schema':'source-backed-template/v1','id':ID,'slot':'HEAD','category':'Hats','family':'bucket_hat',
 'frameSize':[FRAME,FRAME],
 'sourceIdentity':{
   'kind':'USER_APPROVED_DIRECTIONAL_TEMPLATE',
   'name':'Fisherman Navy 16',
   'selectionAuthority':str(SELECTION.relative_to(ROOT)),
   'runtimeOrder':list(RUNTIME)
 },
 'frameManifest':str((TD/'frame_manifest.json').relative_to(ROOT)),
 'frames':{v:{'path':frames[v]['path']} for v in RUNTIME},
 'geometryLock':{
   'authority':'the four cardinal frame files above','requiredViews':list(RUNTIME),
   'forbidResample':True,'forbidGenericNormalization':True,'forbidBaseAlphaRemoval':True,
   'notes':'16x16 is presentation canvas only; selected source pixels remain native and exact.'
 },
 'zones':{
   'surface':{'purpose':'whole fisherman/bucket body treatment','maskContract':str((TD/'frame_manifest.json').relative_to(ROOT))},
   'front_localized':{'purpose':'future localized front motif only','views':['front']},
   'protected_boundary':{'purpose':'silhouette boundary remains source-authoritative'}
 },
 'anchors':{v:{'contact_center':[8,BOTTOM]} for v in RUNTIME},
 'allowedPartKinds':['STYLE_PROFILE','PALETTE_TONE','MATERIAL_PATTERN','MOTIF','HARDWARE','REUSABLE_COMPONENT','ATTACHMENT'],
 'safeTransferRules':[
   'cardinal template owns crown/brim alpha and directional shape',
   'style and material changes are RGB-only inside opaque interior cells',
   'localized motifs require explicit cardinal visibility',
   'protected boundary cells remain source-exact',
   'neutral render must round-trip exactly'
 ],
 'incompatibilities':[
   {'scope':'ALTERNATE_CONSTRUCTION','deny':True},
   {'feature':'resample_to_fit','deny':True},
   {'feature':'generic_normalization','deny':True}
 ],
 'sourceTransferLibrary':'source_catalog/SOURCE_TRANSFER_LIBRARY.json',
 'photoTailorProfile':str((TD/'pt_profile.json').relative_to(ROOT)),
 'rendererContract':'generator/data/hat_renderer_contract.json',
 'rendererFamily':'bucket_fisherman',
 'wearContract':str(WEAR.relative_to(ROOT))
}
CONTRACT.write_text(json.dumps(contract,indent=2)+'\n')

wear={
 'schema':'rng-hat-wear-contract/v1','family':'bucket_hat','template':ID,
 'frameSize':[FRAME,FRAME],'runtime':'EnhancedSewingMachine','status':'APPROVED_LIVE_ESM_WEAR_QC',
 'baseRenderScale':1.0,
 'directionDefaults':{v:{'offset':([0,-4] if v=="front" else [0,0]),'fitScale':1.0} for v in RUNTIME},
 'note':'Native fisherman frames are already Stardew-scale. User-approved live fit bakes Front Y=-4 as the default authored offset; Right/Back/Left remain 0,0. RenderScale 1.0 preserves 4 display pixels per source pixel; no art resizing.',
 'hairPolicy':{'mode':'Obscured','authority':'wear-fit behavior only; not generator visual vocabulary','runtimeMapping':'Stardew Hat.hairDrawType = 1','appliesTo':['base']}
}
WEAR.write_text(json.dumps(wear,indent=2)+'\n')

idx=json.loads(TINDEX.read_text())
idx['templates'][ID]={
 'contract':str(CONTRACT.relative_to(ROOT)),'family':'bucket_hat','slot':'HEAD',
 'status':'PRODUCTION_READY',
 'constructionAuthority':'user-approved Fisherman Navy four-cardinal set; exact selected frames are hash-pinned',
 'humanArtApprovalRequired':False,'esmWearApprovalRequired':False,'liveWearApproved':True,
 'origin':'sf-approved-rotate/fisherman_views_all','sourceCategory':'Hats',
 'sourceName':'Fisherman Navy 16','humanArtApproved':True
}
TINDEX.write_text(json.dumps(idx,indent=2)+'\n')

lib=json.loads(LIB.read_text())
g=lib['constructionGroups']['sf_fisherman_compact']
g.update({
 'status':'PRODUCTION_PROMOTED',
 'note':'User selected and live-wear-approved this four-cardinal Fisherman Navy set as the first production construction. Intake stays fail-closed; active weighting is owned by generator/data/headwear/bucket_hat_production_registry.json.',
 'rollWeight':0,
 'authority':str(CONTRACT.relative_to(ROOT)),'productionRegistry':'generator/data/headwear/bucket_hat_production_registry.json',
 'directionalSelection':str(SELECTION.relative_to(ROOT))
})
LIB.write_text(json.dumps(lib,indent=2)+'\n')

# ESM QC texture: exact 16x16 template frames stacked Front/Right/Back/Left.
sheet=blank_image(FRAME,FRAME*4)
for i,v in enumerate(RUNTIME):
    blit(sheet,read_rgba_png(TD/f'{v}.png'),0,i*FRAME)
TEX.parent.mkdir(parents=True,exist_ok=True); write_rgba_png(TEX,sheet)
DEF.parent.mkdir(parents=True,exist_ok=True)
directions={}
for i,v in enumerate(RUNTIME):
    directions[v.title()]={'SourceX':0,'SourceY':i*FRAME,'AnchorX':8,'AnchorY':BOTTOM,'OffsetX':0,'OffsetY':(-4 if v=='front' else 0)}
definition={
 'Id':'qc.bucket.fisherman.navy16.base','Category':'Hat','DefinitionVersion':1,
 'WornTexture':'assets/qc/bucket_fisherman_navy16/base.png',
 'FrameWidth':FRAME,'FrameHeight':FRAME,'RenderScale':1.0,
 'VanillaReferenceAnchor':{'X':10,'Y':16},'HairMode':'Obscured',
 'Directions':directions,
 'Metadata':{
   'Family':'bucket_hat','Construction':'bucket_fisherman_navy16','Material':'source_backed',
   'Palette':'navy','Motif':'','GeneratorId':'BucketFishermanNavy16','GeneratorVersion':1,
   'GeneratorSeed':1,'Style':'approved-construction,wear-qc','QualityTier':'QC','Decals':'',
   'Classification':'PRODUCTION_CONSTRUCTION','Label':'FISHERMAN NAVY 16 - APPROVED CONSTRUCTION'
 }
}
DEF.write_text(json.dumps(definition,indent=2)+'\n')

gidx=json.loads(GINDEX.read_text())
rel='qc/bucket_fisherman_navy16/base.json'
gidx['Garments']=[x for x in gidx.get('Garments',[]) if x!=rel]+[rel]
GINDEX.write_text(json.dumps(gidx,indent=2)+'\n')

# Update directional selection to reflect that template + QC garment now exist.
sel['status']='PRODUCTION_CONSTRUCTION_APPROVED'
sel['reconfirmedOn']='2026-10-07'
sel['reconfirmedBy']='user ("finally, do it!")'
sel['templateAuthority']=str(CONTRACT.relative_to(ROOT))
sel['esmQcGarment']='qc.bucket.fisherman.navy16.base'
sel['notYet']=[]
sel['rollWeight']=0
sel['liveWearApprovedOn']='2026-10-07'
sel['liveWearApprovedBy']='user (fit approved)'
sel['productionRegistry']='generator/data/headwear/bucket_hat_production_registry.json'
SELECTION.write_text(json.dumps(sel,indent=2)+'\n')

print(json.dumps({
 'template':str(CONTRACT.relative_to(ROOT)),
 'manifest':str((TD/'frame_manifest.json').relative_to(ROOT)),
 'wearContract':str(WEAR.relative_to(ROOT)),
 'esmGarment':'qc.bucket.fisherman.navy16.base',
 'textureSha256':sha(TEX),
 'definitionSha256':sha(DEF)
},indent=2))
