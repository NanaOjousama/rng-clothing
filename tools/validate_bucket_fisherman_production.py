#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
reg=json.loads((ROOT/'generator/data/headwear/bucket_hat_production_registry.json').read_text())
c=reg['constructions']['bucket_fisherman_navy16']
wear=json.loads((ROOT/'generator/data/headwear/bucket_fisherman_navy16_wear_contract.json').read_text())
old=json.loads((ROOT/'generator/data/headwear/bucket_fisherman_navy16_roll_matrix.json').read_text())
assert reg['active'] is True
assert c['liveWearApproved'] is True
assert c['status']=='CONSTRUCTION_PRODUCTION_READY_SOURCE_GOLDEN_REVIEW_REQUIRED'
assert c['rendererId']=='HAT_RENDERER_V1'
assert c['sourceFamily']=='bucket_fisherman'
assert c['weight']==0
assert c['candidateGoldenRegistry']=='generator/data/source_respecting_hat_goldens_fisherman_candidate.json'
assert c['activationGate']=='User visually approves Fisherman source-golden palette candidates before whitelist/positive production weight'
assert wear['status']=='APPROVED_LIVE_ESM_WEAR_QC'
assert wear['directionDefaults']['front']['offset']==[0,-4]
assert old['status']=='REJECTED_VISUAL_PROOF_DO_NOT_USE'
print('PASS Fisherman construction production-ready; HAT_RENDERER_V1 activation correctly held at weight 0 pending human visual review')
