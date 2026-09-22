#!/usr/bin/env python3
from pathlib import Path
import json

ROOT=Path('/run/media/deck/USD00/RNG_clothing')
OUT=ROOT/'experiments/sf_pipeline_smoke_01'
OUT.mkdir(parents=True,exist_ok=True)

candidate_source=ROOT/'experiments/spritefusion_beanie_material_rescale_test_01/accepted_32_and_under/material_00.png'
candidate_meta=json.loads(
    (ROOT/'experiments/spritefusion_beanie_material_rescale_test_01/metadata.json').read_text()
)
rec=candidate_meta['records'][0]

candidate={
  'schema':'rng-clothing-sf-candidate/v1',
  'id':'smoke.sf01',
  'operation':'style-reference',
  'requestedSize':16,
  'status':'GENERATED_UNREVIEWED',
  'requestId':candidate_meta.get('request_id',''),
  'prompt':'fixture from existing approved-size Sprite Fusion material batch',
  'sourceFamily':'slouch_beanie',
  'constructionTemplate':'generator/data/templates/slouch_pl24.json',
  'output':rec
}
dirs_root=ROOT/'experiments/sfb3_spritefusion_directions/SF01'
dir_meta=json.loads((dirs_root/'metadata.json').read_text())
items=dir_meta.get('items',dir_meta.get('records',[]))
directions={x['direction']:x for x in items}

direction_manifest={
  'schema':'rng-clothing-sf-direction-set/v1',
  'id':'smoke.sf01.directions',
  'sourceCandidateId':'smoke.sf01',
  'sourceAssetId':rec['asset_id'],
  'requestedSize':16,
  'status':'CANDIDATE_DIRECTIONAL',
  'cardinalMap':{'front':'S','right':'E','back':'N','left':'W'},
  'directions':directions,
  'consistencyClasses':{
    'knitStructure':'WHOLE_HAT',
    'pattern':'WHOLE_HAT',
    'trimAccent':'WRAPAROUND_REGION',
    'motif':'LOCALIZED'
  }
}

(OUT/'candidate_manifest.json').write_text(json.dumps(candidate,indent=2)+'\n')
(OUT/'direction_manifest.json').write_text(json.dumps(direction_manifest,indent=2)+'\n')
print('wrote smoke fixture',OUT)
