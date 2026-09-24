"""Hard visual grammar for promoted hat generation.

This module is deliberately dependency-free. It turns the approved hat-family
contracts into proportional line placement and palette sanity gates. Human art
review remains authoritative; these checks prevent known repeat failures.
"""
from __future__ import annotations
import colorsys,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/'generator/data/hat_visual_contracts.json'

def load_contracts():
    return json.loads(REGISTRY.read_text())

def contract_for(family):
    reg=load_contracts()
    try: return reg['families'][family]
    except KeyError: raise KeyError(f'no hat visual contract for {family}')

def value(rgb):
    return 0.299*rgb[0]+0.587*rgb[1]+0.114*rgb[2]

def hsv(rgb):
    h,s,v=colorsys.rgb_to_hsv(rgb[0]/255,rgb[1]/255,rgb[2]/255)
    return h*360,s,v*255

def palette_roles(vocab):
    cols=[]
    for c in vocab or []:
        t=tuple(c[:3])
        if t not in cols: cols.append(t)
    if not cols: return {'ramp':[]}
    ramp=sorted(cols,key=value)
    outline=ramp[0]
    shadow=ramp[min(1,len(ramp)-1)]
    light=ramp[-1]
    middle=ramp[1:-1] or ramp
    midtone=middle[len(middle)//2]
    accent=max(ramp,key=lambda c:(hsv(c)[1],abs(value(c)-value(midtone))))
    return {'outline':outline,'shadow':shadow,'midtone':midtone,
            'light':light,'accent':accent,'ramp':ramp}

def harmony_tag(vocab):
    cols=[tuple(c[:3]) for c in vocab or []]
    if not cols: return 'soft_neutral'
    hs=[hsv(c) for c in cols]
    sats=[x[1] for x in hs]; vals=[x[2] for x in hs]
    chrom=[x for x in hs if x[1]>=0.10]
    avg_sat=sum(sats)/len(sats); span=max(vals)-min(vals)
    if avg_sat<0.11:
        return 'alt_monochrome' if span>=115 else 'soft_neutral'
    if max(sats)>=0.72 and sum(sats)/len(sats)>=0.35:
        return 'bright_playful'
    if sum(vals)/len(vals)>=175 and avg_sat<=0.42:
        return 'cottage_pastel'
    if chrom:
        # circular mean simplified into the dominant chromatic step by saturation
        h=max(chrom,key=lambda x:x[1])[0]
        if 15<=h<=95: return 'earthy_warm'
        if 150<=h<=300: return 'muted_cool'
    return 'soft_neutral'

def filter_style_profiles(family, profiles, target_source_family=None):
    spec=contract_for(family)['paletteSanity']
    allowed=set(spec['allowedHarmonyTags'])
    preferred=list(spec['preferredHarmonyTags'])
    good=[]
    for p in profiles:
        vocab=p.get('vocabulary') or []
        if len(vocab)<2: continue
        tag=harmony_tag(vocab)
        if tag not in allowed: continue
        exact=int(bool(target_source_family and p.get('family')==target_source_family))
        pref=(preferred.index(tag) if tag in preferred else len(preferred)+1)
        good.append((-exact,pref,p.get('pack',''),p.get('family',''),p.get('id',''),p,tag))
    good.sort(key=lambda x:x[:5])
    exact=[x for x in good if x[0]==-1]
    if exact:
        chosen=exact
    else:
        preferred_rows=[x for x in good if x[6] in preferred]
        chosen=preferred_rows or good
    # Numeric palette-role sanity is part of donor admission, not only a
    # post-render rejection. This avoids retrying known collapsed ramps.
    admitted=[]
    for x in chosen:
        roles=palette_roles(x[5].get('vocabulary') or [])
        if not roles.get('ramp'): continue
        od=abs(value(roles['midtone'])-value(roles['outline']))
        ld=abs(value(roles['light'])-value(roles['midtone']))
        if od<spec['minOutlineMidtoneValueDelta'] or ld<spec['minMidtoneLightValueDelta']:
            continue
        admitted.append(x)
    chosen=admitted or chosen
    return [(x[5],x[6]) for x in chosen]

def recipe_visual_precheck(recipe, visual_contract):
    line=visual_contract['linePlacement']; pal=visual_contract['paletteSanity']
    errors=[]
    if recipe.get('trim','none')!='none' and not line['lineAllowed']:
        errors.append('line:family_disallows_line')
    if recipe.get('trim')=='wrap' and line['lineCountMax']<1:
        errors.append('line:count')
    accent_systems=sum(recipe.get(k,'none')!='none' for k in ('motif','attachment','hardware'))
    if accent_systems>pal.get('maxAccentSystems',2):
        errors.append('palette:too_many_accent_systems')
    return errors

def opaque_bbox(frame):
    pts=[(x,y) for y,row in enumerate(frame) for x,p in enumerate(row) if p[3]]
    if not pts:return None
    return min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)

