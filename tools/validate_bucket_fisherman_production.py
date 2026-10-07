#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from v5.pngio import read_rgba_png
from v5.source.template_transfer import alpha_cells
reg=json.loads((ROOT/'generator/data/headwear/bucket_hat_production_registry.json').read_text())
assert reg['active'] is True
c=reg['constructions']['bucket_fisherman_navy16'];assert c['status']=='PRODUCTION_READY' and c['weight']>0 and c['liveWearApproved'] is True
wear=json.loads((ROOT/'generator/data/headwear/bucket_fisherman_navy16_wear_contract.json').read_text())
assert wear['status']=='APPROVED_LIVE_ESM_WEAR_QC' and wear['directionDefaults']['front']['offset']==[0,-4]
m=json.loads((ROOT/'experiments/bucket_fisherman_rng_proof_01/manifest.json').read_text());assert m['candidateCount']==16
base={v:read_rgba_png(ROOT/'authored/templates/bucket_fisherman_navy16'/f'{v}.png') for v in ('front','right','back','left')}
for row in m['candidates']:
 for v,p in row['frames'].items():
  out=read_rgba_png(ROOT/p);assert alpha_cells(out)==alpha_cells(base[v]),(row['seed'],v)
 right=read_rgba_png(ROOT/row['frames']['right']);left=read_rgba_png(ROOT/row['frames']['left']);assert left==[list(reversed(r)) for r in right]
print('PASS Fisherman production: live fit approved, positive construction weight, 16 RNG rolls geometry-locked, left mirrors right')
