#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from generator.catalog_templates import load_family
from generator.taste_policy import evaluate_recipe
from generator.hat_visual_rules import contract_for,recipe_visual_precheck
from generator.source_respecting_hat_production import RARITIES,PRESENTATION_LEANS,load_goldens,render_approved_pair
from v5.pngio import read_rgba_png
BATCH=ROOT/'experiments/hat_production_source_respecting_final_01/manifest.json'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
 reg=load_goldens();assert reg['familyCount']==20
 assert sum(len(x['approvedPairs']) for x in reg['families'].values())==147
 assert reg['rules']['sourceConstructionRulesAuthoritative'] is True
 assert reg['rules']['approvedPairWhitelistRequired'] is True
 assert reg['rules']['genericProjectionAllowed'] is False
 assert reg['rules']['genericLineSynthesisAllowed'] is False
 assert reg['rules']['legacyStyleProfileFallbackAllowed'] is False

 for b in reg['approvedBatches']:
  p=ROOT/b['manifest'];j=json.loads(p.read_text())
  assert j['humanArtApproved'] is True,(b['id'],'not approved')
  assert j['humanApprovalStatus']=='HUMAN_ART_APPROVED'
  assert all(c['status']=='HUMAN_ART_APPROVED' for c in j['candidates'])
  assert sha(p)==b['manifestSha256'],(b['id'],'approved manifest drift')

 parts_path=ROOT/'generator/data/source_parts/hat_source_parts.json';parts=json.loads(parts_path.read_text())
 assert sha(parts_path)==reg['sourcePartsSha256'],'source part registry drifted after freeze'
 assert len(parts['families'])==20
 assert all(x.get('humanArtApproved') is True for x in parts['families'].values())
 assert all(x.get('productionAuthority')=='GOLDEN_SOURCE_RESPECTING_V1' for x in parts['families'].values())
 model=json.loads((ROOT/'generator/data/source_respecting_remix_model.json').read_text())
 assert model['production']['status']=='AUTHORITATIVE'
 assert model['production']['familyCount']==20
 assert model['production']['genericProjectionEnabled'] is False
 assert model['production']['genericLineSynthesisEnabled'] is False
 assert model['production']['legacyStyleProfileFallbackEnabled'] is False

 # The production entry point must not contain the retired compositor vocabulary.
 src=(ROOT/'tools/build_hat_production_batch.py').read_text()
 forbidden=['compatible_donors','apply_style_profile','render_proportional_line','def delta(','def surface(','def attach(','STYLE_PROFILE']
 for token in forbidden:assert token not in src,token
 assert 'roll_and_render' in src

 m=json.loads(BATCH.read_text());assert m['schema']=='hat-production-source-respecting/v1'
 assert m['familyCount']==20 and m['candidateCount']==80
 assert m['rarityCounts']=={r:20 for r in RARITIES}
 assert m['productionAuthority']=='GOLDEN_SOURCE_RESPECTING_V1'
 assert m['approvedPairWhitelistRequired'] is True
 assert m['genericProjectionAllowed'] is False
 assert m['genericLineSynthesisAllowed'] is False
 assert m['legacyStyleProfileFallbackAllowed'] is False
 assert len(m['contactSheets'])==23 # all + A/B + 20 directional sheets

 by_family=defaultdict(list);leans=Counter()
 for c in m['candidates']:
  fam=c['family'];rar=c['rarity'];by_family[fam].append(c);leans[c['presentationLean']]+=1
  assert fam in reg['families'];assert rar in RARITIES
  assert c['presentationLean'] in PRESENTATION_LEANS
  assert c['presentationLeanPolicy']=='BIAS_NOT_HARD_LOCK'
  assert c['fallbackRendererUsed'] is False
  assert c['genericProjectionUsed'] is False and c['genericLineUsed'] is False
  assert c['productionAuthority']=='GOLDEN_SOURCE_RESPECTING_V1'
  assert c['contractDigest']==reg['families'][fam]['contractDigest']
  allowed={(x['state'],x['palette']) for x in reg['families'][fam]['approvedPairs']}
  assert (c['sourceState'],c['palette']) in allowed,(fam,c['sourceState'],c['palette'])
  assert (c['approvedPair']['state'],c['approvedPair']['palette'])==(c['sourceState'],c['palette'])
  rep=evaluate_recipe(c['recipe'],rar,load_family(fam));assert rep.valid,(fam,rar,rep.errors)
  assert not recipe_visual_precheck(c['recipe'],contract_for(fam)),(fam,rar,'visual precheck')
  assert c['taste']['complexity']==rep.complexity
  assert c['taste']['budget']==[rep.budget_min,rep.budget_max]
  # Re-render through the approved-only entry point and require exact pixels.
  expected=render_approved_pair(fam,c['approvedPair'])
  assert expected.trace.get('genericProjectionUsed') is False
  assert expected.trace.get('genericLineUsed') is False
  for v,path in c['frames'].items():
   assert read_rgba_png(ROOT/path)==expected.frames[v],(fam,rar,v,'pixel drift')

 assert set(by_family)==set(reg['families']) and len(by_family)==20
 for fam,rows in by_family.items():
  assert {c['rarity'] for c in rows}==set(RARITIES)
  approved_count=len(reg['families'][fam]['approvedPairs'])
  used={(c['sourceState'],c['palette']) for c in rows}
  assert len(used)>=min(4,approved_count),(fam,'reused approved states too early')
 assert set(leans)==set(PRESENTATION_LEANS)

 print('PASS 20/20 hats frozen as human-approved goldens')
 print('PASS 147 approved state/palette pairs are the only production pixel choices')
 print('PASS production builder has no legacy donor/style-profile/line compositor path')
 print('PASS 80 candidates = 20 families x Common/Uncommon/Rare/Epic')
 print('PASS every rarity recipe revalidates against taste, capacity, roll exclusions, and visual precheck')
 print('PASS every saved frame pixel-matches a re-rendered approved source-respecting pair')
 print('PASS presentation lean remains neutral/male/female bias-only:',dict(leans))
 print('PASS 3 cross-family sheets + 20 per-family directional sheets')
if __name__=='__main__':main()