def _line_color(roles, max_step, mode):
    ramp=roles.get('ramp') or []
    if not ramp:return (128,128,128,255),0
    mid=roles['midtone']; mi=ramp.index(mid)
    direction=-1 if mode in ('contrast','wrap') else 1
    ni=max(0,min(len(ramp)-1,mi+direction*max(1,min(max_step,1))))
    c=ramp[ni]
    return (c[0],c[1],c[2],255),abs(ni-mi)

def render_proportional_line(frame, line_spec, roles, mode, occupied_rows=()):
    out=[row[:] for row in frame]
    if mode=='none':
        return out,{'applied':False,'reason':'none','cells':[]}
    if not line_spec['lineAllowed']:
        return out,{'applied':False,'reason':'family_disallows_line','cells':[]}
    box=opaque_bbox(frame)
    if box is None:
        return out,{'applied':False,'reason':'empty','cells':[]}
    x0,y0,x1,y1=box; h=y1-y0+1; w=x1-x0+1
    ratio=float(line_spec['lineCenterYRatio'])
    y=y0+round((h-1)*ratio)
    forbidden={y1-int(n) for n in line_spec.get('lineForbiddenRowsRelativeToBottom',[])}
    if y in forbidden or y in set(occupied_rows):
        return out,{'applied':False,'reason':'forbidden_or_stacked_row','cells':[],'row':y}
    opaque_x=[x for x in range(x0,x1+1) if frame[y][x][3]]
    if not opaque_x:
        return out,{'applied':False,'reason':'empty_target_row','cells':[],'row':y}
    lo,hi=line_spec['lineWidthRatioRange']
    width_ratio={'subtle':lo,'contrast':(lo+hi)/2,'wrap':hi}.get(mode,(lo+hi)/2)
    row_left,row_right=min(opaque_x),max(opaque_x)
    if not line_spec['lineMayTouchOutline']:
        row_left+=1; row_right-=1
    usable=max(0,row_right-row_left+1)
    target=max(1,round(usable*width_ratio)) if usable else 0
    left=row_left+max(0,(usable-target)//2)
    right=min(row_right,left+target-1)
    color,step=_line_color(roles,int(line_spec['lineContrastMaxStep']),mode)
    cells=[]
    if right>=left:
        for x in range(left,right+1):
            if frame[y][x][3]:
                out[y][x]=color;cells.append((x,y))
    meta={'applied':bool(cells),'reason':'ok' if cells else 'no_safe_cells','cells':cells,
          'row':y,'bbox':[x0,y0,x1,y1],'centerYRatio':((y-y0)/max(1,h-1)),
          'thicknessPx':1 if cells else 0,'widthPx':len(cells),'widthBasisPx':usable,
          'widthRatio':len(cells)/max(1,usable),'contrastStep':step,
          'semanticType':line_spec['lineSemanticType'],'zone':line_spec['lineZone']}
    return out,meta

def validate_line(meta, line_spec):
    if not meta.get('applied'):
        return [] if meta.get('reason') in ('none',) else [f"line:{meta.get('reason')}"]
    errors=[]
    if meta['thicknessPx']>line_spec['lineThicknessPxMax']:errors.append('line:too_thick')
    lo,hi=line_spec['lineWidthRatioRange']
    if meta['widthRatio']<lo-0.08 or meta['widthRatio']>hi+0.08:errors.append('line:too_wide_or_narrow')
    if abs(meta['centerYRatio']-line_spec['lineCenterYRatio'])>line_spec['lineCenterToleranceRatio']:
        errors.append('line:too_low_or_high')
    if meta['contrastStep']>line_spec['lineContrastMaxStep']:errors.append('line:contrast_step')
    x0,y0,x1,y1=meta['bbox']
    forbidden={y1-int(n) for n in line_spec.get('lineForbiddenRowsRelativeToBottom',[])}
    if meta['row'] in forbidden:errors.append('line:forbidden_bottom_row')
    if not line_spec['lineMayTouchOutline'] and any(x in (x0,x1) for x,y in meta['cells']):
        errors.append('line:outline_merge')
    xs=sorted(x for x,y in meta.get('cells',[]) if y==meta.get('row'))
    longest=0; run=0; prev=None
    for x in xs:
        if prev is not None and x==prev+1:
            run+=1
        else:
            run=1
        longest=max(longest,run); prev=x
    min_run=max(int(line_spec.get('lineMinContiguousPixels',1)),
                round(meta.get('widthBasisPx',max(1,x1-x0+1))*float(line_spec.get('lineMinContiguousWidthRatio',0))))
    if line_spec.get('rejectIsolatedCenterFragment',False) and longest<min_run:
        errors.append('line:isolated_center_fragment')
    if line_spec.get('lineRequiresSideSupport',False) and xs:
        if min(xs)>x0+2 and max(xs)<x1-2 and longest<max(4,min_run):
            errors.append('line:missing_side_support')
    h=y1-y0+1
    brim_start=y0+round((h-1)*float(line_spec.get('brimZoneStartRatio',0.72)))
    if not line_spec.get('lineMayOverlapBrimBand',False) and meta['row']>=brim_start:
        errors.append('line:brim_overlap')
    return errors

def _components(cells):
    left=set(cells); n=0
    while left:
        n+=1; stack=[left.pop()]
        while stack:
            x,y=stack.pop()
            near={(x+dx,y+dy) for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))}
            hit=near & left
            left-=hit;stack.extend(hit)
    return n

