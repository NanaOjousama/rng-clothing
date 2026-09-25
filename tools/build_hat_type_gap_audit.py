#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/'source_catalog/HAT_WORKING_CATALOG.json'
PARTS=ROOT/'generator/data/source_parts/hat_source_parts.json'
GOLD=ROOT/'generator/data/source_respecting_hat_goldens.json'
OUT_JSON=ROOT/'generator/data/hat_type_gap_audit.json'
OUT_MD=ROOT/'docs/roadmaps/HAT_TYPE_GAP_AUDIT.md'

def production_source_coverage():
    p=json.load(open(PARTS))
    covered=set()
    for spec in p['families'].values():
        pack=spec['pack']; names={spec['base']}
        names.update(spec.get('alternateConstructionStates',[]))
        for key in ('roleByStateRgb','roleByConstructionRgb'):
            names.update((spec.get(key) or {}).keys())
        for name in names:
            covered.add((pack,name))
    for part in p['parts']:
        if part.get('sourcePack') and part.get('sourceVariant'):
            covered.add((part['sourcePack'],part['sourceVariant']))
    return covered

def source_rows():
    return json.load(open(CAT))['rows']

def production_families():
    g=json.load(open(GOLD))
    return sorted(g['families'])

def repo_presence():
    items=[]
    checks=[
      ('Dad cap','EXPERIMENT_READY_FOR_PROMOTION','experiments/dad_cap/production_20x20'),
      ('Dad cap v2','EXPERIMENT_VARIANT','experiments/dad_cap_v2/production_20x20'),
      ('Trucker cap','EXPERIMENT_INCOMPLETE','experiments/trucker_cap'),
      ('Mario-style reference cap','EASTER_EGG_PROTOTYPE','prototypes/mario_hat'),
      ('Mario worn captures','EASTER_EGG_WORN_PROOF','experiments/mario_hat'),
      ('Slouch beanie','EXPERIMENTAL_CONSTRUCTION','experiments/slouch_beanie_compare'),
    ]
    for name,status,rel in checks:
        p=ROOT/rel
        items.append({'type':name,'status':status,'path':rel,'exists':p.exists()})
    return items

def reference_only_types():
    checks=[
      ('Cowboy variants','references/benchmark/male clothing/[FS] Adventurer\'s Armour and Outfits 1.0.0/Accessories/Cowboy Hats'),
      ('Fancy hats','references/benchmark/male clothing/[FS] Adventurer\'s Armour and Outfits 1.0.0/Accessories/Fancy Hats'),
      ('Helmets','references/benchmark/male clothing/[FS] Adventurer\'s Armour and Outfits 1.0.0/Accessories/Helmets'),
      ('Jester hat','references/benchmark/male clothing/[FS] Adventurer\'s Armour and Outfits 1.0.0/Accessories/Miscellaneous/Jester Hat'),
      ('Pointy witch hood','references/benchmark/male clothing/[FS] Adventurer\'s Armour and Outfits 1.0.0/Accessories/Miscellaneous/Pointy Witch Hood'),
      ('Sombrero','references/benchmark/male clothing/[FS] Adventurer\'s Armour and Outfits 1.0.0/Accessories/Miscellaneous/Sombrero'),
      ('Prospector hats','references/benchmark/male clothing/[FS] Adventurer\'s Armour and Outfits 1.0.0/Accessories/Prospector Hats'),
      ('Visors','references/benchmark/male clothing/[FS] Adventurer\'s Armour and Outfits 1.0.0/Accessories/Visors'),
      ('Sherlock-style hat','references/benchmark/male clothing/[FS] Frogwares Sherlock Pack/Hats/Sherlock Hat'),
      ('Watson-style hat','references/benchmark/male clothing/[FS] Frogwares Sherlock Pack/Hats/Watson Hat'),
      ('Sailor hats','references/benchmark/【FS】SubabyTvanZ\'s sailor suit Set/Hats'),
      ('Dynamic hood family','references/hoodie/Hoods & Hoodies Pack/[FS] Hoods & Hoodies/Hats/Hoods'),
    ]
    return [{'type':name,'path':rel,'exists':(ROOT/rel).exists()} for name,rel in checks]

