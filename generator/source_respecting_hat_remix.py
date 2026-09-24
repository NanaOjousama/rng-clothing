"""Source-respecting hat remix pilot.

Principle:
    Preserve the source hat's core construction. Remix the non-core parts.

The pilot deliberately rejects the old generic donor projection path. It only:
- starts from exact source frames;
- applies exact same-construction source patches that reconstruct an authored
  source variant pixel-for-pixel;
- switches to whole authored alternate construction states;
- recolours only through explicit source RGB -> semantic role maps stored at
  ingest/extraction time;
- mutates the Straw Hat's built-in ribbon by recolouring its exact source mask,
  never by synthesising a new line.

Human review remains authoritative.
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path

from v5.pngio import read_rgba_png

ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/'source_catalog/catalog.json'
PARTS=ROOT/'generator/data/source_parts/hat_source_parts.json'
VIEWS=('front','right','left','back')

def read_jsonc(path):
    import re
    text=Path(path).read_text(encoding='utf-8-sig')
    out=[]; ins=False; esc=False; i=0
    while i<len(text):
        ch=text[i]
        if ins:
            out.append(ch)
            if ch=='"' and not esc: ins=False
            esc=(ch=='\\' and not esc)
            if ch!='\\': esc=False
        elif ch=='"':
            ins=True; esc=False; out.append(ch)
        elif text.startswith('//',i):
            while i<len(text) and text[i]!='\n': i+=1
            continue
        else:
            out.append(ch)
        i+=1
    return json.loads(re.sub(r',\s*([}\]])',r'\1',''.join(out)))

GRAY_TINTS={
    'source_native':None,
    'stone_blue':(150,184,210),
    'rose_cream':(238,184,195),
    'cocoa_gold':(201,153,92),
}
RIBBON_TINTS={
    'source_native':None,
    'cream':(245,224,173),
    'dusty_rose':(210,145,157),
    'sage':(150,177,133),
}

@dataclass(frozen=True)
class RemixResult:
    family:str
    construction:str
    source_state:str
    palette:str
    component:str|None
    frames:dict
    source_frames:dict
    changed:dict
    trace:dict

def _catalog():
    return json.loads(CATALOG.read_text())

def _parts():
    return json.loads(PARTS.read_text())

def _appearance(pack,name):
    return next(a for a in _catalog()['appearances']
                if a.get('pack')==pack and a.get('name')==name)

def source_frames(pack,name):
    a=_appearance(pack,name)
    sheet=read_rgba_png(a['png_path'])
    out={}
    doc=read_jsonc(a['json_path'])
    if isinstance(doc,list):
        doc=next((x for x in doc if x.get('Name')==a.get('name')),doc[0])
    for label,box in a['analysis']['boxes'].items():
        x,y,w,h=map(int,box)
        key=label.lower()
        rows=[row[x:x+w] for row in sheet[y:y+h]]
        block=doc.get(f'{label}Hat') if isinstance(doc,dict) else None
        if isinstance(block,dict) and block.get('Flipped'):
            rows=[list(reversed(row)) for row in rows]
        out[key]=rows
    if 'left' not in out and 'right' in out:
        out['left']=[list(reversed(row)) for row in out['right']]
    return out,a

def _copy(frames):
    return {v:[[p for p in row] for row in frames[v]] for v in frames}

def _tint(px,tint):
    if tint is None or not px[3]: return px
    return (round(px[0]*tint[0]/255),round(px[1]*tint[1]/255),
            round(px[2]*tint[2]/255),px[3])

def _role_tint(px,tint):
    if tint is None or not px[3]: return px
    y=round(0.299*px[0]+0.587*px[1]+0.114*px[2])
    return (round(tint[0]*y/255),round(tint[1]*y/255),round(tint[2]*y/255),px[3])

def _apply_role_prefix_tint(frames,roles,prefix,tint):
    out=_copy(frames);changed={v:set() for v in out}
    if tint is None:return out,changed
    for v in out:
        for y,row in enumerate(out[v]):
            for x,p in enumerate(row):
                if not p[3]:continue
                role=roles[f'{p[0]},{p[1]},{p[2]}']
                if role.startswith(prefix):
                    out[v][y][x]=_role_tint(p,tint)
                    if out[v][y][x]!=p: changed[v].add((x,y))
    return out,changed

def _apply_gray_tint(frames,tint):
    out=_copy(frames)
    if tint is None:return out
    for v in out:
        for y,row in enumerate(out[v]):
            for x,p in enumerate(row):
                if p[3]:
                    if not (p[0]==p[1]==p[2]):
                        raise ValueError(f'{v}: grayscale construction contains chromatic source pixel {p}')
                    out[v][y][x]=_tint(p,tint)
    return out

def _role_map_for(family,state):
    spec=_parts()['families'][family]
    if 'roleByStateRgb' in spec:
        return spec['roleByStateRgb'][state]
    return spec['roleByConstructionRgb'][state]

def _validate_explicit_roles(frames,family,state):
    mapping=_role_map_for(family,state)
    missing=set()
    for v in frames:
        for row in frames[v]:
            for p in row:
                if not p[3]:continue
                key=f'{p[0]},{p[1]},{p[2]}'
                if key not in mapping: missing.add(key)
    if missing:
        raise ValueError(f'{family}/{state}: source RGB without stored role: {sorted(missing)}')
    return mapping

def _component(cid):
    return next(p for p in _parts()['parts'] if p['id']==cid)

def apply_exact_source_patch(base_frames,cid):
    part=_component(cid)
    out=_copy(base_frames)
    for v,cells in part['views'].items():
        for cell in cells:
            x,y=cell['x'],cell['y']
            if tuple(out[v][y][x])!=tuple(cell['before']):
                raise ValueError(f'{cid}/{v}@{x},{y}: source construction drift')
            out[v][y][x]=tuple(cell['after'])
    return out

def verify_patch_reconstruction(cid):
    p=_component(cid)
    base,_=source_frames(p['sourcePack'],p['sourceBase'])
    var,_=source_frames(p['sourcePack'],p['sourceVariant'])
    got=apply_exact_source_patch(base,cid)
    return got==var

def _changed(before,after):
    return {v:{(x,y) for y,row in enumerate(after[v]) for x,p in enumerate(row)
               if p!=before[v][y][x]} for v in after}

def _alpha(frames):
    return {v:{(x,y) for y,row in enumerate(frames[v]) for x,p in enumerate(row) if p[3]}
            for v in frames}

def _assert_locked_geometry(source,out,allow_source_variant=False):
    a,b=_alpha(source),_alpha(out)
    if a==b:return
    if not allow_source_variant:
        raise ValueError('locked source construction alpha changed')

def beret(state='Beret',palette='source_native'):
    pack='Cottagecore Set'
    base,_=source_frames(pack,'Beret')
    component=None
    if state=='Beret':
        raw=base
    elif state=='Beret (Dotted)':
        component='beret.dots_patch';raw=apply_exact_source_patch(base,component)
    elif state=='Beret (Leaf)':
        component='beret.leaf_patch';raw=apply_exact_source_patch(base,component)
    elif state in ('Beret (Ribbon)','Beret (White Ribbon)'):
        # These source variants alter alpha as authored, so they are whole source
        # states, not optional patches. Locked construction is never erased by us.
        raw,_=source_frames(pack,state)
    else:
        raise ValueError(state)
    _validate_explicit_roles(raw,'beret',state)
    tint=GRAY_TINTS[palette]
    out=_apply_gray_tint(raw,tint)
    _assert_locked_geometry(raw,out)
    return RemixResult('beret',state,state,palette,component,out,raw,_changed(raw,out),{
        'constructionAuthority':'exact_source_state',
        'componentPolicy':'exact_source_patch' if component else 'none_or_whole_source_state',
        'genericProjectionUsed':False,'genericLineUsed':False,
        'paletteAuthority':'explicit_source_rgb_roles','paletteSelectionTier':('same_family_source' if palette=='source_native' else 'curated_transfer_group'),
    })

def beanie(construction='Beanie',palette='source_native'):
    pack='More Accessories and Stuff'
    raw,_=source_frames(pack,construction)
    _validate_explicit_roles(raw,'beanie',construction)
    out=_apply_gray_tint(raw,GRAY_TINTS[palette])
    _assert_locked_geometry(raw,out)
    return RemixResult('beanie',construction,construction,palette,None,out,raw,_changed(raw,out),{
        'constructionAuthority':'whole_source_alternate_state',
        'lockedFeatures':['crown','default_knit_band','defining_seams'],
        'genericProjectionUsed':False,'genericLineUsed':False,
        'paletteAuthority':'explicit_source_rgb_roles','paletteSelectionTier':('same_family_source' if palette=='source_native' else 'curated_transfer_group'),
    })

def straw(construction='Straw Hat',ribbon_palette='source_native'):
    pack='More Accessories and Stuff'
    raw,_=source_frames(pack,construction)
    roles=_validate_explicit_roles(raw,'straw_hat',construction)
    out=_copy(raw); tint=RIBBON_TINTS[ribbon_palette]; changed={v:set() for v in out}
    if tint is not None:
        for v in out:
            for y,row in enumerate(out[v]):
                for x,p in enumerate(row):
                    if not p[3]:continue
                    role=roles[f'{p[0]},{p[1]},{p[2]}']
                    if role.startswith('ribbon_'):
                        out[v][y][x]=_tint(p,tint); changed[v].add((x,y))
    _assert_locked_geometry(raw,out)
    # prove no straw body pixel changed when mutating built-in ribbon
    for v in out:
        for y,row in enumerate(out[v]):
            for x,p in enumerate(row):
                role=roles.get(f'{raw[v][y][x][0]},{raw[v][y][x][1]},{raw[v][y][x][2]}') if raw[v][y][x][3] else None
                if role and role.startswith('body_') and p!=raw[v][y][x]:
                    raise ValueError(f'{construction}/{v}: ribbon mutation touched locked straw body')
    return RemixResult('straw_hat',construction,construction,ribbon_palette,None,out,raw,changed,{
        'constructionAuthority':'whole_source_alternate_state',
        'lockedFeatures':['crown','brim','built_in_ribbon_geometry','defining_seams'],
        'mutableFeature':'built_in_ribbon_color',
        'genericProjectionUsed':False,'genericLineUsed':False,
        'paletteAuthority':'same_family_source_body_plus_explicit_ribbon_role_mask','paletteSelectionTier':('same_family_source' if ribbon_palette=='source_native' else 'curated_transfer_group'),
    })

def boater(state='Boater Hat',feature_palette='source_native'):
    pack='Cottagecore Set';base,_=source_frames(pack,'Boater Hat');component=None
    if state=='Boater Hat':
        raw=base
    elif state=='Boater Hat (Bow)':
        component='boater.bow_patch';raw=apply_exact_source_patch(base,component)
    elif state=='Boater Hat (Ribbons)':
        component='boater.ribbons_patch';raw=apply_exact_source_patch(base,component)
    else: raise ValueError(state)
    roles=_validate_explicit_roles(raw,'boater_hat',state)
    out,changed=_apply_role_prefix_tint(raw,roles,'feature_',RIBBON_TINTS[feature_palette])
    _assert_locked_geometry(raw,out)
    return RemixResult('boater_hat',state,state,feature_palette,component,out,raw,changed,{
      'constructionAuthority':'exact_source_state',
      'componentPolicy':'exact_same_construction_patch' if component else 'none',
      'lockedFeatures':['crown','brim','built_in_band_geometry'],
      'mutableFeature':'source_feature_color',
      'genericProjectionUsed':False,'genericLineUsed':False,
      'paletteAuthority':'explicit_source_rgb_feature_roles'})

def mushroom_hat(state='Mushroom Hat',body_palette='source_native'):
    pack='Cottagecore Set';base,_=source_frames(pack,'Mushroom Hat');component=None
    if state=='Mushroom Hat':
        raw=base
    elif state=='Mushroom Hat (Dotted)':
        component='mushroom.dotted_patch';raw=apply_exact_source_patch(base,component)
    else: raise ValueError(state)
    roles=_validate_explicit_roles(raw,'mushroom_hat',state)
    out,changed=_apply_role_prefix_tint(raw,roles,'body_',GRAY_TINTS[body_palette])
    _assert_locked_geometry(raw,out)
    return RemixResult('mushroom_hat',state,state,body_palette,component,out,raw,changed,{
      'constructionAuthority':'exact_source_state',
      'componentPolicy':'source_authored_surface_patch' if component else 'none',
      'lockedFeatures':['cap_geometry','stem','defining_seams'],
      'mutableFeature':'cap_color',
      'genericProjectionUsed':False,'genericLineUsed':False,
      'paletteAuthority':'explicit_source_rgb_body_roles'})

def sun_hat(state='Sun Hat',body_palette='source_native',feature_palette='source_native'):
    pack='More Accessories and Stuff';base,_=source_frames(pack,'Sun Hat');component=None
    if state=='Sun Hat':
        raw=base
    elif state=='Sun Hat (Flowers)':
        component='sun_hat.flowers_patch';raw=apply_exact_source_patch(base,component)
    elif state=='Sun Hat (Ribbon)':
        raw,_=source_frames(pack,state)
    else: raise ValueError(state)
    roles=_validate_explicit_roles(raw,'sun_hat',state)
    if state=='Sun Hat (Ribbon)':
        palette=feature_palette
        out,changed=_apply_role_prefix_tint(raw,roles,'feature_',RIBBON_TINTS[feature_palette])
    else:
        palette=body_palette
        out,changed=_apply_role_prefix_tint(raw,roles,'body_',GRAY_TINTS[body_palette])
    _assert_locked_geometry(raw,out)
    return RemixResult('sun_hat',state,state,palette,component,out,raw,changed,{
      'constructionAuthority':'whole_source_alternate_state' if state=='Sun Hat (Ribbon)' else 'exact_source_state',
      'componentPolicy':'exact_same_construction_patch' if component else 'none_or_whole_source_state',
      'lockedFeatures':['crown','brim','defining_seams'],
      'genericProjectionUsed':False,'genericLineUsed':False,
      'paletteAuthority':'explicit_source_rgb_roles'})

def tulip_hat(state='Tulip Hat',body_palette='source_native',pattern_palette='source_native'):
    pack='More Accessories and Stuff';base,_=source_frames(pack,'Tulip Hat');component=None
    if state=='Tulip Hat':
        raw=base
    elif state=='Tulip Hat (Striped)':
        component='tulip.striped_patch';raw=apply_exact_source_patch(base,component)
    else: raise ValueError(state)
    roles=_validate_explicit_roles(raw,'tulip_hat',state)
    if state=='Tulip Hat (Striped)':
        palette=pattern_palette
        out,changed=_apply_role_prefix_tint(raw,roles,'pattern_',RIBBON_TINTS[pattern_palette])
    else:
        palette=body_palette
        out,changed=_apply_role_prefix_tint(raw,roles,'body_',GRAY_TINTS[body_palette])
    _assert_locked_geometry(raw,out)
    return RemixResult('tulip_hat',state,state,palette,component,out,raw,changed,{
      'constructionAuthority':'exact_source_state',
      'componentPolicy':'source_authored_surface_patch' if component else 'none',
      'lockedFeatures':['petal_silhouette','defining_folds'],
      'genericProjectionUsed':False,'genericLineUsed':False,
      'paletteAuthority':'explicit_source_rgb_roles'})

def source_family_state(family,state=None,palette='source_native'):
    spec=_parts()['families'][family]
    pack=spec['pack']
    state=state or spec['base']
    if state not in spec['alternateConstructionStates']:
        raise ValueError(f'{family}: unknown authored state {state}')
    raw,_=source_frames(pack,state)
    roles=_validate_explicit_roles(raw,family,state)
    tintable=spec.get('tintableState',{}).get(state,False)
    if palette!='source_native' and not tintable:
        raise ValueError(f'{family}/{state}: chromatic authored state is source-native only')
    out,changed=_apply_role_prefix_tint(raw,roles,'body_',GRAY_TINTS[palette])
    _assert_locked_geometry(raw,out)
    return RemixResult(family,state,state,palette,None,out,raw,changed,{
      'constructionAuthority':'whole_authored_source_state',
      'componentPolicy':'none',
      'lockedFeatures':spec['lockedConstruction'],
      'genericProjectionUsed':False,'genericLineUsed':False,
      'paletteAuthority':'source_native' if palette=='source_native' else 'explicit_source_rgb_body_roles',
      'paletteSelectionTier':'same_family_source' if palette=='source_native' else 'curated_transfer_group'
    })

def validate_no_isolated_line_fragment(frames, changed, min_ratio=.45, min_pixels=4):
    """Reject a new horizontal treatment that collapses into a tiny centre dash.

    Only newly changed cells are considered. Source-authored lines/bands are not
    penalised because they are part of locked construction.
    """
    errors=[]
    for v,cells in changed.items():
        by_row={}
        for x,y in cells: by_row.setdefault(y,[]).append(x)
        if not by_row: continue
        alpha=_alpha(frames)[v]
        xs_all=[x for x,y in alpha]
        if not xs_all:continue
        width=max(xs_all)-min(xs_all)+1
        for y,xs in by_row.items():
            xs=sorted(set(xs)); longest=1 if xs else 0;run=1
            for a,b in zip(xs,xs[1:]):
                run=run+1 if b==a+1 else 1;longest=max(longest,run)
            # Only classify it as a line-like treatment when most changed cells
            # in this view share one row.
            if len(xs)>=2 and len(xs)>=sum(len(q) for q in by_row.values())*.65:
                need=max(min_pixels,round(width*min_ratio))
                centred=(sum(xs)/len(xs))>min(xs_all)+width*.25 and (sum(xs)/len(xs))<min(xs_all)+width*.75
                if centred and longest<need:
                    errors.append(f'{v}:floating_or_isolated_line_fragment:{longest}<{need}')
    return errors