def _color_shares(frame):
    counts={}; total=0
    for row in frame:
        for p in row:
            if not p[3]:continue
            c=tuple(p[:3]);counts[c]=counts.get(c,0)+1;total+=1
    return {c:n/max(1,total) for c,n in counts.items()}

def _muddy_warm_stack(frame, spec):
    cats=set()
    threshold=spec['muddyWarmMajorColorMinShare']
    for c,share in _color_shares(frame).items():
        if share<threshold:continue
        h,s,v=hsv(c)
        if 15<=h<=48 and s>=0.18 and v<190:cats.add('brown')
        elif 42<=h<=82 and s>=0.28:cats.add('yellow')
        elif 25<=h<=78 and 0.07<=s<=0.34 and v>=185:cats.add('cream')
    return len(cats),sorted(cats)

def _strong_horizontal_bands(frame, threshold):
    box=opaque_bbox(frame)
    if box is None:return []
    x0,y0,x1,y1=box
    rows=[]
    for y in range(y0,y1+1):
        vals=[value(p[:3]) for p in frame[y][x0:x1+1] if p[3]]
        rows.append((y,sum(vals)/len(vals) if vals else None,len(vals)/(x1-x0+1)))
    hits=[]
    for (y0a,a,fa),(y1a,b,fb) in zip(rows,rows[1:]):
        if a is None or b is None or fa<0.55 or fb<0.55:continue
        if abs(a-b)>=threshold:hits.append((y1a,round(abs(a-b),1)))
    return hits


def _zone_metrics(frame, spec, accent):
    box=opaque_bbox(frame)
    if box is None:return {}
    x0,y0,x1,y1=box; h=y1-y0+1
    crown_end=y0+round((h-1)*spec.get('crownZoneEndRatio',0.70))
    brim_start=y0+round((h-1)*spec.get('brimZoneStartRatio',0.72))
    def collect(a,b):
        pts=[]
        for y in range(max(y0,a),min(y1,b)+1):
            for x in range(x0,x1+1):
                p=frame[y][x]
                if p[3]:pts.append((x,y,p))
        return pts
    crown=collect(y0,crown_end); brim=collect(brim_start,y1)
    def stats(pts):
        if not pts:return {'value':0,'sat':0,'count':0}
        return {'value':sum(value(p[:3]) for x,y,p in pts)/len(pts),
                'sat':sum(hsv(p[:3])[1] for x,y,p in pts)/len(pts),
                'count':len(pts)}
    cm,bm=stats(crown),stats(brim)
    crown_cells={(x,y) for x,y,p in crown}
    cm['accentFraction']=len(crown_cells & accent)/max(1,len(crown_cells))
    return {'crown':cm,'brim':bm}