def curated_missing():
    # "Missing" means missing from the current 20-family production catalog,
    # not necessarily absent from disk.
    return [
      {'type':'Cowboy hat','priority':'HIGH','status':'SOURCE_PRESENT_UNPROMOTED','evidence':['More Accessories and Stuff / Cowboy Hat'],'next':'Promote as its own construction family.'},
      {'type':'Baseball cap','priority':'HIGH','status':'PHOTO_TAILOR_REBOOT_IN_PROGRESS','evidence':['experiments/cap_reboot/baseball_cap_pt_04','cap reference'],'next':'PT5/PT6 worn QC from fresh cap-reference folder; old rectangle clean-room pass is superseded.'},
      {'type':'Dad cap','priority':'HIGH','status':'CLEANROOM_REBOOT_PLANNED','evidence':[],'next':'Fresh construction after Baseball; old Dad experiments remain visually quarantined until new master approval.'},
      {'type':'Snapback cap','priority':'LOW','status':'DEFERRED_NOT_REQUIRED','evidence':['More Accessories and Stuff / Cap (Snapback)'],'next':'Do not include in current cap reboot; revisit only if it proves meaningfully distinct from Baseball at worn scale.'},
      {'type':'Trucker cap','priority':'HIGH','status':'CLEANROOM_REBOOT_PLANNED','evidence':[],'next':'Fresh construction after Baseball/Dad; old Trucker experiment art remains visually quarantined until new master approval.'},
      {'type':'Slouch beanie','priority':'HIGH','status':'EXPERIMENT_PRESENT','evidence':['experiments/slouch_beanie_compare','spritefusion slouch experiments'],'next':'Promote as a distinct beanie construction rather than a material variant.'},
      {'type':'Party hat','priority':'MEDIUM','status':'SOURCE_PRESENT_UNPROMOTED','evidence':['More Accessories and Stuff / Party Hat'],'next':'Review and promote if worn identity passes.'},
      {'type':'Paperboy / newsboy cap','priority':'HIGH','status':'SOURCE_PRESENT_BUT_REJECTED','evidence':['More Accessories and Stuff / Paperboy Hat (REJECTED_LIVE)'],'next':'Do not promote rejected source; replace/re-author a readable construction.'},
      {'type':'Mario-style reference cap','priority':'LOW','status':'DEFERRED_EASTER_EGG','evidence':['prototypes/mario_hat','experiments/mario_hat'],'next':'Separate easter-egg/reference project; excluded from the normal cap reboot.'},
      {'type':'Veil family','priority':'MEDIUM','status':'SOURCE_PRESENT_HEAD_ACCESSORY','evidence':['More Accessories and Stuff / Veil + variants'],'next':'Decide whether this belongs in hat catalog or accessory catalog before promotion.'},
      {'type':'Tiara family','priority':'MEDIUM','status':'SOURCE_PRESENT_HEAD_ACCESSORY','evidence':['More Accessories and Stuff / Tiara 1-4'],'next':'Treat as head-accessory construction family if included in hats.'},
      {'type':'Goggles-on-head','priority':'LOW','status':'SOURCE_PRESENT_HEAD_ACCESSORY','evidence':['More Accessories and Stuff / Goggles (On Head)'],'next':'Optional head-accessory family.'},
      {'type':'Flower crown','priority':'LOW','status':'SOURCE_PRESENT_HEAD_ACCESSORY','evidence':['More Accessories and Stuff / Flower Dance Crown'],'next':'Optional alternate crown/garland construction.'},
      {'type':'Witch / wizard pointy hat','priority':'HIGH','status':'REFERENCE_ONLY','evidence':['benchmark Pointy Witch Hood','vanilla Witch reference','Photo Tailor challenge reference'],'next':'Needs new approved construction before production.'},
      {'type':'Jester hat','priority':'LOW','status':'REFERENCE_ONLY','evidence':['benchmark Jester Hat'],'next':'Needs new approved construction.'},
      {'type':'Sombrero','priority':'MEDIUM','status':'REFERENCE_ONLY','evidence':['benchmark Sombrero + Alt'],'next':'Needs new approved construction.'},
      {'type':'Prospector / miner hat','priority':'MEDIUM','status':'REFERENCE_ONLY','evidence':['benchmark Prospector Hats'],'next':'Needs new approved construction.'},
      {'type':'Helmet family','priority':'MEDIUM','status':'REFERENCE_ONLY','evidence':['benchmark Helmets'],'next':'Separate armor/headgear family; not a normal soft-hat variant.'},
      {'type':'Visor','priority':'LOW','status':'REFERENCE_ONLY','evidence':['benchmark Visors'],'next':'Needs new approved construction.'},
      {'type':'Deerstalker / detective cap','priority':'LOW','status':'REFERENCE_ONLY','evidence':['benchmark Sherlock Hat'],'next':'Needs new approved construction.'},
      {'type':'Sailor cap','priority':'MEDIUM','status':'REFERENCE_ONLY','evidence':['benchmark sailor suit hats'],'next':'Needs source/construction review before production.'},
      {'type':'Top hat','priority':'MEDIUM','status':'REFERENCE_OR_STYLE_PROFILE_ONLY','evidence':['style-profile references'],'next':'No production/source-catalog construction; author or promote a reference-backed construction.'},
      {'type':'Fedora','priority':'MEDIUM','status':'POLICY_REFERENCE_ONLY','evidence':['authored policy/derivation references'],'next':'No production/source-catalog construction; needs approved construction.'},
      {'type':'Bucket hat','priority':'MEDIUM','status':'NOT_FOUND_IN_CURRENT_CORPUS','evidence':[],'next':'New construction required.'},
      {'type':'Chef hat','priority':'LOW','status':'NOT_FOUND_IN_CURRENT_CORPUS','evidence':[],'next':'New construction required.'}
    ]

