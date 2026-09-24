#!/usr/bin/env python3
import hashlib,itertools,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from generator.catalog_templates import list_families,load_family,compatible_donors,load_template_for_family
from generator.taste_policy import evaluate_recipe
from generator.hat_visual_rules import (contract_for,palette_roles,filter_style_profiles,recipe_visual_precheck,render_proportional_line,validate_line,validate_palette_frame)
from v5.pngio import read_rgba_png,write_rgba_png,blank_image,blit,nearest_scale,draw_text
from v5.source.template_transfer import template_frames,assert_geometry_preserved,compile_recipe
from v5.source.source_backed_renderer import apply_style_profile
BATCH=os.environ.get('RNG_HAT_BATCH','hat_production_batch_01')
OUT=ROOT/'experiments'/BATCH; CAND=OUT/'candidates'
CAT=json.loads((ROOT/'source_catalog/catalog.json').read_text())
RAR=('common','uncommon','rare','epic'); VIEWS=('front','right','left','back')

def idx(k,n): return int(hashlib.sha256(k.encode()).hexdigest()[:12],16)%n
def feature_kind(name):
    if not name:return None
    return {'motif':'MOTIF','attachment':'ATTACHMENT','hardware':'HARDWARE','pattern':'MATERIAL_PATTERN'}.get(name.split('.',1)[0])
def app(pack,name):
    return next(a for a in CAT['appearances'] if a.get('pack')==pack and a.get('name')==name)
def crop(sheet,b):
    x,y,w,h=map(int,b); return [r[x:x+w] for r in sheet[y:y+h]]
def view(a,v):
    boxes=(a.get('analysis') or {}).get('boxes') or {}; k=v.capitalize()
    if k not in boxes and v=='left': k='Right'
    if k not in boxes: return None
    return crop(read_rgba_png(Path(a['png_path'])),boxes[k])
def delta(p,v,additive=False):
    i=p['sourceBaseIdentity']; a=view(app(i['pack'],i['base']),v); b=view(app(p['pack'],p['name']),v)
    if a is None or b is None: return []
    h=max(len(a),len(b)); w=max(len(a[0]),len(b[0])); out=[]
    for y in range(h):
        for x in range(w):
            pa=a[y][x] if y<len(a) and x<len(a[0]) else (0,0,0,0)
            pb=b[y][x] if y<len(b) and x<len(b[0]) else (0,0,0,0)
            if (pb[3] and not pa[3]) if additive else (pb[3] and pb!=pa): out.append((x,y,pb))
    if additive and not out:
        return delta(p,v,False)
    return out
def recolor(p,vocab):
    if not vocab:return p
    lum=lambda c:(c[0]*299+c[1]*587+c[2]*114)/1000
    c=min(vocab,key=lambda c:abs(lum(c)-lum(p))); return (c[0],c[1],c[2],255)
def norm(cells,limit):
    if not cells:return []
    xs=[x for x,y,p in cells];ys=[y for x,y,p in cells]
    x0,x1=min(xs),max(xs);y0,y1=min(ys),max(ys)
    pts=[((x-x0)/max(1,x1-x0),(y-y0)/max(1,y1-y0),p) for x,y,p in cells]
    if len(pts)>limit:
        step=len(pts)/limit;pts=[pts[min(len(pts)-1,int(i*step))] for i in range(limit)]
    return pts
def bbox(fr):
    q=[(x,y) for y,r in enumerate(fr) for x,p in enumerate(r) if p[3]]
    if not q: return None
    return (min(x for x,y in q),min(y for x,y in q),max(x for x,y in q),max(y for x,y in q))
