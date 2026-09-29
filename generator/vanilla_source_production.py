"""Production adapter for Stardew-native source-preserving clothing variation.

This is not the old side experiment. It is a source-provenance adapter used by
the production router. Exact vanilla alpha/geometry stays authoritative.
"""
from __future__ import annotations
import colorsys,hashlib,json,math
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
GAME=Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer')
CONTRACTS=ROOT/'generator/data/vanilla_source_contracts.json'
PALETTES=ROOT/'authored/palettes.json'
VIEWS=('front','right','left','back')

def contracts(): return json.loads(CONTRACTS.read_text())
def palettes(): return {p['id']:p for p in json.loads(PALETTES.read_text())['palettes']}
def _sheet(kind): return Image.open(GAME/('hats.png' if kind=='hat' else 'shirts.png')).convert('RGBA')
def source_frames(kind:str,index:int):
    im=_sheet(kind)
    if kind=='hat':
        c,r=index%12,index//12; block=im.crop((c*20,r*80,c*20+20,r*80+80)); size=20
    elif kind=='shirt':
        c,r=index%32,index//32; block=im.crop((c*8,r*32,c*8+8,r*32+32)); size=8
    else: raise ValueError(kind)
    return {v:block.crop((0,i*size,size,(i+1)*size)) for i,v in enumerate(VIEWS)}
def _lum(p): return .299*p[0]+.587*p[1]+.114*p[2]
def _target(pal,lane):
    ramp=palettes()[pal]['ramps'][lane]; h=ramp[len(ramp)//2].lstrip('#'); return tuple(int(h[i:i+2],16) for i in (0,2,4))
def _tint_keep_luma(px,target,strength=.82):
    if not px[3]: return px
    Y=_lum(px); th,ts,tv=colorsys.rgb_to_hsv(*(c/255 for c in target)); rr,gg,bb=colorsys.hsv_to_rgb(th,max(.22,ts),max(.10,min(1,Y/255)))
    raw=[px[i]*(1-strength)+255*q*strength for i,q in enumerate((rr,gg,bb))]; cur=.299*raw[0]+.587*raw[1]+.114*raw[2]; d=Y-cur
    return (*[max(0,min(255,round(q+d))) for q in raw],px[3])
def _copy(frames): return {v:frames[v].copy() for v in VIEWS}
def _alpha_hash(frames):
    h=hashlib.sha256()
    for v in VIEWS:
        for p in frames[v].getdata(): h.update(bytes((p[3],)))
    return h.hexdigest()
def _recolor(source,palette):
    out=_copy(source); tgt=_target(palette,'body')
    for im in out.values():
        for y in range(im.height):
            for x in range(im.width):
                p=im.getpixel((x,y))
                if p[3] and _lum(p)>35: im.putpixel((x,y),_tint_keep_luma(p,tgt,.84))
    return out
def _bbox(im):
    pts=[(x,y) for y in range(im.height) for x in range(im.width) if im.getpixel((x,y))[3]]
    if not pts:return None
    return min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)
def _crown_band(out,palette):
    tgt=_target(palette,'trim'); changed=0
    for im in out.values():
        b=_bbox(im)
        if not b: continue
        x0,y0,x1,y1=b; h=y1-y0+1; y=y0+max(2,round(h*.45)); xs=[x for x in range(x0,x1+1) if im.getpixel((x,y))[3]]
        if len(xs)<5: continue
        for x in xs[1:-1]:
            p=im.getpixel((x,y))
            if p[3] and _lum(p)>35: im.putpixel((x,y),_tint_keep_luma(p,tgt,.94)); changed+=1
    return changed
def _shirt_grammar(out,grammar,palette):
    im=out['front']; tgt=_target(palette,'accent'); changed=0; w,h=im.size
    cells=[]
    if grammar=='horizontal_stripe_or_band': cells=[(x,max(2,min(h-3,round(h*.55)))) for x in range(1,w-1)]
    elif grammar=='placket_or_buttons': cells=[(w//2,y) for y in range(2,h-1,2)]
    elif grammar=='compact_graphic':
        c=w//2; cells=[(c,3),(c-1,4),(c,4),(c+1,4)]
    elif grammar=='checker_or_plaid': cells=[(x,y) for y in range(2,h-1) for x in range(1,w-1) if (x+y)%2==0]
    for x,y in cells:
        if 0<=x<w and 0<=y<h:
            p=im.getpixel((x,y))
            if p[3]: im.putpixel((x,y),_tint_keep_luma(p,tgt,.90)); changed+=1
    return changed
def _region_style(out,palette):
    tgt=_target(palette,'trim'); changed=0
    for im in out.values():
        b=_bbox(im)
        if not b: continue
        x0,y0,x1,y1=b; split=y0+(y1-y0+1)*.62
        for y in range(im.height):
            for x in range(im.width):
                p=im.getpixel((x,y))
                if p[3] and y>=split and _lum(p)>42:
                    im.putpixel((x,y),_tint_keep_luma(p,tgt,.55)); changed+=1
    return changed
def render(kind:str,index:int,palette:str='COASTAL_SEAFOAM_CORAL')->dict:
    table=contracts()['hats' if kind=='hat' else 'shirts']; key=str(index)
    if key not in table: raise KeyError(f'unpromoted vanilla {kind} {index}')
    contract=table[key]; source=source_frames(kind,index); out=_recolor(source,palette); used=['recolor']; changedExtra=0
    allowed=contract['allowed']
    if kind=='hat' and 'crown_band' in allowed:
        changedExtra+=_crown_band(out,palette); used.append('crown_band')
    if kind=='shirt':
        grammar=next((g for g in ('horizontal_stripe_or_band','placket_or_buttons','compact_graphic','checker_or_plaid') if g in allowed),None)
        if grammar: changedExtra+=_shirt_grammar(out,grammar,palette); used.append(grammar)
        elif 'region_style' in allowed: changedExtra+=_region_style(out,palette); used.append('region_style')
    if _alpha_hash(source)!=_alpha_hash(out): raise RuntimeError('vanilla geometry/alpha drift')
    return {'provenance':'VANILLA','kind':kind,'sourceIndex':index,'sourceName':contract.get('name',f'Vanilla {kind} {index}'),'capacity':contract['capacity'],'allowed':allowed,'used':used,'palette':palette,'sourceFrames':source,'frames':out,'extraChangedPixels':changedExtra,'productionAuthority':'STARDEW_SOURCE_PIXELS_FIRST'}
def promoted(kind:str):
    table=contracts()['hats' if kind=='hat' else 'shirts']; return [int(x) for x in sorted(table,key=lambda q:int(q))]
