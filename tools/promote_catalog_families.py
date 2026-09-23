#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from v5.pngio import read_rgba_png

CAT=ROOT/'source_catalog/MASTER_CATALOG.json'
TRANSFER=ROOT/'source_catalog/SOURCE_TRANSFER_LIBRARY.json'
TIDX=ROOT/'generator/data/templates/index.json'
TREG=ROOT/'generator/data/taste_policy_registry.json'
OUT=ROOT/'generator/data/templates/catalog'
POUT=ROOT/'generator/data/taste_policies/catalog'
REPORT=ROOT/'generator/data/templates/catalog_promotion_report.json'
VIEWS=('front','right','left','back')
META={
 'Hats':('Hat','HatSize','HeadPosition','HEAD'),
 'Shirts':('Shirt','ShirtSize','BodyPosition','SHIRT'),
 'Accessories':('Accessory','AccessorySize','BodyPosition','ACCESSORY'),
}

def slug(s):
    s=re.sub(r'[^a-z0-9]+','_',s.lower()).strip('_')
    return re.sub(r'_+','_',s)

def read_jsonc(path):
    text=Path(path).read_text(encoding='utf-8-sig')
    out=[]; ins=False; esc=False; i=0
    while i<len(text):
        ch=text[i]
        if ins:
            out.append(ch)
            if ch=='"' and not esc: ins=False
            esc=(ch=='\\' and not esc)
            if ch!='\\': esc=False
        elif ch=='"': ins=True; esc=False; out.append(ch)
        elif text.startswith('//',i):
            while i<len(text) and text[i]!='\n': i+=1
            continue
        else: out.append(ch)
        i+=1
    clean=''.join(out)
    clean=re.sub(r',\s*([}\]])',r'\1',clean)
    return json.loads(clean)

def pixel_hash(rows):
    b=bytearray()
    for row in rows:
        for p in row: b.extend(bytes(p))
    return hashlib.sha256(b).hexdigest()

def alpha_hash(rows):
    pts={(x,y) for y,row in enumerate(rows) for x,p in enumerate(row) if p[3]}
    return hashlib.sha256(';'.join(f'{x},{y}' for x,y in sorted(pts)).encode()).hexdigest()

def crop(sheet,rect,flip=False):
    x,y,w,h=rect
    rows=[r[x:x+w] for r in sheet[y:y+h]]
    return [list(reversed(r)) for r in rows] if flip else rows

def bbox(rows):
    pts=[(x,y) for y,row in enumerate(rows) for x,p in enumerate(row) if p[3]]
    if not pts: return (0,0,len(rows[0])-1,len(rows)-1)
    xs=[x for x,y in pts]; ys=[y for x,y in pts]
    return min(xs),min(ys),max(xs),max(ys)

def animation_frames(block):
    frames=set()
    for k,v in block.items():
        if 'Animation' not in k or not isinstance(v,list): continue
        for ent in v:
            if isinstance(ent,dict) and 'Frame' in ent: frames.add(int(ent['Frame']))
    return frames

def classify(entry,category):
    if category not in META:
        return None,'category_requires_specialized_adapter'
    suffix,sizekey,poskey,slot=META[category]
    try: data=read_jsonc(entry['json_path'])
    except Exception as e: return None,f'json_parse_failed:{type(e).__name__}'
    blocks={v:data.get(v.capitalize()+suffix) for v in VIEWS}
    if not all(blocks.values()):
        miss=[v for v,b in blocks.items() if not b]
        return None,'missing_cardinal:'+','.join(miss)
    sizes={}; frames=set()
    for view,b in blocks.items():
        sz=b.get(sizekey,{})
        wh=(int(sz.get('Width',0)),int(sz.get('Length',0)))
        sizes[view]=wh; frames|=animation_frames(b)
    if any(w<=0 or h<=0 or w>32 or h>32 for w,h in sizes.values()):
        return None,'unsupported_frame_size'
    unique=set(sizes.values())
    uniform=next(iter(unique)) if len(unique)==1 else None
    if frames and frames!={0}:
        return None,'animated_or_stateful'
    return {'data':data,'blocks':blocks,'size':uniform,'frameSizes':sizes,'slot':slot,'suffix':suffix,'sizekey':sizekey,'poskey':poskey},None