def _max_accent_neighbor_delta(frame, accent):
    worst=0.0
    for x,y in accent:
        if not (0<=y<len(frame) and 0<=x<len(frame[0])):continue
        p=frame[y][x]
        if not p[3]:continue
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx,ny=x+dx,y+dy
            if 0<=ny<len(frame) and 0<=nx<len(frame[0]) and (nx,ny) not in accent and frame[ny][nx][3]:
                worst=max(worst,abs(value(p[:3])-value(frame[ny][nx][:3])))
    return worst

def validate_palette_frame(frame, roles, visual_contract, masks=None, harmony=None, reference_frame=None, accent_kinds=None):
    spec=visual_contract['paletteSanity']; masks=masks or {}
    errors=[]; metrics={}
    harmony=harmony or harmony_tag(roles.get('ramp',[]))
    metrics['harmonyTag']=harmony
    if harmony not in spec['allowedHarmonyTags']:errors.append('palette:harmony_disallowed')
    if roles.get('ramp'):
        od=abs(value(roles['midtone'])-value(roles['outline']))
        ld=abs(value(roles['light'])-value(roles['midtone']))
        metrics['outlineMidtoneDelta']=round(od,1);metrics['midtoneLightDelta']=round(ld,1)
        if od<spec['minOutlineMidtoneValueDelta']:errors.append('palette:outline_midtone_collapse')
        if ld<spec['minMidtoneLightValueDelta']:errors.append('palette:midtone_light_collapse')
    accent=set()
    kinds=tuple(accent_kinds) if accent_kinds is not None else ('MOTIF','ATTACHMENT','HARDWARE')
    for k in kinds:
        accent.update(masks.get(k,set()))
    opaque=sum(1 for row in frame for p in row if p[3])
    frac=len(accent)/max(1,opaque);metrics['accentFraction']=round(frac,4)
    max_accent=max(int(spec.get('accentPixelBudgetMinPixels',0)),int(opaque*spec['accentPixelBudgetMax']+0.9999))
    metrics['accentPixelBudget']=max_accent
    if len(accent)>max_accent:errors.append('palette:accent_budget')
    islands=_components(accent) if accent else 0;metrics['accentIslands']=islands
    if islands>spec['maxDisconnectedAccentIslands']:errors.append('palette:accent_islands')
    neighbor_delta=_max_accent_neighbor_delta(frame,accent);metrics['maxAccentNeighborDelta']=round(neighbor_delta,1)
    if neighbor_delta>spec['maxAccentToNeighborValueDelta']:errors.append('palette:accent_neighbor_contrast')
    zones=_zone_metrics(frame,spec,accent);metrics['zones']=zones
    if zones:
        if spec.get('crownDominanceRequired') and zones['crown']['accentFraction']>spec.get('maxCrownAccentFraction',0.34):
            errors.append('palette:crown_accent_dominance')
        if spec.get('hasBrimZone',False) and not spec.get('brimMayBeHighestSaturation',False):
            c,b=zones['crown'],zones['brim']
            if b['count'] and c['count'] and b['sat']>c['sat']+0.10 and b['value']<c['value']-25:
                errors.append('palette:brim_dominates')
    if spec.get('rejectMuddyWarmMajorStack'):
        n,cats=_muddy_warm_stack(frame,spec);metrics['warmMajorRoles']=cats
        if n>spec['muddyWarmMajorColorMaxCount']:errors.append('palette:muddy_warm_stack')
    bands=_strong_horizontal_bands(frame,spec['strongBandValueDelta'])
    ref_bands=_strong_horizontal_bands(reference_frame,spec['strongBandValueDelta']) if reference_frame is not None else []
    metrics['strongBands']=bands;metrics['referenceStrongBands']=ref_bands
    added=max(0,len(bands)-len(ref_bands));metrics['addedStrongBands']=added
    if added>spec['maxStrongHorizontalBands']:errors.append('palette:harsh_split_bands')
    return list(dict.fromkeys(errors)),metrics
