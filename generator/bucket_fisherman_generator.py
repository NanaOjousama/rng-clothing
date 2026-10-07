from __future__ import annotations
import json, random, hashlib
from pathlib import Path
from v5.pngio import read_rgba_png
from v5.source.template_transfer import load_contract, template_frames, assert_geometry_preserved

ROOT=Path(__file__).resolve().parents[1]
MATRIX_PATH=ROOT/'generator/data/headwear/bucket_fisherman_navy16_roll_matrix.json'
TEMPLATE_PATH=ROOT/'generator/data/templates/bucket_fisherman_navy16.json'
VIEWS=('front','right','back','left')

PALETTES={
 'navy':[(8,13,35),(24,28,64),(40,47,84),(95,120,157),(150,170,200)],
 'cream':[(70,48,30),(142,105,68),(205,170,120),(245,220,175),(255,246,211)],
 'olive_moss':[(45,47,20),(69,64,42),(105,103,50),(149,148,81),(194,194,118)],
 'rust':[(56,29,20),(105,52,28),(153,90,42),(203,156,108),(223,180,127)],
 'pastel_pink':[(81,9,39),(145,55,88),(205,120,150),(251,183,204),(255,222,232)],
 'rain_yellow':[(82,45,16),(130,82,28),(185,145,55),(233,197,94),(243,213,111)]
}
RARITIES=('Common','Uncommon','Rare','Epic')

def _lum(p): return p[0]*299+p[1]*587+p[2]*114
def _weighted(rng, weights, allowed=None):
    pairs=[(k,v) for k,v in weights.items() if allowed is None or k in allowed]
    total=sum(v for _,v in pairs); n=rng.uniform(0,total); acc=0
    for k,v in pairs:
        acc+=v
        if n<=acc:return k
    return pairs[-1][0]

def roll_recipe(seed:int, rarity:str)->dict:
    m=json.loads(MATRIX_PATH.read_text()); rng=random.Random(seed)
    rp=m['rarityPolicy'][rarity]; a=m['axes']
    return {
      'seed':seed,'rarity':rarity,'construction':'bucket_fisherman_navy16',
      'material':_weighted(rng,a['material']),
      'pattern':_weighted(rng,a['pattern'],rp['allowPattern']),
      'wraparound':_weighted(rng,a['wraparound'],rp['allowWraparound']),
      'motif':_weighted(rng,a['motif'],rp['allowMotif']),
      'palette':_weighted(rng,a['palette'])
    }

def _alpha_cells(fr):
    return {(x,y) for y,row in enumerate(fr) for x,p in enumerate(row) if p[3]}

def _boundary(fr):
    op=_alpha_cells(fr)
    return {p for p in op if any((p[0]+dx,p[1]+dy) not in op for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))}

def _palette_map(frame,ramp):
    vals=sorted({_lum(p) for row in frame for p in row if p[3]})
    out=[row[:] for row in frame]
    for y,row in enumerate(frame):
      for x,p in enumerate(row):
        if not p[3]:continue
        rank=min(range(len(vals)),key=lambda i:abs(vals[i]-_lum(p)))
        ri=round(rank*(len(ramp)-1)/max(1,len(vals)-1))
        out[y][x]=(*ramp[ri],p[3])
    return out

def _shade_index(rgb,ramp):
    return min(range(len(ramp)),key=lambda i:sum(abs(rgb[j]-ramp[i][j]) for j in range(3)))

def _apply_surface(frame,recipe):
    ramp=PALETTES[recipe['palette']]
    out=_palette_map(frame,ramp); b=_boundary(out); op=_alpha_cells(out); interior=op-b
    material=recipe['material']
    for x,y in sorted(interior):
      i=_shade_index(out[y][x][:3],ramp)
      if material=='canvas' and (x*3+y*5)%11==0: i=max(0,i-1)
      elif material=='corduroy_like' and x%3==0: i=min(4,i+1)
      elif material=='waterproof_rain' and (x+y)%7==0: i=min(4,i+1)
      out[y][x]=(*ramp[i],out[y][x][3])
    pat=recipe['pattern']
    if pat=='gingham':
      for x,y in sorted(interior):
        i=_shade_index(out[y][x][:3],ramp)
        if x%4==0 or y%4==0: i=max(0,i-1)
        if x%4==0 and y%4==0: i=min(4,i+1)
        out[y][x]=(*ramp[i],out[y][x][3])
    elif pat=='patchwork_large_blocks':
      for x,y in sorted(interior):
        i=_shade_index(out[y][x][:3],ramp)
        shift=(-1,0,1)[((x//4)+(y//3))%3]
        i=max(0,min(4,i+shift))
        out[y][x]=(*ramp[i],out[y][x][3])
    wrap=recipe['wraparound']
    if wrap!='none':
      ys=[y for x,y in op]; y0=max(ys)-3
      for x,y in sorted(interior):
        if y in (y0,y0+1):
          i=1 if wrap=='contrast_band' else 2
          if wrap=='floral_band' and (x+y)%4==0:i=4
          out[y][x]=(*ramp[i],out[y][x][3])
    return out

def _place_motif(front,recipe):
    motif=recipe['motif']
    if motif=='none': return front, None
    op=_alpha_cells(front); out=[row[:] for row in front]
    if motif=='mushroom_patch':
      cells=[(0,0,(236,104,12)),(1,0,(236,104,12)),(2,0,(236,104,12)),(1,1,(255,211,181)),(1,2,(255,211,181))]
    else:
      cells=[(1,0,(255,248,225)),(0,1,(255,248,225)),(1,1,(240,190,40)),(2,1,(255,248,225)),(1,2,(255,248,225))]
    # Search around lower-front body center.
    preferred=(6,7)
    for rad in range(0,5):
      for dy in range(-rad,rad+1):
       for dx in range(-rad,rad+1):
        ox,oy=preferred[0]+dx,preferred[1]+dy
        if all((ox+x,oy+y) in op for x,y,c in cells):
          for x,y,c in cells: out[oy+y][ox+x]=(*c,out[oy+y][ox+x][3])
          return out,{'offset':[ox,oy],'cells':len(cells)}
    return out,{'skipped':'no-safe-fit'}

def render_recipe(recipe:dict):
    base=template_frames(load_contract(TEMPLATE_PATH)); rendered={}; reports={}
    for v in ('front','right','back'):
      fr=_apply_surface(base[v],recipe)
      motif=None
      if v=='front': fr,motif=_place_motif(fr,recipe)
      assert_geometry_preserved(base[v],fr)
      rendered[v]=fr; reports[v]={'geometryPreserved':True,'motif':motif}
    rendered['left']=[list(reversed(r)) for r in rendered['right']]
    assert_geometry_preserved(base['left'],rendered['left'])
    reports['left']={'geometryPreserved':True,'mirrorOf':'right'}
    return rendered,reports

def pixel_sha(fr):
    return hashlib.sha256(bytes(c for row in fr for p in row for c in p)).hexdigest()