def old_material_disposition():
    return {
      'KEEP_ACTIVE':[
        'generator/source_respecting_hat_production.py',
        'generator/hat_hybrid_enhancements.py',
        'generator/data/source_respecting_hat_goldens.json',
        'generator/data/source_parts/hat_source_parts.json',
        'generator/data/hat_hybrid_production_policy.json',
        'generator/data/hat_renderer_contract.json',
      ],
      'KEEP_REFERENCE_OR_PROMOTION_INPUT':[
        'source_catalog/HAT_WORKING_CATALOG.json',
        'source_catalog/HAT_WORKING_CATALOG.md',
        'experiments/slouch_beanie_compare',
        'prototypes/mario_hat',
        'experiments/mario_hat',
        'experiments/source_respecting_hat_pilot_01',
        'experiments/source_respecting_hat_batch_a_01',
        'experiments/source_respecting_hat_remaining_01',
      ],
      'QUARANTINED_CAP_HISTORY':[
        'experiments/dad_cap/',
        'experiments/dad_cap_v2/',
        'experiments/trucker_cap/',
      ],
      'ARCHIVE_CANDIDATE_AFTER_CURRENT_FREEZE':[
        'experiments/hat_production_batch_01',
        'experiments/hat_production_batch_09',
        'experiments/source_fidelity',
        'experiments/cap_ai',
      ],
      'DELETE_CANDIDATE_AFTER_VERIFICATION':[
        'temporary enlarged previews / caches that are reproducible',
      ],
      'RULE':'Do not delete source/provenance or unpromoted constructions merely because the renderer is frozen.'
    }