def surface(fr,cells,anchor,vocab,limit):
    out=[r[:] for r in fr];pts=norm(cells,limit)
    if not pts:return out,0
    box=bbox(fr)
    if box is None:return out,0
    x0,y0,x1,y1=box;cx,cy=anchor
    span=max(2,min(5,int(limit**.5)+1));n=0
    ox=max(x0,min(x1-span+1,cx-span//2));oy=max(y0,min(y1-span+1,cy-span//2))
    for nx,ny,p in pts:
        x=ox+round(nx*(span-1));y=oy+round(ny*(span-1))
        if 0<=y<len(fr) and 0<=x<len(fr[0]) and fr[y][x][3]:
            out[y][x]=recolor(p,vocab);n+=1
    assert_geometry_preserved(fr,out);return out,n
def attach(fr,cells,anchor,vocab,limit):
    out=[r[:] for r in fr];pts=norm(cells,limit);span=2 if limit<=4 else 3
    proposed={}
    for nx,ny,p in pts:
        x=anchor[0]+round((nx-.5)*span);y=anchor[1]+round((ny-.5)*span)
        if 0<=y<len(out) and 0<=x<len(out[0]) and not out[y][x][3]:
            proposed[(x,y)]=recolor(p,vocab)
    base={(x,y) for y,row in enumerate(fr) for x,p in enumerate(row) if p[3]}
    keep=set()
    frontier={q for q in proposed if any((q[0]+dx,q[1]+dy) in base for dx in (-1,0,1) for dy in (-1,0,1) if dx or dy)}
    while frontier:
        keep|=frontier
        frontier={q for q in proposed if q not in keep and any((q[0]+dx,q[1]+dy) in keep for dx in (-1,0,1) for dy in (-1,0,1) if dx or dy)}
    for q in keep: out[q[1]][q[0]]=proposed[q]
    assert_geometry_preserved(fr,out,allow_added=True);return out,len(keep)
def trim(fr,a,vocab,mode):
    if mode=='none' or len(vocab)<2:return fr
    out=[r[:] for r in fr]; vals=sorted(vocab,key=sum)
    c=vals[min(len(vals)-1,2 if mode=='subtle' else max(1,len(vals)//2))]
    for y in range(max(0,a[1]-1),min(len(fr),a[1]+1)):
        for x,p in enumerate(fr[y]):
            if p[3]:out[y][x]=(c[0],c[1],c[2],p[3])
    assert_geometry_preserved(fr,out);return out
def pool(fam,rar):
    pol=load_family(fam); visual=contract_for(fam); axes=list(pol['vocabulary']);rows=[]
    for vals in itertools.product(*(pol['vocabulary'][a] for a in axes)):
        rec=dict(zip(axes,vals));rep=evaluate_recipe(rec,rar,pol)
        if rep.valid and not recipe_visual_precheck(rec,visual):rows.append((rec,rep))
    if not rows: raise RuntimeError(f'{fam}: no visually legal {rar} recipe')
    m=max(x[1].complexity for x in rows);return [x for x in rows if x[1].complexity>=max(0,m-1)]
def parts(fam,rec,key):
    by={}
    for z in compatible_donors(fam)['allowed']:
        p=z['part'];by.setdefault(p.get('partKind'),[]).append(p)
    for a in by.values():a.sort(key=lambda p:(p.get('pack',''),p.get('name',''),p.get('id','')))
    target_family=load_template_for_family(fam).source_identity.get('family')
    filtered=filter_style_profiles(fam,by.get('STYLE_PROFILE',[]),target_family)
    if not filtered: raise RuntimeError(f'{fam}: no harmony-valid style profile')
    style, harmony=filtered[idx(key+'style',len(filtered))]; chosen=[]
    wants=[('pattern','MATERIAL_PATTERN','solid'),('motif','MOTIF','none'),('attachment','ATTACHMENT','none'),('hardware','HARDWARE','none')]
    for axis,k,off in wants:
        if rec.get(axis)!=off and by.get(k):
            arr=by[k]
            hat_arr=[p for p in arr if p.get('category')=='Hats']
            if hat_arr: arr=hat_arr
            chosen.append(arr[idx(key+k,len(arr))])
    return style,chosen,harmony
def render(fam,rar,n):
    pol=load_family(fam);tpl=load_template_for_family(fam);visual=contract_for(fam);choices=pool(fam,rar)
    base=template_frames(tpl);cap=pol['familyCapacity'];rejected=[]
    start=idx(fam+rar+'recipe',len(choices))
    for attempt in range(min(24,max(8,len(choices)*2))):
        rec,rep=choices[(start+attempt)%len(choices)]
        style,chosen,harmony=parts(fam,rec,fam+rar+f':{attempt}')
        compile_recipe(tpl,style,chosen)
        vocab=[tuple(c) for c in style.get('vocabulary',[])]
        roles=palette_roles(vocab)
        accent_kinds={feature_kind(x) for x in rep.accents if feature_kind(x)}
        frames={};logs={};attempt_errors=[]
        for v in VIEWS:
            fr=apply_style_profile(base[v],style)
            styled_reference=[row[:] for row in fr]
            fr,line_meta=render_proportional_line(fr,visual['linePlacement'],roles,rec.get('trim','none'))
            line_errors=validate_line(line_meta,visual['linePlacement'])
            line_cells=set(tuple(q) for q in line_meta.get('cells',[]))
            masks={};log=[]
            for part in chosen:
                k=part['partKind'];before=[row[:] for row in fr]
                if k in ('MOTIF','MATERIAL_PATTERN'):
                    limit=min(cap.get('maxMotifFootprintCells',8),4 if k=='MOTIF' else 8)
                    fr,c=surface(fr,delta(part,v),tpl.anchors[v].get('crown_center',tpl.anchors[v]['center']),vocab,limit)
                else:
                    limit={'tiny':2,'small':4,'medium':6,'large':8}[cap['surfaceAreaClass']]
                    fr,c=attach(fr,delta(part,v,True),tpl.anchors[v].get('attachment_edge',tpl.anchors[v]['right_edge']),vocab,limit)
                for x,y in line_cells: fr[y][x]=before[y][x]
                changed={(x,y) for y,row in enumerate(fr) for x,pix in enumerate(row) if pix!=before[y][x]}
                masks.setdefault(k,set()).update(changed)
                log.append({'kind':k,'name':part.get('name'),'cellsApplied':len(changed)})
            pal_errors,pal_metrics=validate_palette_frame(fr,roles,visual,masks,harmony,reference_frame=styled_reference,accent_kinds=accent_kinds)
            errors=line_errors+pal_errors
            if errors: attempt_errors.extend(f'{v}:{e}' for e in errors)
            frames[v]=fr;logs[v]={'line':line_meta,'parts':log,'palette':pal_metrics,'errors':errors}
        if attempt_errors:
            rejected.append({'attempt':attempt,'recipe':rec,'harmony':harmony,'errors':list(dict.fromkeys(attempt_errors))[:16]})
            continue
        out=CAND/f'{n:03d}_{rar}_{fam}';out.mkdir(parents=True,exist_ok=True)
        for v,fr in frames.items():write_rgba_png(out/f'{v}.png',fr)
        serial_roles={k:([list(x) for x in val] if k=='ramp' else list(val) if isinstance(val,tuple) else val) for k,val in roles.items()}
        return {'family':fam,'rarity':rar,'capacity':cap['surfaceAreaClass'],'recipe':rec,
          'taste':{'complexity':rep.complexity,'budget':[rep.budget_min,rep.budget_max],'channels':list(rep.active_channels),
                   'primary':rep.primary,'secondary':list(rep.secondary),'accents':list(rep.accents)},
          'styleDonor':{'id':style.get('id'),'pack':style.get('pack'),'family':style.get('family'),'harmonyTag':harmony},
          'paletteRoles':serial_roles,
          'parts':[{'kind':part['partKind'],'name':part.get('name'),'pack':part.get('pack')} for part in chosen],
          'frames':{v:str((out/f'{v}.png').relative_to(ROOT)) for v in VIEWS},'renderLog':logs,
          'rejectedAttempts':rejected,'visualContract':'generator/data/hat_visual_contracts.json',
          'template':tpl.id,'status':'CANDIDATE_REVIEW_REQUIRED'}
    reasons=sorted({e for row in rejected for e in row['errors']})
    raise RuntimeError(f'{fam}/{rar}: visual sanity rejected all attempts: {reasons[:12]}')
def label(f):return f.replace('catalog_hats_','').replace('more_accessories_and_stuff_','MAS ').replace('cottagecore_set_','CC ').replace('alt_fashion_set_','ALT ').replace('_',' ')
def sheet(grid,k):
    rows=grid[k*10:(k+1)*10];cw,ch=300,180;s=blank_image(cw*4,ch*10,(238,236,229,255))
    for y,row in enumerate(rows):
      for x,e in enumerate(row):
        fr=read_rgba_png(ROOT/e['frames']['front']);q=[(a,b) for b,r in enumerate(fr) for a,p in enumerate(r) if p[3]]
        if q:
          x0=min(a for a,b in q);x1=max(a for a,b in q);y0=min(b for a,b in q);y1=max(b for a,b in q);fr=[r[x0:x1+1] for r in fr[y0:y1+1]]
        sc=max(2,min(7,180//max(1,len(fr[0])),105//max(1,len(fr))));big=nearest_scale(fr,sc)
        blit(s,big,x*cw+(cw-len(big[0]))//2,y*ch+50+(105-len(big))//2)
        draw_text(s,f'{e["rarity"].upper()} {e["capacity"].upper()} C{e["taste"]["complexity"]}',x*cw+8,y*ch+7,scale=1)
        if x==0:draw_text(s,label(e['family'])[:43],x*cw+8,y*ch+20,scale=1)
        draw_text(s,','.join(e['taste']['channels'])[:42],x*cw+8,y*ch+33,scale=1)
        draw_text(s,('PARTS '+str(len(e['parts']))+' '+str(e['styleDonor']['family']))[:42],x*cw+8,y*ch+161,scale=1)
    p=OUT/f'{BATCH.upper()}_{k+1}.png';write_rgba_png(p,s);return p
def main():
    CAND.mkdir(parents=True,exist_ok=True)
    hats=sorted(e['family'] for e in list_families(include_manual=False) if load_family(e['family']).get('category')=='Hats')
    man={'schema':'hat-production-batch/v2','batch':BATCH,'families':len(hats),'humanArtApproved':False,'visualContractRegistry':'generator/data/hat_visual_contracts.json','proportionalLinePlacementEnabled':True,'paletteSanityEnabled':True,'candidates':[]};grid=[];n=0
    for fam in hats:
      row=[]
      for rar in RAR:
        n+=1;e=render(fam,rar,n);man['candidates'].append(e);row.append(e)
        print(f'{n:02d}/80 {rar:8} {e["capacity"]:6} {label(fam)} C{e["taste"]["complexity"]} parts={len(e["parts"])}')
      grid.append(row)
    man['candidateCount']=len(man['candidates'])
    man['rejectedAttemptCount']=sum(len(x.get('rejectedAttempts',[])) for x in man['candidates'])
    contacts=[sheet(grid,0),sheet(grid,1)]
    man['contactSheets']=[str(x.relative_to(ROOT)) for x in contacts]
    (OUT/'manifest.json').write_text(json.dumps(man,indent=2)+'\n')
    print('CONTACT',contacts[0]);print('CONTACT',contacts[1]);print('MANIFEST',OUT/'manifest.json')
if __name__=='__main__':main()
