"""Production-only source-respecting hat selection/rendering.

Rarity/taste/capacity decide semantic intensity. Pixels may only come from
human-approved source-respecting state/palette pairs in the golden registry.
There is deliberately no donor projection, STYLE_PROFILE fallback, or generic
line synthesis in this module.
"""
from __future__ import annotations
import hashlib,itertools,json
from pathlib import Path
from typing import Any
from generator.catalog_templates import load_family
from generator.taste_policy import evaluate_recipe
from generator.hat_visual_rules import contract_for,recipe_visual_precheck
from generator.hat_hybrid_enhancements import enhance_frames
from generator.source_respecting_hat_remix import (
 beret,beanie,straw,boater,mushroom_hat,sun_hat,tulip_hat,
 source_family_state,RemixResult,
)
ROOT=Path(__file__).resolve().parents[1]
GOLDENS=ROOT/'generator/data/source_respecting_hat_goldens.json'
PARTS=ROOT/'generator/data/source_parts/hat_source_parts.json'
RARITIES=('common','uncommon','rare','epic')
PRESENTATION_LEANS=('neutral','male_leaning','female_leaning')

def _idx(key:str,n:int)->int:
 return int(hashlib.sha256(key.encode()).hexdigest()[:12],16)%n

def load_goldens()->dict:
 j=json.loads(GOLDENS.read_text())
 if not j.get('humanArtApproved') or j.get('familyCount')!=20:
  raise RuntimeError('hat golden registry is not production-approved')
 rules=j['rules']
 if rules.get('genericProjectionAllowed') or rules.get('genericLineSynthesisAllowed') or rules.get('legacyStyleProfileFallbackAllowed'):
  raise RuntimeError('golden registry illegally enables legacy rendering')
 return j


def _parts()->dict:
 return json.loads(PARTS.read_text())


def legal_recipe_pool(template_family:str,rarity:str):
 """Existing taste policy + capacity + visual exclusions remain authoritative."""
 pol=load_family(template_family);visual=contract_for(template_family)
 axes=list(pol['vocabulary']);rows=[]
 for vals in itertools.product(*(pol['vocabulary'][a] for a in axes)):
  rec=dict(zip(axes,vals));rep=evaluate_recipe(rec,rarity,pol)
  if rep.valid and not recipe_visual_precheck(rec,visual):rows.append((rec,rep))
 if not rows:raise RuntimeError(f'{template_family}: no legal {rarity} recipe')
 high=max(x[1].complexity for x in rows)
 return [x for x in rows if x[1].complexity>=max(0,high-1)]


def select_recipe(template_family:str,rarity:str):
 pool=legal_recipe_pool(template_family,rarity)
 return pool[_idx(f'{template_family}|{rarity}|recipe',len(pool))]


def select_presentation_lean(template_family:str,rarity:str,mode:str='mixed')->str:
 if mode in PRESENTATION_LEANS:return mode
 if mode!='mixed':raise ValueError(f'unknown presentation lean mode {mode!r}')
 return PRESENTATION_LEANS[_idx(f'{template_family}|{rarity}|presentation',3)]


def _pair_distinctiveness(source_family:str,pair:dict)->float:
 spec=_parts()['families'][source_family];state=pair['state'];pal=pair['palette']
 s=0.0 if state==spec['base'] else 2.0
 if pal!='source_native':s+=1.0
 name=state.lower()
 for token in ('dotted','striped','flower','leaf','ribbon','bow','cat','bunny','horn','wing','studded','puffs','tie','messy','floppy','wide','pointy','side','coronet','diadem'):
  if token in name:s+=0.35
 return s


def _semantic_bonus(recipe:dict,pair:dict)->float:
 name=pair['state'].lower();bonus=0.0
 patt=recipe.get('pattern','solid')
 if patt in ('stripe','dense','colorblock') and any(x in name for x in ('strip','dot','plaid')):bonus+=1.0
 if recipe.get('attachment') not in (None,'none') and any(x in name for x in ('bow','ribbon','flower','leaf','cat','bunny','horn','wing','puffs','tie')):bonus+=1.0
 if recipe.get('motif') not in (None,'none') and any(x in name for x in ('dot','flower','leaf','studded','diadem')):bonus+=0.7
 if recipe.get('materialTreatment') in ('textured','statement') and pair['palette']!='source_native':bonus+=0.5
 return bonus


def select_approved_pair(template_family:str,rarity:str,recipe:dict,presentation_lean:str)->dict:
 gold=load_goldens()['families'][template_family];source=gold['sourceFamily']
 pairs=list(gold['approvedPairs'])
 ordered=sorted(enumerate(pairs),key=lambda x:(_pair_distinctiveness(source,x[1]),x[0]))
 rank=RARITIES.index(rarity)
 # Small approved pools exhaust distinct states before reuse. Never fabricate a
 # fourth visual just to make rarity look different.
 if len(ordered)<=4:return dict(ordered[min(rank,len(ordered)-1)][1])
 target=round((len(ordered)-1)*(rank/3))
 # Common and Epic anchor the cleanest/most-distinctive approved ends.
 if rank==0:return dict(ordered[0][1])
 if rank==3:return dict(ordered[-1][1])
 lo=max(0,target-1);hi=min(len(ordered)-1,target+1)
 options=ordered[lo:hi+1]
 scored=[]
 for original,p in options:
  bonus=_semantic_bonus(recipe,p)
  jitter=_idx(f'{template_family}|{rarity}|{presentation_lean}|{p["state"]}|{p["palette"]}',1000)/1000000
  scored.append((-bonus+jitter,original,p))
 scored.sort(key=lambda x:(x[0],x[1]))
 return dict(scored[0][2])


