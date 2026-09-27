#!/usr/bin/env python3
"""Side experiment: vanilla Stardew clothing as the ONLY source corpus.

Purpose: test the source-backed generator architecture without AI/PT/source-quality noise.
Vanilla art owns geometry and source construction. The experiment performs a small
source deconstruction (palette groups + shade ladders + boundary/interior masks),
then applies existing generator palette/treatment axes without touching alpha.

Nothing here mutates production registries or canonical templates.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import colorsys, hashlib, json, random, shutil

ROOT=Path(__file__).resolve().parents[1]
GAME=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer')
OUT=ROOT/'experiments/vanilla_source_only_random_batch_01'
SEED=260927; RNG=random.Random(SEED)
HATS=Image.open(GAME/'hats.png').convert('RGBA')
SHIRTS=Image.open(GAME/'shirts.png').convert('RGBA')
PALETTES=json.loads((ROOT/'authored/palettes.json').read_text())['palettes']
TREATMENTS=json.loads((ROOT/'authored/treatments.json').read_text())['treatments']
VIEWS=('front','right','left','back')
GROUP_RAMP={'body':'body','trim':'trim','accent':'accent'}


def luma(p): return 0.2126*p[0]+0.7152*p[1]+0.0722*p[2]
def sat(p):
    r,g,b=[x/255 for x in p[:3]]; return colorsys.rgb_to_hsv(r,g,b)[1]
def hue(p):
    r,g,b=[x/255 for x in p[:3]]; return colorsys.rgb_to_hsv(r,g,b)[0]
def rgba(h):
    h=h.lstrip('#'); return tuple(int(h[i:i+2],16) for i in (0,2,4))+(255,)
def occupied(im): return sum(1 for p in im.getdata() if p[3])
def alpha_hash(im):
    pts=[f'{x},{y}' for y in range(im.height) for x in range(im.width) if im.getpixel((x,y))[3]]
    return hashlib.sha256(';'.join(pts).encode()).hexdigest()
def pixel_hash(im): return hashlib.sha256(im.tobytes()).hexdigest()

def extract_hat(idx):
    c,r=idx%12,idx//12; block=HATS.crop((c*20,r*80,c*20+20,r*80+80))
    return {v:block.crop((0,i*20,20,(i+1)*20)) for i,v in enumerate(VIEWS)}
def extract_shirt(idx):
    c,r=idx%32,idx//32; block=SHIRTS.crop((c*8,r*32,c*8+8,r*32+32))
    return {v:block.crop((0,i*8,8,(i+1)*8)) for i,v in enumerate(VIEWS)}

def boundary(im):
    a={(x,y) for y in range(im.height) for x in range(im.width) if im.getpixel((x,y))[3]}
    return {p for p in a if any((p[0]+dx,p[1]+dy) not in a for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))}

def rgb_dist(a,b): return sum((a[i]-b[i])**2 for i in range(3))**0.5

def kmeans_colors(frames,k=3,iters=12):
    # Use distinct RGB values weighted by frequency across all four views.
    counts={}
    for im in frames.values():
        for p in im.getdata():
            if p[3]: counts[p[:3]]=counts.get(p[:3],0)+1
    cols=list(counts)
    if not cols: return [],{}
    # farthest-first deterministic seeds, starting from most common non-near-black color
    common=sorted(cols,key=lambda c:(-counts[c],-luma(c)))
    first=next((c for c in common if luma(c)>35),common[0]); centers=[first]
    while len(centers)<min(k,len(cols)):
        centers.append(max(cols,key=lambda c:min(rgb_dist(c,z) for z in centers)))
    for _ in range(iters):
        bins=[[] for _ in centers]
        for c in cols:
            j=min(range(len(centers)),key=lambda i:rgb_dist(c,centers[i])); bins[j].append(c)
        new=[]
        for old,b in zip(centers,bins):
            if not b: new.append(old); continue
            total=sum(counts[c] for c in b)
            new.append(tuple(round(sum(c[ch]*counts[c] for c in b)/total) for ch in range(3)))
        if new==centers: break
        centers=new
    assign={c:min(range(len(centers)),key=lambda i:rgb_dist(c,centers[i])) for c in cols}
    return centers,assign

def source_deconstruct(frames):
    centers,assign=kmeans_colors(frames,3)
    if not centers: return {},{}
    # Cluster roles: largest coverage = body; remaining by saturation => accent then trim.
    cover=[0]*len(centers)
    for im in frames.values():
        for p in im.getdata():
            if p[3]: cover[assign[p[:3]]]+=1
    body=max(range(len(centers)),key=lambda i:cover[i])
    rest=[i for i in range(len(centers)) if i!=body]
    accent=max(rest,key=lambda i:sat(centers[i])) if rest else body
    trim=next((i for i in rest if i!=accent),body)
    role_of={body:'body',trim:'trim',accent:'accent'}
    # Rank luma WITHIN each group, preserving each source group's own shade topology.
    lum_by_group={i:[] for i in range(len(centers))}
    for im in frames.values():
        for p in im.getdata():
            if p[3]: lum_by_group[assign[p[:3]]].append(luma(p))
    cuts={}
    for g,vals in lum_by_group.items():
        vals=sorted(vals)
        cuts[g]=[vals[min(len(vals)-1,round((len(vals)-1)*q/5))] for q in range(6)] if vals else [0]*6
    per_view={}
    for v,im in frames.items():
        b=boundary(im); cells={}
        for y in range(im.height):
            for x in range(im.width):
                p=im.getpixel((x,y))
                if not p[3]: continue
                g=assign[p[:3]]; lv=luma(p); step=min(range(6),key=lambda q:abs(cuts[g][q]-lv))
                cells[(x,y)]={'group':role_of[g],'step':step,'boundary':(x,y) in b,'source':list(p[:3])}
        per_view[v]=cells
    meta={'centers':[list(x) for x in centers],'coverage':cover,'clusterRoles':{str(i):role_of[i] for i in role_of}}
    return per_view,meta

def apply_treatment(step,x,y,name):
    t=TREATMENTS[name]; rule=t['rule']; p=t.get('params',{}); lo=int(p.get('min_step',0)); d=int(p.get('delta',1))
    if step<lo or rule=='plain': return step
    if rule=='speckle':
        # same style as authored Treatment._hash, deterministic
        h=((x*73856093)^(y*19349663)^0x9E3779B9)&0xffffffff; h=((h^(h>>13))*1274126177)&0xffffffff; frac=((h^(h>>16))&0xffff)/0xffff
        return min(5,step+d) if frac<float(p.get('density',.15)) else step
    if rule=='rib' and x%int(p.get('period',2))==0: return max(lo,step-d)
    if rule=='check':
        n=(1 if x%int(p.get('period',4))==0 else 0)+(1 if y%int(p.get('row_period',3))==0 else 0)
        return min(5,step+d*n) if n else step
    if rule=='panel':
        # source-independent restrained seam; this experiment applies only to interior body pixels
        return max(lo,step-d) if ((x+y)%7==0) else step
    return step

def render_variant(frames,decon,palette,treatment):
    ramps={k:[rgba(x) for x in palette['ramps'][GROUP_RAMP[k]]] for k in GROUP_RAMP}
    out={}
    for v,im in frames.items():
        dst=Image.new('RGBA',im.size,(0,0,0,0))
        for (x,y),c in decon[v].items():
            step=c['step']
            # material treatment only on interior BODY cells. This avoids turning trims/accents into noise.
            if c['group']=='body' and not c['boundary']:
                step=apply_treatment(step,x,y,treatment)
            dst.putpixel((x,y),ramps[c['group']][step])
        assert alpha_hash(dst)==alpha_hash(im)
        out[v]=dst
    return out

def stack(frames):
    w=next(iter(frames.values())).width; h=next(iter(frames.values())).height
    out=Image.new('RGBA',(w,h*4),(0,0,0,0))
    for i,v in enumerate(VIEWS): out.alpha_composite(frames[v],(0,i*h))
    return out

def usable(kind):
    src=HATS if kind=='hat' else SHIRTS; iw,ih=(20,80) if kind=='hat' else (8,32); cols=src.width//iw
    rows=[]
    for idx in range((src.width//iw)*(src.height//ih)):
        c,r=idx%cols,idx//cols; block=src.crop((c*iw,r*ih,c*iw+iw,r*ih+ih)); fh=ih//4
        if all(occupied(block.crop((0,i*fh,iw,(i+1)*fh)))>0 for i in range(4)): rows.append(idx)
    return rows

if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)
hat_pool=usable('hat'); shirt_pool=usable('shirt')
hat_ids=RNG.sample(hat_pool,6); shirt_ids=RNG.sample(shirt_pool,6)
records=[]
for kind,ids,extract in [('hat',hat_ids,extract_hat),('shirt',shirt_ids,extract_shirt)]:
    for idx in ids:
        frames=extract(idx); decon,meta=source_deconstruct(frames)
        pal=RNG.choice(PALETTES); treatment=RNG.choice(list(TREATMENTS))
        var=render_variant(frames,decon,pal,treatment)
        d=OUT/f'{kind}_{idx:03d}'; d.mkdir()
        for v in VIEWS:
            frames[v].save(d/f'source_{v}.png'); var[v].save(d/f'generated_{v}.png')
        stack(frames).save(d/'source_4view.png'); stack(var).save(d/'generated_4view.png')
        serial={v:{f'{x},{y}':c for (x,y),c in sorted(decon[v].items())} for v in VIEWS}
        (d/'deconstruction.json').write_text(json.dumps({'paletteGroups':meta,'views':serial},indent=2)+'\n')
        records.append({'kind':kind,'sourceIndex':idx,'palette':pal['id'],'treatment':treatment,'paletteGroups':meta,
            'geometryPreserved':all(alpha_hash(frames[v])==alpha_hash(var[v]) for v in VIEWS),
            'sourceHashes':{v:{'pixels':pixel_hash(frames[v]),'alpha':alpha_hash(frames[v]),'opaque':occupied(frames[v])} for v in VIEWS}})

# Clean contact, one source row and one generated row per item; hats and shirts get different scale.
W=1180; itemh=205; H=60+itemh*len(records)
contact=Image.new('RGBA',(W,H),(239,237,231,255)); dr=ImageDraw.Draw(contact)
dr.text((14,10),'VANILLA-ONLY SOURCE-BACKED RANDOM BATCH',fill=(20,20,20,255))
dr.text((14,30),'Exact vanilla geometry -> palette-group deconstruction -> generator palette/material variation',fill=(55,55,55,255))
for ri,rec in enumerate(records):
    y=60+ri*itemh; d=OUT/f"{rec['kind']}_{rec['sourceIndex']:03d}"; sc=6 if rec['kind']=='hat' else 10
    dr.text((14,y),f"{rec['kind'].upper()} #{rec['sourceIndex']}  |  {rec['palette']}  |  {rec['treatment']}",fill=(30,30,30,255))
    for row,name in enumerate(('source','generated')):
        dr.text((14,y+24+row*82),name.upper(),fill=(80,80,80,255)); x=105
        for v in VIEWS:
            im=Image.open(d/f'{name}_{v}.png').convert('RGBA'); big=im.resize((im.width*sc,im.height*sc),Image.Resampling.NEAREST)
            contact.alpha_composite(big,(x,y+20+row*82)); dr.text((x,y+20+row*82+big.height+1),v.upper(),fill=(90,90,90,255)); x+=big.width+25
contact.save(OUT/'VANILLA_ONLY_RANDOM_BATCH_CONTACT.png')
manifest={'schema':'vanilla-source-only-side-experiment/v2','seed':SEED,'sourceAuthority':'unpacked vanilla Stardew assets only',
 'inputs':{'hats':str(GAME/'hats.png'),'shirts':str(GAME/'shirts.png')},
 'prep':['exact four-view extraction','3-group source-relative palette deconstruction','per-group shade ladder','outer boundary/interior mask'],
 'generatorOps':['existing authored palette ramps','existing material treatment rules on interior body pixels only'],
 'prohibited':['Photo Tailor in baseline','AI geometry','resampling','alpha edits','production registry mutation','unmapped motif/attachment placement'],
 'pools':{'hat':len(hat_pool),'shirt':len(shirt_pool)},'records':records}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
assert all(r['geometryPreserved'] for r in records)
print('PASS vanilla-only source-backed baseline v2')
print('selected hats',hat_ids); print('selected shirts',shirt_ids)
print(OUT/'VANILLA_ONLY_RANDOM_BATCH_CONTACT.png')
