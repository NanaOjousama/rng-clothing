#!/usr/bin/env python3
from pathlib import Path
import json, random, sys

ROOT=Path('/run/media/deck/USD00/RNG_clothing')
sys.path.insert(0,str(ROOT))
from generator.taste_policy import evaluate_registered_recipe, report_dict

MATRIX=json.loads((ROOT/'generator/data/headwear/slouch_beanie_roll_matrix.json').read_text())
SEED=9222026
RNG=random.Random(SEED)
TARGETS=[
    ('common','WHOLE_HAT'),
    ('common','WRAPAROUND_REGION'),
    ('uncommon','WHOLE_HAT'),
    ('uncommon','WRAPAROUND_REGION'),
    ('rare','WHOLE_HAT'),
    ('rare','LOCALIZED'),
    ('epic','WRAPAROUND_REGION'),
    ('epic','LOCALIZED'),
]

def weighted(axis, rarity):
    items=MATRIX['axes'][axis]
    guidance=set(MATRIX['rarityGuidance'].get(rarity,[]))
    vals=[]; weights=[]
    for k,w in items.items():
        boost=5 if k in guidance else 1
        vals.append(k); weights.append(max(1,w)*boost)
    return RNG.choices(vals,weights=weights,k=1)[0]

def matches(recipe, cond):
    for k,v in cond.items():
        actual=recipe.get(k)
        if isinstance(v,list):
            if actual not in v: return False
        elif actual!=v: return False
    return True
def valid(recipe):
    for ex in MATRIX['exclusions']:
        if 'when' in ex and not matches(recipe,ex['when']):
            continue
        if 'whenNot' in ex and matches(recipe,ex['whenNot']):
            continue
        if 'force' in ex:
            for k,v in ex['force'].items():
                if recipe.get(k)!=v: return False
        if 'disallow' in ex:
            for k,vals in ex['disallow'].items():
                if recipe.get(k) in vals: return False
        if 'allowOnly' in ex:
            for k,vals in ex['allowOnly'].items():
                if recipe.get(k) not in vals: return False
    return True

def roll_one(rarity):
    axes=[a for a in MATRIX['rollOrder'] if a in MATRIX['axes']]
    for _ in range(10000):
        r={a:weighted(a,rarity) for a in axes}
        if rarity=='common':
            r['motif']='none'; r['decorationStyle']='none'; r['motifPlacement']='none'
            r['carrierStyle']='none'; r['microAccent']='none'; r['attachment']='none'
            r['hardwareAccent']='none'
        if valid(r) and evaluate_registered_recipe(ROOT,'slouch_beanie',r,rarity).valid: return r
    raise RuntimeError('failed to roll '+rarity)
def consistency(recipe):
    localized=any([
        recipe.get('microAccent') not in (None,'none','diagonal_wrap_band'),
        recipe.get('motif') not in (None,'none'),
        recipe.get('carrierStyle') not in (None,'none'),
        recipe.get('decorationStyle') not in (None,'none'),
    ])
    wrap=recipe.get('trimAccent')!='none' or recipe.get('pattern')=='contrast_cuff' or recipe.get('microAccent')=='diagonal_wrap_band'
    if localized: return 'LOCALIZED'
    if wrap: return 'WRAPAROUND_REGION'
    return 'WHOLE_HAT'

def material_profile(recipe):
    k=recipe.get('knitStructure')
    p=recipe.get('pattern')
    if k=='cable': return 'cable_knit'
    if p=='heather': return 'heather_knit'
    if p in {'single_stripe','twin_stripe','contrast_cuff','two_tone_block'}: return 'stripe_colorblock'
    if p=='plaid_woven': return 'plaid_woven'
    if k in {'fleece_wool','brushed'}: return 'fleece_wool'
    return 'rib_knit'
def front_prompt(recipe, rarity):
    bits=['slouch beanie']
    bits.append(recipe['knitStructure'].replace('_',' ')+' knit')
    if recipe['pattern']!='solid':
        bits.append(recipe['pattern'].replace('_',' '))
    if recipe['bandType']!='none':
        bits.append(recipe['bandType'].replace('_',' '))
    if recipe['trimAccent']!='none':
        bits.append(recipe['trimAccent'].replace('_',' '))
    bits += [recipe['slouchDepth'].replace('_',' ')+' slouch', recipe['drapeDirection'].replace('_',' ')]
    if consistency(recipe)=='LOCALIZED':
        bits.append('leave localized decoration off the base hat; decoration is added later')
    return ', '.join(bits)+'. Simple wearable Stardew-style hat; preserve a clean isolated hat.'

def main():
    out=ROOT/'experiments/sfp2_rarity_batch/reroll_v2'
    out.mkdir(parents=True,exist_ok=True)
    mats=json.loads((ROOT/'authored/materials/slouch_beanie_v1/manifest.json').read_text())
    small=mats['smallScaleEvidencePool']
    recipes=[]
    seen=set()
    for i,(rarity,target_class) in enumerate(TARGETS):
        for _ in range(20000):
            rec=roll_one(rarity)
            if consistency(rec)!=target_class:
                continue
            if rarity=='rare' and target_class=='WHOLE_HAT':
                if not (rec['knitStructure']=='cable' or rec['pattern'] in {'simple_jacquard','plaid_woven'} or rec['slouchDepth']=='extra'):
                    continue
            if rarity=='epic' and target_class=='WRAPAROUND_REGION':
                if not (rec['trimAccent'] in {'double_trim_lines','crown_trim_line'} or rec['microAccent']=='diagonal_wrap_band' or rec['pattern']=='contrast_cuff'):
                    continue
            if rarity=='epic' and target_class=='LOCALIZED':
                if rec['microAccent']=='none' and rec['motif'] in {'none','star','moon','heart'}:
                    continue
            sig=json.dumps(rec,sort_keys=True)
            if sig in seen:
                continue
            seen.add(sig)
            break
        else:
            raise RuntimeError(f'failed target {rarity}/{target_class}')
        rid=f"SFP2_{rarity.upper()}_{1+sum(1 for x in recipes if x['rarity']==rarity)}"
        profile=material_profile(rec)
        refs=mats['profiles'][profile]['semanticEvidence']
        taste=report_dict(evaluate_registered_recipe(ROOT,'slouch_beanie',rec,rarity))
        item={'id':rid,'rarity':rarity,'recipe':rec,'consistencyClass':consistency(rec),'materialProfile':profile,'taste':taste}
        recipes.append(item)
        spec={
          'operation':'style-reference','size':16,'prompt':front_prompt(rec,rarity),
          'referenceRoles':[
            {'role':'construction','localPath':'authored/templates/slouch_pl24/front.png','note':'approved slouch construction'},
            {'role':'overall_style','localPath':small[i%len(small)],'note':'approved small-scale beanie evidence'},
            {'role':'material','localPath':refs[0],'note':profile+' material evidence'},
            {'role':'material','localPath':refs[1],'note':profile+' material evidence alternate'}
          ]
        }
        (out/f'{rid}_front_request.json').write_text(json.dumps(spec,indent=2)+'\n')
    manifest={'schema':'sfp2-rarity-batch/v1','seed':SEED,'count':len(recipes),'recipes':recipes}
    (out/'batch_plan.json').write_text(json.dumps(manifest,indent=2)+'\n')
    for x in recipes:
        r=x['recipe']
        print(x['id'],x['rarity'],x['consistencyClass'],'|',r['knitStructure'],r['pattern'],r['bandType'],r['trimAccent'],r['microAccent'],r['motif'],r['motifPlacement'])
if __name__=='__main__': main()
