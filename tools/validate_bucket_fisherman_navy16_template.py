#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from v5.pngio import read_rgba_png
ID='bucket_fisherman_navy16'
TD=ROOT/'authored/templates'/ID
m=json.loads((TD/'frame_manifest.json').read_text())
c=json.loads((ROOT/f'generator/data/templates/{ID}.json').read_text())
w=json.loads((ROOT/f'generator/data/headwear/{ID}_wear_contract.json').read_text())
lib=json.loads((ROOT/'generator/data/headwear/bucket_hat_approved_library.json').read_text())
idx=json.loads((ROOT/'generator/data/templates/index.json').read_text())
sel=json.loads((ROOT/'authored/approved/bucket_hat_v1/rotations/fisherman_navy/selection.json').read_text())
assert m['id']==c['id']==ID
assert m['runtimeAuthority']==['front','right','back','left']
assert c['geometryLock']['forbidResample'] is True
assert w['frameSize']==[16,16] and w['baseRenderScale']==1.0
for name,rec in m['frames'].items():
    p=ROOT/rec['path']; pix=read_rgba_png(p)
    assert len(pix)==16 and len(pix[0])==16
    assert hashlib.sha256(p.read_bytes()).hexdigest()==rec['sha256']
    sp=ROOT/rec['sourcePath']
    assert hashlib.sha256(sp.read_bytes()).hexdigest()==rec['sourceSha256']
right=read_rgba_png(TD/'right.png'); left=read_rgba_png(TD/'left.png')
assert left==[list(reversed(row)) for row in right], 'left must be exact mirror of right'
g=lib['constructionGroups']['sf_fisherman_compact']
assert g['status']=='DIRECTIONAL_APPROVED_ESM_WEAR_QC_READY'
assert g['rollWeight']==0 and g['authority']==f'generator/data/templates/{ID}.json'
reg=idx['templates'][ID]
assert reg['humanArtApproved'] is True and reg['esmWearApprovalRequired'] is True
assert sel['status']=='USER_APPROVED_FOR_CONSTRUCTION_ESM_QC_READY'
assert sel['esmQcGarment']=='qc.bucket.fisherman.navy16.base'
print('PASS bucket_fisherman_navy16: exact approved four-cardinal art locked; no resampling; Left mirrors Right; ESM QC registered; production weight 0 pending live wear QC')
