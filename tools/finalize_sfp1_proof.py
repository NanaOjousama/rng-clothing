#!/usr/bin/env python3
from pathlib import Path
import json, sys

ROOT=Path('/run/media/deck/USD00/RNG_clothing')
sys.path.insert(0,str(ROOT))

PROOF=ROOT/'experiments/sfp1_proof'
SELECT=json.loads((PROOF/'selected_fronts.json').read_text())

CONFIG={
 'sfp1.wholehat': {
   'folder':'wholehat_directions',
   'class':'WHOLE_HAT',
   'semantic':'knitStructure/material identity',
 },
 'sfp1.wraparound': {
   'folder':'wraparound_directions',
   'class':'WRAPAROUND_REGION',
   'semantic':'cuff/headband trim',
 },
 'sfp1.localized': {
   'folder':'localized_directions',
   'class':'LOCALIZED',
   'semantic':'edge label',
 },
}

registry_path=ROOT/'sf_pipeline/registry.json'
registry=json.loads(registry_path.read_text())

for cid,cfg in CONFIG.items():
    selected=SELECT[cid]
    outputs=json.loads((PROOF/cfg['folder']/'outputs.json').read_text())
    directions={o['direction']:o for o in outputs}

    candidate_manifest={
      'schema':'rng-clothing-sf-candidate/v1',
      'id':cid,
      'operation':'style-reference',
      'status':'CANDIDATE_FRONT_APPROVED',
      'selectedOutput':selected,
      'candidateMechanicalPassed':True,
      'humanFrontReview':'APPROVED_FOR_DIRECTION_TEST',
      'productionApproved':False,
    }
    direction_manifest={
      'schema':'rng-clothing-sf-direction-set/v1',
      'id':cid+'.directions',
      'sourceCandidateId':cid,
      'sourceAssetId':selected['asset_id'],
      'status':'CANDIDATE_DIRECTIONAL',
      'consistencyClass':cfg['class'],
      'semanticFeature':cfg['semantic'],
      'cardinalMap':{'front':'S','right':'E','back':'N','left':'W'},
      'directions':directions,
      'directionMechanicalPassed':True,
      'semanticDirectionalReview':'PASS_FOR_ESM_QC',
      'productionApproved':False,
    }

    cpath=PROOF/(cid.replace('.','_')+'_candidate_manifest.json')
    dpath=PROOF/(cid.replace('.','_')+'_direction_manifest.json')
    cpath.write_text(json.dumps(candidate_manifest,indent=2)+'\n')
    dpath.write_text(json.dumps(direction_manifest,indent=2)+'\n')

    registry['assets'][cid]={
      'status':'CANDIDATE_DIRECTIONAL',
      'candidateManifest':str(cpath.relative_to(ROOT)),
      'directionManifest':str(dpath.relative_to(ROOT)),
      'candidateMechanicalPassed':True,
      'directionMechanicalPassed':True,
      'humanArtApproved':False,
      'esmWearApproved':False,
      'history':[
        {'status':'GENERATED_UNREVIEWED','note':'SFP1 proof generation'},
        {'status':'CANDIDATE_FRONT_APPROVED','note':'clean front selected for direction-set'},
        {'status':'CANDIDATE_DIRECTIONAL','note':'8-direction set passed mechanical + semantic pre-ESM review'},
      ],
    }

registry_path.write_text(json.dumps(registry,indent=2)+'\n')
print('finalized',len(CONFIG),'SFP1 proof assets')