def main():
    rows=source_rows()
    covered=production_source_coverage()
    uncovered=[r for r in rows if (r['pack'],r['name']) not in covered]
    by_kind=Counter(r['hat_kind'] for r in uncovered)
    production=production_families()
    audit={
      'schema':'hat-type-gap-audit/v1',
      'generatedOn':'2026-09-24',
      'rendererContract':'HAT_RENDERER_V1',
      'rendererFrozen':True,
      'catalogFrozen':False,
      'productionFamilyCount':len(production),
      'productionFamilies':production,
      'sourceCatalogHatSlotAppearances':len(rows),
      'sourceAppearancesCoveredByProductionContracts':sum(1 for r in rows if (r['pack'],r['name']) in covered),
      'sourceAppearancesNotCoveredByProductionContracts':len(uncovered),
      'uncoveredByKind':dict(sorted(by_kind.items())),
      'uncoveredSourceRows':[
        {k:r.get(k) for k in ('pack','name','png_size','hat_kind','review_state','note')}
        for r in uncovered
      ],
      'repoExperimentsAndPrototypes':repo_presence(),
      'referenceOnlyConstructionEvidence':reference_only_types(),
      'stillMissingFromProduction':curated_missing(),
      'oldMaterialDisposition':old_material_disposition(),
      'notes':[
        'Still missing means missing from the current production catalog, not necessarily absent from disk.',
        'Reference-only benchmark material is evidence/inspiration, not automatically approved production source.',
        'Head accessories are listed separately because inclusion in the hat catalog is a design choice.',
        'Paperboy source failed live readability and must not be promoted unchanged.'
      ]
    }
    OUT_JSON.parent.mkdir(parents=True,exist_ok=True)
    OUT_MD.parent.mkdir(parents=True,exist_ok=True)
    OUT_JSON.write_text(json.dumps(audit,indent=2)+'\n')

    cap_reboot=[x for x in audit['stillMissingFromProduction'] if x['status'].startswith('CLEANROOM_REBOOT') or x['status'].startswith('PHOTO_TAILOR_REBOOT') or x['status']=='DEFERRED_NOT_REQUIRED']
    easter_deferred=[x for x in audit['stillMissingFromProduction'] if x['status']=='DEFERRED_EASTER_EGG']
    source_ready=[x for x in audit['stillMissingFromProduction'] if ('SOURCE' in x['status'] or 'EXPERIMENT' in x['status'] or 'PROTOTYPE' in x['status']) and x not in cap_reboot and x not in easter_deferred]
    ref_only=[x for x in audit['stillMissingFromProduction'] if 'REFERENCE' in x['status'] or x['status']=='NOT_FOUND_IN_CURRENT_CORPUS']
    lines=[
      '# Hat Type Gap Audit',
      '',
      '**Renderer:** HAT_RENDERER_V1 is frozen. **Catalog:** open for expansion.',
      '',
      '## Snapshot',
      '',
      f'- Current production families: **{len(production)}**.',
      f'- Hat-slot source appearances audited: **{len(rows)}**.',
      f'- Source appearances already represented by production family contracts/states: **{audit["sourceAppearancesCoveredByProductionContracts"]}**.',
      f'- Source appearances not represented by production contracts: **{len(uncovered)}**.',
      '',
      '## Current cap reboot',
      '',
      '- **Scope:** Baseball Cap + Dad Cap + Trucker Cap.',
      '- **Snapback:** deferred/not required unless future worn-scale testing proves it meaningfully distinct.',
      '- **Mario/reference cap:** excluded; separate easter-egg project later.',
      '- **Clean-room rule:** old Dad/Trucker experiment art remains visually quarantined during new construction.',
      ''
    ]
    for x in cap_reboot:
        lines.append(f'- **{x["type"]}** — {x["status"]} — {x["next"]}')
    lines += ['', '## Highest-value production gaps already present in the repo/source corpus', '']
    for x in source_ready:
        lines.append(f'- **{x["type"]}** — {x["status"]} — {x["next"]}')
    lines += ['', '## Deferred easter-egg/reference content', '']
    for x in easter_deferred:
        lines.append(f'- **{x["type"]}** — {x["status"]} — {x["next"]}')
    lines += ['', '## Reference-only / genuinely new construction gaps', '']
    for x in ref_only:
        lines.append(f'- **{x["type"]}** — {x["status"]} — {x["next"]}')
    lines += ['', '## Uncovered source-catalog items by classification', '']
    for kind,count in sorted(by_kind.items()):
        lines.append(f'- **{kind}**: {count}')
    lines += ['', '## Old material disposition', '']
    disp=audit['oldMaterialDisposition']
    for section in ('KEEP_ACTIVE','KEEP_REFERENCE_OR_PROMOTION_INPUT','QUARANTINED_CAP_HISTORY','ARCHIVE_CANDIDATE_AFTER_CURRENT_FREEZE','DELETE_CANDIDATE_AFTER_VERIFICATION'):
        lines.append(f'### {section}')
        lines.append('')
        for item in disp[section]:
            lines.append(f'- {item}')
        lines.append('')
    lines += [
      '## Important findings',
      '',
      '- **Cowboy Hat already exists in the primary source corpus** and is REVIEW_NEEDED; it does not need a brand-new silhouette unless live review rejects it.',
      '- **Baseball Cap (Cap 2) and Snapback are already LIVE_APPROVED source constructions**, but were never promoted into the current 20-family production catalog.',
      '- Dad Cap, Trucker Cap, Slouch Beanie, and the Mario-style cap all have existing repo work that should be reviewed/promoted instead of recreated blindly.',
      '- The old Paperboy Hat failed live identity/readability; keep that failure as evidence, but do not promote the rejected construction.',
      '- Do not delete old source/prototype material before the corresponding missing family is promoted or explicitly rejected.'
    ]
    OUT_MD.write_text('\n'.join(lines)+'\n')
    print('wrote',OUT_JSON)
    print('wrote',OUT_MD)
    print('production families',len(production),'source covered',audit['sourceAppearancesCoveredByProductionContracts'],'uncovered',len(uncovered))
    print('still-missing production types',len(audit['stillMissingFromProduction']))

if __name__=='__main__':
    main()