def render_approved_pair(template_family:str,pair:dict)->RemixResult:
 gold=load_goldens()['families'][template_family];source=gold['sourceFamily']
 allowed={(x['state'],x['palette']) for x in gold['approvedPairs']}
 key=(pair['state'],pair['palette'])
 if key not in allowed:raise RuntimeError(f'{template_family}: unapproved pair {key}')
 state,palette=key
 if source=='beret':res=beret(state=state,palette=palette)
 elif source=='beanie':res=beanie(construction=state,palette=palette)
 elif source=='straw_hat':res=straw(construction=state,ribbon_palette=palette)
 elif source=='boater_hat':res=boater(state=state,feature_palette=palette)
 elif source=='mushroom_hat':res=mushroom_hat(state=state,body_palette=palette)
 elif source=='sun_hat':res=sun_hat(state=state,body_palette=palette,feature_palette=palette)
 elif source=='tulip_hat':res=tulip_hat(state=state,body_palette=palette,pattern_palette=palette)
 else:res=source_family_state(source,state=state,palette=palette)
 if res.trace.get('genericProjectionUsed') or res.trace.get('genericLineUsed'):
  raise RuntimeError(f'{template_family}: source-respecting renderer reported legacy path')
 return res


def roll_and_render(template_family:str,rarity:str,presentation_mode:str='mixed')->dict[str,Any]:
 if rarity not in RARITIES:raise ValueError(rarity)
 reg=load_goldens();gold=reg['families'][template_family]
 rec,rep=select_recipe(template_family,rarity)
 lean=select_presentation_lean(template_family,rarity,presentation_mode)
 pair=select_approved_pair(template_family,rarity,rec,lean)
 golden_res=render_approved_pair(template_family,pair)
 enhanced_frames,enhancement=enhance_frames(golden_res.frames,gold['sourceFamily'],rec,rarity)
 changed={v:sum(1 for y,row in enumerate(golden_res.frames[v]) for x,p in enumerate(row) if p!=enhanced_frames[v][y][x]) for v in ('front','right','left','back')}
 trace=dict(golden_res.trace)
 trace.update({
  'nativeHybridEnhancement':True,
  'hybridAuthority':'GOLDEN_SOURCE_PIXELS_FIRST',
  'hybridApplied':enhancement.applied,
  'hybridFallbackReason':enhancement.fallback_reason,
  'hybridChangedPixels':enhancement.changed_pixels,
  'hybridChangedRatio':enhancement.changed_ratio,
  'outlinePreserved':enhancement.outline_preserved,
  'alphaPreserved':enhancement.alpha_preserved,
  'photoTailorDependency':False,
  'prototypeImportUsed':False,
 })
 res=RemixResult(
  family=golden_res.family,construction=golden_res.construction,source_state=golden_res.source_state,
  palette=golden_res.palette,component=golden_res.component,frames=enhanced_frames,
  source_frames=golden_res.frames,changed=changed,trace=trace,
 )
 cap=load_family(template_family)['familyCapacity']
 return {
  'family':template_family,'sourceFamily':gold['sourceFamily'],'rarity':rarity,
  'capacity':cap['surfaceAreaClass'],'presentationLean':lean,
  'presentationLeanPolicy':'BIAS_NOT_HARD_LOCK','recipe':rec,
  'taste':{'complexity':rep.complexity,'budget':[rep.budget_min,rep.budget_max],
   'channels':list(rep.active_channels),'primary':rep.primary,
   'secondary':list(rep.secondary),'accents':list(rep.accents)},
  'approvedPair':pair,'renderResult':res,'contractDigest':gold['contractDigest'],
  'productionAuthority':'GOLDEN_SOURCE_RESPECTING_HYBRID_V1','goldenAuthority':'HAT_PRODUCTION_GOLDEN_V1',
  'hybridEnhancement':{
   'applied':enhancement.applied,'fallbackReason':enhancement.fallback_reason,
   'changedPixels':enhancement.changed_pixels,'changedRatio':round(enhancement.changed_ratio,6),
   'outlinePreserved':enhancement.outline_preserved,'alphaPreserved':enhancement.alpha_preserved,
   'pattern':enhancement.pattern,'motif':enhancement.motif,'motifPlacement':enhancement.motif_placement,
   'regionMode':enhancement.region_mode,
  },
  'fallbackRendererUsed':bool(enhancement.fallback_reason),
  'genericProjectionUsed':False,'genericLineUsed':False,'photoTailorDependencyUsed':False,
 }
