#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'authored/approved/bucket_hat_v1/manifest.json').read_text())
library=json.loads((ROOT/'generator/data/headwear/bucket_hat_approved_library.json').read_text())
assert manifest['status']=='USER_APPROVED_INTAKE_NOT_PRODUCTION'
assert library['status']=='AUDITED_INTAKE_FAIL_CLOSED'
assert library['activeGeneratorIntegration'] is False
assert library['mainSelectionIndices']==[1,2,3,4,5,6]
items=manifest['items']
assert len(items)==23
for it in items:
    p=ROOT/it['canonicalPath']
    assert p.exists(),p
    got=hashlib.sha256(p.read_bytes()).hexdigest()
    assert got==it['sha256'],(p,got,it['sha256'])
    assert it['humanApproved'] is True
    assert it['productionApproved'] is False
# user-priority six must be unique construction groups and exact source bytes
main=[]
for i in range(1,7):
    hits=[x for x in items if x.get('selectionIndex')==i]
    assert len(hits)==1,(i,len(hits))
    x=hits[0]; main.append(x['constructionGroup'])
    src=ROOT/x['originPath']; dst=ROOT/x['canonicalPath']
    assert src.read_bytes()==dst.read_bytes(),x['id']
assert len(set(main))==6
# known intentional shape dedupes
byid={x['id']:x for x in items}
assert byid['construction_fisherman_cream_worn64']['constructionGroup']=='pl_fisherman_tight'
assert byid['construction_fisherman_navy_worn64']['constructionGroup']=='pl_fisherman_tight'
assert byid['construction_fisherman_rust_worn64']['constructionGroup']=='pl_fisherman_tight'
for k in ['pattern_gingham_red_front64','motif_mushroom_pixellab_front64','motif_mushroom_spritefusion_front64']:
    assert byid[k]['constructionGroup']=='vanilla_footprint_core'
assert byid['design_moss_mushroom_front']['constructionGroup']=='sf_round_wide_28x16'
assert byid['motif_daisy_pink_front']['constructionGroup']=='sf_round_wide_28x16'
# nothing incomplete is accidentally rollable
for name,g in library['constructionGroups'].items():
    assert g['rollWeight']==0,(name,g['rollWeight'])
print(f"PASS bucket approved intake: {len(items)} preserved inputs, {len(library['constructionGroups'])} construction groups, priority 01-06 unique and fail-closed")