def zones_for(category):
    common={'surface':{'purpose':'palette/material/pattern inside locked opaque cells','geometry':'opaque source-template cells only'}}
    if category=='Hats':
        common.update({'crown':{'purpose':'upper hat treatment'},'band':{'purpose':'lower/cuff treatment'},'attachment_edge':{'purpose':'approved additive edge parts'}})
    elif category=='Shirts':
        common.update({'upper':{'purpose':'neck/chest treatment'},'lower':{'purpose':'hem/lower-body treatment'},'center':{'purpose':'front/back focal design zone'}})
    else:
        common.update({'upper':{'purpose':'upper accessory zone'},'lower':{'purpose':'lower accessory zone'},'side':{'purpose':'side-localized accessory zone'},'attachment_edge':{'purpose':'approved additive edge parts'}})
    return common

def allowed_parts(category):
    base=['STYLE_PROFILE','PALETTE_TONE','MATERIAL_PATTERN','MOTIF','REUSABLE_COMPONENT','BASE_SPECIFIC']
    if category in {'Hats','Accessories'}: base+=['ATTACHMENT','HARDWARE']
    else: base+=['HARDWARE']
    return base

def transfer_identity(pack,category,base):
    lib=json.loads(TRANSFER.read_text())
    for fam in lib['families']:
        ident=fam['identity']
        if ident.get('pack')==pack and ident.get('category')==category and ident.get('base')==base:
            return ident
    return {'pack':pack,'category':category,'family':base,'base':base}


def make_contract(entry,category,pack,parsed,family_id,template_id):
    data=parsed['data']; blocks=parsed['blocks']; uniform=parsed['size']; sizes=parsed['frameSizes']; poskey=parsed['poskey']
    sheet=read_rgba_png(entry['png_path'])
    sheet_rel=str(Path(entry['png_path']).resolve().relative_to(ROOT.resolve()))
    json_rel=str(Path(entry['json_path']).resolve().relative_to(ROOT.resolve()))
    frames={}; anchors={}; wear={}
    for view in VIEWS:
        b=blocks[view]; start=b.get('StartingPosition',{})
        w,h=sizes[view]
        rect=[int(start.get('X',0)),int(start.get('Y',0)),w,h]
        x,y,ww,hh=rect
        if x<0 or y<0 or x+ww>len(sheet[0]) or y+hh>len(sheet):
            raise ValueError(f'{template_id}/{view}: source rect outside sheet')
        flip=bool(b.get('Flipped'))
        rows=crop(sheet,rect,flip)
        x0,y0,x1,y1=bbox(rows)
        cx=(x0+x1)//2; cy=(y0+y1)//2
        frames[view]={'sheetPath':sheet_rel,'sourceRect':rect,'flipX':flip,'pixelSha256':pixel_hash(rows),'alphaSha256':alpha_hash(rows)}
        anchors[view]={
          'center':[cx,cy],'top_center':[cx,y0],'bottom_center':[cx,y1],
          'left_edge':[x0,cy],'right_edge':[x1,cy]
        }
        if category=='Hats':
            anchors[view]['crown_center']=[cx,y0+(max(0,y1-y0)*2)//5]
            anchors[view]['band_center']=[cx,y0+(max(0,y1-y0)*4)//5]
            anchors[view]['attachment_edge']=[x1,y0]
        pos=b.get(poskey,{'X':0,'Y':0})
        wear[view]={'position':{'X':int(pos.get('X',0)),'Y':int(pos.get('Y',0))},'flipped':flip}
        for key in ('DrawOrderOverride','DrawAfterSleeves','HideWhileSwimming','HideWhileWearingBathingSuit','DisableNativeOffset'):
            if key in b: wear[view][key]=b[key]
    source_sha=hashlib.sha256(Path(entry['png_path']).read_bytes()).hexdigest()
    identity=transfer_identity(pack,category,entry['name'])
    contract={
      'schema':'source-backed-template/v1','id':template_id,'slot':parsed['slot'],'category':category,'family':family_id,
      'sourceIdentity':identity,
      'sourceCatalog':{'kind':'CATALOG_FAMILY_BASE','name':entry['name'],'pack':pack,'author':entry.get('author'),'sourcePng':sheet_rel,'sourceJson':json_rel,'sourcePngSha256':source_sha,'transferLibrary':'source_catalog/SOURCE_TRANSFER_LIBRARY.json'},
      'requiredInputs':['catalog FAMILY_BASE source','four stable cardinal source blocks','locked extracted-frame hashes','semantic zones and anchors','registered family taste policy'],
      'frames':frames,
      'geometryLock':{
        'authority':'source-sheet rectangles above','requiredViews':['front','right','left','back'],
        'forbidResample':True,'forbidGenericNormalization':True,'forbidBaseAlphaRemoval':True,
        'allowedAlphaGrowth':'ATTACHMENT/HARDWARE only when family policy and target anchor permit it',
        'humanArtApprovalRequiredBeforeProduction':True,
      },
      'zones':zones_for(category),'anchors':anchors,'wearContract':{'sourceRuntime':'Fashion Sense','views':wear},
      'allowedPartKinds':allowed_parts(category),
      'safeTransferRules':[
        'source family base owns geometry and directional silhouette',
        'palette/material/pattern changes may not alter locked base alpha',
        'motifs map through semantic zones instead of source coordinates',
        'alternate constructions become separate templates rather than silent silhouette mutations',
        'production still requires human visual/wear approval'
      ],
      'incompatibilities':[
        {'scope':'ALTERNATE_CONSTRUCTION','deny':True,'reason':'different geometry requires its own template'},
        {'scope':'SAME_BASE_ONLY','deny':True,'reason':'base-specific deltas cannot cross construction templates'},
        {'feature':'generic_normalization','deny':True,'reason':'source construction geometry is authoritative'},
        {'feature':'resample_to_fit','deny':True,'reason':'resampling is not a construction transfer operation'},
        {'feature':'blind_source_coordinates','deny':True,'reason':'cross-template parts require semantic mapping'}
      ],
      'catalogProvenance':{'generatorRole':'FAMILY_BASE','pack':pack,'sourceName':entry['name'],'approval':'CANDIDATE_TEMPLATE'},
    }
    if uniform is not None:
        contract['frameSize']=list(uniform)
    else:
        contract['frameSizes']={v:list(sizes[v]) for v in VIEWS}
    return contract

def make_taste_policy(family_id,template_id,category):
    attachment_values=['none'] if category=='Shirts' else ['none','small','large']
    default={'materialTreatment':'plain','pattern':'solid','trim':'none','motif':'none','motifPlacement':'none','attachment':'none','hardware':'none'}
    rarity={
      'order':['common','uncommon','rare','epic'],
      'common':{
        'forced':{'motif':'none','motifPlacement':'none','attachment':'none','hardware':'none'},
        'allowedValues':{'materialTreatment':['plain','subtle'],'pattern':['solid','subtle'],'trim':['none','subtle']},
      },
      'uncommon':{
        'forced':{'motif':'none','motifPlacement':'none'},
        'allowedValues':{'materialTreatment':['plain','subtle','textured','statement'],'pattern':['solid','subtle','stripe','colorblock'],'trim':['none','subtle','contrast','wrap'],'attachment':attachment_values,'hardware':['none','small']},
        'distinctiveFeatureRule':{'requireAny':{'materialTreatment':['textured','statement'],'pattern':['stripe','colorblock'],'trim':['contrast','wrap'],'attachment':['small'],'hardware':['small']}},
      },
      'rare':{'allowedValues':{'attachment':attachment_values}},
      'epic':{'allowedValues':{'attachment':attachment_values}},
      'minimumRarityRules':[
        {'axis':'motif','nonNone':True,'minimum':'rare'},
        {'axis':'pattern','values':['dense'],'minimum':'rare'},
        {'axis':'attachment','values':['large'],'minimum':'rare'},
      ],
      'minimumRarityByFeature':{},
    }
    taste={
      'version':1,'principle':'Rarity increases distinctiveness, not clutter. One dominant visual idea with bounded support.',
      'complexityBudgets':{
        'common':{'min':0,'max':1,'maxVisualChannels':1,'maxSecondary':0,'maxAccents':1},
        'uncommon':{'min':1,'max':2,'maxVisualChannels':2,'maxSecondary':1,'maxAccents':1},
        'rare':{'min':2,'max':4,'maxVisualChannels':3,'maxSecondary':1,'maxAccents':2},
        'epic':{'min':3,'max':5,'maxVisualChannels':3,'maxSecondary':2,'maxAccents':2},
      },
      'channels':{'SURFACE':['materialTreatment'],'PATTERN':['pattern'],'REGION':['trim'],'GRAPHIC':['motif'],'ATTACHMENT':['attachment'],'HARDWARE':['hardware']},
      'featureCosts':{
        'materialTreatment':{'plain':0,'subtle':0,'textured':1,'statement':2},
        'pattern':{'solid':0,'subtle':0,'stripe':1,'colorblock':1,'dense':2},
        'trim':{'none':0,'subtle':1,'contrast':1,'wrap':2},
        'motif':{'none':0,'small':2,'emblem':2,'large':3},
        'attachment':{'none':0,'small':1,'large':2},
        'hardware':{'none':0,'small':1},
      },
      'impact':{'high':['materialTreatment.statement','pattern.dense','trim.wrap','motif.large','attachment.large'],'medium':['materialTreatment.textured','pattern.stripe','pattern.colorblock','trim.contrast','motif.small','motif.emblem','attachment.small'],'mediumPrefixes':[]},
      'dominantPriority':['GRAPHIC','PATTERN','SURFACE','REGION','ATTACHMENT','HARDWARE'],
      'strongConflictRules':[
        {'id':'dense_pattern_vs_large_motif','when':{'pattern':'dense'},'disallow':{'motif':['large']},'reason':'two dominant visual systems compete'},
        {'id':'statement_surface_vs_dense_pattern','when':{'materialTreatment':'statement'},'disallow':{'pattern':['dense']},'reason':'statement surface needs quieter pattern'},
        {'id':'large_attachment_vs_large_motif','when':{'attachment':'large'},'disallow':{'motif':['large']},'reason':'two large focal points compete'},
        {'id':'wrap_vs_dense_pattern','when':{'trim':'wrap'},'disallow':{'pattern':['dense']},'reason':'wrap and dense pattern compete for region hierarchy'},
      ],
      'semanticRequirements':[{'id':'motif_needs_placement','axis':'motif','whenNonNone':True,'requiresNonNone':['motifPlacement']}],
      'roleRules':{
        'BASE':'construction/template geometry and zero-impact treatments','PRIMARY':'single strongest visual identity','SECONDARY':'supporting medium/high-impact feature','ACCENT':'low-impact finishing detail','rule':'Exactly zero or one PRIMARY; reject competing focal points before visual generation.'
      },
    }
    return {'schema':'rng-family-taste-policy/v1','family':family_id,'template':template_id,'category':category,'rarityRules':rarity,'tastePolicy':taste,'defaultRecipe':default,'vocabulary':{
      'materialTreatment':['plain','subtle','textured','statement'],'pattern':['solid','subtle','stripe','colorblock','dense'],'trim':['none','subtle','contrast','wrap'],'motif':['none','small','emblem','large'],'motifPlacement':['none','front_center','front_offset','side','back_center'],'attachment':attachment_values,'hardware':['none','small']
    }}

def main():
    catalog=json.loads(CAT.read_text())
    tidx=json.loads(TIDX.read_text())
    treg=json.loads(TREG.read_text())
    OUT.mkdir(parents=True,exist_ok=True); POUT.mkdir(parents=True,exist_ok=True)
    # Remove prior generated catalog registrations only; preserve manual entries like slouch_pl24.
    tidx['templates']={k:v for k,v in tidx['templates'].items() if v.get('origin')!='catalog-promoter'}
    treg['families']={k:v for k,v in treg['families'].items() if v.get('origin')!='catalog-promoter'}
    promoted=[]; deferred=[]
    for category,packs in catalog['categories'].items():
      for pack,items in packs.items():
        for entry in items:
          if entry.get('generator_role')!='FAMILY_BASE': continue
          parsed,reason=classify(entry,category)
          rec={'category':category,'pack':pack,'name':entry['name'],'author':entry.get('author'),'png':entry.get('png_path'),'json':entry.get('json_path')}
          if reason:
            rec['reason']=reason; deferred.append(rec); continue
          family_id='catalog_'+slug(category)+'_'+slug(pack)+'_'+slug(entry['name'])
          template_id=family_id
          try:
            contract=make_contract(entry,category,pack,parsed,family_id,template_id)
          except Exception as e:
            rec['reason']='contract_build_failed:'+type(e).__name__+':'+str(e); deferred.append(rec); continue
          cpath=OUT/(template_id+'.json')
          cpath.write_text(json.dumps(contract,indent=2)+'\n')
          policy=make_taste_policy(family_id,template_id,category)
          ppath=POUT/(family_id+'.json')
          ppath.write_text(json.dumps(policy,indent=2)+'\n')
          tidx['templates'][template_id]={
            'contract':str(cpath.relative_to(ROOT)),'family':family_id,'slot':parsed['slot'],
            'status':'CANDIDATE_READY','constructionAuthority':'catalog FAMILY_BASE source rectangles',
            'humanArtApprovalRequired':True,'origin':'catalog-promoter','sourceCategory':category,'sourcePack':pack,'sourceName':entry['name'],
          }
          treg['families'][family_id]={
            'policyFile':str(ppath.relative_to(ROOT)),'status':'ACTIVE','origin':'catalog-promoter',
            'template':template_id,'category':category,
          }
          promoted.append({**rec,'family':family_id,'template':template_id,'frameSize':(list(parsed['size']) if parsed['size'] else None),'frameSizes':({v:list(sz) for v,sz in parsed['frameSizes'].items()} if not parsed['size'] else None),'slot':parsed['slot']})
    tidx['schema']='source-backed-template-registry/v2'
    tidx['catalogPromotion']={'tool':'tools/promote_catalog_families.py','promoted':len(promoted),'deferred':len(deferred),'humanApprovalRequiredBeforeProduction':True}
    TIDX.write_text(json.dumps(tidx,indent=2)+'\n')
    treg['unregisteredActiveTemplateFamilyAction']='REJECT'
    TREG.write_text(json.dumps(treg,indent=2)+'\n')
    report={'schema':'catalog-family-promotion/v1','sourceCatalog':str(CAT.relative_to(ROOT)),'familyBaseCount':len(promoted)+len(deferred),'promotedCount':len(promoted),'deferredCount':len(deferred),'promoted':promoted,'deferred':deferred}
    REPORT.write_text(json.dumps(report,indent=2)+'\n')
    print('PROMOTED',len(promoted),'DEFERRED',len(deferred))
    from collections import Counter
    print('PROMOTED_BY_CATEGORY',dict(Counter(x['category'] for x in promoted)))
    print('DEFERRED_REASONS',dict(Counter(x['reason'] for x in deferred)))
    for x in deferred: print('DEFER',x['category'],x['pack'],x['name'],'=>',x['reason'])

if __name__=='__main__': main()
